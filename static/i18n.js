const supported = ['zh','zh-tw','en','ja','ko','fr','de','es','pt','it','ar','ru'];
let current = 'zh', messages = {}, version = 0;
const extra = {
  en: {
    timeMode:'Time mode',preserve:'Keep original timestamps',paceMode:'Generate from pace',startHint:'Leave empty to keep the GPX date. Custom time uses this device’s timezone.',
    simulation:'Fill missing simulated metrics',simulationHint:'Enabled by default; recorded sensor data takes priority.',simulationOn:'Simulation enabled',simulationOff:'Simulation off',simulationWarning:'Simulated values are enabled by default. For testing only.',
    cadenceHint:'Running: total steps/min on screen, single-leg cadence in TCX.',cyclingHint:'Cycling cadence is revolutions/min (rpm).',sourceGpx:'Original GPX',outputTcx:'Exported TCX',
    routeWeather:'Weather at route start',loadMap:'Load map background',mapPrivacy:'Map tiles are requested from OpenStreetMap only after you choose to load the background.',
    privacyNote:'Files are uploaded here. Source files are removed after processing; output retained for',minutes:'minutes, or delete it manually.',stats:'Visit statistics',analyticsNote:'Only aggregate visit, conversion and download counts are recorded. No filenames, tracks or precise locations in analytics. Location weather and map backgrounds are opt-in.',
    weatherLocate:'Locate weather',weatherEmpty:'Choose a location to get weather.',weatherLoading:'Loading weather…',weatherUnavailable:'Weather unavailable. Try again later.',weatherModel:'Current weather model',weatherStale:'Last available weather (stale)',humidity:'Humidity',wind:'Wind',locating:'Locating…',locationUnavailable:'Location unavailable. You can use the route start instead.',
    noTime:'No timestamps',missingTimes:'Missing timestamps: choose pace generation and set a start time.',previewHint:'Source GPX metrics. Track segments remain separate.',loadingPreview:'Reading track…',ready:'Ready',
    invalidFile:'Choose a .gpx file.',tooLarge:'The file must be 16 MB or less.',singleFile:'Choose one file at a time.',minMax:'The maximum cannot be below the minimum.',needStart:'Set a start time for this track.',networkError:'Network request failed. Please retry.',
    processing:'Converting…',queued:'Waiting in the queue…',uploading:'Uploading GPX…',reconnecting:'Reconnecting…',complete:'Conversion complete',completeSimulated:'Missing metrics were simulated. Recorded data was preserved.',completeMeasured:'Sensor metrics preserved; missing metrics left empty.',failed:'Conversion failed',cancelled:'Task cancelled or expired.',deleteResult:'Delete this result',deleted:'The result has been deleted.',drop:'Drop a GPX or click to select',fileHint:'GPX 1.0 / 1.1 · Up to 16 MB',theme:'Light / dark'
  },
  zh: {
    timeMode:'时间模式',preserve:'保留原始时间',paceMode:'按配速生成时间',startHint:'留空沿用 GPX 日期；自定义时间使用当前设备时区。',
    simulation:'补充模拟运动数据',simulationHint:'默认开启，只补充缺失指标，已有传感器数据优先。',simulationOn:'模拟数据已开启',simulationOff:'模拟数据已关闭',simulationWarning:'默认补充模拟数据，仅供测试使用。',
    cadenceHint:'跑步显示双脚总步频，TCX 存为单脚步频。',cyclingHint:'骑行踏频单位为 rpm（每分钟转数）。',sourceGpx:'原始 GPX',outputTcx:'输出 TCX',routeWeather:'查看轨迹起点天气',loadMap:'加载地图底图',mapPrivacy:'加载底图会向 OpenStreetMap 请求地图瓦片；纯轨迹预览无需外部地图。',
    privacyNote:'文件上传至本站处理；源文件处理后删除，输出保留',minutes:'分钟，可手动删除。',stats:'访问统计',analyticsNote:'本站只记录聚合访问、转换和下载次数；统计不记录文件名、轨迹或精确位置。定位天气与地图底图由用户主动开启。',
    weatherLocate:'定位天气',weatherEmpty:'点击定位查看天气',weatherLoading:'正在获取天气…',weatherUnavailable:'天气暂时不可用，请稍后重试。',weatherModel:'当前天气模型',weatherStale:'最近可用天气（已过期）',humidity:'湿度',wind:'风速',locating:'正在定位…',locationUnavailable:'定位不可用，可选择查看轨迹起点天气。',
    noTime:'缺少时间',missingTimes:'轨迹缺少时间，请选择按配速生成并设置开始时间。',previewHint:'原始 GPX 数据，轨迹分段独立显示。',loadingPreview:'正在读取轨迹…',ready:'可以转换',invalidFile:'请选择 .gpx 文件。',tooLarge:'文件不能超过 16 MB。',singleFile:'每次请选择一个文件。',minMax:'最大值不能小于最小值。',needStart:'这条轨迹需要设置开始时间。',networkError:'网络请求失败，请重试。',
    processing:'正在转换…',queued:'正在排队…',uploading:'正在上传 GPX…',reconnecting:'正在重新连接…',complete:'转换完成',completeSimulated:'已补充缺失的模拟指标，已有传感器数据保留。',completeMeasured:'保留传感器数据，缺失指标保持为空。',failed:'转换失败',cancelled:'任务已取消或过期。',deleteResult:'删除本次结果',deleted:'本次结果已删除。',drop:'拖入 GPX，或点击选择',fileHint:'GPX 1.0 / 1.1 · 最大 16 MB',theme:'明 / 暗'
  }
};
const cache = new Map();
export const t = key => messages[key] ?? extra.en[key] ?? key;
export async function setLanguage(lang) {
  if (!supported.includes(lang)) lang='zh';
  const serial=++version;
  let dictionary=cache.get(lang);
  try {
    if (!dictionary) {
      const response=await fetch(`/static/locales/${lang}.json`);
      if (!response.ok) throw new Error('Locale unavailable');
      dictionary=await response.json(); cache.set(lang,dictionary);
    }
  } catch { dictionary=extra[lang] || extra.en; }
  if(serial!==version) return;
  current=lang;
  messages={...extra.en,...dictionary,...(extra[lang] || {})};
  document.documentElement.lang=lang==='zh'?'zh-CN':lang==='zh-tw'?'zh-TW':lang;
  document.documentElement.dir=lang==='ar'?'rtl':'ltr';
  document.querySelectorAll('[data-translate]').forEach(el=>{
    if (messages[el.dataset.translate]) el.textContent=messages[el.dataset.translate];
  });
  document.getElementById('languageSelector').value=lang;
  document.cookie=`language=${lang}; Path=/; SameSite=Lax; Max-Age=31536000`;
  try{localStorage.setItem('preferred-language',lang);}catch{}
}
export async function initializeLanguage() {
  let saved;
  try{saved=localStorage.getItem('preferred-language');}catch{}
  const lang=(navigator.language||'zh').toLowerCase();
  await setLanguage(saved||(lang==='zh-tw'||lang==='zh-hk'?'zh-tw':lang.split('-')[0]));
}
