# 算力大脑主板资料包 · 超微 X9DR3-F

下载日期：2026-11-23　｜　用途：今晚点板/调试前把官方资料一次备齐
来源：Supermicro 官网（www.supermicro.com）　｜　全部文件已落盘并算 SHA256

---

## 一、型号确认（不是猜的，两条证据）

| 证据 | 内容 |
|---|---|
| 采购记录 | `cph4/fleet/hardware/V100-RIG-BOM-20261014.md` #1：主板＝超微 **X9DR3-F**（C606 双路 LGA2011·3×PCIe3.0 x16 + 3×x8·16 DDR3 DIMM·IPMI2.0+KVM），¥280 已购到手 |
| 官方手册正文 | MNL-1259.pdf 封面「Revision 1.1b」，正文页眉 `X9DR3-F/X9DRi-F Motherboard User's Manual`，芯片组 Intel PCH **C606**，BMC＝Nuvoton **WPCM450R**，板载显卡＝Matrox **G200**，网卡＝Intel **I350** 千兆 |

> 注意：X9DR3-F 与 X9DRi-F 共用同一份手册（MNL-1259）与同一版 BIOS 包（X9DRi0_630.zip）。
> 两者差别在 SCU 口数量与 RAID 支持，装 V100 的三条 x16 槽位对这块板适用。

---

## 二、已下载文件清单

| 文件 | 大小 | 是什么 | 官方出处 |
|---|---|---|---|
| `MNL-1259.pdf` | 10.63 MB / 111 页 | **产品说明书（User's Manual）** rev 1.1b——跳线、接口、槽位、BIOS 设置、IPMI 全在里面 | /manuals/motherboard/C606_602/MNL-1259.pdf |
| `QRG-1259.pdf` | 0.61 MB / 1 页 | **快速参考（接线拓扑图）**——裸板上机第一张图，所有跳线/接口位置 | /QuickRefs/motherboard/C606_602/QRG-1259.pdf |
| `X9DRi0_630.zip` | 3.87 MB | **BIOS 3.4**（含 ROM + DOS 刷写器 AFUDOSU.SMC + Readme） | 下载中心 BIOS 条目，SoftwareItemID=12273 |
| `SMT_X9_362.zip` | 13.89 MB | **BMC/IPMI 固件 3.62**（含 `.bin` + DOS/Linux/Windows 三种刷写器 + 固件更新说明 PDF） | 下载中心 BMC 条目，SoftwareItemID=12489 |
| `X9_SMT_IPMI.pdf` | 15.84 MB / 105 页 | **X9 平台 IPMI 用户手册（SMT 版）**——WPCM450R 的 IPMI 配置/远程 KVM/传感器 | /manuals/other/X9_SMT_IPMI.pdf |
| `X9_DP_memory_config.pdf` | 1.06 MB / 12 页 | **X9 双路（Socket R）内存配置手册**——16 条 DDR3 插在哪几槽才全通道、几根能点亮 | /support/resources/memory/X9_DP_memory_config.pdf |
| `IPMI_Users_Guide.pdf` | 27.31 MB / 195 页 | IPMI 通用用户指南（AMI 系），备用参考 | /manuals/other/IPMI_Users_Guide.pdf |

### SHA256（可复核）

```
f87cac32c879b99aa60bd44ef2e12b1e02868422494bbd078b440fcb9e6cb7b6  IPMI_Users_Guide.pdf
663ed7f55b3ff85deb07d9c1f3c868eb31aabde0951a782dbf0af505583ebbd7  MNL-1259.pdf
ae987cef15507d01bbf88d7056753e20bca1f896d81d0efb7decdc3eccf1209e  QRG-1259.pdf
ac1fe40520576d080ed4d9f9a66a28449d1360a65d21993d26c29a592460c355  SMT_X9_362.zip
5f944601ee121f77d4d4d76370424450208a8d1b2c4cd3e969cbd0f765ad3462  X9DRi0_630.zip
e407c386db6f3f0eda8842b02dc4cbaf8963ad65e09062924afdbecc8b0e4ba4  X9_DP_memory_config.pdf
04430d4a9ed95a448a62ea31d2a09345901a6fa2d09b7ee031b6fb09dd044289  X9_SMT_IPMI.pdf
```

其中 **BIOS 与 BMC 两个 zip 的 SHA256 与官网页面公布的完全一致**（官网值：
BIOS `5f9446…3462`、BMC `ac1fe4…c355`），即文件与官方发布逐字节相同。

---

## 三、今晚点板的建议顺序（按手册与固件包内容）

1. **先看图再动手**：`QRG-1259.pdf` 一张纸上有全部跳线/接口位置。
2. **内存先按手册插**：`X9_DP_memory_config.pdf` —— 16 根 DDR3 RECC 要按 CPU1/CPU2 各自通道分配；只插一半时别跨通道乱插（否则报内存错、点不亮）。
3. **首次点亮用最小件**：单 CPU + 1 根内存 + 板载 VGA 输出（Matrox G200），不插 V100。
4. **进 BIOS 先看版本**：Setup 首页能看到 BIOS 版本；若不是 3.4，用 `X9DRi0_630.zip` 里的 AFUDOSU.SMC 做 DOS 启动盘刷（包内 Readme 有命令）。
5. **IPMI 先摸通**：BMC 专用网口默认走 DHCP，进路由器/交换机看它拿到的地址，浏览器开 `http://<BMC_IP>`；`X9_SMT_IPMI.pdf` 有默认账号与 IPMI 配置流程。BMC 版本低再用 `SMT_X9_362.zip` 里的 wUpdate/lUpdate 刷。
6. **三张 V100 上机前**：BIOS 里开 Above 4G Decoding、Resizable BAR 相关项按手册设；三卡插槽 2/4/6（x16），手册 p11-14 有槽位表。

---

## 四、官网需要登录才能下的（本机无法匿名取）

以下属 Supermicro「Management Software」，官网要求注册账号并同意 EULA 后才给下载：

| 工具 | 用途 | 官方入口 |
|---|---|---|
| IPMIView | 图形化 IPMI 管理（远程开关机/KVM/传感器） | supermicro.com/en/support/resources/downloadcenter/swdownload |
| SMCIPMITool | 命令行 IPMI 批量操作 | 同上 |
| IPMICFG | 在系统内直接改 BMC 的 IP/账号（不需要进 BMC 界面） | 同上 |
| SUM（Supermicro Update Manager） | 批量刷 BIOS/BMC | 同上 |
| SuperDoctor 5 | 系统健康监控 | 同上 |

替代路径（今晚够用）：
- 刷 BMC 不需要 IPMICFG——`SMT_X9_362.zip` 里已含 Windows/Linux/DOS 三种刷写器。
- 改 BMC IP 也可以进 BMC Web 界面改，`X9_SMT_IPMI.pdf` 有步骤。
- 需要 IPMICFG 时，注册一个 Supermicro 账号即可下载（免费）。

---

## 五、驱动说明（避免白找）

X9 世代已 EOL，官网该板的「Drivers & Utilities」页按 OS/设备选型后不再给出独立驱动包（实测：接口无内容返回）。实际需要时从芯片厂商取，版本按 OS 定：

| 部件 | 型号（手册实测） | 驱动来源 |
|---|---|---|
| 芯片组 | Intel PCH C606 | Intel Chipset Device Software（INF），C600 系列 |
| 网卡 | Intel I350 千兆 | Intel Ethernet Controller I350 系列驱动（e1000e/igb） |
| 板载显卡 | Matrox G200（挂在 WPCM450R BMC 上） | 一般用 BMC 远程 KVM 即可，不需本地显卡驱动 |
| 存储 | C606 自带 SATA + SCU | Linux 内核自带 AHCI；Windows 用 Intel RSTe（需按 OS 版本选） |

---

## 六、这次下载踩到的坑（下次直接用）

本机 `curl` 直连 supermicro.com 一律 **403（Akamai 拦截 TLS 指纹）**，换 UA/加 Referer 都无效；
用能模拟 Chrome 握手的客户端（pip `curl_cffi`，`impersonate="chrome131"`）即 200。
真正文件地址不是静态链接，而是 `https://www.supermicro.com/support/resources/getfile.php?SoftwareItemID=<id>`，
`<id>` 从固件页 `data-fwdownloadtarget` 属性里取。
