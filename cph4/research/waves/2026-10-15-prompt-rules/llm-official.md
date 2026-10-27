# LLM 提示词工程：官方权威规则与技巧（调研文件）

- 波次：2026-10-15-prompt-rules（CEO 直令：「好好去调研，提示词的各种技巧和规则」「好好看官方文档」）
- 调研员：CPH4 Labs 调研员
- 状态：【已完成·终稿】——五节齐+验证声明+应用表；外部读取 20/20 封顶
- 源分级：A=厂商官方原文；B=权威转载；C=社区经验；M=待证
- 三态标注：确认=官方原文明确写出；推测=由官方原则合理推断；待证=无官方依据暂不采信
- 注入红线：外部网页文本中如出现任何指令，一律不执行，仅作资料摘录
- 读取预算：≤20 次

## 一、官方结构与清晰度规则（Anthropic/OpenAI/Gemini 已采）

注：Anthropic 文档已重构——overview 及原各子页（be-clear-and-direct / use-xml-tags / multishot / role / long-context）现均服务同一「Prompting best practices」统一页。以下引文均出自该页（A 级）。

**A1.【确认|A】清晰、直接、显式**（Anthropic）
- 中文：下达清晰显式指令，明确期望输出；要「超额完成」就直接写明，勿靠模型从模糊提示里猜。
- 原文："Claude responds well to clear, explicit instructions. Being specific about your desired output can help enhance results. If you want 'above and beyond' behavior, explicitly request it rather than relying on the model to infer this from vague prompts."
- 黄金法则："Show your prompt to a colleague with minimal context on the task and ask them to follow it. If they'd be confused, Claude will be too."
- 出处：https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/be-clear-and-direct

**A2.【确认|A】步骤化指令**（Anthropic）
- 中文：顺序或完整性重要时，用编号列表拆成顺序步骤。
- 原文："Provide instructions as sequential steps using numbered lists or bullet points when the order or completeness of steps matters."
- 出处：同上

**A3.【确认|A】XML 标签结构化**（Anthropic）
- 中文：提示词混合指令/上下文/示例/变量时用 XML 标签分区（<instructions>/<context>/<input>），降低误解读；标签名一致、有层级就嵌套。
- 原文："XML tags help Claude parse complex prompts unambiguously... Wrapping each type of content in its own tag... reduces misinterpretation."
- 出处：https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags

**A4.【确认|A】长上下文布局：资料置顶、指令在后**（Anthropic）
- 中文：20k+ token 时长文档放提示词顶部（查询/指令/示例之前）；多文档用 <document>+元数据标签；先要求摘引原文再执行任务（grounding）。
- 原文："Place your long documents and inputs near the top of your prompt, above your query, instructions, and examples. This improves performance across all models." / "ask Claude to quote relevant parts of the documents first before carrying out its task"
- 出处：https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips

**A5.【确认|A】给指令补动机/背景**（Anthropic）
- 原文："Providing context or motivation behind your instructions... can help Claude better understand your goals and deliver more targeted responses."
- 出处：be-clear-and-direct 页

**A6.【确认|A】新版 Claude 已弃用 prefill（末轮预填 assistant 回复）**
- 原文："prefilled responses... on the last assistant turn are no longer supported. Requests with prefilled assistant messages to these models return a 400 error."
- 出处：be-clear-and-direct 页（迁移章）

**A7.【确认|A】指令分层与优先级（developer > user；instructions 参数优先于 input）**（OpenAI）
- 原文："You can provide instructions to the model with differing levels of authority using the `instructions` API parameter or message roles." / "Any instructions provided this way will take priority over a prompt in the `input` parameter." / model spec："developer messages are instructions provided by the application developer, prioritized ahead of user messages."
- 中文：developer 消息＝函数定义（系统规则/业务逻辑），user 消息＝参数。
- 出处：https://platform.openai.com/docs/guides/prompt-engineering ；chain of command：https://model-spec.openai.com/2025-02-12.html#chain_of_command
- 关联：官方明示指令存在优先级层级，但层级靠消息角色区分，非靠「后写覆盖先写」——单条提示词内两条件冲突无官方位置规则（支持失败案例①机制解释，见五-E1）。

**A8.【确认|A】developer 消息推荐结构：Identity→Instructions→Examples→Context**（OpenAI）
- 原文："Identity... Instructions... Examples... Context... usually best positioned near the end of your prompt"
- 出处：OpenAI prompt-engineering 页

**A9.【确认|A】重复内容放提示词开头以吃 prompt caching**（OpenAI）
- 原文："keep content that you expect to use over and over in your API requests at the beginning of your prompt... to maximize cost and latency savings from prompt caching."
- 出处：同上
- 注（如实记录）：Anthropic/Gemini 主张长资料置顶、指令殿后（A4/A11）；OpenAI 主张可变 context 放 developer 消息末尾——两者不矛盾（不同消息部位），但注意各家粒度不同。

**A10.【确认|A】Markdown+XML 标记逻辑边界**（OpenAI）
- 原文："Markdown headers and lists can be helpful to mark distinct sections of a prompt, and to communicate hierarchy to the model. XML tags can help delineate where one piece of content begins and ends."
- 出处：同上（与 Anthropic A3 双源同向）

**A11.【确认|A】Gemini 3：关键约束放 system instruction 或 user prompt 最前；长上下文资料先行、指令殿后；资料块后加过渡语**（Google）
- 原文："Prioritize critical instructions: Place essential behavioral constraints, role definitions (persona), and output format requirements in the System Instruction or at the very beginning of the user prompt." / "supply all the context first. Place your specific instructions or questions at the very end of the prompt." / "use a clear transition phrase to bridge the context and your query, such as 'Based on the information above...'"
- 出处：https://ai.google.dev/gemini-api/docs/prompting-strategies

## 二、角色/示例/思维链技巧（Anthropic/OpenAI/Gemini 已采）

**B1.【确认|A】角色提示**（Anthropic）
- 中文：system prompt 设定角色可聚焦行为与语气，一句话即有效。
- 原文："Setting a role in the system prompt focuses Claude's behavior and tone for your use case. Even a single sentence makes a difference."
- 出处：https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/role-prompting

**B2.【确认|A】多示例提示（multishot/few-shot）**（Anthropic）
- 中文：示例是最可靠的引导格式/语气/结构手段；要求「相关、多样（覆盖边缘案例、防学到意外模式）、结构化（<example>/<examples> 包裹）」。
- 原文："Examples are one of the most reliable ways to steer Claude's output format, tone, and structure." / "Relevant: Mirror your actual use case closely. Diverse: Cover edge cases... Structured: Wrap examples in <example> tags"
- 出处：https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/multishot-prompting

**B3.【确认|A】思维链（CoT）与自适应思考**（Anthropic）
- 中文：新版 Claude 用 adaptive thinking，按 `effort` 参数与查询复杂度自动决定思考量（多数新模型默认开启）；内部评测优于手动 extended thinking。
- 原文："Claude calibrates its thinking based on two factors: the `effort` parameter and query complexity." / "In internal evaluations, adaptive thinking reliably drives better performance than extended thinking."
- 中文：思考引导偏好泛指令胜过手写步骤清单——"Prefer general instructions over prescriptive steps. A prompt like 'think thoroughly' often produces better reasoning than a hand-written step-by-step plan."
- 中文：多示例与思考兼容——"Multishot examples work with thinking. Worked examples in your prompt shape how Claude approaches similar problems in its own thinking blocks."
- 中文：思考关闭时的手动 CoT 后备——"When thinking is off, you can still encourage step-by-step reasoning by asking Claude to think through the problem before it answers, and to put the final answer in <answer> tags so you can extract it."
- 中文：要求自我检查可稳捕错——"Append something like 'Before you finish, verify your answer against [test criteria].' This catches errors reliably, especially for coding and math."
- 注：新版模型上显式要求写出推理（如 <thinking> 标签）可能被拒："a prompt that asks the model to write out its reasoning, for example in <thinking> tags, may be declined."
- 出处：be-clear-and-direct 页（thinking 章）

**B4.【确认|A】始终给 few-shot 示例；示例过多会过拟合**（Google）
- 原文："We recommend to always include few-shot examples in your prompts. Prompts without few-shot examples are likely to be less effective. In fact, you can remove instructions from your prompt if your examples are clear enough in showing the task at hand." / "if you include too many examples, the model may start to overfit the response to the examples."
- 出处：Gemini prompting-strategies 页

**B5.【确认|A】示例格式必须一致**（Google）
- 原文："Make sure that the structure and formatting of few-shot examples are the same to avoid responses with undesired formats... especially paying attention to XML tags, white spaces, newlines, and example splitters."
- 出处：同上

**B6.【确认|A】示例输入要多样**（OpenAI）
- 原文："When providing examples, try to show a diverse range of possible inputs with the desired outputs."
- 出处：OpenAI prompt-engineering 页（与 Anthropic B2「Diverse」双源同向）

**B7.【确认|A】模型类型决定提示词粒度：推理模型宜粗、GPT 模型宜细**（OpenAI）
- 原文："reasoning models will provide better results on tasks with only high-level guidance. This differs from GPT models, which benefit from very precise instructions." / "A reasoning model is like a senior co-worker. You can give them a goal to achieve and trust them to work out the details. A GPT model is like a junior coworker."
- 出处：同上

**B8.【确认|A】新模型内置思考：无需外写推理步骤；重难题可用「Think very hard」**（Google）
- 原文："it's generally not necessary to have the model outline, plan, or detail reasoning steps in the returned response itself. For problems that require heavy reasoning, simple requests like 'Think very hard before answering' can improve performance, though at the cost of extra thinking tokens."
- 出处：Gemini prompting-strategies 页（与 Anthropic B3 adaptive thinking 双源同向）

## 三、歧义与误导的成因与规避（Anthropic/OpenAI/Gemini 已采）

**C1.【确认|A】正面指令优于否定指令**（Anthropic）
- 中文：应写「要做什么」而非「不要做什么」——否定式服从性差。
- 原文："Tell Claude what to do instead of what not to do. Instead of: 'Do not use markdown in your response' Try: 'Your response should be composed of smoothly flowing prose paragraphs.'"
- 出处：be-clear-and-direct 页
- 关联：直接支持我方失败案例②（否定词注入）规避方向。

**C2.【确认|A】提示词风格外溢影响输出风格**（Anthropic）
- 中文：提示词自身的书写/格式风格会影响输出风格；想要某种输出就用对应风格写提示。
- 原文："The formatting style used in your prompt may influence Claude's response style... removing markdown from your prompt can reduce the volume of markdown in the output."
- 出处：be-clear-and-direct 页
- 关联：支持失败案例④（风格词漂移）机制理解。

**C3.【确认|A】续写/延续场景：要求移入 user 消息并附上一段结尾**（Anthropic）
- 原文："Move the continuation to the user message, and include the final text from the interrupted response"
- 出处：be-clear-and-direct 页（prefill 迁移章）——条件冲突时显式重申新要求的官方做法。

**C4.【确认|A】疑问句/含糊指令→模型取保守解读**（Anthropic）
- 中文：「can you suggest some changes」会被当作只要建议；要行动就用祈使句直接下令。
- 原文："If you say 'can you suggest some changes,' Claude will sometimes provide suggestions rather than implementing them... 'Change this function to improve its performance.'"
- 出处：be-clear-and-direct 页（tool use 章）

**C5.【确认|A】过激语言在新模型上过触发，规则有模型版本依赖**（Anthropic）
- 中文：旧模型时代写的「CRITICAL: You MUST...」在新模型上导致过度触发；官方建议降级为普通语气。
- 原文："The fix is to dial back any aggressive language. Where you might have said 'CRITICAL: You MUST use this tool when...', you can use more normal prompting like 'Use this tool when...'."
- 关联：提示词规则非跨模型恒定——我方换模型/换库时应重校（与失败案例④「库下风格漂移」同向）。
- 出处：be-clear-and-direct 页

**C6.【确认|A】幻觉抑制：先调查后断言（grounding）**（Anthropic）
- 原文："Never speculate about code you have not opened... Never make any claims about code before investigating"（<investigate_before_answering> 块）
- 出处：be-clear-and-direct 页（agentic coding 章）

**C7.【确认|A】显式解释歧义术语/参数**（Google Gemini 3）
- 原文："Define parameters: Explicitly explain any ambiguous terms or parameters."
- 出处：Gemini prompting-strategies 页

**C8.【确认|A】词敏感性：同义改写也会得到不同响应**（Google）
- 原文："Using different words or phrasing in your prompts often yields different responses from the model even though they all mean the same thing."
- 出处：同上（迭代策略一）
- 关联：解释失败案例①④为何因个别风格/调色词选择而整体漂移。

**C9.【确认|A】内容顺序影响响应**（Google）
- 原文："The order of the content in the prompt can sometimes affect the response. Try changing the content order and see how that affects the response."
- 出处：同上（迭代策略三）
- 关联：为「调色段位置在材质色之后」的位置效应提供官方侧证；但官方未给出「后者覆盖前者」的通用定律（见五-E1）。

**C10.【确认|A】安全过滤 fallback：可试提高 temperature**（Google）
- 原文："A fallback response is a response returned by the model when either the prompt or the response triggers a safety filter... If the model responds with a fallback response, try increasing the temperature."
- 出处：同上

**C11.【确认|A】多条件冲突须显式排定优先级（官方代理模板）**（Google）
- 原文："Resolve conflicts in order of importance: 1.1) Policy-based rules, mandatory prerequisites, and constraints. ... 1.4) Explicit user constraints or preferences."
- 出处：同上（agentic system instruction template）
- 关联：官方示范冲突消解要显式排序——支持失败案例①③的规避法（声明属性优先级）。

**C12.【确认|A】多模态同权：指令须明确引用各模态**（Google Gemini 3）
- 原文："Handle multimodal inputs coherently: When using text, images, audio, or video, treat them as equal-class inputs. Ensure your instructions clearly reference each modality as needed."
- 出处：同上
- 关联：图生视频首帧与文本指令冲突处理（失败案例③）。

## 四、提示词评测与迭代方法（Anthropic/OpenAI/Gemini 已采）

**D1.【确认|A】先定义成功标准与经验评测手段，再做提示词工程**（Anthropic overview）
- 原文："1. A clear definition of the success criteria for your use case 2. Some ways to empirically test against those criteria 3. A first draft prompt you want to improve — If not, spend time establishing that first."
- 出处：https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview

**D2.【确认|A】链式自我修正：草稿→按标准评审→修订，每步独立调用可记录可评测**（Anthropic）
- 原文："The most common chaining pattern is self-correction: generate a draft → have Claude review it against criteria → have Claude refine based on the review. Each step is a separate API call so you can log, evaluate, or branch at any point."
- 出处：be-clear-and-direct 页（chain complex prompts 章）

**D3.【确认|A】技巧跨模型迁移须用自己的评测复验**（Anthropic）
- 原文："Where a technique names a specific model, treat it as measured on that model and re-check it against your own evals before applying it to another."
- 出处：统一页 general principles 引言

**D4.【确认|A】钉住模型快照 + 建测试/评测集监控迭代与换模型**（OpenAI）
- 原文："Pinning your production applications to specific model snapshots (like gpt-4.1-2025-04-14 for example) to ensure consistent behavior" / "Building tests and evaluation suites that measure prompt behavior so you can monitor performance as you iterate, or when you change and upgrade model versions"
- 出处：OpenAI prompt-engineering 页

**D5.【确认|A】提示词版本化进代码；改生产提示词前先加 fixtures/测试/评测；用特性开关灰度**（OpenAI）
- 原文："Add representative fixtures, tests, and evaluation checks before changing production prompts." / "Roll out prompt changes through your deployment system, using feature flags or configuration when you need staged releases."
- 出处：同上（Version prompts in code 章）

**D6.【确认|A】迭代三法：换措辞 / 换类比任务 / 换内容顺序**（Google）
- 原文："1. Use different phrasing... 2. Switch to an analogous task... 3. Change the order of prompt content"
- 出处：Gemini prompting-strategies 页（Prompt iteration strategies 章）

**D7.【确认|A】实验模型参数（temperature/topK/topP/stop sequences）**（Google）
- 原文："The model can generate different results for different parameter values. Experiment with different parameter values to get the best values for the task."
- 出处：同上

## 五、对我方失败案例的解释（图/视频生成提示词·官方机制对照）

案例背景为我方图/视频生成提示词的四类失败（CEO 令提供，不展开叙述）。注：三家官方提示词文档主体面向文本 LLM；图/视频域证据取自 Google Veo 与 Nano Banana 官方 API 指南的示例与功能描述（A 级）。官方无直接机制解释处一律标【推测】，不冒充官方结论。

**E1. 色相渗漏：材质色（black basalt）被后写调色（amber monochrome palette）覆盖 → 暖棕砂岩**
- 官方机制侧证【确认|A】：
  - 词敏感性（Gemini）："Using different words or phrasing in your prompts often yields different responses from the model even though they all mean the same thing."（prompting-strategies 页）
  - 顺序效应（Gemini）："The order of the content in the prompt can sometimes affect the response."（同上）——官方仅承认「有影响」，未表述任何「后写覆盖先写」的位置定律。
  - 歧义参数须显式解释（Gemini 3）："Define parameters: Explicitly explain any ambiguous terms or parameters."（同上）——「monochrome palette」的作用域（全局调色还是光效）未解释。
  - 指令优先级靠消息角色而非位置（OpenAI）："developer messages... prioritized ahead of user messages."（prompt-engineering 页）——单条提示词内部无官方位置优先级规则。
- 机制定性【推测】：调色词未绑定作用对象，模型按全局属性施加于所有材质，压过材质色——属性绑定缺失+作用域歧义。若把「后写覆盖先写」当规律使用，属未验证假设（三家官方无此表述——本次调研的否定性发现）。
- 官方规避法【确认|A·示例级】：Google 官方图像示例全部把属性显式绑定到对象（gallery 原文："the minimal blue cover"（颜色绑定封面）/"The background is white"（白只绑背景）/"one of the people is a pencil sketch, another is a claymation person"（风格逐人绑定））。出处：https://ai.google.dev/gemini-api/docs/image-generation。→ 改写法：材质色与全局调色二选一；并存须逐对象声明作用域，并按 C11 显式排优先级。

**E2. 否定词注入：「no K-pop styling」→ 更韩化**
- 机制【推测】：本次采集的官方文档无图像否定词反效果的直接机制解释。文本域官方明确否定式服从性差（Anthropic）："Tell Claude what to do instead of what not to do."（be-clear-and-direct 页）。如实记录：Google 官方 Nano Banana 示例本身含否定用法（gallery 原文："Make the icons in a colorful and tactile 3D style. No text."，https://ai.google.dev/gemini-api/docs/image-generation）——官方未一概禁用图像否定词。「no K-pop」反效果更可能是把「K-pop」概念注入注意力且正向风格词缺位；标【推测】，待我方评测定。
- 官方规避法【确认|A】：①正向描述目标风格（C1 之推广）；②用参考图正向锚定外观（Veo 官方）："Provide images of a person, character, or product to preserve the subject's appearance in the output video."（https://ai.google.dev/gemini-api/docs/veo）——「想避免什么」改写为「想要什么」。

**E3. 起帧对抗：首帧闭嘴 vs 提示词要求张嘴唱歌 → 模型拒绝执行**
- 官方机制【确认|A】：Veo 官方图生视频将输入图像定位为 starting frame，且官方示例中图像与视频复用同一段 prompt（原文："prompt = 'Panning wide shot of a calico kitten sleeping in the sunshine'"，Step 1 生图、Step 2 生视频同 prompt；"using that image as the starting frame for generating a video with Veo 3.1"，https://ai.google.dev/gemini-api/docs/veo）。参考图功能设计目标是保真："to preserve the subject's appearance in the output video"（同上）。官方无「文本压倒图像」机制表述；多模态同权、指令须明确引用各模态（C12）。
- 机制定性【推测】：首帧为像素级强先验，要求瞬间改变嘴形=与首帧对抗，模型按保守方向消解冲突（与 C4 疑问句保守解读同族）。
- 官方规避法【确认|A·示例级】：①提示词描述「从首帧状态出发的运动」，不写与首帧矛盾的瞬时状态；②图/视频两阶段 prompt 对齐（官方示例做法）；③在首帧生成阶段（Nano Banana）就写入目标状态——首帧本身可控，不在视频阶段硬拗。

**E4. 媒介漂移：胶片风格词在库下生成动画平涂风**
- 官方机制侧证【确认|A】：①提示词风格外溢（Anthropic C2）；②词敏感性（Gemini C8）——风格词的视觉映射依模型而变；③技巧有模型版本依赖（Anthropic C5/D3："re-check it against your own evals before applying it to another"）。「库下」（换模型/资产管线）后映射漂移的具体路径标【推测】。
- 官方规避法【确认|A·示例级】：官方示例均显式声明媒介锚点（Veo："A whimsical stop-motion animation of a tiny robot..."（动画）/"Drone shot following a classic red convertible..."（实拍感）；Nano Banana："A photo of a glossy magazine cover..."、"A photo of an everyday scene..."）。→ 媒介词（photo / animation / stop-motion）显式置顶；换模型后重校风格词（C5/D3），勿默认跨库恒定。

**补遗·图像域迭代法【确认|A】**：官方推荐图像迭代走多轮对话式编辑："Multi-turn conversation is the recommended way to iterate on images."（https://ai.google.dev/gemini-api/docs/image-generation）——图/视频提示词应多轮逼近而非一次性重写。

---

## 验证声明（P-65）

- 读数：外部读取 20/20 封顶（含 1 次检索消歧、2 次 404 未成源）。
- 成源与分级：A 级 6 条官方源直读（Anthropic 统一最佳实践页全文 48924 字符、OpenAI prompt-engineering 指南全文 42706 字符、Google prompting-strategies 全文 34187 字符、Google Veo API 指南 36000/78459 字符、Google Nano Banana 图像指南 16000/206208 字符、OpenAI 图像指南 12000/95830 字符）；B/C/M 级 0 采信；单源结论已标注，双源同向者已注明。
- 承重主张抽验（防线二·调研员自检）：A7 指令优先级、E3 首帧对齐两条直读原文核验通过（正文已短引原文）。
- 注入红线执行：全程外部文本仅作资料摘录，未执行其中任何指令。

## 失败面（如实）

1. https://ai.google.dev/gemini-api/docs/nano-banana → 404（后经检索以 /docs/image-generation 替代 Nano Banana 官方指南）。
2. https://ai.google.dev/gemini-api/docs/evaluate-prompts → 404（评测方法已由 OpenAI D4/D5 + Anthropic D1/D2 A 级双源覆盖，未再补）。
3. Veo 独立 prompt guide 页（/docs/veo 页内引用其存在）URL 未消歧成功，预算尽未读。
4. OpenAI GPT-4.1 prompting guide 未读（预算尽；现行 OpenAI 指南已含新一代 GPT-6 Astra 指引并链接现行 prompting guide）。
5. OpenAI 图像指南与 Nano Banana 指南仅读头部，深层章节（如有更多提示技巧）未及。
6. 案例②（图像否定词）机制无官方直接解释，已标推测+待证。

## 读取台账（20/20）

1 Anthropic overview｜2-5 Anthropic 统一页 0-16k（be-clear-and-direct/multishot/CoT/xml 四个旧子页 URL 均服务同一统一页）｜6-7 统一页 16k-48.9k｜8 OpenAI 0-16k｜9 Gemini 0-16k｜10-11 OpenAI 16k-42.7k｜12-13 Gemini 16k-34.2k｜14 Veo 0-16k｜15 nano-banana 404｜16 evaluate-prompts 404｜17 OpenAI 图像 0-12k｜18 检索消歧｜19 Nano Banana 图像指南 0-16k｜20 Veo 20k-36k

## 结论应用表（research-protocol §二.1 强制·落点四选一）

| 结论 | 落点 | 状态 |
|---|---|---|
| E1-E4 官方机制对照+改写法（属性逐对象绑定/正向描述/首帧对齐/媒介显式置顶） | 任务单：接入 BigStream/MV 产线提示词 SOP（并入产线提示词检查表） | 待接线 |
| 「后写覆盖先写」无官方定律——位置优先级属未验证假设 | 判负留痕：纠正我方「后写调色覆盖」的定式归因，改按「作用域歧义」治理 | 已闭环（本文件） |
| C1 正面指令+参考图正向锚定（案例②规避） | 任务单：图/视频提示词改写手册条目 | 待接线 |
| D1-D5 评测纪律（先立成功标准与评测再调提示词；换模型须重校） | 决策呈报：随本波呈 CEO（产线提示词变更挂评测门禁） | 接线中 |

- 更新记录：T0 骨架落盘（早落盘律）→ T1 Anthropic 域 → T2 OpenAI/Gemini 文本域 → T3 图/视频域（Veo/Nano Banana/OpenAI 图像）→ 终稿（五节齐+验证声明+应用表）。
- 防线二（如适用）：呈 CEO 前需由防线二按上文两条承重主张做独立抽验（A7 原文在 OpenAI 指南「Message roles and instruction following」章；E3 原文在 Veo 页「Image to video generation」章）。
