# bigdomain — NEED-JUDGMENT 台账

> 域标：**bigdomain**（巡视席·BigDomain 硅基域）。本件只记需裁决项，裁决权=枢纽；本席不直写 orders/decisions/POOL。
> 格式：`- [状态] 条目` + 证据指针 + 候选处置（不代决）。

- [OPEN 2026-11-01 06:0x] **D:\FluxGroup\domain\BigDomain 是同 remote 的第二克隆，落后 12 天且带本地脏改**
  - 事实：两处同源（origin=git@github.com:BigRain-11122/BigDomain.git）。直播正身=`C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain`（HEAD 21ea75c9，2026-11-01 05:49 提交，git 0/0 同步，R2313 在跑，24h 内 434 文件落盘）；`D:\FluxGroup\domain\BigDomain`（HEAD c99b68f6，末提交 2026-10-20 18:18 R2059，**落后 12 天**，`git status` dirty=1，24h 内 0 文件变更）。
  - 正典未分叉：两侧 `BLUEPRINT.md` SHA256 前 16 位相同（A09378500115BA33）——漂移只在代码/数据层，不在法面。
  - 危害（本班实锚）：本席先读到 D 树，按「末提交 10-20 + 日志断 10-21」差点判定「BigDomain 域休眠 11 天/OSLoop 假绿 12 天」，顺 C 树复核才推翻。任何按 D 路径垂读的巡视/复盘都会得出同一错判。
  - 已核：仓库工具面无引用（`Tools\*.ps1|*.py`、`cph4\fleet\dispatcher` 全扫 0 命中），故不构成生产事故，仅人/agent 阅读面污染。
  - 候选处置（择一，候枢纽）：①归档 D 副本（移 `_offload`/`media/_trash`，可逆）；②保留但落 `D:\FluxGroup\domain\BigDomain\STALE-README.md` 指针行（「正身=C 树，本件 12 天陈旧，禁垂读」）；③若确需 D 盘双备份，改为定期 robocopy 镜象并禁本地提交。
   - **[第二轮·2026-11-02 00:2x 复核：仍未决，升格候枢纽收]** D 副本仍在（无 `STALE-README.md`；其 `src\os\iteration_loop.ps1` mtime=2026-10-20 18:27）；C 树正身 HEAD=5070b522（R2354 于 23:57:47 提交，`git status` 0/0）。危害面与首轮一致（按 D 路径垂读必得错判），候选处置①②③不变，本席不擅动他树。

- [OPEN 2026-11-02 00:2x] **域产线被云端并发帽整轮放弃（假绿：任务 result=0 而本轮零工作）**
  - 机制：`domain\BigDomain\src\os\iteration_loop.ps1`（196-208 行）在 `live>=2` 时整轮 `exit 0` 放弃，只写 `logs\cloud-cap.log` 一行；`live` 统计全机 `codely.exe` 且命令行带 ` -p "` 的无头会话。
  - 事实：2026-11-02 **00:04 / 00:09 / 00:14 / 00:19 四连 CLOUD_CAP_DEFER live=3-4**（cap>=2）⇒ 自 R2354（23:57:47）起**零产出约 30min**；同期任务 `BigDomain-OSLoop` 报 `last=00:19:01 result=0 next=00:24`（表面全绿）。
  - 量级（`logs\cloud-cap.log` 累计 1030 行）：10-25=71 / 10-26=50 / 10-27=78 / 10-28=57 / 10-29=10 / 10-31=17 / 11-01=31 / 11-02=4。
  - 计数面异常（为什么夜间更重）：`live` 把**巡视席自身**计入（本班载体 pid 52284 即一条 `codely.exe -p`），夜间多席并发 + 各线轮同时点火 ⇒ 互相饿死。
  - 候选处置（候枢纽，不代决）：① `live` 计数排除 `patrol-fleet-carrier` 起的巡视会话；② 给各司轮次域级配额（或 cap 抬到 3-4）；③ BigDomain 轮改本地档（承 10-20 云令「非必要不云端」）；④ 保留现状但把 defer 记账为 EXPECTED-IDLE 而非绿，防假绿。

- [观察·未定归因 2026-11-02 00:2x] `media\logs\cloud-off-suppressed.log` 23:56-00:18 有 6 行「iteration_loop.ps1 | suppressed cloud round (T0)」，但 C 树 BigDomain 祖先链**无** `cph4\fleet\CLOUD-OFF-LOCAL-ONLY-v1.md`（仅 `D:\FluxGroup\` 有），故**不是本域轮**（本域走 cap-defer 分支）；疑他线经 junction 物理根命中 D 盘标记。仅留证不升格，供枢纽归因。
- [OPEN->升级 2026-11-02 00:5x · 第三轮] **云端并发帽使域轮结构性饿死（cap>=2，而夜间巡视舰队自身 live=2-4）**
  - 复测（本轮实锚，替换上一轮「~30min」读数）：`logs\cloud-cap.log` 00:04/00:09/00:14/00:19/00:24/00:29/00:34/00:39/00:44/00:49 共 **十连** CLOUD_CAP_DEFER（今日累计 10 行）；最后一次成功轮产物 `logs\round_20261101_235401.out` mtime=00:01:09（对应 R2354 commit 5070b522 @00:00:47），至本席判定时刻 **约 50 分钟零产出**。
  - 阈值面加固证据：00:34 / 00:39 / 00:44 三行 **live=2 即 defer**——`src\os\iteration_loop.ps1:203-204` 判据为 `-ge 2`，故不是「机器忙才让路」，而是任意两条 `codely.exe -p` 共存即整轮放弃（exit 0）。
  - 现场 pid 级：本轮 live=3 = pid53160（bigmoney 轮）+ **pid61732（本席·BigDomain 巡视载体）** + pid62660（bigstream 巡视）——**巡视舰队自身吃满帽**，域轮在巡视时段结构上不可能点火；夜间十域班同窗 ⇒ 近乎确定性饿死。
  - 假绿面：任务 `BigDomain-OSLoop` `LastTaskResult=0 / Next=00:54`，表面全绿，真实语义是「放弃本轮」；任何按任务结果判健康的监督面（含本席首读）都会读成健康。
  - 饿死有成本（在队真活）：`src\os\backlog.md` carried 行 R2355 首项=提交树上全量电池（预注册 485 套件 / 3886 判据），R2354 收轮明写「电池未跑，顺延 R2355」——已连续 10 个 5 分钟格点无法开工。
  - 候选处置（不变，择一，候枢纽）：① `live` 计数排除 `patrol-fleet` 载体会话（最小改面）；② 各司域级配额，或 cap 抬到 3-4；③ 域轮改本地档（承 10-20「非必要不云端」令；本地 35B 不需 codely 会话即可彻底解耦本约束）；④ defer 记账为 EXPECTED-IDLE/DEFERRED 而非 result=0，防假绿。
  - 本席不建议继续观察：同夜三轮读数单调恶化（30min→50min，且 live=2 即 defer 已证），属机制面非抖动 → **升级候枢纽收**。

- [OPEN 2026-11-02 00:5x] **BigDomain-OSLoop 注册为 InteractiveToken（违 2026-09-29「本机车道任务一律 S4U」律）**
  - 实测：`Get-ScheduledTask BigDomain-OSLoop` → `Principal.LogonType=Interactive`（UserId=sjs20 / RunLevel=Limited），State=Ready，触发器每 5 分钟。
  - 违律与历史：2026-09-29 判例（10-15 复检）要求本机一切车道计划任务 S4U；本域 backlog 侧已连续披露 100+ 轮（carried 行 `loop-s4u-reconcile`，`state\debt.md` 在档）。
  - 为何长期未修：重注册需**提权** shell；无人值守会话触 UAC=弹窗，违静默律，故历代轮次只披露不动手（本席同样不动手）。
  - 候选处置（候枢纽/CEO 侧一次提权执行）：导出 `%TEMP%\bigdomain-osloop-backup-*.xml` → 改 LogonType=S4U、SWA=false → 重注册 → 读回 `LogonType` 验 S4U、并实测一轮出 `round_*.out`。
  - 关联：若采纳上条处置③（域轮改本地档），本项优先级可降，但 Interactive 本身仍属违律态。

- [观察·非本域 2026-11-02 00:5x] PATROL-FLEET/LOG.md 存在既存编码损坏：681 非空行中 11 行带 U+FFFD（2491 字符，集中在 642 行之后的近期行），疑为早期会话经 GBK 控制台写入所致。本席追加行已复核 0 替换字符（UTF-8/LF 直写）。仅供枢纽归因与修账参考，本席不改他席台账、不修他人行。
