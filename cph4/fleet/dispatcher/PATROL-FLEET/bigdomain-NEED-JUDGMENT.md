# bigdomain — NEED-JUDGMENT 台账

> 域标：**bigdomain**（巡视席·BigDomain 硅基域）。本件只记需裁决项，裁决权=枢纽；本席不直写 orders/decisions/POOL。
> 格式：`- [状态] 条目` + 证据指针 + 候选处置（不代决）。

- [OPEN 2026-11-01 06:0x] **D:\FluxGroup\domain\BigDomain 是同 remote 的第二克隆，落后 12 天且带本地脏改**
  - 事实：两处同源（origin=git@github.com:BigRain-11122/BigDomain.git）。直播正身=`C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain`（HEAD 21ea75c9，2026-11-01 05:49 提交，git 0/0 同步，R2313 在跑，24h 内 434 文件落盘）；`D:\FluxGroup\domain\BigDomain`（HEAD c99b68f6，末提交 2026-10-20 18:18 R2059，**落后 12 天**，`git status` dirty=1，24h 内 0 文件变更）。
  - 正典未分叉：两侧 `BLUEPRINT.md` SHA256 前 16 位相同（A09378500115BA33）——漂移只在代码/数据层，不在法面。
  - 危害（本班实锚）：本席先读到 D 树，按「末提交 10-20 + 日志断 10-21」差点判定「BigDomain 域休眠 11 天/OSLoop 假绿 12 天」，顺 C 树复核才推翻。任何按 D 路径垂读的巡视/复盘都会得出同一错判。
  - 已核：仓库工具面无引用（`Tools\*.ps1|*.py`、`cph4\fleet\dispatcher` 全扫 0 命中），故不构成生产事故，仅人/agent 阅读面污染。
  - 候选处置（择一，候枢纽）：①归档 D 副本（移 `_offload`/`media/_trash`，可逆）；②保留但落 `D:\FluxGroup\domain\BigDomain\STALE-README.md` 指针行（「正身=C 树，本件 12 天陈旧，禁垂读」）；③若确需 D 盘双备份，改为定期 robocopy 镜象并禁本地提交。