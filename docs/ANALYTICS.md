# 免费全站访客统计

网站继续由 GitHub Pages 托管，`analytics/worker.mjs` 使用 Cloudflare Workers + D1 收集六种固定事件，`/analytics/` 展示今日访客、累计访客、今日/累计访问次数及最近 30 天的转换、下载和天气刷新计数。日期按北京时间，累计从后端启用时开始，不导入旧本机数据。网页仍可查看和清空本机计数，清空本机数据不会影响全站汇总。

当前统计后端为 `https://gpx-tcx-analytics.gpx-tcx-web-tests.workers.dev`，D1 数据库与固定去重密钥已配置，GitHub Actions 的 `PAGES_ANALYTICS_ENDPOINT` 已接入 `/events`。统计汇总入口为 [网站访问统计](https://mariohuang233.github.io/gpxtcxconvert233/analytics/)。

访客按浏览器随机 UUID 去重。服务器只保存经固定密钥 HMAC 后的标识，不保存原始 UUID、IP、文件名、轨迹、位置或表单；转换等非访问事件不带访客标识。更换浏览器、设备或清除站点数据会计为新访客，浏览器拒绝存储时标识只在当前页面有效。累计访客跨日期去重，不能把每日访客相加。统计基于浏览器上报，不代表精确自然人数，屏蔽脚本或网络失败的访问可能不会记录。

## 首次部署

注册 Cloudflare 免费账号，用官方 Wrangler 完成浏览器授权；以下命令从仓库根目录执行，工具版本固定为 `4.149.0`。不要将账号密码或令牌提交到仓库。

```powershell
npx wrangler@4.149.0 login
npx wrangler@4.149.0 d1 create gpx-tcx-analytics
```

把返回的数据库 UUID 写入 `analytics/wrangler.jsonc` 的 `database_id`，确认 `ALLOWED_ORIGIN` 是网站来源域名（当前为 `https://mariohuang233.github.io`，不带仓库路径），随后执行：

```powershell
npx wrangler@4.149.0 d1 execute gpx-tcx-analytics --remote --file analytics/schema.sql --config analytics/wrangler.jsonc
npx wrangler@4.149.0 secret put VISITOR_SALT --config analytics/wrangler.jsonc
npx wrangler@4.149.0 deploy --config analytics/wrangler.jsonc
```

`VISITOR_SALT` 使用随机生成的长字符串，通过 secret put 的交互输入保存，不能写入公开配置。上线后保持该密钥不变，改变它会让已有访客被识别为新访客。Worker 使用默认 `workers.dev` 地址即可，无需购买域名。

在 GitHub 仓库 Settings → Secrets and variables → Actions → Variables 中设置 `PAGES_ANALYTICS_ENDPOINT` 为 Worker 的 `/events` HTTPS 地址，例如 `https://gpx-tcx-analytics.example.workers.dev/events`，重新执行 Web checks and Pages 工作流。构建时自动允许该来源的 CSP，访问统计页使用同一 Worker 的 `/stats` 接口。可用来源头验证 `/health`：

```powershell
curl.exe -H "Origin: https://mariohuang233.github.io" https://gpx-tcx-analytics.example.workers.dev/health
```

## 保存与维护

每日汇总和累计计数长期保留；历史访客哈希保留以支持累计去重。每日访客去重键保留 90 天，事件投递去重键保留 7 天，由北京时间每日 00:15 定时清理；清理不删除汇总和累计计数。单次事件通过数据库唯一键及触发器原子写入，重复 event_id 不增加计数，多次并发访问也只计一个访客。汇总接口只读取计数，公开可读，不暴露标识，也不提供远程清空接口。

使用 Workers Free 和 D1 免费计划，保持在账户额度内即可免月费；超额度会暂时无法上报，网页转换不依赖统计服务。官网额度和计费规则见 [Workers](https://developers.cloudflare.com/workers/platform/pricing/) 与 [D1](https://developers.cloudflare.com/d1/platform/pricing/)。

## 验证

`npm run test:analytics` 使用真实 SQLite 执行同一份 D1 SQL，检查同日/跨日去重、并发、投递去重、北京时间边界、非法数据与来源限制、数据库失败、定时清理。`npm run test:pages` 包括两个独立浏览器标识与 Worker 逻辑贯通测试，检查全站页面、手机布局、明暗主题无障碍、服务失败后刷新恢复和本机清空隔离。
