// Pages conversion runs in a Worker. Saxes enforces namespace-aware XML well-formedness.
import { SaxesParser } from 'saxes';

export const MAX_BYTES = 16 * 1024 * 1024, MAX_POINTS = 100000;
const GPX = new Set(['', 'http://www.topografix.com/GPX/1/0', 'http://www.topografix.com/GPX/1/1']);
const EXT = new Set(['TrackPointExtension/v1','TrackPointExtension/v2','GpxExtensions/v3','PowerExtension/v1'].map(s=>'http://www.garmin.com/xmlschemas/'+s));
const SPORTS = new Set(['Running','Running_Street','Running_Trail','Running_Track','Running_Treadmill','Running_Indoor','Cycling','Walking','Hiking']);
const TCX='http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2', AX='http://www.garmin.com/xmlschemas/ActivityExtension/v2';
export class ConversionError extends Error {
  constructor(message, field='file') { super(message); this.field=field; }
}
function fail(message, field) { throw new ConversionError(message,field); }
function number(value, field, low, high) {
  if(value==null || !/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(String(value).trim()))fail(`${field} 必须是有效数字。`,field);
  const n=Number(value);
  if(!Number.isFinite(n)||n<low||n>high)fail(`${field} 必须在 ${low} 至 ${high} 之间。`,field);
  return n;
}
function round(n) { const floor=Math.floor(n); return n-floor===.5?floor+(floor%2):Math.round(n); }
function timestamp(value, deviceOffset=0) {
  const match=/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,6}))?)?(Z|[+-]\d{2}:?\d{2})?$/.exec(String(value).trim());
  if(!match)fail('时间格式无效，请重新选择开始时间。','start_time');
  const [,y,m,d,h,min,s='0',fraction='',zone]=match;
  const date=new Date(0); date.setUTCFullYear(+y,+m-1,+d);date.setUTCHours(+h,+min,+s,+fraction.padEnd(3,'0').slice(0,3));
  if(+y<1||date.getUTCFullYear()!==+y||date.getUTCMonth()!==+m-1||date.getUTCDate()!==+d||date.getUTCHours()!==+h||date.getUTCMinutes()!==+min||date.getUTCSeconds()!==+s)
    fail('时间格式无效，请重新选择开始时间。','start_time');
  let offset=deviceOffset;
  if(zone==='Z')offset=0;
  else if(zone){const digits=zone.slice(1).replace(':','');if(+digits.slice(2)>59||+digits.slice(0,2)>23)fail('时间时区无效。','start_time');offset=(+digits.slice(0,2)*60 + +digits.slice(2))*(zone[0]==='+'?-1:1);}
  return date.getTime()+offset*60000;
}
const iso=value=>new Date(value).toISOString();
export function configuration(v={}) {
  const sport=String(v.activity_type??'Running'),mode=String(v.time_mode??'preserve');
  if(!SPORTS.has(sport))fail('请选择支持的运动类型。','activity_type');
  if(!['preserve','pace'].includes(mode))fail('时间模式无效。','time_mode');
  const pace=/^(\d{1,2}):([0-5]\d)$/.exec(String(v.target_pace??'5:30'));
  if(!pace)fail('配速应为 分:秒，例如 5:30。','target_pace');
  const seconds=+pace[1]*60 + +pace[2];
  if(seconds<60||seconds>3600)fail('配速必须在 1:00 至 60:00 分/公里之间。','target_pace');
  const offset=Math.trunc(number(v.timezone_offset??0,'timezone_offset',-840,840));
  const cfg={activity_type:sport,time_mode:mode,target_pace:seconds,start_time:v.start_time?timestamp(v.start_time,offset):null,
    simulate_metrics:['1','true','on'].includes(String(v.simulate_metrics??'true').toLowerCase()),
    min_hr:Math.trunc(number(v.min_hr??v.base_hr??135,'min_hr',30,240)),max_hr:Math.trunc(number(v.max_hr??165,'max_hr',30,240)),
    min_cadence:Math.trunc(number(v.min_cadence??v.base_cadence??(sport==='Cycling'?70:100),'min_cadence',0,240)),
    max_cadence:Math.trunc(number(v.max_cadence??(sport==='Cycling'?95:140),'max_cadence',0,240)),
    base_power:Math.trunc(number(v.base_power??v.min_power??150,'base_power',0,1500)),max_power:Math.trunc(number(v.max_power??300,'max_power',0,1500)),
    weight:number(v.weight??70,'weight',30,250),seed:Math.trunc(number(v.seed??0,'seed',0,2**32-1)),
    calories_per_km:number(v.calories_per_km??60,'calories_per_km',0,300)};
  for(const [low,high] of [['min_hr','max_hr'],['min_cadence','max_cadence'],['base_power','max_power']])
    if(cfg[low]>cfg[high])fail('最大值不能小于最小值。',high);
  return cfg;
}
export function readGpx(xml, maxPoints=MAX_POINTS) {
  if(new TextEncoder().encode(xml).byteLength>MAX_BYTES)fail('GPX 文件不能超过 16 MB。');
  const parser=new SaxesParser({xmlns:true}), points=[],stack=[];
  let namespace='',segment=0,point=null,pointDepth=0;
  parser.on('doctype',()=>fail('GPX 文件不能包含 DTD 或实体声明。'));
  parser.on('error',()=>fail('GPX 无法解析；请检查 XML 格式。'));
  parser.on('opentag',tag=>{
    if(!stack.length){if(tag.local!=='gpx'||!GPX.has(tag.uri))fail('请选择 GPX 1.0 或 1.1 轨迹文件。');namespace=tag.uri;}
    const parent=stack.at(-1);
    stack.push({local:tag.local,uri:tag.uri,text:''});
    if(stack.length>64)fail('XML 嵌套过深。');
    if(tag.uri===namespace&&['trkseg','rte'].includes(tag.local))segment++;
    if(tag.uri===namespace&&parent?.uri===namespace&&((tag.local==='trkpt'&&parent.local==='trkseg')||(tag.local==='rtept'&&parent.local==='rte'))){
      if(points.length>=maxPoints)fail(`轨迹点不能超过 ${maxPoints.toLocaleString()} 个。`);
      point={lat:number(tag.attributes.lat?.value,'latitude',-90,90),lon:number(tag.attributes.lon?.value,'longitude',-180,180),
        segment,time:null,elevation:null,hr:null,cadence:null,watts:null,distance:0,speed:0};pointDepth=stack.length;
    }
  });
  const text=value=>{if(point)stack.at(-1).text+=value;};
  parser.on('text',text);parser.on('cdata',text);
  parser.on('closetag',()=>{
    const element=stack.at(-1),value=element.text.trim();
    if(point){
      if(stack.length===pointDepth+1&&element.uri===namespace&&value){
        if(element.local==='time')point.time=timestamp(value);
        if(element.local==='ele')point.elevation=number(value,'elevation',-12000,100000);
      }
      const extension=stack[pointDepth];
      if(stack.length>pointDepth+1&&extension?.local==='extensions'&&extension.uri===namespace&&EXT.has(element.uri)&&value){
        if(element.local==='hr')point.hr=Math.trunc(number(value,'heart_rate',0,255));
        if(element.local==='cad')point.cadence=Math.trunc(number(value,'cadence',0,254));
        if(['power','watts','PowerInWatts'].includes(element.local))point.watts=Math.trunc(number(value,'power',0,65535));
      }
      if(stack.length===pointDepth){points.push(point);point=null;}
    }
    stack.pop();
  });
  parser.write(xml).close();
  if(!points.length)fail('文件没有有效轨迹点，请上传包含 trkpt 或 rtept 的 GPX。');
  return points;
}
function haversine(a,b) {
  const rad=n=>n*Math.PI/180,la=rad(a.lat),lb=rad(b.lat);
  const h=Math.sin((lb-la)/2)**2 + Math.cos(la)*Math.cos(lb)*Math.sin(rad(b.lon-a.lon)/2)**2;
  return 6371008.8*2*Math.asin(Math.sqrt(Math.min(1,Math.max(0,h))));
}
export function summary(points) {
  let minTime=Infinity,maxTime=-Infinity,missing=0,distance=0,ascent=0;
  const segments=new Set(),route=[],stride=Math.max(1,Math.ceil(points.length/1000));
  points.forEach((p,i)=>{
    segments.add(p.segment);
    if(p.time==null)missing++;else{minTime=Math.min(minTime,p.time);maxTime=Math.max(maxTime,p.time);}
    const prev=points[i-1];
    if(prev?.segment===p.segment){distance+=haversine(prev,p);if(prev.elevation!=null&&p.elevation!=null)ascent+=Math.max(0,p.elevation-prev.elevation);}
    if(i%stride===0||i===points.length-1||(prev&&prev.segment!==p.segment))route.push([p.lat,p.lon,p.segment]);
  });
  return {points:points.length,segments:segments.size,distance_m:distance,duration_s:minTime===Infinity?null:Math.max(0,(maxTime-minTime)/1000),
    ascent_m:ascent,start_time:minTime===Infinity?null:iso(minTime),missing_times:missing,route:route.slice(0,2200)};
}
function random(seed) {
  let state=seed>>>0;
  return ()=>{state=(state+0x6D2B79F5)>>>0;let n=state;n=Math.imul(n^n>>>15,n|1);n^=n+Math.imul(n^n>>>7,n|61);return ((n^n>>>14)>>>0)/4294967296;};
}
function prepare(points,cfg) {
  if(cfg.time_mode==='preserve'&&points.some(p=>p.time==null))fail('轨迹缺少时间；请切换为按配速生成，并设置开始时间。','time_mode');
  const first=points[0].time,start=cfg.start_time??first;
  if(start==null)fail('没有可用时间，请设置开始时间。','start_time');
  const shift=cfg.start_time!=null&&first!=null?cfg.start_time-first:0,rng=random(cfg.seed);
  const randint=(low,high)=>low+Math.floor(rng()*(high-low+1));
  let elapsed=0,distance=0,previous=null;
  for(const p of points){
    const step=previous?.segment===p.segment?haversine(previous,p):0;distance+=step;
    if(cfg.time_mode==='pace'){elapsed+=step*cfg.target_pace;p.time=start+round(elapsed);}else p.time+=shift;
    p.distance=distance;
    if(previous){const dt=(p.time-previous.time)/1000;if(dt<0)fail('轨迹时间倒序；请修正 GPX 或选择按配速生成。','time_mode');p.speed=dt>0?step/dt:0;}
    if(cfg.simulate_metrics){
      if(p.hr==null)p.hr=randint(cfg.min_hr,cfg.max_hr);
      if(p.cadence==null){const total=randint(cfg.min_cadence,cfg.max_cadence);p.cadence=cfg.activity_type==='Cycling'?total:round(total/2);}
      if(p.watts==null)p.watts=Math.min(cfg.max_power,round(cfg.base_power*cfg.weight/70*(.95+rng()*.1)));
    }
    previous=p;
  }
}
function metrics(points,key){let total=0,count=0,max=0;for(const p of points)if(p[key]!=null){total+=p[key];max=Math.max(max,p[key]);count++;}return{count,max,average:count?round(total/count):0};}
export function tcxXml(points,cfg) {
  const sport=cfg.activity_type.startsWith('Running')?'Running':cfg.activity_type==='Cycling'?'Biking':'Other';
  const start=iso(points[0].time),distance=points.at(-1).distance,duration=(points.at(-1).time-points[0].time)/1000;
  const hr=metrics(points,'hr'),cad=metrics(points,'cadence'),watts=metrics(points,'watts'),speed=metrics(points,'speed');
  const calorie=cfg.simulate_metrics?Math.min(65535,round(distance/1000*cfg.calories_per_km*cfg.weight/70)):0;
  const xml=['<?xml version="1.0" encoding="utf-8"?>',`<TrainingCenterDatabase xmlns="${TCX}" xmlns:ae="${AX}"><Activities><Activity Sport="${sport}"><Id>${start}</Id><Lap StartTime="${start}">`,
    `<TotalTimeSeconds>${duration.toFixed(3)}</TotalTimeSeconds><DistanceMeters>${distance.toFixed(3)}</DistanceMeters><MaximumSpeed>${speed.max.toFixed(6)}</MaximumSpeed><Calories>${calorie}</Calories>`];
  if(hr.count)xml.push(`<AverageHeartRateBpm><Value>${hr.average}</Value></AverageHeartRateBpm><MaximumHeartRateBpm><Value>${hr.max}</Value></MaximumHeartRateBpm>`);
  xml.push('<Intensity>Active</Intensity>');
  if(cad.count&&sport==='Biking')xml.push(`<Cadence>${cad.average}</Cadence>`);
  xml.push('<TriggerMethod>Manual</TriggerMethod>');
  let segment=null;
  for(const p of points){
    if(p.segment!==segment){if(segment!==null)xml.push('</Track>');xml.push('<Track>');segment=p.segment;}
    xml.push(`<Trackpoint><Time>${iso(p.time)}</Time><Position><LatitudeDegrees>${p.lat}</LatitudeDegrees><LongitudeDegrees>${p.lon}</LongitudeDegrees></Position>`);
    if(p.elevation!=null)xml.push(`<AltitudeMeters>${p.elevation}</AltitudeMeters>`);
    xml.push(`<DistanceMeters>${p.distance.toFixed(3)}</DistanceMeters>`);
    if(p.hr!=null)xml.push(`<HeartRateBpm><Value>${p.hr}</Value></HeartRateBpm>`);
    if(p.cadence!=null&&sport==='Biking')xml.push(`<Cadence>${p.cadence}</Cadence>`);
    xml.push(`<Extensions><ae:TPX><ae:Speed>${p.speed.toFixed(6)}</ae:Speed>`);
    if(p.cadence!=null&&sport!=='Biking')xml.push(`<ae:RunCadence>${p.cadence}</ae:RunCadence>`);
    if(p.watts!=null)xml.push(`<ae:Watts>${p.watts}</ae:Watts>`);
    xml.push('</ae:TPX></Extensions></Trackpoint>');
  }
  xml.push(`</Track><Extensions><ae:LX><ae:AvgSpeed>${(duration>0?distance/duration:0).toFixed(6)}</ae:AvgSpeed>`);
  if(cad.count)xml.push(sport==='Biking'?`<ae:MaxBikeCadence>${cad.max}</ae:MaxBikeCadence>`:`<ae:AvgRunCadence>${cad.average}</ae:AvgRunCadence><ae:MaxRunCadence>${cad.max}</ae:MaxRunCadence>`);
  if(watts.count)xml.push(`<ae:AvgWatts>${watts.average}</ae:AvgWatts><ae:MaxWatts>${watts.max}</ae:MaxWatts>`);
  let note=`Converted from GPX; activity=${cfg.activity_type}.`;
  note+=cfg.simulate_metrics?' Calories estimated from distance, configured kcal/km and weight.':' Calories unavailable (0).';
  if(cfg.time_mode==='pace')note+=' Timestamps generated from target pace.';
  if(cfg.simulate_metrics)note+=' Missing HR/cadence/power filled with SIMULATED values; not sensor measurements.';
  xml.push(`</ae:LX></Extensions></Lap><Notes>${note}</Notes></Activity></Activities></TrainingCenterDatabase>`);
  return xml.join('');
}
export function convert(xml,values={},progress=()=>{}) {
  const cfg=configuration(values),points=readGpx(xml),source=summary(points);progress(35);
  prepare(points,cfg);progress(65);
  const result=tcxXml(points,cfg),data=new TextEncoder().encode(result);progress(95);
  return {data,result:{...summary(points),source,simulated:cfg.simulate_metrics,generated_times:cfg.time_mode==='pace',size_bytes:data.byteLength}};
}
