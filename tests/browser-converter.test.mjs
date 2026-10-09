import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {configuration,readGpx,summary,convert} from '../static/browser-converter.mjs';
const fixture=fs.readFileSync(new URL('./fixtures/track.gpx',import.meta.url),'utf8');
const root=points=>`<gpx><trk><trkseg>${points}</trkseg></trk></gpx>`;
const point=(lat=1,lon=2,time='2025-01-01T00:00:00Z')=>`<trkpt lon='${lon}' lat='${lat}'>${time?'<time>'+time+'</time>':''}</trkpt>`;
test('namespace, attribute order, quotes, self-closing route points',()=>{
  const xml='<g:gpx xmlns:g="http://www.topografix.com/GPX/1/1"><g:rte><g:rtept lon="2" lat="1"/><g:rtept lat="1.001" lon="2"/></g:rte></g:gpx>';
  assert.equal(readGpx(xml).length,2);assert.ok(summary(readGpx(xml)).distance_m>100);
});
test('default simulation is deterministic and enabled; source dates remain',()=>{
  const a=convert(fixture),b=convert(fixture);assert.deepEqual(a.data,b.data);
  assert.equal(a.result.simulated,true);assert.match(new TextDecoder().decode(a.data),/SIMULATED/);
  assert.equal(a.result.start_time,'2025-01-01T08:00:00.000Z');
});
test('simulation off emits no missing sensor measurements',()=>{
  const xml=new TextDecoder().decode(convert(fixture,{simulate_metrics:false}).data);
  assert.doesNotMatch(xml,/HeartRateBpm|RunCadence|Watts|SIMULATED/);assert.match(xml,/<Calories>0<\/Calories>/);
});
test('recorded Garmin sensors take priority, including zero values',()=>{
  const xml=root('<trkpt lat="1" lon="2"><time>2025-01-01T00:00:00Z</time><extensions><t:TrackPointExtension xmlns:t="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"><t:hr>123</t:hr><t:cad>0</t:cad><t:power>0</t:power></t:TrackPointExtension></extensions></trkpt>');
  const tcx=new TextDecoder().decode(convert(xml).data);assert.match(tcx,/<Value>123<\/Value>/);assert.match(tcx,/<ae:RunCadence>0<\/ae:RunCadence>/);assert.match(tcx,/<ae:Watts>0<\/ae:Watts>/);
});
test('segments remain separate with no joining distance or speed',()=>{
  const xml=`<gpx><trk><trkseg>${point()}</trkseg><trkseg>${point(50,60,'2025-01-01T00:00:30Z')}</trkseg></trk></gpx>`;
  const result=convert(xml);assert.equal(result.result.distance_m,0);assert.equal(result.result.segments,2);
  assert.equal((new TextDecoder().decode(result.data).match(/<Track>/g)||[]).length,2);
});
test('custom timezone, explicit timezone and naive UTC',()=>{
  assert.equal(convert(fixture,{start_time:'2025-07-01T12:00',timezone_offset:240}).result.start_time,'2025-07-01T16:00:00.000Z');
  assert.equal(convert(fixture,{start_time:'2025-07-01T12:00:00+08:00',timezone_offset:240}).result.start_time,'2025-07-01T04:00:00.000Z');
  assert.equal(convert(root(point(1,2,'2025-01-01T12:00:00'))).result.start_time,'2025-01-01T12:00:00.000Z');
});
test('missing time requires pace and explicit start; stationary and single point remain valid',()=>{
  const missing=root(point(1,2,null));assert.throws(()=>convert(missing),/缺少时间/);
  assert.throws(()=>convert(missing,{time_mode:'pace'}),/开始时间/);
  assert.equal(convert(missing,{time_mode:'pace',start_time:'2025-01-01T00:00'}).result.duration_s,0);
});
test('reversed source timestamps rejected',()=>assert.throws(()=>convert(root(point()+point(1.01,2,'2024-12-31T23:59:59Z'))),/时间倒序/));
test('running cadence is halved; cycling is RPM; weight changes power and calories',()=>{
  const cfg={min_cadence:120,max_cadence:120,min_hr:150,max_hr:150,weight:140};
  const run=new TextDecoder().decode(convert(fixture,cfg).data),cycle=new TextDecoder().decode(convert(fixture,{...cfg,activity_type:'Cycling'}).data);
  assert.match(run,/<ae:RunCadence>60<\/ae:RunCadence>/);assert.match(cycle,/<Cadence>120<\/Cadence>/);
  assert.match(run,/<ae:Watts>2\d\d<\/ae:Watts>|<ae:Watts>300<\/ae:Watts>/);
  const base=new TextDecoder().decode(convert(fixture).data);
  assert.ok(+/<Calories>(\d+)/.exec(run)[1]>+/<Calories>(\d+)/.exec(base)[1]);
});
const invalidXml=[['DTD','<!DOCTYPE gpx [<!ENTITY x "secret">]><gpx/>'],['bad entity',root(point().replace('<time>','<time>&x;'))],
  ['mismatched tags','<gpx><trk></gpx>'],['duplicate attributes','<gpx><rte><rtept lat="1" lat="2" lon="3"/></rte></gpx>'],
  ['unsupported namespace','<gpx xmlns="https://other.example"><rte><rtept lat="1" lon="2"/></rte></gpx>'],
  ['not GPX','<other/>'],['empty','<gpx/>'],['empty latitude',root(point('',2))],['infinite latitude',root(point('Infinity',2))],
  ['latitude bounds',root(point(91,2))],['longitude bounds',root(point(1,181))],['invalid date',root(point(1,2,'2025-02-30T00:00:00Z'))],
  ['zero year',root(point(1,2,'0000-01-01T00:00:00Z'))],['hex latitude',root(point('0x10',2))],
  ['nesting','<gpx>'+('<x>'.repeat(65))+('</x>'.repeat(65))+'</gpx>']];
for(const [name,xml] of invalidXml)test('reject '+name,()=>assert.throws(()=>readGpx(xml)));
const invalidConfig=[['pace seconds',{target_pace:'5:99'}],['short pace',{target_pace:'0:59'}],['long pace',{target_pace:'61:00'}],
  ['sport',{activity_type:'Fake'}],['time mode',{time_mode:'today'}],['heart bounds',{min_hr:200,max_hr:100}],['cadence bounds',{min_cadence:200,max_cadence:100}],
  ['power bounds',{base_power:400,max_power:100}],['infinite power',{base_power:'Infinity'}],['invalid weight',{weight:0}],['negative seed',{seed:-1}],
  ['bad offset',{timezone_offset:900}],['bad start',{start_time:'garbage'}]];
for(const [name,config] of invalidConfig)test('validate '+name,()=>assert.throws(()=>configuration(config)));
test('point and byte limits',()=>{assert.throws(()=>readGpx(root(point()+point()),1),/轨迹点/);assert.throws(()=>readGpx(' '.repeat(16*1024*1024+1)),/16 MB/);});
test('exported summaries agree with the last trackpoint and maximum speed',()=>{
  const {data,result}=convert(fixture);const xml=new TextDecoder().decode(data);
  assert.equal(+/<TotalTimeSeconds>([^<]+)/.exec(xml)[1],result.duration_s);
  assert.ok(Math.abs(+/<DistanceMeters>([^<]+)/.exec(xml)[1]-result.distance_m)<.001);
});
test('write synthetic exports for official XSD and Python semantic parity checks',()=>{
  const sensor=root('<trkpt lat="1" lon="2"><time>2025-01-01T00:00:00Z</time><extensions><x:TrackPointExtension xmlns:x="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"><x:hr>120</x:hr><x:cad>80</x:cad><x:power>200</x:power></x:TrackPointExtension></extensions></trkpt>');
  const cases=[{name:'plain',xml:fixture,config:{simulate_metrics:false}},{name:'default',xml:fixture,config:{}},
    {name:'cycling',xml:fixture,config:{activity_type:'Cycling'}},{name:'walking',xml:fixture,config:{activity_type:'Walking'}},
    {name:'pace',xml:fixture,config:{time_mode:'pace',start_time:'2025-07-01T12:00',timezone_offset:240}},
    {name:'sensor',xml:sensor,config:{simulate_metrics:false}}];
  const output=path.resolve(process.env.TEST_ARTIFACTS||'test-artifacts/converter');fs.mkdirSync(output,{recursive:true});
  for(const item of cases){const result=convert(item.xml,item.config);fs.writeFileSync(path.join(output,item.name+'.tcx'),result.data);item.result=result.result;}
  fs.writeFileSync(path.join(output,'parity.json'),JSON.stringify(cases));
});
