# 机队 tailnet 策略与发令通道（2026-11-22/23）

## 一、tailnet 体检已落地（正身=Tools/fleet/tailnet_audit.py）
- 三判据：在线 / 直连 or 中继（给中继名+ms）/ 密钥剩余天数。rc=1 是告警不是故障。
- 阈值写死：密钥 <30 天 WARN、<7 天 CRIT；离线 >24h WARN、>7 天 CRIT。
- **必须分开的两个概念**：`OFFLINE-DOWN`＝真机停机（要去找人开机/查服务）vs `STALE-NODE`＝与在线节点**重名**的旧节点（可删）。首版把"离线 12 天的 bm-b"判成可删，属危险误判，已修。
- 已接主控脉阶段表 `("tailnet", [...], 120, {0,1}, True)`，证据落 `cph4/fleet/state/tailnet-audit.json`。
- 策略正身：`cph4/fleet/TAILNET-POLICY-v1.md`（五层：地址稳定/密钥不过期/标签+最小 ACL/连接质量/可观测）。

## 二、2026-11-22 实测快照（会变，看工具别抄数）
- 本机 100.75.133.10；传家宝 100.123.74.104 **直连 3–5ms**（同 LAN）；公司生产力机 100.110.185.62 **中继 DERP(sin) 392ms**；小钢炮 100.82.175.0 **离线 12 天**；旧 `bm-m 100.87.248.66` 离线 24 天（重名重复节点）。
- MagicDNS `tail316e0c.ts.net` 已开，短名 `bm-a/bm-b/bm-c` 可解析到 100.x（`dscacheutil -q host -a name` 验证）。
- 本机 UDP 通、`MappingVariesByDestIP=false`（NAT 友好）；`netcheck` 只报 sfo(168ms)，hkg/sin 探测未通。
- **CLI 1.104.7 ≠ 守护进程 1.104.5**（brew CLI 与 App 不同步，ping 会打 warning）→ 升一次 Tailscale.app。
- 待 CEO 在管理台点：①四台全 Disable key expiry（现 2027-03/04 集中到期＝同日全断且不自愈）②删旧节点 100.87.248.66 ③（可选）打 `tag:fleet` + 最小 ACL（片段在策略文件 L3）。
- 中继现实：公司生产力机的 NAT 做不了洞，**机队心跳超时须 ≥3×中继延迟（≥1.2s）**，否则把在线机判离线。

## 三、tailnet_audit.py 两个自身 bug（留作负控）
1. `tailscale status --json` 报文**结尾无换行**，把 stderr 拼进 stdout 就 `Extra data: line 273` 解析失败 → 取 JSON 只用 stdout（本工具已加 `run_json()`）。
2. 首版把真机停机判成"废弃节点可删" → 见上，改成 dup 检测才判 STALE-NODE。

## 四、给全机队发令的正规通道（2026-11-22 实锚）
- 工具：`Tools/fleet/fleet_order_bus.py --send "..."`（`--dry-run` 先看车道路由）。它做四件：拆车道→写 `cph4/fleet/cmd/<OB-id>.json`→追加 `docs/orders.md` 台账→push→NATS `fleet.cmd` 秒级通知→逐机 poke 并校验 `repo_heads["."]==sha`。
- **坑 1：poke 的 tasks 必须是白名单**（取 `Tools/fleet-nodes.json` 每台的 `wake_tasks`）。自己拼名字（如 `git-pull-and-apply-order`）节点回 `deny`，而 poke 本身仍回 `ok=True`＝假成功。
- **坑 2：NATS 发布写在 push 成功之后**，push 失败会静默跳过秒级通道 → 需手动 `fleet_hb.Nats("100.110.185.62",4222).publish("fleet.cmd", {...})` 补发。
- **坑 3：推送竞态**。本轮 `PUSH-FAIL non-fast-forward` 处理路径（实测有效）：`git stash` 运行时改动 → `git reset --hard origin/main` → `git cherry-pick <自己那条>` → 循环 `fetch/rebase/push`（5 次内必成，别的机在抢推）。判据只认 `origin/main..HEAD` 为 0。
- 令已落地但机器没执行时的排查顺序：`/status` 的 `origin_main`（拉到了吗）→ `repo_heads["."]`（工作树前进了吗）→ `fork`（这台的领先/落后）。实锚：公司生产力机 `origin_main` 已是含令 sha，但工作树 50 落后/808 领先，ff-only 进不去＝老分叉问题，不是令没发到。
