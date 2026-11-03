# 主控 MacBook 游戏环境与设置 v2（2026-11-03）

CEO 令：「不要 steam，不跑大作，大概就用 switch 什么的玩玩」。
本文件记录**装了什么、缺什么、怎么用**。机器=MacBook Pro 16" M1 Pro / 32GB / macOS 27.2。

## 一、现在的状态

| 项 | 状态 | 说明 |
|---|---|---|
| Steam | **已卸载** | 应用、cask 记录、用户数据都已清掉（CEO 令不要） |
| Ryujinx（Ryubing 分支 1.3.3） | **已装并启动通过** | 官方源 `git.ryujinx.app`，universal 二进制（含 arm64），已清 Gatekeeper 隔离 |
| RetroArch 1.22.2 | 已装 | 老主机（NES/SNES/GBA/N64/PS1/街机）用它；核心首次启动在线下载 |
| Whisky | 已装 | 暂时不用：那是跑 Windows 游戏的，Switch 不靠它 |

安装位置：`/Applications/Ryujinx.app`；配置与数据：`~/Library/Application Support/Ryujinx/`。

## 二、还差的两件必须你自己提供（我不能也不该代劳）

1. **key 文件**：`prod.keys` 与 `title.keys`，从**你自己的 Switch** 导出。
   放到：`~/Library/Application Support/Ryujinx/system/`
2. **固件**：同样从你自己的机器导出，得到一个含 `*.nca` 的文件夹，首次启动后在
   Ryujinx 菜单里 `Tools → Install Firmware → Install a firmware from a folder / ZIP`。
3. **游戏**：用你自己卡带/自购数字版转出的文件。

没有第 1、2 两项，模拟器能开但什么游戏都起不来——这是硬前提，不是设置问题。
我不提供、也不指引任何 key/ROM 的获取渠道。

## 三、首次使用四步

1. 打开 `Ryujinx.app`（已清隔离，双击即可，不会再被拦）。
2. 放好 key → `Tools → Install Firmware` 装固件。
3. `Options → Settings → General → Game Directories` 添加你放游戏的文件夹。
4. 回主界面双击游戏开跑。

## 四、M1 Pro 上建议的设置（默认值已经够用，这两条才是关键）

| 设置 | 建议 | 为什么 |
|---|---|---|
| Graphics Backend | **Vulkan**（默认已是） | Metal 后端在这版里还不成熟；Vulkan 走 MoltenVK 最稳 |
| Resolution Scale | **1x（原生）** | M1 Pro 不是游戏显卡；2x 只适合小体量游戏 |
| Docked Mode | 卡就关掉 | 关掉=按掌机 720p 跑，负载明显低 |
| Texture Recompression | 关（默认关） | 省内存，32GB 要和机队共用 |
| Memory Manager Mode | 默认 `HostMappedUnsafe` | 更快；若崩溃改成 `HostMapped` |

## 五、老主机（NSW 以外）用 RetroArch

`/Applications/RetroArch.app` → 首次启动 → `Online Updater → Core Downloader` → 下你要的核：
- SNES：`snes9x`
- GBA/GBC：`mgba`
- N64：`mupen64plus_next`
- PS1：`beetle_psx_hw`
- FC/NES：`fceumm`

ROM 自己准备，本机不预置任何受版权保护的内容。

## 六、玩之前让机队让路（同 v1，仍然必要）

```bash
Tools/fleet/ceo_mode.sh start --with-ai   # 停主控脉+看门狗+本地模型，让出 3-4GB
Tools/fleet/ceo_mode.sh stop              # 玩完恢复（先过 deploy_gate）
Tools/fleet/ceo_mode.sh status            # 看现在谁在跑
```

## 七、合规与边界（必须知道）

1. 模拟器本身在很多地区合法，但**内容来源必须是你自己的机器与卡带**。
2. 任天堂对 Switch 模拟器的态度是持续法律施压（原 Ryujinx 已因此下架，现用社区分支 Ryubing）。
   自己玩没事，**不要分发、不要商用、不要对外演示**。
3. 不要为了跑某个游戏去网上抓"整合包"——那类包常带恶意程序和别人的 key，风险大于收益。

## 八、何时候该停下来

1. 某游戏在 Ryujinx 里崩溃两次以上 → 换 `HostMapped` 内存模式再试一次；还崩就放下，别陷进配置黑洞。
2. 帧数低到不能玩 → 先关 Docked、再降 Resolution Scale；M1 Pro 的上限就在这里，不是设置没调对。
3. 玩完发现 `ceo_mode.sh status` 显示脉冲 stopped → 立刻 `stop` 拉回来，别让它空跑一夜。