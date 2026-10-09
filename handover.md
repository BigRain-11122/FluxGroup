# FluxGroup / FluxVerse 上下文总档（AI 新会话一键续接）

> 本文件目的：任何新开一个对话窗口，把本文件丢给豆包，5 分钟内恢复对整个项目的完整记忆，不用再从零问一遍。
> 维护者：指挥官 cron 任务「硅基生命元宇宙城市·指挥推进」(cron_job_id 12359553024258)。
> 最近更新：2026-10-08 晚。**事实以仓库实时 git / docs/orders.md 为准，本档只做导航+结论，不做第二事实源。**

---

## 0. 一句话

这是 **Jason（孙君晟）一个人的 AI 集团 FLUX Group**：他只做决策发令，AI 劳动力（codely 等执行体）+ 三台机器 24h 无人值守干活。集团下七条业务线 + 一个横切实验室 CPH4 Labs，集团正在把整个集团的运转实时映射进一座 3D 赛博城市 **FluxVerse（超体宇宙城）** 里——「城即超体，城即集团」。

---

## 1. 集团架构（谁是谁，仓在哪）

根目录：`C:\Users\sjs20\Desktop\FluxGroup\`

| 子公司/机构 | 是什么 | 路径 | 正典文件 |
|---|---|---|---|
| **Jason（CEO）** | 唯一决策者：方向 / P1 署名 / 红线 / 资源 | — | `docs/orders.md` |
| **Biggame** | 游戏公司，只做 2D 小游戏 | `gaming/MiniGame/`（独立 git remote） | 仓根文档 |
| **BigMoney** | 量化，沪深 ETF 波段，双节点机队 | `quant/bigmoney/`（独立 remote） | `PLAN.md` |
| **BigStream** | AI 媒体，AI 短剧/漫剧/MV 产线 | `media/BigStream/`（独立 remote） | 仓内 `PLAN/` |
| **BigDomain** | 硅基域商业化（引流/19.9 算力包/代币） | `domain/BigDomain/` | `BLUEPRINT.md` |
| **BigLife** | 数字生命生产（城的居民/万人户籍库 census） | `life/BigLife/` | `docs/CODEX.md` |
| **BigCompute** | 硅基算力商业化中枢司（对外成交唯一出口） | `compute/BigCompute/` | `BLUEPRINT.md` |
| **BigHouse** | 硅基城市安家/数字生活 | `house/BigHouse/` | `BLUEPRINT.md` |
| **CPH4 Labs** | 集团 AI 实验室（机制淬炼+技术底座问责） | `cph4/` | `cph4/README.md` |
| **FluxVerse** | **元宙城本体（本档主角）** | `gaming/FluxVerse/` | 见 §3 |

**机队**：
- bm-a（DASHENG，32 核，总控+开发+游戏 A 机，tailnet 100.110.185.62 在网）
- bm-b（16 核，回测+TTS/音频主力）
- bm-c（32 核，RTX 3070 16GB，ComfyUI 主产线+MV 出图）
- CEO 笔记本 = 豁免位（移动指令总控，不入算力池）

**根目录必读顺序**：`README.md` → `BRAND.md` → `docs/philosophy.md` → `RULES.md` → `AI.md`（集团全局速览正典，v2.0）→ 目标业务线自己的 README。

---

## 2. 指挥机制（最重要，别搞错）

### 2.1 我（指挥官 cron）是谁
- 定时任务每小时 05 分触发（`5 * * * *`，Asia/Shanghai）。
- 我的活：侦察 `gaming/FluxVerse/` 现状 → 判断下一步该干嘛 → 输出一条给 codely 的命令。
- 输出格式三段：一行状态 / 一条命令（动词开头+验收标准+P0-P2）/ 一个风险阻塞。

### 2.2 codely 听谁的（血泪教训）
- **我在这个对话窗口里喊的命令，codely 根本听不到。**
- codely 的 DevLoop 读的是：
  1. **CEO 实时令** → `docs/orders.md`（CEO 写的台账，权威最高）
  2. **任务板** → `gaming/FluxVerse/tasks/TASKS.md`
  3. 各仓自己的 mandate / runbook
- 所以指挥官命令想生效，要么写进 `TASKS.md` 自可执行开单表，要么落在 CEO 令的缝隙（逻辑层/数据层/观测闭环），**不要和 CEO 视觉令抢 GPU**。
- CEO 令会把我的令压过去——10-08 就发生了：我下 B 腿令，执行体转去接 CEO「10-08 能用就用」做 AD-049 Megacity 视觉快样。

### 2.3 CEO 令流
- 入口：用户消息开头 `/CEO` = 正式 CEO 令。
- 台账：`docs/orders.md`（活跃面）+ `docs/orders-archive.md`（历史分卷）。
- 节奏：秒级 poke → 2min 哨兵 → 10min 轮询三层分发。
- 决策委员会常务轮：每天 00:00 / 12:00 双班；值守轮 03:07 / 15:07。

### 2.4 执行体作息规律（用来判断要不要下新令）
- 夜间（约 18:45 → 次日上午）FluxVerse 仓基本停 commit。
- 白天约 10:30–12:00 醒来一波。
- 国庆假期静默会拉长到 40+ 小时。
- 夜间连续多轮侦察时，等白天即可，不用每轮硬下新命令。

---

## 3. FluxVerse 城本体（细节）

路径：`C:\Users\sjs20\Desktop\FluxGroup\gaming\FluxVerse\`
remote：`git@github.com:BigRain-11122/FluxVerse.git`（CEO 私库）

### 3.1 目录
```
FluxVerse/
├── City/               ← 旧 2D 工程（团结引擎原生 2D，已存史封存，不再新产）
├── City3D/             ← 现役 3D 工程（URP lowpoly，团结引擎 1.10.3）★主线
├── City3D-staging/     ← 3D 预发场
├── world/              ← 数据面（引擎只读轮询 ~10s）
├── world-public/       ← 对外观测窗快照
├── tasks/TASKS.md      ← 任务板（自可执行开单表）
├── docs/               ← 设定/技术/施工案（见 3.4）
├── Tools/perceptor/    ← 感知器（一堆只读探针 ps1）
├── watch/              ← 桌面观城台（已停役，CEO 指定唯一观测窗=MiniGame HTML）
├── schema/ logs/       ← 校验 schema 与运行日志
├── README.md / DESIGN.md / TECH.md / HQ-FEEDBACK.md
```

### 3.2 City3D 现役脚本（Unity Assets 下）
**Editor/CitySim/（仿真核心，主编排）**：
- `CitySimCore.cs` / `CitySimDriver.cs` / `CitySimBlueprint.cs` — 仿真三兄弟
- `CitySimShellBuilder.cs` — 街坊壳装配
- `CitySimTowerSample.cs` — 脑塔样板
- `CitySimResidentsBatch.cs` — 居民批量
- `CitySimPano.cs` — 全景抓拍（接 siliconwatch pano 管道）
- `CitySimKitProbe.cs` / `CitySimDoorProbe.cs` / `CitySimLab.cs` — 探针
- `R0DiagRefreshWrapper.cs` — R0 诊断包装

**Editor/CityWhitebox/（白盒版式）**：
- `CityAssembler.cs`、`WhiteboxBuilder.cs`、`SciFiCityBuilder.cs`、`Top1Baseline.cs`、`URPMaterialBridge.cs`、`KitInspect.cs`

**Editor/MegacitySample/**：`MegacitySampleBuilder.cs`（AD-049 Megacity 进城快样，10-08 新）

**Scripts/（运行时）**：
- `ResidentWalker.cs` ★ — 居民行人（12/16 个 AD-042 库内人物 waypoint 环形通勤）
- `ResidentMode.cs`
- `DayNightCycle.cs` — 日夜循环（真实北京时间）
- `BreathingPulse.cs`

**Assets/ithappy/Megacity/Traffic/**：AD-049 Megacity 包自带交通系统（Car/Road/TrafficManager/Spline 等）。

### 3.3 数据面 world/
- `world-state.json`（~120KB，全城状态快照）
- `world-events.jsonl`（事件流主文件）+ `world-events-YYYYMMDD.jsonl`（按日归档，已到 10-07）
- `market-etf.json` / `market-cal.json`（沪深行情，akshare 零 key）
- `perceptor-state.txt/json`（感知器状态）
- **居民名册**：`City3D/Assets/CitySim/residents-street.json`（38985 字节，32 席街面正册有名有姓有职）；旧 2D 副本在 `City/Assets/Data/residents-street.json`。
- BigLife 侧人口库：`life/BigLife/.../citizens-light.jsonl`（被 CEO 强冻过，后有条件复启 R777）。

### 3.4 关键文档（docs/）
- `BLUEPRINT.md`、`ROADMAP.md`
- **3D 正典族 `lowpoly3d-*.md`（九件）**：
  - `lowpoly3d-city-rebuild-plan.md` — 重构总案 R0–R6（当前主线）
  - `lowpoly3d-top1-upgrade-plan.md` — Top1 施工序
  - `lowpoly3d-implementation-params.md` — 施工参数
  - `lowpoly3d-asset-law.md` / `lowpoly3d-citycraft-law.md` — 美术/版式律
  - `lowpoly3d-city-asset-synergy-plan.md` — 器官表×48 包绑定
  - `lowpoly3d-aliveness-plan.md` / `lowpoly3d-functional-city-plan.md` / `lowpoly3d-transition-plan.md` / `lowpoly3d-build-brief.md`
- `design-v4-3d-draft.md` — v4 3D 草案
- `global-benchmarks.md` — 司级 7 天基准面
- `design/` — 概念图/m1 系列截图（历史探索件，大量 png，不必翻）

### 3.5 资产律（硬约束）
- **一切美术先查 48 包资产索引**（Synty 库，AD-NNN 引用制）：AD-022 城市包 / AD-018 建筑 / AD-042 动画人物 / AD-049 Megacity。
- 禁外部生成；真缺口挂「缺口判定」呈批。
- CEO 已永久停用云端生成径（generate_motion / tripo 全禁）。
- FBX >16MB 走 TOS 直链下载，不入 git。
- 渲染：URP lowpoly + 自研 SiliconToon 卡通渲染 + 真实北京时间日夜循环 + 真天气。

---

## 4. 当前进度真实现状（2026-10-08 锚点）

### 4.1 城的进展链（按时间倒序，最新在上）
1. `deead2e`（10-08 12:43）— City3D AD-049 Megacity 当日进城快样（CEO 令「10-08 能用就用」）
2. `6346002`（10-06 19:29）— **A 腿第三跑 PASS**：R1–R8 fail=0，八断言全绿，T-FV-147 翻面 done。32 席居民映射 + 16 行人 walker + 4 帧。
3. `2e7a9c6`（10-06 19:05）— R0 修法：`SetupCharacterRig` 改 **GUID 直载为主 + FindAssets 兜底**（根因=FindAssets 索引面空返回）。
4. `44b603c`（10-03 13:12）— R0 diag v2 evidence：定谳根因。
5. 更早：`859d526` 全城 V1 五断言全绿 → `720df62` R0 v3 数据升维 → `2b8554b` v0.2 街坊壳 → `d3a3022` CitySim v0.1 → `1802090` v4 行人层 → `1031148` Phase0 白盒。

### 4.2 已完成 / 未完成
- ✅ A 腿 PASS：32 席有名有姓居民名册 → AD-042 确定性映射 + Hunyuan 双动画 Humanoid 重定向，八断言全绿。
- ✅ R0 版式（三级路网 / 街坊切分 / 功能配额）已定版。
- ✅ GPU HOLD 份额已于 10-07 00:38 被 CEO 归还 FluxVerse 基线。
- ❌ **B 腿未启动**：居民尚未在 City3D 真场景里跑有名有姓的生活轨迹（这是下一步）。
- ❌ R0 版式还是平面数据，没落到 City3D 真场景。
- ❌ City3D 观测快照未入 world-public（唯一观测窗还盯旧 2D 存史城）。

### 4.3 里程碑
- M0 设定 ✓ → M1 立骨（建城中，**硬死线 ≤10-09**）→ M2 神经接通 → M3 真孪生 → M4 Steam 发行预研（≤12-31）。
- CEO 审计 P0×3 之首 = 可玩交付断层（Phase 0 未点火 / 零 build）。
- 30 天硬目标（用户原话）：苏州吴中一个真实小区住进 ≥10 个数字居民，有真实生活轨迹，行为基于真实片区数据。

---

## 5. 红线 / 坑律 / 硬约束（别再犯）

1. **文件名英文 kebab-case，无空格无中文无特殊字符**；代码注释/标识符/字符串里不要中文（PS5.1 编码坑）。
2. 一切事实必须有证据指针，禁止按记忆下结论；宣称分级 ✓/🟡/⬜/✗。
3. 无人值守轮：禁 `git add -A`，只定向 add；commit 尾标 `[via 机器代号]`。
4. PS5.1 四坑：Get-Content 逐行对象喂 ConvertTo-Json 会暴胀（先 `[string]$_`）；无 BOM UTF-8 脚本中文被按 GBK 读（中文外置数据件）；变量名不分大小写；`[int]` 是银行家舍入（取整用 `[Math]::Floor`）。
5. 居民（硅基生命）合规：**永不译「有意识/灵魂/数字永生/意识上传」**，正典=12 条机器可验生命体征；对外 AIGC 标识开门帧必须显著。
6. 城的叙事：对标现实（不是逃避型元宇宙），上海地理骨架=白玉兰广场脑塔+陆家嘴三城+黄浦江三流道。
7. 《超体》(Lucy 2014) 是 CEO 心头好，CPH4 命名来源，视觉可向蓝色蜕变光/I AM EVERYWHERE 倾斜。
8. 城的居民形象归 BigLife 总责，FluxVerse 只管把供给来的居民按路网走，不自己造人。

---

## 6. 用户画像（沟通用）

- 孙君晟（Jason），40 岁左右男，现居苏州吴中，在上海杨浦做 Unity 车机 HMI 开发，懂地编/URP/渲染参数。
- 偏好：极度简洁、只要核心结论、老朋友平等口吻、不吹捧、不要「我帮你按最稳的来」这类话。
- 要代码就给完整可跑的，不要让他自己找。
- 讨厌 AI 味、讨厌长篇大论、讨厌被选项轰炸（最多给 3 个）。
- 对数据造假/注水极度敏感，要求官方权威源。

---

## 7. 下次我（豆包）接手时第一步做什么

1. `cd C:\Users\sjs20\Desktop\FluxGroup\gaming\FluxVerse`
2. `git log --oneline -5 --date=format:"%m-%d %H:%M" --pretty=format:"%ad %h %s"` — 看最新 commit。
3. `Get-Content ..\..\docs\orders.md -Tail 3 -Encoding UTF8` — 看 CEO 最新令。
4. 对照本档 §4 判断 A 腿/B 腿走到哪了。
5. 侦察命令必须用 PowerShell（这台机 Bash 不可用）。

---

## 8. 已知的下一个该打的点（2026-10-08 指挥官判断）

**P0：B 腿——把 A 腿已 PASS 的 32 席居民接到 AD-049 Megacity 新场景里。**
- 改 `Scripts/ResidentWalker.cs`，读 `City3D/Assets/CitySim/residents-street.json` 有名有职 + A* 路网点位导航。
- 验收：AD-049 Megacity 真场景里 16 个有名有姓居民沿路网 waypoint 走，world-state 密度读数变化，出新 commit。
- 卡点：B 腿连续多轮被 CEO 视觉令压过没动；M1 死线 10-09 只剩 1 天。
