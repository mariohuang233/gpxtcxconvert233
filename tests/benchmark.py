"""Reproducible parser benchmark; no brittle wall-clock assertion in CI."""
import json
import sys
import time
import tracemalloc
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gpx_to_tcx import Config, convert, read_gpx
from tempfile import TemporaryDirectory

def fixture(count):
    return ('<gpx><trk><trkseg>'+''.join(f'<trkpt lat="31.2" lon="{121.4+i*.000001:.6f}"><time>2025-01-01T00:00:00Z</time></trkpt>' for i in range(count))+'</trkseg></trk></gpx>').encode()

rows=[]
for count in [1000,2000,4000,8000,16000]:
    data=fixture(count); samples=[]
    for _ in range(3):
        started=time.perf_counter();points=read_gpx(data);samples.append(time.perf_counter()-started)
    rows.append({'points':count,'best_seconds':round(min(samples),5),'bytes':len(data)})
with TemporaryDirectory() as directory:
    tracemalloc.start();started=time.perf_counter()
    convert(fixture(8000),Path(directory)/'track.tcx',Config())
    elapsed=time.perf_counter()-started;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
print(json.dumps({'parser':rows,'conversion_8000':{'seconds_with_tracemalloc':round(elapsed,4),'peak_mib':round(peak/1024**2,2)}},indent=2))
