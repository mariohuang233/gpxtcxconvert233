const {chromium}=require('playwright');
const AxeBuilder=require('@axe-core/playwright').default;
const assert=require('node:assert/strict');
(async()=>{
  const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{})});
  const context=await browser.newContext(),page=await context.newPage();
  const base=process.env.TEST_BASE_URL||'http://127.0.0.1:8080';
  for(const path of ['/','/analytics']){
    await page.goto(base+path);await page.waitForLoadState('networkidle');
    for(const theme of ['dark','light']){
      const uploadBackground=await page.evaluate(theme=>{
        document.documentElement.dataset.theme=theme;
        const upload=document.getElementById('fileUpload');
        return upload?getComputedStyle(upload).backgroundColor:null;
      },theme);
      if(path==='/')assert.equal(uploadBackground,theme==='light'?'rgb(255, 255, 255)':'rgb(32, 35, 33)',
        'Theme text and background must switch together without a contrast gap');
      const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
      assert.deepEqual(result.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[],`${path} ${theme}`);
    }
  }
  await browser.close();console.log('Accessibility: both pages, light/dark, no WCAG A/AA violations detected.');
})().catch(error=>{console.error(error);process.exit(1);});
