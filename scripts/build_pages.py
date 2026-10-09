"""Render the shared templates and copy only public website assets for Pages."""
import json
import os
from pathlib import Path
import shutil
from urllib.parse import urlsplit
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'_site'
if SITE.resolve().parent != ROOT:
    raise RuntimeError('Output must remain inside the repository.')
if SITE.exists():
    shutil.rmtree(SITE)
SITE.mkdir()
shutil.copytree(ROOT/'static',SITE/'static',ignore=shutil.ignore_patterns('browser-converter.mjs','conversion-worker.js','analytics.js'))
endpoint=os.environ.get('PAGES_ANALYTICS_ENDPOINT','').strip()
parsed=urlsplit(endpoint)
if endpoint and (parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment):
    raise RuntimeError('PAGES_ANALYTICS_ENDPOINT must be a public HTTPS event URL without credentials or a fragment.')
origin=f'{parsed.scheme}://{parsed.netloc}' if endpoint else ''
csp=("default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; "
     "img-src 'self' data: https://tile.openstreetmap.org; "
     f"connect-src 'self' https://api.open-meteo.com {origin}; worker-src 'self'; "
     "object-src 'none'; base-uri 'self'; form-action 'self'")
messages=json.loads((ROOT/'static/locales/zh.json').read_text(encoding='utf-8'))
messages.update(privacyNote='文件仅在本浏览器中处理，不上传服务器；下载结果在当前页面最多保留 60 分钟，',
                minutes='重置、删除或关闭页面后释放。',stats='本机访问统计',
                privacyDesc='轨迹在浏览器后台线程中处理，不上传服务器。',
                analyticsNote='访问、转换与下载次数仅保存在本浏览器，保留最近 30 个 UTC 日期。天气由你主动获取，地图在读取轨迹后自动加载；统计不会记录文件名、轨迹内容或精确位置。')
env=Environment(loader=FileSystemLoader(ROOT/'templates'),autoescape=select_autoescape(['html']))
for template,destination,prefix in [('index.html','index.html','./'),('analytics.html','analytics/index.html','../')]:
    target=SITE/destination;target.parent.mkdir(exist_ok=True)
    html=env.get_template(template).render(pages=True,pages_csp=csp,html_lang='zh-CN',html_dir='ltr',
         translate=lambda key:messages.get(key,key),retention_minutes=60,
         url_for=lambda endpoint,filename:prefix+'static/'+filename)
    target.write_text(html,encoding='utf-8',newline='\n')
(SITE/'static/pages-config.json').write_text(json.dumps({'analytics_endpoint':endpoint})+'\n',encoding='utf-8')
(SITE/'.nojekyll').touch()
print('Rendered GitHub Pages templates and public assets.')
