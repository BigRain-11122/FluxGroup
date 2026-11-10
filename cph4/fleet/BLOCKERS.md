# 堵点台账 2026-11-05T15:25:18

共 9 条，其中 5 条可自动打通。

| 类型 | 堵点 | 打通方式 | 责任 | 自动 |
|---|---|---|---|---|
| B-CAP | OPEN 卡未派出：bm-c×1, bm-m×1 | 检查该机车道是否在跑；槽位不足则开槽或跨机回落 | S2 调度 | 是 |
| B-CAP | 满负荷缺口 1 处：槽位 2 只用了 1，还有 1 张可跑 | 补料/开槽/换机；主控只吃轻活 | S2 调度 | 是 |
| B-CAP | GPU 产能集中在单机（bm-c），该机排队即全线等待 | 夜窗开放 bm-a 的 4070S 备援；重活按云端兜底（有预算闸） | S2 调度 | 是 |
| B-GATE | 不变量红 7 项：I2×1,I3×9,I4×17,I6×1,I7×2,I12×19 | 已进 L2 决策，按项修到归零（修卡/修闸/改判据三选一） | S4 账房 | 是 |
| B-PHYS | bigdomain：商户号/支付资质未签（CEO 物理件） | 前置件先做（已配 1 项）+ 触发即解锁；其余线照跑 | CEO（物理件）/ S2（前置件） | 是 |
| B-PHYS | bigcompute：bm-d 未入网（需现场装机） | 前置件先做（已配 0 项）+ 触发即解锁；其余线照跑 | CEO（物理件）/ S2（前置件） | 否 |
| B-PHYS | biglife：居民 3D 接入未通（缺模型资产） | 前置件先做（已配 0 项）+ 触发即解锁；其余线照跑 | CEO（物理件）/ S2（前置件） | 否 |
| B-PHYS | recon：缺对标样片（需指定片子或授权下载） | 前置件先做（已配 0 项）+ 触发即解锁；其余线照跑 | CEO（物理件）/ S2（前置件） | 否 |
| B-PHYS | 节点不在线：bm-d | bm-d 需现场装机（物理件）；其余查心跳/调度任务 | CEO（bm-d）/ S7 自愈 | 否 |
| B-ENV | bm-b 的 git 仓库被卡住的 fetch 占锁（22:16 起 20+ 分钟），后续 reset/切片卡全部排队 | 人工在 bm-b 上删 `index.lock`/`shallow.lock` 并重启 FluxGroup-FleetLink + HQ-ProductionClaim；主控侧已改用"不 fetch 的轻量 reset"避免再触发 | CEO/现场（物理件）；S7 自愈（轻量卡） | 否 |
| B-ENV | bm-b 于 00:30 起 /status 完全探不到（此前是 git 锁，现在整机/服务不可达） | 现场检查 bm-b：电源/睡眠、Tailscale 在线、FluxGroup-FleetLink 任务；恢复后先清 git 锁再谈派卡 | CEO/现场 | 否 |
| B-INPUT | MV v716 成片缺失：卡面引用的 `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/full_mv_v716.mp4` 在 bm-a 与主控仓都不存在（仓内只有 test-reel）；Q-MV-0001-003 的 PASS 无法复验 | 到 bm-a 上确认真实成片路径（可能在 D: 或交付盘），把卡面 deliverable/命令改成真实路径；找不到就按“产物丢失”重渲 | S7 自愈（取证卡）；CEO（若需重渲授权） | 否 |
| B-ENV | bm-c lane 停摆：02:15 起 last_pull 戳冻结（15 分钟不动），COMFY-UP 卡无回执失败 | 重启 bm-c 的 HQ-ProductionClaim；再手动起 ComfyUI(127.0.0.1:8188) 并确认 RAM≥4G，之后 GPU 卡统一重派 | CEO/现场 | 否 |
| B-ENV | 三台 Windows 的 git 写入链路同时异常：bm-a 领先 32 且 reset 卡连失败、reset 不落 node 分支；bm-c 的 GPU 卡与 bm-a 的 reset 都"无回执"失败；bm-b 不可达 | 逐台现场：`git push --dry-run` 看是凭证还是网络；清 index.lock/shallow.lock；确认 SSH key/token 未过期。这是今晚停机的主因，主控无法远程代替 | CEO/现场 | 否 |
