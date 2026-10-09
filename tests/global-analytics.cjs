const {chromium}=require('playwright');
const AxeBuilder=require('@axe-core/playwright').default;
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const path=require('node:path');
(async()=>{
  const {createD1}=await import('./helpers/d1.mjs'),{handle}=await import('../analytics/worker.mjs');
  const {DB,sqlite}=createD1(),base=process.env.TEST_BASE_URL||'http://127.0.0.1:8900/gpxtcxconvert233';
  const env={DB,ALLOWED_ORIGIN:new URL(base).origin,VISITOR_SALT:'integration-test-only'};
  const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{})});
  const sent=[],errors=[];let unavailable=false;
  async function context(){
    const context=await browser.newContext({locale:'zh-CN'});
    await context.route('**/pages-config.json',route=>route.fulfill({contentType:'application/json',body:JSON.stringify({analytics_endpoint:'https://api.open-meteo.com/events',analytics_protocol:'visitors-v1'})}));
    await context.route('https://api.open-meteo.com/**',async route=>{
      const r=route.request(),payload=r.postDataJSON();if(r.method()==='POST')sent.push(payload);
      const response=await handle(new Request(r.url(),{method:r.method(),headers:r.headers(),...(r.postData()?{body:r.postData()}:{})}),env);
      await route.fulfill({status:unavailable&&r.url().endsWith('/stats')?503:response.status,headers:Object.fromEntries(response.headers),body:await response.text()});
    });
    const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));return {context,page};
  }
  const first=await context();await first.page.goto(base);await first.page.waitForFunction(()=>!document.getElementById('remote-stats-note').hidden);
  await first.page.reload();await first.page.waitForFunction(()=>!document.getElementById('remote-stats-note').hidden);
  await first.page.waitForTimeout(150);assert.equal(sent.length,2);assert.equal(sent[0].visitor_id,sent[1].visitor_id);assert.notEqual(sent[0].event_id,sent[1].event_id);
  assert.deepEqual(Object.keys(sent[0]).sort(),['event','event_id','visitor_id']);
  await handle(new Request('https://stats.example/events',{method:'POST',headers:{Origin:env.ALLOWED_ORIGIN,'Content-Type':'application/json'},body:JSON.stringify({...sent[0],event_id:crypto.randomUUID()})}),env,Date.now()-86400000);
  const second=await context();await second.page.goto(base);await second.page.waitForFunction(()=>!document.getElementById('remote-stats-note').hidden);await second.page.waitForTimeout(150);
  assert.notEqual(sent[0].visitor_id,sent[2].visitor_id);
  await first.page.goto(base.replace(/\/$/,'')+'/analytics/');await first.page.locator('#global-stats-data').waitFor({state:'visible'});
  assert.equal(await first.page.locator('#today-visitors').textContent(),'2');assert.equal(await first.page.locator('#total-visitors').textContent(),'2');assert.equal(await first.page.locator('#today-views').textContent(),'3');assert.equal(await first.page.locator('#total-views').textContent(),'4');
  assert.equal(await first.page.locator('#global-stats-body tr').count(),2);
  for(const theme of ['dark','light']){
    await first.page.evaluate(theme=>document.documentElement.dataset.theme=theme,theme);
    const result=await new AxeBuilder({page:first.page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();assert.deepEqual(result.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[],theme);
  }
  await first.page.setViewportSize({width:390,height:844});assert.equal(await first.page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  if(process.env.TEST_ARTIFACTS){await fs.mkdir(process.env.TEST_ARTIFACTS,{recursive:true});await first.page.screenshot({path:path.join(process.env.TEST_ARTIFACTS,'global-statistics-mobile.png'),fullPage:true});}
  unavailable=true;await first.page.locator('#refresh-global-stats').click();await first.page.waitForFunction(()=>document.getElementById('global-stats-status').textContent.includes('不可用'));assert.equal(await first.page.locator('#total-visitors').textContent(),'2');
  unavailable=false;await first.page.locator('#refresh-global-stats').click();await first.page.waitForFunction(()=>document.getElementById('global-stats-status').textContent.includes('已更新'));
  first.page.on('dialog',d=>d.accept());await first.page.locator('#clear-stats').click();await first.page.locator('#refresh-global-stats').click();assert.equal(await first.page.locator('#total-visitors').textContent(),'2');
  assert.deepEqual(errors,[]);await browser.close();sqlite.close();console.log('Global analytics: distinct browsers, cross-day deduplication, stable IDs, dashboard, mobile/axe, local clear isolation and outage recovery passed.');
})().catch(error=>{console.error(error);process.exit(1);});
