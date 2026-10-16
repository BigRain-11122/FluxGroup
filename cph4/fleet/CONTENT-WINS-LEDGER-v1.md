# CONTENT-WINS-LEDGER v1 — 自媒体线惊喜录（好的积累·CEO 令）

> CEO 令 2026-10-16 21:3x：「把好的，就是一次性可以产出的一些好的，这些有惊喜的地方，也要做一个积累，好的坏的都要去做。」
> 与坑账（EXPERIENCE-LEDGER 判例册/各线 LEDGER）对称：坏账记「病→闸」，好账记「**条件→配方**」。坏账防复发，好账=可复用配方库。
> 入册律：每片 DIRECTOR-GATE 收口时导演席标注「一次过/超预期」项→入册（无惊喜=零条也如实，禁硬凑）；每条必须带**可直接拷贝复用的配方**+实锚指针；跨线复用时注明引用。

| # | 惊喜（一次过/超预期） | 条件（怎么做到的） | 可复用配方 | 实锚 |
|---|---|---|---|---|
| W-1 | **V5 装配器实跑一次全绿**：final_len 234.25 精确命中、九点 xfade offset 全落词锚、单链断言全过（零返工） | 六次 DRYRUN 干跑把坑全踩在干跑里（缺重烧件用旧件顶替验数学）；断言律（逐点 offset==窗起点断言+终长对账） | 大装配器标配 DRYRUN 模式：`DRYRUN=1` 验数学→坑清零→`DRYRUN=0` 一次过；断言三件=窗表守恒/offset 逐点/final=Σ窗对账（正身=build_full_mv_v5.py·坑律在全局记忆 2026-10-16 21:07 条） | V5-PROXY-PREFLIGHT-20261016.md · commit 7b1c4eb |
| W-2 | **字层 PTS 三层修法一次过**：3/3 多模态验字（V4 全灭病根当窗治愈） | 把单帧 PNG 的 fade PTS 病根链完整推演后再动手（三层病根链拆到第三层才写正解） | 字层叠加正解=scale 对齐分辨率+`setpts=PTS+<窗起>/TB` 平移+fade st 用主片时刻；配套断言=窗内抽帧多模态验字（CHK-T1） | EXPERIENCE-LEDGER v1 · 30s-reel-v1/make_text_layers.py |
| W-3 | **phase1 试烧六镜 winners 全过审**（B01 s9911 背 C 形塌/INT1-INT5 全项命中·零整镜判负） | 三段式表演提示词全嵌+jman 0.8 骨相锚+INT4 480P 试镜先行（12 trials 才升 768P） | 试烧两段制：480P trials×N 种子→导演审定选 winners→768P 正片只烧胜者（省算力+一次过率） | orders.md 18:0x 行 · V5-REBURN-SPEC |
| W-4 | **KF-P/KF-N 现实锚版一次过帧级 QC**（8.5/9.0 vs v1/v2 两连 2/10 判负） | J-M17 立闸：2026 现实场景必带现实参照系硬锚（发布会=超密 LED 巨幕+蒙布揭幕车；工厂=白环氧地坪+机械臂+AGV） | 现实参照系硬锚法：新场景帧先写参照系锚再写主体（判例 J-M17/J-M18 检查单） | meme-daily-v1/LEDGER.md J-M17 |
| W-5 | **grade v5 参数链一次到位**：盲评 9/10「死黑与琥珀对比极具胶转磁神韵」 | 量测先行：原版 MV 24 参照帧实测（avgRGB/饱和/对比）vs 我方旧帧逐项对表，参数从数据派生非拍脑袋 | 调色量测对标法：先实测参照帧三参数（RGB 均值/饱和/对比度）→差值定向推参（暖推 rs/rh+sat+contrast+黑位）→盲评验收 | EXECUTION-FIX-LEDGER-20261011.md §三 |
| W-6 | **克制档 finishing CEO 终裁过**（「做旧要克制…其他都可以了」） | D 档判负后收半：罩染减半/黑位只去数字黑/饱和 .97/暗角 PI5/颗粒 alls6 | finishing 克制档参数链正身=build_30s_v4.py fin 链（DELIVERY-NOTE-v44）·后续直接引用勿再调参 | 30s-reel-v1/DELIVERY-NOTE-v44.md |
| W-7 | **变速修复一次过**：minterpolate 48fps 插值链盲评 8/10「丝滑无顿挫」 | 病根先定谳（非真掉帧=慢放拖长每帧的视觉卡顿）再上修法 | 慢放镜正法=`minterpolate=fps=48:mi_mode=mci`→setpts 变速→fps=24 三段链 | CEO-FEEDBACK-fullmv-fix-20261011.md |
| W-8 | **安明远音色定谳后旁白零返工** | 音色三候选实听对比后定谳清亮自然非播音腔 | 旁白音色正身=qwen:anmingyuan_v3.1·speed 1.2（禁播报腔=AI 感源·禁方言=CEO 令） | meme-daily-v1 LEDGER J-M7 |
| W-9 | **星晴 38 镜歌词意象全意象化 0 直译**（J-23 立闸当窗全过） | 逐句歌词→镜头→三档判定表（直译=打回/意象化=过/升华=佳）四方联审 | 意象转化表=剧本 vN 必携件；具象名词=情绪载体（LYRIC-IMAGERY-LAW） | EXPERIENCE-LEDGER J-23 |
| W-10 | **反向测试一次过线**：M 系原创脸多模态评审报不出任何明星名 | 防撞脸四锚点工艺（眉/眼距/鼻翼/唇形改 ≥2 项+不碰签名造型） | 反向测试入合规自证链：候选脸喂多模态问「像谁」→报名即迭代→留档=举证链 | ai-star-research/RESEARCH-20260909.md §四 |
| W-11 | **jman LoRA 训成 12/12 验证格全过**（4 场景×4 强度零废） | musubi-tuner 12GB 配方+数据集工艺判例（多模态拼板三轮 QC+逐格 bbox） | 12G 卡 LoRA 配方正身=jman-lora-training-spec-v1.md（fp8 成对+blocks_to_swap 26+rank32） | outbound/krea2/jman-lora-training-spec-v1.md |
| W-12 | **Krea2 参数化词表价值实证**：模糊自然语言版 vs 词表版门检差（更少油蜡皮·光按词表落位） | prompt_lexicon 七类专业词+三名单 lint+可检测性原则 | 「词不能被摄影机/测光表/秒表检测到就改写」——新产线直接 import 词表勿裸写 | prompt-writing-spec-v1/PROMPT-SPEC.md |

—— bm-a · 2026-10-16 首版 12 条 · 随片收口滚动追加（入册律见档头）
