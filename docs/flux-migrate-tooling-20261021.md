# FLUX-MIGRATE-TOOLING v1 — FluxGroup 全量迁 D 盘工具链（2026-10-21·千问席制）

> 令源：CEO 2026-10-21 原话「Library你给我清了，然后把flux所有文件都给我腾挪到D盘去」。
> 实测基线：仓总 158.3G；Library 缓存合计 ≈49.9G（MiniGame projects 37.4 + 吸嘟嘟 2.34 + FluxVerse City3D 5.5/City 2.03/其余散项）；**净迁移面 ≈102.6G / 1,050,148 文件**（robocopy /L 干跑口径·已排除 Library 与 _offload junction）。
> 目的地：`D:\FluxGroup\`（D: 现剩 3511G，容量无忧）。_offload 保持现状（已在 D:\FluxGroup-Offload，junction 不复制）。

## 一、执行序（三步·每步独立可停）

### STEP A · 清 Library（回 C 盘 ≈50G）
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\sjs20\Desktop\FluxGroup\Tools\purge-library-cache.ps1"            # WhatIf 报表
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\sjs20\Desktop\FluxGroup\Tools\purge-library-cache.ps1" -Apply    # 真删
```
- 安全闸内建：只删**无编辑器进程占用**的工程 Library；被占用（当前=metis/GUIAgent/P3D 在开）自动 SKIP 并列表上报。
- 代价如实：重开各工程触发全量重导入（P3D_Spike 11.6G 那个最久），一次性的。

### STEP B · 全量复制到 D（源零改动）
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\sjs20\Desktop\FluxGroup\Tools\migrate-fluxgroup-to-d.ps1"            # 纯复制+校验报告（幂等可续跑）
```
- robocopy /E（非 /MIR——目标侧绝不删除任何东西），排除 `Library`（防把缓存又拷回去）与 `_offload`（junction 跳过）；日志落 `D:\FluxGroup-migrate.log`。
- 102.6G 内部磁盘对拷，跨盘并行度默认 8。

### STEP C · 切换（你点头后我才做·唯一动原目录的一步）
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\sjs20\Desktop\FluxGroup\Tools\migrate-fluxgroup-to-d.ps1" -Cutover
```
前置硬条件（脚本自检）：STEP B 回执 FAIL=0 且字节账对齐 → 才允许切。
动作：①先 `git fsck` + `git bundle create D:\FleetBackup-20261020\bundles-live\FluxGroup-all-refs.bundle --all`（根仓+8 子仓全 refs 现场版兜底，昨日备份不含 gaming/media 工作树，这一步不可跳）→ ②确认无编辑器/无头会话持锁 → ③整目录改名 `FluxGroup -> FluxGroup.old`（**保留不删**）→ ④同名 junction `C:\...\Desktop\FluxGroup -> D:\FluxGroup`（全部绝对路径引用照常有效，含计划任务/脚本内硬编码 root）→ ⑤读回验证（junction 可访问+git status 干净+随机抽 20 文件字节比对）→ ⑥出回执件。
- **FluxGroup.old 至少保留 7 天**，你确认一切正常后才谈清理，且走回收站不走永删。

## 二、风险登记（如实）

| 风险 | 缓解 |
|---|---|
| 编辑器开着时切目录=崩当前会话 | STEP C 前我列占用清单，等你收工窗口执行 |
| junction 上 git 行为差异 | git 对 junction 透明（同 _offload 判例）；bundle 先行兜底 |
| 外部引用按 C 路径寻址 | junction 保形，零改引用 |
| 大文件 >95MB git 红线 | 迁移不动 git 内容，仅换物理位 |
| 中途断电/中断 | robocopy 幂等续跑；C 步前源始终完好 |

## 三、当前状态

- [x] 预检完成（体积/占用/junction/git 面实测）
- [ ] STEP A 待点火（WhatIf→Apply）
- [ ] STEP B 待点火
- [ ] STEP C 候你收工窗口+点头
