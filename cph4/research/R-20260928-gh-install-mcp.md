# R-20260928-gh-install-mcp：GitHub MCP servers 普查（CEO 全面安装令·P-2026-09-28-15 调研面）

> 状态：【采集中】骨架先行·边查边更新（早落盘律）
> 调研员纪律：只调研绝不安装；许可/★数/pushed_at 一律 api.github.com/repos/<org>/<repo> 直验；查不到标「未验明」禁编造；普通 GH 网页被带偏≠源不存在，换 api 端点再试才可判负。
> 本机环境事实（安装可行性基线）：node 24 有但无 npm/npx（Tuanjie Cowork 自带裸 node，Node LTS 补装中）；python 3.14 + uv ✓；Go ✗；Docker ✗。
> 反重复门基线：Codely 已内置——文件读写/代码搜索/结构化记忆/多模态图像视频音频分析/Unity 工具/计划任务 cron/run_shell_command（最佳可用 Windows shell）/web_fetch；且 Codely 自带 MCP 型生成工具（TTS/语音克隆/音乐/音效/图像/图像分层/视频/3D 生成与重拓扑/天空盒/精灵图集/资产库检索）。
> Codely settings.json mcpServers 配置面：stdio 型 {command,args,trust} + 远程型 {httpUrl,headers,timeout}。

## 一 结论应用表（结论|应用面|归属司/机|落地动作）
（采集中——已有暂记见 §二/§三，收拢后填）

## 二 采用候选逐件（repo|api 直验★|license spdx_id|pushed_at|安装方式+依赖|业务契合一句话|五门初判）

### 种子面·已 api 直验（元数据 4/4 命中）
1. **microsoft/playwright-mcp**（https://api.github.com/repos/microsoft/playwright-mcp ✓）
   - ★37,642 · **Apache-2.0**（注意：非 MIT·Apache 含专利授权条款·集团三红线=GPL/AGPL 禁入产品链，Apache 过门）· pushed 2026-09-25 · TypeScript · 非归档 · Microsoft 官方维护
   - 安装（README 直验）：标准 stdio 配置 `{command:"npx", args:["@playwright/mcp@latest"]}`；要求 **Node.js ≥18**（本机 npx 缺位 → 落地挂起 Node LTS 补装）；Docker 法 `mcr.microsoft.com/playwright/mcp`（仅 headless chromium·本机无 Docker 出局）。截图工具 `browser_take_screenshot`（filename/fullPage/scale）+ `--caps vision/pdf/devtools` 扩展。
   - **README 官方自陈分流**：coding agent 更宜姊妹项目 **microsoft/playwright-cli（CLI+SKILLS，token 更省）**；MCP 面宜持久浏览器状态/自愈测试/长自治环——两条路 Codely 都支持（skills 在案），MCP 面采本件，CLI 面在姊妹工具件记备案。
   - 业务契合：QA 冒烟令「真跑 webgl demo+截图自判」闭环=navigate→wait→screenshot→Codely 多模态分析自判。
   - 五门初判：契合✓（冒烟令立法）·反重复✓（Codely 无浏览器工具）·许可✓Apache-2.0·健康✓（9/25 仍推送）·成本安全✓（免费本地跑·首跑下载浏览器二进制约百 MB 级·README 明言 MCP 非安全边界→隔离 profile+禁 --allow-unrestricted-file-access）
2. **github/github-mcp-server**（api ✓）
   - ★33,251 · MIT · pushed 2026-09-25 · Go · 非归档 · GitHub 官方
   - 安装面（README 113k 超 web_fetch 内联上限→已换 curl 落盘 grep 通道采集中）：远程 https://api.githubcopilot.com/mcp/ + PAT（远程型 {httpUrl,headers} 直配）；本地=发布版二进制（免 Go 工具链）。**需 PAT=安全门重点**。
   - 业务契合：集团 git 工作流=commit+push（本地 git 已覆盖）——真增益集中在 issues/PR/Actions/Releases 读写与 GitHub code search（调研面真增益）。
3. **CoplayDev/unity-mcp**（api ✓·full_name 实为小写 unity-mcp·默认分支=beta）
   - ★14,552 · MIT · pushed 2026-09-27 · C# —— 与在案事实「MIT·14.5k★」吻合 ✓·当前 release **v10.0.0**（2026-06-30）·47 个 MCP 工具入口·Aura 赞助维护·ACM 论文在案
   - 安装（README 直验）：Unity 侧=Package Manager → Add from git URL `https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#main`（可锁 `#v10.0.0`；或 `openupm add com.coplaydev.unity-mcp`）；配置=`Window → MCP for Unity → Configure All Detected Clients`。要求 **Unity 2021.3 LTS→6.x**（Tuanjie=2022.3 分支 ✓ 版本面兼容）+ **Python 3.10+（uv 管理）**（本机 uv ✓）。Codely 不在官方自动检测客户端名单→手动 stdio 配置命令查 docs（采集中）。
   - 工作原理一句话：Unity 编辑器内 C# 插件暴露编辑器操作（场景/资产/脚本/测试/构建 47 工具），本地 Python MCP 服务端（uv 管理）把 stdio MCP 会话桥接到编辑器插件。
   - 业务契合：游戏/元宙城核心生产力——AI 会话直控 Tuanjie 编辑器；Tuanjie 兼容 spike 已获 CEO 批。
4. **upstash/context7**（api ✓）
   - ★62,491 · MIT · pushed 2026-09-28（当日活跃）· TypeScript · homepage=context7.com
   - 安装（README 直验）：**远程 https://mcp.context7.com/mcp 免本地依赖**——README 措辞 API key 为「Recommended（提速率限额）」非必需，初判可免 key 试连；免费 key 走 context7.com/dashboard（OAuth）。本地 stdio=`npx @upstash/context7-mcp`（卡 npx 缺位）；另有 CLI+skills 模式 `npx ctx7 setup`（同卡）。工具=resolve-library-id / query-docs。
   - 反重复判：web_fetch 能抓文档页，但 context7 提供版本定向+LLM 优化文档检索——增量成立（省多轮「翻文档站→截取」往返）；与 Codely 内置无重叠。
   - 业务契合：全司研发线（Tuanjie/Unity/Python 量化库）拿最新版库文档，治模型过时训练知识。

### 扩面候选（GitHub search API 直验——search 端点返回 license/★/pushed_at 同样构成 api.github.com 直验）
5. **nickclyde/duckduckgo-mcp-server**（search API ✓）
   - ★1,510 · MIT · pushed 2026-09-04 · Python · 190 forks · 非归档
   - 安装：Python 包，`uvx duckduckgo-mcp-server` 即可（uv ✓ 本机可用）；依赖 duckduckgo_search 库（无官方 API 的抓取型）。
   - 反重复判：**Codely 有 web_fetch 但无搜索工具**——本件填「给一个 URL 能抓、但不给 URL 就找不到」的真空白，替调研/内容线省「先猜 URL 再抓」的往返。
   - 业务契合：调研线（R-件普查）、AI 媒体内容线选题检索。
   - 五门初判：契合✓（搜索空白）·反重复✓·许可✓MIT·健康✓（月内推送·单人维护小仓=中等风险注记）·成本安全✓（免 key 免费·DDG 抓取型有被限速风险·查询词出境到 DDG=轻微数据面注记）
6. **Comfy-Org/comfy-mcp（Comfy 官方 MCP）**（comfy.org/mcp 直验·★/license/pushed_at 采集中）
   - 官方页直验：**本地连接=开源 comfy-mcp，PyPI `pip install comfy-mcp`，stdio 由客户端拉起，驱动本机 ComfyUI，免费无账号**（uv/pip 本机可用 → 安装可行性 ✓）；云连接=远程 `https://cloud.comfy.org/mcp`（OAuth/API key·产图耗 Comfy 积分）——集团只需本地连接。
   - 反重复判（从严）：run_shell_command+ComfyUI REST API 已可裸跑触发——官方件真增量=「生成/模型/节点/模板检索+workflow 提交跟踪+批量队列」结构化工具面（Comfy 官方维护=比任何社区件更贴引擎版本）；bm-c ComfyUI 产线契合成立。
   - 业务契合：bm-c SDXL 城市量产线（在案正典 R-20260926-sdxl-city-production）从「shell 裸调」升级为「会话内结构化编 workflow+批量」。
   - 五门初判：契合✓·反重复△→✓（结构化面增量·待 spike 定增量大小）·许可待验（ComfyUI 核心系 GPL-3.0——**若 comfy-mcp 同 GPL：纯内部产线工具可用但须标注边界、禁入产品交付链**）·健康✓（Comfy-Org 官方·comfy.org 当日活跃）·成本安全✓（本地连接免 key 免费·云连接不采）

## 三 parked+理由（逐件如实）
1. **Ollama 生态 MCP servers（整体面）**：search「ollama mcp」top10=全部是「支持 Ollama 的 UI/框架/自托管栈」（open-webui 153k★·PDFMathTranslate·docker-android·langchain4j·pal-mcp-server·Kiln 等），**无一为「Ollama 专用 MCP server」**。反重复门从严定谳：本机管线=python 直调 localhost:11434（run_shell_command 可达），一个把本地 LLM 包成 MCP 工具的 server 只省一层 curl 调用——增量不足；且真空白（若未来要「让 AI 会话把本地模型当子代理调度」）可用 10 行 python 脚本经 run_shell_command 达成。**parked：无官方件+反重复**。（注：Ollama 自身新版本的 MCP 客户端方向=另一面，见 §4 采集中）
2. **open-webui/open-webui**（153,416★·license=NOASSERTION「Other」）：角色=Codely 的重复（AI 会话 UI）；license 带品牌条款杂音——反重复+许可双 parked。
3. **BeehiveInnovations/pal-mcp-server**（11,758★·NOASSERTION·pushed 2025-12-15）：多模型路由聚合（Gemini/OpenAI/Ollama 合一）——Codely 模型槽+本地直调已覆盖；license 未验明=许可门不过。parked。
4. **heshengtao/super-agent-party + comfyui_LLM_party**（2706★/2370★·**AGPL-3.0**）：AI 伴侣/直播向——AGPL 三红线禁入产品交付链，且与数字居民自研栈重叠；仅记录不采。
5. **aqm857886159/Nomi**（530★·AGPL-3.0）：AI 视频工作台（ComfyUI+MCP）——同 AGPL 红线，parked。
6. **ATH-MaaS/Pixelle-MCP**（1,120★·MIT·pushed 2025-12-17≈9 个月未动）：健康门不过（停更面），parked。
7. **yokingma/one-search-mcp**（143★·MIT）：多引擎搜索聚合——与 #5 nickclyde 件功能重叠，单选制 parked（选了 ★数 10 倍的 nickclyde 件；若 DDG 限速再回头）。
8. **filesystem / memory / fetch / sequential-thinking / desktop-commander 类**（含 modelcontextprotocol/servers 官方参考系）：**一律 parked——Codely 内置已覆盖**（文件读写=读写工具、代码搜索=search_file_content、记忆=结构化记忆三件套、fetch=web_fetch、sequential-thinking=会话内建推理、desktop-commander=run_shell_command）。modelcontextprotocol/servers 仓 2025-03 起归档（raw README 直验中，见 §4）——归档仓即使功能不重也过不了健康门。

## 四 实搜面实录（查了哪些源/端点、死面记录、被带偏记录）
- 2026-09-28 调研开始：本件为 P-2026-09-28-15（CEO「去 github 找公司能用到的所有环境、工具、skills、mcp 等，全面安装」）的 MCP 面；姊妹件 R-20260928-gh-install-tools.md（工具面）/ R-20260928-gh-install-skills.md（skills 面）。
- （待补：各端点逐条实录）
