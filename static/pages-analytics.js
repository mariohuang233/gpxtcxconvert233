import {localStats,clearLocalStats,remoteAnalyticsEnabled} from './platform.js';
const labels={page_view:'访问',conversion_started:'开始转换',conversion_completed:'转换成功',conversion_failed:'转换失败',download:'下载',weather_requested:'天气刷新成功（不含缓存）'};
function render(){
  const {stats,persisted}=localStats(),body=document.getElementById('stats-body');body.replaceChildren();
  const rows=Object.entries(stats).sort(([a],[b])=>b.localeCompare(a)).flatMap(([day,counts])=>Object.entries(labels).filter(([event])=>Number(counts[event])>0).map(([event,label])=>[day,label,counts[event]]));
  if(!rows.length)rows.push(['暂无统计。','','']);
  for(const row of rows){const tr=document.createElement('tr');for(const value of row){const td=document.createElement('td');td.textContent=String(value);tr.append(td);}body.append(tr);}
  document.getElementById('stats-result').hidden=false;
  document.getElementById('stats-error').textContent=persisted?'':'浏览器限制了本地存储，当前仅显示本次页面会话的统计。';
}
document.getElementById('clear-stats').addEventListener('click',()=>{if(confirm('确定清空本浏览器的统计？')){clearLocalStats();render();}});
window.addEventListener('storage',render);render();
if(await remoteAnalyticsEnabled())document.getElementById('remote-stats-note').hidden=false;
