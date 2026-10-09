const form=document.getElementById('stats-form'), result=document.getElementById('stats-result'), error=document.getElementById('stats-error');
const labels={page_view:'访问',conversion_started:'开始转换',conversion_completed:'转换成功',conversion_failed:'转换失败',download:'下载请求',weather_requested:'天气刷新成功（不含缓存）'};
let token='';
async function load() {
  error.textContent=''; result.hidden=true;
  const response=await fetch('/api/analytics/stats',{headers:{Authorization:`Bearer ${token}`}});
  const payload=await response.json();
  if(!response.ok) throw new Error(payload.error||'统计加载失败。');
  const rows=[...payload.events.map(row=>({...row,label:labels[row.event]||row.event})),...payload.visitors.map(row=>({...row,label:'独立访客（每日会话）'}))].sort((a,b)=>b.day.localeCompare(a.day)||a.label.localeCompare(b.label));
  const body=document.getElementById('stats-body'); body.replaceChildren();
  if(!rows.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=3;td.textContent='暂无统计。';tr.append(td);body.append(tr);}
  for(const row of rows){const tr=document.createElement('tr');for(const value of [row.day,row.label,row.count]){const td=document.createElement('td');td.textContent=String(value);tr.append(td);}body.append(tr);}
  result.hidden=false;
}
form.addEventListener('submit',async event=>{event.preventDefault();token=document.getElementById('admin-token').value;try{await load();}catch(err){error.textContent=err.message;}});
document.getElementById('clear-stats').addEventListener('click',async()=>{
  if(!confirm('确定清空聚合访问统计？此操作不可恢复。')) return;
  try{const response=await fetch('/api/analytics/stats',{method:'DELETE',headers:{Authorization:`Bearer ${token}`}});if(!response.ok)throw new Error('清空失败。');await load();}catch(err){error.textContent=err.message;}
});
