// Run against a built static site, including at a repository subpath.
const {execFileSync}=require('node:child_process');
const path=require('node:path');
const env={...process.env,TEST_PAGES:'1',TEST_ARTIFACTS:process.env.TEST_ARTIFACTS||'test-artifacts/pages'};
for(const file of ['browser.cjs','map.cjs','accessibility.cjs'])execFileSync(process.execPath,[path.join(__dirname,file)],{env,stdio:'inherit'});
execFileSync(process.execPath,[path.join(__dirname,'pages-storage.cjs')],{env,stdio:'inherit'});
