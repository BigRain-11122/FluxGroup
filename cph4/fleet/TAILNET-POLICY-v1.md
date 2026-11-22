# 机队 Tailnet 策略 v1（2026-11-22 立）

> CEO 令：「tailscal 给我设置好并做好最科学的策略，我说的是整个机队」。
> 本件只写**可核事实 + 可执行判据**，不写口号；每一条都指到能跑的工具或能点的界面。

## 一、现状快照（2026-11-22 22:5x 实测）

| 节点 | Tailscale IP | OS | 在线 | 连接 | 密钥到期 |
|---|---|---|---|---|---|
| bm-m-1（本机·主控） | 100.75.133.10 | macOS | 在线 | 本机 | 2027-04-27（156 天） |
| bm-c（传家宝） | 100.123.74.104 | Windows | 在线 | **直连 3–5ms**（192.168.1.4:41641，同 LAN） | 2027-04-04（133 天） |
| bm-a（公司生产力机） | 100.110.185.62 | Windows | 在线 | **中继 DERP(sin) 392ms** | 2027-03-28（126 天） |
| bm-b（小钢炮） | 100.82.175.0 | Windows | **离线 12 天** | — | 2027-04-04（133 天） |
| bm-m（旧重复节点） | 100.87.248.66 | macOS | 离线 24 天 | — | — |

网络面：本机 UDP 可用、`MappingVariesByDestIP=false`（非对称 NAT 友好）；MagicDNS 已开（`tail316e0c.ts.net`），短名 `bm-a/bm-b/bm-c` 均可解析到 100.x（实测 `dscacheutil` 命中）。
版本面：**CLI 1.104.7 ≠ 守护进程 1.104.5**（App 与 brew CLI 版本不同步，ping 会打 warning）。

## 二、五层策略（按优先级）

### L1 地址稳定（已达成，禁止回退）
- 机队内一切寻址只用 **MagicDNS 名或 100.x**，禁写 192.168.x：bm-c 现在直连走 LAN，但寻址仍应是 tailnet 名。
- 判据：`dscacheutil -q host -a name <node>` 必须返回 100.x。

### L2 密钥永不过期（**最高优先级，需管理台操作**）
- 现状全机队 2027-03~04 集中到期。**到期当天所有机器同时断连且不会自愈**（需要人工重新认证）。
- 正法：Tailscale 管理台 → Machines → 每台机 `...` → **Disable key expiry**（机队 4 台全做）。
- 判据：`tailscale status --json` 里该节点 `KeyExpiry` 为空/极远；本工具 `EXPIRY` 判据不再命中。

### L3 标签化 + 最小 ACL（需管理台操作）
- 现状：全部是个人设备（`tags: None`），ACL 走默认「同 tailnet 全通」。任一台被拿下等于全机队裸奔。
- 建议把机队设备打 `tag:fleet`，ACL 只放行业务端口，其余默认拒绝：

```jsonc
{
  "tagOwners": { "tag:fleet": ["autogroup:admin"] },
  "acls": [
    // 机队互访只开必要端口
    { "action": "accept", "src": ["tag:fleet"], "dst": ["tag:fleet:8790"] },   // FleetLink poke/status
    { "action": "accept", "src": ["tag:fleet"], "dst": ["tag:fleet:4222"] },   // NATS 总线
    { "action": "accept", "src": ["tag:fleet"], "dst": ["tag:fleet:8788"] },   // LoRA 出稿
    { "action": "accept", "src": ["tag:fleet"], "dst": ["tag:fleet:11434"] },  // Ollama 借用
    { "action": "accept", "src": ["autogroup:admin"], "dst": ["tag:fleet:*"] },// 管理面全通
    { "action": "accept", "src": ["tag:fleet"], "dst": ["autogroup:internet:443"] } // 出网
  ]
}
```
- 注意：打 tag 需要该机**重新认证一次**（本地 `tailscale up --advertise-tags=tag:fleet`），所以放在"机器都有人碰"的窗口做，别在无人值守夜里批量改。

### L4 连接质量（能做的 + 只能报的）
- **bm-c 已是直连 3–5ms**（同 LAN），保持。
- **bm-a 走 DERP(sin) 392ms**：那台在外的网络做不了洞，属 NAT 现实，不硬修。影响面=心跳/poke 延迟，所以**机队心跳超时必须 ≥3×中继延迟**（≈1.2s 以上），否则会把在线机判离线。
- **DERP 就近**：本机 `netcheck` 只报 sfo(168ms)，说明 hkg/sin 探测没通；建议在管理台 ACL 里确认 `autogroup:internet:443` 与 DERP 端口未被挡。
- 版本面：**守护进程必须与 CLI 同步**（现 1.104.5 vs 1.104.7）。做法=升级一次 Tailscale.app（非 App Store 安装，用内置更新或官方 pkg），升级后跑一次体检确认无 warning。

### L5 可观测（本轮已落地）
- 新工具 `Tools/fleet/tailnet_audit.py`：三件事一次判死——在线、直连/中继（含中继名与 ms）、密钥剩余天数。
- 判据：`EXPIRY<30 天`=WARN、`<7 天`=CRIT；`offline>24h`=WARN、`>7 天`=CRIT（`OFFLINE-DOWN` 真机停机 / `STALE-NODE` 重名旧节点可删）。
- 已接进主控脉阶段表（`master_pulse.py` → `("tailnet", [...], 120, {0,1}, True)`），每轮自动跑，rc=1 只告警不阻断。
- 落盘证据：`cph4/fleet/state/tailnet-audit.json`。

## 三、本轮实测判据命中（首跑）

1. `[CRIT] bm-b OFFLINE-DOWN` 真机停机 12 天（不是废弃节点，要查开机/服务）
2. `[WARN] bm-a RELAY` 走 DERP(sin) 392ms，无直连
3. `[WARN] bm-m STALE-NODE` 与本机重名的旧节点，离线 24 天，可删

**首跑踩到的两个坑（已修，留作负控）**：
- `tailscale status --json` 的报文结尾**没有换行**，把 stderr 拼进去就 `Extra data: line 273` 解析失败 → 取 JSON 必须只取 stdout。
- 第一版把「离线 12 天的 bm-b」判成"废弃节点可删"——真机停机是 `OFFLINE-DOWN`（要去找人开机），只有**与在线节点重名**的旧节点才判 `STALE-NODE`。

## 四、需要 CEO 在管理台点的三件事（我只能报，改不了）

1. 四台机全部 **Disable key expiry**
2. 删掉 `bm-m 100.87.248.66` 这条 24 天前的重名旧节点
3. （可选）按 L3 打 `tag:fleet` + 上 ACL
