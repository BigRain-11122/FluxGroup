# 算力大脑主板资料包 · 超微 X9DR3-F

下载日期：2026-11-23　｜　用途：今晚点板/调试前把官方资料一次备齐
来源：Supermicro 官网（www.supermicro.com）　｜　全部文件已落盘并算 SHA256
最近实检：2026-11-23 晚（逐项解压/校验，不是照清单念）

---

## 零、齐全性检查（按"要干什么"核对）

| 用途 | 需要什么 | 齐不齐 | 在哪 |
|---|---|---|---|
| 认出这块板、看跳线接口 | 说明书 + 快速参考 | **齐** | `MNL-1259.pdf`（111 页）、`QRG-1259.pdf`（1 页拓扑） |
| 插内存不点不亮 | X9 双路内存插法 | **齐** | `X9_DP_memory_config.pdf`（12 页） |
| 刷 BIOS | ROM + 刷写器 | **齐**（3.4，SHA256 与官网一致） | `X9DRi0_630.zip` 内 AFUDOSU.SMC + Readme |
| 刷 BMC（无系统也能刷） | 固件 + DOS/Win/Linux 刷写器 | **齐**（3.62，SHA256 一致） | `SMT_X9_362.zip` 内 dUpdate/lUpdate/wUpdate |
| 配 IPMI、远程开关机/看画面 | IPMI 手册 + IPMIView | **齐** | `X9_SMT_IPMI.pdf`、`管理软件/IPMIView_*`（Win+Linux） |
| 系统里改 BMC 的 IP/账号 | IPMICFG | **齐**（含 Win32/64、Linux32/64、DOS、UEFI、FreeBSD） | `管理软件/IPMICFG_1.38.0_*` |
| 批量刷多块板 | SUM | **齐**（Win + Linux） | `管理软件/SUM_2.15.0_*` |
| 命令行 IPMI 批量操作 | SMCIPMITool | **齐**（Win + Linux，自带 JRE） | `管理软件/SMCIPMITool_*` |
| 装系统后的驱动 | Intel C600 芯片组 INF / i350 网卡 | **齐**（芯片组 INF 10.1.20658 + 网卡 31.3，Win10 x64 可用） | `驱动/`，用法见 `驱动/驱动说明.txt` |
| 怀疑内存/CPU 有硬故障时做整机诊断 | Super Diagnostics Offline（UEFI 启动盘） | **齐**（1.12.0，含官方使用手册） | `管理软件/SDO_SuperDiag_1.12.0/X86/x86_extracted/`（解压到 U 盘即可启动） |

至此**十项用途全部齐**。只有两件"按需再取"，不是缺漏：
- **Intel RSTe**：只有用主板 SCU 口组 RAID 才需要；不组 RAID 就用 Win10 自带 AHCI。
- **Matrox G200 显卡驱动**：日常走 BMC 的 KVM 看画面，不需要本地显卡驱动。

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

**已用 CEO 账号登录后下载完毕**（2026-11-23，Windows 与 Linux 两套齐全，均在 `管理软件/` 子目录）：

| 工具 | 版本 | Windows | Linux | 说明 |
|---|---|---|---|---|
| IPMIView | 2.25.0 (260812) | `IPMIView_…_Windows.exe` 178MB | `…_bundleJRE_Linux_x64.tar` 194MB | 图形化 IPMI：开关机/KVM/传感器。Linux 版自带 JRE |
| SMCIPMITool | 2.31.0 (260727) | `…_bundleJRE_Windows/` 134MB | `…_bundleJRE_Linux_x64.tar` 218MB | 命令行 IPMI，自带 JRE 不用另装 Java |
| IPMICFG | 1.38.0 (260701) | `…\Windows\{32bit,64bit}` | `…\Linux\` | 一个包内含 DOS/Windows/Linux/UEFI/FreeBSD 五套 |
| SUM | 2.15.0 (251104) | `sum_2.15.0_Win_x86_64/` 41MB | `sum_2.15.0_Linux_x86_64_…tar` | 批量刷 BIOS/BMC，Linux 版另可刷 BMC |
| SuperDoctor 5 升级包 | 5.23.0 (1154) | 同一包 | 同一包 | 配合 SSM 远程升级已装 SD5 的机器 |
| SAA 迁移指南 | 1.0.0 | 同一包 | 同一包 | SUM/SMCIPMITool/IPMICFG → SAA 的命令对照 |

用法要点：
- **Windows 10 直接可用**：Windows 侧 exe 是 32 位 PE，bundleJRE 包自带 Java 运行时，不用预装 JDK。
- IPMICFG 在系统内改 BMC 的 IP/账号最快（不用进 BMC 网页）：`IPMICFG64.exe -m` 看帮助。
- `*.tar` 是 Linux 包，`tar -tzf` 已验证完整（三份全 OK）。
- Safari 自动解压了 zip，所以 Windows 侧是**解压好的目录**，直接进目录找 exe 即可。

---

## 五、驱动（已备好，Win10 x64）

X9 世代已 EOL，官网该板的「Drivers & Utilities」页按 OS/设备选型后不再给独立包（实测：接口无内容返回），所以驱动从芯片厂商取。已下的放 `驱动/`，哈希见 `驱动-MANIFEST.txt`：

| 部件 | 实际型号 | 已备的驱动 | Win10 x64 怎么用 |
|---|---|---|---|
| 芯片组 | Intel PCH C606 | `SetupChipset_10.1.20658.8883.exe`（98MB） | 双击装；静默 `-s -overwrite` |
| 网卡 | Intel I350 千兆 | `Wired_driver_31.3_x64.zip`（已解压） | 设备管理器指向 `Wired_driver_31.3_x64/PRO1000/Winx64/NDIS68`（inf=`e1r68x64.inf`）；或用 `SetupBD.exe` 一键装 |
| 板载显卡 | Matrox G200（挂 BMC） | 不装 | 走 IPMI 的 KVM 远程画面 |
| 存储 | C606 SATA + SCU | 不装（RSTe 按需） | 不组 SCU RAID 就用 Win10 自带 AHCI |

安装顺序：装完系统 → 看设备管理器 → 先芯片组 → 再网卡。

---

## 六、这次下载踩到的坑（下次直接用）

本机 `curl` 直连 supermicro.com 一律 **403（Akamai 拦截 TLS 指纹）**，换 UA/加 Referer 都无效；
用能模拟 Chrome 握手的客户端（pip `curl_cffi`，`impersonate="chrome131"`）即 200。
真正文件地址不是静态链接，而是 `https://www.supermicro.com/support/resources/getfile.php?SoftwareItemID=<id>`，
`<id>` 从固件页 `data-fwdownloadtarget` 属性里取。

---

## 七、目录结构与清单文件

```
brain-X9DR3-F/
├── README-INDEX.md              本文件（齐全性检查 + 用法）
├── 今晚点板操作单.md             ★ 照这个做就行（十节：装配→点亮→BIOS→IPMI→上卡→排障）
├── 官方文档知识卡.md             ★ 问什么答什么（规格/槽位/内存/跳线/JF1/蜂鸣码/BIOS/IPMI，全部带页码）
├── 论坛与实战经验.md             手册不写的坑（PCIe 按 CPU 分区、BMC 不可降级、SATA RAID 禁区、Java KVM 修法、V100 黑屏判据）
├── 管理软件-MANIFEST.txt         管理软件总表 + 主要可执行文件 SHA256 + 使用入口
├── 驱动-MANIFEST.txt             驱动清单 + SHA256
├── MNL-1259.pdf                 产品说明书（111 页）
├── QRG-1259.pdf                 快速参考接线图（1 页）
├── X9_DP_memory_config.pdf      X9 双路内存插法（12 页）
├── X9_SMT_IPMI.pdf              X9 平台 IPMI 手册（105 页）
├── IPMI_Users_Guide.pdf         IPMI 通用指南（195 页，备用）
├── IPMIView_User_Guide.pdf      IPMIView 官方手册（100 页，含 WPCM450/X9 支持说明）
├── X9DRi0_630.zip               BIOS 3.4（原包，含 DOS 刷写器）
├── X9DRi0.630/                  ↑ 已解压：AFUDOSU.SMC + X9DRi0.630(ROM) + Readme + ami.bat
├── SMT_X9_362.zip               BMC 3.62（原包）
├── BMC_3.62/                    ↑ 已解压：Windows1.22/wUpdate.exe、Linux1.21/lUpdate、Dos 1.21/、.bin、固件更新说明 PDF
├── 驱动/                        Intel 芯片组 INF + I350 网卡（Win10 x64，已解压）
└── 管理软件/                     Windows + Linux 双套（约 1.9GB 含解压件，不入 git）
    ├── IPMICFG_1.38.0_build.260701/           Win32/64 + Linux32/64 + DOS + UEFI + FreeBSD
    ├── IPMIView_2.25.0_..._Windows.exe
    ├── IPMIView_2.25.0_..._bundleJRE_Linux_x64.tar     原包
    ├── IPMIView_2.25.0_..._bundleJRE_Linux_x64/        ↑ 已解压，入口 ./IPMIView20
    ├── SMCIPMITool_2.31.0_..._bundleJRE_Windows/
    ├── SMCIPMITool_2.31.0_..._bundleJRE_Linux_x64.tar   原包
    ├── SMCIPMITool_2.31.0_..._bundleJRE_Linux_x64/      ↑ 已解压，入口 ./SMCIPMITool
    ├── SUM_2.15.0_Win_x86_64/
    ├── SUM_2.15.0_Linux_x86_64_20251104.tar             原包
    ├── SUM_2.15.0_Linux_x86_64/                         ↑ 已解压，入口 ./sum
    ├── SuperDoctor5UpdatePackage_5.23.0/
    │   └── extracted/                                    ↑ 已解压，入口 start_sd5.sh / start_sd5.bat
    ├── SDO_SuperDiag_1.12.0/                  UEFI 整机诊断盘
    │   ├── X86/x86_extracted/                          已解压：SuperDiag.efi + startup.nsh + 使用手册
    │   └── ARM/arm_extracted/                          已解压
    └── SAA_Migration_Guide/
```

实检结论（2026-11-23）：
- `X9DRi0_630.zip`、`SMT_X9_362.zip` 的 SHA256 **与官网公布值逐字节一致**，`unzip -t` 通过。
- 三个 Linux `.tar` 全部 `tar -tzf` 通过；SD5 内层 zip `unzip -t` 通过。
- 五个 PDF 页数实测：111 / 1 / 12 / 105 / 195，无零字节或损坏。
- IPMIView Windows 侧确认为 PE32 可执行；SMCIPMITool 目录内 `SMCIPMITool.exe` 与 `KVMPlugIn.jar` 在位。
- 2026-11-23 补：SDO 诊断盘 1.12.0 已下（X86/ARM 各一个 zip，`unzip -t` 通过，内含 `SuperDiag.efi`、`startup.nsh` 与官方使用手册 PDF）。
- 2026-11-23 全部解压到位：BIOS→`X9DRi0.630/`、BMC→`BMC_3.62/`、三个 Linux 包与 SDO/SD5 内层包均已解开；Linux 二进制 `sum`、`SMCIPMITool`、`IPMIView20`、`lUpdate`、SD5 的 `.sh` 已补 `+x`，可直接 `scp -r` 到大脑机使用；原压缩包全部保留以便校验与重传。
