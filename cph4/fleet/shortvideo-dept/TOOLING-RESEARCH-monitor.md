# 热点监控开源件快研（TOOLING-RESEARCH-monitor）

- 日期：2026-10-10 · 调研员：开源数据件调研员 · 纯 web（search+fetch；GitHub API 限流，stars 为量级估值）
- 背景：机队 Windows + PowerShell 5.1 计划任务 · 无 docker · 日更 3 条短视频需热榜多轮扫描+推送值守

## 一、逐项验证（功能 / stars 量级 / 活跃度 / Windows 适配 / 结论）

| 件 | 功能 | stars | 活跃度 | Windows 适配 | 结论 |
|---|---|---|---|---|---|
| imsyy/DailyHotApi | 聚合 60+ 热榜统一 API（微博/知乎/百度/抖音/B站…），RSS+JSON 双模式，60min 缓存 | ~7k | 活跃（接口清单持续扩） | Node LTS 直跑 `npm i → build → start`（或 pm2 守护），PS 只调本地 :6688 | **直接用**＝主扫描件 |
| ourongxing/newsnow | 热点聚合阅读 Web 应用，60+ 源，缓存/OAuth 登录，带 MCP | ~6k | 转维护（Next 新版开发中，暂停社区 PR） | Node≥20+pnpm+D1 库，Web 应用非 API 件，落地重 | **仅参考**＝抄 sources 源清单 |
| DIYgod/RSSHub | 万物转 RSS，数千路由（微博热搜/知乎/微信读书…） | ~40k | 极活跃（数年如一日） | 官方主推 Docker；Node 可跑但非重点；公共实例免自建 | **直接用**＝公共实例补源，不自建 |
| n8n（n8n-io/n8n） | 可视化工作流自动化（扫描→清洗→推送全托管） | 10万+ | 极活跃 | npm/npx 可装但**非官方支持路径**，须手工守护+开机自启 hack，常驻吃内存 | **不引入**＝重牛刀且 Windows 原生落地运维成本高 |
| 微博热搜爬虫类（Bowen1911/Weibo_Hot_Search、legeling/weibo_hotSearch） | 定时爬微博热搜→Markdown 存档/GitHub 备份/邮件·QQ 推送 | 百~千级 | 低频存档型（个人件） | Python3+requests/lxml/bs4，需装 Python 运行时 | **仅参考**＝DailyHotApi 已含 weibo；兜底 PS 直调微博公开端点零依赖 |
| Server酱·Turbo（sct.ftqq.com，SaaS） | SendKey HTTP→微信推送，一行 API | —（非开源） | 服务稳定运营多年 | Invoke-RestMethod 原生一行，零依赖 | **直接用**＝免费 5 条/天；订阅 ¥8/月→1000 条/天 |
| PushPlus（pushplus.plus，SaaS） | 多通道推送（微信/邮件/钉钉/飞书），一行 API | —（非开源） | 服务稳定运营 | 同上，HTTP API 零依赖 | **直接用**＝免费 200 条/天，备份通道 |

## 二、采纳建议 Top5

1. **DailyHotApi（主扫描件）**：本机 Node 起服（pm2 守护），PS 计划任务多轮 Invoke-RestMethod 拉 60+ 榜，一装永逸。
2. **Server酱·Turbo（推送主通道）**：免费 5 条/天恰好覆盖日更 3 条+值守告警，一行 PS 推微信。
3. **PushPlus（推送备通道）**：免费 200 条/天额度充裕，与 Server酱互为灾备防漏推。
4. **RSSHub 公共实例（补源件）**：补特殊源（微信读书飙升/知乎日报等 RSS），PS 解析 XML 即用，不自建。
5. **newsnow 源清单（参考件）**：不部署本体，抄 60+ 源定义补 DailyHotApi/RSSHub 漏源；观望其 NewsNext。

## 三、落地要点

- 扫描链：PS5.1 计划任务（每日多轮）→ DailyHotApi 本地 API(:6688) → 选题落盘 → Server酱+PushPlus 双通道推送值守
- 新增装机仅 Node.js LTS 一项（供 DailyHotApi）；推送与 RSS 解析零依赖
- n8n 不引入三因：官方不支持 Windows 原生、常驻服务重、PS 脚本+计划任务已满足本场景
- 微博兜底：DailyHotApi weibo 接口失效时，PS 直调微博公开热榜端点（Invoke-RestMethod 零依赖顶上）
