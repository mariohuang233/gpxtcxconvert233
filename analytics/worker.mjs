const EVENTS=new Set(['page_view','conversion_started','conversion_completed','conversion_failed','download','weather_requested']);
const UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
export const beijingDay=(now=Date.now())=>new Date(now+8*3600000).toISOString().slice(0,10);
async function readPayload(request){
  if(!request.headers.get('content-type')?.startsWith('application/json'))throw new Error('json');
  const reader=request.body?.getReader();if(!reader)throw new Error('body');
  let size=0,chunks=[];
  try{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>512)throw new Error('size');chunks.push(value);}}
  finally{await reader.cancel();}
  const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
  const payload=JSON.parse(new TextDecoder().decode(bytes));
  if(!payload||typeof payload!=='object'||Array.isArray(payload)||Object.keys(payload).some(key=>!['event','event_id','visitor_id'].includes(key))||!EVENTS.has(payload.event)||typeof payload.event_id!=='string'||!UUID.test(payload.event_id))throw new Error('event');
  if(payload.visitor_id!=null&&(typeof payload.visitor_id!=='string'||!UUID.test(payload.visitor_id)))throw new Error('visitor');
  if(payload.event!=='page_view'&&payload.visitor_id!=null)throw new Error('visitor');
  return payload;
}
async function hashVisitor(id,salt){
  const key=await crypto.subtle.importKey('raw',new TextEncoder().encode(salt),{name:'HMAC',hash:'SHA-256'},false,['sign']);
  const hash=await crypto.subtle.sign('HMAC',key,new TextEncoder().encode(id));
  return Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');
}
export async function handle(request,env,now=Date.now()){
  const origin=request.headers.get('Origin'),allowed=env.ALLOWED_ORIGIN;
  const headers={'Cache-Control':'no-store','Vary':'Origin','X-Content-Type-Options':'nosniff'};
  const reply=(body,status=200)=>Response.json(body,{status,headers});
  if(!allowed||origin!==allowed)return reply({error:'Origin not allowed'},403);
  Object.assign(headers,{'Access-Control-Allow-Origin':allowed,'Access-Control-Allow-Methods':'GET, POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type','Access-Control-Max-Age':'86400'});
  const url=new URL(request.url);
  if(!['/events','/stats','/health'].includes(url.pathname))return reply({error:'Not found'},404);
  if(request.method==='OPTIONS')return new Response(null,{status:204,headers});
  if(!env.DB||!env.VISITOR_SALT)return reply({error:'Analytics is not configured'},503);
  if(url.pathname==='/health'&&request.method==='GET')return reply({ok:true});
  try{
    if(url.pathname==='/events'&&request.method==='POST'){
      let payload;try{payload=await readPayload(request);}catch{return reply({error:'Invalid event'},400);}
      const visitor=payload.visitor_id?await hashVisitor(payload.visitor_id,env.VISITOR_SALT):null;
      await env.DB.prepare('INSERT OR IGNORE INTO received_events(event_id,day,event,visitor_hash,received_at) VALUES (?,?,?,?,?)')
        .bind(payload.event_id,beijingDay(now),payload.event,visitor,Math.floor(now/1000)).run();
      return new Response(null,{status:204,headers});
    }
    if(url.pathname==='/stats'&&request.method==='GET'){
      const day=beijingDay(now),since=beijingDay(now-29*86400000);
      const [totals,days,first]=await env.DB.batch([
        env.DB.prepare('SELECT event,count FROM total_counts'),
        env.DB.prepare('SELECT day,event,count FROM daily_counts WHERE day>=? AND day<=? ORDER BY day DESC').bind(since,day),
        env.DB.prepare('SELECT MIN(day) AS day FROM daily_counts')]);
      const total=Object.fromEntries(totals.results.map(row=>[row.event,row.count])),daily={};
      for(const row of days.results){daily[row.day]??={};daily[row.day][row.event]=row.count;}
      return reply({timezone:'Asia/Shanghai',day,since:first.results[0]?.day??null,total,today:daily[day]??{},daily});
    }
    return reply({error:'Method not allowed'},405);
  }catch{return reply({error:'Analytics temporarily unavailable'},503);}
}
export default {
  fetch(request,env){return handle(request,env);},
  async scheduled(_event,env){
    // Counters persist; only temporary retry IDs and old daily deduplication keys expire.
    await env.DB.batch([
      env.DB.prepare('DELETE FROM received_events WHERE received_at<?').bind(Math.floor(Date.now()/1000)-7*86400),
      env.DB.prepare('DELETE FROM daily_visitors WHERE day<?').bind(beijingDay(Date.now()-90*86400000))]);
  }
};
