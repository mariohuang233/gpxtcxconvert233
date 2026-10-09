// The existing UI uses the same request contract in Flask and on static Pages.
export const isPages=document.querySelector('meta[name="app-mode"]')?.content==='pages';
const jobs=new Map(), weatherCache=new Map(), root=new URL('../',import.meta.url);
const events=new Set(['page_view','conversion_started','conversion_completed','conversion_failed','download','weather_requested']);
const storageKey='gpx-tcx:stats:'+root.pathname;
let memoryStats={},settings={analytics_endpoint:''};
let memoryVisitor;
export const settingsReady=isPages?fetch(new URL('./pages-config.json',import.meta.url)).then(r=>r.ok?r.json():{}).then(config=>{settings=config;}).catch(()=>{}):Promise.resolve();
const apiError=(message,field,status=400)=>Object.assign(new Error(message),{field,status});

function prune(stats) {
  const oldest=new Date();oldest.setUTCDate(oldest.getUTCDate()-29);
  const day=oldest.toISOString().slice(0,10);
  return Object.fromEntries(Object.entries(stats).filter(([date,values])=>date>=day&&/^\d{4}-\d{2}-\d{2}$/.test(date)&&values&&typeof values==='object').slice(-30));
}
export function localStats() {
  let persisted=true,stats;
  try{stats=JSON.parse(localStorage.getItem(storageKey)||'{}');}catch{persisted=false;stats=memoryStats;}
  if(!stats||typeof stats!=='object'||Array.isArray(stats))stats={};
  stats=prune(stats);memoryStats=stats;
  try{localStorage.setItem(storageKey,JSON.stringify(stats));}catch{persisted=false;}
  return {stats,persisted};
}
export function clearLocalStats() { memoryStats={};try{localStorage.removeItem(storageKey);}catch{} }
export function record(event) {
  if(!events.has(event))return;
  if(!isPages){if(event==='page_view')void fetch('/api/analytics',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({event}),keepalive:true}).catch(()=>{});return;}
  const {stats}=localStats(),day=new Date().toISOString().slice(0,10);
  if(!stats[day])stats[day]={};
  stats[day][event]=Math.min(Number.MAX_SAFE_INTEGER,(Number(stats[day][event])||0)+1);memoryStats=stats;
  try{localStorage.setItem(storageKey,JSON.stringify(stats));}catch{}
  // Remote visitor counts use a random browser ID, never user files or location metadata.
  void settingsReady.then(()=>{
    if(!settings.analytics_endpoint)return;
    const payload={event};
    if(settings.analytics_protocol==='visitors-v1'){
      payload.event_id=crypto.randomUUID();
      if(event==='page_view'){
        try{const key='gpx-tcx:visitor:'+root.pathname;let id=localStorage.getItem(key);
          if(!/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(id||'')){id=crypto.randomUUID();localStorage.setItem(key,id);}memoryVisitor=id;
        }catch{memoryVisitor??=crypto.randomUUID();}
        payload.visitor_id=memoryVisitor;
      }
    }
    void fetch(settings.analytics_endpoint,{method:'POST',mode:'cors',credentials:'omit',referrerPolicy:'no-referrer',
      headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),keepalive:true,signal:AbortSignal.timeout(4000)}).catch(()=>{});
  });
}
export async function remoteAnalyticsEnabled(){await settingsReady;return Boolean(settings.analytics_endpoint);}
export async function remoteStats(){
  await settingsReady;
  if(!settings.analytics_endpoint||settings.analytics_protocol!=='visitors-v1')return null;
  const endpoint=new URL(settings.analytics_endpoint);endpoint.pathname=endpoint.pathname.replace(/\/events\/?$/,'/stats');endpoint.search='';
  const response=await fetch(endpoint,{credentials:'omit',referrerPolicy:'no-referrer',cache:'no-store',signal:AbortSignal.timeout(5000)});
  if(!response.ok)throw new Error('统计服务暂时不可用，请稍后刷新。');
  return response.json();
}

function workerCall(file,mode,config,{signal,onProgress}={}) {
  const worker=new Worker(new URL('./conversion-worker.js',import.meta.url),{type:'module'});
  let cancelled=false;
  const promise=new Promise((resolve,reject)=>{
    const finish=(value,error)=>{worker.terminate();signal?.removeEventListener('abort',abort);error?reject(error):resolve(value);};
    const abort=()=>{cancelled=true;finish(null,new DOMException('Cancelled','AbortError'));};
    worker.onmessage=({data})=>{if(data.progress!=null){onProgress?.(data.progress);return;}finish(data,data.error?apiError(data.error,data.field):null);};
    worker.onerror=()=>finish(null,apiError('浏览器转换线程无法启动，请刷新重试。'));
    if(signal?.aborted){abort();return;}
    signal?.addEventListener('abort',abort,{once:true});
    worker.postMessage({file,mode,config});
  });
  return {promise,cancel:()=>{if(!cancelled)worker.terminate();}};
}
function remove(id) { const job=jobs.get(id);if(!job)return;clearTimeout(job.expiry);job.cancel?.();if(job.url)URL.revokeObjectURL(job.url);jobs.delete(id); }
export function downloadUrl(id) { return isPages?jobs.get(id)?.url:`/download/${id}`; }
export function downloadName(id) {return jobs.get(id)?.filename||'';}
window.addEventListener('pagehide',()=>{for(const id of jobs.keys())remove(id);});

async function pagesWeather(url,signal) {
  const lat=Number(url.searchParams.get('lat')),lon=Number(url.searchParams.get('lon'));
  if(!Number.isFinite(lat)||!Number.isFinite(lon)||Math.abs(lat)>90||Math.abs(lon)>180)throw apiError('经纬度无效。');
  const latitude=lat.toFixed(2),longitude=lon.toFixed(2),key=latitude+','+longitude,old=weatherCache.get(key),now=Date.now();
  if(old&&now-old.stored<900000)return {...old.data,cached:true};
  const controller=new AbortController(),abort=()=>controller.abort();signal?.addEventListener('abort',abort,{once:true});
  const timer=setTimeout(abort,4000);
  try{
    if(signal?.aborted)abort();
    const query=new URLSearchParams({latitude,longitude,current:'temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code',timezone:'UTC'});
    const response=await fetch('https://api.open-meteo.com/v1/forecast?'+query,{signal:controller.signal,credentials:'omit',referrerPolicy:'no-referrer'});
    if(!response.ok)throw new Error('Weather unavailable');
    const {current}=await response.json();
    if(!current||!Number.isFinite(current.temperature_2m)||!Number.isFinite(current.relative_humidity_2m)||!Number.isFinite(current.wind_speed_10m))throw new Error('Invalid weather');
    const result={available:true,source:'Open-Meteo',temperature:current.temperature_2m,humidity:current.relative_humidity_2m,
      wind_kmh:current.wind_speed_10m,updated_at:current.time.endsWith('Z')?current.time:current.time+'Z',cached:false,stale:false};
    weatherCache.delete(key);weatherCache.set(key,{stored:now,data:result});
    if(weatherCache.size>128)weatherCache.delete(weatherCache.keys().next().value);
    record('weather_requested');return result;
  }catch(error){
    if(signal?.aborted)throw new DOMException('Cancelled','AbortError');
    if(old&&now-old.stored<3600000)return {...old.data,cached:true,stale:true};
    throw apiError('天气暂时不可用。',null,503);
  }finally{clearTimeout(timer);signal?.removeEventListener('abort',abort);}
}
export async function request(url,options={}) {
  if(!isPages){
    const response=await fetch(url,{credentials:'same-origin',...options});
    const payload=await response.json().catch(()=>({}));
    if(!response.ok)throw apiError(payload.error||'网络请求失败。',payload.field,response.status);
    return payload;
  }
  if(url==='/preview')return (await workerCall(options.body.get('file'),'preview',null,{signal:options.signal}).promise).result;
  if(url==='/upload'){
    if(jobs.size>=4)throw apiError('请先删除或重置已有转换。',null,503);
    const file=options.body.get('file'),id=crypto.randomUUID(),job={status:'processing',progress:10,filename:file.name.replace(/\.gpx$/i,'')+'.tcx'};
    jobs.set(id,job);record('conversion_started');
    const operation=workerCall(file,'convert',Object.fromEntries([...options.body.entries()].filter(([key])=>key!=='file')),
      {onProgress:value=>{if(jobs.has(id))job.progress=value;}});job.cancel=operation.cancel;
    job.expiry=setTimeout(()=>remove(id),3600000);
    void operation.promise.then(({data,result})=>{
      if(!jobs.has(id))return;
      job.url=URL.createObjectURL(new Blob([data],{type:'application/vnd.garmin.tcx+xml'}));
      Object.assign(job,{status:'completed',progress:100,result});record('conversion_completed');
    }).catch(error=>{if(jobs.has(id)){Object.assign(job,{status:'error',error:error.message,field:error.field});record('conversion_failed');}});
    return {task_id:id};
  }
  const match=/^\/(status|tasks)\/([\w-]+)$/.exec(url);
  if(match){const [,route,id]=match;if(!jobs.has(id))throw apiError('任务已删除或过期。',null,404);if(route==='tasks'&&options.method==='DELETE'){remove(id);return {deleted:true};}const {status,progress,result,error,field}=jobs.get(id);return {status,progress,result,error,field};}
  if(url.startsWith('/api/weather?'))return pagesWeather(new URL(url,root),options.signal);
  throw apiError('静态网页不支持此操作。',null,404);
}
