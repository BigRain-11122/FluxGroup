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
