import io
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
import web_app

def upload(client,gpx,**config):
    return client.post('/upload',data={'file':(io.BytesIO(gpx),'测试轨迹.gpx'),**config})

def wait(client,task):
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        result=client.get('/status/'+task).get_json()
        if result['status'] in {'completed','error','cancelled'}: return result
        time.sleep(.01)
    raise AssertionError('Conversion did not finish')

def test_real_upload_preview_status_download(client,app,gpx):
    preview=client.post('/preview',data={'file':(io.BytesIO(gpx),'track.gpx')})
    assert preview.status_code==200 and preview.json['duration_s']==60
    response=upload(client,gpx)
    assert response.status_code==202
    task=response.json['task_id']; result=wait(client,task)
    assert result['status']=='completed' and result['result']['simulated']
    download=client.get('/download/'+task)
    assert download.status_code==200 and b'TrainingCenterDatabase' in download.data
    assert '%E6%B5%8B' in download.headers['Content-Disposition']
    download.close()
    assert not list(Path(app.config['DATA_DIR']).glob('*.gpx'))
    assert client.delete('/tasks/'+task).status_code==200
    assert client.get('/download/'+task).status_code==404
    assert not list(Path(app.config['DATA_DIR']).glob('*.tcx'))

def test_download_and_status_owned_by_session(client,app,gpx):
    task=upload(client,gpx).json['task_id'];wait(client,task)
    other=app.test_client()
    for url in ['/status/','/download/']:
        assert other.get(url+task).status_code==404
    assert other.delete('/tasks/'+task).status_code==404

def test_persistent_status_across_app_instances(client,app,gpx):
    task=upload(client,gpx).json['task_id'];wait(client,task)
    second=web_app.create_app(dict(app.config))
    try:
        other=second.test_client();cookie=client.get_cookie('session')
        other.set_cookie('session',cookie.value)
        assert other.get('/status/'+task).json['status']=='completed'
    finally:
        second.extensions['executor'].shutdown(wait=True)

@pytest.mark.parametrize('data',[{}, {'file':(io.BytesIO(b'x'),'a.txt')}, {'file':(io.BytesIO(b''),'a.gpx')}])
def test_invalid_preview_upload(client,data):
    assert client.post('/preview',data=data).status_code==400

def test_bad_xml_reports_job_error_and_removes_source(client,app):
    task=upload(client,b'not xml').json['task_id']
    assert wait(client,task)['status']=='error'
    app.extensions['executor'].shutdown(wait=True)
    assert not list(Path(app.config['DATA_DIR']).glob('*.gpx'))

def test_oversized_is_413(client):
    response=upload(client,b'x'*(16*1024*1024+1))
    assert response.status_code==413 and response.is_json

@pytest.mark.parametrize('config',[{'base_power':'inf'},{'target_pace':'5:99'},{'min_hr':200,'max_hr':100}])
def test_invalid_configuration_does_not_enqueue(client,gpx,config):
    response=upload(client,gpx,**config)
    assert response.status_code==400 and response.json['field']

def test_queue_bounded_even_when_cancelled(client,app,gpx,monkeypatch):
    entered,release=threading.Event(),threading.Event();original=web_app.convert
    def blocked(*args,**kw):
        entered.set();release.wait(5);return original(*args,**kw)
    monkeypatch.setattr(web_app,'convert',blocked)
    first=upload(client,gpx).json['task_id'];assert entered.wait(2)
    second=upload(client,gpx).json['task_id']
    assert client.delete('/tasks/'+first).status_code==200
    assert client.delete('/tasks/'+second).status_code==200
    full=upload(client,gpx)
    assert full.status_code==503 and full.headers['Retry-After']=='5'
    release.set();app.extensions['executor'].shutdown(wait=True)
    assert not list(Path(app.config['DATA_DIR']).glob('*.tcx'))

def test_expiry_and_orphan_cleanup(client,app,gpx):
    task=upload(client,gpx).json['task_id'];wait(client,task)
    with sqlite3.connect(app.extensions['database']) as con:
        con.execute('UPDATE jobs SET expires=0 WHERE id=?',(task,))
    assert client.get('/download/'+task).status_code==404
    orphan=Path(app.config['DATA_DIR'])/'orphan.part';orphan.write_text('partial')
    # Cleanup is throttled; exercise a fresh instance sharing the persistent directory.
    second=web_app.create_app(dict(app.config))
    try:
        second.extensions['cleanup']()
        assert not orphan.exists() and not (Path(app.config['DATA_DIR'])/(task+'.tcx')).exists()
    finally: second.extensions['executor'].shutdown(wait=True)

def test_origin_and_security_headers(client,gpx):
    assert client.post('/upload',headers={'Origin':'https://other.example'},data={'file':(io.BytesIO(gpx),'a.gpx')}).status_code==403
    response=client.get('/')
    assert "script-src 'self'" in response.headers['Content-Security-Policy']
    assert response.headers['X-Content-Type-Options']=='nosniff'
    assert '<script>' not in response.text and 'onclick=' not in response.text

def test_health_does_not_sample_cpu(client):
    started=time.perf_counter();assert client.get('/health').status_code==200
    assert time.perf_counter()-started<.2

def test_weather_true_cache_and_unavailable(client,app):
    calls=[]
    def provider(url):
        calls.append(url)
        return {'current':{'time':'2025-01-01T00:00','temperature_2m':20,'relative_humidity_2m':60,'wind_speed_10m':12,'weather_code':1}}
    app.extensions['weather_provider']=provider
    one=client.get('/api/weather?lat=31.2&lon=121.4');two=client.get('/api/weather?lat=31.2&lon=121.4')
    assert one.status_code==200 and not one.json['cached'] and two.json['cached']
    assert one.json['source']=='Open-Meteo' and len(calls)==1
    def offline(url): raise OSError('offline')
    app.extensions['weather_provider']=offline
    failed=client.get('/api/weather?lat=0&lon=0')
    assert failed.status_code==503 and not failed.json['available'] and 'temperature' not in failed.json

@pytest.mark.parametrize('query',['lat=nan&lon=1','lat=91&lon=1','lat=1&lon=inf','lat=1'])
def test_weather_coordinate_validation(client,query):
    assert client.get('/api/weather?'+query).status_code==400

def test_analytics_private_bounded_and_no_personal_data(client,app,gpx):
    assert client.get('/api/analytics/stats').status_code==401
    assert client.delete('/api/analytics/stats').status_code==401
    assert client.post('/api/analytics',json={'event':'conversion_completed'}).status_code==400
    assert client.post('/api/analytics',json=[]).status_code==400
    for _ in range(3): assert client.post('/api/analytics',json={'event':'page_view','filename':'not retained','coordinates':[1,2]}).status_code==204
    task=upload(client,gpx).json['task_id'];wait(client,task)
    response=client.get('/api/analytics/stats',headers={'Authorization':'Bearer test-admin'})
    assert response.status_code==200
    counts={event['event']:event['count'] for event in response.json['events']}
    assert counts['page_view']==3 and counts['conversion_completed']==1
    assert response.json['visitors'][0]['count']==1
    assert 'not retained' not in response.text and 'coordinates' not in response.text
    assert client.delete('/api/analytics/stats',headers={'Authorization':'Bearer test-admin'}).status_code==204

def test_analytics_rate_limit(client):
    for _ in range(12):assert client.post('/api/analytics',json={'event':'page_view'}).status_code==204
    assert client.post('/api/analytics',json={'event':'page_view'}).status_code==429

@pytest.mark.parametrize('trigger', ['cleanup', 'stats', 'record'])
def test_analytics_retention_includes_exactly_thirty_utc_dates(client, app, trigger):
    today = datetime.now(timezone.utc).date()
    oldest = (today-timedelta(days=29)).isoformat()
    expired = (today-timedelta(days=30)).isoformat()
    with sqlite3.connect(app.extensions['database']) as con:
        for day in (oldest, expired):
            con.execute('INSERT INTO events VALUES (?, ?, 1)', (day, 'page_view'))
            con.execute('INSERT INTO visitors VALUES (?, ?)', (day, 'anonymous'))
    if trigger == 'cleanup':
        app.extensions['cleanup']()
    elif trigger == 'stats':
        response = client.get('/api/analytics/stats', headers={'Authorization': 'Bearer test-admin'})
        assert response.status_code == 200
        assert all(row['day'] != expired for key in ('events', 'visitors') for row in response.json[key])
    else:
        assert client.post('/api/analytics', json={'event': 'page_view'}).status_code == 204
    with sqlite3.connect(app.extensions['database']) as con:
        for table in ('events', 'visitors'):
            days = {row[0] for row in con.execute('SELECT day FROM '+table)}
            assert oldest in days and expired not in days

def test_convert_alias_uses_configuration(client,gpx):
    response=client.post('/convert',data={'file':(io.BytesIO(gpx),'a.gpx'),'simulate_metrics':'false','start_time':'2025-07-01T12:00:00','timezone_offset':-480})
    result=wait(client,response.json['task_id'])
    assert result['result']['start_time']=='2025-07-01T04:00:00.000Z' and not result['result']['simulated']
