# BigStream 提示词撰写规范 v1.1（定稿）

> **CEO 三连令**：O-20261009-1815「自媒体公司好好去研究一下提示词的撰写，你现在写的很有问题，AI识别肯定做不出来好的结果」· O-20261009-1830「多写专业词汇，要具体到某个颜色某个运镜等等，好好去调研开源社区的分享案例什么的，形成机制，不要用模糊的人类自然语言！」+「大量使用成熟的相关skill，并派出专家指导和审查」
> 适用：mv0001《爱在西元前》全管线（Krea 2 Turbo t2i / Qwen-Image-Edit-2511 / MiniMax-H3 本地 / Seedance 云端）
> 状态：v1.1 定稿 · 2026-10-09 · 五路证据归笼（官方深研×3 + 专家审查×2）· A/B 实验结果随附

---

## 卷首·总律

**可检测性原则（本规范一切条款的母法）**：
> **一个词如果不能被摄影机、麦克风、测光表或秒表检测到，就改写它。**

- 可执行词：光源方位/色温值/光比、相机焦段/光圈/f 值行为、运镜类型+幅度+速度、胶片型号/滤镜/颗粒、调色方向+具体色名、秒级时间轴。
- 不可执行词（全禁）：电影感/大片感/史诗感/唯美/震撼/氛围感/高级感/意境/好看/8K/杰作/超写实——情绪标签让模型回归训练先验，产出=「模型那天的心情」（cineprompt.io 实证：'cinematic lighting' 可能给一盏背景灯，也可能给一整套 Storaro 布光）。
- **零否定律（Qwen 系管线）**：负面=ConditioningZeroOut 死通道，一切 NOT/no/without 全部注入正面条件。官方改写器规则 8 原文：「改写之后的prompt中不应该出现任何否定词。」
- **约束词分家律**：Seedance 官方约束句（「保持无字幕，不要生成Logo水印」）与 Qwen-Edit 官方后缀（「，超清，4K，电影级构图」）是各自官方口径的**例外授权位**——仅限该位使用，画面内容描述区仍零否定。

---

## 一、病灶诊断（官方背书定谳）

| # | 病灶 | 证据 |
|---|---|---|
| 1 | **否定词大墙**：NOT Korean idol / no K-pop / no makeup / NO_TEXT 墙 → 把 K-pop/makeup/watermark 概念注入每张图的正面条件 =「太韩化」顽疾总根源 | 官方改写器规则 8（QwenLM/Qwen-Image prompt_utils.py）；社区实证（r/comfyui/Civitai/知乎三源） |
| 2 | 跨图无效指令：`The same young man in every image`（t2i 无跨图机制） | 机制事实 |
| 3 | 编辑指令与画面描述混写（fastface 一句塞 11 层） | 官方口径：一句直接具体改动 |
| 4 | 结构松散/景别缺失/权重稀释（60–120 词堆砌无主线） | 官方公式未按序 |
| 5 | **年代错位词**（图面「干净现代感」来源）：Vision3 5219/5207=2007/09 型号、teal 阴影/变宽耀斑/2383=2010s 审美、85mm f/1.8 奶油焦外=现代 | 摄影指导专家审查 |
| 6 | **视频面根因**：H3 质量依赖 Context-IR 预处理（官方原话 critical）——该模块未开源，本地直跑没有 → 必须自己写官方结构化长文自担预处理 | MiniMax-H3 README |

---

## 二、词表与禁词机制（lint 三名单）

**机制件**：`scratch/mv-carve-bma/prompt_lexicon.py`（产线唯一 prompt 来源，禁手写散文）。

1. **NEG 名单**（Qwen 系零否定）：not/no/without/avoid/never/non- + 缩写（don't/can't/won't/isn't/doesn't）——词边界正则+撇号归一捕捉（子串法误伤 piano/casino、漏网 nothing/can't 的坑已修）。
2. **VAGUE 名单**（模糊词全禁）：beautiful/stunning/aesthetic/masterpiece/8k/dreamy/ethereal/whimsical/cozy/glass skin/porcelain skin/airbrushed/vibrant/epic/photorealistic 等 40+ 词；`cinematic` 灰名单=仅首句 1 次合法。
3. **CONCEPT 名单**（概念注入词，写进条件=注入该概念）：korean/K-pop/idol/salon/makeup/watermark/typography/logo——**反韩化的正确姿势=全词消失，不是否定它**。
4. **FIX_MAP 否定改写器**：`no makeup→bare face, natural matte skin` 等 25 条对照表代码化，lint 命中自动替换复检。
5. **长度闸**：40–200 词（官方上限 200）；**ID 块逐字复用律**：同一人所有镜头引用同一 ID 常量，禁止改写（文本身份漂移）。
6. **f 值行为写法**：不写「浅景深」，写 `f/1.4, only the eyes in focus, ears already soft`。

**正面等价改写表（节选）**：

| 禁 | 正 |
|---|---|
| NOT a Korean idol, no K-pop styling | plain 2001 Taiwanese campus wardrobe, loose unbranded cotton |
| no makeup, no glossy grooming | bare face, matte natural skin with visible pores, unstyled hair |
| no see-through fringe, no curtain bangs | heavy straight solid fringe lying flat over the eyebrows |
| no beautification, no smoothing | keep natural skin with visible pores and 35mm film grain |
| NO_TEXT 墙 | 删除（出字=噪声，重 roll） |

---

## 三、Krea 2 Turbo（t2i）——官方结构公式 + 专业词表组装

**官方公式**（prompt_utils.py）：身份（ethnicity/gender/age）→服装发型→面部/皮肤→姿态动作→周围环境光照→**镜头与风格收尾**。单段连贯散文，英文 <200 词，禁 Markdown 列表/标签堆砌。Krea 2 官方：natural language、长细节出最佳、文字渲染加引号。

**组装器槽位**（build_shot，词表键入）：
- 景别/机位：`head-and-shoulders framing, at eye level`
- ID（逐字复用常量）：`a 20-year-old Taiwanese student with heavy-lidded monolid eyes, a thick lower lip, softly rounded cheeks and a thick black fringe lying flat over his eyebrows`
- 服装（WARDROBE_M）：`loose white short-sleeve school-uniform shirt with dark collar trim...`
- 光（LIGHT·色温+灯型+行为）：`a tungsten practical lamp at 3200K lights the face from frame left, a warm amber pool with deep falloff into shadow`
- **收尾（镜头+调色+胶片）**：`Shot on 35mm lens at f/2.8, 2001 telecine grade with warm skin tones, milky lifted blacks and blooming practical highlights, shot on 35mm Kodak Vision 500T 5279 with visible grain and halation on practical lights`

**2001 年代正确参数（摄影指导定谳）**：胶片=Kodak Vision 500T **5279**（夜）/ 250D **5246**（日）（Vision3 5219/5207 是 2007/09 型号·判「干净现代」）；球面 1.85/4:3 框（变宽 2.39=2010s 判删）；特写 35–50mm f/2.8–4 深焦靠柔光镜软化（85mm f/1.8 奶油焦外=现代判删）；调色=telecine 暖肤色+奶黑+practical 高光晕（teal 阴影/2383 LUT=2010s 判删）；蓝调时刻 8000K+钠灯 2200K 撞色；年代签名光色词=**sodium 钠灯/fluor 荧光管/halo 穿烟逆光光晕/godray 神庙光柱/telecine 调色/plyset 手绘景片**。

---

## 四、Qwen-Image-Edit-2511（编辑管线）——官方三规则

1. **一句直接具体的改动+保持项**（官方正例：`Replace the man's hat with a dark brown beret; keep smile, short hair, and gray jacket unchanged`）——描述**结果状态**，不重述整幅画面、不写编辑过程。
2. **多参照图必须点名** picture 1/2/3（最优 1–3 张）；构图跟随 image1（底潜空间源）。
3. **风格描述放句尾**；妆容/表情修改必须 natural and subtle, never exaggerated（官方红线）。
4. 官方后缀位（例外授权）：结尾加 `，超清，4K，电影级构图`（官方稳定器——lint 对 edit 模式放行）。
5. 官方强烈建议 LLM 改写前置（不 rewrite 结果不稳定）——无本地 LLM，以三段式规则组装逼近：
   `Change only [部位] to [参照 picture N].` + `Picture N shows the same person from another angle for identity reference.` + `Keep identical face shape and head angle, identical eyes and gaze, identical nose, mouth and jawline, identical skin with natural film grain and pores.`
6. denoise 判例沿用：锁脸 0.55–0.6 / 发型档 0.62–0.7。

---

## 五、MiniMax-H3（本地视频）——Context-IR 自担 + 官方三字段

**根因（官方原话）**："H3-Context-IR is critical to the quality of the final output"——未开源，本地直跑必须自己写官方结构化长文。

**I2VA 官方结构**（build_h3_i2va 组装）：
```
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.
integrated_multimodal_description: [首帧锚定→action onset→continuous development→result or reaction]
overall_soundscape: [环境声总结]
non_diegetic_music: N/A (song laid in post)   ← MV 后期贴歌防音轨打架
```
- **运镜三维公式**：Motion type + Amplitude + Speed——`The camera pushes in with small amplitude at slow speed toward the folded letter in her hands.`
- 切镜带时间戳：`[Shot 2] At 00:03.500, the camera cuts to...`（切镜须引入新信息；仅变距离/角度优先用运镜）
- 官方范本=8 秒拉面静态镜头：固定机位+蒸汽持续升腾+中段焦点转移——**静态特写+微呼吸=官方最稳区**（我方 8.5 分判例吻合）。
- H3 词汇（fal 官方托管方）：subtle handheld shake / rack focus / fine grain, soft highlight halation, restrained color。
- 社区强化版结构（Alex Patrascu 实测）：SCENE CONTEXT→TIMELINE 秒级分拍→LOCATION MAP 构图定位→CAMERA（距离/高度/总位移上限）→PHYSICS→LIGHTING→AUDIO→POSITIVE LOCKS→真实设备收尾。

---

## 六、Seedance（云端 generate_video）——中文八要素 + 防崩尾句

**官方公式**：精准主体+动作细节+场景环境+光影色调+镜头运镜+视觉风格+画质+约束条件（60–100 词）。

- **单镜单运镜红线**（官方：「同时要求推拉摇移会增加画面的不稳定性」）。
- **低缓连续小动作优先**（官方：「规避狂奔、大跳、剧烈翻滚」）；动作量化（缓慢抬手/快速转头）；情绪外化（悲伤=低头+肩膀微颤+攥紧衣角）。
- **禁精确秒数时间戳**（官方：强限时长导致异常——与 H3 相反，跨模型不套用）。
- 主体绑定：`张三@图片1` 标签法，2–3 个稳定静态特征。
- **防崩尾句（官方原文）**：`全局约束：人物面部稳定不变形，动作自然流畅，无卡顿无闪烁；保持无字幕，不要生成Logo水印。`（竖屏出字率高）
- ID 防漂移：人脸用大头照特写+全身照分图；双胞胎→「禁止生成同款分身」。
- 官方灯光杠杆：「Adding a single line about lighting is more effective than adding ten adjectives.」

---

## 七、A/B 归因实验设计（提示词工程专家审查版）

- **A 组**：旧否定墙原样（基线）
- **B′组**：A 逐字仅删否定墙+NO_TEXT——单变量干净验证病灶 1
- **C 组**：官方结构公式改写版（128 词样板）——验证新机制全貌
- 同场景同种子 ×4（冒烟级）；定谳级=8–12 种子×多场景+盲评配对。
- 判据：韩化残留/文字出现率/三律自审（高级/去烂俗/去AI感）。

---

## 八、机制件与产线改造

**已落盘**：`prompt_lexicon.py` v1.2——七类专业词表（年代修正版）+ 三名单 lint + FIX_MAP 否定改写器 + 五组装器（build_shot 官方顺序 / build_edit 三段式 / build_h3_i2va 三字段 / build_seedance 八要素 / autofix）。

**产线脚本改造清单（定版门后执行）**：krea2_campus / designs2/3 / qwen2511_edit / hairera / female_era / fastface 六脚本 prompt 全部改 import 词表组装器；NO_TEXT 常量全产线删除；所有编辑批换三段式。

**skill 复用**：create-game-assets（视觉系统命名法/家族生产复用参照/QA 拼板）已入役；机制件+规范=双产出。

---

## 九、证据链（五路归笼）

1. **Qwen 官方**：github.com/QwenLM/Qwen-Image（README + prompt_utils.py 改写器规则 8/结构公式 + prompt_utils_2512.py）· HF Qwen/Qwen-Image 模型卡（negative_prompt 官方态度）
2. **Krea 2 官方**：github.com/krea-ai/krea-2 docs/prompting.md + expansion.txt · krea.ai blog 探索式流程
3. **MiniMax-H3 官方**：github.com/MiniMax-AI/MiniMax-H3（README + skills/h3-prompt-writing base-en.txt）· fal.ai/learn/devs/minimax-h3-prompting-guide · 社区实测 github.com/ecomimagelab/awesome-minimax-h3-prompts
4. **Seedance 官方**：volcengine.com/docs/82379/2222480（经镜像全文提取）· docs.seedance.tv 2.5 指南（镜像核对）
5. **通用方法论**：Google Veo 3.1 prompting guide（cloud.google.com blog + deepmind.google）· OpenAI Sora 2 Cookbook（developers.openai.com/cookbook）
6. **社区分界实证**：cineprompt.io/field-notes/cinematic-is-useless · liminalshort.org/blog/jailbreak-ai · kling-prompt-engineering（github.com/Yuyyxz）· awesome-qwen-image-2-1-prompts · stillslab.com 扩散滤镜解码 · videolens.cc 调色 14 种 · melies.co 运镜句法
7. **专家审查**（2026-10-09 本司派出）：摄影指导（年代修正+2001 签名词+运镜 8 补）· 提示词工程（官方顺序+lint 三名单+FIX_MAP+归因设计）
8. **ComfyUI 官方模板活样例**（本机提取）：api_krea2_t2i / video_minimax_h3_* / api_seedance2_0_* / image_qwen_image_edit_2509_relight

---

*执笔 bm-a · 2026-10-09 · CEO 三令 O-20261009-1815/1830 全收口 · A/B/B′/C 实验结果随附呈报*
