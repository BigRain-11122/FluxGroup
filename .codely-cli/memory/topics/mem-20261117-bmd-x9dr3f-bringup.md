# bm-d（算力大脑）X9DR3-F 装机正身 2026-11-17

> 用途：bm-d 装机/点亮/入网时的硬事实。查配置前先读本文，勿按旧记忆或旧配置复述。
> 手册正身 = Supermicro MNL-1259（X9DR3-F/X9DRi-F User's Manual，111 页）。
> 取法：厂商 CDN 直连 403 → 走 `https://web.archive.org/web/<ts>id_/` 原始快照可下。

## 一、主板硬事实（官方手册 + 产品页）

- 型号 **超微 X9DR3-F**，C606 芯片组，双路 LGA2011（E5-2600 / v2），E-ATX 30.5×33.2cm
- **E5-2600 v2 需 BIOS 3.0 以上**（产品页原文 `BIOS version 3.0 or above is required`）
- PCIe：**3× x16 + 3× x8**。x16 = **PCI-E 2 / 4 / 6**；槽 2 归 **CPU1**，槽 4 / 6 归 **CPU2**
- 产品页原文：`Both CPUs need to be installed for full access to PCI-E slots and onboard controllers`
  → 单 CPU 时 CPU2 那几个槽是死的
- 内存：16× DDR3 DIMM，**每 CPU 8 条**（P1 DIMM A/B/C/D、P2 DIMM E/F/G/H），丝印提示 `ALWAYS POPULATE DIMMxA FIRST`
- 视频：**Matrox G200eW（走 BMC）**，板载**只有 1 个 VGA 口**，无 DVI/DP/HDMI
- 网络：2× Intel i350 千兆 + **1× 专用 IPMI LAN（Realtek RTL8201N 独立 PHY）**
- 管理：IPMI 2.0 + **KVM-over-LAN** + virtual media over LAN；BMC = Nuvoton WPCM450
- BIOS：AMI，128Mb SPI Flash，UEFI 2.3.1（无 TPM 2.0）

## 二、后置 I/O 顺序（手册 2-21 页图，左→右）

```
[COM1 绿色DB9] [ ③IPMI_LAN 在上 ] [①LAN1] [②LAN2] [VGA 蓝色DB15]
               [ PS/2 | 4×USB 在下 ]
```

- **IPMI_LAN = 跟 USB 组在一块、坐在 USB 上方的那个 RJ45**（原文：located **above USB 0/1 ports**）
- **LAN1 / LAN2 = 紧挨 VGA 左边的那一对**（系统网口，归操作系统）
- 2026-11-16 现场曾误判「VGA 左边那个是 IPMI」，实为 LAN2 —— 已由手册图纠正

## 三、点亮/显示相关的三个坑

1. **VGA Priority 默认 Onboard** → 独显在整个 POST 阶段不输出，只有板载 VGA 出画面。不改这一项，插什么卡都黑屏。改法：BIOS → Advanced → PCIe/PCI/PnP Configuration → `VGA Priority = Offboard`，同时 `Above 4G Decoding = Enabled`。
2. **显示器只有 HDMI/DP 时无解** → VGA 是模拟信号，转 HDMI/DP 必须用**带供电的主动转换器**，无源线一律不通。替代路径 = IPMI KVM 看屏。
3. **DP→DVI 无源线在 GeForce 上不出信号** → N 卡无 DP++，需主动转换。**HDMI→DVI 是纯 TMDS 线序对接，一定能用**。

## 四、IPMI 接入

- 账号 **ADMIN / ADMIN**（手册 1-3 页 Note 2：默认用户名 ADMIN、密码 ADMIN）
- BMC 吃 **5V 待机电** —— 电源主开关必须开，不是按机箱电源键
- **BMC Enable 跳线 JPB1**：`1-2 = 启用（默认）`、`2-3 = 禁用`（手册 2-35 页）——拆机板可能被动过
- IPMI 口 LED（手册 2-37 页）：**左绿 = 速率，右琥珀 = 连接/活动**；全灭 = BMC 没供电或跳线禁用
- IP 不是死的：BIOS 4-x 页 **IPMI Configuration** 里可直接读 `Station IP Address` / `Station MAC Address`，`Configuration Address Source` 可切 **Static / DHCP**
- 找 IP 的最快法 = 路由器 DHCP 客户端列表里找 MAC 前缀 `00:25:90` / `AC:1F:6B` / `3C:EC:EF`（超微厂商号）
- 打不开的常见原因：网段不同 / BMC 走 DHCP / 浏览器把 http 自动跳 https（老 BMC 的 TLS 被现代浏览器拒绝，必须手打 `http://`）

## 五、现场状态（2026-11-17 凌晨）

- 已购合计 **¥5,408**（主板 280 + 2696v2×2 105 + 16G×16 1910 + V100×3 1812 + 转接板 435 + 冷头扣具 270 + 冷排 235 + 电源 137 + 机架 199 + 排插 25）
- **单 CPU + 旁边 4 根内存 → 能 POST**（蜂鸣、键盘灯、鼠标灯正常）
- **双 CPU → 不 POST（未解决，唯一未清的硬件问题）**。排查顺序：①第二个 CPU 的 JPWR2 8pin 是否接 ②CPU2 那组内存槽是否为空 ③CPU2 座子针脚 ④两颗 CPU 对调位置
- 3080 临时装机验机用（**Tesla + GeForce 禁同机**，BOM 红线，装完系统必拔）
- 主板实购 CPU 型号 = **E5-2696 v2（12C/24T，130W，OEM SR19G）**，不是 BOM 原定的 2695v2

## 六、配置档案同步状态

- 2026-11-17 已把 `cph4/fleet/STATIONS.json`、`CPU-PLAN-v1.json`、`MODEL-COMPUTE.json` 三处 CPU 型号由 2695v2 统一改为 **2696v2**
- 生成物 `cph4/fleet/FLEET-SPEC.md` 已 `python Tools/fleet/fleet_doc.py --write` 重出，`--check` 后「文档与配置一致、源间漂移 0 处」
- 仍写 2695v2 的历史件（BOM §一 规划节、MODEL-COMPUTE-v1.md、FLEET-COMPUTE-ARCHITECTURE.md、BMD-ONBOARDING-v1.md）属规划期记录，未改写
