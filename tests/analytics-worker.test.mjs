import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createD1} from './helpers/d1.mjs';
import {randomUUID} from 'node:crypto';
import worker,{handle,beijingDay} from '../analytics/worker.mjs';
const origin='https://mariohuang233.github.io';
function fixture(){
  const {DB,sqlite}=createD1();
  return {sqlite,env:{DB,ALLOWED_ORIGIN:origin,VISITOR_SALT:'test-only-visitor-salt'}};
}
const req=(path,body,headers={})=>new Request('https://stats.example'+path,{method:body?'POST':'GET',headers:{Origin:origin,...(body?{'Content-Type':'application/json'}:{}),...headers},...(body?{body:JSON.stringify(body)}:{})});
const event=(visitor,event='page_view',event_id=randomUUID())=>({event,event_id,...(visitor?{visitor_id:visitor}:{})});
test('daily visitor deduplication, cumulative cross-day deduplication and duplicate delivery',async()=>{
  const {env,sqlite}=fixture(),a=randomUUID(),b=randomUUID(),now=Date.parse('2026-10-09T15:59:59Z'),first=event(a);
  for(const data of [first,first,event(a),event(b),event(null,'conversion_completed'),event(null,'download')])assert.equal((await handle(req('/events',data),env,now)).status,204);
  let stats=await (await handle(req('/stats'),env,now)).json();assert.equal(stats.today.unique_visitors,2);assert.equal(stats.today.page_view,3);assert.equal(stats.total.unique_visitors,2);assert.equal(stats.total.download,1);
  assert.equal((await handle(req('/events',event(a)),env,now+1000)).status,204);
  stats=await (await handle(req('/stats'),env,now+1000)).json();assert.equal(stats.day,'2026-10-10');assert.equal(stats.today.unique_visitors,1);assert.equal(stats.total.unique_visitors,2);assert.equal(stats.total.page_view,4);assert.equal(stats.daily['2026-10-09'].unique_visitors,2);
  assert.ok(sqlite.prepare('SELECT visitor_hash FROM visitors').all().every(row=>/^[a-f0-9]{64}$/.test(row.visitor_hash)));assert.ok(!JSON.stringify(sqlite.prepare('SELECT * FROM received_events').all()).includes(a));
  sqlite.close();
});
test('parallel new events from one browser count one visitor',async()=>{
  const {env,sqlite}=fixture(),id=randomUUID(),now=Date.now();await Promise.all(Array.from({length:20},()=>handle(req('/events',event(id)),env,now)));
  const stats=await (await handle(req('/stats'),env,now)).json();assert.equal(stats.today.page_view,20);assert.equal(stats.today.unique_visitors,1);assert.equal(stats.total.unique_visitors,1);sqlite.close();
});
test('invalid data, foreign origins, wrong methods and missing configuration are rejected',async()=>{
  const {env,sqlite}=fixture();
  for(const body of [event(null,'unknown'),{...event(randomUUID()),filename:'private.gpx'},{...event(null),event_id:'invalid'},{...event(null),event_id:[randomUUID()]},event(randomUUID(),'download'),{...event(null),padding:'x'.repeat(1000)}])assert.equal((await handle(req('/events',body),env)).status,400);
  assert.equal((await handle(req('/events',event(null),{Origin:'https://foreign.example'}),env)).status,403);
  assert.equal((await handle(req('/events'),env)).status,405);
  assert.equal((await handle(req('/unknown'),env)).status,404);
  assert.equal((await handle(req('/stats'),{...env,VISITOR_SALT:''})).status,503);
  const preflight=await handle(new Request('https://stats.example/events',{method:'OPTIONS',headers:{Origin:origin}}),env);assert.equal(preflight.status,204);assert.equal(preflight.headers.get('Access-Control-Allow-Origin'),origin);
  assert.equal(sqlite.prepare('SELECT COUNT(*) AS count FROM received_events').get().count,0);sqlite.close();
});
test('UTC boundary becomes Beijing midnight and Cloudflare execution context is not a clock',async()=>{
  assert.equal(beijingDay(Date.parse('2026-10-09T15:59:59Z')),'2026-10-09');assert.equal(beijingDay(Date.parse('2026-10-09T16:00:00Z')),'2026-10-10');
  const {env,sqlite}=fixture();const response=await worker.fetch(req('/events',event(randomUUID())),env,{});assert.equal(response.status,204);sqlite.close();
});
test('database failure is a recoverable response, not an exception',async()=>{
  const {env,sqlite}=fixture();sqlite.close();assert.equal((await handle(req('/events',event(null)),env)).status,503);
});
test('scheduled cleanup preserves historical daily totals and cumulative visitor identity',async()=>{
  const {env,sqlite}=fixture(),id=randomUUID(),old=Date.now()-100*86400000;
  await handle(req('/events',event(id)),env,old);await worker.scheduled({},env);
  assert.equal(sqlite.prepare('SELECT COUNT(*) AS count FROM received_events').get().count,0);
  assert.equal(sqlite.prepare('SELECT COUNT(*) AS count FROM daily_visitors').get().count,0);
  await handle(req('/events',event(id)),env);
  const stats=await (await handle(req('/stats'),env)).json();assert.equal(stats.total.page_view,2);assert.equal(stats.total.unique_visitors,1);assert.equal(stats.today.unique_visitors,1);assert.equal(stats.since,beijingDay(old));sqlite.close();
});
