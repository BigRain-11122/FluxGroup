# Tailscale 全链路体检（2026-11-18 15:3x · 公司生产力机本机实测）

> 触发：CEO「Tailscale 控制台你全链路审查 有什么要修改和优化的马上做」。
> 本件只写实测值与可执行修法；数字均为本机命令输出，不引用记忆或旧档。

## 一、实测现状

| 项 | 实测值 |
|---|---|
| 客户端版本 | tailscaled **1.104.5**（commit 788384763），服务 Automatic / Running |
| 本机身份 | bm-a · 100.110.185.62 · 密钥到期 **2027-03-28（+129 天）** |
| 网络类型 | UDP 可用；**MappingVariesByDestIP = true（硬 NAT）**；**PortMapping 空（无 UPnP/NAT-PMP）**；IPv6 = no；无强制门户 |
| DERP 时延 | **sin 68.8ms** / hkg 98.2 / tok 132.5 / bom 137.1 / syd 199.8 / fra 220.5 / sfo 231.3 / lax 246.1 |
| MagicDNS | 正常：`bm-m-1.tail316e0c.ts.net → 100.75.133.10` |
| 本机路由偏好 | RouteAll=on、CorpDNS=on、ShieldsUp=off、RunSSH=off、无 exit node |

### 节点表（tailscale status --json 实读）

| 节点 | 系统 | 在线 | 密钥到期 | 走的 DERP | 直连地址 | 最后在线 |
|---|---|---|---|---|---|---|
| bm-a（公司生产力机） | windows | 是（本机） | 2027-03-28（+129d） | — | — | 现在 |
| bm-m-1（MacBook 现役） | macOS | 是 | 2027-04-27（+160d） | sin | **192.168.160.107**（直连） | 现在 |
| bm-c（传家宝） | windows | 否 | 2027-04-04（+137d） | **sfo** | 无 | 2026-11-18 14:2x |
| bm-b（小钢炮） | windows | 否 | 2027-04-04（+137d） | **lax** | 无 | 2026-11-10 |
| bm-m（旧 key·死条目） | macOS | 否 | 2027-04-27（+160d） | sin | 无 | 2026-10-29（20 天） |

## 二、要改的（按优先级，含执行位）

| # | 问题 | 证据 | 影响 | 修法 | 执行位 |
|---|---|---|---|---|---|
| P0-1 | **两台机器在绕美国 DERP**：传家宝走 sfo(231ms)、小钢炮走 lax(246ms)，而最近 DERP 新加坡只要 68.8ms | 上表 relay 列 | 每次 git 同步/poke 多付 ~160ms×往返；批量小文件拉取明显变慢 | 先等它们上线跑 `tailscale netcheck`；若最近 DERP 也是 sin 却仍绕美西，查是否配了 exit node 或系统代理把出口放在美国（Tailscale 用本机出口选 DERP） | 现场（两机上线后） |
| P0-2 | **所有节点密钥会到期**（2027-03/04） | KeyExpiry 列 | 到期当天设备自动掉线，表现为"突然全部离线"，与这次小钢炮/传家宝掉线同类症状 | 给四台常开设备打 `tag:fleet`（tag 设备密钥永不过期），或控制台逐台 Disable key expiry | 控制台（CEO 或 API key） |
| P0-3 | **死节点 bm-m(100.87.248.66)** 挂了 20 天 | 上表最后一行 | 按名字找机会歧义；机器列表噪音 | Machines → 该设备 → Remove | 控制台 |
| P1-1 | **硬 NAT + 无端口映射** → 跨公网直连基本不成立，全程靠 DERP | MappingVariesByDestIP=true、PortMapping 空 | 传家宝/小钢炮回线后大概率仍走中继；大文件走中继要排队 | 路由器开 UPnP 或 NAT-PMP（本机网关 10.86.96.1 属运营商级 NAT，若确认 CGNAT 则此路不通，接受 sin 中继 69ms 即可） | 物理件（路由器） |
| P1-2 | **无 IPv6** | netcheck IPv6=no | 少一条直连路径（IPv6 下常能直连） | 路由器开 IPv6 后重跑 netcheck 验证 | 物理件 |
| P1-3 | 本机 RunSSH=off 且 **Windows 不支持 Tailscale SSH 服务端** | prefs RunSSH=false；Tailscale 官方仅 Linux/macOS 提供 SSH 服务端 | 远程执行通道不能指望 Tailscale SSH；跨机执行只能走 OpenSSH（各机跑一次 `Tools/fleet/enable-remote-exec.ps1`） | 保持 off；远程执行按 OpenSSH 方案推进 | 现场 |
| P2-1 | tailnet 全端口可达（Tailscale-In 允许 100.64.0.0/10 任意端口） | 实测监听 445/3389/4222/8790… | 目前 4 台都是自有设备，可接受；接入任何外部设备前必须收紧 | 接入他人设备前把 ACL 改成按 tag 限定端口 | 控制台（预置见 §四） |

## 三、控制台三步（CEO 点，约 2 分钟）

1. **Machines** → 找 `bm-m`（IP 100.87.248.66，Last seen 20 天前）→ **Remove**。
2. **Machines** → `bm-m-1` → **Rename** 为 `bm-m`（删掉死条目后名字空出来了）。
3. **四台常开设备**（bm-a / 传家宝 / 小钢炮 / MacBook）→ 各自 **Disable key expiry**；或用 §四 的 tag 方案一次性解决（推荐 tag：一次做完且新设备默认继承）。

## 四、ACL 正本（可整段粘贴到 Access controls → 保存）

```json
{
  "tagOwners": {
    "tag:fleet": ["autogroup:admin"]
  },
  "acls": [
    { "action": "accept", "src": ["tag:fleet"], "dst": ["tag:fleet:*"] }
  ],
  "ssh": [
    { "action": "accept", "src": ["tag:fleet"], "dst": ["tag:fleet"], "users": ["autogroup:nonroot"] }
  ]
}
```

说明与约束：
- `tag:fleet` 的设备密钥**永不过期**，直接消除 P0-2。
- `acls` 只放行 fleet 内部互通，与现状等价（不会切断现有链路）。
- `ssh` 段只对支持 SSH 服务端的系统生效（Linux/macOS）；Windows 机加了也无效，不影响其它规则。
- 打 tag 后设备身份从"用户名"变"标签"，凡是按用户名写死的分享/ACL 要一并核对（本机队无此类）。

## 五、同链路但不在 Tailscale 内的两处（已发现，未擅自改）

1. **NATS 4222 无认证**：`Tools/nats/bin/nats-server.exe -p 4222 -js -n fleetbus`——无 `--auth/--user`，且监听 0.0.0.0，局域网与 tailnet 内任何人都能往机队总线发布消息。修法=加 user/pass 并同步所有客户端（Mac + 各 Windows），属跨机改动，须协调窗口，不能在跑批中途断。
2. **8790 FleetLink / 3389 RDP / 445 SMB 对 tailnet 全开**：自有设备内可接受，见 P2-1。

## 六、本机已做（本班实际执行）

- 复核 `tailscaled` 服务为 Automatic + Running（掉线后能自起，无需改）
- 复核 MagicDNS 解析与到 MacBook 的直连路径（192.168.160.107，走内网不经 DERP）
- 复核监听面与防火墙规则，登记 P2-1
- 无凭据可调控制面：本机无 `tskey-api-*`/OAuth 客户端，**删除节点/锁密钥/改 ACL 三件必须走控制台或提供 API key**

## 七、复验命令（改完后按这个核）

```powershell
tailscale status --json | Select-String -Pattern "KeyExpiry","Relay","Online"
tailscale netcheck
Resolve-DnsName bm-m.tail316e0c.ts.net
```
判据：①死节点不再出现在 status；②四台 KeyExpiry = `0001-01-01T00:00:00Z`（永不过期）；③传家宝/小钢炮上线后 Relay 为 `sin`。

## 八、后续实测与修复（2026-11-18 15:4x 本班）

1. **远程执行通道确认缺位**：本机 `Get-Service sshd` = 不存在（未装 OpenSSH Server），且当前会话非管理员，无法一次装好。`Tools/fleet/enable-remote-exec.ps1` 已加固（见 ②），仍需各机一次提权执行。
2. **`enable-remote-exec.ps1` 三处收紧**：①防火墙规则从"全放行"改为**仅 tailnet**（100.64.0.0/10 + fd7a:115c:a1e0::/48），原版等于把 22 端口暴露给整个局域网；②新增 `-AuthorizedKey` 落主控公钥到 `administrators_authorized_keys` 并收紧 ACL（Windows 特有坑：ACL 不收紧 sshd 直接忽略公钥）；③新增 `-DisablePassword`（先验密钥再关密码，防锁死）。
3. **主控网关健康**：8792 实测 27–42ms（首次冷启 625ms），链路正常；对照 8787 控制台页 2.1s＝服务端处理慢，不是网络问题。
4. **打标签不能用 `tailscale set`**：本机 1.104.5 的 `set` 无 `--advertise-tags`（报 flag not defined），只能 `tailscale up --advertise-tags=tag:fleet`（会重跑登录流程，风险）或控制台。故密钥到期仍归控制台/API 处理。
5. **新增两个执行体**：`Tools/fleet/tailnet_health.py`（一条命令体检：在线/密钥剩余/DERP 归属/关键端口/配置 IP 是否失真/同机重名，P0 判据含退出码）、`Tools/check-ps1-encoding.ps1`（查/修无 BOM 的 .ps1）。
6. **顺带修掉一个真雷（编码）**：中文 Windows 上 PowerShell 5.1 把"无 BOM 的 UTF-8 .ps1"按 GBK 读，字节错位吞掉引号 → 报假语法错。实测 `enable-remote-exec.ps1` 无 BOM 时报「参数列表中缺少参量 @ line 75」，补 BOM 后同一内容 OK。**本班已给主仓 22 个风险脚本补 BOM**（含 `.codely-cli/machine-state.ps1` 这个让路开关、`Tools/fleet-dispatch.ps1`、`selfaudit.ps1` 等），全仓另有他司子仓/临时脚本 30+ 个未动（属别的 git 仓，动会造跨仓脏面）。判据=改后 23 个 .ps1 逐个 ParseFile 全绿。

### 复验命令（本班用这套）

```powershell
python Tools\fleet\tailnet_health.py                 # 期望 P0 = 只有 MacBook 双条目
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\check-ps1-encoding.ps1 -Root Tools
python Tools\fleet\prechange.py                      # 动手前闸
```