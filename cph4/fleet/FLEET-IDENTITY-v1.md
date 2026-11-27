# 机队编号与判据正典 v1（2026-11-27 · 主控 bm-m-1 定）

> 机器面=`cph4/fleet/FLEET-IDENTITY-v1.json`（唯一来源，工具只读）。本文件是人读版。
> 为什么要有它：2026-11-27 一天里三台机器各自改名、各自写 doctor、各自发回执，同一个节点在尾网/心跳/花名册/判活屏上叫三个名字。CEO 令「做好机器编号和判断，然后统一弄好」。

## 一、编号（一号一名，网络层为准）

| 规范 id | 机器 | 主机名 | tailnet IP | DNSName | 状态 |
|---|---|---|---|---|---|
| bm-a | 公司生产力机 | DASHENG | 100.110.185.62 | bm-a.tail316e0c.ts.net | 在线 |
| bm-b | 小钢炮 | BIGMONEY | 100.82.175.0 | bm-b.tail316e0c.ts.net | 按 CEO 令暂停（11-14，未开机） |
| bm-c | 传家宝 | FLUXGROUP | 100.123.74.104 | bm-c.tail316e0c.ts.net | 在线（经 DERP-sfo） |
| **bm-m-1** | MacBook 主控 | junshengsundemacbook-pro.local | 100.75.133.10 | bm-m-1.tail316e0c.ts.net | 在线（主控面按令停用，养号线在跑） |
| bm-d | 算力大脑 | 未入网 | — | — | 未安装 |

旧名处置：`bm-m`（100.87.248.66，离线 29 天的旧登录残留）**只作为入站别名**，不再由任何机器写出；该设备待管理员在 tailnet 后台删除，删除前禁止用短名 `bm-m` 寻址。

## 二、六条规则

1. **R1 一号一名**：规范 id == Tailscale 设备名。台式用 `bm-<字母>`；主控/移动机名字被占时用 `bm-<字母>-<n>`。
2. **R2 重名只改本机**：不动别人的设备；本机让位后代号同步改，不留两层名。
3. **R3 寻址只用 DNSName 或 IP**；短名不作唯一键，脚本遇歧义必须报错不许猜。
4. **R4 写出端只写规范 id**；读取端过渡期接受 aliases（`bm-m-1` 的别名=`bm-m`）。
5. **R5 改编号必须一次提交同时改**：本正典 + `Tools/fleet-nodes.json` + 写出端（心跳/回执），主控签署。禁止单机只改自己那一半。
6. **R6 push 前自检**：`git ls-files` 文件数须与 `origin/main` 树同量级（差 >5% 停手）；删除 >200 文件或 >5% 必须显式声明（11-27 主干被削空就是这么来的）。
7. **R7 网络锚点固定 bm-c，不是主控**：主控是笔记本，会换网络、对称 NAT、无端口映射、无全局 IPv6，永久只做客户机；禁止把主控设为锚点/中继/跨机收件中心。锚点细节读 `cph4/fleet/anchor/ANCHOR-BMC-20261127.md`，本正典只做指针。

## 二之补、网络角色（CEO 2026-11-27 令：以传家宝网络为锚点）

| 节点 | 网络角色 | 依据（实测） |
|---|---|---|
| **bm-c 传家宝** | **锚点（listen-only）** | 锥形 NAT（MappingVariesByDestIP=false）、出口 114.220.80.252/CN 电信江苏、稳定 IPv6 `240e:…:6393` 但入站被光猫拦、relay 41641 已监听、8790 在听 |
| bm-a | 客户机（同网段可直连锚点） | — |
| bm-m-1 主控 | **client-only** | 对称 NAT、portmap 空、无全局 IPv6、笔记本换网漂移 → 永不锚点 |
| bm-b | 客户机（按 CEO 令暂停） | — |

锚点还差一步物理动作（CEO/物理侧三选一）：光猫 `UDP 41641 → 192.168.1.4`／放行 IPv6 入站／换可入站线路。在放行前**不要广告静态端点**——实测广告会把本来直连的对端打回 relay(sfo)，慢 27 倍。判直连必须带流量看（空闲显示 relay，ping 一下立刻 direct）。

## 三、判据（谁判、按什么判）

- **身份**：本正典 + 花名册；身份冲突（文件说 A、hostname 说 B）→ 拒绝运行（IdentityConflict），不许挑一个继续。
- **存活**：三腿合看——NATS 落盘 `cph4/fleet/state/node-state/<id>.json`、git 回执 `queue-receipts/_last_lane_<id>.json`、tailnet 在线态；阈值 1h/6h/24h；**只认机器自己写的时间戳**，不认本地 mtime；`paused_by_ceo` 不算故障；查不到尾网状态记 unknown，**不许记成离线**。
- **锚点**：锚点固定 bm-c（见上表与 `cph4/fleet/anchor/ANCHOR-BMC-20261127.md`）。判定某机能否当锚点：端口映射非空 / 全局 IPv6 可入站 / 公网 UDP 41641 已转发，三者有其一；对称 NAT 且都没有=client-only，不开 relay-server-port、不广告端点。
- **大件交接**：走 bm-c 的 HTTP 收件口；Taildrop 只作小件与回执。主控不做收件中心（会漂移）。
- **互传**：`tailscale file cp` 返回 0 只代表**本端已交给 tailscaled**；"对端已收"必须由对端回执证明。
- **8790 FleetLink**：Windows 才有；macOS 判 Taildrop-only，不起 8790。

## 四、工具归属（不许再各写一套）

| 事 | 归谁 |
|---|---|
| 编号与判据正典 | 仅 bm-m-1 可改 |
| Windows 网络体检 | `Tools/fleet-net-doctor.ps1`（bm-a 维护） |
| Windows 互传 | `Tools/fleet-drop.ps1`（bm-a 维护） |
| macOS 网络体检/判活 | tailscale CLI + `Tools/fleet/fleet_liveness.py`（读本正典） |

新增检查项：加进本正典的 judgments/checks，不新开兄弟脚本。

## 五、变更记录

- 2026-11-27：立 v1。设备名 `bm-m`→`bm-m-1` 定案为规范 id，`bm-m` 降别名；身份/存活/锚点/互传/8790 五类判据收成单一来源；登记待删旧设备 100.87.248.66；补 R6 push 自检（同日主干被 867558ab16 削空事故）。
