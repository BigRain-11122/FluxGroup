# 机队配置与系统说明书（FLEET-SPEC）

> 生成时间：2026-11-12T14:11:39｜生成器：`Tools/fleet/fleet_doc.py`｜**本文件是生成物，不要手改正文**
> 数据源（改这里，不改正文）：`STATIONS.json` · `Tools/fleet-nodes.json` · `OS-MATRIX-v1.json` · `CPU-PLAN-v1.json` · `AGENT-CAPACITY-v1.json` · `MODEL-COMPUTE.json` · `ASSET-VAULT.json`
> 改完跑 `python3 Tools/fleet/fleet_doc.py --write`；只查不改跑 `--check`（有漂移 rc=1）。
> **综合评分 81.6 / 100**（验证 24.1/25｜规则 20.0/20｜工作流 20.0/25｜机队 10.5/15｜环境 2.0/10｜文档 5.0/5；评分时间 2026-11-12T14:11:07）；外部阻塞 4 项

## 一、速查表

| 工位 | 机器 | 系统 | CPU | 内存 | GPU | 角色 | 状态 |
|---|---|---|---|---|---|---|---|
| delivery | 公司生产力机 | Windows | Ryzen 9950X 16C/32T | 94G | RTX 4070 SUPER | 游戏产线主业（CEO 2026-11 | network_ok_not_registered |
| visual | 传家宝 | Windows | Ryzen 3950X 16C/32T | 24G | RTX 3070 (modded 16G) | 全视频主责（CEO 2026-11- | blocked_no_comfyui |
| audio | 小钢炮 | Windows | Ryzen 3800X 8C/16T | 24G | RTX 3070 | 声音工位：全视频线的配音/混音/BG | offline |
| brain | 算力大脑 | 待定（未装机/未入网）（未核实） | 2× Xeon E5-2695v2 24C/48T | 256G | 3× Tesla V100 | 机队本地模型能力中心 + BigMo | not_installed |
| control | MacBook | macOS | Apple M1 Pro 10C/10T | 32G | M1 Pro 集成 | 主控台（2026-11-11 收窄） | ready |

合计：**74 核 / 138 线程 / 430G 内存 / 84G 显存**（5 台）

## 二、逐机配置

### 1) 公司生产力机（工位 delivery / bm-a）

| 项 | 值 |
|---|---|
| 机器名 | 公司生产力机 |
| 系统 | Windows（已核实） |
| 核实依据 | tailscale status 显示 windows 100.110.185.62；机名 DASHENG |
| 解释器 / shell | python（或 py -3） / powershell |
| 路径约定 | windows（C:\） |
| 文件锁 | msvcrt |
| 调度器 | 任务计划程序（FluxGroup-Nats* 等） |
| CPU | Ryzen 9950X 16C/32T |
| 内存 | 94 GB |
| GPU | RTX 4070 SUPER（12G 显存） |
| 磁盘 | C:（系统+代码+.git）；D:（重资产与产物，余 3379G） |
| 工作目录 | C:/Users/sjs20/Desktop/FluxGroup |
| 网络 | tailnet 100.110.185.62（端口 8790） |
| 角色 | 游戏产线主业（CEO 2026-11-11）：Biggame 与车机游戏的全部提审/图标/截图/构建/适配/准入材料都在这里；不再接视频与对外物料。 |
| 班次 | 工作日 09:00-19:00 只接轻 CPU（day_ok）；19:00-09:00 与周末重活 |
| 允许的活 | 游戏提审全套(材料/图标/截图/清单)、构建打包、车机适配、3D 场景装配、城市数据与资产、事件接入 |
| 禁区 | 视频剪辑与字幕、画面生成、声音 |
| 磁盘水位 | 低于 20 GB 停手 |
| 模型座位 | qwen3.5:8b 级（Q4）（8G，ctx 8192，并发 2） |
| 模型额度 | 600 次/天，180 模型分钟/天，实测 22 tok/s |
| 已装软件 | python（Windows 无 python3，实测 rc=9009）、ffmpeg、Unity/团结引擎、pillow、git |
| 唤醒任务 | BigStream-OSLoop、BigLife-OSLoop、BigDomain-OSLoop、FluxVerseTick、MiniGameEngineTick、Bigmoney-IterationLoop、HQ-ProductionClaim、HQ-StationDrive |
| 当前状态 | network_ok_not_registered |

**可承担的 CPU 活（夜窗并行上限）**

| 活类 | 单任务线程 | 单任务内存 GB | 并行 |
|---|---|---|---|
| ASR 后处理/字幕对齐/时间轴 | 4 | 4.0 | 3 |
| 批处理/打包/去重/索引 | 2 | 1.0 | 6 |
| 引擎编译/出包/源码门禁 | 8 | 8.0 | 1 |
| 给 GPU 喂数据（图片预处理/切图/命名） | 2 | 2.0 | 6 |
| 规则校验（哈希/命名/台账/字段） | 1 | 0.5 | 13 |
| 转码/压制/字幕烧录 | 6 | 4.0 | 2 |

岗位书：`cph4/fleet/stations/delivery/CHARTER.md`

### 2) 传家宝（工位 visual / bm-c）

| 项 | 值 |
|---|---|
| 机器名 | 传家宝 |
| 系统 | Windows（已核实） |
| 核实依据 | tailscale status 显示 windows 100.123.74.104 |
| 解释器 / shell | python / powershell |
| 路径约定 | windows（C:\ / K:\） |
| 文件锁 | msvcrt |
| 调度器 | 任务计划程序 |
| CPU | Ryzen 3950X 16C/32T |
| 内存 | 24 GB |
| GPU | RTX 3070 (modded 16G)（16G 显存） |
| 磁盘 | K:（仓库+产物，余 1217G）；C:（执行器） |
| 工作目录 | K:/Fluxgroup/FluxGroup |
| 网络 | tailnet 100.123.74.104（端口 8790） |
| 角色 | 全视频主责（CEO 2026-11-11）：MV/漫剧/短剧/短视频的画面+剪辑+字幕+装配；声音仍由声音工位做。 |
| 班次 | 全天；GPU 串行，同一时刻只跑 1 张 |
| 允许的活 | 关键帧海选/正档、图生视频、口型、角色 LoRA、视觉一致性机检、剪辑、字幕、成片装配 |
| 禁区 | 声音制作、文本批量生成、打包构建 |
| 磁盘水位 | 低于 20 GB 停手 |
| 模型座位 | qwen3.5:8b 级（Q4）（8G，ctx 8192，并发 1） |
| 模型额度 | 400 次/天，120 模型分钟/天，实测 24 tok/s |
| 已装软件 | python（Windows 无 python3，实测 rc=9009）、ComfyUI(8188)、ffmpeg、git |
| 唤醒任务 | Bigmoney-IterationLoop、Bigmoney-SaturationEngine、Bigmoney-ResidentDispatcher、Bigmoney-Autofill、Bigmoney-PoolWorker、MiniGameEngineTick、MiniGameComfyDraftTick、MiniGameAuditTick、MiniGameGateTick、MiniGameRadarTick、MiniGameRadarDeepTick、MiniGameSiliconWatchTick、HQ-ProductionClaim、HQ-StationDrive |
| 当前状态 | blocked_no_comfyui |

**可承担的 CPU 活（夜窗并行上限）**

| 活类 | 单任务线程 | 单任务内存 GB | 并行 |
|---|---|---|---|
| ASR 后处理/字幕对齐/时间轴 | 4 | 4.0 | 2 |
| 批处理/打包/去重/索引 | 2 | 1.0 | 6 |
| 引擎编译/出包/源码门禁 | 8 | 8.0 | 1 |
| 给 GPU 喂数据（图片预处理/切图/命名） | 2 | 2.0 | 5 |
| 规则校验（哈希/命名/台账/字段） | 1 | 0.5 | 13 |
| 转码/压制/字幕烧录 | 6 | 4.0 | 2 |
| 配音后处理/响度/重采样 | 2 | 2.0 | 5 |

岗位书：`cph4/fleet/stations/visual/CHARTER.md`

### 3) 小钢炮（工位 audio / bm-b）

| 项 | 值 |
|---|---|
| 机器名 | 小钢炮 |
| 系统 | Windows（已核实） |
| 核实依据 | tailscale status 显示 windows 100.82.175.0（当前 offline，最后在线 16h 前） |
| 解释器 / shell | python / powershell |
| 路径约定 | windows（C:\） |
| 文件锁 | msvcrt |
| 调度器 | 任务计划程序 |
| CPU | Ryzen 3800X 8C/16T |
| 内存 | 24 GB |
| GPU | RTX 3070（8G 显存） |
| 磁盘 | C:（系统+仓库+素材）；E:（未见用途） |
| 工作目录 | C:/Fluxgroup/FluxGroup |
| 网络 | tailnet 100.82.175.0（端口 8790） |
| 角色 | 声音工位：全视频线的配音/混音/BGM/音色；不做画面、不做视频装配。 |
| 班次 | 全天低负载 |
| 允许的活 | 配音、TTS、配乐、混音、480p animatic |
| 禁区 | 768p 出片、8G 以上显存需求、大模型常驻 |
| 磁盘水位 | 低于 20 GB 停手 |
| 模型座位 | qwen3.5:4b-8b 档（6G，ctx 8192，并发 1） |
| 模型额度 | 300 次/天，90 模型分钟/天，实测 28 tok/s |
| 已装软件 | python（Windows 无 python3，实测 rc=9009）、ffmpeg、TTS 引擎（index-tts venv 缺失待补） |
| 唤醒任务 | Bigmoney-IterationLoop、HQ-ProductionClaim |
| 当前状态 | offline |

**可承担的 CPU 活（夜窗并行上限）**

| 活类 | 单任务线程 | 单任务内存 GB | 并行 |
|---|---|---|---|
| ASR 后处理/字幕对齐/时间轴 | 4 | 4.0 | 1 |
| 批处理/打包/去重/索引 | 2 | 1.0 | 3 |
| 规则校验（哈希/命名/台账/字段） | 1 | 0.5 | 6 |
| 配音后处理/响度/重采样 | 2 | 2.0 | 3 |

岗位书：`cph4/fleet/stations/audio/CHARTER.md`

### 4) 算力大脑（工位 brain / bm-d）

| 项 | 值 |
|---|---|
| 机器名 | 算力大脑 |
| 系统 | 待定（未装机/未入网）（**未核实**） |
| 核实依据 | 无：tailnet 无此节点；fleet-compute-plan-20261021 只记硬件（2×E5-2695v2/256G/3×V100），未写 OS |
| 解释器 / shell | 待定 / 待定 |
| 路径约定 | 待定 |
| 文件锁 | 待定 |
| 调度器 | 待定 |
| CPU | 2× Xeon E5-2695v2 24C/48T（**无 AVX2**） |
| 内存 | 256 GB |
| GPU | 3× Tesla V100（48G 显存，3× P104 8G） |
| 磁盘 | SSD（系统+模型+工作区） |
| 工作目录 | C:/Fluxgroup/FluxGroup |
| 网络 | tailnet PENDING-TAILNET（端口 8790） |
| 角色 | 机队本地模型能力中心 + BigMoney 量化回测 + 夜间批处理（CEO 2026-11-11）：绝大多数本地推理与 agent 自动化算力落在它；机队自己能做的先做，做不了的立刻由它赋能。 |
| 班次 | 入网后全天 |
| 允许的活 | 回测、深判、代码评审、35B/27B 大脑服务、批量转码 |
| 禁区 | 未入网前一律不派 |
| 磁盘水位 | 低于 20 GB 停手 |
| 模型座位 | 32B 级（FP16/Q4 分卡）（32G，ctx 16384，并发 4） |
| 模型额度 | 3000 次/天，720 模型分钟/天，实测 18 tok/s |
| 已装软件 | 待装（系统/驱动/llama.cpp/LiteLLM） |
| 当前状态 | not_installed |

**可承担的 CPU 活（夜窗并行上限）**

| 活类 | 单任务线程 | 单任务内存 GB | 并行 |
|---|---|---|---|
| 回测/数据处理 | 8 | 32.0 | 2 |
| 批处理/打包/去重/索引 | 2 | 1.0 | 10 |
| 规则校验（哈希/命名/台账/字段） | 1 | 0.5 | 20 |
| 转码/压制/字幕烧录 | 12 | 4.0 | 1 |

岗位书：`cph4/fleet/stations/brain/CHARTER.md`

### 5) MacBook（工位 control / bm-m）

| 项 | 值 |
|---|---|
| 机器名 | MacBook |
| 系统 | macOS（已核实） |
| 核实依据 | tailscale status 显示 macOS 100.75.133.10；本机 sysctl machdep.cpu.brand_string=Apple M1 Pro |
| 解释器 / shell | python3 / bash/zsh |
| 路径约定 | posix |
| 文件锁 | fcntl |
| 调度器 | launchd（用户级 LaunchAgent，当前 44 项全部暂停） |
| CPU | Apple M1 Pro 10C/10T |
| 内存 | 32 GB |
| GPU | M1 Pro 集成 |
| 磁盘 | /（系统+仓库+轻产物，余 210G） |
| 工作目录 | /Users/junsheng.sun/FluxGroup |
| 网络 | tailnet 100.75.133.10（端口 8790） |
| 角色 | 主控台（2026-11-11 收窄）：文本、判据、账本、对外材料、索引、调度；不再做视频剪辑与字幕。 |
| 班次 | 全天（CEO 在用电脑时降载） |
| 允许的活 | 文本与判读、质量闸与验收、账本与一屏、对外材料与索引、合规判定、账号评论草稿、跨机调度 |
| 禁区 | GPU 生成、视频剪辑与字幕、媒体素材落盘、代发/登录任何平台账号 |
| 磁盘水位 | 低于 15 GB 停手 |
| 模型座位 | qwen3.5:4b-mlx（0G，ctx 8192，并发 2） |
| 模型额度 | 300 次/天，90 模型分钟/天，实测 40 tok/s |
| 已装软件 | python3、ffmpeg、Ollama(4B/9B/8B/2B)、git |
| 当前状态 | ready |

**可承担的 CPU 活（夜窗并行上限）**

| 活类 | 单任务线程 | 单任务内存 GB | 并行 |
|---|---|---|---|
| 批处理/打包/去重/索引 | 2 | 1.0 | 4 |
| 规则校验（哈希/命名/台账/字段） | 1 | 0.5 | 8 |

岗位书：`cph4/fleet/stations/control/CHARTER.md`

## 三、跨机约定（命令写错必失败的地方）

| # | 铁律 | 说明 |
|---|---|---|
| OS-1 | 解释器名随 OS 变 | macos=python3；windows=python 或 py -3。卡里写 python3 的属于 mac 卡，派到 Windows 必 rc=9009（2026-11-03 实测两次）。 |
| OS-2 | 路径分隔与盘符 | Windows 命令含 C:\ 或盘符=Windows 卡；Mac 路径以 / 开头，外接盘在 /Volumes（已退役，不再使用移动盘）。 |
| OS-3 | 文件锁实现不同 | POSIX 用 fcntl，Windows 必须 msvcrt；直接 import fcntl 的脚本在 Windows 导入即崩（master_pulse 就是这种，只能在 Mac 跑）。 |
| OS-4 | 调度器不同 | Mac=launchd（launchctl bootstrap/bootout/kickstart），Windows=任务计划程序（schtasks / Get-ScheduledTask）。两套命令互不通用。 |
| OS-5 | 编码与换行 | 老 Windows 文件可能是 GBK；写前先探字节再决定编码，写后回读校验。换行 CRLF/LF 混写会触发 .gitattributes 的 eol=lf 冲突（本仓踩过）。 |
| OS-6 | 系统专属命令不算通用 | sysctl / getloadavg / launchctl / os.fork 只在 POSIX；schtasks / Get-CimInstance / powershell 只在 Windows。失真判据一律双实现或显式拒绝。 |
| OS-7 | 未验证 OS 不得排卡 | os=unverified 的机器不得作为任何卡的落点（除非卡本身就是装机/验机卡）。 |

队列与存储：分片 `cph4/fleet/rt/<工位>/`（一机一写者，主控只读 origin 快照）；素材字节留产出机，素材库落点 `—`（status=EMPTY；重建目标 传家宝:K:/FluxAssets）。

## 四、模型端点阶梯

| 端点 | order | url | 角色 |
|---|---|---|---|
| 本机（每台机自己） | 0 | http://127.0.0.1:11434 | local-loop |
| 算力大脑 | 1 | **空（未装备）** | primary |
| MacBook 主控台 | 2 | http://100.75.133.10:11434 | light-fallback |

规则：闭环优先：能在本机做完的绝不出机器；本机小模型做不好的（长剧本/语感/审稿）上升算力大脑；主控只在两头都不可用时兜底。

## 五、AI 运行环境对齐

| 工位 | 环境档 | 判定 | python | ollama | ffmpeg | 探针年龄 | 缺口 |
|---|---|---|---|---|---|---|---|
| control | darwin-arm64 | PASS | 3.13.18 | 0.40.16 | 7.1 | 0.2h | — |
| delivery | windows-cuda | GAP | 3.14.10 | 0.40.13 | 9.0.2-full_build-www.gyan.dev | 1.9h | python 3.14.10 不满足 <3.13；环境变量 OLLAMA_MODELS 未设置（模板 <盘符>:\ollama\models）（等 5 项） |
| visual | — | 未探测 | — | — | — | — | 没有 env/visual.json：该机还没跑过探针 |
| audio | — | 未探测 | — | — | — | — | 没有 env/audio.json：该机还没跑过探针 |
| brain | — | 未定档 | — | — | — | — | 该机没有对应环境档位（OS 待定或未入网）：先定系统再定环境 |

标准=`cph4/fleet/AI-ENV-SPEC-v1.json`；事实=`cph4/fleet/env/<工位>.json`（由 `env_probe.py` 各机自采）；超过 24h 未更新判 STALE。1 台达标 / 4 台待办。

标准档：`darwin-arm64`（主控，MLX）/ `windows-cuda`（三台生产机）/ `linux-cuda`（大脑若装 Ubuntu）。各机每日跑 `python3 Tools/fleet/env_probe.py --write`，产物随 git 同步；探针超过 24h 判 STALE。

## 六、缺口与待决（按此清单推进，不要靠记忆）

1. brain：系统未核实（待定（未装机/未入网））——入网时二选一：Ubuntu（CUDA/驱动省事，工具多为 py）或 Windows（与另外三台一致，可复用 .ps1）。选前不得按任何一方排卡。
2. 算力大脑：端点未装备（未入网：tailnet IP 未分配。装备完成后在此填 http://<brain-tailnet>:11434，order 保持 1。）
3. 素材库为空（已按 CEO 令清空），重建落点 K:/FluxAssets

## 七、配置一致性校验

六源一致，无漂移。

## 八、变更日志（人工区，重新生成会保留）

<!-- MANUAL:CHANGELOG -->
- 2026-11-11 首版：由 fleet_doc.py 依据六份配置生成，替代此前散落在多份 md 的机器说明。
<!-- /MANUAL -->
