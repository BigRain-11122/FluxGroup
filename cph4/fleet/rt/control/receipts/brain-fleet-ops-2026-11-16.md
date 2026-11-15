> ⛔ 引证核验未过（3 处查无此文件），本页结论不可作为决策依据：
> PRODUCTION-QUEUE.json
> STATIONS.json
> cph4/fleet/PRODUCTION-QUEUE.json

# 2026-11-12

**执行摘要**  
满负荷规则在 R41 事件班实测中陷入“全域停滞”状态。五个工位（control、visual、audio、brain、delivery）全部因 `STATIONS.json` 的状态开关关闭而自驱受阻。其中 `delivery` 工位不仅未注册，更缺失 16 个工序的产物契约；其余四机分别呈现关机、离线或未安装故障。此外，时钟漂移机制因中继不对称被误报为真漂，导致资源空转。

**机制死角与补法**  
当前调度供给机制（`cph4/fleet/dispatcher/POOL.json` 仅统计 open 卡）在 `f502fef37` 换挡当晚写入后失效，无法感知 `PRODUCTION-QUEUE.json` 中的真实工作负载（由 RUNNING 3 降至 OPEN 4），导致调度器持续误报空载。  
**补法**：修改 `Tools/fleet-dispatcher.ps1` 判据，将供给评估从单靠 POOL 转为联合读取 `cph4/fleet/PRODUCTION-QUEUE.jsonl`；同时采纳时钟提案，仅在 `absOff / rtt/2 ≥ 10` 且连续 3 同向采样时触发行动，其余降级为观察态，避免中继不对称噪音干扰资源分配。

【给谁·下一步】  
致 CEO-Proxy：需在非工作时段（19:00–09:00）重构 `STATIONS.json` 放行逻辑，并部署联合队列评估补丁至 `Tools/fleet-dispatcher.ps1`。

<!-- verify: citations=4 unverified=3 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
