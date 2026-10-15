# R-20261015-video-official — AI 视频生成模型官方提示词规则与技巧（CEO 直令·调研波一）
> 溯源：CEO 原话「好好看官方文档」·消费方=BigStream/MV 产线（MiniMax H3 本地 ComfyUI + Seedance 2.0/2.5 云端）·判据预注册=①各模型官方提示词结构规则清单 ②官方关于「失败/误导提示词」的全部条款 ③i2v 起帧主导性/动作可行性/运动粒度官方口径
> 验证声明：实读 19 次（15 抓取+4 检索），成源 10 条：A=9（①volcengine 82379/2222480 ②docs.seedance.tv/en/seedance-2-5-prompting-guide ③docs.seedance.tv 排查指南 ④github.com/MiniMax-AI/MiniMax-H3 README ⑤同仓 base-en.txt ⑥同仓 ref-en.txt ⑦developers.openai.com sora2_prompting_guide ⑧cloud.google.com/blog Veo 3.1 guide ⑨docs.cloud.google.com video-gen-prompt-guide）B=1（fal.ai H3 guide）C=0 M=0。
> 失败面：volcengine 站内 2.5 中文提示词指南未获独立 URL（英文官方版已替代，未成源不算失败面缺口）；fal.ai 指南 48k 字符仅读前 14k（示例为主，核心规范已获）；Sora 指南全文读毕；注入红线：全程未执行任何外部页面内嵌指令。
> 注记：本件超出 R 件 60 行帽——派工单明令五节全清单+逐条出处，内容规格优先，超帽留痕。

## 一、Seedance 官方结构与规则

### A1. 火山引擎《Doubao Seedance 2.0 系列提示词指南》（A·确认）https://www.volcengine.com/docs/82379/2222480
1. 进阶公式：`精准主体+动作细节+场景环境+光影色调+镜头运镜+视觉风格+画质+约束条件`（"好的提示词不是单纯的'文案型形容'，而是'工程型指令'"）
2. 模型内部按"空间层/时间层"解耦理解
3. 主体定义句式「将<图片N>中的[核心特征]定义为<主体N>」，2–3 个稳定静态特征，标签全程一致
4. 分镜按"镜头1/2/3"组织，每镜=运镜+动作表情+空间变化+音频
5. 运镜："一个镜头里尽量只指定 1 种运镜方式，不要同时要求推拉摇移，会增加画面的不稳定性"
6. 符号：音乐（）、音效<>、台词{}、字幕【】
7. 素材 4-5 个为宜，"不建议用满素材上限，过多素材会导致模型难以判断特征优先级"
8. 参考生视频三类句式：全模态参考「参考<图片N>中的<主体N>，生成...」/编辑「严格编辑<视频N>，将<原特征>修改为<新特征>」/延长「向前/向后延长<视频N>」
9. 动作边界（A 级原文）："优先选用缓慢、轻柔、连贯的细微动作，尽量规避狂奔、大跳、剧烈翻滚等高爆发、大动态动作"
10. 动作写法：细化到肢体部位+幅度/速度/力度；写明"前后动作的惯性与承接关系"（=衰减态/结果态写法的官方依据）
11. 2.0 时间口径："模型对精确时间（如 0–3 秒）的支持不稳定，强行限制时长可能导致生成结果异常"

### A2. docs.seedance.tv《Seedance 2.5 Prompting Guide Part 1》（A·确认）https://docs.seedance.tv/en/seedance-2-5-prompting-guide
12. 四段式：`Asset mapping + one-sentence brief + timeline or shot order + global constraints`
13. 资产映射两问："Who or what does it belong to? What specifically should be referenced?"；须声明"what must not be inherited"；"Do not rely on names written inside reference images, and do not make the model guess"
14. 2.5 时间口径（与 2.0 相反，版本差异！）："Seedance 2.5 can follow whole-second timestamps. Time ranges should be continuous—`0–3 seconds, 3–7 seconds, 7–15 seconds`—without unexplained gaps"
15. 内容密度律（A 级原文）："If a time range contains too little, the model will improvise; if it contains too much, actions may be omitted or the edit may become frantic"
16. 不常见运镜术语须补"describe what the audience should actually see"
17. 情绪外化："use visible facial changes... instead of an abstract mood alone"
18. 分镜板"leaves room for interpretation"，严格对齐用独立关键帧；关键帧声明句式"Use Images 1 through N in order as keyframes"
19. blockout 泄漏："Remove motion paths, axes, and camera frustums so they do not leak into the result"
20. 上限：图≤30（1-8 主体最稳）、视频/音频各≤10 段共 30s、分镜板<15 格
21. "A basic prompt does not need a pile of adjectives... make the action, camera, and sound form a complete eight-second arc"

### A3. docs.seedance.tv《Generation Failure Troubleshooting Guide》（A·确认）https://docs.seedance.tv/
22. 官方失败原因列表含 "The prompt is too long, too complex, or includes a format the model does not support"
23. 官方反模式原文："several blurry screenshots with a very long prompt containing many unrelated instructions, multiple scenes, and complex camera movements"
24. 音频失败反模式：三人 20 秒重叠争吵；官方修正="A single spokesperson says one short line"
25. 审核拦截：真人名人/版权 IP/敏感内容（产线关联弱）

## 二、MiniMax H3 官方结构与规则

### A4. GitHub README（A·确认）https://github.com/MiniMax-AI/MiniMax-H3
26. 官方提示词技能=skills/h3-prompt-writing，两份指南：base-en.txt（T2VA/I2VA/FL2VA/L2VA）+ref-en.txt（Ref2VA）；ComfyUI 用 R2V/T2V 模板
27. 三模块：H3-Context-IR（指令中间表示，官方"strongly recommend"接入）+H3-Base+H3-Regenerate-2K
28. 规格：4-15s、24FPS、768p 短边（2K 需 Regenerate）；FL2VA 图 0/1/2 张；Ref2VA 图≤9/视频≤3/音频≤3/总≤12

### A5. 官方 base-en.txt《Video Prompt Writing Guide》（A·确认）https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/main/skills/h3-prompt-writing/references/base-en.txt
29. 三核心字段：`integrated_multimodal_description:` + `overall_soundscape:`（1-4 句）+ `non_diegetic_music:`（1-3 句，"do not use abstract mood words"）
30. I2VA 强制首行："For the target video, at 0.00 seconds into the target video, (from [Shot 1]) is fully referenced."
31. I2VA 结构律（起帧主导性核心）："first-frame anchor → action onset → continuous development → result or reaction"；"first establish the style, subjects, composition, and scene anchors in the image, then describe the next action. Character identity, clothing, colors, key objects, and spatial relationships should remain consistent"
32. FL2VA 结构律："first-frame state → observable intermediate changes → progressively narrowing differences → last-frame state"，"generally favors a single shot"
33. L2VA 结构律："plausible preceding state → ... → last-frame landing"（末帧图"does not inherently belong to Shot 1"）
34. 切换句式 "[Shot 2] At 00:03.500, the camera cuts to..."；"If only the distance or a slight angle needs to change, prefer camera motion"
35. 运镜三维语法（运动粒度官方口径）：motion type+amplitude+speed；"Add amplitude and speed only when they are meaningful; medium amplitude and normal speed are usually omitted"；官方样例均为绑定目标物的自然动作句："The camera pushes in with small amplitude at slow speed toward the folded letter in her hands."
36. 说话人 ID：(S1)(S2) 跨镜头稳定；台词 <spoken> 逐字保留不改写
37. 画外音唇音规则："Immediately after every voiceover `<spoken>` block, state that the corresponding on-screen character's lips remain completely closed"（唇态=官方显式受管特征）

### A6. 官方 ref-en.txt《Full-Reference Mode Guide》（A·确认）同仓 references/ref-en.txt
38. Ref2VA 六节结构：subject_definitions/summary/retention_analysis/detailed_description/overall_soundscape/non_diegetic_music；四类标签 <SUBJECT_N>/<PICTURE_N>/<VIDEO_N>/<AUDIO_N>
39. <PICTURE_N> 独立项仅当图"itself serves as a shot's first frame, keyframe, last frame"；保持度标记 fully_preserved/partially_preserved/attribute_transfer/weak_reference
40. 任务类型六分：keyframe completion/reference generation/video editing/video continuation/audio reuse/audio reference；"Do not treat newly added actions, backgrounds, or plot events in the target video as losses of reference fidelity"

### B1. fal.ai H3 Prompting Guide（B·确认）https://fal.ai/learn/devs/minimax-h3-prompting-guide
41. 端点三分律："No media means Text to Video. An image that is literally the first or last frame means First & Last Frame. Anything you are treating as a *reference* rather than a frame means Reference to Video"
42. 提示词≤7000 字符；示例模式：关键帧序列声明、素材映射先行、负面约束收尾（"Do not add people, vehicles, buildings, or logos"）

## 三、Veo/Sora 官方规则（对照系）

### A7. OpenAI《Sora 2: Prompting Guide》（A·确认）https://developers.openai.com/cookbook/examples/sora/sora2_prompting_guide
43. 心法："briefing a cinematographer who has never seen your storyboard. If you leave out details, they'll improvise"；"Treat your prompt as a creative wish list, not a contract"（同提示词多次结果不同=特性）
44. 参数律：分辨率/时长/角色引用"will not change based on prose like 'make it longer.'"——必须走 API 参数
45. 短片律（A 级）："The model generally follows instructions more reliably in shorter clips... stitching together two 4 second clips... instead of a single 8 second clip"
46. 详略律："Longer, more detailed prompts restrict the model's creativity. It will try to follow your guidance, but might not always do so reliably"（官方自认长提示词跟随不可靠）
47. 运动粒度（A 级）："Each shot should have one clear camera move and one clear subject action. Actions work best when described in beats or counts"；弱→强示例："Actor walks across the room"→"Actor takes four steps to the window, pauses, and pulls the curtain in the final second"；"moves quickly"→"Cyclist pedals three times, brakes, and stops at crosswalk"
48. 多镜头律："keep each shot block distinct: one camera setup, one subject action, and one lighting recipe at a time"
49. 台词律："Long, complex speeches are unlikely to sync well and may break pacing"；4s 容一两个短对答，8s 容几组
50. 角色≤2/次；画面一致性："reuse phrasing for continuity, and avoid mixing traits that may compete"
51. i2v 口径："The model uses the image as an anchor for the first frame, while your text prompt defines what happens next."；官方 i2v 示例均为短句顺延（"She turns around and smiles, then slowly walks out of the frame."）
52. 官方降级法（失败恢复协议，A 级）："Editing is for nudging, not gambling. Use it to make controlled changes – one at a time"；"If a shot keeps misfiring, strip it back: freeze the camera, simplify the action, clear the background. Once it works, layer additional complexity step by step."
53. 模板：Prose 场景描述+Cinematography（Camera shot/Mood）+Actions（beats 列表）+Dialogue 块

### A8. Google Cloud 官方博客《Ultimate prompting guide for Veo 3.1》（A·确认）https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1
54. 五段公式：`[Cinematography]+[Subject]+[Action]+[Context]+[Style & Ambiance]`
55. 负面提示词写法："specify 'a desolate landscape with no buildings or roads' instead of 'no man-made structures'"（否定嵌入正向描述）
56. 声音三段式：台词用引号、`SFX:` 前缀、`Ambient noise:` 前缀
57. 时间戳分镜：`[00:00-00:02]` 段落式多镜头单次生成
58. Veo 3.1 image-to-video="greater prompt adherence"（官方宣称以图为准的跟随性更强）

### A9. Google Cloud 文档《Video generation prompt guide》（A·确认）https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/video-gen-prompt-guide
59. 运镜可靠性条款（A 级）："Some advanced camera angles are not officially supported. The results and reliability may vary depending on the overall prompt"
60. 长时事件提醒："keep clip length in mind for events that occur over a longer period"（花绽/冰融等过程须匹配片长）

## 四、i2v 起帧主导性官方口径（判据③收口）
61. 【确认·三源 A】首帧=锁定锚点：Seedance 2.5"Locked tasks include... first/last-frame generation... **The model must adapt to that asset**, so some generation settings cannot be changed freely"；H3 I2VA"fully referenced"+先锚定后写发展；Sora"image as an anchor for the first frame, while your text prompt defines what happens next"。三家一致：提示词职责=描述"从锚点向前发展"，无一官方文档承诺提示词可改写起帧既有状态。
62. 【推测·单源无原文】"冲突时谁赢"官方无逐字裁决；但锚点律+H3"key objects... remain consistent"一致指向：起帧赢，提示词须顺着锚点写。我方案例①（起帧闭嘴要求唱→保持闭嘴）与此吻合。
63. 【确认·A】唇态为显式受管特征：H3 画外音规则强制声明"lips remain completely closed"，反向证明唇动-音轨为模型主动对齐项；案例①修正路径=起帧换张嘴帧，或按 I2VA 结构写"从闭嘴到张嘴"的 action onset+唱词入 <spoken>。
64. 【推测·结构律推演】案例②：「the mallet has just landed」（衰减/结果态）合乎官方"result or reaction"结构与"动作惯性承接"律；「strikes with mallet」需帧外道具+已完成事件，违反锚点律（key objects consistency）。官方无「凭空出道具」原文。
65. 【确认·A】运动描述粒度：H3 三维语法"只在有意义时写幅度/速度"；Sora"one clear camera move + one clear subject action"+beats 计数；Seedance"一镜一运镜"。案例④「at slow speed」本身是 H3 官方合法词汇，但官方样例全部绑定目标物（"toward the folded letter"）；裸速度标签出匀速机械感=推测级（官方未明示，样例模式一致指向：速度须绑定动作与目标物成句）。
66. 【确认·A 单源】案例③多物体光事件「dimming one by one」：Seedance 2.0"通过提示词文字描述特定特效时，可能会出现特效效果与预期不符"→官方解法=参考视频定义特效；叠加 2.5 密度律"contains too much, actions may be omitted"。此条仅 Seedance 官方明文，H3 侧无对应条款（单源标注）。

## 五、常见误导模式汇总（官方失败/误导条款全录）
67. 长而杂的提示词：A3-22/23（过长过杂+多场景+复杂运镜堆叠=官方认证反模式）、A1"请勿直接将完整剧本作为提示词使用，文案内容过度冗余易造成模型理解混乱"、A7-46（长提示词跟随不可靠，官方自认）
68. 时序错误：A1-11（2.0 精确秒不稳定）vs A2-14（2.5 支持整秒但须连续无缺口）；A2-15（内容过少→模型即兴，过多→动作被省略/剪辑急促）；A9-60（过程事件须匹配片长）
69. 运镜错误：A1-5（一镜堆推拉摇移→不稳定）、A9-59（非官方支持角度可靠性存疑）、A2-16（生僻运镜术语须写可见结果）
70. 动作错误：A1-9（高爆发大动态规避）、A7-47（模糊动作词→写 beats 计数）、A1 情绪抽象词→外化为身体细节
71. 特效/多对象错误：A1-12 特效文字描述不可靠→参考视频；数字倒计时"无序跳变"；参考人物>4 人不稳、多视图→双胞胎
72. 台词错误：A7-49（长复杂台词不同步）、A3-24（多人重叠对白失败→单人说单句）、A1 台词语言混用
73. 素材错误：A1-7（素材堆满→优先级混乱）、A2-13（让模型猜资产归属）、A1-18（人脸混用图/占比小→换脸）、A2-19（blockout 辅助线泄漏）
74. 参数错误：A7-44（时长/分辨率散文内请求无效）
75. 恢复协议：A7-52（失败→冻结镜头/简化动作/清空背景，成功后再逐步加复杂度）；一次只改一处

## 结论应用表（research-protocol §二.1 强制·落点四选一）
| 结论 | 落点 | 状态 |
|---|---|---|
| 各模型官方结构规则清单（#1-#60） | 任务单：BigStream/MV 产线提示词规范修订（H3 用三字段模板，Seedance 用四段式/八要素公式） | 已交付待接线 |
| 起帧主导律：起帧=锁定锚点，提示词只写"向前发展"（#61-64） | 任务单：i2v 起帧选帧标准（唇态/道具须在帧内）+提示词改衰减态写法 | 已交付待接线 |
| 运动粒度律：速度绑定目标物成句、一镜一运镜、动作写 beats（#65） | 任务单：产线运动描述词表修订 | 已交付待接线 |
| 多物体时序特效改参考视频（#66·A 单源） | 决策呈报：CEO 定夺是否引入特效参考视频管线 | 已交付待接线 |
| Sora 官方降级法（#75） | 任务单：产线抽卡失败 SOP | 已交付待接线 |

- 更新记录：T0 骨架落盘（早落盘律 2026-10-15）→ T1 Seedance 2.0+2.5+排查（实读6）→ T2 H3 README+base+ref+fal（实读5）→ T3 Sora 全文+Veo 双源+收口（实读8）→ 终稿 123 行（超 60 行帽，内容规格优先，验证声明注记·防线二重读实测）。
- 防线二：待独立抽验（建议抽 #5 运镜条款与 #61 锚点律两处承重主张直读源）。
