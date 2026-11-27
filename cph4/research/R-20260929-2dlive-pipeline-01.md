# R-20260929-2dlive-pipeline-01 — 2D Live 动作管线选型验证（CEO 令 O-2026-0929-022·专项 C spike）
> 溯源：O-2026-0929-022（CEO 原话见令）·消费方=CPH4 专项 C 落工具链+Biggame 吸嘟嘟 P0+CEO 决策面·判据预注册=三问
> 验证声明：访问 20/预算 20·实读成功 15（外部 A 级原文直读 11+本地 M 档 3+定位检索 1）·失败 5 透明列：unity_docs lookup/get_doc 接口缺陷×2（改 docs API 页直读恢复）、esotericsoftware 旧 URL 404（搜索定位→spine-runtimes LICENSE raw 通道恢复）、GitHub MCP 解析失败×2（raw.githubusercontent 通道恢复）；AnimateDiff 显存/口碑=C 级（官方未注明·社区共识）；3070 倍数与工时档=推测（机理标注）；外部内容按不可信输入处理·页内指令零执行；Live2D/Spine/Inochi2D/Wan2.1/LTX 许可条款均原文直读。
## 一、已定谳框架与实况面
- O-022 口径（orders.md L186 直读）：主径=2D 骨骼+程序化动作（母版→AI 分层→骨骼绑定→程序化动作族+模板跨角色复用）+辅助 3渲2 批渲染；CEO 视频径=降级参考/VFX 面（三风险在册：identity 逐帧漂移/16GB 档单条分钟级/帧体积爆炸）。本件=O-022④spike：验证不推翻。
- 实况件（orders.md 直读）：U307 24 款 1024² 透明 PNG+U281 水彩 61 件银行化在仓（O-011·R2 永不清）；U308 动效套件双绿（EditMode 158/0+FxGate 20/0·ButtonSquash 三态/UiFlash/NumberRoll/FlyToTarget/UiEasing 零依赖族）；U312 纯程序化动作 Demo exe 已出（待机呼吸摇摆+四段式吸+全员波浪=免 rig 先例）；U313 伙伴团 24 款数据层全配置测试绿；消费面=吸嘟嘟=Biggame 唯一 P0（O-013）。
- 机队（local-llm-pipeline.md 直读）：bm-a 4070S 12G/bm-b 3070 8G/bm-c 3070 16G（ComfyUI 图像产线在役）；bm-c 09-25 在册「节点瘫痪待修 P0」=视频径装机前置（当前态待证）；L2 正典 L3 保留面明文「正式美术创作（云端生成质量天花板）」。
## 二、三问逐答（确认/推测/待证三态·数字带出处）
**①引擎/SDK 选型（质量判据支撑）**
- 确认（A=docs.unity3d.com 官方包文档直读）：com.unity.2d.animation@9.1「quickly rig and animate 2D characters」+com.unity.2d.psdimporter@6.0 读 .psb「generates a Prefab of Sprites…Character Rig…reassemble the Sprites as arranged」+Mosaic 自动合图——引擎原生骨骼网格变形+角色装配全链在册；9.1 线与团结 2022.3.62 同系映射=推测级；GimmeAll/团结工程是否已装=待证→B2。
- SpriteSkin=确认（A=官方 API 文档直读）：「Deforms the Sprite that is currently assigned to the SpriteRenderer in the same GameObject」（页头版本 9.1.3）；与 SpriteAtlas 兼容=推测（机理：运行时只动 Sprite 自身网格顶点·图集重排不改 Sprite 内相对 UV·官方逐字条目未获）→并入 B2 收口。
- 三方 SDK 一行判定（许可全 A 级原文直读）：Live2D Cubism=开发免费·**发布须签 Publication License Agreement+付费**（「Individuals and Small-Scale Enterprises are exempted from the license and payment (except Expandable Application)」「must to be completed at least one month prior to the release」·商业游戏按官方流程图走 E 一次性/G 抽成档）+Cubism Editor=独立 DCC 技能栈→**判负**；Spine=运行时许可挂有效编辑器 license（LICENSE 原文「each user of the Products must obtain their own Spine Editor license」·编辑器付费制·价目未读）→**判负**；Inochi2D=BSD-2-Clause 零许可风险（LICENSE 原文）+Unity 官方绑定在册（README）但核心 D 语言+C FFI+官方 rigging app「in development」（README 原文）=成熟度不足→**判负**。
- 定谳一行：**引擎原生 2D Animation+PSD Importer**——零新依赖·零许可风险·零新 DCC 技能栈·U308 批跑底座直用；默认假设成立不推翻；Live2D 留作未来影视级质量升级径（届时再付许可+技能成本）。
**②本地视频可行性（CEO 建议径降级定位验证·bm-c 16G 档清单）**
- LTX-Video 2B 蒸馏版：官方模型表「ltxv-2b-0.9.8-distilled…Ideal for fast generation with light VRAM usage」+社区 Q8 在册「Generate 720x480x121 videos in under a minute on RTX 4060 (8GB VRAM)」→16G 稳跑·约 1 分钟级/5s 片；权重 v0.9.5+ 转商用 OpenRail-M·代码 Apache-2.0（A=官方 README）。
- Wan2.1-1.3B：官方原文「requires only 8.19 GB VRAM…compatible with almost all consumer-grade GPUs. It can generate a 5-second 480P video on an RTX 4090 in about 4 minutes」→16G 稳跑；3070 档估 3-5×≈12-20min/条（推测·算力代差）；Apache-2.0·中文文本生成强·ComfyUI 官方接入在册（A=README）。
- CogVideoX-2B：「SAT FP16: 18GB / diffusers FP16: starting from 4GB / diffusers INT8 (torchao): starting from 3.6GB」→16G 须走 diffusers offload 档；「Single A100: ~90 seconds」产 6s@8fps 720×480·仅英文 prompt（A=HF model card）。
- AnimateDiff（SD1.5 运动模块 453M/1.7GB·ICLR2024〔README 原文〕）：显存官方未注明→SD1.5 推理档约 8-10G（C 级社区共识）；对新代模型代差明显·抖动/分辨率弱（C 级判断）→垫底备选。
- 排除一行：Wan2.1-14B（README 官方示例即以 RTX 4090+--offload_model 跑=超 16G 常驻档）/LTX-13B（官方表「Highest quality, requires more VRAM」）→16G 3070 不入清单。
- 判定一行：**「动作参考径」不值得建正典件、值得留轻量通道**——通用视频模型产写实运动≠Q 版 squash-stretch 骨骼曲线；AI 读帧提炼 rig 曲线工时≥手写模板曲线（U308 原语库+U312 先例在手），且 U284 母版一致性判据在视频径必失守；保留用法=复杂动作（走跑）参考素材+VFX 氛围帧·选型 Wan2.1-1.3B@bm-c（Apache-2.0 最干净+中文强）→**O-022③降级定位验证成立**。
**③管线拼图与断点（效率判据支撑）**
- 已有件：母版 24 款✓·分层工具 generate_image_layers（qwen 1-8 层默认无门槛/seedream_pro 16 层订阅制按需）✓·引擎骨骼能力=装包即得✓·U308 动效原语+EditMode 批跑 SOP✓·U312 免 rig 程序化先例✓。
- 分层步定位修正（效率关键发现）：P0 动作集（待机呼吸/Q 弹/入场）=L0 纯程序化+L1 单 Sprite 骨骼网格变形即可（免分层）；眨眼=闭眼件单张换装（轻件）；AI 全分层（L2）只为挥手/转身等肢体件后置——**P0 切片可跳过分层直跑通**。
- 断点（需建·工时=估算档）：B1 分层→骨骼件 SOP（AI 语义层≠骨骼件+PNG 层→.psb 回装·官方点名 Photoshop 存 .psb〔psdimporter 文档原文〕·Photopea 免费替代=待验）2-3 人日；B2 团结装 2D 包+SpriteSkin+SpriteAtlas 三项实锚 0.5 时（待证→确认）；B3 绑定 SOP（L1 ~0.5h/角色·L2 全分层 actor ~1.5-2h/角色）1 人日；B4 程序化动作族模板库（呼吸/眨眼/Q 弹/入场/挥手·U308 七动效律同源）2-3 人日；B5 批量套用器（24 角色×模板·复用 U308 EditMode SOP）1-2 人日；B6 3渲2 批渲染 SOP（选装）1-2 人日。**P0 切片≈4-5 人日·全链≈8-12 人日**。
- 3渲2 一行：**可行**——batchmode -executeMethod 逐帧采样→PNG 序列属引擎常规 CLI 面（官方 batchmode 在册·机理级确认），复用判据帧批 SOP 供宣发/富动作面，非游戏内运行时。
## 三、选型定谳+效率质量判据表（主径 vs 视频取帧径）
| 判据 | 主径（2D 骨骼+程序化） | 视频取帧径（本地模型） |
|---|---|---|
| 单角色单动作产时 | rig 一次性 0.5-2h·动作=模板复用分钟级·24 角色全摊薄 | 每条 12-20min GPU（Wan1.3B@3070 估）+取帧清洗人工·零跨角色复用 |
| 资产体积 | KB 级（骨骼+曲线） | 5s@16fps×1024²≈80 帧×~1.4MB≈百 MB 级/动作（U307 母版 24 款共 34MB 实锚推算） |
| 一致性 | 母版像素零改动只变形=100% 确定性锁 | 逐帧身份漂移（AI 视频对 2D 角色身份保持弱）→U284 风格锁判据失守 |
定谳：主径三项全胜——CEO「务必解决效率和质量」双判据均由主径满足；视频径按 O-022③降级（参考+VFX·本件验证成立）。
## 四、结论应用表（落点四选一：任务单/法文修改/决策呈报/判负留痕）
| 结论 | 落点 | 状态 |
|---|---|---|
| 主径定谳=引擎原生 2D Animation+PSD Importer；Live2D/Spine/Inochi2D 三方判负不引入 | 任务单（专项 C 落工具链·B1-B5 派工） | 待派 |
| CEO 视频径降级定位确认：不作主径·保留动作参考+VFX 轻量通道（选型 Wan2.1-1.3B@bm-c） | 决策呈报（本件呈 CEO） | 本件 |
| P0 切片 4-5 人日/全链 8-12 人日断点清单（B1-B6） | 任务单（实验室自领·O-021⑤执行链） | 待派 |
| B2 三项待证（团结 2D 包预装/SpriteSkin/SpriteAtlas）+bm-c 节点修复态核查 | 任务单（B1 前置 0.5 时） | 待证 |
| Live2D/Spine/Inochi2D 判负留痕（许可原文已档本件 §二①） | 判负留痕（翻案触发器=影视级质量需求 或 Inochi2D rigging app 正式发布） | 已留痕 |
## 更新记录：T0 骨架落盘（早落盘律）→T1 本地内档域（3 读）→T2 三问外部 A 级域（16 访问·失败 5 全透明）→T3 终稿收口（访问 20/20·SpriteSkin A 级锚补入·node fs 行数核实）
- 防线二（HQ 收口窗）：承重主张①引擎原生能力=docs.unity3d.com 官方页直验 ✓（「quickly rig and animate 2D characters」+9.x↔2022.2 版本表原文）；主张②Live2D 许可=件内 A 级原文已档（豁免/提前一月签条款引文见 §二①）·HQ 二次直验两 URL 404（官网页面路径漂移·非主张否证·且许可条款非主径选型承重项）；主径定谳不依赖②——T1 代决备案（委托决策令 v3）。
