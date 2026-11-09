# 7x24 韧性方案（突发情况矩阵 + 闭环验收）

> 目标：不是"假设不出事"，而是"出事 5 分钟内被发现、能自愈的自愈、不能的上报"。
> 判据全部可机检：Tools/fleet/resilience.py 每天 09:07 跑一次，全绿才算过。
> 2026-11-09 首次验收：12 项 11 PASS / 1 WARN / 0 FAIL；演练 4/4 通过。

## 一、失败矩阵

| # | 突发 | 检测信号 | 自动处置 | 升级 | 验收 |
|---|---|---|---|---|---|
| 1 | 主控脉进程崩 | launchd KeepAlive | 立即重启 | 连续崩 3 次→日志 | services PASS |
| 2 | 脉假活（进程在、不推进） | PULSE.json 心跳 >900s | watchdog kill + kickstart | 同日 3 次→上报 | pulse_heartbeat |
| 3 | 状态同步停摆 | state-sync.ok_ts >1200s | statesync 每 60s 自跑；连败 3 次熔断 15 分钟；watchdog >15 分钟 kickstart | 熔断仍失败→日志 | state_sync |
| 4 | git 冲突/脏树 | git status UU / behind 暴涨 | 脉不碰 git；statesync 本地优先合并 + push 重试 | 连败熔断 | git_state |
| 5 | 队列损坏/重复 | 逐行 JSON 解析、DUP-ID | queue_integrity 每拍校验；resilience 每日深查 | 坏行→阻断派单 | queue_integrity |
| 6 | 供给干涸 | 每台可跑卡 < 3 | loadwatch 60s 跑 supply_batch + demand_gen | 仍不足→报缺口（不造假卡） | supply（WARN） |
| 7 | 执行机掉线/心跳陈旧 | comms hb_s >3600s | 不再派新卡；租约到期回收重派 | 连续离线→CEO 面 | lane_heartbeats |
| 8 | 卡被接了不干 | 租约到期（CPU 45 / GPU 180 分钟） | 自动回收重派，记 attempt | 3 次→FAILED + failed_triage | 队列状态 |
| 9 | 模型服务挂 | 11434/11436 /api/tags 超时 | 该阶段失败但不拖垮整拍；L2 熔断 300s | 连续失败→降级 L3 或告警 | model_endpoints |
| 10 | 云端凭据过期 | Codely oauth 文件 >30 天 | 只 WARN，不阻断本地 | 过期→CEO 重新登录 | codely_creds |
| 11 | 本地令牌缺失 | ~/.fluxgroup-llm-token 不存在 | llm_client 判"缺料"不发请求（不空打） | 补令牌 | llm_token |
| 12 | 磁盘将满 | 可用 <20GB | 现有 disk-sentinel 清理；resilience 每日判 | 连续告警→扩容 | disk |
| 13 | 内存/换页 | 可用 <8% | mem_gate 拒绝重活；模型装卸让位 | 持续→停车道 | memory |
| 14 | 机器睡眠 | pmset 断言 | caffeinate -s -i 常驻 | 合盖无效→人工 | services（caffeinate） |

## 二、分层责任

- **OS 层**：launchd（KeepAlive / StartInterval）+ caffeinate；断电/注销不可自愈，靠 RunAtLoad 恢复。
- **进程层**：watchdog 判"假活"；statesync 独立于脉。
- **数据层**：single-writer 派单、租约回收、队列去重、回执核销。
- **算力层**：L1 规则 → L2 本地（缺令牌不空打、失败熔断）→ L3 Codely（无上限，但需理由/分级/授权）。
- **验收层**：resilience 每日体检 + 演练；FAIL 进日志与 CEO 一屏。

## 三、演练（证明检测器不是摆设）

python3 Tools/fleet/resilience.py --drill

- 伪造"心跳 10000s 未更新" → 检测器必须 FAIL；
- 伪造"坏行 + 重复 id 队列" → 必须 FAIL；
- 伪造"服务不存在" → 必须 FAIL；
- 真实环境心跳 → 必须 PASS。

2026-11-09 实测 4/4 通过。

## 四、已知边界

1. 断电、注销登录、合盖休眠：launchd 用户域起不来，只能靠来电/登录后 RunAtLoad；
2. 远端仓库不可达：同步熔断，本机调度继续，跨机状态变旧；
3. 供给源头枯竭：守卫只能报缺口，不能造假卡；
4. git 里仍有状态（union 合并），仓库会继续长——根治要迁事件总线。
