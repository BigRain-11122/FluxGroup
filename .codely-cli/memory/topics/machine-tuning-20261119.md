# 本机（MacBook 主控）调优定案 — 2026-11-19

> 索引自 `.codely-cli/memory.md`。本文件记录**已实测的结论**，含对早前错误结论的勘正。

## 1. 风扇：最终走 Macs Fan Control 自定义曲线（勘正早前"自建 SMC 守护"结论）

**早前结论错在哪**：曾判定 Macs Fan Control「无 AppleScript / URL scheme / 命令行参数，改 plist 会被启动覆盖成 `Predefined:0`，故正法是自写 `Tools/fleet/fan_boost.py` 直连 IOKit AppleSMC 装 LaunchDaemon」。上述接口事实成立，但**推论错了**——Free 版本身就支持自定义曲线，不需要付费也不需要自建守护。

- 自建径路实测失败：`fan_boost.py` 在 M1 上卡在 `IOServiceOpen` 返回 `kIOReturnBadArgument`，穷举参数组合后直接 Bus error。不要再走这条路。
- 正法：用 **Quartz 原生鼠标/键盘事件驱动它那套 Qt 界面**完成配置（不弹 TCC 权限框，不用 osascript 控浏览器那类做法）。
- 真正的毛病：两个风扇的**传感器默认绑成 Airport Proximity（Wi-Fi 模块温度）**，所以 CPU 烧起来风扇也不动。
- 生效配置：两风扇传感器都改 **CPU Core Average**；左扇 49→75℃、右扇 48→76℃ 线性提速。
- 实测验证：CPU 70℃ 时左 3548 RPM、右 1635 RPM，曲线在按温度实时调节（右扇天然偏低，属机型差异，不是配置错）。
- **前提**：Macs Fan Control 必须保持运行（可缩到菜单栏），退出即回到系统自动曲线。
- 可另存 Preset，便于重装/换机后一键恢复。

## 2. 本机 AI 环境 pin（2026-11-19 实测，均已是最新或按令保持）

- `ollama 0.40.16`（最新）；8 个模型实跑，`ollama ps` 确认 **100% GPU / runner=mlx**。
- `mlx 0.32.4`(GPU)、`mlx-lm 0.32.2`、`torch 2.15.0`(MPS)、`numpy 2.5.4` 均最新；`transformers 5.22.2→5.23.0`、`pip 26.3`。
- `ffmpeg` **保持在 7.1**：macOS 27.2.1 上无 brew bottle；源码编译实测 23 KB/s，需 20–40 分钟，而本机按令不做转码 → 停止编译，备份为 `~/bin/ffmpeg-7.1`。
- `ollamamodel` 监听收窄 `0.0.0.0` → **`127.0.0.1:11434`**，并退出 Ollama.app 让 launchd 独占端口。

## 3. 系统通知/专注模式：不可程序化（复核结论）

- `com.apple.ncprefs.plist` 四个候选位置全不存在；`~/Library/DoNotDisturb/DB` 连 `ls` 都 `Operation not permitted`；ControlCenter 无 AX 菜单栏；`sudo` 需密码。
- 旧版勿扰键**能写但不生效**（A/B 实测）。
- 判据：**"写得进去" ≠ "生效"**。这类系统偏好只能 GUI 手动一次。

## 4. 通知弹窗的燃料（补记，与 2026-11-15 结论一致）

- 高频 spawn python3 的机队 LaunchAgent 是燃料（`statesync`/`locallane` 60s、`seatdispatch` 180s、`drive` 300s）。
- 正法仍是 `launchctl disable gui/$UID/<label>`（持久）＋ 目录 `chflags uchg`；`restore-startup.sh` 必须先 `chflags nouchg` + `launchctl enable`。
- 注意：本轮把归档里**全部 44 个** label 都 disable 了（不只是高频那几个），恢复时按需挑（`bash Tools/restore-startup.sh pulse console`）。

## 电池 + 低功耗模式：训练慢 4.6 倍（2026-11-20 实锚）

- 同一段 shallow 训练：**电池 + lowpowermode=1 时 18.6 秒/步**，接电 4 秒/步；
  电量 1 小时内见底（83% 报剩余 1:07）。这是 macOS 对 GPU 的限速，不是代码问题。
- 处置：`train_forever.power_verdict(on_ac, lowpowermode)` 纯函数 + `power_ok()` 读 pmset，
  电池或低功耗 → 记 `last_rc=POWER` 并直接返回（不记 FAIL，避免触发重试），自检 3 条。
- 与 CEO「不许留余量」令不冲突：这不是保守限流，是硬件限速 + 断电会丢整轮的事实。
- 另：**mlx 训练日志是 tqdm 写文件、有缓冲**，`tail` 看着停在 iter 110 其实已到 300；
  判断训练是否推进只认 **checkpoint 文件落盘 + 进程 CPU 时间增长**，别读日志行号。
