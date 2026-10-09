"""Safe namespace-aware GPX parsing and linear-time TCX conversion."""
from __future__ import annotations
import io
import math
import random
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from defusedxml import ElementTree as SafeET
from defusedxml.common import DefusedXmlException

TCX = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
AX = "http://www.garmin.com/xmlschemas/ActivityExtension/v2"
GPX_NAMESPACES = {"", "http://www.topografix.com/GPX/1/0", "http://www.topografix.com/GPX/1/1"}
EXT_NAMESPACES = {f"http://www.garmin.com/xmlschemas/{s}" for s in
                  ("TrackPointExtension/v1", "TrackPointExtension/v2", "GpxExtensions/v3", "PowerExtension/v1")}
SPORTS = {"Running", "Running_Street", "Running_Trail", "Running_Track", "Running_Treadmill",
          "Running_Indoor", "Cycling", "Walking", "Hiking"}
MAX_BYTES = 16 * 1024 * 1024
MAX_POINTS = 100_000
ET.register_namespace("", TCX)
ET.register_namespace("ae", AX)


class ConversionError(ValueError):
    def __init__(self, message, field=None):
        super().__init__(message)
        self.field = field


def number(value, field, low, high):
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ConversionError(f"{field} 必须是有效数字。", field) from None
    if not math.isfinite(result) or not low <= result <= high:
        raise ConversionError(f"{field} 必须在 {low:g} 至 {high:g} 之间。", field)
    return result


def timestamp(value, offset_minutes=0):
    try:
        result = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if result.tzinfo is None:
            # Browser getTimezoneOffset means UTC minus local time at the selected date.
            result = result.replace(tzinfo=timezone(timedelta(minutes=-offset_minutes)))
        return result.astimezone(timezone.utc)
    except (ValueError, OverflowError, AttributeError):
        raise ConversionError("时间格式无效，请重新选择开始时间。", "start_time") from None


def iso(value):
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class Config:
    activity_type: str = "Running"
    time_mode: str = "preserve"
    target_pace: float = 330.0
    start_time: datetime | None = None
    simulate_metrics: bool = True
    min_hr: int = 135
    max_hr: int = 165
    min_cadence: int = 100
    max_cadence: int = 140
    base_power: int = 150
    max_power: int = 300
    weight: float = 70.0
    seed: int = 0
    calories_per_km: float = 60.0

    @classmethod
    def from_mapping(cls, values):
        sport = str(values.get("activity_type", "Running"))
        if sport not in SPORTS:
            raise ConversionError("请选择支持的运动类型。", "activity_type")
        mode = str(values.get("time_mode", "preserve"))
        if mode not in {"preserve", "pace"}:
            raise ConversionError("时间模式无效。", "time_mode")
        match = re.fullmatch(r"(\d{1,2}):([0-5]\d)", str(values.get("target_pace", "5:30")))
        if not match:
            raise ConversionError("配速应为 分:秒，例如 5:30。", "target_pace")
        seconds = int(match[1]) * 60 + int(match[2])
        if not 60 <= seconds <= 3600:
            raise ConversionError("配速必须在 1:00 至 60:00 分/公里之间。", "target_pace")
        offset = int(number(values.get("timezone_offset", 0), "timezone_offset", -840, 840))
        start = timestamp(str(values["start_time"]), offset) if values.get("start_time") else None
        hr_low = int(number(values.get("min_hr", values.get("base_hr", 135)), "min_hr", 30, 240))
        hr_high = int(number(values.get("max_hr", 165), "max_hr", 30, 240))
        cad_low = int(number(values.get("min_cadence", values.get("base_cadence", 70 if sport=="Cycling" else 100)), "min_cadence", 0, 240))
        cad_high = int(number(values.get("max_cadence", 95 if sport=="Cycling" else 140), "max_cadence", 0, 240))
        power_low = int(number(values.get("base_power", values.get("min_power", 150)), "base_power", 0, 1500))
        power_high = int(number(values.get("max_power", 300), "max_power", 0, 1500))
        for lo, hi, field in [(hr_low, hr_high, "max_hr"), (cad_low, cad_high, "max_cadence"),
                              (power_low, power_high, "max_power")]:
            if lo > hi:
                raise ConversionError("最大值不能小于最小值。", field)
        return cls(sport, mode, seconds, start,
                   str(values.get("simulate_metrics", "true")).lower() in {"1", "true", "on"},
                   hr_low, hr_high, cad_low, cad_high, power_low, power_high,
                   number(values.get("weight", 70), "weight", 30, 250),
                   int(number(values.get("seed", 0), "seed", 0, 2**32-1)),
                   number(values.get("calories_per_km", 60), "calories_per_km", 0, 300))


@dataclass(slots=True)
class Point:
    lat: float
    lon: float
    segment: int
    time: datetime | None = None
    elevation: float | None = None
    hr: int | None = None
    cadence: int | None = None
    watts: int | None = None
    distance: float = 0.0
    speed: float = 0.0


def split_tag(tag):
    return tuple(tag[1:].split("}", 1)) if tag.startswith("{") else ("", tag)


def read_gpx(source, max_points=MAX_POINTS):
    size = len(source) if isinstance(source, bytes) else source.stat().st_size
    if size > MAX_BYTES:
        raise ConversionError("GPX 文件不能超过 16 MB。", "file")
    stream = io.BytesIO(source) if isinstance(source, bytes) else source
    points, stack = [], []
    segment, namespace = 0, ""
    try:
        for event, element in SafeET.iterparse(stream, events=("start", "end"),
                                              forbid_dtd=True, forbid_entities=True, forbid_external=True):
            ns, name = split_tag(element.tag)
            if event == "start":
                if not stack:
                    if name != "gpx" or ns not in GPX_NAMESPACES:
                        raise ConversionError("请选择 GPX 1.0 或 1.1 轨迹文件。", "file")
                    namespace = ns
                stack.append(element)
                if len(stack) > 64:
                    raise ConversionError("XML 嵌套过深。", "file")
                if ns == namespace and name in {"trkseg", "rte"}:
                    segment += 1
                continue
            parent_name = split_tag(stack[-2].tag)[1] if len(stack) > 1 else ""
            if ns == namespace and ((name == "trkpt" and parent_name == "trkseg") or
                                    (name == "rtept" and parent_name == "rte")):
                if len(points) >= max_points:
                    raise ConversionError(f"轨迹点不能超过 {max_points:,} 个。", "file")
                p = Point(number(element.get("lat"), "latitude", -90, 90),
                          number(element.get("lon"), "longitude", -180, 180), segment)
                for child in element:
                    child_ns, child_name = split_tag(child.tag)
                    if child_ns == namespace and child_name == "time" and child.text:
                        p.time = timestamp(child.text)
                    elif child_ns == namespace and child_name == "ele" and child.text:
                        p.elevation = number(child.text, "elevation", -12000, 100000)
                    elif child_ns == namespace and child_name == "extensions":
                        for metric in child.iter():
                            mns, mname = split_tag(metric.tag)
                            if mns not in EXT_NAMESPACES or not metric.text:
                                continue
                            if mname == "hr":
                                p.hr = int(number(metric.text, "heart_rate", 0, 255))
                            elif mname == "cad":
                                p.cadence = int(number(metric.text, "cadence", 0, 254))
                            elif mname in {"power", "watts", "PowerInWatts"}:
                                p.watts = int(number(metric.text, "power", 0, 65535))
                points.append(p)
                stack[-2].remove(element)
                element.clear()
            elif ns == namespace and name in {"trkseg", "trk", "rte"} and len(stack) > 1:
                stack[-2].remove(element)
                element.clear()
            stack.pop()
    except (ET.ParseError, DefusedXmlException, OSError) as exc:
        raise ConversionError("GPX 无法解析；文件不能包含 DTD 或实体声明。", "file") from exc
    if not points:
        raise ConversionError("文件没有有效轨迹点，请上传包含 trkpt 或 rtept 的 GPX。", "file")
    return points


def haversine(a, b):
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    h = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(math.radians(b.lon-a.lon)/2)**2
    return 6371008.8 * 2 * math.asin(math.sqrt(min(1.0, max(0.0, h))))


def summary(points):
    times = [p.time for p in points if p.time is not None]
    duration = max(0.0, (max(times)-min(times)).total_seconds()) if times else None
    distance = sum(haversine(a, b) for a, b in zip(points, points[1:]) if a.segment == b.segment)
    ascent = sum(max(0, b.elevation-a.elevation) for a, b in zip(points, points[1:])
                 if a.segment == b.segment and a.elevation is not None and b.elevation is not None)
    stride = max(1, math.ceil(len(points)/1000))
    route = [[p.lat, p.lon, p.segment] for i, p in enumerate(points)
             if i % stride == 0 or i == len(points)-1 or (i and points[i-1].segment != p.segment)]
    return {"points": len(points), "segments": len({p.segment for p in points}),
            "distance_m": distance, "duration_s": duration, "ascent_m": ascent,
            "start_time": iso(min(times)) if times else None,
            "missing_times": sum(p.time is None for p in points), "route": route[:2200]}


def prepare(points, config):
    if config.time_mode == "preserve" and any(p.time is None for p in points):
        raise ConversionError("轨迹缺少时间；请切换为按配速生成，并设置开始时间。", "time_mode")
    first_time = points[0].time
    start = config.start_time or first_time
    if start is None:
        raise ConversionError("没有可用时间，请设置开始时间。", "start_time")
    shift = config.start_time-first_time if config.start_time and first_time else timedelta(0)
    elapsed, distance = 0.0, 0.0
    rng, previous = random.Random(config.seed), None
    for p in points:
        step = haversine(previous, p) if previous and previous.segment == p.segment else 0.0
        distance += step
        if config.time_mode == "pace":
            elapsed += step * config.target_pace/1000
            p.time = start + timedelta(seconds=elapsed)
        else:
            p.time += shift
        p.distance = distance
        if previous:
            dt = (p.time-previous.time).total_seconds()
            if dt < 0:
                raise ConversionError("轨迹时间倒序；请修正 GPX 或选择按配速生成。", "time_mode")
            p.speed = step/dt if dt > 0 else 0.0
        if config.simulate_metrics:
            if p.hr is None:
                p.hr = rng.randint(config.min_hr, config.max_hr)
            if p.cadence is None:
                total = rng.randint(config.min_cadence, config.max_cadence)
                p.cadence = total if config.activity_type == "Cycling" else round(total/2)
            if p.watts is None:
                p.watts = min(config.max_power, round(config.base_power * config.weight/70 * rng.uniform(.95, 1.05)))
        previous = p


def node(parent, name, value=None, namespace=TCX, **attributes):
    child = ET.SubElement(parent, f"{{{namespace}}}{name}", attributes)
    if value is not None:
        child.text = str(value)
    return child


def tcx_bytes(points, config):
    root = ET.Element(f"{{{TCX}}}TrainingCenterDatabase")
    sport = "Running" if config.activity_type.startswith("Running") else "Biking" if config.activity_type == "Cycling" else "Other"
    activity = node(node(root, "Activities"), "Activity", Sport=sport)
    node(activity, "Id", iso(points[0].time))
    lap = node(activity, "Lap", StartTime=iso(points[0].time))
    duration = (points[-1].time-points[0].time).total_seconds()
    node(lap, "TotalTimeSeconds", f"{duration:.3f}")
    node(lap, "DistanceMeters", f"{points[-1].distance:.3f}")
    node(lap, "MaximumSpeed", f"{max(p.speed for p in points):.6f}")
    calories = round(points[-1].distance / 1000 * config.calories_per_km * config.weight / 70) if config.simulate_metrics else 0
    node(lap, "Calories", min(65535, calories))
    hrs = [p.hr for p in points if p.hr is not None]
    cadences = [p.cadence for p in points if p.cadence is not None]
    watts = [p.watts for p in points if p.watts is not None]
    if hrs:
        node(node(lap, "AverageHeartRateBpm"), "Value", round(sum(hrs)/len(hrs)))
        node(node(lap, "MaximumHeartRateBpm"), "Value", max(hrs))
    node(lap, "Intensity", "Active")
    if cadences and sport == "Biking":
        node(lap, "Cadence", round(sum(cadences)/len(cadences)))
    node(lap, "TriggerMethod", "Manual")
    previous_segment = track = None
    for p in points:
        if p.segment != previous_segment:
            track = node(lap, "Track")
            previous_segment = p.segment
        tp = node(track, "Trackpoint")
        node(tp, "Time", iso(p.time))
        pos = node(tp, "Position")
        node(pos, "LatitudeDegrees", p.lat)
        node(pos, "LongitudeDegrees", p.lon)
        if p.elevation is not None:
            node(tp, "AltitudeMeters", p.elevation)
        node(tp, "DistanceMeters", f"{p.distance:.3f}")
        if p.hr is not None:
            node(node(tp, "HeartRateBpm"), "Value", p.hr)
        if p.cadence is not None and sport == "Biking":
            node(tp, "Cadence", p.cadence)
        tpx = node(node(tp, "Extensions"), "TPX", namespace=AX)
        node(tpx, "Speed", f"{p.speed:.6f}", namespace=AX)
        if p.cadence is not None and sport != "Biking":
            node(tpx, "RunCadence", p.cadence, namespace=AX)
        if p.watts is not None:
            node(tpx, "Watts", p.watts, namespace=AX)
    lx = node(node(lap, "Extensions"), "LX", namespace=AX)
    node(lx, "AvgSpeed", f"{points[-1].distance/duration if duration > 0 else 0:.6f}", namespace=AX)
    if cadences:
        if sport == "Biking":
            node(lx, "MaxBikeCadence", max(cadences), namespace=AX)
        else:
            node(lx, "AvgRunCadence", round(sum(cadences)/len(cadences)), namespace=AX)
            node(lx, "MaxRunCadence", max(cadences), namespace=AX)
    if watts:
        node(lx, "AvgWatts", round(sum(watts)/len(watts)), namespace=AX)
        node(lx, "MaxWatts", max(watts), namespace=AX)
    note = f"Converted from GPX; activity={config.activity_type}."
    note += " Calories estimated from distance, configured kcal/km and weight." if config.simulate_metrics else " Calories unavailable (0)."
    if config.time_mode == "pace":
        note += " Timestamps generated from target pace."
    if config.simulate_metrics:
        note += " Missing HR/cadence/power filled with SIMULATED values; not sensor measurements."
    node(activity, "Notes", note)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def convert(source, destination: Path, config: Config, progress=lambda value: None):
    points = read_gpx(source)
    original = summary(points)
    progress(35)
    prepare(points, config)
    progress(65)
    data = tcx_bytes(points, config)
    temporary = destination.with_suffix(".part")
    try:
        temporary.write_bytes(data)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    result = summary(points)
    result.update(source=original, simulated=config.simulate_metrics,
                  generated_times=config.time_mode == "pace", size_bytes=len(data))
    progress(95)
    return result
