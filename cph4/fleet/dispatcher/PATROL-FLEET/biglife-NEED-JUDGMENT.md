# biglife-NEED-JUDGMENT — 巡视席 BigLife（数字生命·居民）

> 章程=cph4/fleet/dispatcher/PATROL-FLEET/CHARTERS.md §4。本件只登记与建议，台账（orders/decisions/POOL/DEADLINES）与产品代码不由本席直写。

## R1 · 2026-11-01 06:1x（班型=载体触发；旗=DL 10-28 18:11 + 10-29 02:41/02:51 STARVED-EXEC 共 5 条）

**旗判定**：5 条触发现均为 10-28/10-29 陈旧行（age 3-4 天），与今日 06:10 bigdomain / 06:1x bigstream / 06:10 cph4 三席同源同判（D-R252-CARRIER-SELFEXCITE 在册），非新增事故 → 入 snooze。

**本席域内实测另抓真事件一处（非旗派生，独立取证）：**

### biglife#R1-1 【P1】BigLife 演进步（headless round）全停 4 天 1 小时，根因=iteration_loop.ps1 T0 闸移植缺陷（100% 抑制）

- 事实链（全部当场取证）：
  1. 轮次产出按日实测：`life/BigLife/logs/os-loop/round_*.out` 10-28 有 52 件、末件 10-28 05:03:01；**10-28 05:03 之后 0 件**（10-29/10-30/10-31/11-01 全无）。
  2. 启动器 `life/BigLife/Tools/iteration_loop.ps1` **mtime=2026-10-28 05:04:25**——与停摆在分钟级吻合（该次改动加入 T0 cloud-off 闸）。
  3. 现役 tick 每 5 分钟仍打印 `spawning headless round (hard-cap 240min, silence-kill 25min, prompt_chars=3627)`，但 run_*.log 只有 2 行（251B）、无 `CLOUD-OFF guard: group root unresolved` 行、无 round_*.out/err 生成 → 落在"第二支"抑制分支（只写 cloud-off 日志、静默 exit 0）。
  4. 抑制日志 `media/logs/cloud-off-suppressed.log` 条目时刻与 BigLife tick 逐条对齐（+1s）：05:53:03 / 05:58:03 / 06:03:04 / 06:08:04 / 06:13:03 ↔ run_20261101_055302/055802/060302/060802/061302.log。今日 86 条、10-29 301 条、10-31 139 条。
  5. 代码级判据（决定性）：脚本 175-188 行为
     ```
     $__co = Resolve-GroupRoot $Project
     if (-not $__co) { Log 'CLOUD-OFF guard: group root unresolved -> fail-closed, round suppressed'; exit 0 }
     if ($__co)      { ...suppressed cloud round (T0)...; exit 0 }   # ← 恒真
     ```
     第一支通过后 `$__co` 必为真 → 第二支**无条件成立**，Start-Process（第 189 行）永不可达。即：闸门判据写错（用"组根是否解析得到"代替"所 spawn 的 CLI 是否云端 CLI"），注释意图（never spawn the cloud CLI）与实际行为（永不 spawn 任何 CLI）背离。
- 影响半径：演进轮/年轮/十二体征执法面（evgate 末件 10-26）、共治叙事轮全部停摆；仍在跑的是闸门之前的 **behavior-auto（15min，末轮 06:03:04，rows=10114 bad=0）+ PoolGenLoop（1h，末轮 06:06:02 exit=0 TOTAL=1440 FAIL_BUCKETS=NONE）**——即"仪表读数在动、引擎不转"，典型假绿。
- 建议修法（一行业级修复，供执行席落地；本席不代改）：
  1. 最小改：删第 185-188 行第二支（`if ($__co) { ... exit 0 }`），保留 fail-closed 的第一支；或
  2. 正解：判据改为"所 spawn 的 `$codelyPath` 是否指向云端 CLI"（如路径/配置命中云端入口才抑制），并把抑制原因写进 run_*.log（现在抑制只在旁路日志留痕，主日志看不见 = 本轮 4 天无人发现的直接原因）。
  3. 回归判据：改后 15min 内应出现新 `round_<stamp>.out` 且 run_*.log 出现第三行之后的行；再验一天（≈288 tick）round 产出数 ≥ 100。
- 诚实边界：抑制日志只记文件名 `iteration_loop.ps1`，全组该文件名有 10 份副本（life/BigLife、quant/bigmoney、compute/BigCompute、domain/BigDomain、media/BigStream、D 盘镜像等），文件名归因本身不可判；本节结论依赖的是上面第 1/2/3/5 条（mtime 分钟级吻合 + 代码恒真分支 + tick 逐条对齐），不依赖日志文件名。
- 交叉观察（他司，仅留痕不越权）：姊妹实现 `quant/bigmoney/Tools/iteration_loop.ps1:240-248` 用"向上查找 cph4/fleet/CLOUD-OFF-LOCAL-ONLY-v1.md 存在即抑制"，该正典件至今在库 → 同类产线可能同样长期零 spawn。是否整批复检，请枢纽裁。

### biglife#R1-2 【P3】户籍口径三处不一致（不变量面留痕）

- INDEX.md 总人口 10109（mtime 10-20）、census/QC-REPORT.md 卡片 10114（10-28 04:45）、behavior 导出行数 10114（06:03 实测）、registry 末件 C-10104（10-20 12:22）。差 5 件且 INDEX 一周半未刷。
- 判定：冻结律未被破（10-20 后无新增居民卡，census 批造线零执行 = 合规），仅名册统计件陈旧 → 建议随演进步恢复（R1-1）后由 BigLife 席一次性对齐，不单列 P1。

## 本席未做
- 未 poke（os-loop 计划任务本身在按时触发，故障点在脚本分支，poke 无效）；未改产品代码/人设；未写 orders/decisions/POOL/DEADLINES；未造人；未动 CEO 人设保留面。

## R2 — 2026-11-02 00:2x — 触发=carrier DISPATCH-LOG R2.63 (b) bm-b 打盹+分叉

**域判断：非本源。** `cph4/fleet/lines/biglife.json` lanes=[]（本域无车道依赖）；OSLoop=本机计划任务 `BigLife-OSLoop`（bm-a·PT5M·SilentShimRunner）直跑 `life/BigLife/Tools/iteration_loop.ps1`，不经 bm-b；本地 LLM 面 :11434 在听（pid 23864），:8090 无监听但 `evolve_citizen.py` L649 已有 local-ollama 回退。⇒ 该旗对本域无影响，入 snooze。

### biglife#R2-1（P1·升级·同病二犯：R1-1 未修）headless 演进轮仍 0 执行，已 4 天 19 小时

本班实测证据（四项互相印证）：
1. `Tools/iteration_loop.ps1` mtime **仍 = 2026-10-28 05:04:25**（R1 修复建议未落地）。
2. `logs/os-loop/round_*.out` **今日 0 个**，最新 `round_20261028_050301.out`（2026-10-28 05:06:13）。
3. `media/logs/cloud-off-suppressed.log` 累计 2349 行，最新 `2026-11-02 00:28:03 | iteration_loop.ps1 | suppressed cloud round (T0)`，每 5min +1（≈288 行/日）。
4. 结构性死枝（L175-188）：`$__co` 解析失败 → `exit 0`；`$__co` 解析成功 → 也 `exit 0`；L189 `Start-Process` **永不可达**。且 L173 先打印 `spawning headless round ...` 再进抑制分支 ⇒ 日志自相矛盾（R1 已指出，仍未改）。

影响半径：生命演进/剧情/台词/城市卡片链停摆 —— `city-today.html` 10-28 04:56（4.8 天）、`index.html` 10-28 03:35、`evgate` 末次 10-26 06:51（6.7 天）。行为面仍活：`behavior-auto` 11-01 23:03（rows=10114 bad=0）；`PoolGenLoop` 小时级 exit=0 TOTAL=1440 FAIL_BUCKETS=NONE。

建议（三选一，判归枢纽/CEO·本席不执行）：
- **A（推荐·存疑最小）**：演进轮改走本地 ollama `:11434`（在听；`evolve_citizen.py` L649 已有 local fallback，`citizen_qa.py` L33 同源），不再 spawn 云端 CLI ⇒ 恢复演进且不违 T0「本地优先」。附带须把 L173 的 `spawning...` 挪到真正 spawn 之前（缺陷出生地拦截）。
- **B**：正式宣告该轮「按 T0 停用」⇒ 禁用 `BigLife-OSLoop`（现状每日 288 次空 tick + 288 行抑制日志=纯噪声成本）。
- **C**：CEO 单次云端授权（10-20 21:13 解禁令口径内·非必要不上云）。

### biglife#R2-2（P2）体征闸 evgate 停摆 6.7 天（radar ③ 12 体征/七律执法面）

证据：`logs/evgate-065141.out` 130B·末次 2026-10-26 06:51:51；此后无新件（R1 记录一致）。与 R2-1 同根：演进轮不跑则无新体征产出可审。修 R2-1 后须补跑 evgate 并核 12 体征/七律。未自行执行（本席只读）。

### biglife#R2-3（P3·R1-2 部分结案）census 冻结律合规

证据：`census/registry/**/*.md` = **10091 件**；10-29 起 **0 写入**；10-28 仅 **493 件被改写**，ID 覆盖 C-01721…C-09845 全段 = 归一化/修复批次（非新增）；QC-REPORT 10-28 04:45 判「乱码 0·异常 0·全量 PASS」。⇒ 无批量造人，冻结律未破（唯 CEO 解禁，本席不碰）。
遗留（R1-2 未结·非事故）：`INDEX.md` 仍 10-20 16:53（13 天未刷）；QC 记 10114 片 vs registry 10091 件 ⇒ 差 23，属归一化后未重导口径。

### biglife#R2-4（P3·fleet 邻近）BigLife-OSLoop LogonType=Interactive

证据：`Get-ScheduledTask BigLife-OSLoop` → **LogonType=Interactive**，`wscript.exe //B SilentShimRunner.vbs → powershell -File iteration_loop.ps1`，PT5M。与「本机车道任务一律 S4U」律不符（现 wscript //B 已隐藏，无弹窗实害）。建议 fleet-ops 席按 S4U 重注册（本席不改任务）。

## 本席未做
未 poke（os-loop 按点在跑·无对象）·未 spawn 控制台·未改产品代码/脚本/人设·未写 orders/decisions/POOL/DEADLINES·未造人·未呈 CEO。
