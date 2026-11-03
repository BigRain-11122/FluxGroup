# 主控 MacBook 游戏环境与设置 v1（2026-11-03）

CEO 令：「我可能会用 macbook 去玩一些游戏，帮我搭建好环境和设置」。
本文件记录**装了什么、为什么装、怎么用、边界在哪**。机器=MacBook Pro 16" M1 Pro / 32GB / macOS 27.2。

## 一、已装（免费路线，已实测可启动）

| 应用 | 版本 | 干什么 | 备注 |
|---|---|---|---|
| Steam | 6.1 | 主力商店：Mac 原生游戏 + 大量独立游戏 | 二进制同时含 x86_64 与 arm64 → 原生跑，不靠 Rosetta |
| Whisky | 2.3.5 | 跑 Windows 独占游戏（Wine + Apple Game Porting Toolkit） | 每个游戏一个瓶子，独立配置；DX11 级基本可用 |
| RetroArch | 1.22.2 | 模拟器前端（NES/SNES/GBA/N64/PS1/街机…） | 只有 x86_64，走 Rosetta；首次启动要在线下载核心 |

安装方式（可复现，已去掉 Gatekeeper 隔离标记）：

```bash
brew install --cask steam whisky retroarch
xattr -dr com.apple.quarantine /Applications/Steam.app /Applications/Whisky.app /Applications/RetroArch.app
```

## 二、老实说的边界（别指望它跑 3A）

1. **M1 Pro 不是游戏显卡**。原生 Mac 3A 屈指可数；大型 Windows 3A 即使能启动，帧数也不体面。
2. **Whisky 的甜点在 DX11 级与小体量游戏**（策略/独立/RPG 老作）。DX12 大作多失败，别浪费时间。
3. **不要装 Parallels 来玩游戏**：Windows-on-ARM 跑 x86 游戏是二次翻译，性能比 Whisky 更差，只适合办公软件。
4. **想认真玩 Windows 3A，唯一正解是 CrossOver 26.3（付费，约 74 美元/年）**，它带更新的 D3DMetal。这属于花钱决定，等 CEO 定，我不代购。

## 三、设置（已按苹果逻辑定好）

| 项 | 值 | 为什么 |
|---|---|---|
| Game Mode | 自动（macOS 14+ 系统级，无需设置） | 焦点在游戏时自动提升 CPU/GPU 优先级、降低蓝牙延迟 |
| 插电低电量模式 | 关 | 满性能；见 `BM-M-POWER-PROFILE-v1.md` |
| 插电系统睡眠 | 不睡（屏幕 10 分钟休眠） | 玩游戏时屏幕不会因系统睡眠被掐 |
| 拔电屏幕休眠 | 5 分钟 | 同上文档 |
| 手柄 | 系统设置 → 蓝牙 → 配对 | Xbox 无线手柄、DualSense/DualShock 原生支持；无需驱动 |

## 四、玩游戏前必做的一件事：让机队让路

这台机器 32GB 统一内存同时养 4B 模型 + 主控脉。开游戏不先让路，两边都难受。

```bash
# 让路（停主控脉+看门狗；加 --with-ai 连本地模型一起停，多让出 3-4GB）
Tools/fleet/ceo_mode.sh start --with-ai

# 玩完恢复（先过 deploy_gate，闸不过不许起，这是 2026-11-02 定的法）
Tools/fleet/ceo_mode.sh stop

# 随时看状态
Tools/fleet/ceo_mode.sh status
```

来回已实测：start 后 pulse/watchdog/执行腿全部停止；stop 后 deploy_gate 六关 PASS、三个常驻全部恢复、PULSE.json 继续刷新。
**让路不改任何配置**，只停常驻进程，`stop` 即回到原样。

## 五、首次使用要做的三步

1. **Steam**：打开 → 登录 → 库里只显示"支持 macOS"的游戏，别看错平台。
2. **Whisky**：首次打开会让你建瓶子（选 Windows 10）→ 装完后在瓶子里装游戏平台或直接拖 exe。
3. **RetroArch**：首次打开 → Online Updater → 下载需要的核心（如 `snes9x`、`mgba`）→ 再加载自己的 ROM。

ROM 与游戏文件自己准备，本机不预置任何受版权保护的内容。

## 六、何时候该停下来

1. 某游戏在 Whisky 里黑屏/闪退超过两次 → 别硬调，换原生 Mac 版或放弃（调 Wine 是无底洞）。
2. 游戏时机器风扇持续满转、帧数一路掉 → 是散热墙，不是你设置错；降低画质或改插电通风。
3. 玩完发现主控脉没恢复（`ceo_mode.sh status` 显示 stopped）→ 立刻 `stop` 拉回来，别让它空跑一夜。