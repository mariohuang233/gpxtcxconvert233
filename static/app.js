import { t, setLanguage, initializeLanguage } from './i18n.js';

const aliases = {'converter':'configForm','convert-button':'convertBtn','reset-button':'resetBtn','drop-zone':'fileUpload','file-input':'fileInput','file-name':'upload-heading','file-hint':'upload-hint','form-error':'errorMessage','activity-type':'activityType','start-time':'startTime','target-pace':'targetPace','min-hr':'baseHr','max-hr':'maxHr','min-cadence':'baseCadenceDisplay','max-cadence':'maxCadenceDisplay','base-power':'basePower','max-power':'maxPower','route-view':'gpxMap','job-panel':'progressSection','job-message':'progressText','download-link':'downloadBtn','weather-location':'locationToggle','weather-state':'weatherSummary','language':'languageSelector'};
const $ = (id) => document.getElementById(aliases[id] || id);
const form = $('converter');
let selectedFile = null, routeData = null, taskId = null, generation = 0, pollTimer = null;
let previewController = null, pollController = null, weatherController = null;
let busy = false, languageReady = false, previewReady = false, sourceData = null, leafletMap = null;

function text(id, value) { $(id).textContent = value; }
function clearErrors() {
  $('form-error').hidden = true;
  text('file-error', '');
  form.querySelectorAll('[data-error]').forEach((el) => { el.textContent = ''; });
  form.querySelectorAll('[aria-invalid]').forEach((el) => el.removeAttribute('aria-invalid'));
}
function error(message, field) {
  const control = form.elements.namedItem(field);
  const target = Array.from(form.querySelectorAll('[data-error]')).find((el) => el.dataset.error === field);
  if (target) target.textContent = message;
  if (field === 'file') text('file-error', message);
  if (control) {
    control.setAttribute('aria-invalid', 'true');

    control.focus();
  }
  text('form-error', message);
  $('form-error').hidden = false;
}
async function jsonRequest(url, options = {}) {
  const response = await fetch(url, { credentials: 'same-origin', ...options });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw Object.assign(new Error(payload.error || t('networkError')), { field: payload.field, status: response.status });
  return payload;
}
function activeTheme() {
  return document.documentElement.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
}
function updateButton() { $('convert-button').disabled = busy || !previewReady || !languageReady; $('cancel-button').hidden = !selectedFile || !$('resultSection').hidden; }
function duration(seconds) {
  if (seconds == null) return t('noTime');
  const s = Math.round(seconds);
  return `${Math.floor(s / 3600).toString().padStart(2, '0')}:${Math.floor(s % 3600 / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;
}
function drawRoute() {
  const canvas = $('route-canvas'), box = canvas.getBoundingClientRect(), ctx = canvas.getContext('2d');
  const scale = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(box.width * scale); canvas.height = Math.round(box.height * scale);
  ctx.scale(scale, scale);
  if (!routeData?.route?.length) return;
  const points = routeData.route;
  const latMid = points.reduce((sum, p) => sum + p[0], 0) / points.length;
  const cos = Math.max(.01, Math.cos(latMid * Math.PI / 180));
  // Unwrap longitude at the date line before fitting to the viewport.
  let last = points[0][1];
  const projected = points.map(([lat, lon, segment]) => {
    while (lon - last > 180) lon -= 360;
    while (lon - last < -180) lon += 360;
    last = lon;
    return [lon * cos, -lat, segment];
  });
  const xs = projected.map((p) => p[0]), ys = projected.map((p) => p[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const fit = Math.min((box.width - 68) / Math.max(maxX - minX, .00001), (box.height - 68) / Math.max(maxY - minY, .00001));
  const xy = ([x, y]) => [(x - (maxX + minX) / 2) * fit + box.width / 2, (y - (maxY + minY) / 2) * fit + box.height / 2];
  const color = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim();
  const surface = getComputedStyle(document.documentElement).getPropertyValue('--surface').trim();
  ctx.strokeStyle = color; ctx.lineWidth = 3; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath();
  projected.forEach((p, i) => {
    const [x, y] = xy(p);
    if (i === 0 || p[2] !== projected[i - 1][2]) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();
  for (const index of [0, projected.length - 1]) {
    const [x, y] = xy(projected[index]);
    ctx.beginPath(); ctx.arc(x, y, index === 0 ? 6 : 4, 0, 2 * Math.PI); ctx.fillStyle = surface; ctx.fill(); ctx.stroke();
  }
}
function showSummary(data, output = false) {
  routeData = data;
  text('distance', `${(data.distance_m / 1000).toFixed(2)} km`);
  text('duration', duration(data.duration_s));
  text('points', data.points.toLocaleString());
  text('ascent', `${Math.round(data.ascent_m)} m`);
  text('preview-source', t(output ? 'outputTcx' : 'sourceGpx'));
  text('preview-note', data.missing_times ? t('missingTimes') : t('previewHint'));
  $('route-empty').hidden = true; $('gpxPreview').hidden = false;
  $('route-weather').hidden = false;
  if (leafletMap) renderMap(); else drawRoute();
}
function stopLocal() {
  generation += 1;
  clearTimeout(pollTimer); pollTimer = null;
  previewController?.abort(); pollController?.abort();
  busy = false; previewReady = false;
}
async function removeTask(id) {
  if (!id) return;
  await fetch(`/tasks/${id}`, { method: 'DELETE', credentials: 'same-origin' }).catch(() => {});
}
async function chooseFile(file) {
  const previous = taskId;
  stopLocal(); taskId = null; void removeTask(previous);
  const version = generation;
  selectedFile = null; routeData = null; sourceData = null;
  if (leafletMap) {
    leafletMap.stop(); leafletMap.remove(); leafletMap = null; $('route-canvas').hidden = false;
    for (const cls of Array.from($('route-view').classList)) if (cls.startsWith('leaflet-')) $('route-view').classList.remove(cls);
  }
  clearErrors();
  $('job-panel').hidden = true; $('resultSection').hidden = true; $('gpxPreview').hidden = true; $('download-link').hidden = true; $('delete-result').hidden = true;
  $('route-empty').hidden = false; $('route-weather').hidden = true;
  ['distance', 'duration', 'points', 'ascent'].forEach((id) => text(id, '—'));
  drawRoute(); updateButton();
  if (!file) { $('file-input').value = ''; text('file-name', t('drop')); text('file-hint', t('fileHint')); return; }
  if (!/\.gpx$/i.test(file.name)) { error(t('invalidFile'), 'file'); return; }
  if (file.size > 16 * 1024 * 1024) { error(t('tooLarge'), 'file'); return; }
  selectedFile = file;
  updateButton();
  text('file-name', file.name); text('file-hint', `${(file.size / 1024 / 1024).toFixed(2)} MB · ${t('loadingPreview')}`);
  previewController = new AbortController();
  const data = new FormData(); data.append('file', file);
  try {
    const result = await jsonRequest('/preview', { method: 'POST', body: data, signal: previewController.signal });
    if (version !== generation) return;
    sourceData = result; showSummary(result); previewReady = true;
    text('file-hint', `${(file.size / 1024 / 1024).toFixed(2)} MB · ${t('ready')}`);
  } catch (err) {
    if (err.name !== 'AbortError' && version === generation) error(err.message, 'file');
  } finally { if (version === generation) updateButton(); }
}
function syncSettings() {
  $('pace-field').hidden = $('time-mode').value !== 'pace';
  for (const name of ['min_hr','max_hr','min_cadence','max_cadence','base_power','max_power','weight','calories_per_km']) form.elements[name].disabled = !$('simulate-metrics').checked;
  form.querySelectorAll('[data-adjust]').forEach(button => { button.disabled = !$('simulate-metrics').checked; });
  $('target-pace').disabled = $('time-mode').value !== 'pace';
  text('simulation-badge', t($('simulate-metrics').checked ? 'simulationOn' : 'simulationOff'));
  text('cadence-unit', t($('activity-type').value === 'Cycling' ? 'cyclingHint' : 'cadenceHint'));
}
function validate() {
  for (const control of form.elements) {
    if (control.willValidate && !control.checkValidity()) { error(control.validationMessage, control.name); return false; }
  }
  for (const [low, high] of [['min_hr','max_hr'], ['min_cadence','max_cadence'], ['base_power','max_power']]) {
    if (!$('simulate-metrics').checked) break;
    if (+form.elements[low].value > +form.elements[high].value) { error(t('minMax'), high); return false; }
  }
  if ($('time-mode').value === 'preserve' && sourceData.missing_times) { error(t('missingTimes'), 'time_mode'); return false; }
  if ($('time-mode').value === 'pace' && !$('start-time').value && !sourceData.start_time) { error(t('needStart'), 'start_time'); return false; }
  return true;
}
async function poll(id, version, attempts = 0) {
  if (version !== generation) return;
  pollController = new AbortController();
  try {
    const payload = await jsonRequest(`/status/${id}`, { signal: pollController.signal });
    if (version !== generation) return;
    $('job-progress').value = payload.progress;
    if (payload.status === 'completed') {
      busy = false; updateButton();
      text('job-title', t('complete')); $('resultSection').hidden = false; $('job-panel').hidden = true; text('resultMessage', t('complete'));
      text('job-message', t(payload.result.simulated ? 'completeSimulated' : 'completeMeasured'));
      showSummary(payload.result, true);
      text('result-summary', `${payload.result.start_time} · ${(payload.result.distance_m / 1000).toFixed(2)} km · ${duration(payload.result.duration_s)} · ${t(payload.result.simulated ? 'completeSimulated' : 'completeMeasured')}`);
      $('download-link').href = `/download/${id}`; $('download-link').hidden = false;
      $('delete-result').hidden = false;
      $('job-progress').hidden = true; updateButton();
      return;
    }
    if (payload.status === 'error' || payload.status === 'cancelled') {
      busy = false; updateButton(); $('job-progress').hidden = true;
      text('job-title', t('failed')); text('job-message', payload.error || t('cancelled'));
      error(payload.error || t('cancelled'), payload.field); return;
    }
    text('job-message', t(payload.status === 'queued' ? 'queued' : 'processing'));
    pollTimer = setTimeout(() => poll(id, version), 650);
  } catch (err) {
    if (err.name === 'AbortError' || version !== generation) return;
    if (attempts < 4 && (!err.status || err.status >= 500)) {
      text('job-message', t('reconnecting'));
      pollTimer = setTimeout(() => poll(id, version, attempts + 1), 1000 * 2 ** attempts);
    } else { busy = false; updateButton(); error(err.message); text('job-title', t('failed')); $('job-progress').hidden = true; }
  }
}
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (busy || !selectedFile || !previewReady) return;
  clearErrors(); if (!validate()) return;
  const version = generation, previous = taskId;
  taskId = null; void removeTask(previous);
  busy = true; updateButton();
  const data = new FormData(form); data.set('file', selectedFile);
  data.set('simulate_metrics', $('simulate-metrics').checked ? 'true' : 'false');
  data.set('timezone_offset', String($('start-time').value ? new Date($('start-time').value).getTimezoneOffset() : new Date().getTimezoneOffset()));
  $('job-panel').hidden = false; $('resultSection').hidden = true; $('download-link').hidden = true; $('delete-result').hidden = true;
  $('job-progress').hidden = false; $('job-progress').value = 0;
  text('job-title', t('processing')); text('job-message', t('uploading'));
  try {
    const payload = await jsonRequest('/upload', { method: 'POST', body: data });
    if (version !== generation) { void removeTask(payload.task_id); return; }
    taskId = payload.task_id; void poll(taskId, version);
  } catch (err) {
    if (version !== generation) return;
    busy = false; updateButton(); error(err.message, err.field);
    text('job-title', t('failed')); text('job-message', err.message); $('job-progress').hidden = true;
  }
});
$('file-input').addEventListener('change', (event) => void chooseFile(event.target.files[0]));
$('reset-button').addEventListener('click', () => { form.reset(); syncSettings(); void chooseFile(null); });
$('delete-result').addEventListener('click', async () => {
  const id = taskId, version = generation;
  try { await jsonRequest(`/tasks/${id}`, { method: 'DELETE' });
    if (version === generation) { taskId = null; $('download-link').hidden = true; $('delete-result').hidden = true; text('result-summary', t('deleted')); }
  } catch (err) { if (version === generation) error(err.message); }
});
const drop = $('drop-zone');
drop.addEventListener('click', event => { if (event.target !== $('file-input')) $('file-input').click(); });
form.querySelectorAll('[data-adjust]').forEach(button => button.addEventListener('click', () => {
  const input = $(button.dataset.adjust), delta=+button.dataset.step;
  input.value = Math.min(+input.max || Infinity, Math.max(+input.min || 0, (+input.value || 0)+delta));
  input.dispatchEvent(new Event('change',{bubbles:true}));
}));
for (const name of ['dragenter','dragover']) drop.addEventListener(name, (event) => { event.preventDefault(); drop.classList.add('dragging'); });
for (const name of ['dragleave','drop']) drop.addEventListener(name, (event) => { event.preventDefault(); drop.classList.remove('dragging'); });
drop.addEventListener('drop', (event) => {
  const files = event.dataTransfer.files;
  if (files.length !== 1) { error(t('singleFile'), 'file'); return; }
  void chooseFile(files[0]);
});
for (const id of ['time-mode','simulate-metrics','activity-type']) $(id).addEventListener('change', syncSettings);
$('activity-type').addEventListener('change', () => {
  $('min-cadence').value = $('activity-type').value === 'Cycling' ? '70' : '100';
  $('max-cadence').value = $('activity-type').value === 'Cycling' ? '95' : '140';
});
$('theme-toggle').addEventListener('click', () => {
  const theme = activeTheme() === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem('theme', theme); } catch { /* preference stays in this tab */ }
  drawRoute();
});
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', drawRoute);
new ResizeObserver(drawRoute).observe($('route-view'));

async function weather(lat, lon) {
  weatherController?.abort(); weatherController = new AbortController();
  text('weather-state', t('weatherLoading')); text('weather-time', '');
  const controller = weatherController;
  try {
    const result = await jsonRequest(`/api/weather?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`, { signal: controller.signal });
    if (controller !== weatherController) return;
    text('weather-state', `${Math.round(result.temperature)}°C · ${t('humidity')} ${result.humidity}% · ${t('wind')} ${result.wind_kmh} km/h`);
    text('weather-time', `${t(result.stale ? 'weatherStale' : 'weatherModel')} · ${new Date(result.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`);
  } catch (err) { if (err.name !== 'AbortError' && controller === weatherController) text('weather-state', t('weatherUnavailable')); }
}
$('weather-location').addEventListener('click', () => {
  if (!navigator.geolocation) { text('weather-state', t('locationUnavailable')); return; }
  text('weather-state', t('locating'));
  navigator.geolocation.getCurrentPosition((pos) => void weather(pos.coords.latitude, pos.coords.longitude),
    () => text('weather-state', t('locationUnavailable')), { timeout: 8000, maximumAge: 300000 });
});
$('route-weather').addEventListener('click', () => {
  if (routeData?.route.length) void weather(routeData.route[0][0], routeData.route[0][1]);
});
$('language').addEventListener('change', async (event) => {
  await setLanguage(event.target.value); syncSettings();
  if (routeData) showSummary(routeData, Boolean(taskId && !$('download-link').hidden));
  if (!selectedFile) text('file-name', t('drop')); else { text('file-name', selectedFile.name); text('file-hint', `${(selectedFile.size/1024/1024).toFixed(2)} MB · ${t(previewReady?'ready':'loadingPreview')}`); }
});
$('cancel-button').addEventListener('click', () => { form.reset(); syncSettings(); void chooseFile(null); });
await initializeLanguage(); languageReady = true; syncSettings(); updateButton();
// Only fixed aggregate event names are sent; never include filenames, coordinates or form data.
void fetch('/api/analytics', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event: 'page_view' }), keepalive: true }).catch(() => {});

function renderMap() {
  if (!leafletMap || !routeData) return;
  leafletMap.eachLayer(layer => { if (!(layer instanceof L.TileLayer)) leafletMap.removeLayer(layer); });
  const segments = new Map();
  routeData.route.forEach(([lat,lon,segment]) => { if(!segments.has(segment)) segments.set(segment,[]); segments.get(segment).push([lat,lon]); });
  const color=getComputedStyle(document.documentElement).getPropertyValue('--primary-green').trim();
  for(const points of segments.values()) L.polyline(points,{color,weight:3}).addTo(leafletMap);
  const coords=routeData.route.map(p=>p.slice(0,2));
  if(coords.length===1) leafletMap.setView(coords[0],15); else leafletMap.fitBounds(coords,{padding:[24,24],maxZoom:16});
}
$('load-map').addEventListener('click',async()=>{
  if(leafletMap || !routeData) return;
  const version=generation;
  $('load-map').disabled=true;
  try {
    if(!window.L) {
      const css=document.createElement('link'); css.rel='stylesheet'; css.href='/static/vendor/leaflet/leaflet.css'; document.head.append(css);
      await new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='/static/vendor/leaflet/leaflet.js';script.onload=resolve;script.onerror=reject;document.head.append(script);});
    }
    if(version!==generation || !routeData) return;
    $('route-canvas').hidden=true;
    leafletMap=L.map('gpxMap',{zoomAnimation:false,fadeAnimation:false,markerZoomAnimation:false}).setView(routeData.route[0].slice(0,2),13);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).addTo(leafletMap);
    renderMap();
  } catch { error(t('networkError')); } finally { $('load-map').disabled=false; }
});
