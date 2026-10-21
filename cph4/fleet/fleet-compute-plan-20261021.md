# FLEET-COMPUTE-PLAN 2026-10-21 — 机队全到位后的本地算力分配规划（接管准备件）

> 性质=规划准备件（非新法条·不动任何现有车道定岗）。令源：CEO 2026-10-21「机队全部到位后怎么分配本地算力，规划一下」。
> 输入事实：fleet-nodes.json 名册 + resource-chain §二/§9.1 + hardware/ 七档（BOM 终审/MARKET-WATCH v1 10-20/P-CARD-WORKFORCE v1）+ 千问席 2026-10-21 模型能力调研。
> 生效前提=机队通道恢复（tailscale/NATS/FleetLink）+ 各线复产口令。在此之前本文只作接管预案。

## 一、家底（实测名册口径，纠偏两处旧读）

| 机 | CPU/RAM | GPU | 现车道 | 关键约束 |
|---|---|---|---|---|
| bm-a DASHENG | 32C/94G | 12G（夜窗备援） | hq-central-night-gpu | 白天=CEO 用机零排单；INT8 768P 装不下（OOM 实测） |
| bm-b BIGMONEY | 3800X 16T/24G | **3070 8G**（非纯 CPU 机） | cpu-sound | 8G 禁正片；曾 53.5h 停摆史→长跑必带守护；P104 #1 草图官候选位（第二槽若有） |
| bm-c FLUXGROUP | 3950X 32T/24G | 3070 16G | gpu-production | 全集团正片 i2v/KF 唯一产线=最大瓶颈；白天让路 CEO |
| bm-d（到位后） | 2×E5-2695v2 24C48T/**无 AVX2**/256G DDR3 | **V100 16G×3**（#1 已购，#2/#3 采购中）+X9DR3-F 仅剩 1 短卡位 | bmd-brain-backtest | Volta 架构：无 bf16/无 FA2/FP8 需特化 kernel；GPTQ-int4 可用（compute 7.0）；AVX2 缺失→CPU 推理弱，活全压 GPU+多核 |

## 二、分配总纲：按"卡的代际"定岗，不按"机器的情面"

核心原则四条：
1. **Ampere 位（bm-c/bm-b）=生产正片**：30 系有 INT8/量化 kernel 生态，ComfyUI Dynamic VRAM+FP8/Q4 权重跑得顺（16G 实测 60s 出 5s 片级别）。
2. **Volta 位（bm-d V100×3）=大脑+并行批量**，不碰 ComfyUI 新链路（缺 FA2/FP8 生态，SDXL 可用 fp16，视频 14B 单卡 fp16 装不下——不要拿 V100 烧片，那是 bm-c 的活）。
3. **无 AVX2= bm-d 禁任 llama.cpp/CPU 兜底**，35B-on-CPU 那类方案永久排除在 bm-d 外。
4. **草图与正片分层**：秒级预览/占位下放到 P104/4b 小卡位，正片卡时只给过了审的镜头——bm-c 的 16G 是全集团最贵的秒表。

## 三、分工矩阵（接管执行态）

### LLM 思考面（替代旧 codely 云端角色）
| 层 | 载体 | 用途 |
|---|---|---|
| 主脑 | **千问席（本地+云端）** | 主 AGENT 判断/审读/架构/深判——不再自建，这就是 CEO 定的执行体 |
| 产线小脑 | bm-d V100×3 vLLM tensor-parallel：**Qwen 14B-int4-gptq 双实例（卡1+卡2）+ 卡3 跑 32B-int4 或 SDXL fp16** | 批量分类/草拟/十一面初筛/日 digest/POOL 分诊——零云端 |
| 轻量本地 | bm-a 夜窗 :8090 35B-A3B **改配比**（attn+共享专家驻 12G，长尾 experts 留 RAM；禁 n-cpu-moe=999 全 CPU 配置——那是 5min/398token 的病根） | 夜窗簿记/审核板生成 |
| 微模型 | bm-b 4b :11434（保留） | 格式化/校验类死活 |

### 视频/图像生产（41 曲 MV+短剧漫剧+游戏资产）
| 位 | 载体 | 内容 |
|---|---|---|
| 草稿层 | **P104 草图官**（SD1.5/LCM 占位·Wan-5B-Q4 秒级预览，队列全网投单，同机集中） | 游戏占位资产/meme 分镜底/KF 风格初稿——过审前不占正片卡 |
| 海选层 | bm-b 3070 8G：480P trial 批 | 效率律先行（批量前先低清验证）——**激活 bm-b 被闲置的 GPU**，只派 480P 以下 |
| 正片层 | bm-c 3070 16G：Krea2 KF INT8 + Wan INT8 768P i2v + LatentSync/Animate 过闸件 | 唯一正片产线；波≤8；18-21 点后满载、白天让路 |
| 重烧层 | bm-c 夜窗专属队列（v511 家族类像素手术/补镜） | 按 DIRECTOR 单执行 |

### 回测/量化
| 位 | 载体 | 内容 |
|---|---|---|
| 大脑厂 | **bm-d 24C48T/256G**（正典 O-20261015-1055 已定 W 波主机） | 全市场日线回测/波链主轮/RAM>8G 分片 bm-d-first |
| 快档 | bm-c 副道（CPU 空窗） | 轻回测补片 |
| 数据 | bm-a akshare 拉数+审计探针（Tools/quant-*） | 零 GPU |

### 音频/人口/媒体其余
bm-b：TTS/Music3/whisperX+allin1 双锚批（POOL-0018/0019 恢复后首认领）+B 站运营线本地版；BigLife 日报/簿记、BigStream 装配 CPU 段=bm-a 夜窗与 bm-d 富余核。

## 四、机队到位后的启动序列（接管首夜 SOP）
1. tailscale 三机+bm-d 上线 → fleet-reality 实测基线。
2. NATS hub + FleetLink :8790 全机复听 → fleet-live-status -Server 三行全绿。
3. OrderSentinel/FleetDispatcher/IdleWatch/DeliveryWatch 四机械件先回（零 token）。
4. bm-d：bmd-bootstrap → JOIN-REPORT → 名册 enabled=true → vLLM 双实例起 + MARKET-WATCH 三条前置确认过的散热/供电验收。
5. 复产口令逐线：BigMoney W 链（bm-d）→ 双锚批（bm-b）→ MV 签发-烧制链（bm-c）。
6. POOL 22 卡对账补货，L2 判断由千问席 8 班承载（会话式，不建旧 codely 无头班）。

## 五、风险与止损（预注册）
- bm-d V100 #2/#3 未到=大脑面只起单实例，回测主轮候满配——W 链先在 bm-b 过渡（正典已有借池律）。
- bm-c 积压>1 天 → 触发 MARKET-WATCH #2080Ti-22G 蹲价闸（¥1800-2700·片长位）；**禁**为省卡时砍 QC 闸。
- P104 岗位判负线沿用预注册：H3 5s 片 P104≤30min 不过闸→转纯 SD1.5 占位夜批（¥100 不亏）。
- 35B-A3B 重配比后仍 <20 字/秒 → bm-a 夜窗 LLM 面降级为"仅簿记"，判断全走千问席（本地/云按必要闸）。
- 全部停摆位（84 任务）恢复只按第四节序列点名，其余维持停用——禁批量 Enable 复发旧账。

---
*千问席 · 2026-10-21 · 接管规划件（生效前无执法面·与 resource-chain §9.1 现行定岗零冲突，bm-d 满配后建议委员会走一次合册修订）*
