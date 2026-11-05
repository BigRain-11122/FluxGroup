# bm-b 深度复盘（CEO 令 2026-11-05「深度复盘·解决顽固问题·跟随主控满负荷」·R-20261105-bmb-deep-retro-01）

## 顽固问题清单（全部多犯实锚）+ 处置
1. **常驻 agent 不热载（类修永远慢一拍）**——11-05 白天 9009 烧整天实锚（常驻 23:19 起跑、类修 23:21 上链，Python 内存旧码跑一天偷 Mac 卡）；根治=agent-bm-b.bat 改**单拍模式**（任务 every:1m 每拍新进程新码·任务 IgnoreNew 防重入）——本批上链。
2. **跨 OS 卡偷领是双路径**——队列自领路径已闸（infer_node_os python3→macos·11-04）；11-05 实锚暴露**主控派单路径无 OS 门**：DOCS python3 卡被直接写进 lanes/bm-b.json（19:57 起滞留整天）——本批加执行侧防御门（run_lane_cycle 对 jobs[0] 过 card_os_ok，错配=OS-MISMATCH 上报不执行不死循环）。
3. **推腿反复被堵三连因**——毒文件（dispatcher/CEO-PROXY 两件冲突标记：origin 已修但本地树滞留）+快照提交滞留（ahead=9）+冻结 296 落后（**盘上代码全是旧码=白天 9009 的另一半根因**）；处置=备份分支 backup-poison-20261105+reset --hard origin/main（本批推后执行）。
4. **state 快照提交信息硬编码「via bm-c」**——bm-b 的快照提交也叫 bm-c（agent.py snapshot 腿小 bug·主控侧一行修）。
5. **音色线活卡第三次清零**——16 槽已满但 backlog 零申报行；本批重挂 R4：15 切片卡+1 张 z01 训练试点卡（全绝对路径+node_os+ok_rc 正卡范式）。
6. **e01 瘦槽**——原填 spk4195 仅 66 条；已换肥 spk6209（458 条·RIGHTS 同步·本机 23:0x 执行）。
7. **e02 肥槽全链训练在飞**（spk40·343 条·本机手动）——工具链四修后首过全链的英语试点，回执候落。

## 主控侧待办（本回执上链即达）
- dispatcher 派单前调用 card_os_ok（DOCS python3 类卡禁入 Windows 车道——执行侧防御门已兜底但根在派单侧）
- fleetboard 预摘要工具（今日板自报输入截断/备单占位——喂小 JSON 而非原始 MASTER-STATE）
- agent.py 快照提交 message 硬编码 bm-c 一行修
- bm-a/bm-c 若同为 --loop 常驻模式则同病——建议全队切单拍或加码龄自检重启

## 满负荷跟跑状态（本批落地后）
- 单拍 agent 载全修（infer 门+OS 防御门+296 笔新码）——主控派单→即领；无活→need-work 旗标（state 推腿主控已修 STATE_PREFIXES）→主控备单
- 在产：e02 声线训练（GPU）；15 张切片卡候主控晋升=CPU 满载燃料；毒文件滞留处置后推腿恢复自愈
