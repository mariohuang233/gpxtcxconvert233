const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
  const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{})});
  const context=await browser.newContext(),page=await context.newPage(),base=process.env.TEST_BASE_URL||'http://127.0.0.1:8899/';
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto(base);await page.waitForFunction(()=>document.getElementById('simulation-badge').textContent.length>0);
  const dates=await page.evaluate(()=>{
    const key=Object.keys(localStorage).find(k=>k.startsWith('gpx-tcx:stats:'));
    const day=offset=>{const now=new Date();now.setUTCDate(now.getUTCDate()+offset);return now.toISOString().slice(0,10);};
    const oldest=day(-29),expired=day(-30);localStorage.setItem(key,JSON.stringify({[oldest]:{page_view:1},[expired]:{page_view:9}}));
    return {key,oldest,expired};
  });
  await page.goto(new URL('analytics/',base.endsWith('/')?base:base+'/').href);await page.locator('#stats-result').waitFor({state:'visible'});
  const stats=JSON.parse(await page.evaluate(key=>localStorage.getItem(key),dates.key));
  assert.ok(stats[dates.oldest]);assert.equal(stats[dates.expired],undefined);
  await page.addInitScript(()=>{Storage.prototype.getItem=()=>{throw new Error('Storage denied');};Storage.prototype.setItem=()=>{throw new Error('Storage denied');};});
  await page.goto(base);await page.waitForFunction(()=>!document.getElementById('simulation-badge').textContent.includes('simulationOn'));
  await page.goto(new URL('analytics/',base.endsWith('/')?base:base+'/').href);await page.locator('#stats-result').waitFor({state:'visible'});
  assert.match(await page.locator('#stats-error').textContent(),/限制/);
  await context.close();
  const remote=await browser.newContext(),remotePage=await remote.newPage(),sent=[];
  await remotePage.route('**/pages-config.json',route=>route.fulfill({contentType:'application/json',body:JSON.stringify({analytics_endpoint:'https://api.open-meteo.com/test-event'})}));
  await remotePage.route('https://api.open-meteo.com/test-event',route=>{
    if(route.request().method()==='POST')sent.push(route.request().postDataJSON());
    return route.fulfill({status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'POST','Access-Control-Allow-Headers':'Content-Type'}});
  });
  await remotePage.goto(base);await remotePage.locator('#remote-stats-note').waitFor({state:'visible'});
  await remotePage.waitForTimeout(150);assert.deepEqual(sent,[{event:'page_view'}]);
  assert.deepEqual(errors,[]);await browser.close();console.log('Pages: 30-date retention, storage denial and optional anonymous endpoint passed.');
})().catch(error=>{console.error(error);process.exit(1);});
