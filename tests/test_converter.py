from datetime import timedelta
from pathlib import Path
import math
import xml.etree.ElementTree as ET
import pytest
from lxml import etree
from gpx_to_tcx import Config, ConversionError, TCX, AX, convert, read_gpx, prepare, summary, tcx_bytes

NS={'t':TCX,'a':AX}

def result(gpx, config=Config()):
    points=read_gpx(gpx); prepare(points,config)
    return ET.fromstring(tcx_bytes(points,config))

def values(root, xpath):
    return [float(node.text) for node in root.findall(xpath,NS)]

@pytest.mark.parametrize('body', [
    "<trkpt lat='31' lon='121'/>", '<trkpt lon="121" lat="31"></trkpt>',
    '<trkpt\n lon="121"\n lat="31" />', '<p:trkpt lon="121" lat="31"/>'])
def test_attribute_order_quotes_self_closing_namespace(body):
    points=read_gpx(f'<gpx xmlns:p="http://www.topografix.com/GPX/1/1" xmlns="http://www.topografix.com/GPX/1/1"><trk><trkseg>{body}</trkseg></trk></gpx>'.encode())
    assert len(points)==1 and points[0].lat==31

def test_route_points():
    assert len(read_gpx(b'<gpx><rte><rtept lat="1" lon="2"/></rte></gpx>'))==1

@pytest.mark.parametrize('data', [b'',b'<not-gpx/>', b'<gpx><trk/></gpx>',
    b'<!DOCTYPE gpx [<!ENTITY x "a">]><gpx>&x;</gpx>',
    b'<gpx><trk><trkseg><trkpt lat="NaN" lon="1"/></trkseg></trk></gpx>',
    b'<gpx><trk><trkseg><trkpt lat="91" lon="1"/></trkseg></trk></gpx>'])
def test_invalid_gpx_rejected(data):
    with pytest.raises(ConversionError): read_gpx(data)

def test_point_limit(gpx):
    with pytest.raises(ConversionError): read_gpx(gpx,max_points=2)

@pytest.mark.parametrize('pace',['5:99','-1:30','nan','inf','0:00','100:00','5.5'])
def test_invalid_pace(pace):
    with pytest.raises(ConversionError): Config.from_mapping({'target_pace':pace})

@pytest.mark.parametrize('config',[{'base_hr':'inf'},{'weight':'NaN'},{'max_hr':'-1'},
    {'min_hr':200,'max_hr':100},{'base_power':500,'max_power':100},
    {'activity_type':'Running & Other'},{'time_mode':'invent'}, {'timezone_offset':10000}])
def test_invalid_configuration(config):
    with pytest.raises(ConversionError): Config.from_mapping(config)

def test_default_simulation_and_date_preserved(gpx):
    cfg=Config.from_mapping({}); assert cfg.simulate_metrics
    tree=result(gpx,cfg)
    assert tree.find('.//t:Id',NS).text=='2025-01-01T08:00:00.000Z'
    assert values(tree,'.//t:TotalTimeSeconds')==[60]
    assert len(values(tree,'.//t:Trackpoint/t:HeartRateBpm/t:Value'))==3
    assert 'SIMULATED' in tree.find('.//t:Notes',NS).text

def test_explicit_simulation_off(gpx):
    tree=result(gpx,Config.from_mapping({'simulate_metrics':'false'}))
    assert not tree.findall('.//t:HeartRateBpm',NS)
    assert not tree.findall('.//a:Watts',NS)
    assert values(tree,'.//t:Calories')==[0]

@pytest.mark.parametrize('offset,expected', [(-480,'2025-07-01T04:00:00.000Z'),(240,'2025-07-01T16:00:00.000Z')])
def test_start_time_offsets(gpx,offset,expected):
    tree=result(gpx,Config.from_mapping({'start_time':'2025-07-01T12:00:00','timezone_offset':offset}))
    assert tree.find('.//t:Id',NS).text==expected
    assert values(tree,'.//t:TotalTimeSeconds')==[60]

def test_offset_iso_is_authoritative(gpx):
    tree=result(gpx,Config.from_mapping({'start_time':'2025-07-01T12:00:00+09:00','timezone_offset':240}))
    assert tree.find('.//t:Id',NS).text=='2025-07-01T03:00:00.000Z'

def test_preview_includes_first_timestamp(gpx):
    data=summary(read_gpx(gpx))
    assert data['duration_s']==60 and data['ascent_m']==5 and data['points']==3

def test_stationary_and_single_point(gpx):
    stationary=gpx.replace(b'31.2005',b'31.2000').replace(b'31.2010',b'31.2000').replace(b'121.4005',b'121.4000').replace(b'121.4010',b'121.4000')
    tree=result(stationary)
    assert values(tree,'.//t:DistanceMeters')==[0,0,0,0]
    assert values(tree,'.//t:TotalTimeSeconds')==[60]
    single=b'<gpx><trk><trkseg><trkpt lat="1" lon="2"><time>2025-01-01T00:00:00Z</time></trkpt></trkseg></trk></gpx>'
    assert values(result(single),'.//t:TotalTimeSeconds')==[0]

def test_segments_do_not_bridge_gaps():
    data=b'<gpx><trk><trkseg><trkpt lat="1" lon="1"><time>2025-01-01T00:00:00Z</time></trkpt></trkseg><trkseg><trkpt lat="80" lon="80"><time>2025-01-01T00:01:00Z</time></trkpt></trkseg></trk></gpx>'
    tree=result(data)
    assert values(tree,'.//t:Lap/t:DistanceMeters')==[0]
    assert len(tree.findall('.//t:Track',NS))==2

def test_missing_and_reversed_times(gpx):
    missing=b'<gpx><trk><trkseg><trkpt lat="1" lon="2"/></trkseg></trk></gpx>'
    with pytest.raises(ConversionError): result(missing)
    tree=result(missing,Config.from_mapping({'time_mode':'pace','start_time':'2025-01-01T00:00:00Z'}))
    assert values(tree,'.//t:TotalTimeSeconds')==[0]
    reverse=gpx.replace(b'08:01:00',b'07:59:00')
    with pytest.raises(ConversionError): result(reverse)

def test_pace_changes_time_not_coordinates(gpx):
    tree=result(gpx,Config.from_mapping({'time_mode':'pace','target_pace':'5:00'}))
    distance=values(tree,'.//t:Lap/t:DistanceMeters')[0]
    assert math.isclose(values(tree,'.//t:TotalTimeSeconds')[0],distance*.3,abs_tol=.002)
    assert values(tree,'.//t:LatitudeDegrees')==[31.2,31.2005,31.201]

def test_summary_matches_trackpoints_and_deterministic(gpx):
    tree=result(gpx); second=result(gpx)
    assert ET.tostring(tree)==ET.tostring(second)
    hrs=values(tree,'.//t:Trackpoint/t:HeartRateBpm/t:Value')
    watts=values(tree,'.//a:TPX/a:Watts')
    cad=values(tree,'.//a:RunCadence')
    assert values(tree,'.//t:AverageHeartRateBpm/t:Value')==[round(sum(hrs)/len(hrs))]
    assert values(tree,'.//t:MaximumHeartRateBpm/t:Value')==[max(hrs)]
    assert values(tree,'.//a:AvgWatts')==[round(sum(watts)/len(watts))]
    assert values(tree,'.//a:MaxWatts')==[max(watts)]
    assert values(tree,'.//a:MaxRunCadence')==[max(cad)]

def test_power_weight_and_calories_change_output(gpx):
    low=result(gpx,Config.from_mapping({'base_power':150,'weight':70,'calories_per_km':60}))
    high=result(gpx,Config.from_mapping({'base_power':250,'weight':90,'calories_per_km':100,'max_power':1000}))
    assert values(high,'.//a:AvgWatts')[0]>values(low,'.//a:AvgWatts')[0]
    assert values(high,'.//t:Calories')[0]>values(low,'.//t:Calories')[0]

def test_recorded_metrics_win(gpx):
    extension=b'<extensions><gpxtpx:TrackPointExtension xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"><gpxtpx:hr>155</gpxtpx:hr><gpxtpx:cad>90</gpxtpx:cad></gpxtpx:TrackPointExtension></extensions>'
    data=gpx.replace(b'</trkpt>',extension+b'</trkpt>')
    tree=result(data)
    assert values(tree,'.//t:Trackpoint/t:HeartRateBpm/t:Value')==[155]*3
    assert values(tree,'.//a:RunCadence')==[90]*3

@pytest.mark.parametrize('sport,expected',[('Running_Trail','Running'),('Cycling','Biking'),('Walking','Other')])
def test_sport_and_official_schema(gpx,sport,expected):
    tree=result(gpx,Config.from_mapping({'activity_type':sport,'min_cadence':70,'max_cadence':90}))
    assert tree.find('.//t:Activity',NS).get('Sport')==expected
    document=etree.fromstring(ET.tostring(tree))
    directory=Path(__file__).parent/'schemas'
    schema=etree.XMLSchema(etree.parse(str(directory/'TrainingCenterDatabasev2.xsd')))
    schema.assertValid(document)
    extension_schema=etree.XMLSchema(etree.parse(str(directory/'ActivityExtensionv2.xsd')))
    for item in document.xpath('//a:TPX | //a:LX',namespaces={'a':AX}): extension_schema.assertValid(item)

def test_atomic_output(gpx,tmp_path):
    output=tmp_path/'test.tcx'
    data=convert(gpx,output,Config())
    assert output.is_file() and not output.with_suffix('.part').exists()
    assert data['source']['duration_s']==60 and data['simulated']
