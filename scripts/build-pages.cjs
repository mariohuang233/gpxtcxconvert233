const {build}=require('esbuild');
const {execFileSync}=require('node:child_process');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
execFileSync(process.env.PYTHON||'python',[path.join(__dirname,'build_pages.py')],{cwd:root,stdio:'inherit'});
build({entryPoints:[path.join(root,'static/conversion-worker.js')],outfile:path.join(root,'_site/static/conversion-worker.js'),
  bundle:true,format:'esm',platform:'browser',target:'es2022',minify:true,legalComments:'eof'}).then(()=>console.log('Bundled the self-hosted conversion worker.')).catch(error=>{console.error(error);process.exit(1);});
