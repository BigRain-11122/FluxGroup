# 产线 v2 + 前置资产规格 + 机队调度方案 + 调度实战（2026-11-10）

## 一、产线 v2（AI-CONTENT-PIPELINE-v2·commit b076ce6a5）

九段流水线（每段一闸·不过禁下段）：D0 立意→D1 分镜选角→D2 KF 批→D3 i2v 批→D4 take 入库→D5 装配→D6 交付闸→D7 导演盲审→D8 CEO 终审→D9 迭代。全周期 MV ≤5 天 / 短剧 ≤3 天 / 漫剧 ≤2 天。

八组规则：
1. 角色一致性（ID 锚+脸 dHash 三节点闸·换脸级=一票否决）
2. 表演运镜（八维法唯一正身·口型镜判负·标杆锚=克制型表演）
3. 装配交付（变更集单一正典·分块自复用对变更集判·回归对比必跑·闸参数显式传）
4. 云端烧制（H3=写实人脸唯一通道·无脸意境镜任意通道·PS5.1 GB2312 编码坑）
5. 审核升格（审链不审对·验性质不只验存在·敌对盲审席·CEO 发现=闸失效复盘）
6. 短剧/漫剧增补（复用 MV 链·配音字幕四段闸·声画对齐交付门）
7. 时间红线
8. 前提工程四件（take-registry·一键出片·回归对比·脸 dHash 闸）

## 二、前置资产规格 v1（AI-PREPRO-ASSET-SPEC-v1·commit 9331dff68）

22 项就绪清单全过才准烧视频：A 类角色（设定卡→LoRA→定妆帧→参考板）+ B 类场景（设定卡→场景 KF→一致性板）+ C 类道具（考据三查→KF→连续性板）+ D 类音声（原曲→音色 LoRA→TTS 样板）+ E 类提示词（风格常量→表演卡→运镜卡→光句卡→lint 三名单）+ F 类技术（take-registry→装配配置→闸参数→脏集）。

五席专家群审（导演/表演/灯光/考据/调色）≥7/10 → 导演签「前置就绪令」→ 机队开烧。

## 三、机队调度方案 v1（AI-FLEET-DISPATCH-v1·commit 267cb1a05）

原子卡拆解（A2.1 写卡→A2.2 生 18 备料→A2.3 标注→A2.4 训练→A2.5 验证→A2.6 盲评，每步=一张机队卡带机器/耗时/交付/验收）。依赖 DAG 关键路径 ≈ 半天-一天。机队矩阵：bm-a/bm-c GPU 并行训 LoRA+KF，bm-b GPU 训音色，bm-m CPU 写卡+盲评，云端 H3 为正片主力。主控协议：night_plan 铺卡→lane_agent 认领→closer 2min 验→血缘链记 registry 改上游标脏下游。

## 四、调度实战测试（2026-11-10 CEO 令「先测试一波这个流程」）

- **调度令三路并发**：git commit（12a12f6c3）+ NATS 总线广播（406B）+ 救生分支推 origin（lz-d05-dispatch·88a2def2f）。8 张原子卡（LoRA gate + 3 场景卡 + 2 道具卡 + 风格常量 + 盲评）。
- **LoRA gate 自动化工具**（Tools/lora_gate_eval.py）：生 4 张试烧图+dHash 对锚+verdict JSON，全机器判零人眼。
- **本机在跑**：her_mv0002 LoRA gate（第三跑·修完模型名/后缀/LoRA 拷贝后重跑·后台）。
- **主控在收**：收到调度令后应铺卡进 PRODUCTION-QUEUE 供各机认领（机队合作测试验证中）。

## 五、ComfyUI Krea2 模型名对照表（三连 400 实锚）

| 确认名 | 类型 | 位置 |
|---|---|---|
| krea2_turbo_int8_convrot.safetensors | DiT/UNET | models/diffusion_models/ |
| qwen3vl_4b_fp8_scaled.safetensors | 文本编码器（krea2）| models/text_encoders/（**不是 bf16**） |
| qwen_image_vae.safetensors | VAE | models/vae/ |
| jman_v1_rank32.safetensors | 男主 LoRA | models/loras/（已拷入） |
| her_mv0002_rank32.safetensors | 龙卷风女主 LoRA | models/loras/（已拷入，447MB） |

坑：① LoRA 文件名必须带 `.safetensors` 后缀；② LoRA 训练输出目录 ≠ ComfyUI 读取目录，须拷贝/链接入 models/loras/；③ replace 工具的并行编辑顶掉（文件 changed 提示后必须 re-read 再改）。

## 六、GitHub 产线调研（CEO 令「好好学习领会」·初步）

四大头部项目（合计 6 万+ star）：
1. waoowaoo (14.8k★) — 工业级全流程 AI 影视生产平台（Hollywood-standard workflows），Elastic License 2.0
2. Toonflow-app (21.3k★) — 短剧/漫剧制作工具（剧本→分镜→角色/场景资产管理→图像→视频），无限画布+AI Agent
3. ViMax (12.9k★) — Agentic Video Generation（导演/编剧/制片/生成 all-in-one），HKUDS 出品
4. NarratoAI (11.8k★) — AI 大模型一键解说+剪辑

学习结论初步：我们的产线 v2 已覆盖 Toonflow 的核心概念（资产管理+分镜+工序化）和 ViMax 的角色分工（导演/编剧/制片分离），但缺少 waoowaoo 的「Hollywood-standard」级别的工序控制面板（可视化工作流编辑器）。深入对比待完成。
