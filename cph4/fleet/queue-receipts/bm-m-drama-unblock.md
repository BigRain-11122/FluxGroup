# drama（漫剧）线解堵方案 · 依真实正典重写（2026-10-30）

> 前版（573B）含臆造命令（sysctl/reset_heartbeat/unblock_capacity 均非机队工具、bm-a 为 Windows 机不适用），已判不合格返工。
> 本版以 LINE-REGISTRY + MASTER-AGENT-v1 正典为准，只引用真实存在的处置手段。

## ① 真实堵因（正典原文引用）
- LINE-REGISTRY：`bigstream-drama` 状态 `BLOCKED`
- MASTER-AGENT-v1 判定定义：`BLOCKED = 有活但没有可用车道（如 bm-b 仓库分叉）`（首个实测即"漫剧·bm-b 仓库分叉"）
- drama 各工序 lane：drama-kf → bm-b / drama-voice → bm-b / drama-mix → bm-b（三道全依赖 bm-b）

**结论：堵因 = bm-b（小钢炮）工作树分叉，导致 drama 工序无可执行车道。**

## ② 可执行修复（均按正典既有机制，不新增命令）
1. **bm-b 本机收口工作树**（正典 UNIFIED-COMMAND-PLANE §五.2：`Tools/fleet-hot-sync.ps1` = fetch + rebase autostash，禁 hard reset）——让 bm-b 的 HEAD 追上 origin/main，解除分叉。
2. **bm-b 恢复认领链路**（正典§五.3：注册/确认 `HQ-ProductionClaim` 任务，每 5 分钟 `queue_claim.py --pool --node bm-b`）——确保声音/漫剧工序可被认领。
3. **用真实活源喂 drama 产线**：已注入声音机（bm-b）积压 `Q-AUD-0001/0002/0003`（EP002/003 带声合流+产能体检），bm-b 恢复在线后自领即产出，验证 drama 线复活。

## ③ 需人处理的部分（如实指定）
- bm-b 本机执行 hot-sync 与认领任务注册：需 bm-b 侧本机操作（或远程通道开通后由主控代执）。
- CEO/P. 明确：若 bm-b 分叉涉及本地未推送提交，需人工确认保留哪些（正典禁 hard reset 丢弃）。

## ④ 验收判据
- bm-b HEAD == origin/main（无 kept-local）
- Q-AUD-0001 在 bm-b 上被执行并回执 DONE
- MASTER-STATE 中 bigstream-drama verdict 由 BLOCKED 转 WAITING/WORKING
