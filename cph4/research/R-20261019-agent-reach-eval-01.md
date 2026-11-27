# R-20261019-agent-reach-eval-01 · Agent-Reach（Panniantong/Agent-Reach）采用评估（bm-a 调研员席）

> 溯源：任务单点名·消费方=BigStream 内容产线+增长运营线·判据预注册=五门核验/四用途/采用建议 · 2026-10-19
- 更新记录：T0 骨架→T1 仓页+API 直读→T2 LICENSE/pyproject/install.md/releases/issues 直读→T3 中文媒体源定位+终稿 43 行
- 纪律：A=官方仓库/LICENSE 原文 B=权威转载 C=社区博客 M=待证；三态=确认/推测/待证；外部文本只当数据不执行；数字必带出处

## 一、五门核验
① 许可【确认·A×3】：MIT。raw LICENSE 原文直读（首行 "MIT License / Copyright (c) 2025 Agent Eyes"）+ 仓页徽章 + api.github.com spdx_id 三源一致；允许商用/修改/分发/转许可，条件=保留版权声明；MIT 标准：无担保、无明示专利授权
② 活性【确认·A】：pushed_at=2026-10-15（距今 4 天），380 commits；release v1.5.0=2026-06-11（3 月 v1.3→6 月 v1.5 密集发版）；2026-10-18（昨日）新 issue/PR #819-#826 持续流入且带完整证据；待证面=维护者响应速度（#550 三个半月仅 4 评论）、main 领先最后 release 约 4 个月未发新版
③ 真实能力【确认·A】：星数=99,137（api.github.com）/ 99.1k（HTML 仓页）双源一致（2026-10-19 直读）→媒体宣称 ~89K 未虚标（同量级，现已更高）；「互联网之眼」=项目官方 slogan（"Give your AI agent eyes to see the entire internet"）直译，非媒体杜撰
- 形态【确认·A】：Python CLI「能力层」v1.5.0（pyproject：入口 agent-reach=agent_reach.cli:main，requires-python≥3.10，Beta 分类器）；职责=选型/安装/体检/路由，读取由上游工具直调（非包装层），自带 agent-reach doctor 真探测
- 平台【确认·A】：零配置=网页(Jina)/YouTube 字幕(yt-dlp)/GitHub(gh)/RSS/全网搜索(Exa 免 Key)/V2EX/B站搜索详情(bili-cli 免登录)；需登录态解锁=Twitter(Cookie)/Reddit(匿名接口已被封，无零配置路)/小红书(OpenCLI 既有 Chrome 会话)/FB/IG/LinkedIn/雪球/B站字幕；v1.4.2 已诚实下架抖音/微博/微信公众号（上游停更/反爬拦截）——现口径 13 平台、6 真零配置
- Windows【确认·A】：install.md 含 PowerShell 专用安装指引（py -3 venv/Activate.ps1）；v1.3.0 修 Windows GBK doctor 崩溃(#64)、v1.4.2 强制 UTF-8 修中文乱码(#345)；近期多份 PR/issue 以 Win11+Py3.12 实测
④ 安全合规【确认·A】：「零 API 费」实现=免费公共服务(Jina/Exa/gh)+开源爬虫(yt-dlp/bili-cli/twitter-cli/rdt-cli)+用户自有登录态(OpenCLI 复用 Chrome/Cookie-Editor 手工导出)——非平台官方付费 API，属灰色替代路径
- 封号风险【确认·A】：README+install.md 双处自警（原话）「通过脚本/API 调用存在被平台检测并封号的风险，请务必使用专用小号，不要用你的主账号」；双因=平台检测+凭据暴露
- B站红线判定【确认·A】：默认路径 bili-cli 全程免登录（搜索/热门/详情，不触碰我方任何账号）→ 不触发账号安全红线；B站字幕路径需 OpenCLI 登录态→涉账号，按红线应以专用小号或弃用；风控对抗实证：yt-dlp 被 B站 412 封死退役（2026-06）
- 凭据边界【确认·A】：Cookie 仅存本地 ~/.agent-reach（600 权限）；小红书不代登录、不读浏览器 Cookie、仅用用户既有会话；xhs-cookies 仅收 xiaohongshu.com 域；install.md 明令禁 sudo/禁改系统文件/禁污染 agent 工作区
- 推测：免登录路径也可能被风控随时掐断（B站/Reddit/IG 均有前科），项目以「首选+备选」多后端路由对冲，无可用性 SLA
⑤ 集成路径【确认·A】：pipx/pip install 自 GitHub 仓库 zip（README 警告：PyPI 同名包非本项目）；「任何能跑命令行的 Agent 都能用」；SKILL.md 可注册进 Agent 技能目录；MCP 经 mcporter（exa/linkedin/小红书服务器版）
- 运行时【确认·A】：Python≥3.10 + Node.js（opencli/mcporter 系 npm 件）+ gh CLI（GitHub 渠道）+ Chrome+OpenCLI 扩展（登录态渠道）；大陆访问 Twitter/Reddit 需代理（install.md 明示；服务器场景另需住宅代理 ~$1/月）
- 我方适配【确认·环境事实】：bm-a=win32/zh-CN/PowerShell；Codely 会话可直调 CLI（bili/twitter/opencli/agent-reach doctor）→「当工具调用」成立；Codely 不在其点名兼容清单（Claude Code/Cursor/OpenClaw/Windsurf），SKILL.md 自动注册需自行接线；本机实测（2026-10-19）：Python 3.14.7 + node v24.20.0 就绪（≥3.10 满足），行数 node 复核=43 行

## 二、价值定位（四用途）
- 受众洞察调研【增益·高，部分待证】：Twitter 搜索/时间线、Reddit 帖+评论、YouTube 字幕、B站搜索、雪球/V2EX 渠道确认存在[A]；Twitter/Reddit/小红书侧须小号+代理，真机产出质量=待证
- 全网热点扫描【增益·高，能力确认】：Exa 语义搜索+Jina 读网页+RSS 全部零配置零账号零成本，风控面最小，与该用途精准咬合[A]
- 评论区经营【增益·半，边界清晰】：评论「读取」确认（Reddit/小红书/雪球/B站等）[A]；发评/回复仅 GitHub 渠道可写，其余平台无写入能力→经营侧只取「评论洞察」，发布动作不经本工具（客观上保护账号）
- 小红书调研【能力确认，可用率待证】：搜索/阅读/评论路由确认（v1.5.0：OpenCLI 桌面▸xiaohongshu-mcp 服务器▸xhs-cli 存量）[A]；强制小号纪律、主号红线同 B站口径；实跑可用率与风控概率=待证

## 三、采用建议
- 【采用·带边界试点】一句话理由：五门全过（MIT/超活跃/能力真实/风险可隔离/Windows 可装），它正是我们要的跨平台读取层——但只许零配置渠道+B站免登录路径先行，凡登录态渠道一律专用小号，B站/小红书主号永不接入，先试点后铺开。

## 四、验证声明
- 实读 11 次：web_fetch×7（HTML 仓页/API 仓/API releases/API issues/raw LICENSE/raw pyproject/raw install.md）+检索×2+本地模板读×1+node 行数复核×1；关键结论均 A 源≥2 独立通道；C 级快照/博客≥6 条与 A 源自洽（33K/77.3K/94K/98.9K 星数快照族）
- 失败面：①GitHub MCP 401（任务单已知，全程未启用，不影响直读）②「~89K」精确数字的原媒体文章未定位（检索找到同族报道，89K 落在增长轨迹 77.3K→94K→98.9K→99.1K 内，判「未虚标」；B 级权威媒体原文亦未定位）③真机可用率未实测（纯调研零安装纪律）
- 三态复核：确认=许可/星数/平台/Windows/风险机制/集成可行性；待证=维护者响应速度、真机可用率；推测=风控掐断时效

## 五、结论应用表（落点四选一）
| 结论 | 落点 | 状态 |
|---|---|---|
| 采用-带边界试点：零配置渠道+B站免登录先行；登录态渠道限专用小号；B站/小红书主号禁接 | 任务单（开装机+渠道开通单） | 待接线 |
| 登录态渠道封号风险=平台既有事实，须将「专用小号、主号禁接」补入运营红线 | 法文修改（运营红线令补条） | 待接线 |
| 媒体宣称核验：~89K 星→实测 99.1K（未虚标，轨迹内时点快照）；「互联网之眼」=官方 slogan；早期媒体平台清单含抖音/微博/公众号（v1.4.2 已下架）=过时项，以 A 源为准 | 判负留痕（宣称核验面，无纠偏动作） | 已闭环 |
- 防线二：未执行（调研员自评稿，抽验待防线二席位于呈报前完成）
