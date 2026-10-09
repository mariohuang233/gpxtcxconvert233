import {localStats,clearLocalStats,remoteAnalyticsEnabled,remoteStats} from './platform.js';
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
const status=document.getElementById('global-stats-status'),refresh=document.getElementById('refresh-global-stats');
const number=value=>Number.isSafeInteger(value)&&value>=0?value:0;
async function loadGlobal(){
  refresh.disabled=true;status.textContent='正在连接统计服务…';
  try{
    const data=await remoteStats();
    if(!data){status.textContent='尚未接入全站统计后端，下方可查看本浏览器数据。';refresh.hidden=true;return;}
    if(data.timezone!=='Asia/Shanghai'||!/^\d{4}-\d{2}-\d{2}$/.test(data.day)||!data.total||!data.today||!data.daily)throw new Error('统计服务返回的数据格式不正确。');
    for(const [id,value] of Object.entries({'today-visitors':data.today.unique_visitors,'total-visitors':data.total.unique_visitors,'today-views':data.today.page_view,'total-views':data.total.page_view}))document.getElementById(id).textContent=number(value).toLocaleString('zh-CN');
    const body=document.getElementById('global-stats-body');body.replaceChildren();
    for(let offset=0;offset<30;offset++){
      const day=new Date(Date.parse(data.day+'T00:00:00Z')-offset*86400000).toISOString().slice(0,10),counts=data.daily[day]||{};
      if(data.since&&day<data.since)break;
      const row=document.createElement('tr');
      for(const value of [day,...['unique_visitors','page_view','conversion_started','conversion_completed','conversion_failed','download','weather_requested'].map(key=>number(counts[key]))]){const cell=document.createElement('td');cell.textContent=String(value);row.append(cell);}body.append(row);
    }
    document.getElementById('global-stats-data').hidden=false;
    document.getElementById('global-stats-since').textContent=data.since?`累计自 ${data.since} 起；接入前的本机历史不会汇入全站统计。`:'尚无全站访问记录，接入后开始累计。';
    status.textContent=`已更新 · ${new Date().toLocaleTimeString('zh-CN')}`;
  }catch(error){status.textContent=error.message||'统计服务暂时不可用，请稍后刷新。';}
  finally{refresh.disabled=false;}
}
refresh.addEventListener('click',()=>void loadGlobal());void loadGlobal();
