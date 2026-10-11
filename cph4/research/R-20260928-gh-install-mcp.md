# R-20260928-gh-install-mcp：GitHub MCP servers 普查（CEO 全面安装令·P-2026-09-28-15 调研面）

> 状态：**已完成**（2026-09-28·CPH4 调研员）| 姊妹件：R-20260928-gh-install-tools.md（工具面）/ R-20260928-gh-install-skills.md（skills 面）
> 纪律执行声明：**全程零安装零改系统**——仅 web_fetch / curl 只读下载到 $env:TEMP / search API；许可与元数据一律 api.github.com 直验（repos 端点 4/4 命中 + search 端点 8 发全命中）；死面如实记录；无「被带偏」事件（本轮所有 web_fetch 均命中目标页或明确 4xx/超限）。
> 本机环境事实（安装可行性基线）：node 24 有但无 npm/npx（Tuanjie Cowork 自带裸 node，Node LTS 补装中）；python 3.14 + uv/uvx ✓；Go ✗；Docker ✗；gh CLI 缺（工具面姊妹件在办）。
> 反重复门基线：Codely 已内置——文件读写/代码搜索/结构化记忆/多模态图像视频音频分析/Unity 工具/计划任务 cron/run_shell_command（最佳可用 Windows shell）/web_fetch；且 Codely 自带生成工具面（TTS/语音克隆/音乐/音效/图像/图像分层/视频/3D 生成与重拓扑/天空盒/精灵图集/资产库检索）。
> Codely settings.json mcpServers 配置面：stdio 型 {command,args,trust} + 远程型 {httpUrl,headers,timeout}。

## 一 结论应用表（结论|应用面|归属司/机|落地动作）

| # | 结论 | 应用面 | 归属司/机 | 落地动作 |
|---|------|--------|-----------|----------|
| 1 | **采：CoplayDev/unity-mcp** | Tuanjie/Unity 编辑器自动化（48 工具：场景/资产/脚本/测试/构建/ProBuilder/Profiling） | Biggame+BigDomain 开发面·bm-a | ①Unity UPM git URL `https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#main`（锁版 `#v10.0.0`）②`Window → MCP for Unity` 向导（Python3.10+uv ✓）③Codely 手动配置二选一：stdio `{command:"uvx", args:["--from","mcpforunityserver","mcp-for-unity","--transport","stdio"]}` 或远程 `{httpUrl:"http://localhost:8080/mcp"}`；Tuanjie 兼容 spike 按 CEO 批示先行 |
| 2 | **采：upstash/context7** | 全司研发线库文档「最新版」检索（Tuanjie/Unity/Python 量化库） | 全司研发·bm-a 起步 | Codely 远程 `{httpUrl:"https://mcp.context7.com/mcp"}` 免 key 试连（README 措辞 key=「Recommended 提额」非必需）；限速再走 context7.com/dashboard 领免费 key 入 headers |
| 3 | **采（挂起在 Node LTS）：microsoft/playwright-mcp** | QA 冒烟令「真跑 webgl demo+截图自判」的浏览器操控面 | 观测窗/游戏 web 面·bm-a | 待 Node LTS/npx 就绪 → stdio `cmd /c npx @playwright/mcp@latest`（官方 Windows 包裹律）；`--browser msedge` 可复用本机 Edge 免下载浏览器二进制；截图走 `browser_take_screenshot` → Codely 多模态自判；CLI 备案=microsoft/playwright-cli（Apache-2.0·13.6k★，coding agent 官方推荐路径，skills 姊妹件对接） |
| 4 | **采（低优先·PAT 安全门）：github/github-mcp-server** | GH issues/PR/Actions/Releases/code search——commit+push 本地 git 已覆盖，真增益在调研面 | CPH4 调研线·bm-a | 远程 `{httpUrl:"https://api.githubcopilot.com/mcp/", headers:{"Authorization":"Bearer <PAT>"}}`；**只读 PAT + --read-only 优先 + toolsets 白名单**（repos,issues,pull_requests 之类按需）；与 Agent-Reach 的 gh CLI 渠道部分重叠→装 Agent-Reach 后本件增益缩小，降级观察 |
| 5 | **采：nickclyde/duckduckgo-mcp-server** | Codely 无搜索工具的真空白（web_fetch 只能抓、不能搜） | CPH4 调研+BigStream 选题·bm-a | stdio `{command:"uvx", args:["duckduckgo-mcp-server"]}`（命令文本落地前以 README 直读为准）；DDG 抓取型免 key，被限速时备胎=yokingma/one-search-mcp |
| 6 | **采（AGPL 边界内）：Comfy-Org/comfy-mcp** | bm-c ComfyUI 产线结构化（生成/模型/节点检索+workflow 提交跟踪+批量队列） | BigCompute·bm-c | `pip install comfy-mcp`（官方 PyPI·requires_python>=3.10）→ stdio 由 Codely 拉起；**双许可 AGPL-3.0 或商业许可：内部产线工具可用须标注边界·禁入产品交付链·禁做对外网络服务**（否则触发 AGPL §13 源码披露） |
| 7 | **采：Panniantong/Agent-Reach** | B站/小红书/YouTube/Reddit/Twitter 读搜层（skill+CLI+MCP 混合能力层，非单 MCP server） | BigStream 内容调研·bm-a | 按官方 install.md 流程装 CLI（`agent-reach install` 默认安全检查模式；**`--system` 须显式批准才动系统**）；零配置渠道先行（网页 Jina Reader/B站 bili-cli 免登录/YouTube 字幕/RSS/GitHub）；cookie 平台（XHS/Twitter/Reddit/FB/IG）一律**专用小号**（README 明示封号风险）；内含 Exa 免 key MCP 搜索与 #5 部分重叠→装后并轨观察 |
| 8 | **低优先候选：Alex2Yang97/yahoo-finance-mcp** | bm-b 行情/历史价/财报/期权/新闻会话查询 | BigMoney·bm-b | Python/uvx stdio（启动命令落地前直验 README）；yfinance=非官方数据通道（Yahoo ToS 灰区注记）；回测主算力仍在自研 python 管线，本件只做会话内查数 |
| — | 其余全部 parked | 见 §三 | — | 不装 |

## 二 采用候选逐件（repo|api 直验★|license spdx_id|pushed_at|安装方式+依赖|业务契合一句话|五门初判）

1. **CoplayDev/unity-mcp**（api.github.com/repos ✓·full_name 实为小写 unity-mcp·默认分支=beta）
   - ★14,552 · **MIT** · pushed 2026-09-27 · C# · 非归档 —— 与在案事实「MIT·14.5k★」吻合 ✓；当前 release v10.0.0（2026-06-30）；Aura 赞助维护；ACM SA'25 论文在案
   - 安装+依赖（README+官方 docs 直验）：要求 **Unity 2021.3 LTS→6.x**（Tuanjie=2022.3 分支→版本面兼容）+ **Python 3.10+（uv 管理，本机 ✓）**；三路安装=UPM git URL / Asset Store / `openupm add com.coplaydev.unity-mcp`；PyPI 服务端真名=**mcpforunityserver**（本批两次猜名 404 后经官方 install 页定谳）；Codely 官方手动配置二选一：stdio `uvx --from mcpforunityserver mcp-for-unity --transport stdio`（Windows 示例给全路径 `C:/Users/<user>/AppData/Local/Microsoft/WinGet/Links/uvx.exe`）/ HTTP `http://localhost:8080/mcp`（Codely {httpUrl} 直配）；自动配置支持 12+ 客户端（Claude 系/Cursor/VS Code/Windsurf/Cline/Copilot CLI/Codex/Qwen/Gemini/OpenClaw/Antigravity），Codely 不在内→手动
   - 工作原理一句话：Unity 编辑器内 C# 插件（MCPForUnity）暴露编辑器操作（48 工具/25 只读资源），本地 Python 服务端（FastMCP+WebSocket hub）把 MCP 会话桥接到编辑器插件，会话从不直连 Unity
   - 业务契合：游戏/元宙城核心生产力——AI 会话直控 Tuanjie 编辑器；spike 已获 CEO 批
   - 五门：契合✓（核心产线）·反重复✓（Codely 内置 Unity 工具≠编辑器内操控，真增量）·许可✓MIT·健康✓（昨日仍推送）·成本安全✓（本地、默认无遥测自述；编辑器内执行=信任面与 trust 旗标对齐）
2. **upstash/context7**（api ✓）
   - ★62,491 · **MIT** · pushed 2026-09-28（当日活跃）· TypeScript
   - 安装+依赖（README 直验）：**远程 `https://mcp.context7.com/mcp` 免本地依赖**——API key 为「Recommended（提速率限额）」非必需→免 key 试连起用；免费 key=context7.com/dashboard（OAuth）；本地 stdio=`npx @upstash/context7-mcp`（卡 npx）·CLI+skills 模式=`npx ctx7 setup`（同卡）；工具=resolve-library-id / query-docs
   - 业务契合：全司研发线拿版本定向的最新库文档，治模型过时训练知识与幻觉 API
   - 五门：契合✓·反重复✓（web_fetch 可抓文档页但 context7 给 LLM 优化+版本定向，省多轮往返）·许可✓MIT·健康✓（当日推送）·成本安全✓（免费；库名/查询词出境到 Upstash 云=轻微数据面注记，禁贴敏感代码）
3. **microsoft/playwright-mcp**（api ✓）
   - ★37,642 · **Apache-2.0**（注意非 MIT——Apache 含专利授权条款，过集团红线面）· pushed 2026-09-25 · TypeScript · Microsoft 官方
   - 安装+依赖（README 直验）：标准 stdio `{command:"npx", args:["@playwright/mcp@latest"]}`（**Node≥18，Windows 须 `cmd /c npx ...` 包裹律**）→挂起在 Node LTS 补装；Docker 法仅 headless chromium（本机无 Docker 出局）；`--browser chrome|firefox|webkit|msedge` 可用系统浏览器免下载；`--caps vision/pdf/devtools`；截图工具 `browser_take_screenshot`（filename/fullPage/scale）+ 隔离 profile `--isolated`
   - **README 官方自陈分流**：coding agent 更宜姊妹件 **microsoft/playwright-cli**（CLI+SKILLS·token 更省；api ✓·Apache-2.0·★13,635·pushed 2026-09-18）；MCP 面宜持久浏览器状态/自愈测试/长自治环——两路 Codely 都支持，MCP 记本件、CLI 归工具/skills 姊妹件
   - 业务契合：QA 冒烟令闭环=navigate→wait→screenshot→Codely 多模态自判（WebGL 面无头渲染须 spike 实测，SwiftShader 软渲染兜底）
   - 五门：契合✓（冒烟令立法）·反重复✓（Codely 无浏览器工具）·许可✓Apache-2.0·健康✓·成本安全△（免费；首跑下载浏览器二进制约百 MB 级→msedge 通道可免；README 明言 MCP 非安全边界→隔离 profile+工作区根限 file 访问）
4. **github/github-mcp-server**（api ✓）
   - ★33,251 · **MIT** · pushed 2026-09-25 · Go · GitHub 官方
   - 安装+依赖（README 经 curl 落盘 grep 直验——web_fetch 超 10 万字符内联上限，换只读通道）：远程 `{url:"https://api.githubcopilot.com/mcp/", headers:{"Authorization":"Bearer <PAT>"}}`（部分客户端 OAuth，PAT 优先制在案）；本地=发布二进制 `github-mcp-server stdio` + env `GITHUB_PERSONAL_ACCESS_TOKEN`（免 Go 工具链；Docker 亦可选但本机无）；`--toolsets repos,issues,pull_requests,actions,code_security` 白名单制；**`--read-only` 旗标在案（优先级最高，写工具全跳）**
   - 业务契合：commit+push=本地 git 已覆盖（真增益不在此）；issues/PR/Actions 读写+GitHub code search=调研面与仓库运营面真增益
   - 五门：契合△→✓（调研面）·反重复△（与 Agent-Reach 的 gh CLI 渠道部分重叠·单选观察）·许可✓MIT·健康✓·成本安全△（**PAT 凭证面=最大安全抓手：只读 PAT+最小 scope+toolsets 白名单起步**；远程型配置恰配 Codely {httpUrl,headers}）
5. **nickclyde/duckduckgo-mcp-server**（search API ✓——search 端点返回 license/★/pushed_at 同为 api.github.com 直验）
   - ★1,510 · **MIT** · pushed 2026-09-04 · Python · 190 forks
   - 安装+依赖：Python/PyPI 包（uvx 可拉）；启动命令本批未逐字直验，落地前以 README 直读为准
   - 业务契合：填「不给 URL 就找不到」的搜索空白——调研线与内容选题线省「猜 URL→web_fetch」往返
   - 五门：契合✓（真空白）·反重复✓·许可✓MIT·健康△（月内推送但单人小仓=bus factor 注记）·成本安全✓（免 key；DDG 抓取型有被限速风险；查询词出境 DDG=轻微注记）
6. **Comfy-Org/comfy-mcp**（search API repo: 直验 + LICENSE 原文直读 + comfy.org/mcp 官方页直验 + PyPI JSON 直验）
   - ★238 · **license=NOASSERTION→LICENSE 原文定谳：双许可 AGPL-3.0-or-later 或商业许可（licensing@comfy.org）** · pushed 2026-09-20 · Python · 2026-07-01 建仓（Comfy-Org 官方新件）；PyPI comfy-mcp v0.10.0（summary：「MCP server for ComfyUI — a thin wrapper over comfy-cli」·requires_python>=3.10）
   - 安装+依赖（comfy.org/mcp 直验）：**本地连接=`pip install comfy-mcp`（开源·stdio 客户端拉起·驱动本机 ComfyUI·免 key 免账号免费）**；云连接=`https://cloud.comfy.org/mcp`（OAuth/API key·产图耗 Comfy 积分·需订阅）——集团只采本地连接
   - 业务契合：bm-c SDXL 城市量产线（R-20260926-sdxl-city-production 正典）从 shell 裸调升级为会话内结构化（生成/模型/节点/模板检索+workflow 提交跟踪+批量队列），官方维护=贴引擎版本
   - 五门：契合✓·反重复△→✓（结构化面增量·spike 定增量大小）·**许可⚠AGPL 双许可：内部产线工具面可用须标注·禁入产品交付链·禁做对外网络服务（否则 §13 源码披露义务）**·健康✓（官方·月内推送）·成本安全✓（本地免 key）
7. **Panniantong/Agent-Reach**（search API ✓ + README 全文直验）
   - ★85,884 · **MIT** · pushed 2026-09-15 · Python（3.10+）· 2026-02 建仓 7 个月 8.5 万星（Trendshift 在案）
   - 定性与安装（README 直验）：**skill+CLI 能力层，非单 MCP server**——替 Agent 选型/安装/体检/路由各平台读取：零配置渠道=网页（Jina Reader）/B站（bili-cli·免登录）/YouTube（yt-dlp 字幕）/RSS/GitHub（gh CLI）；MCP 接入=Exa 语义搜索（mcporter·免 key）等；登录态渠道=小红书/Twitter/Reddit/FB/IG（OpenCLI 复用 Chrome 会话或 Cookie）；安装=`agent-reach install` 默认只读检查、**`--system` 显式批准才动系统**；`agent-reach doctor` 渠道体检；凭据仅存本地 `~/.agent-reach/`（600 权限）
   - 业务契合：BigStream 视频号/公众号/B站内容线的选题+素材+口碑调研一站式；CPH4 调研线亦受益
   - 五门：契合✓（内容线正中）·反重复△（Exa 搜索与 #5 重叠→装后并轨单选观察；gh CLI 渠道与 #4 重叠→#4 降级）·许可✓MIT·健康✓（活跃·自述平台封路即换后端路由）·成本安全△（免费；**cookie 平台封号风险——一律专用小号禁主账号**；登录态=敏感凭证面入 fleet 安全章程）
8. **Alex2Yang97/yahoo-finance-mcp**（search API ✓·低优先）
   - ★356 · **MIT** · pushed 2026-09-19 · Python
   - 安装+依赖：Python/uvx stdio（启动命令落地前直验 README）
   - 业务契合：bm-b 会话内查行情/历史价/财报/期权/新闻（回测主算力仍在自研管线）
   - 五门：契合△（增益=会话查数便利）·反重复✓（Codely 无行情工具）·许可✓MIT·健康✓（月内推送）·成本安全△（yfinance 非官方通道=Yahoo ToS 灰区注记·数据仅供内部研究）

## 三 parked+理由（逐件如实）

1. **Ollama 生态 MCP servers（整体面）**：search「ollama mcp」top10 全为「支持 Ollama 的 UI/框架/自托管栈」，**无一件 Ollama 专用 MCP server**；ollama/ollama 官方 README 全文无 MCP 字样（只有 REST API localhost:11434+客户端集成名单；docs.ollama.com/mcp 405 死面）。反重复门从严定谳：python 直调 localhost:11434（run_shell_command 可达）已覆盖——一个把本地 LLM 包成工具的 server 只省一层 curl；未来若要「会话调度本地模型当子代理」10 行 python 即达。**parked：无官方件+反重复**（Ollama 自身 MCP 客户端能力=未验明，docs 405 无法定谳）
2. **open-webui/open-webui**（★153,416·license=NOASSERTION「Other」带品牌条款）：AI 会话 UI=Codely 角色重复+许可杂音——反重复+许可双 parked
3. **BeehiveInnovations/pal-mcp-server**（★11,758·NOASSERTION·2025-12 后未推）：多模型路由聚合——Codely 模型槽+本地直调已覆盖；license 未验明——许可门不过
4. **heshengtao/super-agent-party + comfyui_LLM_party**（★2,706/2,370·AGPL-3.0）：AI 伴侣/直播向——AGPL 三红线禁入产品交付链+与数字居民自研栈重叠，仅记录
5. **aqm857886159/Nomi**（★530·AGPL-3.0）：AI 视频工作台——同 AGPL 红线 parked
6. **ATH-MaaS/Pixelle-MCP**（★1,120·MIT·pushed 2025-12-17≈9 个月未动）：健康门不过（停更面）
7. **artokun/comfyui-mcp**（★769·MIT·README 顶部公告直验：**「no longer maintained…repo will be archived on 2026-10-09」，官方 Comfy MCP/Agent 已上位**）：健康门判负；其官方继任者 Comfy-Org/comfy-mcp 已采（§二.6）——本件记为过渡参照
8. **yokingma/one-search-mcp**（★143·MIT）：多引擎搜索聚合——与 #5 nickclyde 件重叠单选（选 ★10 倍者）；DDG 被限速时回头作备胎
9. **wshobson/maverick-mcp**（★678·MIT·pushed 2026-09-27）：个股分析 MCP——分析面与 bm-b 自研回测重叠，单选数据面 yahoo-finance-mcp；分析我们自己做，parked
10. **modelcontextprotocol/servers 官方参考系**（Fetch/Filesystem/Git/Memory/Sequential Thinking/Time/Everything）：**一律 parked——Codely 内置全覆盖**（fetch=web_fetch·filesystem=读写工具·git=run_shell_command+本地 git·memory=结构化记忆·sequential-thinking=会话内建·time=系统日期+cron）。勘误留痕：本调研员初稿曾记「该仓 2025-03 已归档」——**错**，raw README 直验修正：仓未归档，仅第三方 server 子集（brave/github/gitlab/gdrive/postgres/puppeteer/redis/sentry/slack/sqlite 等）迁 servers-archived；现役参考件自陈「参考实现、非生产就绪」；许可=Apache-2.0（新贡献）+既有 MIT。Parked 理由=反重复+官方自陈非生产定位
11. **desktop-commander 等社区 shell/命令执行类**：run_shell_command 已覆盖——反重复 parked
12. **bilibili-mcp-js**（★193·MIT·pushed 2026-03-30≈半年未动）/ **huccihuang/bilibili-mcp-server**（★190·MIT·pushed 2025-04-21 停更）：健康门不过；B站读取面由 Agent-Reach（bili-cli 活跃路由）承接
13. **JimmyLv/bibigpt-skill**（★127·**license=null**）：非 MCP（skill 面）+许可门不过+外付 BibiGPT API——归 skills 姊妹件提示，MCP 面 parked
14. **ZJU-REAL/Easel**（★2,044·Apache-2.0·pushed 当日）：社交媒体「发现趋势+创作+**一键发布**」整 agent 产品——非单 MCP server；**发布面需各平台登录凭证（安全门重）**；BigStream 若走第三方发布栈再议——观察名单不采
15. **HuggingFace 官方 MCP server**：search「huggingface mcp server」未命中官方件（**未验明**）；evalstate/mcp-hfspace（★388·MIT·2025-06 停更+Spaces 调用与 Codely 生成工具面重叠）parked；本地 LLM 管线的模型检索由 web_fetch+HF 网页可达，无真空白
16. **B 站/公众号/视频号「发布类」MCP 总注**：本轮普查未见健康+免凭证两全的发布件——发布面走各平台官方后台/专用小号+人工或 Easel 型整栈评估，不在 MCP 安装清单（安全门判据：平台凭证即敏感面）

## 四 实搜面实录（查了哪些源/端点、死面记录、被带偏记录）

**方法面**：普查策略=「search API 定向扩面 + api.github.com 逐件直验」替代整单拉取 awesome-mcp-servers（该清单无 license/元数据、逐件直验成本高；本轮 8 发定向 search 已覆盖六条业务线：游戏/Unity、量化、内容媒体、本地 LLM、ComfyUI 产线、通用搜索/GitHub/HF/B站面）。modelcontextprotocol/servers raw README 直验过门；**MCP Registry（registry.modelcontextprotocol.io）记为官方浏览面**（README 直验在案），后续轮可作扩面源。punkpeye/awesome-mcp-servers 未直验（参考源注记）。

**api.github.com/repos 端点（5 发）**：microsoft/playwright-mcp ✓ · github/github-mcp-server ✓ · CoplayDev/unity-mcp ✓ · upstash/context7 ✓ · github/github-mcp-server/releases/latest **403 rate limit exceeded（死面·如实记录）**——限流后按「换端点再试」纪律改走 search 端点（独立配额）完成全部补验，无一件因限流而降级为「未验明」。

**api.github.com/search 端点（8 发·全命中）**：ollama+mcp（total 4029·top10 全非专用件→Ollama 定谳）· duckduckgo+mcp（total 243）· comfyui+mcp（total 348→浮出 artokun→反转→官方件）· repo:Comfy-Org/comfy-mcp（total 1·license NOASSERTION→LICENSE 原文定谳 AGPL 双许可）· yfinance+mcp（total 147）· repo:microsoft/playwright-cli（total 1）· huggingface+mcp+server（total 88·官方件未命中）· bilibili+mcp（total 153→浮出 Agent-Reach 85884★）。

**raw.githubusercontent.com（9 发·1 死面）**：unity-mcp@beta README ✓ · playwright-mcp@main README ✓ · context7@master README ✓ · github-mcp-server@main README **超 web_fetch 10 万字符内联上限被拒（非死面·非带偏）→换 curl 只读落盘 $env:TEMP\ghmcp-readme.md + Select-String grep 通道命中**（remote URL/PAT/--read-only/toolsets/二进制 stdio 全取）· modelcontextprotocol/servers@main README ✓（勘误「归档」误记）· ollama@main README ✓（无 MCP 字样）· Comfy-Org/comfy-mcp@main LICENSE ✓（AGPL 双许可定谳）· artokun/comfyui-mcp@main README ✓（停更公告）· Agent-Reach@main README ✓（MCP 模式定性）· CoplayDev docs http-vs-stdio.md **404（死面）→换 sitemap.xml 定位正确路径成功**。

**官方 docs/站点（5 发·1 死面）**：coplaydev.github.io 首页 ✓ + /getting-started/clients ✓（12 客户端矩阵+Codely 不在内）+ /getting-started/install ✓（**PyPI 真名 mcpforunityserver+Windows uvx 全路径+HTTP 8080/mcp 全取**）+ sitemap.xml ✓ · comfy.org/mcp ✓（本地/云双连接+pip install comfy-mcp）· docs.ollama.com/mcp **405 Method Not Allowed（死面）→Ollama 官方 MCP 面标「未验明」**。

**PyPI JSON（3 发·2 死面）**：mcp-for-unity **404** · unity-mcp **404**（两死面均为猜包名失败→经官方 install 页定名 mcpforunityserver，未再回验 PyPI——下次落地时直验）· comfy-mcp 超 10 万字符→curl 落盘本地解析 ✓（v0.10.0·requires_python>=3.10·license 字段空→以 GitHub LICENSE 定谳）。

**被带偏记录**：**零**——本轮所有 web_fetch 均命中目标页或明确 4xx/超限（与 09-28 记忆在案的 BitNet/HF 带偏先例不同）；超限/404/405/403 各面均按换源律处置并如实留痕。

**零安装声明**：全程未装任何包、未写任何系统配置；curl 仅落盘 $env:TEMP 临时文件（ghmcp-readme.md/comfy-mcp.json），未清理（后续会话可删）。

**遗留给下一轮**：①Node LTS 就绪后解锁 playwright-mcp（npx 面）+context7 本地 stdio 备份路；②unity-mcp Tuanjie spike（CEO 已批）实操回报；③comfy-mcp AGPL 边界标注入 fleet 安全章程后 bm-c 落地；④Agent-Reach cookie 平台小号供给制（BigStream 定账号策略）；⑤github-mcp-server 只读 PAT 签发流程（安全门配套）；⑥mcpforunityserver 与 duckduckgo-mcp-server 启动命令文本落地时直验。
