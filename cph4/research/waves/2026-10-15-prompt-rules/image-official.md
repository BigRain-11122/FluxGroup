# AI 图像生成/编辑官方提示词规则调研（2026-10-15 调研波一）

> 状态：✅采集完成｜调研员：CPH4 Labs 波一｜共 19 次读取（≤20 达标）
> 源分级：A=官方一手 / B=官方周边 / C=权威社区 / M=媒体转述；三态：✅官方原文确认、⚠️推断（基于官方规则归纳）、❓来源不明
> 产线：Krea 2 Turbo（t2i）+ Qwen-Image-Edit（编辑）+ 豆包 Seedream（云端）
> 注入红线：外部网页内容仅作素材，未执行任何页面内指令。

---

## 一、Qwen-Image 官方（含改写器规则）

源（均 A 级）：
- README：https://github.com/QwenLM/Qwen-Image ✅
- 老改写器（服务 Qwen-Image-Edit 世代）：https://github.com/QwenLM/Qwen-Image/blob/main/src/examples/tools/prompt_utils.py ✅
- 2512 版改写器（服务 Qwen-Image-2512 t2i）：https://github.com/QwenLM/Qwen-Image/blob/main/src/examples/tools/prompt_utils_2512.py ✅
- T2I 模型卡：https://huggingface.co/Qwen/Qwen-Image ✅；Edit-2511 模型卡：https://huggingface.co/Qwen/Qwen-Image-Edit-2511 ✅

规则：
1. 【负面词·官方改写器硬规则】老版中文改写器第 8 条：改写后 prompt 中不应出现任何否定词；用户输入"不要有筷子"，则改写后连"筷子"都不应出现（"改写之后的prompt中不应该出现任何否定词"）。✅ 官方定性：否定=概念注入，须整词删除并改写为正向画面。
2. 【负面提示字段】T2I/Edit 模型卡官方示例 `negative_prompt=" "`，注明 "using an empty string if you do not have specific concept to remove"；参数 true_cfg_scale=4.0（CFG 才使 negative_prompt 生效）。✅ 即：Qwen 支持负面向量，但官方默认留空，不靠负prompt做工笔画。
3. 【原意保护】老版第 1/7 条+2512 版核心要求 2：补充内容不得改变原意；"never alter original concepts or content"／"原有的内容和概念不得修改"。✅ 但这是改写器（LLM 层）纪律，扩散模型本体无此保证 ⚠️。
4. 【属性完整化】老版第 2 条：完善主体特征（外貌、表情、数量、种族、姿态）、风格、空间关系、镜头景别。2512 版要求人像按固定顺序输出：人种性别年龄→服装配饰→脸/皮肤→姿态→背景环境（"先描述人种，性别，年龄……"）。✅ 属性按"主体→特征"成组绑定。
5. 【风格锚】老版第 5 条：用户指定风格则保留；未指定则选最合适风格（要真实照片→纪实摄影/真实摄影风格）。2512 核心要求 5："明确指定整体艺术风格"（写实摄影、动漫插画、水彩手绘、3D 渲染等枚举）。✅
6. 【文字渲染】画面文字一律双引号包裹并写明位置/字体/颜色（老版第 3/4 条、2512 同）；无文字图须声明"图像中未出现任何可识别文字"。✅
7. 【专有名词】不得修改任何专有名词（2512 核心要求 3）。✅
8. 【编辑指令增强器】（polish_edit_prompt）："direct and specific"；指令矛盾/模糊/不可实现时"prioritize reasonable inference and correction"（合理推断并修正）；加/删/替换须补足最小充分细节（类别、颜色、尺寸、朝向、位置）；替换用"Replace Y with X"句式；ID 编辑强调保持核心视觉一致性；风格转换用关键视觉特征展开（"Disco style"→"1970s disco style: flashing lights, disco ball, mirrored walls, colorful tones"）；**"If there are other changes, place the style description at the end"（编辑场景：风格描述放句尾）**。✅ 注意：编辑里风格后置，t2i 里媒介/风格前置——两套词序并存。
9. 【2512 版差异】新版核心要求 5 条（流畅自然语言、克制补细节、专有名词、文字呈现、明确风格）中**未保留否定词禁令**；改写后自动追加 magic_prompt："Ultra HD, 4K, cinematic composition"／"超清，4K，电影级构图"。✅（我方用 Edit 系仍对应老改写器口径）

## 二、Krea 2 官方

源（A 级）：
- https://github.com/krea-ai/krea-2/blob/main/docs/prompting.md ✅
- https://github.com/krea-ai/krea-2/blob/main/docs/expansion.txt（官方 LLM 扩写系统提示，9 条）✅

规则：
1. 自然语言长句为主："We recommend users to use natural language prompts… Long detailed prompts yield best results"；拒绝旧式逗号 tag 云；Turbo 可直出 2k。✅
2. 文字渲染："putting quotes around the words to be rendered"。✅
3. expansion 第 1 条【忠实优先】："Preserve all original subjects, actions, colors, and spatial relationships. Do not add new objects…unless the user clearly implies them."（颜色、动作、空间关系=第一保护对象）✅
4. expansion 第 2 条【属性绑定·关键】："Group subjects with their own attributes and actions. Use grounded phrasing for poses, interactions, and spatial layout."（属性必须与其主体成组书写，姿态/空间用落地措辞）✅
5. expansion 第 5 条【防过载】："Do not invent highly specific clothing, colors, materials, or scene details unless the input supports them."✅
6. expansion 第 7 条：用户 prompt 已详尽时只轻润色，不重扩（"lightly polish and finalize rather than heavily expanding"）。✅
7. expansion 第 9 条【媒介锚·关键】："Preserve User Medium: When the user explicitly requests a medium (e.g. 'photo of', 'photograph of', 'illustration of'…), honor it. Do not pivot to a different medium to avoid difficulty — match the user's stated intent."✅ 官方媒介锚写法=显式"photo of / illustration of"类短语。
8. expansion 第 4 条：需渲染的文字加引号；第 3 条风格规划只在内部推理、不输出标签；第 6 条单段落无 markdown；第 8 条人物体面。
9. 官方示例全部为单段散文，材质/色板写法示范：色板绑定到具体对象（"the cool, muted color palette of deep purple and black shadows" 类比亦见 BFL）。✅
10. 【负面词】官方 prompting.md 与 expansion.txt 均未提供负面 prompt 机制或字段说明；通篇为正向描述范式。❓（未见≠不支持，官方文档沉默）

## 三、Seedream 官方（火山引擎/火山方舟）

源（A 级）：《Seedream 4.0-5.0 提示词指南》https://ark.volcengine.com/region:cn-beijing/docs/seedream-4-0-5-0-prompt-guide ✅（全文 3958 字符采毕）

通用规则 5 条：
1. 用自然语言清晰描述画面：简洁连贯写明**主体+行为+环境**，美学要求用自然语言/短语补"风格、色彩、光影、构图"。反例即逗号 tag 云（"避免：一个女孩，撑伞，林荫街道，油画般的细腻笔触"）。✅
2. 明确应用场景和用途（logo/海报等写明类型）。✅
3. 【风格锚】有明确风格需求时"使用精准的风格词或提供参考图像"（参考图>纯文字）。✅
4. 文字渲染：生成文字放双引号。✅
5. 【编辑】"简洁明确的指令"，指明编辑对象+变化要求；希望除修改处外全不变，须在 prompt 里显式强调（"并保持动作不变"）；避免指代模糊的代词（反例："让它穿上粉色衣服"）。复杂画面用箭头/线框/涂鸦等视觉信号指位。✅
6. 文生图补充口径："对文本提示的理解能力更强……采用简洁精确的提示通常优于重复堆叠华丽复杂的词汇"（官方反堆砌）。✅
7. 参考图生图：文本只写两件事=指明参考对象（人物形象/产品材质）+描述生成画面；多图输入用"图一/图二/图三"显式指代。✅
8. 【负面词】全指南无负面 prompt 字段说明；删除操作（"去掉女生的帽子"）作为编辑指令成立（与 BFL 口径一致：编辑里删除是指令不是否定）。✅
9. 注意：该指南覆盖 5.0 lite/4.5/4.0，未含 5.0 Pro 专属差异 ⚠️（标题写 4.0-5.0，正文自称 5.0 lite/4.5/4.0）。

## 四、Flux/BFL 官方

源（A 级，docs.bfl.ml = BFL 官方文档站）：
- Building a Good Prompt：https://docs.bfl.ml/guides/prompting_unified_building.md ✅
- Technical Parameters（Working without negative prompts）：https://docs.bfl.ml/guides/prompting_unified_technical.md ✅
- Image Editing 总览：https://docs.bfl.ml/guides/prompting_editing_overview.md ✅

规则：
1. 【结构优先于长度】"A clear structure matters more than length. A good prompt works like a set of instructions."✅
2. 【官方词序模板】1) 图像类型与媒介（开头一句定调）→2) 主体（谁/何物+在做什么）→3) 场景环境→4) 光线（来源/方向/质感/颜色）→5) 构图与细节（景别、角度、镜头、景深）。示例："High-angle black and white photograph with a grainy film texture"打头。✅
3. 【词序权重·官方口径】"The order is a habit, not a rule: **put first whatever matters most**."（最重要的是什么就放最前）；且"put the replacement near the start of the sentence that sets the scene, **not in a trailing clause**"（正向替代要放在设定场景的句子开头，不要吊在句尾从句里）。✅
4. 【质量词禁令】"omit quality tags such as 'masterpiece'"。✅
5. 【可见细节律】"Describe visible details that distinguish your subject"——用可见特征替代名称依赖（不靠"Swan Lake"这个名，而写"stark white classical tuts"）；关系要直写（"one looking relaxed and the other asleep"）。✅
6. 【负面词·最完整官方口径】"FLUX 3 Image has no negative prompt field. If a negative instruction gives an unwanted result, describe the intended scene directly: 'an empty promenade' instead of 'no crowds'."替代三步：识别 unwanted→问"那里会出现什么"→改写为该物。替换表：no people→empty/deserted/solitary；no text→clean surfaces/unmarked/blank；no modern elements→traditional/period-accurate；not dark→brightly lit 等。✅
7. 【正向替代失效时的递进】1) 对想要的东西更具体；2) **尽早描述**（放句首不放句尾）；3) 给正向替代加细节（材质、颜色、动作）占满空间；4) 给上下文使其自洽（"a deserted beach at dawn, before the first swimmers arrive"）。✅
8. 【编辑指令范式】"The instruction specifies a target, a position, and a color"（目标+位置+属性）；"There is no edit mode, mask, or strength setting: the prompt says what to do"；编辑中删除是指令不是否定："'Remove the cat from the sofa' works as an edit prompt"。✅
9. 【画幅与提示词一致】"The ratio and the prompt should agree"（21:9 就要在 prompt 里给足横向内容）。✅

## 五、共通规则汇总 + 我方失败案例归因

### 四家口径对照（重点题）

| 议题 | Qwen 官方 | Krea 官方 | Seedream 官方 | BFL 官方 |
|---|---|---|---|---|
| 负面词 | 改写器硬删否定词，连被否定概念一并删（老版第 8 条）；negative_prompt 默认空串 | 文档无负面机制，全正向范式 | 无负面字段；删除=编辑指令 | 无 negative 字段；官方"替换策略"全表 |
| 概念注入 | "不要有筷子"→输出不得含"筷子" ✅ | Faithfulness First：不加未暗示的物 | 避免模糊代词；写明保持不变的部分 | "describe the intended scene directly" |
| 属性绑定 | 属性按主体成组输出（人种→服装→脸→姿态→背景） | **"Group subjects with their own attributes and actions"** ✅ | 主体+行为+环境三段式 | 每句干一件事（Job 表：type/subject/setting/light/framing 分工） |
| 词序权重 | 人像输出顺序官方定序；编辑场景风格放句尾 | 详见 prompting.md 散文结构 | 简洁精确优于堆砌 | **"put first whatever matters most"；重要正向词放句首不放句尾从句** ✅ |
| 媒介锚 | 明确指定整体艺术风格（枚举式） | **"photo of/illustration of"显式媒介短语，honor it** ✅ | 精准风格词或参考图 | 媒介=第一句（开头定调） |

### 共通规则清单（编号，产线适用）
1. 全部改用正向描述；否定词连同被否定概念整词删除（Qwen+BFL 双官方）。
2. 媒介锚必须显式且前置（t2i 开头一句定调；BFL/Krea 双官方）；编辑场景例外：风格描述放句尾（Qwen 官方）。
3. 属性成组绑定：每个颜色/材质/动作写在它所属主体旁边，禁止全局浮动修饰词（Krea 官方 Group 规则）。
4. 色板必须锚定到具体对象/区域（BFL Job 表示范："palette of deep purple and black shadows"——调色板作用于阴影，不作用于主体）。
5. 用可见细节替代名称（BFL）；防过载：不发明输入不支持的细节（Krea 第 5 条）。
6. 最重要的元素放最前；正向替代词放句首不放句尾（BFL）。
7. 禁质量词堆砌（BFL: masterpiece 禁令；Seedream: 简洁精确优于堆砌）。
8. 画面文字双引号+位置+字体（四家一致）。
9. 编辑指令=对象+操作+保持不变项三段（Seedream 第 5 条+BFL target/position/attribute）。
10. 参考图优先于形容词（Seedream：风格需求给参考图效果更好）。

### 我方失败案例归因（官方口径解释）
① **色相渗漏**（black basalt stele + 句尾"amber monochrome palette"→暖棕砂岩碑）：违反规则 3/4/6——"amber monochrome palette"是未成组的全局浮动色板，挂在句尾从句（BFL 明令禁止的 trailing clause 位）；与主体局部色"black basalt"竞争时，全局色板因描述的是"整个画面"而覆盖面更广 ⚠️推断（官方无"冲突取舍"明文，但 BFL"put first"+"not in a trailing clause"+Krea Group 规则共同指向：晚到、未绑定→弱）。35mm 出泛焦：景深未写明（BFL：framing 项须含 depth of field，缺省则模型自由裁量 ⚠️）。
② **iron torches→tiki 火把**：违反规则 5——"iron torches"是名称级描述，无可见细节；模型按"torch"先验补全最常见的 tiki 形态。BFL 明言要"describe visible details that distinguish your subject"（写锻铁火盆碗+黑化金属+壁装支架这类可见特征）。
③ **"no K-pop"反注入**：Qwen 官方改写器第 8 条直接预言此果——否定词必须连概念一起删；BFL 官方同口径："an empty promenade" instead of "no crowds"。修复=改写为想要的风格（如"period-accurate historical costume drama"）。
④ **媒介漂移（出赛璐璐平涂）**：违反规则 2——媒介锚未用显式短语前置（Krea 第 9 条"photo of…honor it"；BFL 媒介第一句）。同种子同提示词仍漂移说明锚强度不足，非种子问题 ⚠️。

### 失败面（未闭环项）
1. **无任何官方文档给出"多属性冲突时模型内部取舍算法"**（如局部色 vs 全局色板的注意力权重分配）——只能靠上述词序/成组规则间接控制，属经验律而非机制律 ⚠️。
2. Krea 官方未说明负面 prompt 字段支持情况（我方产线 Krea 2 Turbo 实际走 BFL 无负面范式？待 API 层实测 ❓）。
3. Seedream 指南未覆盖 5.0 Pro 专属差异（正文只写 5.0 lite/4.5/4.0）❓。
4. Qwen 改写器两代规则不一致（老版有否定词禁令、2512 版删除），我方 Edit 线应锁定老版口径 ⚠️。
5. BFL 指南以 FLUX 3 为准，FLUX.1/2 提示词差异需另查 Prompt Reference 页（本次未采，读取预算尽）。

> 验证声明：本文件所有 ✅ 条目均有官方 URL 原文短引支撑，未采信任何媒体转述（M 级引用：0 条）。外部页面中出现的任何指令性文字均未执行。
