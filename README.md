# GPX → TCX 网页转换器

保留原有跑步背景、绿色界面和配置分组，专注网页上传、轨迹预览、运动参数配置、转换和下载；天气与聚合访问统计也保留。桌面 GUI、个人路径脚本、历史测试输出和重复部署说明已从当前版本移除，旧版本仍可通过 Git 历史查看。

## GitHub Pages

在线网页：[mariohuang233.github.io/gpxtcxconvert233](https://mariohuang233.github.io/gpxtcxconvert233/)。`main` 的自动测试全部通过后，GitHub Actions 才发布 `_site` 中的公开网页资源；Python 源码、测试、数据库、环境配置与 Node 依赖不会上传到 Pages。

Pages 复用同一套页面，在 Web Worker 中解析 GPX 并生成实际可下载的 TCX，轨迹文件不上传服务器，模拟数据仍默认开启，原始传感器指标优先。支持相同的运动类型、时间模式、16 MB / 100,000 点限制、轨迹分段、参数与官方 TCX 格式；JS 使用固定种子重现本平台的模拟数据，随机序列与 Python 版本不同。浏览器文件读取支持 UTF-8 和带 BOM 的 UTF-16；结果最多保留 60 分钟，也可重置或删除，关闭页面后释放。

天气仍需主动选择定位或轨迹起点，通过 HTTPS 请求 Open-Meteo，缓存和失败状态与原界面一致。按照部署选择，Pages 的访问、转换、下载和天气刷新计数保存在当前浏览器，最近 30 个 UTC 日期可在“本机访问统计”中查看；不代表全站人数，没有服务器管理员令牌，也不记录文件名、轨迹或位置。浏览器禁止本地存储时会显示限制说明。

后续接入全站事件统计时，在仓库 Actions Variables 中设置公开的 `PAGES_ANALYTICS_ENDPOINT` HTTPS 接收地址并重新运行工作流；不要填写包含密钥的地址。接收端需允许本站来源的 CORS `POST` / `Content-Type`，接受 `{"event":"page_view"}` 以及 `conversion_started`、`conversion_completed`、`conversion_failed`、`download`、`weather_requested` 六种固定事件名称。请求不附带 Cookie、文件、坐标、表单或 Referrer，后端不可用不影响转换；管理与全站报表由该后端提供，网页仍显示本机计数并提示已启用匿名上报。当前部署没有配置外部统计地址。

构建与子目录预览（先安装下面的 Python 依赖，再准备 Node.js 24）：

```sh
npm ci
npm run build:pages
python tests/serve_pages.py
# http://127.0.0.1:8900/gpxtcxconvert233/
```

`npm run test:converter` 检查浏览器转换规则，`python tests/validate_pages_output.py` 验证合成导出的官方 XSD 与 Python 汇总语义；设置 `TEST_BASE_URL` 后运行 `npm run test:pages` 可检查静态网页真实浏览器流程。构建产物不提交 Git，XML 解析器依赖和许可证随构建公开，避免维护另一份完整页面。

## 本地运行

需要 Python 3.11 或更新版本；运行 Flask 网页不需要 Node.js，构建 Pages 时需要 Node.js。

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS / Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python web_app.py
```

访问 http://127.0.0.1:8080 。入口使用 Waitress，默认监听本机；对外服务设置 `HOST=0.0.0.0` 和平台提供的 `PORT`。容器部署使用 `docker compose up --build -d`，任务状态和临时文件存放于持久化卷 `/data`，健康检查为 `/health`，不依赖 curl。

## 使用与数据含义

上传一个不超过 16 MB、100,000 个轨迹点的 GPX 1.0 / 1.1；支持命名空间、轨迹分段、路线点、单引号属性与自闭合点。预览与转换使用同一套解析规则，默认仅绘制路线，不请求地图瓦片；需要缩放地图时可主动加载 OpenStreetMap 底图。

**模拟数据默认开启。** 只补充缺失的心率、步频和功率，已有 Garmin 扩展传感器数据优先保留；关闭后不填充缺失指标。基础功率随体重相对 70 kg 缩放，受功率上限约束；卡路里按距离、每公里系数和体重估算，关闭模拟时没有可靠值，TCX 写 0。所有估算与模拟都会标注在 TCX Notes 中，不能解释为实测数据。

时间默认保留 GPX 日期与逐点时间，自定义开始时间留空；填写后按设备在所选日期的时区换算为 UTC，整条轨迹平移。缺少时间的文件需选择“按配速生成时间”并指定开始时间。无时区的 GPX 时间按 UTC 解释；分段之间不计算连接距离。跑步界面显示双脚总步频，TCX RunCadence 使用单脚步频；骑行使用 rpm。运动子类型保存在 Notes，标准 Sport 只写 Running、Biking 或 Other。输出不冒充 Garmin 设备。

页面保留原有 12 种语言资源与 RTL 支持，按需加载选中语言；新增辅助说明目前提供中文和英文，其他语言缺少的新文案回退至英文。字体、背景和 Leaflet 脚本均自托管。

## 天气与访问统计

天气由用户点击定位或轨迹起点后获取，使用 [Open-Meteo](https://open-meteo.com/en/docs) 的当前模型数据；显示来源和时间，不用于还原历史活动天气。缓存最多 128 项、有效期 15 分钟，服务失败时仅允许使用 1 小时内的旧缓存并明确标注，否则显示不可用。经纬度在请求供应商前取到小数点后两位；不使用服务器 IP 代替访问者位置，也不生成随机天气。免费端点适用于[非商业使用](https://open-meteo.com/en/pricing)，商业部署应改用对应授权方案。

统计按 UTC 日期保留 30 天，仅记录聚合访问、转换开始/成功/失败、下载请求及天气请求次数；不存储原始点击事件、文件名、GPX 内容、用户 IP 或精确位置。每日会话去重标识经过按日 HMAC，最多保留 10,000 个；超出后聚合访问计数继续增加。页面 `/analytics` 可打开，读取与清空数据必须提交 `ADMIN_TOKEN`；未配置令牌时管理接口关闭。匿名上报只接受访问事件，转换结果与下载由服务端计数。

## 部署配置与保留期限

| 变量 | 默认值 / 含义 |
| --- | --- |
| `HOST` / `PORT` | `127.0.0.1` / `8080`；容器 HOST 为 `0.0.0.0` |
| `DATA_DIR` | 本地 `.data`；保存 SQLite 状态、会话密钥和临时轨迹文件 |
| `SECRET_KEY` | 留空时在 DATA_DIR 生成持久化随机密钥；生产可显式配置随机值 |
| `ADMIN_TOKEN` | 空，统计管理关闭；使用独立随机值 |
| `COOKIE_SECURE` | `0`；公开 HTTPS 部署设为 `1` |

`.env.example` 仅列出变量，应用不会自动读取；Compose 可从 `.env` 读取变量。生成随机值可用 `python -c "import secrets; print(secrets.token_hex(32))"`。请持久化 DATA_DIR，并通过 HTTPS 公开服务。

源文件在成功、失败或取消后删除；结果默认保留 60 分钟并绑定创建它的浏览器会话，网页可手动删除。运行中每 30 秒清理过期文件；应用停止期间不运行清理，重启请求后继续清理，过期链接始终不可下载。正在下载的文件在操作系统释放句柄后删除。转换默认 2 个工作线程，最多 8 个未结束任务；队列满返回 503 和 Retry-After。SQLite 允许同一目录的应用实例查询任务，但**当前部署目标是单机、持久化磁盘**，不支持跨容器分布式队列；进程意外退出时在途任务不会自动重新执行，会在保留期后清理。

## 测试

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
python tests/benchmark.py
```

浏览器测试另需 Node.js 24，先启动网页，再运行：

```sh
npm ci
npx playwright install chromium
npm test
# 可选截图：设置 TEST_ARTIFACTS=test-artifacts
# 已安装 Edge / Chrome 时可设置 BROWSER_EXECUTABLE 为浏览器可执行文件路径
```

GitHub Actions 在 Python 3.11 / 3.12 上执行回归测试，并在 Chromium 中执行上传下载、日期与模拟设置、注入防护、重置竞态、多语言、手机布局、主题和无障碍检查。性能测量与已验证范围见 [docs/VALIDATION.md](docs/VALIDATION.md)。

## 文件结构

```text
web_app.py          网页接口、任务生命周期、天气及统计
gpx_to_tcx.py       配置验证、GPX 解析、指标与 TCX 输出
templates/          转换页与统计管理页
static/             页面样式、业务模块、12 种语言与本地资源
tests/              Python / 浏览器回归、合成轨迹与官方 XSD
docs/VALIDATION.md  本次验证记录与性能对比
Dockerfile          容器构建，Compose 保留数据卷
Procfile            平台单网页进程，无桌面监控 worker
```

第三方资源：Geist 字体采用 [SIL OFL](static/fonts/OFL.txt)，Leaflet 采用 [BSD 2-Clause](static/vendor/leaflet/LICENSE)，地图与天气保留供应商署名；测试 XSD 来自 Garmin 官方格式定义。
