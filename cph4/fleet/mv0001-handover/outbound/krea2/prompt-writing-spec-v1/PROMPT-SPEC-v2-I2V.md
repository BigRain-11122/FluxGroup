# PROMPT-SPEC v2.0 增补律：i2v 提示词拆解律（CEO 2026-10-13 拆解令）

> ⛔ **T0·云道停用（CEO 令 2026-10-20）**：本文件凡以云端 API（视频/图像/TTS/云端 LLM/云存储）为生产路径的条款**停止执行**，改走本地机队（bm-a/bm-b/bm-c）；本地做不了=排队+报障，不得自动回落云端；例外仅 CEO 亲批+留痕。权威口径=`cph4/fleet/CLOUD-OFF-LOCAL-ONLY-v1.md`。历史调用记录与判例保持原样，不作改写。

> **CEO 原令**（2026-10-10-13 上午·O-20261013-1045）：「你的提示词写法很有问题，好好去调研应该怎么写，不是你写个2001台湾音乐MV风格就行了的，所有的提示词要一个个拆解成AI能理解的术语，准确的，简洁的，排序是科学的！」
> 适用：一切 i2v（图生视频）提示词——Seedance 云端 / MiniMax-H3 本地 / 后续引擎；t2i/edit 面沿用 v1.2 不变。
> 证据源（四源归笼·10-13 全文提取）：①**火山方舟官方一手文档**《Doubao Seedance 2.0 系列提示词指南》（volcengine.com/docs/82379/2222480·2026.09.22 版——官方「工程型指令」定义+空间层/时间层解耦+分镜时序法+动作量化表+**情绪具象外化表**+一镜一运镜+人脸参考法+素材四功能角色）②**Seedance 2.0 官方完整指南**（docs.seedance.tv/zh/seedance-2-complete-prompting-guide——i2v 专项「不应再描述图像」铁律+分层运动法+官方关键词表）③**MiniMax H3 官方提示词指南**（docs.seedance.tv/zh/minimax-h3-prompt-guide——六部分结构+可观察动词法+结束画面+保持不变）④**社区经验提炼**（rich5000/seedance-prompt-guide SKILL.md——素材角色指定法/镜头写法表/优化 Checklist/「纯参数堆砌模型不一定响应」避坑实证）。

---

## 一、病灶标本（10-12/13 夜窗实发·自案解剖）

夜窗 Seedance 波 15 单提示词系导演席手写散文，违了自家 v1.2 可检测性原则。以 Z03 实发为标本：

```
Single continuous take at 24fps, 16:9. A wide shot at eye level; the camera holds a
locked-off tripod frame down the long aisle while the case lights go out one after
another, each amber pool shrinking in turn, the last pool holding on around the
carved slab at the far end. A dark museum aisle, the row of warm case lights dying
one by one down the hall, the remaining pools of amber shrinking until only the far
one remains. Warm amber monochrome grade with deep crushed shadows, visible 35mm
film grain, highlights blooming softly. Every motion eases in and settles out, in
the quiet camera language of a 2001 Taiwanese music video.
```

| # | 病灶 | 定性 |
|---|---|---|
| 1 | 「in the quiet camera language of a 2001 Taiwanese music video」 | **文化锚**：模型训练先验对该短语无可靠映射=彩票；CEO 点名判负 |
| 2 | 第二整段重述画面（A dark museum aisle, the row of warm case lights…） | **违反官方 i2v 铁律**：官方原文「输入图像已经确定了主体外观、构图、色彩和基本环境，因此提示词不应只是再次描述图像」——首帧全有，重述=浪费+漂移源 |
| 3 | 风格段正面重述（Warm amber monochrome grade… film grain… blooming softly） | 风格已烘焙在首帧里；正确姿势=官方保留句（preserve film grain / honor the original color palette），不是再描述一遍 |
| 4 | 「Single continuous take at 24fps, 16:9」 | **API 参数入 prompt**：fps/比例/分辨率由 param 字段控制，写进文本=冗余+冲突源 |
| 5 | 「Every motion eases in and settles out」 | **抽象节奏散文**：应拆到每个动作的速度词上 |
| 6 | ~110 词 | 超官方 i2v 范例预算（官方范例 60-90 词） |

## 二、v2.0 拆解律（五律·i2v 一切提示词硬门）

### 律一·文化锚禁令（CULTURE-ANCHOR BAN）
「2001 台湾 MV」「90 年代港片感」「像某某电影」「in the style of」「aesthetic of」「quiet camera language of」——**一切以年代/地域/作品名当风格词的写法全禁**。年代感在本产线的正确载体=关键帧（KF 帧已烘焙全部年代参数：5279 颗粒/球面镜头/telecine 暖调）——i2v 阶段唯一合法的风格动作=**保留句**。若某视觉意图无法用可检测术语表达（光源方位/色温/运镜类型+幅度+速度/秒级行为），说明理解不到位，回去拆，不是换个文化词。

### 律二·运动优先律（官方 i2v 铁律·逐字执法）
Seedance 官方原文：「**提示词不应只是再次描述图像，而应说明接下来会发生什么，以及场景如何运动**。」i2v 提示词的信息预算全部花在「接下来 5 秒内的变化」上：主体动作（一个可观察动词+速度+方向）→ 前景运动 → 背景运动 → 相机行为 →（可选）一句氛围。**禁写首帧已含的静态信息**（构图/材质/光线状态/风格描述）。

### 律三·分层运动法（官方）
官方分层：**前景**（最近镜头层：飘尘/烛焰晃动/水波）→**主体**（核心动作）→**背景**（纵深：远处火光/移动云层/走动人影）。「初学者常见的错误是只描述主体动作，而忽略环境变化」——每镜至少两层有运动（静镜=微呼吸+尘埃层）。三层不必等强：主体清晰优先，前后景以更细微运动衬托。

### 律四·科学排序（按引擎·官方序逐字复用）
- **Seedance i2v**：`[镜头定式] → [主体动作+速度+方向] → [前景运动] → [背景运动] → [相机行为收束] → [保留句]`（可选单句氛围）。官方关键词词表（逐字复用勿改写）——运动质感：gently / barely perceptible / slowly drifting / rhythmically swaying / subtly rippling；人物生命感：micro-expression shift / eyes slowly tracking / breath visible / hair softly lifted by wind；镜头：locked off / slow push-in / subtle drift / gentle handheld sway / rack focus；风格保留：maintain painterly texture / **preserve film grain / honor the original color palette**。
- **MiniMax-H3（六部分·官方）**：`场景顺序（开场→动作→结束） → 主体动作 → 参考用途 → 相机（初始景别角度→主要运动→停在什么构图） → 声音（MV 场=按音轨禁令省） → 结束画面+保持不变`。**方括号相机命令是官方唯一有语法保证的运镜通道**（`[Push in] [Truck right] [Pan left] [Tilt up] [Pedestal up] [Tracking shot] [Shake] [Static shot]`·官方示例可串联：`picks up a book [Pedestal up], then reads [Static shot]`）——我方 32 条 H3 单曾零方括号，属闲置官方能力。**H3 时间戳：官方 API 示例无时间戳（旧「0.0–1.2s 官方案例」=误引，2026-10-20 官方文档调研勘正）**。
- **Seedance 官方框架（2026-10-20 复核）**：六要素=主体/动作/环境/风格/镜头/声音；参考生视频用「(Preserve) 保留 + (Transform) 转换」两段式。**Seedance 2.5 指南称支持整数秒时间戳**（示例「第 5 秒向左快速横移」·研究件转述，待我方复核该页原文）——**「禁精确秒数」是本厂旧偏好，不是官方律，已废止**。
- **正字法**：官方「使用可观察的动词：把『很高级』改成『冷色侧光沿玻璃边缘移动，反射干净克制』」——每个审美判断落成一件可观察的物理事件。

### 律五·准确+简洁（参数分家）
- **API 参数禁入 prompt**：fps/分辨率/时长一律走工具参数位。**例外=Seedance 全局约束段**：官方四段式最后一段要求写「画幅 + 无字幕 + 无 BGM」，该段合法（旧 lint「见 16:9/720p 即 FAIL」过宽，已收窄为「非 Seedance 包才判」）。
- **一镜一动作**（v1.2 沿袭）：动作链=压缩=AI 加速感；动作量化=速度+方向+一次完成。**官方背书**：Seedance「不将提示当剧本处理」、时间戳「非逐帧剪辑指令」；PixVerse 实测堆叠动作被「混合成不稳定运动」。
- **词预算**：i2v 单镜 40–90 词=**本厂偏好，非官方**（官方结构是六要素，无词数上限；Vidu 允许 20000 字符）。超预算仍建议压缩，但不得以「官方上限」为名拦截合法长包。
- **负面词按模型分轨（勘正·2026-10-20）**：Krea2/BFL 系**无 negative 字段**，且我方 KF 链路 `steps=8, cfg=1.0` + `ConditioningZeroOut` → **cfg=1 时负向条件乘 0，负权重一律不生效**（本机脚本实读）；Seedance 官方**建议**写关键排除项（`no cuts` / `do not change the character's appearance`）；H3 未载明。→「零否定」只在 Krea2 面成立，禁当全局律。

## 三、Before/After 终例（Z03 同镜重写）

**AFTER（v2 拆解版·58 词）**：
```
Locked-off tripod shot. The row of case lights goes out one by one down the aisle,
nearest first: each amber pool contracts and dies over about one second before the
next follows, until only the far pool around the carved slab remains lit. Fine dust
drifts through the surviving light. The camera and framing stay static throughout.
Preserve the film grain and the original amber palette.
```
对照表：镜头=locked-off tripod（官方词表）｜主体动作=lights go out nearest-first（次序方向）｜速度=each pool contracts over ~1s（可检测）｜前景=fine dust drifts（分层法）｜相机=static throughout（收束）｜保留句=preserve film grain + original amber palette（官方词表原文）｜零文化锚·零画面重述·零参数重复·58 词。

## 四、lint 机制增补（prompt_lexicon.py v1.4 待执行清单）

1. **[CULTURE] 名单**（video/i2v 模式 FAIL 级）：`music video` / `MV style` / `film of` / `like a 19xx/20xx` / `Taiwanese MV` / `in the (quiet )?camera language` / `in the style of` / `aesthetic of` / `vibe of` / `feel of a`。
2. **i2v 重述检**（WARN 级）：i2v 模式下出现 ≥2 句静态场景描述（无运动动词的 be-句）=提示重述嫌疑，人工复检。
3. **API 参数检**（FAIL 级）：prompt 文本出现 `24fps|16:9|9:16|720p|768P|1080p` = 参数入文。
4. **新增组装器** `build_seedance_i2v(subject_motion, fg_motion, bg_motion, camera, preserve, mood=None)`：五槽全走词表键入，禁手写散文（十一脚本改造律同 v1.2 §八）。
5. **mv_full_shots.py 全表 i2v 行重写**：66 镜 i2v 行按五槽组装器重写（回炉波+专辑十曲全部生效）。

## 五、落闸与回炉备案

- **本律即刻生效**：一切新发 i2v 单（回炉波/专辑曲/重摇）必过 [CULTURE]+i2v 检。
- **回炉名单**（QC-r955 披露件·成片交付后按 v2 提示词重烧对审）：C02（v4 7.3）/C03（reveal 事件缺失 5.5）/C04（字形几何上限 7.0）/R05（冻结尾+曝光斜坡 7.0）/E03（玻璃几何 7.0）+ 夜窗云波全 21 条 Seedance/H3 片（提示词病灶产物·按成片观感抽审定回炉范围）。
- **执笔**：bm-a 导演席 · 2026-10-13 · 两官方源全文提取在档（docs.seedance.tv 镜像站）· CEO 拆解令 O-20261013-1045 收口件。
