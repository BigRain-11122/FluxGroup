# 复盘（经验与落点）2026-11-10T23:10:36

判据：**没有落点的不算已推广**。落点四类＝断言(rg) / 码里判据(symbol) / 正身件(doc) / 卡模板(card)。
已落点 19 条 · 待落点 7 条 · 声称有落点但核验不到 0 条（这一栏最严重）

## 待落点：复盘了但还没推广

| 经验 | 症状 | 建议落点 |
|---|---|---|
| L-D-contract | E-CONTRACT 类失败已重复 2 次（涉及 asset-lib×1、bigmone | 给这类失败定一个专属判据或拦在派单前 |
| L-C-不适用 | 撤销原因「不适用」重复 2 次 | 把这条撤销原因变成铺卡前的一次检查 |
| L-C-坏卡闭环 | 撤销原因「坏卡闭环」重复 19 次 | 把这条撤销原因变成铺卡前的一次检查 |
| L-C-同交付物重复在飞 | 撤销原因「同交付物重复在飞」重复 2 次 | 把这条撤销原因变成铺卡前的一次检查 |
| L-C-dupdeliverab | 撤销原因「DUP-DELIVERABLE」重复 3 次 | 把这条撤销原因变成铺卡前的一次检查 |
| L-D-artifact | E-ARTIFACT 类失败已重复 2 次（涉及 bigstream-duanju×1、 | 给这类失败定一个专属判据或拦在派单前 |
| L-C-坏卡闭环 | 撤销原因「坏卡闭环」重复 143 次 | 把这条撤销原因变成铺卡前的一次检查 |

## 已落点：下次会被机器拦住

| 经验 | 症状 | 落点 |
|---|---|---|
| L-20261107-01 | 节奏表里登记了 verify_done，主控脉里却从未接线，91 张 DONE  | rg `RG-11` |
| L-20261107-02 | 卡 claim 后 3 分钟必被杀，因为无心跳记录被算成静默 1e9 秒 | rg `RG-13` |
| L-20261107-03 | 同一张卡被四套阈值来回改状态：600s / 1h / 3 次 / 2 次各写一套 | rg `RG-14` |
| L-20261107-04 | 216 个脚本里 26 个写同一份队列，整文件覆盖会吞掉并发新增的卡 | rg `RG-15` |
| L-20261107-05 | 21 条质量判据里有 3 条连自己的反例都放行（恒 0 的偏差、空目录打不到上限 | rg `RG-16` |
| L-20261107-06 | 内存不足时把模型硬塞进统一内存，swap 涨到 4GB 还报「正常运行」 | rg `RG-17` |
| L-20261107-07 | 巡查把 PARKED 的线（短视频 129h、车机 122h）报成供给失败，责令 | rg `RG-18` |
| L-20261107-08 | fluxverse 派完一张 DONE 卡，线的产物年龄停在 103h 一动不动 | symbol `Tools/fleet/patrol.py:is_selfreport` |
| L-20261107-09 | 同一交付物连铺两天两张 OPEN（G18_PalacePlunder） | symbol `Tools/fleet/supply_batch.py:按交付物去重` |
| L-20261107-10 | 队列报 42 张活卡像供给充足，实际 39 张 nodes=["bm-m"] 钉 | doc `cph4/fleet/PATROL.md` |
| L-20261107-11 | 21 张失败卡没有 error_class，复盘时只能人逐张看 | symbol `Tools/fleet/flux_contracts.py:error_class` |
| L-20261107-12 | 卡里写 python3，在 Windows 上是商店假壳，rc=9009 且 e | symbol `Tools/fleet/failed_triage.py:classify` |
| L-20261107-13 | 同一交付物重试到第 4 次才被人发现「不是偶发」，前三轮都当成正常重派 | symbol `Tools/fleet/card_policy.py:max_attempts` |
| L-20261107-14 | blockers 永久亮 stage:metrics：ops_metrics 与 | rg `RG-20` |
| L-20261107-15 | brain_service 与 brain_brief 都叫 brain，sta | rg `RG-22` |
| L-20261107-16 | 看 PULSE 永远只看到这一轮跑了什么，某阶段三小时没跑在盘上查不到 | rg `RG-21` |
| L-20261107-17 | 移动硬盘没插时 vault 报「台账 651 条，盘上缺失 651 条」——像数 | symbol `Tools/fleet/vault.py:cmd_verify` |
| L-20261107-18 | needs=gpu-vision 合法外值且钉在没有 GPU 的 bm-m，卡挂 | symbol `Tools/fleet/card_contract_check.py:NODE-CAP-MISMATCH` |
| L-20261107-19 | 脉常年挂 swap 假红：只要 pageouts 比上一轮涨一点就判阻塞，而 m | symbol `Tools/fleet/master_pulse.py:swap_rate_limit` |

---
_复盘只提候选与核验；改阈值、写记忆都归各自的席，不在这里自动做_
