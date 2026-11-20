# 移交书 · 内容线（自媒体/漫剧/短剧/MV）→ 传家宝（2026-11-20）

> 令源：CEO 2026-11-20「你把本机自媒体相关 AI 漫剧短剧相关等一切东西移交给传家宝机器电脑，以后都归他了，你只搞硅基城市和游戏公司相关」
>
> 一句话：**从本令起，公司生产力机（DASHENG）的产出面只剩「硅基城市 + 游戏公司」两块；自媒体/AI 漫剧/短剧/短视频/MV/账号运营全线归传家宝（FLUXGROUP）。**

---

## 一、归属划分（生效即事实）

| 面 | 机器 | 机器名 | 范围 |
|---|---|---|---|
| 内容线 | 100.123.74.104 · `K:\Fluxgroup\FluxGroup` | 传家宝 | 自媒体运营（B站/抖音/视频号）、养号与评论、AI 漫剧、短剧与切片、短视频、MV（关键帧/i2v/剪辑/字幕/装配）、选角与 LoRA |
| 城市 + 游戏 | 100.110.185.62 · `C:\Users\sjs20\Desktop\FluxGroup` | 公司生产力机 | 硅基城市（FluxVerse / City3D / BigLife / BigHouse）、游戏公司（Biggame 全系 + 车机游戏 + 提审/构建/图标/截图）、BigMoney 支撑件 |

冲突裁决：凡是「内容成品」与「城市/游戏素材」交叉的件（例如角色脸库、音乐、封面），**生产归传家宝，城市/游戏只按需读取引用，不在此机器上新开内容产线**。

---

## 二、本机现役内容资产清单（2026-11-20 22:4x 实测，非引用旧账）

全部位于 `C:\Users\sjs20\Desktop\FluxGroup\media\`，**均被 .gitignore 排除（`.gitignore:4 media/BigStream/`）**，即：git 里没有，只在本机磁盘。

| 目录 | 文件数 | 体积 | 内容 | 处置 |
|---|---:|---:|---|---|
| `BigStream/` | 39,387 | 14,095 MB | 内容线 OS 全套（src/os 循环·闸·探针·单据）+ orders + output + state | 移交传家宝；本机冻结为冷归档 |
| `faces/` | 69,200 | 26,283 MB | 选角人像库（MV/漫剧用） | 移交传家宝 |
| `drama-tools/` | 36,567 | 8,249 MB | 漫剧工具与素材 | 移交传家宝 |
| `MUSIC/` | 125 | 3,266 MB | 音源（MV 配歌正身） | 移交传家宝（版权红线照旧） |
| `MV/` | 1,955 | 2,186 MB | MV 产物与中间件 | 移交传家宝 |
| `lora/` | 1 | 219 MB | 角色 LoRA 权重 | 移交传家宝 |
| `mv-test/` `mv-album-001-jay/` `kf-ab/` `meme-daily-v1/` `drama-pilot-in/` `drama-pilot-out/` `covers/` | 157 | 186 MB | 内容线零散件 | 移交传家宝 |
| `recon/` | 177,946 | 14,712 MB | 竞品拉片与侦察料（内容+游戏混装） | **暂不动**，待按内容/游戏分拣后各自归属 |

内容线合计约 **54.7 GB / 315,000+ 文件**。

> 口径修正（2026-11-21 实测）：其中 `BigStream\data\assets\models`（CosyVoice/whisper 等权重 ≈7 GB）与 `drama-tools\repos\index-tts\.venv`（torch CUDA ≈8 GB）是**环境**不是资产，重装即可，**不进移交包**。真正要搬的资产 = **≈33 GB**（P1≈0.3 + P2≈0.65 + P3≈2.2 + P4≈3.2 + faces≈26）。

## 三、本机现役内容任务（实测）

| 计划任务 | 状态 | 说明 |
|---|---|---|
| `BigStream-OSLoop` | Ready（本令执行前每 5 分钟） | 起 `media\BigStream\src\os\iteration_loop.ps1`，拉起无头 codely 轮 |
| `BigStream-AIHotWatchdog` | Disabled | 早已停用 |
| `bm-a-BiliAutoReply` / `bm-a-BiliDM` / `bm-a-BiliOutreach` / `bm-a-BiliQC` / `bm-a-BiliSlowDel` | Disabled ×5 | B站养号族，全部停用 |
| `HQ-Patrol-BigStream` | Disabled | 巡查停用 |

**零产出现场（重要）**：`media\BigStream\logs\iteration-loop\` 最后一轮真实产出是 **2026-10-24 06:41**；此后至 2026-11-20，心跳每条都是 `cloud-cap defer (live=2)`——**这条线在本机已经四周没有产出，只是在空转打卡**。

处置：本令下把 `BigStream-OSLoop` 置 **Disabled**（冻结，不删任务、不删数据），内容线在本机的生产权终止。

## 四、传家宝接管步骤（它自己执行，别人不用代跑）

前置（传家宝本机，2026-11-20 实测全缺）：
- `:8790` FleetLink **不通**（tailscale 显示 active，但服务未起）
- `:5985` WinRM **不通**、`:22` SSH **不通**
- `:445` SMB **通**，但无凭据（`net view` 系统错误 5）
- 车道文件 `cph4/fleet/lanes/bm-c.json` = `OFFLINE`，最近回执停在 2026-11-12

接管五步：
1. `git clone git@github.com:BigRain-11122/Bigmedia.git`（或已有仓 `git pull`）—— **内容线代码/文档/订单全套在独立仓 `Bigmedia`**（3258 文件 / 208 MB；本机 2026-11-21 实测 `HEAD...origin/main` = 0/0，已全部推送）。这一段**不需要从本机搬任何字节**。
2. 起自己的自驱：注册/启动 station_agent（或 FleetLink `:8790`），让 `lanes/bm-c.json` 从 OFFLINE 变回有活。
3. 取资产包：本机已封好**可校验档案**（`D:\handover-content-20261120`，6.3 GB / 6,877 文件），同目录 `MANIFEST.json` 带逐包 sha256：

   | 包 | 内容 | 体积 | 文件数 |
   |---|---|---:|---:|
   | `content-p1-20261120.zip` | LoRA 权重 + 关键小件（mv-test/kf-ab/mv-album-001-jay/meme） | 300 MB | 154 |
   | `content-p2-20261120.zip` | 内容线状态（src/orders/docs/research/tests/tools/data） | 650 MB | 4,342 |
   | `content-p3-20261120.zip` | 成品（MV/drama-pilot/covers） | 2.2 GB | 1,970 |
   | `content-p4-20261120.zip` | 音源 + 漫剧工具（MUSIC/drama-tools，已剔 venv） | 3.2 GB | 411 |
   | P5 人脸语料 | `media\faces` 69,200 文件 / 26 GB | 按需现打 | — |

   P5 现场生成（约 30-60 分钟）：`BUILD-PAYLOAD.ps1 -Group P5`；不预打是**不留半成品**（今晚一次打包曾到 5.97 GB 被中止，已删）。
   落地校验：`INSTALL-ON-FLUXGROUP.ps1` 逐包核 sha256 再展开到 `K:\Fluxgroup\FluxGroup`，并写回执。
4. 在传家宝注册自驱任务：`media\BigStream\src\os\register_loop_task.ps1`（脚本纯 ASCII，路径无关）。
5. 写回执 `cph4/fleet/queue-receipts/HANDOVER-content-bm-c.json`（含各目录落地文件数/字节数、任务状态、首轮心跳时间）。

**通道实测（2026-11-21 00:0x–00:2x，我逐条实测，不是推断）**

| 通道 | 结果 |
|---|---|
| tailnet 在线状态 | `Online=True`、`Active=True`、`TaildropTarget=1` |
| Taildrop 吞吐 | 经 DERP(sfo) 中继：**5 MB 349 秒未完成、85.6 MB 8.7 分钟未完成 ⇒ <14 KB/s**；33 GB 需 ≈27 天 → 不可用 |
| SMB 445 / RPC 135 / RDP 3389 | 端口开；本机当前凭据被拒（`net use` = 用户名或密码无效），无其它可用凭据 |
| SSH | 22 端口不通；`tailscale ssh` 落到 TCP 22 直拨同样超时 |
| FleetLink 8790 | 未监听 |
| GitHub | **可用**（代码 208 MB 已全部推送） |

结论与处置（自己搞定，不等 CEO）：
- **代码与文档面 = 已彻底移交**：走 GitHub，不依赖任何本机直连。
- **资产面 = 已封包+哈希，就位待运**：4 包 6.3 GB 已生成并逐个列目录验过完整性；26 GB 人脸语料一条命令现打。
- **物理瓶颈不在凭据，而在这条链路本身**（<14 KB/s）。解除方式只有两种：传家宝恢复自身通道（它自己的自驱职责），或换直连/物理介质。此结论已写进 §七，不再把「等 CEO 给凭据」当成前置。

> 未完成上述步骤前，内容线处于「本机已冻结、传家宝未接」的空窗态 —— 这是本令下的已知代价，不是故障，也不回滚到本机生产。

## 五、本机此后不再做的事（越界即违令）

1. 不生成关键帧、不做图生视频、不剪 MV、不装配漫剧/短剧/短视频。
2. 不写漫剧/短剧剧本、不做内容选题与拉片。
3. 不碰账号侧：B站/抖音/视频号养号、评论、私信、发布准备（一律归传家宝）。
4. 不为此线建卡、不派卡、不代跑、不审片（除非 CEO 直接点名）。

## 六、本机继续做的事

1. 硅基城市：FluxVerse / City3D 装配与灯光、BigLife 居民产线、BigHouse 安家、城市数据与可视化。
2. 游戏公司：Biggame 全系、车机游戏、提审四件套、构建打包、图标截图。
3. BigMoney 的只读支撑件（账本、面板读取），不接内容产出。

## 七、物理件（已降级，不再阻塞执行）

1. **33 GB 资产过网**：链路实测 <14 KB/s，靠凭据解决不了。解除=传家宝恢复自身通道（其自驱职责），或换直连/物理盘。档案已就位，届时一条命令即可。
2. `recon/` 14.7 GB 的内容/游戏分拣（含 17.8 万文件），分拣后各自归属。
3. `media\faces` 26 GB 按需打包（`BUILD-PAYLOAD.ps1 -Group P5`）—— 平时不占额外空间。

---

## 八、执行口径：各司其职 · 本地闭环 · 主控与机队知情 · 互相赋能

> CEO 2026-11-20 重申（原话「也就是现在开始坚决执行各司其职，本地闭环，主控和机队知情，互相赋能」）。
> 本节不是新法——四条在现行正典里都已成立，这里只做**执法登记与今日的落点**，避免又立一套。

| 口径 | 正典（已有，勿重立） | 本令下的落点 |
|---|---|---|
| 各司其职 | `cph4/decision-chain.md` §6 月度使命复盘；`cph4/fleet/AUTONOMY-V3.md`；`STATIONS.json` 各席 allowed/forbidden | 本机停止一切内容生产（任务已 Disabled、PRODUCTS 支援位已摘）；内容线只有传家宝一个生产位 |
| 本地闭环 | `cph4/fleet/LOCAL-CLOSURE-v1.md`（CEO 2026-11-11「每个机器都要本地闭环」）；`AUTONOMY-V3.md` §二 本地模型优先 | 谁的活谁跑完：产物 + 回执 + 台账都落在本机自己的分片；不代跑别家、不把活推回主控等命令 |
| 主控与机队知情 | `MASTER-DUTIES-v3.json`（主控只做六件事）；`lanes/<node>.json` + heartbeat + `docs/orders.md` 令簿 | 本令已落 `orders.md` 并推到 origin；主控与四台机下一次 pull 即知情；机队只读，不需要挨个通知 |
| 互相赋能 | `AUTONOMY-CONFIG.json`「优先本地算力互相赋能」；`decision-chain §6` 赋能对账（给谁什么/得谁什么） | 交接一律走 `HO-` 单与产物引用：传家宝缺资产要 bm-a 的字节，bm-a 缺画面要传家宝的产物，都不许替对方干活 |

**执法判据（可机器验）**
1. 本机出现任何 `mv-cut` / `mv-gate` / 漫剧装配 / 关键帧的新卡或新产物 = 违令。
2. 传家宝的活若被本机代跑（回执落到 `rt/delivery/` 却属内容类）= 违令，且破坏「本地闭环」台账口径。
3. 主控若仍向本机派内容卡 = 派单侧未知情，按 `PRODUCTS.json` 现状（本机已无内容支援位）应判 CARD-DEFECT。
4. 本机与传家宝之间只能通过 `HO-` 单 / 产物路径 / 本移交书互相引用，不得共享未登记的中间状态。

