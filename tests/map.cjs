// External tiles are mocked; failures must never prevent local preview or conversion.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const base=process.env.TEST_BASE_URL||'http://127.0.0.1:8080';
const fixture=path.join(__dirname,'fixtures/track.gpx');
const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jR1sAAAAASUVORK5CYII=','base64');
(async()=>{
  const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{})});
  for(const scenario of ['tiles-fail','assets-fail','reset-loading']){
    const context=await browser.newContext({locale:'zh-CN'}),page=await context.newPage(),errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    await page.route('**/pages-config.json',route=>route.fulfill({contentType:'application/json',body:'{"analytics_endpoint":""}'}));
    await page.route('https://tile.openstreetmap.org/**',route=>scenario==='tiles-fail'?route.abort():route.fulfill({contentType:'image/png',body:png}));
    let release,assetBlocked;
    if(scenario==='assets-fail')await page.route('**/vendor/leaflet/leaflet.js',route=>route.abort());
    if(scenario==='reset-loading'){
      assetBlocked=new Promise(resolve=>{
        page.route('**/vendor/leaflet/leaflet.js',async route=>{
          await new Promise(continueLoad=>{release=continueLoad;resolve();});
          await route.continue();
        });
      });
    }
    await page.goto(base);
    await page.locator('#fileInput').setInputFiles(fixture);
    await page.waitForFunction(()=>!document.getElementById('convertBtn').disabled);
    if(scenario==='reset-loading'){
      await assetBlocked;await page.locator('#cancel-button').click();release();
      await page.waitForFunction(()=>Boolean(window.L));
      assert.equal(await page.locator('.leaflet-container').count(),0,'Late map assets cannot restore a reset route');
      assert.equal(await page.locator('#convertBtn').isDisabled(),true);
      await page.unroute('**/vendor/leaflet/leaflet.js');
      await page.locator('#fileInput').setInputFiles(fixture);
      await page.locator('.leaflet-control-attribution').waitFor();
    }else{
      await page.waitForFunction(()=>document.getElementById('map-status').textContent.includes('不可用'));
      if(scenario==='tiles-fail')assert.ok(await page.locator('.leaflet-overlay-pane path').count()>=4,'Route remains visible when tiles fail');
      else{
        assert.equal(await page.locator('#route-canvas').isVisible(),true,'Asset failure falls back to canvas');
        await page.unroute('**/vendor/leaflet/leaflet.js');
        await page.locator('#load-map').click();await page.locator('.leaflet-control-attribution').waitFor();
      }
    }
    await page.locator('#convertBtn').click();await page.locator('#downloadBtn').waitFor({state:'visible'});
    assert.deepEqual(errors,[],scenario);await context.close();
  }
  await browser.close();console.log('Map: tile failures, asset failure/retry and reset during loading passed; conversion remains available.');
})().catch(error=>{console.error(error);process.exit(1);});
