"""Small WSGI application: bounded jobs, persistent status, private downloads."""
from __future__ import annotations
import hashlib
import hmac
import json
import logging
import os
import secrets
import sqlite3
import threading
import time
import uuid
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from flask import Flask, jsonify, render_template, request, send_file, session
from werkzeug.exceptions import HTTPException
from gpx_to_tcx import Config, ConversionError, MAX_BYTES, convert, number, read_gpx, summary

LOG = logging.getLogger(__name__)
EVENTS = {"page_view", "conversion_started", "conversion_completed", "conversion_failed", "download", "weather_requested"}


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(DATA_DIR=os.environ.get("DATA_DIR", str(Path(__file__).parent / ".data")),
                      MAX_CONTENT_LENGTH=MAX_BYTES + 64*1024, MAX_FORM_MEMORY_SIZE=128*1024,
                      MAX_FORM_PARTS=32, MAX_ACTIVE_JOBS=8, WORKERS=2, JOB_TTL=3600,
                      ANALYTICS_DAYS=30, SECRET_KEY=os.environ.get("SECRET_KEY"),
                      ADMIN_TOKEN=os.environ.get("ADMIN_TOKEN", ""),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                      SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
                      SEND_FILE_MAX_AGE_DEFAULT=3600)
    if config:
        app.config.update(config)
    data_dir = Path(app.config["DATA_DIR"]).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    if not app.config["SECRET_KEY"]:
        key_path = data_dir / ".session-key"
        try:
            with key_path.open("x", encoding="ascii") as file:
                file.write(secrets.token_hex(32))
        except FileExistsError:
            pass
        app.config["SECRET_KEY"] = key_path.read_text(encoding="ascii")
    database = data_dir / "state.sqlite3"

    @contextmanager
    def db():
        connection = sqlite3.connect(database, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    with db() as con:
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
              id TEXT PRIMARY KEY, owner TEXT NOT NULL, filename TEXT NOT NULL,
              status TEXT NOT NULL, progress INTEGER NOT NULL DEFAULT 0,
              created REAL NOT NULL, updated REAL NOT NULL, expires REAL NOT NULL,
              result TEXT, error TEXT, field TEXT);
            CREATE INDEX IF NOT EXISTS job_expiry ON jobs(expires);
            CREATE TABLE IF NOT EXISTS events (
              day TEXT, event TEXT, count INTEGER NOT NULL,
              PRIMARY KEY(day, event));
            CREATE TABLE IF NOT EXISTS visitors (
              day TEXT, visitor TEXT, PRIMARY KEY(day, visitor));
        """)
    executor = ThreadPoolExecutor(max_workers=app.config["WORKERS"], thread_name_prefix="conversion")
    job_slots = threading.BoundedSemaphore(app.config["MAX_ACTIVE_JOBS"])
    app.extensions["executor"] = executor
    app.extensions["database"] = database
    cache, rates = OrderedDict(), OrderedDict()
    lock, weather_slots = threading.Lock(), threading.BoundedSemaphore(4)
    cleanup_state = [0.0]
    janitor_stop = threading.Event()
    janitor_started = [False]
    app.extensions["janitor_stop"] = janitor_stop

    def owner():
        if "owner" not in session:
            session["owner"] = secrets.token_hex(24)
        return session["owner"]

    def purge_analytics(con):
        oldest = (datetime.now(timezone.utc).date() -
                  timedelta(days=app.config["ANALYTICS_DAYS"]-1)).isoformat()
        con.execute("DELETE FROM events WHERE day < ?", (oldest,))
        con.execute("DELETE FROM visitors WHERE day < ?", (oldest,))

    def _record(event, visitor=None):
        day = datetime.now(timezone.utc).date().isoformat()
        with db() as con:
            purge_analytics(con)
            con.execute("INSERT INTO events VALUES (?, ?, 1) ON CONFLICT(day,event) DO UPDATE SET count=count+1", (day, event))
            if visitor:
                digest = hmac.new(str(app.config["SECRET_KEY"]).encode(), (day+visitor).encode(), hashlib.sha256).hexdigest()
                # Daily deduplication is bounded. Aggregate counts still continue above the cap.
                con.execute("INSERT OR IGNORE INTO visitors SELECT ?, ? WHERE (SELECT COUNT(*) FROM visitors WHERE day=?) < 10000",
                            (day, digest, day))

    def record(event, visitor=None):
        try:
            _record(event, visitor)
        except sqlite3.Error:
            LOG.warning("Aggregate analytics write failed", exc_info=True)

    def limited(bucket, limit=20, period=60):
        key = (bucket, owner())
        now = time.monotonic()
        with lock:
            started, count = rates.pop(key, (now, 0))
            if now-started > period:
                started, count = now, 0
            rates[key] = (started, count+1)
            while len(rates) > 2048:
                rates.popitem(last=False)
        return count >= limit

    def cleanup():
        now = time.time()
        with lock:
            if now-cleanup_state[0] < 30:
                return
            cleanup_state[0] = now
        with db() as con:
            expired = con.execute("SELECT id FROM jobs WHERE expires < ?", (now,)).fetchall()
            con.execute("DELETE FROM jobs WHERE expires < ?", (now,))
            purge_analytics(con)
        for row in expired:
            for suffix in (".gpx", ".tcx", ".part"):
                try:
                    (data_dir / (row["id"]+suffix)).unlink(missing_ok=True)
                except PermissionError:
                    pass
        # Retry orphan files when active Windows downloads release their file handles.
        with db() as con:
            known = {row[0] for row in con.execute("SELECT id FROM jobs WHERE status!='cancelled'")}
        for path in data_dir.iterdir():
            if path.suffix in {".gpx", ".tcx", ".part"} and path.stem not in known:
                try:
                    path.unlink(missing_ok=True)
                except PermissionError:
                    pass

    app.extensions["cleanup"] = cleanup

    def janitor():
        while not janitor_stop.wait(30):
            try:
                cleanup()
            except Exception:
                LOG.exception("Retention cleanup failed")

    def get_job(task_id):
        try:
            if str(uuid.UUID(task_id)) != task_id:
                return None
        except ValueError:
            return None
        with db() as con:
            row = con.execute("SELECT * FROM jobs WHERE id=? AND owner=?", (task_id, owner())).fetchone()
        return row

    def update(task_id, event=None, **values):
        values["updated"] = time.time()
        keys = list(values)
        with db() as con:
            changed = con.execute("UPDATE jobs SET "+",".join(k+"=?" for k in keys)+
                                  " WHERE id=? AND status IN ('queued','processing')",
                                  [values[k] for k in keys]+[task_id]).rowcount
            if changed and event:
                try:
                    day = datetime.now(timezone.utc).date().isoformat()
                    con.execute("INSERT INTO events VALUES (?, ?, 1) ON CONFLICT(day,event) DO UPDATE SET count=count+1", (day, event))
                except sqlite3.Error:
                    LOG.warning("Job analytics write failed", exc_info=True)
        if not changed:
            raise ConversionError("任务已取消或过期。")

    def run_job(task_id, cfg):
        source, target = data_dir/(task_id+".gpx"), data_dir/(task_id+".tcx")
        try:
            update(task_id, status="processing", progress=10)
            result = convert(source, target, cfg, lambda value: update(task_id, progress=value))
            update(task_id, event="conversion_completed", status="completed", progress=100, result=json.dumps(result, separators=(",", ":")))
        except ConversionError as exc:
            target.unlink(missing_ok=True)
            try:
                update(task_id, event="conversion_failed", status="error", error=str(exc), field=exc.field)
            except ConversionError:
                pass
        except Exception:
            LOG.exception("Conversion failed: %s", task_id)
            target.unlink(missing_ok=True)
            try:
                update(task_id, event="conversion_failed", status="error", error="转换失败，请稍后重试。")
            except ConversionError:
                pass
        finally:
            source.unlink(missing_ok=True)
            job_slots.release()

    def admin_allowed():
        token = app.config["ADMIN_TOKEN"]
        supplied = request.headers.get("Authorization", "").removeprefix("Bearer ")
        return bool(token) and hmac.compare_digest(str(token), supplied)

    @app.before_request
    def check_origin():
        if not app.testing:
            with lock:
                if not janitor_started[0]:
                    janitor_started[0] = True
                    threading.Thread(target=janitor, name="retention-cleanup", daemon=True).start()
        if request.method in {"POST", "DELETE"} and request.headers.get("Origin"):
            if urlsplit(request.headers["Origin"]).netloc != request.host:
                return jsonify(error="请求来源不允许。"), 403

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: https://tile.openstreetmap.org; "
            "font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; "
            "frame-ancestors 'none'; form-action 'self'; worker-src 'self'")
        response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"
        if request.path.startswith(("/status", "/download", "/api", "/upload", "/preview")):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(ConversionError)
    def conversion_error(error):
        return jsonify(error=str(error), field=error.field), 400

    @app.errorhandler(HTTPException)
    def http_error(error):
        message = "上传文件不能超过 16 MB。" if error.code == 413 else error.description
        return jsonify(error=message), error.code

    @app.get("/")
    def index():
        supported = ("zh", "zh-tw", "en", "ja", "ko", "fr", "de", "es", "pt", "it", "ar", "ru")
        language = request.cookies.get("language")
        if language not in supported:
            language = request.accept_languages.best_match(supported) or "zh"
        with (Path(app.static_folder)/"locales"/(language+".json")).open(encoding="utf-8") as file:
            messages = json.load(file)
        response = app.make_response(render_template("index.html", retention_minutes=app.config["JOB_TTL"]//60,
             html_lang="zh-CN" if language=="zh" else "zh-TW" if language=="zh-tw" else language,
             html_dir="rtl" if language=="ar" else "ltr", translate=lambda key: messages.get(key, key)))
        response.vary.update(("Accept-Language", "Cookie"))
        return response

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="gpx-tcx-web")

    def uploaded_file():
        file = request.files.get("file")
        if not file or not file.filename or not file.filename.lower().endswith(".gpx"):
            raise ConversionError("请选择 .gpx 文件。", "file")
        data = file.read(MAX_BYTES+1)
        if len(data) > MAX_BYTES:
            from werkzeug.exceptions import RequestEntityTooLarge
            raise RequestEntityTooLarge()
        return file, data

    @app.post("/preview")
    def preview():
        if limited("preview", 20):
            return jsonify(error="预览请求过于频繁，请稍后重试。"), 429
        _, data = uploaded_file()
        return jsonify(summary(read_gpx(data)))

    @app.post("/convert")
    @app.post("/upload")
    def upload():
        cleanup()
        if limited("upload", 10):
            return jsonify(error="转换请求过于频繁，请稍后重试。"), 429
        cfg = Config.from_mapping(request.form)
        file, content = uploaded_file()
        task_id, now = str(uuid.uuid4()), time.time()
        if not job_slots.acquire(blocking=False):
            return jsonify(error="转换队列已满，请稍后重试。"), 503, {"Retry-After": "5"}
        # Validate cheaply inside the job; queue reservation is shared across application instances.
        with db() as con:
            con.execute("BEGIN IMMEDIATE")
            active = con.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('queued','processing') AND expires>?", (now,)).fetchone()[0]
            if active >= app.config["MAX_ACTIVE_JOBS"]:
                job_slots.release()
                return jsonify(error="转换队列已满，请稍后重试。"), 503, {"Retry-After": "5"}
            name = "".join(c for c in Path(file.filename.replace("\\", "/")).name if ord(c) >= 32)[:180] or "track.gpx"
            con.execute("INSERT INTO jobs(id,owner,filename,status,created,updated,expires) VALUES (?,?,?,'queued',?,?,?)",
                        (task_id, owner(), name, now, now, now+app.config["JOB_TTL"]))
        source = data_dir/(task_id+".gpx")
        try:
            source.write_bytes(content)
            record("conversion_started")
            executor.submit(run_job, task_id, cfg)
        except Exception:
            source.unlink(missing_ok=True)
            job_slots.release()
            update(task_id, status="error", error="任务创建失败，请稍后重试。")
            LOG.exception("Job submission failed")
            return jsonify(error="任务创建失败，请稍后重试。"), 503
        return jsonify(task_id=task_id, status="queued"), 202

    @app.get("/status/<task_id>")
    def status(task_id):
        cleanup()
        job = get_job(task_id)
        if not job:
            return jsonify(error="任务不存在或已过期。"), 404
        if job["expires"] < time.time():
            return jsonify(error="任务已过期。"), 410
        result = json.loads(job["result"]) if job["result"] else None
        return jsonify(task_id=task_id, status=job["status"], progress=job["progress"],
                       result=result, error=job["error"], field=job["field"])

    @app.get("/download/<task_id>")
    def download(task_id):
        job = get_job(task_id)
        if not job or job["status"] != "completed" or job["expires"] < time.time():
            return jsonify(error="文件不存在、未完成或已过期。"), 404
        path = data_dir/(task_id+".tcx")
        if not path.is_file():
            return jsonify(error="文件已删除。"), 404
        record("download")
        return send_file(path, as_attachment=True, download_name=Path(job["filename"]).stem+".tcx", mimetype="application/vnd.garmin.tcx+xml")

    @app.delete("/tasks/<task_id>")
    def delete_task(task_id):
        if not get_job(task_id):
            return jsonify(error="任务不存在。"), 404
        with db() as con:
            con.execute("UPDATE jobs SET status='cancelled',result=NULL,updated=? WHERE id=?", (time.time(), task_id))
        for suffix in (".tcx", ".part"):
            try:
                (data_dir/(task_id+suffix)).unlink(missing_ok=True)
            except PermissionError:
                pass  # Already inaccessible; janitor retries after any active download.
        return jsonify(status="cancelled")

    def provider(url):
        with urlopen(Request(url, headers={"User-Agent": "GPXTCXWeb/2"}), timeout=3) as response:
            return json.loads(response.read(256*1024))
    app.extensions["weather_provider"] = provider

    @app.get("/api/weather")
    def weather():
        if limited("weather", 10):
            return jsonify(error="天气请求过于频繁，请稍后重试。"), 429
        lat = number(request.args.get("lat"), "latitude", -90, 90)
        lon = number(request.args.get("lon"), "longitude", -180, 180)
        key, now = (round(lat, 2), round(lon, 2)), time.time()
        with lock:
            cached = cache.get(key)
            if cached and now-cached[0] < 900:
                cache.move_to_end(key)
                return jsonify(**cached[1], cached=True, stale=False)
        if not weather_slots.acquire(blocking=False):
            return jsonify(error="天气服务繁忙，请稍后重试。", available=False), 503
        try:
            query = urlencode(dict(latitude=key[0], longitude=key[1], current="temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m", timezone="UTC"))
            payload = app.extensions["weather_provider"]("https://api.open-meteo.com/v1/forecast?"+query)
            current = payload["current"]
            result = dict(available=True, source="Open-Meteo", updated_at=current["time"].removesuffix("Z")+"Z",
                          temperature=number(current["temperature_2m"], "temperature", -100, 70),
                          humidity=number(current["relative_humidity_2m"], "humidity", 0, 100),
                          wind_kmh=number(current["wind_speed_10m"], "wind", 0, 500),
                          code=int(number(current["weather_code"], "weather_code", 0, 99)),
                          latitude=key[0], longitude=key[1])
            with lock:
                cache[key] = (now, result)
                cache.move_to_end(key)
                while len(cache) > 128:
                    cache.popitem(last=False)
            record("weather_requested")
            return jsonify(**result, cached=False, stale=False)
        except Exception:
            LOG.warning("Weather provider unavailable")
            if cached and now-cached[0] < 3600:
                return jsonify(**cached[1], cached=True, stale=True)
            return jsonify(error="天气暂时不可用，请稍后重试。", available=False, source="Open-Meteo"), 503
        finally:
            weather_slots.release()

    @app.post("/api/analytics")
    def analytics_event():
        if request.content_length and request.content_length > 1024:
            return jsonify(error="事件内容过大。"), 413
        if limited("analytics", 12):
            return jsonify(error="事件请求过于频繁。"), 429
        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict) or payload.get("event") != "page_view":
            return jsonify(error="仅接受 page_view；转换与下载由服务器计数。"), 400
        record("page_view", owner())
        return "", 204

    @app.get("/analytics")
    def analytics_page():
        return render_template("analytics.html")

    @app.get("/api/analytics/stats")
    def analytics_stats():
        if not admin_allowed():
            return jsonify(error="需要管理员令牌。"), 401
        with db() as con:
            purge_analytics(con)
            events = [dict(row) for row in con.execute("SELECT day,event,count FROM events ORDER BY day DESC,event")]
            visitors = [dict(row) for row in con.execute("SELECT day,COUNT(*) AS count FROM visitors GROUP BY day ORDER BY day DESC")]
        return jsonify(events=events, visitors=visitors, retention_days=app.config["ANALYTICS_DAYS"])

    @app.delete("/api/analytics/stats")
    def clear_stats():
        if not admin_allowed():
            return jsonify(error="需要管理员令牌。"), 401
        with db() as con:
            con.execute("DELETE FROM events")
            con.execute("DELETE FROM visitors")
        return "", 204

    return app


app = create_app()

if __name__ == "__main__":
    from waitress import serve
    logging.basicConfig(level=logging.INFO)
    serve(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8080")),
          threads=4, max_request_body_size=MAX_BYTES+64*1024, channel_timeout=30)
