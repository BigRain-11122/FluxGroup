# 机队网络锚点：bm-c —— 最优可落地方案（2026-11-27 修订 v2）

- 依据：CEO 令「bm-c 当网络锚点，其他围绕你，生产角色不变」+「给我搞定最优版本」
- 生产角色：**不变**（gpu-production 车道、FleetLink 保活、ComfyUI 全部照旧）
- 本文替代 v1 的「IPv6 锚点」假设——v1 假设已被实测推翻

## 一、两条决定性实测（推翻原方案）

### 测试 1：广告 IPv6 端点
```
tailscale set --relay-server-port 41641 --relay-server-static-endpoints "[240e:...:6393]:41641"
→ bm-b 从 direct 11ms 掉到 relay sfo 308ms
tailscale set --relay-server-static-endpoints ""
→ 约 45-60s 后 bm-b 恢复 direct 11ms
```

### 测试 2：广告公网 IPv4 端点
```
tailscale set --relay-server-static-endpoints "114.220.80.252:41641"
→ bm-a 连续 15 次 ping 全部 timeout；bm-b 直连同时丢失
tailscale set --relay-server-static-endpoints ""
→ bm-b 恢复 direct 12ms，bm-a 恢复 relay sin 339ms
```

**定谳：bm-c 的入站（IPv4 与 IPv6 两个协议族）都被关闭。** 不是 Tailscale 配置问题，广告只会把本来直连的对端打回中继，所以当前策略 = **只监听、不广告**。

### 为什么 IPv6 路线对全队没意义

从控制面 netmap 读到的对端真实端点：

| 节点 | 广告端点 | 结论 |
|---|---|---|
| bm-a | `128.1.186.231:10065/41641/47945`、`10.86.98.91:41641` | 公网 IP 与 bm-m/bm-m-1 **同一个**（办公/共用 NAT），无 IPv6 |
| bm-b | `124.77.140.89:41641`（可用）、`[2001:0:14c9:...]:41641` | IPv4 真直连；IPv6 是 **Teredo 隧道**，非原生 |
| bm-m-1 / bm-m | `128.1.186.231:...` | 同上共用出口，无 IPv6 |
| bm-c | 8 个 `240e:...` + 公网 v4 | 有 IPv6，但**没人能用** |

**全队没有一个原生 IPv6 对端** → 即使光猫放行 IPv6 入站，也帮不到 bm-a（它没有 v6）。IPv6 锚点计划作废。

## 二、最优可落地拓扑（今天就能跑）

```
        控制/数据面（git 正典 + FleetLink 8790 + Taildrop）
bm-a ────────────────► bm-c（中枢：回执汇聚、命令下发、产物落链）
bm-b ────────────────►        ▲
bm-m-1 ──────────────►        │ 传输面（当直连失败时）
                              │
                    bm-b（唯一可入站节点，41641 已通，11-12ms）
                              │
                        DERP sin/sfo（最后兜底，327-339ms）
```

一句话：**bm-c 当「应用层锚点」（已有、且不依赖入站）；bm-b 当「传输层中继」（它天生可入站）。**
等 bm-c 拿到入站后，传输锚点一键切回 bm-c——脚本已备好。

## 三、要让 bm-c 成为真传输锚点，只有两条路

| 路线 | 操作 | 前提 | 生效方式 |
|---|---|---|---|
| **A 光猫 DMZ / 端口映射**（最快） | 登录光猫 → DMZ 主机填 `192.168.1.4`，或端口映射 `UDP 41641 → 192.168.1.4` | 光猫管理密码；WAN 口是**公网 IPv4** | 做完跑 `Tools\fleet-anchor-bmc.ps1 -Advertise`，60s 内自证 |
| **B 申请公网 IPv4** | 10000 号/掌上营业厅：家宽开「公网 IPv4」 | 若当前是运营商级 NAT（traceroute 第 2 跳 `100.84.110.1` 属 100.64/10 共享段，高度疑似） | 拿到公网 IP 后回到路线 A |

> 判定方法（一条命令）：光猫 WAN 状态页看 WAN IP；若是 `100.64.x` / `10.x` = 运营商级 NAT，端口映射无效，必须先走 B。

## 四、本机已就位的自动化（等条件满足自动武装）

```powershell
& Tools\fleet-anchor-bmc.ps1 -Status        # 现状：relay_port=41641, static_endpoints=(空)
& Tools\fleet-anchor-bmc.ps1 -Advertise     # 光猫放行后跑这条
& Tools\fleet-anchor-bmc.ps1 -Unadvertise   # 一发现对端掉 relay 立刻回滚
& Tools\fleet-anchor-bmc.ps1 -Disable       # 彻底关
```

`-Advertise` 自带裁决：`advertising + some peer direct -> inbound reachable`；若显示 `advertising but NO peer direct` 就是入站没开，脚本提示立刻撤回。

## 五、当前状态与验收

| 项 | 值 |
|---|---|
| bm-c relay 监听 | `relay_port=41641`（只监听，不广告） |
| bm-c 入站 | 关闭（IPv4/IPv6 双族实证不可达） |
| bm-b ↔ bm-c | direct 11-12ms（按需建立，空闲显示 relay 属正常） |
| bm-a ↔ bm-c | relay sin 327-339ms（bm-a 无入站；与 bm-m 共用公网出口） |
| FleetLink 8790 | bm-c up；bm-a 可达；bm-b/bm-m-1 侧 down |

托管目标（下一轮验收）：bm-a ↔ bm-c ≤ 80ms（经 bm-b peer relay），否则回 DERP。

## 六、风险与红线

- 全部改动可逆；不改 exit node / 路由 / MTU / 代理 / 凭据；不做公网 445/3389 映射；不开 ShieldsUp。
- 中继只服务本 tailnet（密钥认证），不是公网开放服务。
- 生产面零改动：脚本只写 Tailscale 偏好，不碰 ComfyUI / GPU / 车道任务。
