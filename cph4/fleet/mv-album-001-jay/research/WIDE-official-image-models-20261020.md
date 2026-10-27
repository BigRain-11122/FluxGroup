# WIDE-official-image-models-20261020 — 主流图像模型官方提示词语法与能力边界（KF 包用）
> 溯源：MV 产线 KF 包提示词工程·消费方=mv-album-001-jay KF 包＋lint 规则·判据=结构/权重/负面词/参考图/文字/推荐档/官方红线
> 验证声明：实读 17 次（本地 6 文件＋官方页 11 次）·成源 A=10（全部官方站点/官方 repo）B=0 C=0 M=1（MJ 403）·失败面：docs.midjourney.com 全线 403（5 次）、docs.bfl.ai 404、docs.ideogram.ai/using-ideogram/prompting-guide 404、krea.ai/blog/krea-1 404
> 引文规则：短引逐字；官方未写的写「官方未载明」，不推断成「官方支持」。

## 一、模型对照表（[n]=文末官方 URL）

| 模型 | 结构 | 权重语法 | 负面提示词 | 参考图/一致性 | 文字渲染 | 推荐档 | 官方红线 |
|---|---|---|---|---|---|---|---|
| Krea 2（turbo）[1] | 自然语言单段散文；"Long detailed prompts yield best results"；无主体优先硬序、无换行块规范、无长度上限 | 官方未载明（无括号/数值语法） | 官方未载明字段（我们的 cfg=1.0+ZeroOut 等于关闭） | prompting.md（t2i）未载明；一致性机制见 Krea Train[2] | "putting quotes around the words to be rendered" | "up to 2k resolution images"；步数/CFG 官方未载明 | 无禁词表；官方范例本身用 cinematic / shallow depth of field / golden hour |
| Krea 1 [2] | "A highly expressive model without the heavy prompting"；"Simple prompts, strong visuals" | 官方未载明 | 官方未载明 | Krea Train 微调："Upload up to 50 images of the same style, object, or face" | 页内未载明（以 Krea 2 引号规则为准） | "1.5K Native resolution or up to 4K upscaled" | 暗示勿重提示词（轻提示词=产品主张，非硬禁） |
| Qwen-Image 2512 / Edit 2511 [3] | README 无公式；示例=长段英文自然语言（约 150 词）；官方另供 rewriter 工具 | 官方未载明 | 官方支持字段：2512 示例给中文负向词 + true_cfg 4.0；纯文生图示例写 `negative_prompt = " "`「Recommended if you don't use a negative prompt」 | Edit 2511 多图输入（image 列表）；张数上限官方未载明 | "complex text rendering… especially for Chinese"；2.0 "1k-token instructions" | 2512：50 步/true_cfg 4.0/16:9=1664×928；Edit2511：40 步/guidance 1.0/true_cfg 4.0 | "editing results may become unstable if prompt rewriting is not used… strongly recommend applying prompt rewriting" |
| Seedream 4.0/4.5/5.0 [4] | 简洁连贯自然语言＝主体+行为+环境；美学用自然语言或短语补；先写用途/类型 | 官方未载明 | 官方未载明（指南无负面字段） | 多图输入，按"图一/图二/图三"点名；上限未载明 | 要生成的文字放双引号（例："Seedream 4.5"） | 步数/CFG 官方未载明（API 不暴露） | "避免：一个女孩，撑伞，林荫街道，油画般的细腻笔触"；"简洁精确的提示通常优于重复堆叠华丽复杂的词汇" |
| FLUX（FLUX 3 Image / FLUX.2）[5][6] | 五段序：image type→subject→setting→light→framing；"The order is a habit, not a rule: put first whatever matters most"；"A clear structure matters more than length" | 官方未载明（无括号权重） | "FLUX 3 Image has no negative prompt field"；"FLUX 3 Image has no `negative_prompt` or `prompt_upsampling` field"；四步正述替代法 | FLUX 3 最多 10 张参考图，按位置引用 | 引号包裹待渲文字（prompting basics: "quote text to render"） | aspect_ratio 15 档+auto；resolution 768sq/1k/2k/4k（1k 默认）；步数/guidance 未载明 | "omit quality tags such as 'masterpiece'"；"Use one or two strong effects"；"Do not treat the component list like a checklist" |
| Midjourney [7] | 官方未载明（docs 403） | 官方未载明 | 官方未载明 | 官方未载明（仅官方 changelog 证实 sref 药丸/--exp 存在） | 官方未载明 | 官方未载明 | 官方未载明 |
| Ideogram [8][9] | 8 段模板：`[image type] of [subject], [action], [setting], [lighting], [style]`；主意在句首 | 官方未载明（提权=前置+重复，非数值） | 4.5/4.0 无独立 Negative prompt 字段；3.0 有该设置；"Image models don't handle 'no', 'without' or 'not' well. They latch onto the word that follows" | 3.0 角色/风格参考（官方页存在，本波未逐字读） | 引号+早出现+保持短；非拉丁文"render less reliably than English" | 3.0 "keep plain-language prompts under about 150 words"；4.5 最多 10,000 字符 | "beautiful / cool / artistic / modern" 不指向可画之物；禁自相矛盾描述 |
| Recraft [10][11] | 官方 prompt-engineering guide 按 Subject/Composition/Context 分章（本波未逐章读） | 官方未载明 | 有 Negative prompt 字段；"avoid double negation… write `apples`… not `no apples`" | V4 Styles：1–10 张参考图定风格 | 文字排版/自定义字体为官方卖点；可关文字生成（可能引错字） | 遵循度差时"lowering the Artistic level" | 双重否定；负向字段里写 "no X" |

## 二、我们 KF 包与官方文档冲突的地方

1. **权重语法当官方用（最重）**：FIDELITY-SPEC-v1 §二/§三 写 `(face close to the lens:2.5)`、`(K-pop idol styling:-3)`，标注「Krea2PromptWeight 语法」。Krea 官方 prompting.md 通篇只推自然语言，无任何权重/负权重语法[1]。且 kf_batch_v21.py 实跑 `cfg=1.0` + `ConditioningZeroOut`（L48/L59），CFG=1 时负向条件不参与运算——**负权重在出图上空转**。后果：以为在反韩，实际没反；「官方」二字站不住，lint 无法用官方复核。
2. **伪官方铁律「subject 必须是最长块」**：FIDELITY-SPEC 诊断①把它标成「官方铁律」。Krea 官方无此条；BFL 官方反说 "The order is a habit, not a rule"、"Strong prompts are specific, not necessarily long"[6]。后果：八块换行模板（每块独立一行）被当成官方正序固化，与 Krea 单段散文官方范例相悖，且无人能复核。
3. **分辨率只跑官方一半**：kf_batch_v21.py `EmptyLatentImage 1344×768`、8 步。Krea 官方 "turbo model can generate up to 2k resolution images"（范例全部 2k）[1]；Krea 1 官方 1.5K 原生[2]。后果：脸镜毛孔/发丝细节先天不足，i2v 放大追不回来——与我们「35mm 胶片颗粒/可见毛孔」的年代要求直接打架。
4. **长度闸引错官方上限**：PROMPT-SPEC §二.5「40–200 词（官方上限 200）」。Qwen 官方 README 无 200 词上限，2.0 官方称支持 "1k-token instructions"[3]；~150 词是 Ideogram 3.0 的规矩[8]。后果：长镜头被无据截断，且报告/规范里挂着不存在的官方限制。
5. **文字一律判噪声**：PROMPT-SPEC「出字=噪声，重 roll」。Krea 官方明确支持引号渲字[1]，Seedream 官方给引号规则[4]，BFL 官方亦有引号位[6]。后果：磁带标签/2001 招牌等年代物证被一律判废，QC 只能靠「零窜字」兜底。
6. **文案锁脸 vs 官方微调锁脸**：PROMPT-SPEC「ID 块逐字复用律」暗示文本可锁人；Krea 官方给的一致性机制是 Krea Train（≤50 图微调）[2]，Krea 2 t2i 文档无参考图机制。后果：文档把「降漂移」写成「锁脸」；实跑靠 jman LoRA，两套说法需分家。

## 三、KF 分派建议

| 镜型 | 用哪个 | 一句理由 |
|---|---|---|
| 脸镜（近特/情绪/直视） | Krea 2 + jman LoRA，2k 档 | 官方长描述出最佳质感、上限 2k[1]；锁脸靠 LoRA 不靠文案[2] |
| 物件/道具特写 | Krea 2（单主体 1.5–2k 裁切）；需可读标签→Qwen-Image-2512 | Krea 官方未承诺文字，Qwen 官方以中英文字渲染为强项[3] |
| 空镜/环境/远景 | Krea 2 或 FLUX 3（21:9 等 15 档、4k）[5] | 官方比例/分辨率档最全，横移空镜不裁切 |
| 超现实/风格化 | Krea 1（轻提示词） | 官方定位 "highly expressive… without the heavy prompting"[2] |
| 年代场景/多人复杂叙事 | Seedream 4.5（中文直写主体+行为+环境）[4] | 官方禁堆词、要连贯句，正好克我们的词表拼装习惯 |

## 四、官方禁止/不推荐清单（可直接进 lint；落点=prompt_lexicon lint 规则）

1. 权重语法 `(x:2.5)` / `(x:-3)` → 禁用于 KF 包（Krea 官方未载明[1]；cfg=1.0 下负权重无效）｜落点=lint 新规则 W-NOWEIGHT。
2. `masterpiece` / `8k` / `highly detailed` / `ultrarealistic` → 禁（BFL："omit quality tags"；"add little"）[6]｜落点=VAGUE 名单补词。
3. 散文否定 `no/not/without` → 禁，改写正述（BFL/Ideogram/Recraft 三家官方同口径）[5][9][10]；Recraft 例外：负向字段只写名词[10]｜落点=NEG 名单（已有）。
4. `beautiful / cool / artistic / modern` 等无指向风格词 → 禁（Ideogram 官方）[9]｜落点=VAGUE 名单。
5. 逗号关键词串（"一个女孩，撑伞，林荫街道"）→ 禁，改连贯句（Seedream 官方反例逐字）[4]｜落点=新规则 K-STACK。
6. 特效/风格词叠加 >2 条 → 禁（BFL "Use one or two strong effects"）[6]｜落点=D3 光效闸已有，扩到风格词。
7. 画面内文字必须加引号（Krea/Seedream/Ideogram/BFL 四家一致）[1][4][8][6]｜落点=新规则 T-QUOTE（放开「有字必废」，改为「字必引号」）。
8. 比例/画质设置不写进 prompt（Ideogram 官方：设置与描述分离）[8]｜落点=lint 检 `3:4 frame`/`4K` 类词。
9. 引用「官方」必须带官方 URL；无 URL 的经验律不得标官方｜落点=PROMPT-SPEC 引用纪律。

## 五、拿不到官方文档的模型

- **Midjourney**：docs.midjourney.com 对自动化抓取全线 403（/docs/parameter-list、/hc/en-us、sitemap 均失败）。--ar/--stylize/--sref/--cref/--cw/--no 的官方逐字定义本波未取得，故表内一律「官方未载明」，**不引二手参数表充官方**。仅 updates.midjourney.com（官方 changelog）可证 sref 药丸/--exp 存在。
- **Krea 1 提示词文档**：无独立 prompting 文档，只有产品页[2]；结构/权重/负面词均无官方文本。
- **Ideogram Characters / Style Reference 页**：页面存在（llms.txt 列出），本波未逐字读，表内已标。
- **Recraft prompt-engineering 分章页 / appendix 长度上限**：本波只读 best-practices 与 negative-prompts 两页。

## 官方 URL
[1] https://raw.githubusercontent.com/krea-ai/krea-2/main/docs/prompting.md ｜[2] https://www.krea.ai/models/krea-1 ｜[3] https://raw.githubusercontent.com/QwenLM/Qwen-Image/main/README.md ｜[4] https://docs.volcengine.com/docs/ark/seedream-4-0-5-0-prompt-guide ｜[5] https://docs.bfl.ml/guides/prompting_unified_technical.md ｜[6] https://docs.bfl.ml/guides/prompting_unified_building.md ｜[7] https://updates.midjourney.com/ （docs.midjourney.com 403）｜[8] https://docs.ideogram.ai/prompting/prompt-structure.md ｜[9] https://docs.ideogram.ai/prompting/fix-common-problems.md ｜[10] https://www.recraft.ai/docs/recraft-studio/image-generation/working-with-text-and-prompts/negative-prompts.md ｜[11] https://www.recraft.ai/docs/best-practices/prompting-and-image-generation.md

- 更新记录：T0 骨架落盘→T1 Krea→T2 Qwen/Seedream→T3 BFL→T4 Ideogram/Recraft→T5 MJ 判阻→终稿 61 行（node 字节级计数）。
- 内证文件：PROMPT-SPEC.md §二/§三、FIDELITY-SPEC-v1.md §一/§二/§三、kf_batch_v21.py L45-L63。