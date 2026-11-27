# T0 令 — 机队网络自愈立即执行（2026-11-27 17:45）

CEO 原话：「你传过去让他们执行，ceo最高级别命令」

- 级别：T0（最高）
- 执行面：bm-a / bm-b / bm-c / bm-m-1（bm-d 入网即执行）
- 授权：本令覆盖“不打扰 CEO”的常规约束；执行代理不得再向人确认，不得空停。

## 每台必须做的四步（按序，不得跳）

1. **自识别**：读 `Tools/fleet-nodes.json` 匹配 `COMPUTERNAME` 得到 id；读 `tailscale status --json` 的 `Self.HostName` / `Self.DNSName` / `MagicDNSSuffix` / `Self.TailscaleIPs`。
2. **执行提示词**：完整执行 `cph4/fleet/AGENT-NET-UNIVERSAL-PROMPT.md`（自识别 → 取证 → 决策树 → 回执）。
3. **管理员项**（仅 Windows）：以管理员执行 `Tools/fleet-fix-admin.ps1` —— 启动 w32time（Automatic + resync）、把 `FluxGroup-FleetLink` 改为 S4U、读回 logontype 与 `/health`。
4. **回执**：写 `cph4/fleet/receipts/net-<id>-20261127.md`，只加该文件提交并推 main（禁 force；分叉则 staged 并说明）；Taildrop 兜底发 bm-a。

## 各机已知起点（bm-a 2026-11-27 实测，执行席以此为基线）

- **bm-a**：命名合规（`bm-a.tail316e0c.ts.net`）；8790 up v1.9.7；task `LogonType=Interactive`；w32time Stopped；CGNAT，不可做锚点。
- **bm-c**：8790 up v1.9.7；最后拉取 `2026-11-27T17:37:41`（`.:updated`）；从 bm-a 看仍 `relay sfo`，需本机查 VPN/TUN。
- **bm-b**：8790 down（仅 Taildrop 可用）；已投 6 文件包（rc=0）；先 `tailscale file get`。
- **bm-m-1**：直连（192.168.160.100，18ms，实测 2268KB/s）；已投提示词；确认命名 `bm-m-1` 与常开。
- **bm-d**：入网后按同一提示词执行。

## 红线（T0 也不得违）

不改 exit node / 路由 / MTU / 凭据 / 系统代理；不把 445/3389 映射到公网；不重命名或删除他人设备；不 `git add -A`；不 force push；不静默改 VPN 全局设置。

## 验收（全部满足才算执行完成）

1. `Self.DNSName == <id>.<MagicDNSSuffix>`；`fleet-drop -To bm-a` 不报歧义。
2. 应跑 8790 的节点 `/health` 200；不跑的写明 `TaildropOnly=true`。
3. 管理员脚本在每台 Windows 上 `RESULT=PASS`（或写清阻塞与一条建议）。
4. 回执已落盘并推 main（或 staged + 说明）。
5. 没有触发任何红线动作。

SLA：立即执行；回执 2 小时内。执行不了的，回执必须写“阻塞项 + 一条可执行建议”，不得空停。
