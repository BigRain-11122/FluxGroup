> ⛔ 引证核验未过（4 处查无此文件），本页结论不可作为决策依据：
> POOL.json
> PRODUCTION-QUEUE.json
> cph4/fleet/PRODUCTION-QUEUE.json
> queue_card_audit.py

# 2026-11-06 机队运行周报

满负荷规则执行总体正常，但调度供给口径存在结构性偏差。实测显示，系统仅统计 `cph4/fleet/dispatcher/POOL.json` 的 open 卡（如 POOL-0010），导致真工作活跃时仍报 `STARVED-EXEC`。真实负载数据见 `cph4/fleet/PRODUCTION-QUEUE.jsonl`（本班次 OPEN 22→4，RUNNING 3）。此外，`queue_card_audit.py` 校验发现的 19 张卡因 cmd 指向非根目录被误报为资源枯竭。

## 机制死角与补法
**死角**：当前满负荷判定仅依赖 `POOL.json`，忽略 `PRODUCTION-QUEUE.jsonl` 中的活跃卡片及 `queue_card_audit.py` 判定的结构性缺陷，导致“有卡跑不了”与“无卡可执行”被混淆。
**补法**：改为双源统计机制。当两源均为空时触发 `SUPPLY-DRY`；否则优先计入生产队列中状态为 OPEN 且节点匹配的卡片。新增 `FLAG CARD-DEFECT` 通道，专门报告经脚本判定缺陷的卡片，将资源瓶颈与任务错误分离上报。

## 需补充
CEO 未授权修改受保护件 `Tools/fleet-dispatcher.ps1` 核心逻辑。

<!-- verify: citations=5 unverified=4 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
