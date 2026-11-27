# R-20261015-prompt-rules — 提示词为什么会误导生成模型：四类失败机制证据（CEO 令·wave 2026-10-15-prompt-rules）
> 溯源：任务单「为提示词规则找 3-4 条权威机制证据」·消费方=prompt-rules 任务单·判据预注册=①否定词是减法还是注入 ②属性渗漏/绑定失败机制 ③词冗余/前部偏置 ④i2v 起帧主导性
> 验证声明：外部读取动作 11 次（DDG 搜索×2+页面抓取×9），有效成读 7 次·成源 8 条（A=7/B=1/C=0/M=0）·失败面：①DDG「Hidden Life of Tokens」被反爬拦截 ②export.arxiv.org http→https 重定向浪费 1 次 ③HF diffusers negative_prompt 文档 404×2（v0.41 版无此页+main 版 404）——以上均如实记录，未影响承重结论（第一节已有 A 级直读源）

## 一、否定词机制（negative prompt 究竟是减法还是注入）

- 机制（确认·A·arxiv 2406.02965 直读摘要页）：首篇系统实证《Understanding the Impact of Negative Prompts》(Ban et al. 2024)——否定词非"输出端减法"，而是条件注入后的**延迟中和**："Delayed Effect: The impact of negative prompts is observed after positive prompts render corresponding content. Deletion Through Neutralization: ...mutual cancellation effect in latent space with positive prompts"。即：概念仍先被渲染，删改靠潜空间对消完成。URL: https://arxiv.org/abs/2406.02965
- 佐证（确认·B·摘要句经搜索引得未直读页面）：arxiv 2410.14398《Dynamic Negative Guidance of Diffusion Models》："conventional NP is limited by the assumption of a constant guidance scale, which may lead to highly suboptimal results, or even complete failure"。URL: https://arxiv.org/abs/2410.14398
- 规避法：正向提示里写「不要X」无效（无此通道）；负向提示是延迟中和——关键内容用正向重构而非否定句，负向提示只放通用瑕疵词。

## 二、属性绑定/渗漏（attribute binding / leakage）

- 机制（确认·A·arxiv 2306.08877 SynGen，NeurIPS 2023 oral）：T2I 常把修饰词绑到错误实体——"a pink sunflower and a yellow flamingo" 可生成 "a yellow sunflower and a pink flamingo"；根因是 "impaired mapping between linguistic binding of entities and modifiers in the prompt and visual binding of the corresponding elements"（语言绑定→视觉绑定映射受损，cross-attention 图与句法不对齐）。URL: https://arxiv.org/abs/2306.08877
- 佐证（确认·A·arxiv 2411.17472）：多对象多属性提示 "often misaligning modifiers with their corresponding nouns or neglecting certain elements"（属性错绑+元素丢失）。URL: https://arxiv.org/abs/2411.17472
- 规避法：多对象场景降低并列密度——一对象一短句、修饰词紧贴名词、避免「A色X和B色Y」式平行结构。

## 三、词序偏置（判据线索判负后的替代证据）

- 判负留痕（A 级核实）：任务单线索《The Hidden Life of Tokens》(Text-to-Image) 判负——arxiv 全库仅 2502.03628 同名论文，研究对象为 LVLM 幻觉（"gradual visual information loss/early excitation"），**非 T2I**。URL: https://arxiv.org/abs/2502.03628
- 机制（确认·A·arxiv 2606.03715，Technion）：T2I 实际只消费文本嵌入两件事："(i) the merging of adjacent tokens into a word representation... (ii) word order, which is imprinted by the positional embedding"——"bag of position-tagged words" 即足够生成；上下文/句法信息基本不被图像模型使用 → 堆冗余词不增信号，词序=位置嵌入即信号本体。URL: https://arxiv.org/abs/2606.03715
- 机制（确认·A·arxiv 2410.10291 SemVarBench，ICLR 2025）：模型几乎追不上词序换义：最强模型仅 0.2/1；对象关系类 0.07/1（属性类 0.17-0.19/1）→ 靠语序表达「谁对谁」基本无效。URL: https://arxiv.org/abs/2410.10291
- 规避法：关系表达不靠语序（近无效），改显式命名+前置关键对象；删冗余修饰不损语义。

## 四、i2v 起帧主导（first-frame conditioning dominance）

- 机制（确认·A·arxiv 2402.04324 ConsistI2V）：I2V 任务定义即 "use the initial frame (alongside a text prompt)"，且模型要努力 "preserve the integrity of the subject, background, and style from the first frame"——主体/背景/风格全由帧1锚定。URL: https://arxiv.org/abs/2402.04324
- 佐证（确认·A·arxiv 2608.13205 HPSD）：帧1是 "privileged condition"——"Given a high-quality first frame or a detailed textual prompt, TI2V models unlock substantially better visual quality than their T2V mode"。URL: https://arxiv.org/abs/2608.13205
- 反证自编辑范式（确认·A·arxiv 2405.16537 I2VEdit）：改视频的标准做法="propagate edits from the modified first frame to the remaining frames"——改帧1=改全片。URL: https://arxiv.org/abs/2405.16537
- 待证：SVD (arxiv 2311.15127) 发布模型弃文本纯图条件的细节不在摘要内，需读正文核实——不作承重结论。URL: https://arxiv.org/abs/2311.15127
- 规避法：i2v 的内容决策全部放帧1，文本提示只写运动/运镜/时长类指令，勿指望提示词修正画面。

## 五、结论应用表（落点四选一：任务单/法文修改/决策呈报/判负留痕）

| 结论 | 落点 | 状态 |
|---|---|---|
| 否定词=延迟中和非减法→禁用「不要X」式正向 | 任务单 2026-10-15-prompt-rules | 已闭环 |
| 属性渗漏→多对象降密+修饰词贴名词 | 任务单 2026-10-15-prompt-rules | 已闭环 |
| T2I 只吃词义+词序→删冗余、关系显式化 | 任务单 2026-10-15-prompt-rules | 已闭环 |
| i2v 帧1锚定全片→内容决策放首帧 | 任务单 2026-10-15-prompt-rules | 已闭环 |
| 《Hidden Life of Tokens》=T2I 线索不成立 | 判负留痕（本件三节） | 已闭环 |

- 更新记录：T0 骨架落盘（早落盘律）→ T1 否定词→T2 属性绑定→T3 词序（含判负修正）→T4 i2v→终稿 43 行（node 字节级实计 44 split 段）。
- 防线二：单兵小任务，防线二抽验（两根承重主张直读源核验：2406.02965/2306.08877 均为官方页/API 直读=A 级）由主会话收口时执行。
