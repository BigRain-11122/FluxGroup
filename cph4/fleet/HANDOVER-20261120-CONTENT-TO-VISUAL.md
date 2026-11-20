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
1. `git -C K:\Fluxgroup\FluxGroup pull origin main` —— 本移交书与清单已随仓下发。
2. 起自己的自驱：注册/启动 station_agent（或 FleetLink `:8790`），让 `lanes/bm-c.json` 从 OFFLINE 变回有活。
3. 拉内容资产：从公司生产力机 `\\100.110.185.62\C$\Users\sjs20\Desktop\FluxGroup\media\<目录>` → `K:\Fluxgroup\FluxGroup\media\<目录>`（需一次性 SMB 凭据；**全量 54.7 GB**，建议先 `BigStream`+`MV`+`drama-tools`+`faces` 四件，`MUSIC` 按需）。
4. 在传家宝注册自驱任务：`media\BigStream\src\os\register_loop_task.ps1`（脚本纯 ASCII，路径无关）。
5. 写回执 `cph4/fleet/queue-receipts/HANDOVER-content-bm-c.json`（含各目录落地文件数/字节数、任务状态、首轮心跳时间）。

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

## 七、物理件（零催办，等 CEO 有空）

1. 传家宝 SMB 凭据或远程桌面一次 —— 否则 54.7 GB 无法过网。
2. `recon/` 14.7 GB 的内容/游戏分拣（含 17.8 万文件），分拣后各自归属。
