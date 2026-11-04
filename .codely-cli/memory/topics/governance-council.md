
- [2026-10-20 23:10:13] 文档「整理」判例（CEO 令「先好好回忆和理解 别搞错了」→全量回退）：①整改期规则/章程 md 默认停+删除预算，整理=减法（删/合并/修指针），**禁新增索引章节或扩写规则**；②执行位不碰主控面文档（governance/council/resource-chain）无票；③正确顺序=只读盘点（重复/被取代/零引用/断链）→验证引用→呈清单→再动；仅指针修复（断链勘正）属保留动作。

- [2026-11-02 13:22:54] TCC「可移除卷」拦 launchd（2026-11-02 两次实测）：launchd 起的 bash 与 python 写 `/Volumes/<外置盘>` 一律 `Operation not permitted`（kTCCServiceSystemPolicyRemovableVolumes；`os.path.isdir` 能过、`open(...,'w')` 被拒 → 会误判成"盘已挂载所以正常"）。修法=系统设置→隐私与安全性→**完全磁盘访问权限**加入 `/usr/bin/python3`（bash 同理），否则备份脚本与产出收件口只能手动跑、无法无人值守。代码侧必须自己接住 PermissionError 并返回明确 `permission-denied`+hint，不能让异常冒泡——否则连接被直接断掉，上传端只看到空响应，查不出是权限还是掉盘。Why：这条决定备份/收件口能否自动化，不知情会归因到"盘坏"或"脚本 bug"。How：新增任何要写外置盘的服务，先做一次 launchd 写入探针再上生产。

- [2026-09-28 15:15:23] U275 图谱正典指针+R3 减密轮判例（2026-09-28·X1332/X1333·70938c1e7/21154b089 已推）： → 全文档案: .codely-cli/memory/mem-20260930-g-021.md

- [2026-11-04 14:37:00] [2026-11-04 14:36] macOS 可移除卷 TCC 权限定谳（外接盘"插了读不到"的真相·实测）：①现象=同一块 HFS+ 盘（/Volumes/移动硬盘，651 条资产），我在会话里读 0 缺失、后台脉冲读 651 缺失——差别只在 TCC，不是盘坏、不是 Unicode 路径问题。②修法=系统设置→隐私与安全性→完全磁盘访问，加**真正跑活的那个解释器** `/Users/junsheng.sun/.pyenv/versions/3.13.18/bin/python3`（launchd 的 pulse/watchdog 都指向它），授权后 vault/backup 两阶段立刻从红转绿；`/bin/bash` 仍被拒（Operation not permitted），当前无任务依赖它，可暂不管。③**验证方法（重要）**：从已授权的会话 shell 里测权限会继承 FDA，得到假阳性——必须用 `launchctl submit -l <id> -- <bin> -c "..."` 在真 launchd 上下文测，或直接看 PULSE 里 vault/backup 阶段的 rc。④另：Windows 读不了 HFS+，插到 Windows 机"不能读取"是格式问题，绝不能点格式化（会清空 651 条）；跨机读写只能 exFAT（需先备份）。⑤附带清理：Google Chrome 与 Keystone/GoogleUpdater 已删（弹窗"更新器损坏"根因），/Library/Google 属 root 残留需 sudo rm。
