# 机队网络审计与互传优化 — 2026-11-27

作者：bm-a 交互会话　范围：本机 Tailscale + 机队互传通道　证据：本文所有数字均为 2026-11-27 15:0x–15:5x 本机实测。

## 0. 一句话结论

bm-a 位于**运营商级 NAT（CGNAT）之后、公网出口在新加坡**；bm-b/bm-c 的 Tailscale 中继固定在**美西 sfo**。三者之间**没有一条直连**，所有报文绕 `bm-a(SG) → sfo(US) → 对端`。实测单流 **8–12 KB/s**、4 路并行 **19.4 KB/s**。本机侧能做的已落地（免登录常驻、Taildrop 通道、压缩/分片/校验工具）；要真正"网络畅通"，必须在对端和网络侧动 §5 的三件事。

## 1. 实测证据

| 项 | 实测值 |
|---|---|
| Tailscale | 1.104.5，服务 Running/Automatic，节点 bm-a `100.110.185.62` |
| MagicDNS | `tail316e0c.ts.net`，`bm-b`/`bm-c` 名称解析正常 |
| 中继 | bm-b、bm-c 均 `relay "sfo"`；`tailscale ping` RTT **376–398ms**，偶发 1.31s |
| 直连 | 两对端 `tailscale ping` 均返回 `direct connection not established` |
| netcheck | UDP true；IPv4 出口 `128.1.186.231`（Singapore / AS21859 Zenlayer）；**无公网 IPv6（仅 ULA）**；`MappingVariesByDestIP=true`（对称 NAT）；`PortMapping: PCP/PMP/UPnP 全 false` |
| 路径 | `10.86.96.1 → 58.33.9.198 → 100.64.35.225 → 100.64.17.198`（`100.64/10` = CGNAT） |
| 网关 | MAC `00-1B-17-00-32-30`（Palo Alto Networks），HTTP 管理页超时 |
| 吞吐 | 100KB 11.8s（8.5KB/s）；1MB 86.5s（11.8KB/s）；5MB 306.8s（16.3KB/s） |
| 并行 | 4×1MB 总墙钟 211.7s（**19.4KB/s**，单流 109–212s）→ 约 1.65× |
| 对照 | **bm-m-1 是直连**（192.168.160.100）→ 直连能力本身没坏，问题只在 bm-b/bm-c 两台的网络 |
| 本机防火墙 | `Tailscale-Process` 入站 UDP 全配置放行；`Tailscale-In` Domain/Private；Tailscale 网卡为 Private；无管理员权限 |
| FleetLink | 本机 `100.110.185.62:8790` 监听正常、pusher 心跳正常；**对端 8790 关闭**；`last-pull-bm-b/bm-c` 停在 11-05；pusher 日志持续 TCP 连接失败 |
| 对端端口 | bm-b/bm-c 的 **445 开放**；bm-c **3389 开放**；22/5985/5986 关闭 |

## 2. 根因（按层级）

1. **物理层（本机侧，不可改）**：CGNAT + 对称 NAT + 无 UPnP/PMP/PCP + 无公网 IPv6 ⇒ 端口映射与 UDP 打洞都不可能。不是防火墙问题，也不是 Tailscale 配置问题。
2. **中继选择（对端侧）**：中继固定 sfo。在 bm-a 上执行 `tailscale debug force-prefer-derp 3`（sin）**实测无效，relay 仍为 sfo** ⇒ 中继区域由**对端的 home DERP** 决定。bm-b/bm-c 出口在美国是强信号（VPN/TUN 全局接管）。
3. **结果**：DERP 是 TCP 中继，跨太平洋两次 + 拥塞/丢包 ⇒ 8–20KB/s。这是 FleetLink 长期 `timeout / oversize / reject` 的物理根源，不是代码 bug。

## 3. 本机已做的改动（全部可逆）

- `tailscale set --unattended=true`（rc=0，免登录常驻）。
- 新增 `Tools/fleet-drop.ps1`：Taildrop 封装；文本自动 gzip；>4MB 自动分片并行；清单 + SHA256 校验；接收端 `-Pick` 重组并清理临时件。
- 未改：exit node / accept-routes / MTU（保持 1280）/ 防火墙（无需改）/ 系统级服务（无管理员权限，也未越权）。
- 验证记录：
  - `-SelfTest`：分片/重组 + gzip 往返 **PASS**
  - staged 端到端：9.4MB → 3 片 → 清单 → 校验 → 重组，SHA256 一致 **PASS**
  - 真实单发：`orders.md` 342,369B → gzip 163,871B，**7.3s / 21.8KB/s**（2.1× 压缩）
  - 真实并行：4×1MB = **19.4KB/s**（1.65× 单流）
  - 真实分片并行：1.5MB / 2 片，**71.3s / 21.5KB/s**（1.8× 单流，走完整清单+分片链路）

## 4. 用法

```powershell
# 发送（自动压缩；>ChunkMB 自动分片并行；默认 4 片并发）
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-drop.ps1 -Send D:\path\big.zip -To bm-b

# 接收（在对端执行；自动校验+重组，默认落到 <repo>\fleet-inbox）
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-drop.ps1 -Pick

# 看链路（谁直连、谁中继）
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-drop.ps1 -Status

# 逐机体检（每台机器跑一次，只读；输出该机"能不能做直连锚点/该改什么"）
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-net-doctor.ps1
```

参数：`-ChunkMB`（默认 4）、`-Parallel`（默认 4）、`-NoSplit`、`-Compress`、`-Force`、`-Inbox`、`-Out`、`-StageDir`（只落盘不发送，测试用）。

## 5. 要真正畅通，必须在别处做（按收益排序）

**A. 对端（bm-b/bm-c）查 VPN/TUN 是否劫持 Tailscale**——home DERP 在 sfo 是强证据。
在对端执行：

```powershell
$ts="C:\Program Files\Tailscale\tailscale.exe"
& $ts netcheck                      # 看 sin / sfo 延迟
& $ts debug force-prefer-derp 3     # 临时切 sin（重启失效）
& $ts ping -c 3 100.110.185.62      # 看是否变 DERP(sin) 且 RTT 下降
```

若 relay 变 sin 且 RTT 明显下降 ⇒ 在该机 VPN 客户端里把 `tailscaled.exe` **排除 TUN**（Clash/V2Ray 类都有进程分流），或取消全局接管。这是**收益最大的一步**：380ms/8KB/s 的根源是对端出口在美国。

**B. 对端 FleetLink 监听已死**（8790 关闭，11-05 起无拉取）。在对端执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-link.ps1
Get-ScheduledTask FluxGroup-FleetLink | Select-Object TaskName,State
```

**C. 公网中继（备选）**：若 A 后仍无直连，可让一台**公网可达**的机器做 peer relay（`tailscale set --relay-server-port 41641`）。本机 CGNAT 做不到，必须另找节点/VPS。

## 6. 验收判据（下次复查直接用）

- `fleet-drop -Status`：bm-b/bm-c 显示 `direct` 而不是 `relay sfo`
- `tailscale ping`：RTT < 100ms 且无 `direct connection not established`
- 1MB Taildrop：直连下 > 1MB/s；退一步 relay sin 下 > 100KB/s
- 对端 8790 可连，pusher 日志出现 `sync-push ... applied=`

## 7. 副作用与清理

本次验证向 **bm-b 的 Taildrop 收件箱**投了约 12MB 测试文件（`ts-drop-test.txt`、`ts-speed-5mb.bin`、`k100.bin`、`m1.bin`、`p1..p4.bin`、`orders.md.gz`、`fd-net-1p5mb` 分片+清单）。在 bm-b 上清理：

```powershell
& "C:\Program Files\Tailscale\tailscale.exe" file get --conflict=overwrite C:\Temp\fleet-inbox-clean
Remove-Item C:\Temp\fleet-inbox-clean -Recurse -Force
```

## 8. 2026-11-27 追加：国内路径实测与"苏州锚点"方案

从 bm-a 实测到江苏电信 DNS（`61.177.7.1`）**7–10ms**，路径 `10.86.96.1 → 58.33.9.198（上海电信）→ 58.33.9.193 → 222.72.238.114`，**全程国内，没有绕新加坡**；到 AliDNS `223.5.5.5` 4–5ms。

**结论修正**：`128.1.186.231`（新加坡 Zenlayer）只是**国际出口**，国内流量是直连的。因此 380ms / 8KB/s **不是物理距离**造成，而是**对端 home DERP 在 sfo**（VPN/TUN 全局接管）把机队流量拉去了美西中继。只要把对端的 TUN 劫持摘掉，国内直连/中继应回到 10–50ms 量级。

**一台苏州电信千兆家庭宽带的机器 = 最佳锚点候选**，按该机 `fleet-net-doctor` / `netcheck` 结果判：

| 判据 | 好 | 坏 |
|---|---|---|
| `MappingVariesByDestIP` | false（锥形 NAT，可打洞） | true（对称 NAT，需端口映射） |
| `PortMapping` | UPnP / PMP / PCP 任一 | 空 |
| `IPv6` | yes（`240e:` 开头） | no |
| 出口 | CN / China Telecom | US / SG（说明 TUN 接管） |
| 上行带宽 | 30–100Mbps（以实测为准） | <10Mbps |

处置：
- 有 UPnP/PMP，或公网 IPv4 + 端口转发 ⇒ 直连自动成立；再开 `tailscale set --relay-server-port 41641` 让它成为 peer relay，bm-a↔bm-c 也能绕开 sfo。
- 只有 IPv6 ⇒ 对 bm-a 无效（bm-a 只有 ULA，无公网 IPv6）；对 bm-c 可能有效。
- 是 CGNAT（WAN 为 `100.64/10` 或 `10.x`）⇒ 打 10000 申请公网 IPv4，或路由器开 IPv6。
- 先关 VPN/TUN 或把 `tailscaled.exe` 排除，否则 home DERP 仍是 sfo。

角色建议：常开 + 路由器 DHCP 保留 + UPS；**不要开 exit node**（会把全部流量压到家庭上行）；不要对公网映射 445/3389，只走 Tailscale。

验收：`fleet-drop -Status` 显示该机 `direct`；`tailscale ping` RTT < 30ms；1MB Taildrop > 1MB/s（以家宽上行为准）。

## 9. 命名法（2026-11-27 立，全机队硬规则）

- 规范 id：主机 `bm-a/bm-b/bm-c/bm-d`；移动/临时 `bm-m-1..n`。**唯一、永不复用**。
- Tailscale hostname == 规范 id；MagicDNS FQDN == `<id>.<MagicDNSSuffix>`（当前 `tail316e0c.ts.net`）。
- 唯一寻址只用 **DNSName 或 IP**。短名可能重名：当前两台设备都报 `HostName=bm-m`（100.75.133.10 在线 / 100.87.248.66 离线 28 天），MagicDNS 分别给 `bm-m-1` / `bm-m`。
- 工具行为：`fleet-drop -To` 对歧义短名**直接报错并列出候选**；`-Status` 打印 `WARN duplicate hostname`；`fleet-net-doctor` 全用 DNSName 显示。
- 改名（本机执行）：`tailscale set --hostname <id>`；离线旧设备在 admin console 改名 `bm-m-old` 或删除（只能由人操作，脚本不碰别人的设备）。
- 花名册：`Tools/fleet-nodes.json` 是唯一花名册（含 `_naming`）；新机先登记但 `enabled=false`，确认 8790 能力后再开。
- 通用自愈提示词：`cph4/fleet/AGENT-NET-UNIVERSAL-PROMPT.md`（任何一台机器粘贴即跑，自识别、自修复、写回执）。
