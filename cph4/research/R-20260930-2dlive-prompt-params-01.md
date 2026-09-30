# R-20260930-2dlive-prompt-params-01｜本地视频生成（I2V）提示词工程与参数科学

- **件类**：调研件（R-件）｜**状态**：定稿 v3
- **立令**：O-20260930-1856（O-1706 追加令）·调研路 2
- **产出日**：2026-09-30
- **产线背景**：2D 动作/特效唯一产线＝本地 I2V 短视频 → 科学取关键帧 → sprite 图集 → 引擎逐格播放；本机 RTX 4070S 12GB
- **对象模型（12–16GB 显存档）**：LTX-Video 0.9.5（本司在用·diffusers 0.40 链）、Wan2.2-TI2V-5B、CogVideoX-5B-I2V
- **边界声明**：模型谱系实测矩阵＝R-20260930-video-models-01.md（他窗在档）；取帧方法＝R-20260930-video-extraction-01.md（他窗在档）。本件只管**提示词工程**与**参数科学**，不重复上述两件内容。
- **诚实律**：✓ 双源确认｜🟡 单源（官方单源/社区均标此级，附注区分）｜⬜ 未验证（推演/待产线实测）｜✗ 判负勿采用。【本司法】＝本司已立法/定谳条目（内规，不出本件重推导）。关键结论附 URL；官方无成文处如实标「官方空白」。

---

## §0 结论速览（SOP 可直接抄）

### 0.1 万用 I2V 提示词结构公式（本司定谳版）

```
[相机锁定] + [主体+identity 锚] + [单一动作+时序词] + [风格锁] + [背景稳定措辞]（+ 模型面允许时：负面提示词）
```

五段纪律：
1. **相机锁定先行**（sprite 产线铁律，【本司法】）：`static camera, no camera movement, no zoom, fixed view`。官方锚：LTX 官方示例反复用 `The camera remains stationary, focused on ...`（✓ HF 卡+diffusers 双源）；CogVideoX 官方改写模板明令 `Don't contain camera transitions!!! Don't contain screen switching!!! Don't contain perspective shifts!!!`（🟡 官方单源成文）。
2. **主体一句到位**（【本司法】）：I2V 下首帧＝identity 锚；提示词**默认不复述外观细节**，只给动作上下文。Cog 官方同向：「The input image is the first frame of the video, and the output video caption should describe the motion starting from the current image.」（🟡 官方单源成文）。Wan 官方 I2V 示例则示范「与首帧一致的复述」可行——原则＝**宁缺毋错**：要么不写，要么必须与首帧逐点一致。
3. **动作只写一个**，配时序词 first/then/during，结尾写「回到起始姿态」；循环靠引擎逐格回放保证，不指望模型自身完美循环（【本司法】；LTX 官方「Start with main action in a single sentence」🟡 官方单源，为部分依据）。
4. **风格锁**＝双锚之一，整段照抄（【本司法】，两锚词为已立法风格资产）：
   - 水彩锚：`wet-on-wet watercolor, no ink outline, morandi palette, white dot highlights, soft edges`
   - 糖瓷锚：`soft glossy ceramic toy render, pastel palette, rounded, global illumination`
5. **背景稳定**：`background stays unchanged, no new objects appear`（【本司法】措辞；LTX 官方示例默认背景静态描述 ✓）。

### 0.2 三模型参数 profile 速查表（投产 M 表）

| 参数 | LTX-Video 0.9.5 | Wan2.2-TI2V-5B | CogVideoX-5B-I2V |
|---|---|---|---|
| 分辨率 | 512px【本司法 M1】；官方约束：32 倍数、<720×1280 最佳（✓ 卡+README） | **仅** 1280×704 / 704×1280（✓ configs+README） | 720×480 硬固定（✓ HF 卡+README 表） |
| fps | 24（官方示例导出 ✓；pipeline `frame_rate` 默认 25 仅作时间坐标） | 24（✓ config+README/HF 卡） | 8（✓ HF 卡+README 表） |
| 帧数 | 8N+1（25/33/…/257），官方「below 257 最佳」（✓ 卡+README） | 默认 **121**（✓ config+「5 秒 720P」互证）；帧律 4N+1（✓ generate.py+diffusers 注） | **49**（8N+1，N≤6，默认即上限 ✓✓） |
| steps | 30【本司法 M1】；官方带 20–30（速）/40+（质）（🟡 官方单源） | **50**（✓ 官方 config+diffusers 默认） | **50**（✓ HF 卡示例+diffusers 示例） |
| CFG/guidance | **3.0**【本司法 M1】；官方 3–3.5 带（✓ README+diffusers 默认 3 互证） | **5.0**（✓ 官方 config+diffusers 默认） | **6.0**（✓ HF 卡示例+diffusers 示例） |
| shift | 无此参 | **5.0**（🟡 官方 config 单源；diffusers 通用建议：低分档 2.0–5.0、高分档 7.0–12.0 🟡） | 无此参 |
| negative prompt | 支持＋官方句（✓ 卡+diffusers） | 支持；Wan 家族默认负面词（diffusers 官方示例全文照录，🟡 官方单源） | 支持（diffusers 参数+示例 🟡） |
| 提示词语言 | 仅英文（🟡 官方单源，卡面两处成文） | 中英双语（✓ HF 卡标签+umt5-xxl config） | 仅英文（✓ 三处官方成文） |
| token 窗 | **128**（✓ diffusers 默认+本司 0.40 链实测判例） | 512（🟡 diffusers `__call__` 默认单源；同页 `encode_prompt` 签名示 226，文档页内不一致，如实记录） | **226**（✓ HF 卡+README 表+diffusers） |
| 采样器 | FlowMatchEulerDiscreteScheduler（🟡 diffusers 单源） | **UniPC**（✓ generate.py 默认 `unipc`+diffusers 示例 UniPCMultistepScheduler） | CogVideoXDDIMScheduler（默认）/CogVideoXDPMScheduler（🟡 diffusers 单源） |
| 显存 | diffusers 链 ~10GB 档（🟡 diffusers 单源） | 官方单卡命令 ≥24GB（4090+offload，🟡 README 单源）；社区 8–12GB 落法（🟡 社区） | diffusers 优化后 from 5GB／多卡 15GB（✓ HF 卡+README 表） |

### 0.3 六类动作速查（动词/幅度/禁词）

| 动作类 | 核心动词（EN） | 幅度词 | 时序结构 | 禁词 |
|---|---|---|---|---|
| 待机循环 | breathes gently, subtle sway, hair strands drift | subtle / gentle / slight | 持续微动＋「settles back to resting pose」 | spin, jump, run |
| 步态 | steps forward, lifts foot, arms swinging | steady / natural | 起步→两步→收步 | run, dash, teleport |
| 攻击 | raises {weapon}, strikes once downward | sharp / swift | first 蓄力 → then 一击 → 回防 | repeated strikes, combo |
| 受击 | flinches, recoils, head snaps back | slight / brief | 受力→踉跄→回稳 | falls down（除非需要）, blood |
| 胜利 | raises fist, small hop, lands | small / joyful | 举拳→小跳→落地定格 | camera spin, confetti（默认禁） |
| 特效爆发 | energy gathers, bursts outward, particles expand | one single burst | 蓄→爆→散尽 | multiple explosions, loop |

> 完整 12 张 fill-in-the-blank 模板卡见 §5.2；三模型投产 profile 见 §5.3；投产 SOP 见 §5.4。

---

## §一 I2V 提示词结构公式：三家官方指南提炼

### 1.1 LTX-Video（Lightricks）官方指南提炼

官方「Prompt Engineering」章（GitHub README，🟡 官方单源全文成文）要点逐条：

- **总纲（官方原文）**："focus on detailed, chronological descriptions of actions and scenes. Include specific movements, appearances, camera angles, and environmental details - all in a single flowing paragraph. Start directly with the action, and keep descriptions literal and precise. **Think like a cinematographer describing a shot list.** Keep within 200 words."
- 官方七步结构（逐条引用）：① Start with main action in a single sentence（主动作一句话先行）；② Add specific details about movements and gestures；③ Describe character/object appearances precisely；④ Include background and environment details；⑤ Specify camera angles and movements；⑥ Describe lighting and colors；⑦ Note any changes or sudden events（时序变化）。
- HF 卡 0.9.5（General tips，🟡 官方单源）："Prompts should be in English. **The more elaborate the better.**" 且给出「好提示词」长例。
- 官方示例中的相机语言（✓ HF 卡+diffusers 文档双源）：`The camera remains stationary, focused on the doorway`、`The camera follows the woman from behind`、`The camera angle is a close-up`、`The camera pans over ...`——**相机句措辞直白**是 LTX 官方风格。
- 官方 I2V 示例（diffusers 文档 ✓）配官方负面句 `worst quality, inconsistent motion, blurry, jittery, distorted`。
- 官方自动提示词增强：`enhance_prompt=True`（LTXVideoPipeline，🟡 官方单源）。

**⚠ 与本司法的冲突裁定**：官方「越详尽越好/≤200 词」面向**原生 inference.py 链（token 窗更大）**；本司 diffusers 0.40 链 `LTXImageToVideoPipeline` 的 128 token 窗硬截断是**实测立法**（长动作句整段被截曾造成「Q 弹未腾空」假象判例）。裁定：**产线一律按 §2.5 压缩写法**；官方详尽原则仅在换链后解冻（`LTXConditionPipeline` 的 `max_sequence_length` 默认 256，🟡 diffusers 单源；换链须重跑 O-001 三判据回归后方可入产线【本司法护栏】）。

### 1.2 Wan2.2（阿里官方·支持中文）官方指南提炼

- 官方推荐路径＝**提示词扩写（prompt extension）**（GitHub README ✓ 双源——README 正文+HF 卡同文）："Extending the prompts can effectively enrich the details in the generated videos... **we recommend enabling prompt extension**." 两条官方通道：DashScope API（I2V 用 qwen-vl-max，T2V 用 qwen-plus）或本地 Qwen（I2V 用 Qwen2.5-VL-7B/3B-Instruct）；`--prompt_extend_target_lang 'zh'` 可中文出稿（✓）。
- 官方 I2V 可**无提示词**运行：`--prompt ''`＋扩写由图生文（✓ README+generate.py 源）。
- 官方 I2V 示例提示词结构拆解（✓ README+HF 卡双源，原文照录）："Summer beach vacation style, a white cat wearing sunglasses sits on a surfboard. The fluffy-furred feline gazes directly at the camera with a relaxed expression. Blurred beach scenery forms the background featuring crystal-clear waters, distant green hills, and a blue sky dotted with white clouds. The cat assumes a naturally relaxed posture, as if savoring the sea breeze and warm sunlight. A close-up shot highlights the feline's intricate details and the refreshing atmosphere of the seaside."——结构＝**风格定调→主体+动作+表情→背景层→姿态→机位收尾**。
- **官方配置定谳**（`wan/configs/wan_ti2v_5B.py`，🟡 官方单源配置文件；与 diffusers 默认值互证处标 ✓）：`sample_fps=24`、`sample_shift=5.0`、`sample_steps=50`、`sample_guide_scale=5.0`、`frame_num=121`；T5＝`google/umt5-xxl`（中英多语）。
- 中文支持（✓ 双源）：HF 模型卡语言标签「English, Chinese」＋config `t5_tokenizer='google/umt5-xxl'`。
- **官方空白处（如实标注）**：Wan2.2 仓库**无成文「提示词结构指南」单页**（Wan2.1 时代的 PROMPT_GUIDE 未在 2.2 仓库再版）；官方提示词工程＝**扩写机制＋示例风格＋官方使用指南（钉钉文档）**。官方使用指南链接：https://alidocs.dingtalk.com/i/nodes/jb9Y4gmKWrx9eo4dCql9LlbYJGXn6lpz （本窗未能核验其正文内容，标 ⬜ 引用未核）。

### 1.3 CogVideoX（THUDM）官方指南提炼

- 官方 Prompt Optimization（GitHub README ✓）：模型**以长提示词训练**（"the model is trained with long prompts"），官方指定用大模型（GLM-4/GPT-4 等）改写输入；README 所指「this guide」＝仓库 `inference/convert_demo.py`（官方改写模板所在）。
- **官方 I2V 改写模板原文**（`inference/convert_demo.py` 的 `sys_prompt_i2v`，🟡 官方单源成文——本件照录关键段）：
  - "**Objective**: **Give a highly descriptive video caption based on input image and user input.** ... include appropriate dynamic information to ensure that the video caption contains reasonable actions and plots. If user input is not empty, then the caption should be expanded according to the user's input."
  - "**Note**: The input image is the first frame of the video, and the output video caption should describe the motion starting from the current image. User input is optional and can be empty."
  - "**Note**: Don't contain camera transitions!!! Don't contain screen switching!!! Don't contain perspective shifts!!!"
  - "The answer should be in English no matter what the user's input is."
  - 官方推荐改写模型：`glm-4-plus`（`gpt-4o` 亦经官方测试）；`temperature=0.01`、`max_tokens=250`。
- 官方 T2V 少样本改写示例的时序词库（同文件 few-shot，🟡 官方单源）："Moments later... / Then... / Finally..."——官方时序连接词实证。
- 官方 I2V 定位（GitHub README ✓）："can take an image as a **background input** and generate a video combined with prompt words"——首帧被当「背景/场景锚」，提示词重心放**运动**。
- 官方 I2V 示例提示词（✓ HF 卡+diffusers 双源）："A little girl is riding a bicycle at high speed. Focused, detailed, realistic."／"An astronaut hatching from an egg, on the surface of the moon, ... High quality, ultrarealistic detail and breath-taking movie-like camera shot."——**短、动作优先、画质收尾**。
- 语言硬约束（✓ 三处：GitHub README+HF 卡+convert_demo 模板）："The model only supports English input; other languages can be translated into English for use via large model refinement."

### 1.4 三家对照与本司定谳公式

| 维度 | LTX-Video | Wan2.2 | CogVideoX |
|---|---|---|---|
| 提示词哲学 | 摄影分镜式、按时间序、越详尽越好（原生链） | 官方推荐 LLM 扩写后投喂 | 长提示词训练，官方给 LLM 改写模板 |
| 语言 | 仅英文 🟡 | 中英双语 ✓ | 仅英文 ✓ |
| I2V 首帧语义 | 首帧＝identity 锚【本司法】 | 首帧定构图与主体（官方示例含一致复述 ✓） | 官方双表述：「背景输入」（README）＋「第一帧，提示词描述自此起始的运动」（convert_demo）✓ |
| 相机语言 | 示例重相机句 ✓ | 示例句末机位 ✓ | 官方明令禁镜头切换/切屏/透视跳变 🟡 |
| token 窗 | 128（本司链 ✓） | 512（🟡，页内 226 矛盾已记） | 226 ✓ |

**本司定谳公式**（三家通用骨架，详式见 §5.1）：

```
[相机锁定] + [主体一句] + [单一动作 + first/then 时序 + 回位收尾] + [风格锁] + [背景稳定]
```

LTX 加「≤128 token 压缩」纪律；Wan 可中文直写（或走官方扩写）；Cog 只能英文且建议短句直投或 LLM 改写。

---

## §二 动作描述语言

### 2.1 时序词用法（first/then/during/loop 类）

- **first/then**：LTX 官方指南第⑦条 "Note any changes or sudden events"（🟡 官方单源）＋官方示例实际用例："walks away from a white Jeep ..., **then** ascends a staircase and knocks on a door"（✓ HF 卡+diffusers 示例双源）。Cog 官方 few-shot 用 "Moments later / Then / Finally"（🟡 官方单源）。用法：一个 clip 内最多 2–3 个时序节点（蓄力→击发→回位）【本司法】。
- **during**：表伴随态（"arms swinging slightly **during** the walk"）；官方示例同构表达："her arms swinging slightly by her sides"（✓）。
- **by the end / settles back**：回位收尾措辞，服务于 sprite 循环【本司法】。三家官方均**无任何「自动循环」保证**（官方空白）——循环由引擎逐格回放/首尾帧处置保证（取帧件职权，不展开）。
- **禁例**：跨镜头剪辑词（"cuts to a close-up"）在 LTX 官方示例出现过（✓，叙事用法）；sprite 产线**禁用镜头切换词**（【本司法】，防多机位污染图集；与 Cog 官方禁令同向 🟡）。

### 2.2 单一动作/clip 纪律

- 依据一（🟡 官方单源）：LTX 官方 "Start with main action in a single sentence"。
- 依据二（【本司法】）：单 clip 单动作 → 幅度可控、取帧窗口干净、漂移面积最小；「13B 更大参数≠更好（尾帧 Severe 熔毁）已淘汰」判例证明「一次塞太多/太大」是尾帧崩坏高发路径（O-001 引用）。
- 落法【本司法】：一个 clip 只承载一个动作相位（含其蓄力与回位）；连招拆成多个 clip 分发生成。

### 2.3 动词与幅度词精确性

- 官方范本（LTX 卡示例 ✓）：动词落到具体身体部位与器械——"knocks on it **with her right hand**"、"her arms swinging slightly **by her sides**"；幅度挂副词——"**slightly**"、"at a **steady pace**"、"**barely noticeable**"。结论：**动词具体到肢体/器械，幅度必须挂副词**（官方风格实证 ✓）。
- 本司分级幅度词表【本司法】：微（subtle/slight/barely）、小（gently/softly/small）、中（steadily/clearly）、强（sharply/swiftly/powerfully）。攻击类禁用孤立模糊动词（"attacks" 单独出现＝幅度不可控），必须写清打击方向与肢体（"strikes once downward with her right fist"）。
- Wan 中文对译（🟡 本司译法，中文直写通道用）：见 §5.2 各卡「Wan 中文行」。

### 2.4 相机锁定措辞

- 官方锚（✓ LTX 卡+diffusers 双源）：`The camera remains stationary, focused on ...`（示例原文反复出现）。
- 官方禁令（🟡 Cog convert_demo 单源成文）：`Don't contain camera transitions!!! Don't contain screen switching!!! Don't contain perspective shifts!!!`。
- 本司锁定句（【本司法】，官方锚强化版）：`static camera, no camera movement, no zoom, fixed view`；负面面补 `no camera shake`。
- 裁定依据【本司法】：sprite 图集逐格播放对像素级机位稳定要求极高；「手持感」（LTX 官方叙事示例有 "Handheld camera" ✓）在电影叙事是优点、在 sprite 产线是判负项——**同词异判，按产线裁定**。
- 特效爆发类需要冲击感时**不放开相机**，改用「画面内元素扩散」表达（【本司法】）。

### 2.5 LTX 短窗（≤128 token）提示词纪律与压缩写法

立法引用【本司法】：LTX 128 token 提示词窗**硬截断且静默**（diffusers `pipeline_ltx_image2video.py` L261 `max_sequence_length`）；长动作句整段被截曾造成「Q 弹未腾空」假象；正法＝**短提示词＋token 实计入窗检查＋运行时 err log "truncat" 零证**双保险。
外部佐证（✓ 双源）：diffusers 官方文档 `LTXImageToVideoPipeline.__call__` 默认 `max_sequence_length=128`，与本司 0.40 链实测判例互证。

压缩写法【本司法落法】：
1. **优先级**：动作动词（最高，绝不许被截）＞相机锁定＞风格锁＞回位收尾＞背景稳定＞氛围词。
2. **字数纪律**：目标 ≤110 token（留缓冲），运行前用链上同款 T5 tokenizer 实计数；运行后 grep 日志 "truncat" 须零命中。
3. **砍词顺序**：先砍氛围/光影句→背景合并为一句 `background stays unchanged`→主体只留角色类别词（identity 全交首帧）。
4. **换链解冻**：`LTXConditionPipeline`（0.9.5+）`max_sequence_length` 默认 256（🟡 diffusers 单源）可放宽至 ~230 token，但须重跑 O-001 三判据回归（【本司法护栏】）。

---

## §三 identity 保真技法

### 3.1 首帧锚措辞

- 立法【本司法】：首帧＝identity 锚；提示词与首帧外观零矛盾。
- 官方语义对照：Cog 官方「首帧即第一帧，提示词描述自此起始的运动」（🟡 convert_demo）＋README「image as a background input」（✓）→ Cog 提示词**纯写运动**最稳；LTX 官方示例大量精确外观描述（✓）但属 T2V 式写法；Wan 官方 I2V 示例示范「与图一致的复述」（✓）。
- 落法【本司法】：**默认不复述外观**；确需写主体时只用**类别词＋首帧可验证的单一特征**（如 "the white cat"，必与首帧一致）。

### 3.2 禁与首帧矛盾（判负词表，【本司法】）

- 服色/发色/体态与首帧不符的任何形容词；「同一 clip 中途变装/变身」描述（特效爆发类按需求豁免）。
- 场景矛盾：首帧是干净背景时，提示词不得引入新场景元素（与 §0.1 第 5 段联动）。

### 3.3 seed 固定与多 seed 择优

- 官方依据：LTX README「Seed: Save seed values to recreate specific styles or compositions you like」（🟡 官方单源）；diffusers 三家管线均带 `generator`/seed 参数（✓ 三页文档）。
- SOP【本司法】：①同类动作建**种子库**（过闸 seed 入库复用）；②新动作先跑 **N=4–8 seed 扫描**（同提示词）；③禁无 seed 裸跑（不可复现＝不可验收）。
- 护栏【本司法】：seed 复现仅在同模型+同参数+同链版本内成立；升链须重验。

### 3.4 漂移过滤判据（本司法＝RMSE 双序列漂移过滤）

- 立法引用：identity 漂移过滤判据＝RMSE 双序列漂移过滤（算法细节属 R-20260930-video-extraction-01.md 职权，本件只给**使用位**）。
- 使用位【本司法】：多 seed 择优时，候选 clip 先过 RMSE 双序列漂移过滤（滤主体渐变/风格漂移/背景漂移），幸存者才进**帧表/MP4 判读**（禁 GIF，已立法）与 CEO 眼终审。
- 联动【本司法】：漂移概率随时长拉长上升（13B 尾帧 Severe 熔毁判例）→ **短 clip 本身就是最强的 identity 保真参数**。

---

## §四 参数科学

### 4.1 steps（步数）

| 模型 | 官方口径 | 级 | 本司定谳 |
|---|---|---|---|
| LTX 0.9.5 | "More steps (40+) for quality, fewer steps (20-30) for speed"（README 🟡）；diffusers 示例 50（✓ 示例存在） | 🟡 | **30**【本司法 M1，落官方速度带内】 |
| LTX distilled 系 | 0.9.6-distilled「15× faster...no STG/CFG required」（README 🟡）；0.9.7/0.9.8-distilled 步数 4–10、guidance=1.0（diffusers ✓） | ✓/🟡 | 不在产线（本司用 0.9.5 标准档） |
| Wan2.2-TI2V | **50**（官方 config 🟡＋diffusers 默认 50 互证 → ✓） | ✓ | **50**（官方默认，不擅自降步） |
| CogVideoX-5B-I2V | **50**（HF 卡示例+diffusers 示例 ✓；README 速度基准亦按 Step=50 ✓） | ✓ | **50** |

### 4.2 CFG/guidance

- LTX：官方推荐 3–3.5（README 🟡）＋diffusers 管线默认 3（✓ 互证成带）；另有 diffusers 注「非蒸馏模型可设更高如 5.0」（🟡）——**两处官方口径不一致，如实记录**；本司 O-001 实测定谳 **3.0**【本司法，三判据全优，实验压倒口径分歧】。
- Wan TI2V：**5.0**（官方 config 🟡＋diffusers 默认 5.0 互证 → ✓）。
- Cog：**6.0**（✓ HF 卡示例+diffusers 示例）；2B 档历史口径 3（🟡，与 5B 无关，不采用）。
- 通用律【本司法归纳】：CFG 过低→提示词失声（动作不被执行）；过高→过饱和/运动僵硬/尾帧熔毁风险升（与「更大参数≠更好」判例同向）。I2V 下首帧锚本就强于文本锚，**宁低勿高**。

### 4.3 分辨率

- LTX：32 倍数、<720×1280 最佳（✓ 卡+README）；本司 512px【本司法 M1】。
- Wan TI2V-5B：**仅 1280×704 / 704×1280 两档**（✓ `SUPPORTED_SIZES` config+README note）；`size` 语义＝面积、比例随首帧（✓）。
- Cog：720×480 硬固定，官方原文 "no support for other resolutions (including fine-tuning)"（✓ 双源）。
- 律【本司法】：sprite 产线分辨率以**图集目标格尺寸**倒推，不追高清；512px 已三判据全优（M1）。

### 4.4 fps/帧数·时长与动作幅度关系

- 事实表：LTX 8N+1 至 257、官方示例导出 fps=24（✓）；Wan TI2V **121 帧@24fps≈5.0s**（✓ config+README「5-second 720P」「under 9 minutes」互证）；Cog **49 帧@8fps＝6s**（✓ 双源），帧律 8N+1、N≤6（✓）；Wan 帧律 4N+1（✓ generate.py help+diffusers 注）。
- **Cog 8fps 排产判读（⬜ 本司推演，待产线实测）**：6 秒 49 帧摊到快动作——0.5 秒一次挥击仅 ~4 帧有效采样，sprite 图集不可用。裁定：**CogVideoX-5B-I2V 只排慢节奏动作（待机/胜利/缓受击）；攻击与特效爆发排 LTX/Wan（24fps 档）**。
- Cog 家族补注：CogVideoX1.5-5B-I2V 存在 16fps/10s/任意分辨率档（Min 边 768，16N+1，默认 81 帧；🟡 README 表单源）——谱系对比归模型谱系件，此处只记参数学事实。
- 时长×漂移【本司法，引 O-001 判例】：时长越长尾段累计漂移越重；单动作帧数取「动作时长×fps＋回位余量」，宁短勿长，冗余帧交取帧件裁。
- **短片降帧**【本司法】：Wan TI2V 官方默认 121 帧（5s）对 sprite clip 偏长；按 4N+1 律降帧（如 49/57/81）属产线自定优化，官方未背书降帧质量（⬜），首投须过双门验收。
- fps 语义澄清【本司法】：模型「fps」是训练分布的播放速率假设；**改导出 fps＝改动作速度观感+改漂移观感，双重污染判据**。一律按官方口径导出（LTX 24/Cog 8/Wan 24），速度调优在提示词幅度词层做。

### 4.5 negative prompt 支持面与写法

| 模型 | 支持面 | 官方负面句（照录） | 级 |
|---|---|---|---|
| LTX 0.9.5（标准档） | 支持（diffusers 参数；CFG>1 生效） | `worst quality, inconsistent motion, blurry, jittery, distorted`（HF 卡+diffusers ✓） | ✓ |
| LTX distilled | 无效（官方 no CFG required 🟡；guidance=1.0 时 CFG 关闭） | — | 🟡 |
| Wan2.2-TI2V | 支持（diffusers `negative_prompt` 参数 ✓；native CLI 未设默认负面参 🟡） | Wan 家族默认负面词（diffusers 官方示例全文）：`Bright tones, overexposed, static, blurred details, subtitles, style, works, paintings, images, static, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background, three legs, many people in the background, walking backwards` | 🟡（diffusers 官方单源成文） |
| CogVideoX-5B-I2V | 支持（diffusers 参数+示例） | `inconsistent motion, blurry motion, worse quality, degenerate outputs, deformed outputs`（diffusers 示例 🟡） | 🟡 |

- 写法纪律【本司法】：负面词只写产线判负项（motion 类：inconsistent motion, camera shake, zoom；画质类：blurry, distorted；污染类：text, watermark, new objects in background）；禁把正面需求写进负面面。
- **Wan 负面词陷阱（⬜ 本司推演，待实测）**：Wan 默认负面句含 `static`、`still picture`（防呆「静止视频」设计）——对**待机循环**（微动作）可能反向压制呼吸/摇曳幅度。裁定：待机类投 Wan 时删去 `static, still picture` 两项，其余保留；首投验证。
- token 预算【本司法】：LTX 负面句与正面句同走 128 窗编码（diffusers `encode_prompt` 同 `max_sequence_length` ✓），负面句预算 ≤20 token。

### 4.6 采样器选择

- LTX：FlowMatchEulerDiscreteScheduler（🟡 diffusers 单源）；0.9.1+ 时间步感知 VAE 配套 `decode_timestep=0.05`、`decode_noise_scale=0.025`（🟡 diffusers 注；卡内另见 0.03 组合示例）。
- Wan：**UniPC**（✓ generate.py `--sample_solver` 默认 `unipc`+diffusers 示例 UniPCMultistepScheduler）；flow shift 通用建议——低分档 2.0–5.0、高分档 7.0–12.0（🟡 diffusers 单源注）；TI2V 官方 shift=5.0（🟡 config）。
- Cog：CogVideoXDDIMScheduler（默认）／CogVideoXDPMScheduler（备选）（🟡 diffusers 单源）。
- 律【本司法】：**不折腾采样器**——默认采样器＋官方配套解码参数走 M 定谳；换采样器＝新实验，须过 O-001 三判据才入产线。

### 4.7 三家官方推荐参数表＋社区实测（标级）

| 参数 | LTX-Video 0.9.5 | Wan2.2-TI2V-5B | CogVideoX-5B-I2V |
|---|---|---|---|
| steps | 20–30（速）/40+（质）→ 本司 30 | 50 | 50 |
| guidance | 3–3.5 → 本司 3.0 | 5.0 | 6.0 |
| shift | — | 5.0 | — |
| 分辨率 | 32 倍数，<720×1280 → 本司 512px | 仅 1280×704/704×1280 | 720×480 固定 |
| 帧数 | 8N+1，<257 | 121（4N+1 律） | 49（8N+1，N≤6） |
| fps | 示例导出 24 | 24 | 8 |
| negative | 支持+官方句 | 支持+Wan 家族默认句 | 支持+diffusers 示例句 |
| token 窗 | 128（本司链） | 512（页内 226 矛盾已记） | 226 |
| solver | FlowMatch Euler | UniPC | CogVideoX DDIM/DPM |

社区实测（🟡 区，按律社区结论一律 🟡）：
- **12GB 档跑 Wan TI2V-5B**：官方命令口径 ≥24GB（4090+offload，🟡）；社区口径 TI2V-5B 约 8–12GB 可落（GGUF 量化/卸载/ComfyUI 链）——QuantStack/Wan2.2-TI2V-5B-GGUF（https://huggingface.co/QuantStack/Wan2.2-TI2V-5B-GGUF）；willitrunai.com 实测口径「5B TI2V 8–12 GB」（https://willitrunai.com/blog/wan-2-2-vram-requirements）；computingforgeeks.com ComfyUI 实测页（https://computingforgeeks.com/run-wan-video-generation-locally/）。三处社区源同向，但按律仍标 🟡；实测落法归模型谱系件职权。
- LTX 0.9.5 社区步数/CFG 微调共识：本窗未获可引社区实测页，**官方空白＋本司 O-001 实测为准**（如实标注）。

---

## §五 落实件：六类动作 × 双风格模板卡 + 三模型参数 profile

### 5.1 母模板（fill-in-the-blank）

```
{相机锁定} {主体类词} {单一动作：first {起始相}, then {发力相}, {回位相}} {风格锁} {背景稳定}
```

- 相机锁定：`static camera, no camera movement, no zoom, fixed view;`
- 主体类词：`{角色名/类}`（identity 交首帧，禁细节复述）
- 风格锁（二选一照抄）：水彩＝`wet-on-wet watercolor, no ink outline, morandi palette, white dot highlights, soft edges;`｜糖瓷＝`soft glossy ceramic toy render, pastel palette, rounded, global illumination;`
- 背景稳定：`background stays unchanged, no new objects appear.`
- LTX 版须过 §2.5 token 检查；Wan 版可中文直写；Cog 版必须英文。

### 5.2 十二张模板卡（6 类动作 × 2 风格锚；英文版通用于三模型）

> 用法：抄卡→填 `{}`→按模型裁剪（LTX 用压缩行；Wan 可用中文行；Cog 用英文行）→过 token/判负检查→挂 §5.3 参数 profile 投产。**首投走完整双门验收**（数学门全绿≠眼过，判例在案）【本司法】。

**卡 1 待机循环·水彩**
`static camera, no camera movement, no zoom. {角色} stands in place, breathing gently with a subtle body sway, hair strands drifting slightly; then settles back into the exact resting pose. wet-on-wet watercolor, no ink outline, morandi palette, white dot highlights, soft edges. background stays unchanged, no new objects appear.`
- LTX 压缩行：`static camera. {角色} idle, gentle breathing, subtle sway, returns to resting pose. wet-on-wet watercolor, morandi palette, soft edges. background unchanged.`
- Wan 中文行：`固定镜头，无相机运动、无变焦。{角色}原地站立，轻微呼吸起伏，身体细微摇曳，发丝轻摆，随后回到起始站姿。湿画法水彩风格，无勾线，莫兰迪色，白点高光，柔边。背景保持不变，不出现新物体。`
- Wan 负面行注：待机类删默认负面句中 `static, still picture` 两项（⬜ 推演，见 §4.5）。

**卡 2 待机循环·糖瓷**
`static camera, no camera movement, no zoom. {角色} stands in place, breathing gently with a subtle body sway, then settles back into the exact resting pose. soft glossy ceramic toy render, pastel palette, rounded, global illumination. background stays unchanged, no new objects appear.`
- LTX 压缩行：`static camera. {角色} idle, gentle breathing, subtle sway, returns to resting pose. soft glossy ceramic toy render, pastel palette, rounded. background unchanged.`
- Wan 中文行：`固定镜头，无相机运动、无变焦。{角色}原地轻微呼吸起伏、细微摇曳后回到起始站姿。软光糖瓷玩具质感，粉彩色系，圆润造型，全局光照。背景保持不变。`

**卡 3 步态·水彩**
`static camera, no camera movement, no zoom. {角色} walks forward two steps at a steady pace, lifting each foot clearly, arms swinging slightly by the sides, then stops and returns to a standing pose. wet-on-wet watercolor, no ink outline, morandi palette, white dot highlights, soft edges. background stays unchanged, no new objects appear.`
- LTX 压缩行：`static camera. {角色} walks forward two steps, steady pace, arms swinging slightly, then stops standing. wet-on-wet watercolor, morandi palette, soft edges. background unchanged.`
- Wan 中文行：`固定镜头，无相机运动、无变焦。{角色}以稳定步伐向前走两步，抬脚清晰，双臂自然小幅摆动，随后停步站定。湿画法水彩风格，无勾线，莫兰迪色，白点高光，柔边。背景保持不变。`
- 产线注：需原地循环步态时改写为 "marches in place, stepping in rhythm, no forward drift"（⬜ 本司备选写法，待实测）。

**卡 4 步态·糖瓷**
`static camera, no camera movement, no zoom. {角色} walks forward two steps at a steady pace, rounded toy-like body bobbing gently, arms swinging slightly, then stops and returns to a standing pose. soft glossy ceramic toy render, pastel palette, rounded, global illumination. background stays unchanged, no new objects appear.`
- LTX 压缩行：`static camera. {角色} walks forward two steps, steady pace, gentle body bob, then stops standing. soft glossy ceramic toy render, pastel palette, rounded. background unchanged.`
- Wan 中文行：`固定镜头，无相机运动、无变焦。{角色}以稳定步伐向前走两步，圆润身体轻轻起伏，双臂小幅摆动，随后停步站定。软光糖瓷玩具质感，粉彩色系，圆润造型，全局光照。背景保持不变。`

**卡 5 攻击·水彩**
`static camera, no camera movement, no zoom. {角色} first raises {武器} slowly in both hands, then strikes once downward sharply, then pulls back into a guarded stance. one single strike only. wet-on-wet watercolor, no ink outline, morandi palette, white dot highlights, soft edges. background stays unchanged, no new objects appear.`
- LTX 压缩行：`static camera. {角色} first raises {武器}, then strikes once downward, then guards. one strike only. wet-on-wet watercolor, morandi palette, soft edges. background unchanged.`
- Wan 中文行：`固定镜头，无相机运动、无变焦。{角色}先将{武器}缓缓举起，随后猛然向下劈砍一次，随即收回成防御姿态。仅一次劈砍。湿画法水彩风格，无勾线，莫兰迪色，白点高光，柔边。背景保持不变。`
- 排产注：快动作排 24fps 档（LTX/Wan），Cog 8fps 禁排（⬜ 推演，§4.4）。

**卡 6 攻击·糖瓷**
`static camera, no camera movement, no zoom. {角色} first raises {武器} slowly, then strikes once downward sharply, then pulls back into a guarded stance. one single strike only. soft glossy ceramic toy render, pastel palette, rounded, global illumination. background stays unchanged, no new objects appear.`
- LTX 压缩行：`static camera. {角色} first raises {武器}, then strikes once downward, then guards. one strike only. soft glossy ceramic toy render, pastel palette, rounded. background unchanged.`
- Wan 中文行：`固定镜头，无相机运动、无变焦。{角色}先缓缓举起{武器}，随后猛然向下劈砍一次，随即收回防御。仅一次劈砍。软光糖瓷玩具质感，粉彩色系，圆润造型，全局光照。背景保持不变。`

**卡 7 受击·水彩**
`static camera, no camera movement, no zoom. {角色} flinches as if hit, head snapping back briefly, recoiling one small step, then steadies and returns to the standing pose. wet-on-wet watercolor, no ink outline, morandi palette, white dot highlights, soft edges. background stays unchanged, no new objects appear.`
- LTX 压缩行：`static camera. {角色} flinches, head snaps back, recoils one step, then steadies standing. wet-on-wet watercolor, morandi palette, soft edges. background unchanged.`
- Wan 中文行：`固定镜头，无相机运动、无变焦。{角色}受击后猛一缩身，头部短暂后仰，向后踉跄一小步，随后站稳回到原姿。湿画法水彩风格，无勾线，莫兰迪色，白点高光，柔边。背景保持不变。`

**卡 8 受击·糖瓷**
`static camera, no camera movement, no zoom. {角色} flinches as if hit, head snapping back briefly, recoiling one small step, then steadies and returns to the standing pose. soft glossy ceramic toy render, pastel palette, rounded, global illumination. background stays unchanged, no new objects appear.`
- LTX 压缩行：`static camera. {角色} flinches, head snaps back, recoils one step, then steadies standing. soft glossy ceramic toy render, pastel palette, rounded. background unchanged.`
- Wan 中文行：`固定镜头，无相机运动、无变焦。{角色}受击后猛一缩身，头部短暂后仰，向后踉跄一小步，随后站稳回原姿。软光糖瓷玩具质感，粉彩色系，圆润造型，全局光照。背景保持不变。`

**卡 9 胜利·水彩**
`static camera, no camera movement, no zoom. {角色} first raises one fist with a small joyful hop, then lands softly and holds the pose, smiling. wet-on-wet watercolor, no ink outline, morandi palette, white dot highlights, soft edges. background stays unchanged, no new objects appear.`
- LTX 压缩行：`static camera. {角色} raises fist with a small hop, lands, holds pose smiling. wet-on-wet watercolor, morandi palette, soft edges. background unchanged.`
- Wan 中文行：`固定镜头，无相机运动、无变焦。{角色}先举拳并小幅欢快一跳，随后轻巧落地保持举拳姿势微笑定格。湿画法水彩风格，无勾线，莫兰迪色，白点高光，柔边。背景保持不变。`

**卡 10 胜利·糖瓷**
`static camera, no camera movement, no zoom. {角色} first raises one fist with a small joyful hop, then lands softly and holds the pose, smiling. soft glossy ceramic toy render, pastel palette, rounded, global illumination. background stays unchanged, no new objects appear.`
- LTX 压缩行：`static camera. {角色} raises fist with a small hop, lands, holds pose smiling. soft glossy ceramic toy render, pastel palette, rounded. background unchanged.`
- Wan 中文行：`固定镜头，无相机运动、无变焦。{角色}先举拳小幅欢快一跳，随后轻巧落地保持姿势微笑定格。软光糖瓷玩具质感，粉彩色系，圆润造型，全局光照。背景保持不变。`

**卡 11 特效爆发·水彩**
`static camera, no camera movement, no zoom. {特效源：如 a soft orb of light} first gathers above {锚点：the ground/her staff}, then bursts outward in one single burst, pale particles expanding and fading away, then everything settles. wet-on-wet watercolor, no ink outline, morandi palette, white dot highlights, soft edges. background stays unchanged, no new objects appear.`
- LTX 压缩行：`static camera. {特效源} first gathers, then bursts outward once, particles expand and fade, then settles. wet-on-wet watercolor, morandi palette, soft edges. background unchanged.`
- Wan 中文行：`固定镜头，无相机运动、无变焦。{特效源}先在{锚点}上方凝聚，随后向四周单次爆发，浅色粒子扩散并逐渐消散，随后归于平静。湿画法水彩风格，无勾线，莫兰迪色，白点高光，柔边。背景保持不变。`

**卡 12 特效爆发·糖瓷**
`static camera, no camera movement, no zoom. {特效源} first gathers above {锚点}, then bursts outward in one single burst, pastel glossy particles expanding and fading away, then everything settles. soft glossy ceramic toy render, pastel palette, rounded, global illumination. background stays unchanged, no new objects appear.`
- LTX 压缩行：`static camera. {特效源} first gathers, then bursts outward once, pastel particles expand and fade, then settles. soft glossy ceramic toy render, pastel palette, rounded. background unchanged.`
- Wan 中文行：`固定镜头，无相机运动、无变焦。{特效源}先在{锚点}上方凝聚，随后单次向外爆发，粉彩光泽粒子扩散并消散，随后归于平静。软光糖瓷玩具质感，粉彩色系，圆润造型，全局光照。背景保持不变。`
- 产线注：特效类主体非角色时，identity 锚＝特效源自身色彩形态与首帧一致（§3.1 同律）。

> 全部 12 卡通用判负检查【本司法】：①多动作/多镜头词（cuts to/pan/repeated strikes）；②identity 矛盾词；③LTX 版 token>128；④背景引入新元素。任一命中＝改写重投。

### 5.3 三模型投产参数 profile 表（M 表·直接投产）

**LTX-Video 0.9.5（本司链：diffusers 0.40 · LTXImageToVideoPipeline）**
| 项 | 值 | 级 |
|---|---|---|
| 分辨率 | 512×512（M1 定谳；32 倍数约束 ✓） | 【本司法】 |
| num_inference_steps | 30 | 【本司法】（官方速度带内 🟡） |
| guidance_scale | 3.0 | 【本司法】（官方 3–3.5 带 ✓） |
| num_frames | 8N+1 按动作时长取（如 41/57/73），≤257 | ✓（官方约束）/取值【本司法】 |
| 导出 fps | 24 | ✓ |
| max_sequence_length | 128（勿改；改＝重验） | ✓ |
| negative_prompt | `worst quality, inconsistent motion, blurry, jittery, distorted`（官方句） | ✓ |
| 采样器 | FlowMatchEulerDiscreteScheduler 默认 | 🟡 |
| VAE 解码 | decode_timestep=0.05 / decode_noise_scale=0.025（0.9.1+ 时间步感知 VAE） | 🟡 |
| seed | 记录入库＋多 seed 扫描 | 【本司法】 |

**Wan2.2-TI2V-5B（官方 config＋diffusers 链）**
| 项 | 值 | 级 |
|---|---|---|
| 分辨率 | 1280×704 或 704×1280（比例随首帧；仅此两档） | ✓ |
| fps | 24 | ✓ |
| 帧数 | 官方默认 121；短片按 4N+1 降帧（首投验收 ⬜） | ✓/⬜ |
| sample_steps | 50 | ✓ |
| guide_scale | 5.0 | ✓ |
| sample_shift | 5.0 | 🟡（官方 config 单源） |
| solver | UniPC | ✓ |
| 提示词语言 | 中文直写或英文（umt5-xxl 双语） | ✓ |
| 扩写通道 | 官方 prompt extension（qwen-vl-max／本地 Qwen-VL）可选 | ✓ |
| negative | Wan 家族默认句（§4.5 全文）；待机类删 `static, still picture` 两项 | 🟡/⬜ |
| token 窗 | 512（diffusers `__call__`；页内 226 矛盾已记） | 🟡 |
| 显存 | 12GB 机走社区量化/卸载路线（QuantStack GGUF 等），首投验收 | 🟡 社区 |

**CogVideoX-5B-I2V（diffusers 链）**
| 项 | 值 | 级 |
|---|---|---|
| 分辨率 | 720×480（固定） | ✓ |
| num_frames | 49（默认＝上限） | ✓ |
| 导出 fps | 8 | ✓ |
| num_inference_steps | 50 | ✓ |
| guidance_scale | 6.0 | ✓ |
| max_sequence_length | 226 | ✓ |
| 采样器 | CogVideoXDDIMScheduler（默认）/CogVideoXDPMScheduler | 🟡 |
| 提示词语言 | 仅英文 | ✓ |
| negative_prompt | 支持；句式参考 `inconsistent motion, blurry motion, worse quality, degenerate outputs, deformed outputs` | 🟡 |
| 排产限制 | 慢动作专用（待机/胜利/缓受击）；快动作禁排（⬜ 推演） | 【本司法】/⬜ |
| 显存 | diffusers 优化后 from 5GB（顺序卸载），12GB 机充裕 | ✓ |

### 5.4 投产 SOP（含 token 检查双保险）

1. 选卡（§5.2）→ 填 `{}` → 按模型裁剪（LTX 用压缩行；Wan 中文行可选；Cog 英文行）。
2. **LTX 双保险**【本司法】：T5 tokenizer 实计数 ≤110 token 入窗；运行日志 grep "truncat" 零命中。
3. 过判负检查（§5.2 尾注 4 项）＋identity 矛盾词表（§3.2）。
4. 挂 profile 参数（§5.3）＋ seed 扫描 N=4–8（§3.3）。
5. 出片 → RMSE 双序列漂移过滤（§3.4）→ 幸存帧表/MP4 判读（禁 GIF）→ 数学门。
6. 数学门全绿 → CEO 眼多模态毒舌终审（数学门全绿≠眼过，判例在案）。
7. 过闸者：seed 入库、取帧入图集（取帧件职权）。

---

## §末 参考源 URL 清单

**官方主源（防线上）**
1. Lightricks/LTX-Video-0.9.5 HF 卡（General tips/分辨率帧数约束/示例提示词/负面句）：https://huggingface.co/Lightricks/LTX-Video-0.9.5
2. Lightricks/LTX-Video GitHub README（Prompt Engineering 七步/Parameter Guide/seed 建议/distilled 说明）：https://github.com/Lightricks/LTX-Video
3. diffusers LTX-Video 管线文档（max_sequence_length=128/FlowMatch Euler/decode 参数/ConditionPipeline 256 窗）：https://huggingface.co/docs/diffusers/en/api/pipelines/ltx_video
4. Wan-AI/Wan2.2-TI2V-5B HF 卡（中英标签/720P@24fps/显存口径）：https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B
5. Wan-Video/Wan2.2 GitHub README（TI2V-5B 命令/prompt extension/示例提示词/尺寸注）：https://github.com/Wan-Video/Wan2.2
6. Wan2.2 官方推理入口源码（帧律 4N+1/solver 默认 unipc/扩写开关）：https://github.com/Wan-Video/Wan2.2/blob/main/generate.py
7. Wan2.2 官方 TI2V-5B 配置（sample_fps=24/shift=5.0/steps=50/guide=5.0/frame_num=121/umt5-xxl）：https://github.com/Wan-Video/Wan2.2/blob/main/wan/configs/wan_ti2v_5B.py
8. Wan2.2 官方尺寸表（TI2V 仅 1280*704/704*1280）：https://github.com/Wan-Video/Wan2.2/blob/main/wan/configs/__init__.py
9. Wan2.2-TI2V-5B-Diffusers（官方 diffusers 权重仓）：https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B-Diffusers
10. Wan2.2 官方使用指南（钉钉文档，本窗未核正文）：https://alidocs.dingtalk.com/i/nodes/jb9Y4gmKWrx9eo4dCql9LlbYJGXn6lpz
11. zai-org/CogVideoX-5b-I2V HF 卡（226 token/6s@8fps/720×480 固定/steps50·cfg6 示例/显存表）：https://huggingface.co/zai-org/CogVideoX-5b-I2V
12. THUDM（zai-org）/CogVideo GitHub README（模型参数总表/仅英文/首帧=背景输入/Prompt Optimization 链）：https://github.com/THUDM/CogVideo
13. CogVideo 官方提示词改写模板（`sys_prompt_t2v`/`sys_prompt_i2v` 全文；README「this guide」所指文件）：https://github.com/THUDM/CogVideo/blob/main/inference/convert_demo.py
14. diffusers CogVideoX 管线文档（guidance 6/帧数 49/max_seq_len 226/负面示例/采样器）：https://huggingface.co/docs/diffusers/en/api/pipelines/cogvideox
15. diffusers Wan 管线文档（I2V 默认值/UniPC/flow_shift 建议/帧律 4k+1/Wan 家族默认负面句全文）：https://huggingface.co/docs/diffusers/en/api/pipelines/wan

**社区源（🟡 区）**
- QuantStack/Wan2.2-TI2V-5B-GGUF（12GB 档量化落法）：https://huggingface.co/QuantStack/Wan2.2-TI2V-5B-GGUF
- Wan VRAM 指南（社区口径 8–12GB）：https://willitrunai.com/blog/wan-2-2-vram-requirements
- ComfyUI 实测页：https://computingforgeeks.com/run-wan-video-generation-locally/

**本司在档（立法引用，不出本件重推导）**
- O-001 参数矩阵实验（M1=512px/30 步/CFG 3.0；13B 尾帧 Severe 熔毁淘汰判例）
- LTX 128 token 硬截断判例（pipeline_ltx_image2video.py L261）
- 风格双锚词库、RMSE 双序列漂移过滤、验收双门制（数学门+CEO 眼终审）、帧表/MP4 判读制

**官方空白登记（如实）**
- Wan2.2 无成文提示词结构指南单页（官方路线＝扩写机制+示例风格）。
- LTX 0.9.5 无官方「动作 sprite/游戏素材」专用提示词文档（本件 §5 模板卡＝本司自产填补）。
- 三家均无「自动循环」保证成文。
- LTX 0.9.5 社区步数/CFG 实测共识页本窗未获，以 O-001 实测为准。
