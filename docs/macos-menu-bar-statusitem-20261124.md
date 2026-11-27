# macOS 菜单栏第三方图标不上桌 — 定位报告

日期：2026-11-24
机器：MacBook 主控（MacBookPro18,1 / M1 Pro / 32GB）
系统：macOS Golden Gate 27.2.1
触发场景：安装并自启 Stats 3.0.26（监控）与 Macs Fan Control 1.5.23（风扇），两者的菜单栏图标均不可见。

---

## 一、面清单（这个领域一共 10 个面，逐项状态）

| # | 面 | 状态 | 结论/触发条件 |
|---|---|---|---|
| 1 | 应用是否在跑 | 已验证 | Stats PID 59420、MFC PID 59422 常驻 |
| 2 | 应用是否真的创建了 status item | 已验证 | 最小探针 stderr 打印 `statusItem created, visible=true` |
| 3 | 应用自身配置是否允许显示 | 已验证 | Stats `RAM_widget=mini,memory`、MFC `traySensor=cpu_core_average`、`menubarIcon=2` |
| 4 | 是否有第三方图标管理器拦截 | 已排除 | Hidden Bar（`com.dwarvesv.minimalbar`）与 Ice 均**未运行**；Ice 无配置目录 |
| 5 | 系统是否给新项分配了位置 | **失败点** | 迁移标志 `HasAttemptedMenuBarWorkflowMigration=1`，新项不在迁移名单内 |
| 6 | 菜单栏容量/刘海遮挡 | 部分相关 | 腾槽会改变可见集合，但腾出后进来的全是**既有**项，新项仍不入 |
| 7 | 溢出指示器能否点开 | 不能 | AX 报 `menu-bar-overflow-indicator` 且 `states=["disabled"]`，点击无反应 |
| 8 | 系统偏好键能否改写 | 不能（本版） | `VisibleCC WiFi=0`、`menuextra.clock ShowDate=0` 写入后被 ControlCenter 覆盖/忽略 |
| 9 | 刷新 SystemUIServer 是否有效 | 无效 | 备份并移除 `com.apple.systemuiserver.plist` + `killall SystemUIServer`，无变化 |
| 10 | 重启 ControlCenter 是否有效 | 无效 | 多次 `killall ControlCenter`、复位迁移标志，无变化 |

## 二、决定性实验（最小探针）

自写 40 行 Swift 程序（`/tmp/mbprobe.swift`），只挂一个纯文本 status item `PROBE42`，与应用无关、无签名、无历史记录。

- 单跑（其余第三方全退）：**不显示**，且溢出指示器由 `>>` 变 `<<`（说明它被收进隐藏区）。
- 同期腾出 AltTab+AlDente 槽位：露出 5 个**既有**隐藏项（媒体控制、收藏、Spotify），探针仍不显示。
- 退掉 QQ音乐后再起探针：仍不显示。

**结论：不是这些应用的 bug，也不是空间不够——是这套 macOS 对"迁移之后新注册"的第三方 status item 不分配可见坐标。**

与公开案例吻合：macOS 26.x 起 ControlCenter 用 StatusKit 统一接管菜单栏布局，迁移后新项被置为 y=-17 屏外、且系统不提供自愈 API（参考 jundot/omlx#1497）。

## 三、处置

1. 已保留可用面：两款应用常驻 + 自启（原生登录项 + LaunchAgent 双保险，已做 kill→respawn 实测），数据经 Stats 仪表盘窗口可读（CPU/内存/传感器/风扇）。
2. 待验证的修复：**一次注销或重启**，让 ControlCenter 在会话重建时把当时已存在的项纳入布局。自启已装好，重启后两款会自动在跑，届时观察图标是否出现。
3. 若重启后仍不出现（即系统压根不给新项坐标）：改走不占菜单栏的路径——Stats 桌面小组件（macOS widgets）或常驻仪表盘窗口；或改用已采纳新 API 的监控应用。
4. 已还原实验期间的全部改动：WiFi 可见性恢复 1、时钟键已删、迁移标志保持 1、AltTab/AlDente/QQ音乐 均在运行。

## 四、可复用判据

- 判断"菜单栏项是否上桌"，不要看进程、不要看应用设置、不要信 `isVisible`（刘海遮挡时仍返回 true）。
- 造一个最小 status item 探针，是区分"应用问题 / 系统问题"最便宜的办法（40 行、30 秒编译）。
- 腾槽测试只能证明"容量相关"，不能证明"新项能进"；必须用**腾槽后新起**的对照。
