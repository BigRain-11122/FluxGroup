# 可爱女人-KF-PACK-A-v1-DRAFT（A 批 28 帧·bm-c 烧制包草稿 · 承 可爱女人-shots-v2.py v2.6）

> **状态=已签发（准烧 A 批 28 帧 · 2026-10-20 12:5x）**：签发链闭环=lint 机核 ✓（§五.① 实跑）→ PROMPT-EXPERT-GATE-v1 十一面审 ✓（`PROMPT-GATE-可爱女人-KF-PACK-A-v1-L2.md`·独立评审席 2026-10-18·PASS15/FIX13/REJECT0）→ 导演席合并复检+签发 ✓（`PROMPT-GATE-可爱女人-KF-PACK-A-v1-SIGN.md`·8 条 FIX 全落位·复检 lint 30/30 零命中·词数 105-190）→ 可派单烧制（QC §12 v1.2）。**机读正身=可爱女人-shots-v2.py v2.6 优先于本件**。
> **外观项勘正（承 L2 verdict 移交④）**：PLANE 逐字挂 **16 常量挂 + 2 行内**（KN20b 对偶再生成态 / KN29 按 F-29 回锚 HER_PLANE）；city_bowl 天际线尾句受益帧=**10**（KN07/10/11/12/13/22a/22b/23/25/29）。
> 用法：本包=**组装层**。每帧 KF 主体句已在机读正身 **可爱女人-shots-v2.py `NEW` 元组索引 5**（英文·py 内 `kf()` 组装器出）——bm-c 烧制脚本按**八块模板正序**组装（FIDELITY-SPEC §一：景别构图→灯光→**主体块最长**→环境→表情（脸镜）→次级动态→Pose/动作→风格尾段），**禁增删主体句语义**。提示词三件套（词源/判例/判据）随帧附。
> **零转录律**：一切以 shots-v2.py 为准（SHOTLIST-v2.md=衍生物）；出入记录见 §六。

- **ID 块引用律**：男主 ID 块=py `HIM` 常量（`jman, ` + prompt_lexicon.py `ID_M_2001_BONE` 逐字同源·PROMPT-SPEC §三 ID 槽位常量族·v2.3 服装师令 2000 台式流行衣橱：水洗牛仔外套+图案T+宽松直筒+银链+皮绳手环）；**发型=每镜变量**（底子/发型分离律——本包复审发现 2 镜缺失见 FIX-2/3）；jman LoRA=LoraLoaderModelOnly（jman_v1_rank32=文件名 `jman_v1_640_rank32_final.safetensors`·**strength 0.6**〔剧本 v3 硬约束定谳〕·判决二可7 先网格 0.6-0.8；=FIDELITY-SPEC Character-LoRA Image-Only 范式·防文本互染）。**女主帧=选角案定 ID 块**（KN_HER·候选 A 默认·候定脸）——**B 批帧本包禁烧**；背影/剪影/手部/物件/空景镜免挂 ID 块全量（星晴白名单先例：物件镜免挂）。
- **反韩骨相锚 v2**：正脸/侧脸近景镜必挂（背影剪影免）——A 批命中镜=KN03（cu）/KN09（hs），经 `HIM` 常量 `ID_M_2001_BONE` 结构性挂载 ✓（heavy-lidded monolid/thick lower lip/blunt rounded jaw=骨相锚 v2 词族·KF1v2 s9015 实证同源）；CONCEPT 名单词全消失法（lint 实跑零命中）。
- **年代锚**=QC-MASTER-CHECKLIST §8/§9 + 剧本 v3 §二年代锚清单**正向锚全量入**：天台系=铁皮水塔/晾衣绳/parapet·城灯系=aged hand-painted signboards+old neon shop fronts+sodium 点状（零 LED 大屏·禁品只做 QC 不入提示词）·纸机系=notebook paper 手折素白/奶油纸红翼尖·探照光柱=2000 合法物（CEO 歌词意象令判例）·**天际线零 101=夜城镜第一高危**（帧审三面查·正向锚补位见 FIX-7）·随身听/磁带=白名单合法位不强制（本 30 镜无该道具位）。
- **官方收尾**（py `kf()` 尾段正身·2000 族）：`Shot on <lens>, 2000 telecine grade, warm skin tones, milky lifted blacks, blooming practical highlights, slight color bleed, shot on 35mm Kodak Vision 500T 5279, visible grain, halation on practical lights, as a film still from a 2000 Taiwanese music video`（GRADE_2000=tw2001 块本地覆写 2001→2000·v2.2 残余⑤·胶片 5279=2000 当班夜戏型号·QC §17）。
- **零否定词**：lint 三名单预检 **30/30 CLEAN**（2026-10-18 实跑·证据=§五.①）——禁品清单只做 QC 不入提示词；烧制侧复跑即闸。
- 工艺档（FIDELITY-SPEC §二/§四随工单挂）：权重 3-5 条封顶+8+1 两段采样（refine denoise 0.30·kl_optimal）+主体块字数>风格块硬检。

## 一、共享块（每帧组装时引用）

1. **男主 ID 块（HIM 常量·逐字）**：`jman, a 20-year-old Taiwanese student with heavy-lidded monolid eyes, a thick lower lip, softly rounded cheeks, a flat round nose tip, a blunt rounded jaw and natural unretouched skin with visible pores, in a washed denim jacket over a white graphic tee, loose straight jeans, a thin silver chain and a braided leather bracelet, white canvas shoes`
2. **女主 ID 块（KN_HER·B 批专用·定版依赖）**：`a 20-year-old Taiwanese girl of the year 2000, a softly sweet oval face with full rounded cheeks, large bright dark double-lidded eyes with gentle innocent warmth, a small straight nose, soft medium-full rosy lips, long straight black hair with a solid blunt full fringe, in a striped knit top with a small beaded bracelet`——选角案底座两件补挂候裁（FIX-6：soft natural brows / healthy bare-skin glow with fine natural grain=反水光肌/浓妆正面锚）；每曲独立面孔律（禁挂星晴 XQ_HER）·定脸拍板后逐字复用。
3. **道具双款块（逐字·帧间同款律载体）**：`PLANE`=`a plain white paper plane folded from a single sheet of notebook paper, its creases crisp, one wing slightly buckled from an earlier flight`；`HER_PLANE`=`a small paper plane folded from cream paper with one wing tip dipped in red`（KN08 现词面非逐字→FIX-5）。
4. **年代世界块**：2000 台北天台-城碗-云海-银河世界（py `LX.LIGHT` 扩展八光块=正身）：`roof_dusk`（8000K 蓝调屋顶+钠雾+水塔剪影）/`roof_night`/`city_bowl`（墨蓝城碗+`warm sodium scatter… aged hand-painted signboards and old neon shop fronts among the apartment windows, a slow drift of small lights`·年代招牌霓虹锚）/`city_moon`（银蓝月晕·KN05 修项块·暖点收紧）/`cloud_moon`（4400K 云海月晕）/`galaxy_gold`（暖金星尘带）/`warm_window`（`one small rooftop window lit warm at 2800K in the blue darkness, its light laying a short amber path across the roof ledge`·贯穿锚）/`streak`（纸机暖迹）。
5. **一歌一律色族块**（GRADE-v1 正身）：**银蓝月晕·一窗暖金**——银蓝母调（roof_dusk/cloud_moon/city_bowl/city_moon）+暖金只做点睛（warm_window 一窗/galaxy_gold 金尘/streak 暖迹）；全片无日戏·夜段胶片 5279；时代底（lift 奶黑+颗粒+halation）全量于装配调色链落、帧层零重复处理（调色师 10-12 实测）；分波段调色动作=GRADE-v1 §三表（装配站执行·帧层光块即色族载体）。
6. **B 批依赖声明**：**KN08+KN24=女主定版依赖押后帧**（30 镜中唯二女主入画镜：KN24=灯窗内初见·全片唯一露脸·挂 KN_HER 全块；KN08=灯窗呈现·造型统一 KN24〔条纹针织+串珠+铁刘海·场内连续律〕）——触发=选角案定脸拍板（导演席拍板权 O-20261012-1135·候选 4 型×三门禁+反向测试留档·KN24 定版后必跑以图搜人反向测试）；B 批包另出（KF-PACK-B·含 FIX-5 统一修法）。**先烧机后定脸**（本曲判例）：A 批 28 帧全零女主脸依赖·不阻塞选角。

## 二、A 批 28 帧组装指令（镜位→词窗/速度/光位/tex）

- **帧位全集**（30 镜剔 B 批 KN08/KN24；逐帧参数正身=shots-v2.py `NEW`·本表不重复 i2v 词面）：

| 镜位 | 窗口(s) | 速 | 词面锚（py note 列） | 景别·机位 | 光位块 | tex |
|---|---|---|---|---|---|---|
| KN01 | 0.00-6.50 | 0.90 | 他叠机（手部特写） | cu·high | roof_dusk | film_night |
| KN02 | 6.50-13.00 | 0.95 | 天台全景（水塔/晾衣绳·城在脚下） | med·eye | roof_dusk | film_night |
| KN03 | 13.00-22.00 | 1.00 | 他持机立于边缘（城为底） | cu·eye | roof_dusk | film_night |
| KN04 | 22.00-30.14 | 1.20 | 掷出（burst 快） | cu·eye | roof_dusk | film_night |
| KN05 | 30.14-37.22 | 1.05 | 想要有直升机=纸机穿探照光柱 | med·eye | city_moon | film_night |
| KN06 | 37.22-43.64 | 1.00 | 掠过屋顶升空（蓝渐深） | med·eye | roof_dusk | film_day ⚠FIX-1 |
| KN07 | 43.64-50.48 | 0.95 | 每天每天想着你=俯瞰城·她窗亮一盏 | ext·high | city_bowl | film_night |
| KN09 | 56.94-59.14 | 0.85 | 漂亮得让我面红=他天台仰脸 | hs·eye | roof_night | film_night |
| KN10 | 59.14-62.66 | 1.10 | 飞姿1=宽弧回旋（hook 行首） | med·eye | city_bowl | film_night |
| KN11 | 62.66-66.26 | 1.00 | 飞姿2=迎面直飞（翼尖弹） | cu·eye | city_bowl | film_night |
| KN12 | 66.26-69.80 | 1.15 | 飞姿3=穿两楼灯阵之间 | med·eye | city_bowl | film_night |
| KN13 | 69.80-78.50 | 0.95 | 飞姿4=全城灯碗上的小点 | ext·eye | city_bowl | film_night |
| KN14 | 78.50-85.82 | 1.00 | 收拍=暖微光尾迹 | cu·eye | streak | film_night |
| KN15 | 89.36-99.00 | 0.88 | 穿云（雾流过翼） | med·eye | cloud_moon | film_night |
| KN16 | 99.00-109.00 | 0.84 | 云海月晕（极缓长镜） | wide·eye | cloud_moon | film_night |
| KN17 | 109.00-117.46 | 0.82 | 银河全景（主呼吸镜1） | ext·eye | galaxy_gold | film_night |
| KN18 | 117.46-126.52 | 0.86 | 银河近景（主呼吸镜2） | cu·eye | galaxy_gold | film_night |
| KN19 | 126.52-131.18 | 0.88 | 纸机漂进星流（纸面染金） | med·eye | galaxy_gold | film_night |
| KN20 | 131.18-134.92 | 0.88 | 融化在银河里（XF_T2 唯一叠化源帧） | cu·eye | galaxy_gold | film_night |
| KN20b | 134.92-138.38 | 0.90 | 感谢地心引力=星尘逆引力折拢下坠 | med·eye | galaxy_gold | film_night |
| KN21 | 141.34-155.00 | 0.92 | 她的天台·红尾纸机停檐上（13.66s 单挂） | cu·eye | warm_window | film_night |
| KN22a | 155.00-163.20 | 0.95 | 隔城相望·她的天台端（锚帧A） | ext·high | city_bowl | film_night |
| KN22b | 163.20-171.34 | 0.95 | 隔城相望·他的天台端（锚帧B） | ext·high | city_bowl | film_night |
| KN23 | 171.34-174.46 | 0.84 | 他的天台（俯望城） | wide·high | city_bowl | film_night |
| KN25 | 177.88-183.28 | 1.00 | 两灯之间的城（全力包含你） | ext·eye | city_bowl | film_night |
| KN28 | 218.18-227.28 | 1.02 | 她的红尾机升空（她的回答·10s 源） | med·eye | warm_window | film_night |
| KN29 | 227.28-234.42 | 0.95 | 让我碰到你=双机航线交错（定格源） | cu·eye | city_bowl | film_night |
| KN30 | 234.42-239.03 | 0.96 | 落回天台双机并排定格收（=歌长） | med·eye | warm_window | film_night |

- C 批 REUSE 11 行（KN08/05/20b/25/09/10/11/12×2/05/13）=装配站解析·零新增烧制（星晴 C 批先例）。
- **试构图律**：672×384·8 步·cfg 1.0·**每镜 1 种子先行烧→构图人眼抽检**（漂移在 1/10 成本截杀）→过审升正档 **1344×768·8 步+1 步 refine（denoise 0.30）**。【现行法对照注·候导演席裁】：QC §12 v1.3/PLAYBOOK S3 海选制 v1.1（阶梯早停 8 张先行→常规 N≥16/重要 ≥32/高潮 ≈50→两级海审取 2）=星晴实烧先例（POOL-0015 verdict 已按海选制执行）——本包两口径并呈·终审定档后 bm-c 按单执行。
- **种子系**：试构图随机取；正档按试构图/海审过审种子锁定（V3 先例）；银河系四镜（KN17-20b）与化开-折拢对（KN20/20b）同 seed 系先行（星尘质感跨镜一致）。
- **帧间一致性硬点**：①**纸机双款同款律**——PLANE 全 18 挂镜同款同磨损（单翼早前压痕）；HER_PLANE=KN21/29/30 同款（KN24 B 批·KN08 B 批对齐逐字）。②**灯窗贯穿锚**——她的暖窗 2800K 同款同光位贯穿 KN07（远景一盏）/KN21/22a/25/28/30（KN08/24 B 批）；warm_window 块逐字。③**首尾对位（投掷-归返弧）**——KN01 天台檐上叠机 ↔ KN30 双机并排归位（同 ledge 框位·起手/收口呼应）；KN04 掷出 follow-through ↔ KN28 她机升空（同向上离台构图=他的问/她的答）。④**城碗三点位族**——KN07/13/25（ext·24mm）+KN22a/b=高空城碗同族构图·互抽检（禁一镜一城）。⑤**化开-折拢对偶**——KN20（XF_T2 源帧）↔KN20b=物质转场对偶·星尘/剪影同款。⑥**KN22a/b 双线交叉锚帧 A/B**=同机位族两端天台构图对位（她端一盏暖窗 vs 他端水塔+晾衣绳剪影）。⑦**KN09 夜脸重演**=副歌1/2 两窗双挂·A 批烧一次装配站解析。
- **特殊工艺注**：①**XF_T2 唯一叠化源帧=KN20**——KF 烧「化开前态」静态始态·dissolve 1.5s（24-48 帧）在 i2v 内执行·全片仅此一处（违例即判负）。②**KN29 渲染翻车判例镜**（v2.4 真客机病）——词面已强化 hand-folded/thin notebook-paper/wingtips a hand-span apart·烧制必抽检双机纸感形制（复发=一票否决）。③**银河五镜写实承载律**（KN17-20b）——超现实段 photographed-real 词面·概念词零入·禁插画感/发光粗线（星晴超现实句保真先例）。④**KN05 探照光柱镜**=CEO 歌词意象令判例（真飞行器判负·删机）——烧制禁出真直升机形。⑤**KN30 定格收口源帧**——239.03=歌长·KF 出双机并排静止完成态。⑥开门帧=KN01（AIGC 显著标识=装配站字层位·非 KF 面）；字幕/字卡=装配站字席制字·帧内零可读文字（文字乱码=一票否决）；本曲无框拍镜、无演唱锚镜适用位（30 镜内缺位对账见 §六）。

## 三、验收判据（帧审三件套·每帧）

1. **词源**：镜位↔歌词句锚（py note 列词面锚+anchors/可爱女人.txt 词行至 236.30·片长 239.03=ffprobe 实证·词面正身=官方歌词）。
2. **判例**：PROMPT-SPEC v1.3 五律（含 §九 V3 四型病灶律 C1/G1/C4/D1/B5）+FIDELITY-SPEC 八块模板+本包共享块；年代锚=QC-CHECKLIST §8/§9+剧本 v3 年代锚清单；风格断裂判例=V3-SIL4 今夜判例（同 seed 异风格=检查点污染·一票否决）。
3. **判据**：十席两波 **≥8.5**·任一席 <7 回炉；**年代穿帮检三面** PASS（服装面：skinny/厚底鞋/水光肌；置景道具面：塑料水箱/现代卫星锅/碟刹碳纤车；城灯天际线面：LED 大屏/101 楼形——任一 2000 后形制=一票否决）；**一票否决四查**（悬浮白物/第二张脸/手部崩/文字乱码）零命中。
4. **词法闸**：lint t2i 三名单零命中（§五.① 实跑 30/30 CLEAN·烧制侧复跑即闸）；词数 105-177 全档合规（<200 官方上限）。

## 四、B 批与回执

- A 批完成→CDN+看板上链+orders 回执（导演席抽检 10%+全量十席归档·verdict 板留档）。
- **B 批触发**=选角案定脸拍板（导演席）→KF-PACK-B 另出（KN08/KN24 两帧+FIX-5/6 修法并入；剧本 v3 面部特写层若导演席裁入亦随 B 批）。
- i2v：白名单签章后按 py 索引 6 出 KF-PACK-i2v（六段式正身·D1 起帧主导律逐镜过·slide 变体句 FLAT 修复并案=FIX-11）。

## 五、开工复审记录（旧约束开工复审制·2026-10-18·KF 起草席）

**①lint 实跑**（python·prompt_lexicon.lint(prompt, mode="t2i")·逐条）：**30/30 CLEAN·零命中**；词数区间 105-177（最短 KN21=105·最长 KN24=178）；i2v 侧 video 模式交叉跑=28/30（**KN01/KN18 [FLAT] 命中**→FIX-11）；窗口/时长断言复跑 GREEN（0→239.03 无 >0.5s 空档无叠窗·源长全 ≤15s）。

**②③④逐镜核对矩阵**（年代锚②/反韩骨相③/ID 引用④；F-n=§五 FIX 清单行号）：

| 镜 | 词数 | ①lint | ②年代锚 | ③反韩/骨相 | ④ID 引用 | 判定 |
|---|---|---|---|---|---|---|
| KN01 | 117 | CLEAN | ✓notebook paper/天台檐/roof_dusk | —（手部镜免） | 免挂✓（手部先例） | PASS |
| KN02 | 158 | CLEAN | ✓水塔/晾衣绳/2000 台式衣橱·材质锚缺→F8 | ✓BONE 结构挂载·**发型缺→F2** | HIM✓ | F2·F8 |
| KN03 | 177 | CLEAN | ✓parapet/衣橱 | ✓cu 近景·BONE+fringe 入句 | HIM✓ | PASS |
| KN04 | 115 | CLEAN | ✓水塔 | —（动势物件镜） | 免挂✓ | PASS |
| KN05 | 134 | CLEAN | ✓探照光柱（CEO 意象令判例）·city_moon 银蓝 | — | 免挂✓ | PASS |
| KN06 | 115 | CLEAN | ✓roof_dusk | — | 免挂✓ | **F1（tex 错档）** |
| KN07 | 131 | CLEAN | ✓city_bowl 招牌霓虹·她窗灯·**天际线锚缺→F7** | — | 免挂✓ | F7 |
| KN08 | 120 | CLEAN | ✓暖窗/条纹针织+串珠 | （B 批）**脸向锚缺→F5** | **半写 ID→F5** | B 批·F5 |
| KN09 | 158 | CLEAN | ✓roof_night | ✓hs 近景 BONE·**发型缺→F3** | HIM✓ | F3 |
| KN10 | 129 | CLEAN | ✓city_bowl | — | 免挂✓ | PASS |
| KN11 | 125 | CLEAN | ✓city_bowl | — | 免挂✓ | PASS |
| KN12 | 127 | CLEAN | ✓两楼灯阵 | — | 免挂✓ | PASS |
| KN13 | 130 | CLEAN | ✓city_bowl·天际线锚缺→F7 | — | 免挂✓ | F7 |
| KN14 | 118 | CLEAN | ✓streak 暖迹 | — | 免挂✓ | PASS |
| KN15 | 124 | CLEAN | ✓cloud_moon（气象镜·无年代物件位） | — | 免挂✓ | PASS |
| KN16 | 129 | CLEAN | ✓cloud_moon | — | 免挂✓ | PASS |
| KN17 | 110 | CLEAN | ✓galaxy·5279 收尾 | — | 免挂✓ | PASS |
| KN18 | 110 | CLEAN | ✓galaxy | — | 免挂✓ | PASS（i2v 面 F11） |
| KN19 | 123 | CLEAN | ✓galaxy+PLANE 同款 | — | 免挂✓ | PASS |
| KN20 | 132 | CLEAN | ✓XF_T2 源帧 | — | 免挂✓ | PASS |
| KN20b | 119 | CLEAN | ✓星尘折拢·写实承载 | — | 免挂✓ | PASS |
| KN21 | 105 | CLEAN | ✓HER_PLANE 逐字/暖窗 | — | 免挂✓（物件） | PASS |
| KN22a | 123 | CLEAN | ✓檐上暖窗/city_bowl | —（空景） | 免挂✓ | PASS |
| KN22b | 119 | CLEAN | ✓水塔+晾衣绳·材质锚缺→F8 | — | 免挂✓ | F8 |
| KN23 | 170 | CLEAN | ✓城碗/水塔 | ✓BONE（wide 远脸）·发型可选→F4 | HIM✓ | F4 |
| KN24 | 178 | CLEAN | ✓KN_HER 2000 造型/暖窗 | （B 批）**底座肤纹缺→F6** | KN_HER✓（定版依赖） | B 批·F6 |
| KN25 | 109 | CLEAN | ✓city_bowl·F7·**两灯归属→F9** | — | 免挂✓ | F7·F9 |
| KN28 | 106 | CLEAN | ✓HER_PLANE/暖窗 | — | 免挂✓ | PASS |
| KN29 | 127 | CLEAN | ✓hand-folded/thin notebook-paper（v2.4 判例词面） | — | 免挂✓ | PASS（判例镜抽检） |
| KN30 | 132 | CLEAN | ✓双机/暖窗 | — | 免挂✓ | PASS |

**FIX 清单**（最小改动·禁改写主体句语义·拿不准标候导演席裁）：

| # | 镜位 | 问题 | 建议修法 | 裁级 |
|---|---|---|---|---|
| F1 | KN06 | tex="film_day"（250D 5246 日戏型号）落蓝渐深夜段——违「黄昏蓝调+夜段=5279」（判决二年1·v2.2 只补 KN01-04 漏本镜）+GRADE-v1「全片无日戏」 | tex 改 "film_night"（500T 5279） | **建议直改** |
| F2 | KN02 | 男主发型变量缺失（BONE 底子/发型分离律·本镜零发型词）→跨镜发型漂移风险 | 加发型档一句 `his thick black fringe lying flat over his eyebrows`（ID_M_2001 全版发型句逐字） | **建议直改** |
| F3 | KN09 | 同 F2（hs 夜脸镜·仰脸构图刘海必入画） | 同 F2 加句 | **建议直改** |
| F4 | KN23 | 同族发型缺失（wide 远脸·风险低） | 可选同步加（与 KN09 同夜同台·一致性优先） | 候导演席裁 |
| F5 | KN08（B 批） | ①女主半写 ID（自定义句非 KN_HER 全块·违 ID 逐字复用纪律风险）②CU/85mm 灯窗构图无脸向锚→模型可自渲染正脸·破「KN24 唯一露脸」律③"a red-tipped paper plane" 非 HER_PLANE 逐字 | B 批定脸时统一：改挂 KN_HER 全块+加脸向锚（如 `her face turned toward the room, seen from outside`）+红尾机逐字 HER_PLANE | 候导演席裁（B 批） |
| F6 | KN24（B 批） | KN_HER 缺选角案底座两件（soft natural brows / healthy bare-skin glow with fine natural grain=反水光肌/浓妆正面锚） | B 批定版 ID 块铸词时并入（逐字） | 候导演席裁（B 批） |
| F7 | KN07/13/25+city_bowl 共享块 | 大远景城碗镜天际线年代正向锚缺位——101 楼形=剧本 v3「夜城镜第一高危」·零否定律禁反向写 | city_bowl 光块尾加 `a low-rise 2000 Taipei skyline of apartment rooftops and water towers`（一处改·8 镜受益·不动主体句） | 候导演席裁 |
| F8 | KN02/KN22b | 水塔材质锚未到部件级（C4 形制锚律）：`a black water tower` 无材质——塑料水箱穿帮高危的正面防线 | 加 `corrugated-tin`（铁皮·剧本 v3 布景锚）一词 | 候导演席裁 |
| F9 | KN25 | `two faint warm lights aligned` 第二盏灯归属未锚（KN22b 他端无暖窗锚） | 候裁：①改「她一盏暖窗+城钠光对位」句 ②或维持两灯并于 KN22b 端补一盏（涉语义·导演席定） | 候导演席裁 |
| F10 | KN02/03/09/23 | 单人物正写法（exactly one figure 族·QC §7）缺位·天台空场克隆人风险低 | 可选加 `alone` 一词（星晴 A 包先例未挂·可持平） | 候导演席裁 |
| F11 | KN01/KN18（i2v 面·非 KF） | i2v [FLAT] 命中（slide 变体句含 `at slow speed`）→**py 自检 assert 现红·「SELF-CHECK GREEN」宣称失效** | i2v 面修法：slide 句改缓入缓出曲线短语（KF-PACK-i2v 出时执法·本项不阻塞 A 批 KF） | 候导演席裁（记录在案） |

**复审附记**：光位审计（QC §10·连续 3 镜同光位=违例）——KN01-04（roof_dusk×4）/KN10-13（city_bowl×4）/KN17-20b（galaxy_gold×5）/KN22a-23（city_bowl×3）为波段式落位（GRADE-v1 分波段叙事·段内景别机位有变化）——候导演席裁豁免或插光位变体镜；本审计原为装配前跑项·星晴先例同律。

## 六、正身对账（SHOTS-V2.PY ↔ SHOTLIST-V2.MD 出入 + 剧本 v3 对账）

1. **py↔md**：md=py `_md()` 衍生物·30+11 行窗口/速度/内容**逐行核对零出入**；md 不含 KF/i2v 词面列（设计使然·词面正身唯 py）。
2. **版本头出入（外观性）**：py docstring 首行「v2.2」vs md 标题「v2.5」（py changelog 已至 v2.5·首行未 bump）。
3. **py 自检宣称失效**：md/py 头部「SELF-CHECK GREEN」现不成立——i2v FLAT 2 命中会被 `assert bad==0` 拦（F11·需 i2v 面修复后复跑）。
4. **剧本 v3 对账（重要·候导演席裁）**：py/md 权威挂「可爱女人-剧本-v3.md（v1.2 修订同步）」·现行叙事正身=**剧本-v3**（supersede）——v3 新增**场 I 尾拍**（多年后天台·~4s·红尾翼贴网+航迹云·零人物）/她的**出血式大特写×2**（C 副歌+H 见机）/**演唱锚镜×2**/E 间奏灯下折纸剪影与夜航回归——**均不在 30 镜内**·KF 量级 44-50 vs 现行 30 新镜——候裁：出 shots-v3 补镜或另开 C/D 批包（本 A 批 28 帧烧制不受阻·帧位均与 30 镜正身一致）。
5. **色温出入**：剧本 v3 §六「她的天台一盏 2700K 灯」+选角案「天台夜灯 2700K 侧脸档」vs py `warm_window`=**2800K**+GRADE-v1「一窗暖 2800K」——**以 py 为准**（零转录律）·记录在案。
6. KN25 两灯归属（→F9）为 py 内部一致性疑点·并入 FIX 清单。

---

*执笔 KF 包起草席（bm-a 导演席下级产线）·2026-10-18 · DRAFT 候导演席终审 · 证据指针=可爱女人-shots-v2.py（NEW/REUSE/常量）/lint 实跑记录 §五.①/GRADE-v1/选角案-v1/剧本-v3/QC-MASTER-CHECKLIST §8/§9/§12 · 禁 git 提交·禁烧制·禁改其他文件*
