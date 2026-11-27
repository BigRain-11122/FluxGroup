# bm-m 本机常驻与硬件状态（2026-11-20 实测）

CEO 令：「把本机要加载的效率软件 功能软件什么的都打开」。

## 一、效率/功能软件：哪些是常驻型
| 类别 | 应用 | 2026-11-20 状态 |
|---|---|---|
| 必驻菜单栏 | Mos（鼠标平滑）、Itsycal（日历）、Stats（系统监控）、Raycast（启动器）、AlDente（充电上限）、Hidden Bar（图标收纳）、MonitorControl（外屏亮度） | 原本就在跑 |
| 本轮补开 | AltTab（窗口切换）、Rectangle（贴边布局）、Maccy（剪贴板历史）、Bob（划词翻译） | 已开，全部运行中 |
| **不要同开** | **Ice 与 Hidden Bar 都是菜单栏图标管理器**，同时跑会互相打架 | Ice 保持不开 |
| 按需型（不常驻） | Snipaste/Shottr（截图）、Keka、IINA、iTerm/Ghostty、HandBrake、Motrix、AppCleaner、ForkLift、Skim、LibreOffice、Canva | 点开才用，别放登录项 |

判据：**"要不要放登录项"看它是否必须在后台持续工作**（菜单栏状态、常驻热键），不是看它是不是效率工具。

## 二、机队常驻：实测 14 个，与"4 项白名单"陈述不符
`launchctl list | grep com.fluxgroup` = **14** 个：pulse、console、ollamamodel、mlxlora、trainloop、trainlock、social24x7、socialagentday、socialloop、practice10、traindone、corpusbake、usersession、acceptrun。
- 2026-11-20 之前 **pulse 与 console 都没在跑**（机队在动但 L0 编排层和一屏是空的）；本轮用 `launchctl load -w` 补起（`launchctl bootstrap` 报 `5: Input/output error`，与 memory 里 tool-pitfalls 记录一致）。
- **CODELY.md 里"现行=恒定 4 项白名单"这句已被现实推翻**（实际 14 项，patrol 也在报"自启 17 项"越界）。下一轮改 CODELY.md 时要一并校正，别当成"4 项"去审计。
- 一屏 `127.0.0.1:8787` 起来后 HTTP 200；`8792`（llm gateway）、`8788`（LoRA 服务）、`11434`（ollama）本就在听。
- `FLEET-PAUSED` 哨兵在位（`.codely-cli/state/FLEET-PAUSED`，11-15 23:21），所以 pulse 起来也会跳过复制 plist 的三个阶段，不会弹窗。

## 三、AlDente 充电上限不生效的完整根因（可复用到任何"设了没生效"）
现象：`chargeVal = 80` 但电池 **96% 仍在充**。三条同时成立：
1. **助手 XPC 断了**：`/Library/PrivilegedHelperTools/com.apphousekitchen.aldente-pro.helper` 在跑（root），但 App 日志报 `bootstrap look-up: xpc_error=[3: No such process]` —— App 调不到助手。
2. **激活流程没走完**：偏好 `hasBeenActivated = 0`、`showHelperInstallationMessage = 1`。
3. **未授权**：`paddleLicense` 为空（版本 1.40.1）。
**关键坑**：`defaults write com.apphousekitchen.aldente-pro launchAtLogin -bool TRUE` **写不进去**——App 用 SMAppService 管登录项，重启后会把该键写回 0；真正的值看系统登录项（`osascript -e 'tell application "System Events" to get the name of every login item'`）。写完 defaults 要复查，别信。
**正路**：优先用 macOS 自带的「充电上限 80%」（系统设置→电池，不依赖第三方、不受未授权影响）；要用 AlDente 就得重装/重启助手（需 root）+ 在 UI 里完成激活。

## 四、电池硬件事实（影响排活）
`system_profiler SPPowerDataType`：**Maximum Capacity 78%、Cycle Count 662、Condition = Service Recommended**；`ioreg` 里 DesignCapacity 8694 / FullChargeCapacity 6239。
→ 该机电池已到 Apple 建议维修线。**别把长时重活（整夜训练、长渲染）压在这台机上靠电池扛**；真跑要接电且先修上限，否则长期 100% 顶充会加速衰减。

## 五、性能激进档（2026-11-20 已落地，插电生效）
CEO 令：「性能释放给我激进」，随后追加「我还是需要苹果系统的设计效果 我是美工」。
**已设**（全部只作用于 AC，电池策略未动）：
- `pmset -c powernap 0 standby 0 autopoweroff 0 womp 0 sleep 0 disksleep 0 lowpowermode 0`
- `defaults write NSGlobalDomain NSAppSleepDisabled -bool YES`（App Nap 全局关，后台 python 不降频）
- `sudo sysctl -w debug.lowpri_throttle_enabled=0`（解 I/O 低优先级节流；**重启失效**，要常驻得挂 daemon）
- `defaults write com.apple.SoftwareUpdate AutomaticCheckEnabled -bool FALSE`（不再后台拉更新）
**撤掉的**：`NSAutomaticWindowAnimationsEnabled=false`（实测把 WindowServer 从 59% 压到 25%，但 CEO 否决——视觉观感优先）。
**禁区**：窗口动画 / 降低透明度 / 减弱动态效果 一律不许关（见 CODELY.md User 段 2026-11-20 条）。
**做不到**：High Power Mode 在 M1 Pro 上没有（`pmset -g custom` 无 `highpowermode` 键，该功能仅 16 寸 Max 机型）。
**风扇**：Macs Fan Control 跑 sensor 曲线，CPU 48–49℃ → 75–76%，已是激进档，未动。

## 六、两个测量陷阱（差点误判，务必复用）
1. **macOS 的 `ps -o pcpu` 是进程生命周期均值，不是瞬时值**——一个挂了 9 天的休眠进程也会显示 20–35%，把它当"持续大户"就会去修根本不存在的浪费。**正确取法=`top -l 2 -n 10 -o cpu` 取第二次采样**（第一次是自启动以来的均值）。
2. **归因要看宿主**：WebKit 的 `WebContent/GPU` 子进程 ppid 是 1，`lsof` 也指不到 App；正解是 `lsappinfo info -only name <pid>`，实测揪出 47% 的那个属于 Tuanjie Cowork（本会话 UI 在流式渲染），不是 Raycast。改完这一条，"Raycast 卡死"的假设当场被推翻。
配套结论：本轮没有真正的空转大户——python 61% 是 `mlx_lm lora --train`、chrome 18% 是养号采集、WebKit 是本会话界面；Spotlight（mds/mdworker）只有 0.4%，**没有浪费可收，所以不动 Spotlight 索引**。

## 七、航拍壁纸可自愈（不用备份）
删掉 `~/Library/Application Support/com.apple.wallpaper/aerials`（约 10G）后，macOS 会按需自动重下——2026-11-20 实测删后数小时内已回到 5.8G / 8 条 .mov，系统设置里直接可选航拍。所以"删壁纸省空间"不会破坏观感，只是下次要等下载。
