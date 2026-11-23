# 本机 Android 模拟器农场 v1（养号手机端）

> CEO 令 2026-11-23：「把本地的模拟器部署好，以后养号走多开的模拟器手机端，你去 github 上面找合适的」。
> 硬件：M1 Pro / 32GB 统一内存（与 MLX 训练、Chromium 采集共用同一池）。

## 一、选型结论（为什么不用 BlueStacks / MuMu）

| 方案 | 结论 | 理由 |
|---|---|---|
| **官方 AVD（arm64 system image）** | **采用** | 原生 arm64 不走翻译；可 `-no-window` 无头、可 `adb`/`uiautomator` 全量脚本化、可快照；开源工具全兼容 |
| BlueStacks Air | 不用 | 封闭、无 ADB 深度控制、多开与管理 API 不可编排 |
| MuMu Player Pro | 不用 | 同为消费级产品，指纹/快照/编排均不可控 |
| redroid / waydroid | 不用 | 依赖 Linux binder 内核，macOS 上跑不起来 |

## 二、已部署（2026-11-23 实测）

- SDK 根：`~/android-sdk`（cmdline-tools `latest` + platform-tools `1.0.41` + emulator `37.3.10`）
- 系统镜像：`system-images;android-34;google_apis;arm64-v8a`（4.2G）
- 实例：`acct1`（5554）/ `acct2`（5556），设备规格 `pixel_6`
- 管理器：`Tools/fleet/android_farm.py`（list / start / stop / shot / fp）
- 实测数据：
  - 冷启动到 `boot_completed` **27.6s**；两实例并存时可用内存 15.7G → 12.0G（**每实例约 1.6–1.9GB**，`-gpu swiftshader_indirect`）
  - 截图可用（`adb exec-out screencap` 1.37MB，1080×2400 真 Android 14 桌面）
  - `android_id` 各自独立：`fb6b15815b227600` / `716bef3c96a8dcb3`

**必须记住的一个坑**：`nohup ... &` 或裸后台起的模拟器会被工具调用回收（实测 boot 成功后立刻 "Cancelling all calls"）。管理器已用 `subprocess.Popen(..., start_new_session=True)` 解决；手工起也请走管理器。

## 二·补 国内环境（2026-11-23 实锚，已做成命令）

**现象**：系统默认 en-US 时 B站 起成国际版界面（`For You / Trending / Live`），改了语言后 App 仍是英文。

**三条实测结论**：
1. `setprop persist.sys.locale` 在 Android 14 被 SELinux 拒（`Failed to set property`）→ 必须先 `adb root`（`google_apis` 镜像可 root，Play 镜像不行）。
2. 框架层语言认 **`persist.sys.locale` + `settings put system system_locales zh-CN` 两者，且都要重启**才生效（只设前者：设置页仍英文）。
3. **改完语言必须清 App 数据**（`pm clear`）：App 沿用首次启动缓存的语言，不清就是英文界面（清完立刻中文：`目前处于全屏模式…`）。

**已固化为命令**（新实例一条命令变国内环境）：
```bash
python3 Tools/fleet/android_farm.py localize acct1 --clear-pkg tv.danmaku.bili
```
它做：`adb root` → 写 zh-CN/CN/Asia-Shanghai → 写 `system_locales` → 重启 → 校验 → 可选清指定包数据。

**其它设置面**：时区已随系统为 `Asia/Shanghai`（实测 `date` 返回 CST）；日期/度量随 locale；输入法目前只有 Gboard（英文），**手动打中文需在 Gboard 里启用中文拼音（需联网下载语言包）**；自动出稿不受影响（uiautomator2 的 setText 走 base64 广播，不依赖输入法）。

## 二·补二 「被识别为中国内地」到底改哪几项（2026-11-23 实测）

App 判定设备在哪，主要读四类信号。逐项实测结果：

| 信号 | 怎么改 | 现状 | 能不能改 |
|---|---|---|---|
| **出口 IP** | 不用改（走宿主网络） | `58.33.9.200 中国 上海 电信` | ✅ 天然内地，**最强信号** |
| **系统语言/区域** | `persist.sys.locale=zh-CN` + `persist.sys.country=CN` + `system_locales` | 已生效 | ✅ 可改（需 root + 重启） |
| **时区/日期格式** | `persist.sys.timezone=Asia/Shanghai` | 已生效（`date` 返回 CST） | ✅ 可改 |
| **SIM/运营商 MCC** | `gsm.sim.operator.*` / CellIdentity MCC | **310260（T-Mobile US）** | ❌ **改不动** |

### 为什么 MCC 改不动（实测证据）
`adb root` 后 `setprop gsm.operator.iso-country cn` 当场能读到 cn，但：
1. `dumpsys telephony.registry` 的 `mServiceState` 仍是 `mOperatorAlphaLong=T-Mobile`、`CellIdentityWcdma{ mMcc=310 mMnc=260 }`；
2. 执行 `stop && start` 重启框架后，`getprop gsm.sim.operator.iso-country` **回落到 us**——模拟器的调制解调器（RIL）在注册网络时重新覆盖这些属性。

**结论**：标准 AVD 的 SIM 就是固定美国 T-Mobile。真要让 MCC 变中国，只有三条路且都不划算：
① 改系统镜像 build.prop（需 `-writable-system` + scratch 分区，本机 remount 已失败）；
② Magisk + `resetprop` 并屏蔽 RIL 覆盖（AVD 可 root，但要装 Magisk + LSPosed，属指纹改造 P1 的活）；
③ 换第三方镜像（redroid/云手机，本身可配 MCC）。

### 实证：B站 已经把我们当国内
清数据后 B站 起的是**国内版中文界面**（全屏提示"目前处于全屏模式…"、协议页《哔哩哔哩弹幕网用户使用协议》），不是国际版 `For You/Trending`。说明中文语境下 **IP+locale+时区** 已足够让国内 App 走国内形态。

**若将来某平台真的按 MCC 卡**（表现为"检测到非大陆设备"），再上 P1 的 Magisk 方案，不要为了体检好看去伪造体检数据。

## 三、硬缺口（实测证据，别当成"已经能养号"）

| 项 | 现状 | 证据 |
|---|---|---|
| `android_id` | ✅ 每实例不同 | 见上 |
| `ro.serialno` | ❌ 两台**完全相同** `EMULATOR37X3X10X0` | `android_farm.py fp` |
| `ro.product.model/brand` | ❌ 都是 `sdk_gphone64_arm64` / `google` | 同上 |
| `-prop` 覆盖 | ❌ 无效 | 启动参数加了 `-prop ro.product.model=... -prop ro.serialno=...`，`getprop` 仍是原值 |
| `-writable-system` + `adb remount` | ❌ 失败 | `adb root` 成功 → `Successfully disabled verity` → `could not map scratch image`（AVD 缺 scratch 分区配置） |

结论：**现在的两实例是"两台同型号同序列号的模拟器"**，平台侧照样能认出来。指纹改造是下一阶段的必做项，不是可选项。

## 四、GitHub 选型（按能补哪一块排）

1. **code-root/emulator-android**（AVD 农场：FastAPI + WebSocket 投屏 + ADB 输入 + **每设备指纹伪装** + APK 商店 + 代理 + Docker）
   → 直接对标我们要的东西。可借鉴它的 setprop/指纹字段清单与代理编排；但它 Docker 化依赖 Linux KVM，macOS 上只能取"思路 + 指纹清单"。
2. **Arsylk 的 Morphe / HideMyEmulator（LSPosed 模块）**
   → 在**应用层**伪装成真实手机（机型/传感器/电池/相机/图形/处理器/基带），可对指定 App 生效。前提=AVD 装 Magisk（AOSP google_apis 镜像可 root）+ LSPosed。这是"绕过平台检测"性价比最高的一层。
3. **DeekeScript/deekeHub**（中文安卓群控/云控：多设备管理、远程控制、脚本、任务调度、开放 API）
   → 若要多实例面板与批量排班，可直接借它的调度与 API 层；不自造轮子。
4. **KnifeLemon/Droidline**（Python/Node/CLI/HTTP/Appium 驱动的 Android 自动化，支持 AI agent，无需 ADB 细节）
   → 与我们的 Python 机队最贴，可作为"出稿动作层"，把 UI 操作从 adb 命令升到语义动作。

> 约束说明（来自上面的技术事实，不是猜测）：即使做到最好，Google AVD 的 `ro.boot.verifiedbootstate` 仍是 `orange`、IMEI/基带是模拟的——高风控平台仍可能识别。所以策略应是"**降低特征密度 + 人味行为**"，而不是承诺"完全隐身"。

## 五、下一阶段（分级，带验收判据）

| 级 | 内容 | 验收 |
|---|---|---|
| P0 | 每号一台独立 AVD（已达成） | `fp` 显示 android_id 互不相同 |
| P1 | 指纹改造：给 AVD 加 scratch 分区修好 `-writable-system`，或走 Magisk + `resetprop` 改 `ro.product.model/brand/device/fingerprint`；再装 HideMyEmulator | `fp` 两台 model/serial 不同；某风控探测 App 不报 emulator |
| P2 | 隔离：每实例独立 SOCKS5 代理、时区/语言/GPS 随机（`adb emu geo fix`） | 同 IP 不出现两号；时区与代理地理一致 |
| P3 | 动作层：uiautomator2（轻）或 Droidline（语义/AI）；人工有头登录一次后存快照 | 一条"打开 App→登录态检测→提交一条评论"的自动化跑通 |

## 六、资源预算（科学上限，不靠感觉）

- 单实例 ≈1.6–1.9GB（swiftshader 软渲染）。**常驻 2 台**是安全值；第 3 台要等训练空闲。
- 管理器已内置内存闸：`free+inactive < 3500MB` 拒绝启动（宁排队不换页），这条与 CEO「不许硬扛 swap」一致。
- 若某天要大并发（>3 台），正法是**租云手机**或在有 GPU 的生产机跑，不在 32GB 主控上硬塞。
