# bm-c 自驱力架构 v1（2026-11-16 定稿）

## 一、机器角色宣言（CEO 令 2026-11-15）

**bm-c = BigStream 媒体公司视觉算力基座**：MV/视频/i2v/出图/切片专职机 + 主控（bm-m）调度节点 + 媒体资源库自建产线。7x24 排满运转。

CEO 授权（2026-11-15）：任何任务占用不合理（占显存/内存但不算活），bm-c 可在启动时直接关闭并执行正确任务。

## 二、GPU/CPU 双车道排产矩阵（7x24）

| 车道 | 任务族 | 优先级 |
|---|---|---|
| GPU | 主控派卡（lanes 随到随跑） | 最高 |
| GPU | LoRA 角色库自训批（sd-scripts venv） | 资源库主线 |
| GPU | KF/i2v 产线波（三档位矩阵：DreamShaperXL 速度档 / Qwen-2512 2步质量档 8.8 / Qwen-2.1 备档） | 产线 |
| CPU | 音色库语料批（vb_worker：分片→人声分离→whisperX/faster-whisper ASR） | 资源库主线 |
| CPU | 主控 CPU 卡 | 随派 |
| 守卫 | ComfyGuard every:3m + StationAgent 巡查 every:1h + 主机永不睡眠（屏幕 3min 灭） | 常设 |

## 三、媒体资源库建设路线（CEO 定优先级：下载 → 微调 → 自训；版权原创）

### 3.1 LoRA 角色库（自训=版权原创的正道）
- 训练器：**sd-scripts 最新版 + 独立 venv（torch 2.11.0+cu130 CUDA=True，TRAIN-IMPORT-OK 已验）** 位于 .tools\sd-scripts(-venv)
- 数据集：media\mv-album-001-jay\mv0002-cast-work\lora-dataset\（8_her/8_him 各 32 张，多窗协作扩产中）
- 数据律：caption 二次清洗背景词（framed/against/standing 尾句剔除）；kohya 结构；触发词 jman/ljher 正典
- 训练配方：sdxl_train_network.py + accelerate；首训试验=下一 GPU 批

### 3.2 音色库（voice-library）
- 分工：GPT-SoVITS 训练在 bm-b；**bm-c 腿=语料获取+人声分离+ASR 标注**
- 工具链：bilibili-api(下载) + audio-separator/UVR(人声分离,待装) + **whisperX 25.3k★（词级时间戳，BSD）** + faster-whisper-small（K 盘已落+VB_ASR）
- 卡点：jobs_<voice>.txt BV 清单未到（bm-b 挂账）——催办中
- 质量律：语料 ≥8 分钟可训、≥20 分钟达标；32kHz 不降 16k

### 3.3 道具库（asset-lib）
- 现水位：props20/scenes12/motions15/transitions10/characters96/faces96/styles3/typography4
- 扩库走产出席提案通道（有消费方才提新单元——意义门）；asset_gen 幂等批驱动

## 四、GitHub 最强轮收编矩阵（收获机制五门：契合/反重复/许可/健康/成本）

### 已收编（2026-11-15/16）
| 轮子 | 星数/许可 | 用途 | 形态 |
|---|---|---|---|
| ComfyUI v0.45.0 | 官方 | 生成引擎核心 | 主引擎 |
| sd-scripts (kohya) | ~12k★ | LoRA 训练 | venv+clone |
| MoneyPrinterTurbo | **143,743★ MIT** | 全自动短视频全链参照引擎（文案→TTS→素材→剪辑→成片） | .tools\media-stack |
| whisperX | 25,324★ BSD-2 | 词级时间戳 ASR（音色库标注） | pip |
| BiRefNet | 4,408★ MIT | 最强抠图（透明件质量升级） | .tools\media-stack |
| visual-skills | 684★ CC-BY | AI 电影导演技能包（agent 形态直接可收） | .tools\media-stack |
| VideoClaw | 1,906★ MIT | AI 全自动视频生成员工（模式参照） | .tools\media-stack |
| LivePortrait/LatentSync/PuLID | 19.5k/6.3k★ | 表演/唇形/角色一致性 | 已在役 |

### 拒收（许可证红线）
- video2x 22.7k★ AGPL-3.0——AGPL 禁入（收获机制法条）
- OpenChatCut 3.1k★ AGPL-3.0——同上
- waoowaoo 14.9k★ NOASSERTION——克隆参照前必须细查 LICENSE 文件，商用面暂缓

### 待评估
- waoowaoo（工业级 AI 影视平台——LICENSE 细查后定收编深度）
- cinecode 2.5k★ MIT（代码化短片）

## 五、排产规则
1. 主控派卡最高优先（lanes 唯一执行面）
2. GPU 空闲窗口→资源库自训/产线波自动顶上（禁闲置>10min 律）
3. 下载通道：modelscope/阿里云（国内 CDN 满速）> gh-proxy（串行低并发）> 直连（仅小件）
4. 收编纪律：一切 build 先搜 GitHub 高星（CEO 常设令）；AGPL 拒收；NOASSERTION 先查 LICENSE
5. 自驱批次一律 pythonw 隐藏链后台+日志落盘（U060 零窗口律）

## 六、链路
- 主控：NATS 心跳+lanes 派卡（StationAgent 巡查 every:1h 已在役）
- 本档案：cph4/fleet/bmc-self-drive/ARCHITECTURE-v1.md（node/bm-c 链上正身）


## 七、闭环与上链节拍（2026-11-22 · CEO 令「本地闭环/信息同步/及时上链/主控知情」）

> 本节修正第六节：「主控 = NATS 心跳 + lanes 派卡」在 2026-11 已不成立——
> **全队 NATS hub 无监听，心跳走不通；主控实际按 git 里本机自写的回执判活。**

| 层 | 载体 | 谁写 | 判据 |
|---|---|---|---|
| 在线 | cph4/fleet/queue-receipts/_last_lane_bm-c.json | 本机 | 主控 30 分钟内新鲜 = online |
| 产出 | cph4/fleet/queue-receipts/autodrive-hb-bm-c.json | 本机 | 内容 
ode+	s，超 6h = EXECUTOR-DEAD |
| 派卡 | cph4/fleet/lanes/bm-c.json | **主控**（本机只读） | jobs 非空 = 有待执行卡 |
| 结果 | 回执 + lane.result.bm-c（NATS，当前不通） | 本机 | 以 git 回执为准 |

**执行体只有一个：Bmc-ChainPublish（每 5 分钟）**，顺序固定为
刷新回执 → 提交证据件（单文件 ≤2MB）→ fetch/合并远端 → 推送 → 领一张卡。
其余席位（路由/监督/守卫/巡查）只出判断或重启批，不写 git、不改主控的笔。

三条铁律（违反会重演 2026-11-22 的 927 提交断供）：

1. queue-receipts/ 是忽略目录，回执必须 git add -f 才能到主控——节点侧自证靠它；
2. 主控的笔（PRODUCTION-QUEUE / PRODUCTION-BACKLOG / lanes/ / dispatcher/MASTER-STATE）
   冲突一律取远端，节点绝不覆盖；
3. 同一张车道卡跑过就记进 production/chain-lane-done.json，主控未清卡前不重跑
   （旧账：同一门禁卡被重跑 40+ 轮，每轮推一份同结论回执）。
