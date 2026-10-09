// Start web_app.py first. Synthetic fixtures only; weather and tile providers are mocked.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const path=require('node:path');
const base=process.env.TEST_BASE_URL||'http://127.0.0.1:8080';
const output=process.env.TEST_ARTIFACTS;

(async()=>{
  const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{})});
  const context=await browser.newContext({viewport:{width:1440,height:1000},timezoneId:'America/New_York',locale:'zh-CN'});
  const page=await context.newPage(), errors=[], external=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(!r.url().startsWith(base)) external.push(r.url());});
  const fixture=await fs.readFile(path.join(__dirname,'fixtures/track.gpx'));
  async function open(){await page.goto(base);await page.waitForFunction(()=>document.getElementById('simulation-badge').textContent.length>0);}
  async function choose(name='测试.gpx',buffer=fixture){await page.locator('#fileInput').setInputFiles({name,mimeType:'application/gpx+xml',buffer});await page.waitForFunction(()=>!document.getElementById('convertBtn').disabled);}
  await open();
  assert.equal(await page.locator('#simulate-metrics').isChecked(),true);
  assert.equal(await page.locator('#startTime').inputValue(),'');
  assert.equal(await page.locator('#time-mode').inputValue(),'preserve');
  if(output){await fs.mkdir(output,{recursive:true});await page.screenshot({path:path.join(output,'desktop-dark.png'),fullPage:true});}
  await choose('<img src=x onerror=alert(1)>.gpx');
  assert.equal(await page.locator('#upload-heading').textContent(),'<img src=x onerror=alert(1)>.gpx');
  assert.equal(await page.locator('#fileUpload img').count(),0);
  assert.equal(await page.locator('#duration').textContent(),'00:01:00');
  await page.locator('#baseHr').fill('200');await page.locator('#maxHr').fill('100');
  await page.locator('#convertBtn').click();assert.match(await page.locator('[data-error=max_hr]').textContent(),/不能/);
  await page.locator('#baseHr').fill('135');await page.locator('#maxHr').fill('165');
  await page.locator('#startTime').fill('2025-07-01T12:00');
  await page.locator('#convertBtn').click();await page.locator('#downloadBtn').waitFor({state:'visible'});
  assert.match(await page.locator('#result-summary').textContent(),/2025-07-01T16:00:00/);
  assert.match(await page.locator('#result-summary').textContent(),/模拟/);
  const downloadEvent=page.waitForEvent('download');await page.locator('#downloadBtn').click();
  const download=await downloadEvent;const content=await fs.readFile(await download.path());
  assert.match(content.toString(),/SIMULATED/);
  if(output)await page.screenshot({path:path.join(output,'desktop-result.png'),fullPage:true});
  await page.locator('#languageSelector').selectOption('en');assert.equal(await page.locator('#upload-heading').textContent(),'<img src=x onerror=alert(1)>.gpx');
  await page.locator('#resetBtn').click();assert.equal(await page.locator('#fileInput').inputValue(),'');
  assert.equal(await page.locator('#convertBtn').isDisabled(),true);
  await page.locator('#languageSelector').selectOption('zh');
  await choose();await page.locator('#simulate-metrics').uncheck();
  await page.locator('#convertBtn').click();await page.locator('#downloadBtn').waitFor({state:'visible'});
  const noSimulation=await context.request.get(base+await page.locator('#downloadBtn').getAttribute('href'));
  assert.doesNotMatch(await noSimulation.text(),/HeartRateBpm|RunCadence|Watts|SIMULATED/);
  await page.locator('#delete-result').click();await page.waitForFunction(()=>document.getElementById('result-summary').textContent.includes('已删除'));
  await page.locator('#resetBtn').click();await choose();
  const missing=Buffer.from('<gpx><trk><trkseg><trkpt lat="1" lon="2"/></trkseg></trk></gpx>');
  await choose('missing.gpx',missing);await page.locator('#convertBtn').click();assert.match(await page.locator('[data-error=time_mode]').textContent(),/缺少时间/);
  await page.locator('#time-mode').selectOption('pace');await page.locator('#startTime').fill('2025-01-01T12:00');
  await page.locator('#targetPace').fill('5:99');await page.locator('#convertBtn').click();assert.equal(await page.locator('#targetPace').getAttribute('aria-invalid'),'true');
  await page.locator('#targetPace').fill('5:30');await page.locator('#convertBtn').click();await page.locator('#downloadBtn').waitFor({state:'visible'});
  await page.locator('#resetBtn').click();
  let held=false;
  await page.route('**/status/*',async route=>{held=true;await new Promise(resolve=>setTimeout(resolve,600));try{await route.continue();}catch{}});
  await choose();await page.locator('#convertBtn').click();await page.waitForFunction(()=>!document.getElementById('progressSection').hidden);
  await page.locator('#cancel-button').click();await page.waitForTimeout(800);
  assert.equal(await page.locator('#resultSection').isVisible(),false);assert.equal(await page.locator('#convertBtn').isDisabled(),true);
  await page.unroute('**/status/*');
  // Keyboard activation of the original upload target and native number controls.
  await page.locator('#fileUpload').focus();const chooser=page.waitForEvent('filechooser');await page.keyboard.press('Enter');await chooser;
  await page.locator('[data-adjust=weight][data-step="1"]').focus();await page.keyboard.press('Space');assert.equal(await page.locator('#weight').inputValue(),'71');
  // Every supported locale has a loaded dictionary, correct html lang and RTL direction.
  for(const lang of ['zh','zh-tw','en','ja','ko','fr','de','es','pt','it','ar','ru']){
    await page.locator('#languageSelector').selectOption(lang);await page.waitForFunction(lang=>document.documentElement.lang===(lang==='zh'?'zh-CN':lang==='zh-tw'?'zh-TW':lang),lang);
    assert.equal(await page.locator('html').getAttribute('dir'),lang==='ar'?'rtl':'ltr');
  }
  await page.locator('#languageSelector').selectOption('zh');
  await page.route('**/api/weather?**',route=>route.fulfill({status:503,contentType:'application/json',body:'{"available":false,"error":"offline"}'}));
  await choose();await page.locator('#route-weather').click();await page.waitForFunction(()=>document.getElementById('weatherSummary').textContent.includes('不可用'));
  await page.unroute('**/api/weather?**');
  assert.equal(external.length,0,'Initial page, preview and conversion must not contact third parties');
  await page.route('https://tile.openstreetmap.org/**',route=>route.fulfill({status:200,contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jR1sAAAAASUVORK5CYII=','base64')}));
  await page.locator('#load-map').click();await page.locator('.leaflet-control-attribution').waitFor();
  await page.locator('#cancel-button').click();assert.equal(await page.locator('.leaflet-container').count(),0);
  for(const size of [{width:390,height:844},{width:768,height:1024},{width:1440,height:1000}]){
    await page.setViewportSize(size);
    for(const theme of ['dark','light']){
      await page.evaluate(theme=>{document.documentElement.dataset.theme=theme;},theme);
      await page.locator('body').click({position:{x:2,y:2}});await page.evaluate(()=>window.scrollTo(0,0));await page.waitForTimeout(180);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`${size.width} ${theme} overflow`);
      if(output)await page.screenshot({path:path.join(output,`layout-${size.width}-${theme}.png`),fullPage:true});
    }
  }
  await page.emulateMedia({reducedMotion:'reduce'});
  assert.equal(await page.locator('html').evaluate(el=>getComputedStyle(el).scrollBehavior),'auto');
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({passed:true,checks:'Default simulation, dates/timezones, field errors, download, simulation off, file name safety, reset races, keyboard input, 12 languages, weather failures, map opt-in, 3 viewports and 2 themes',pageErrors:errors},null,2));
  await browser.close();
})().catch(error=>{console.error(error);process.exit(1);});
