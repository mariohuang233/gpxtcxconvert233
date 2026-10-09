"""Validate synthetic JS exports against official TCX schemas and Python semantics."""
import json
from pathlib import Path
import sys
from lxml import etree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gpx_to_tcx import Config, read_gpx, prepare, summary

folder=Path(sys.argv[1] if len(sys.argv)>1 else 'test-artifacts/converter')
schemas=Path(__file__).parent/'schemas'
schema=etree.XMLSchema(etree.parse(str(schemas/'TrainingCenterDatabasev2.xsd')))
for path in folder.glob('*.tcx'):
    document=etree.parse(str(path));schema.assertValid(document)
    extension_schema=etree.XMLSchema(etree.parse(str(schemas/'ActivityExtensionv2.xsd')))
    for extension in document.xpath('//*[namespace-uri()="http://www.garmin.com/xmlschemas/ActivityExtension/v2" and (local-name()="TPX" or local-name()="LX")]'):
        extension_schema.assertValid(etree.ElementTree(extension))
manifest=folder/'parity.json'
if manifest.exists():
    for case in json.loads(manifest.read_text(encoding='utf-8')):
        cfg=Config.from_mapping(case['config']);points=read_gpx(case['xml'].encode());prepare(points,cfg);expected=summary(points)
        actual=case['result']
        assert actual['points']==expected['points'] and actual['segments']==expected['segments'],case['name']
        assert abs(actual['distance_m']-expected['distance_m'])<.001,case['name']
        assert abs(actual['duration_s']-expected['duration_s'])<.002,case['name']
        assert actual['start_time']==expected['start_time'],case['name']
        doc=etree.parse(str(folder/(case['name']+'.tcx')))
        assert abs(float(doc.xpath('string(//*[local-name()="Lap"]/*[local-name()="DistanceMeters"])'))-expected['distance_m'])<.001
print('Official TCX/extension schemas and Python summary parity passed.')
