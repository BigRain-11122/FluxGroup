# 机队网络锚点：bm-c（2026-11-27 决定稿）

- 依据：CEO 2026-11-27 令「你这台机器当网络锚点，其他都围绕你，但你的生产角色职责不变」
- 结论：**网络角色 = 锚点；生产角色不变（gpu-production 车道照常，本决定不新增算力任务）**
- 落地脚本：`Tools/fleet-anchor-bmc.ps1`（幂等、可逆、ASCII-only）
- 机队令：`quant/bigmoney/fleet/orders/O-20261127-1650-bm-c.md`

## 一、本机网络事实（2026-11-27 实测）

| 项 | 值 | 含义 |
|---|---|---|
| 出口 | 114.220.80.252 / CN / AS140292 电信江苏（南京） | 家宽，无公司专线 |
| NAT | `MappingVariesByDestIP=false`，`PortMapping=` 空 | 锥形 NAT，但路由器**不提供** UPnP/PMP/PCP |
| 公网 IPv6 | `240e:3a8:4cdd:62e0:5034:23eb:3213:6393`（SuffixOrigin=Link，稳定；其余 7 个是临时地址，小时级轮换） | 地址可用，但入站未知 |
| VPN 客户端 | 无（只有 Tailscale 隧道网卡） | 不存在 VPN 劫持，无需分流 |
| 本机 8790 | FleetLink v1.9.7，绑 tailnet IP + loopback | 命令面正常 |
| 出口 DERP | 最近 sfo/lax ≈143-157ms，hkg 215ms（异常高） | 电信到境外 DERP 路由差 |

## 二、锚点为什么现在还不生效（关键实测）

本机能起中继（`relay_port=41641` 已监听），但**入站被光猫/路由器挡住**，别人连不进来。

判据用「广告翻转法」（唯一可靠、无需外部工具）：

1. 广告本机稳定 IPv6 为锚点端点后，观测对端路径；
2. 对端从 direct 掉成 relay = 入站不通；对端保持 direct = 入站通。

实测（本日 16:5x）：

| 步骤 | bm-b 路径 | 判定 |
|---|---|---|
| 广告 `[240e:...:6393]:41641` | direct 11ms → **relay sfo 308ms** | 入站**不通** |
| 撤回广告 | **direct 11ms 立刻恢复** | 广告有害，已撤回 |

> 结论：**在路由器放行之前，禁止广告静态端点**（会把本来直连的对端打回中继，慢 27 倍）。
> 当前状态 = 只开中继监听、不广告：`static_endpoints=`（空）。

另注：bm-b 的直连是**按需建立**的——空闲时 `tailscale status` 显示 relay，一有流量（ping）立刻 `curAddr=124.77.140.89:41641` 11ms。所以判直连要带流量看，别只读空闲快照。

## 三、要成为真锚点，缺的是一步物理动作（三选一）

| 方案 | 操作 | 效果 | 备注 |
|---|---|---|---|
| A（推荐）IPv4 端口映射 | 光猫/路由器：UDP **41641 → 192.168.1.4** | 全队（含 bm-a）可直连 bm-c | 需要路由器管理密码；家宽公网 IPv4 真实可用 |
| B IPv6 入站放行 | 关闭光猫「IPv6 防火墙」或放行入站 UDP 41641 | IPv6 对端可直连（bm-a 需自身有 IPv6） | 电信光猫默认拦截入站 |
| C 保持现状 | 仅监听不广告 | bm-c 暂不做锚点，bm-b 继续当事实锚点 | 零动作，但 bm-a 继续吃 327ms 中继 |

做完后（A 或 B）**无需改任何配置**，只需一条命令刷新：

```powershell
& Tools\fleet-anchor-bmc.ps1 -Advertise
```

`-Status` 会给出裁决：`advertising + some peer direct -> inbound reachable`；若仍全 relay，脚本提示立刻 `-Unadvertise`。

## 四、IPv6 前缀会轮换（必须知道的维护点）

本机 8 个公网 IPv6 中只有 `SuffixOrigin=Link` 那一个是稳定的，其余是临时地址（小时级换）。且前缀 `240e:3a8:4cdd:62e0::/64` 的有效期约 2 天——**PPPoE 重拨会换前缀**。

脚本自动选 `SuffixOrigin=Link` 的地址，所以重拨后重跑 `-Advertise` 即可；不建议手工写死地址。

## 五、目标拓扑（CEO 令的落地形态）

```
bm-a ──┐
bm-b ──┼──► bm-c（锚点：直连优先 / 中继兜底）──► DERP(仅最后手段)
bm-d ──┘
```

路径优先级（全队一致）：
1. **direct**（任一方向可入站即成）
2. **经 bm-c 中继**（锚点已放行时）
3. **DERP sin/sfo**（327ms，仅兜底）

## 六、验收判据（机械可核）

| 判据 | 命令 | 通过值 |
|---|---|---|
| 锚点监听在 | `& Tools\fleet-anchor-bmc.ps1 -Status` | `relay_port=41641` |
| 入站可达 | 广告后 60s 再看 peers | 至少一个对端显示 `direct`（且不回落） |
| 反向可达 | 对端执行 `tailscale ping --until-direct -c 15 bm-c` | 末行 `direct connection established` |
| 退化检测 | 广告后若 peers 全 relay | 立刻 `-Unadvertise`（脚本会提示） |

## 七、风险与回滚

- 全部动作可逆：`-Unadvertise` 撤端点、`-Disable` 关中继（`tailscale set --relay-server-port ''`）。
- 不动 exit node / 路由 / MTU / 系统代理 / 凭据；不开 ShieldsUp；不做公网 445/3389 映射。
- 中继只对本 tailnet 成员有效（凭 tailnet 密钥认证），不构成公网开放服务。
- 生产面零影响：本脚本只改 Tailscale 偏好，不碰 ComfyUI/GPU/车道任务。
