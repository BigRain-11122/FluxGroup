# WIDE-official-video-models-20261020 — 官方文档口径对照（只读官方源）

> 消费方：MV 产线提示词包（PROMPT-SPEC-v2-I2V / 星晴-i2v-PACK-A-v1）。源分级 A=厂商官方站/官方 repo。官方未写=未载明，不补猜。

## 一、模型对照表

| 模型 | 提示词结构 | 运镜语法 | 运动/表演 | 首帧/尾帧/参考 | 时长·分辨率 | 负面词 | 官方红线（原文摘） |
|---|---|---|---|---|---|---|---|
| Seedance 2.5 | 四段式：素材绑定→一句话概述→时间轴/镜头顺序→全局约束（A: docs.seedance.tv/zh/seedance-2-complete-prompting-guide） | 常用镜头词直写；**整数秒时间戳** | 表情写可观察变化：「眼眶发红、嘴角压低、呼吸变急」 | 关键帧按「图片 1 至图片 N 的顺序」声明 | 图≤30 张/视频≤10 段≤30s；上限未载明 | 未载明 | 「时间段应连续，例如 0–3 秒、3–7 秒、7–15 秒，不要留下无法解释的空档」 |
| Kling 2.5 | 官方正文未取到（quickstart/API 页仅 JS 壳） | 未载明 | 未载明 | 尾帧可选（Runway 目录转述: 5/10s） | 5/10s | 未载明 | 未载明 |
| MiniMax Hailuo | 自然语言 + 方括号相机指令可串联（A: platform.minimax.io/docs） | 15 命令：`[Push in]` `[Truck right]` `[Pan left]` `[Tilt up]` `[Pedestal up]` `[Tracking shot]` `[Shake]` `[Static shot]`，**可叠加** | 示例把动作与运镜逐段串：`picks up a book [Pedestal up], then reads [Static shot]` | H3 Max 支持首尾帧（Runway 目录） | H3 Max 480p/768p；示例 duration=6 | 未载明 | 无禁止条款载明 |
| Runway Gen-4/4.5 | 未载明（prompting guide 403，仅模型目录可读） | 未载明 | 未载明 | 首帧+文本；5 或 10 秒（help 页摘要） | 5/10s | 未载明 | 未载明 |
| Luma ray-3.2 | 自然语言 1–6000 字符；「Be specific about subject, motion, camera movement, lighting, and pacing」（A: docs.agents.lumalabs.ai） | 无专有命令词 | 未载明 | start_frame / end_frame / keyframes / loop | 5s/10s；360p–1080p | 未载明 | 10s 拒与 hdr/start_frame/end_frame 同用；loop 拒与 10s/hdr/end_frame/keyframes 同用 |
| Google Veo 3.1 | 七要素：Subject/Action/Style/Camera positioning and motion/Composition/Focus/Ambiance（A: ai.google.dev/gemini-api/docs/veo） | 自然语言：`dolly shot` `aerial view` `top-down shot` | 对白用引号；SFX/环境声明写 | 首帧 image + lastFrame 插值；≤3 参考图 | 4/6/8s；720p/1080p/4k（1080/4k 仅 8s）；24fps；原生音频 | 未载明（无 negative 参数） | 「Multi-video prompting … is not currently supported」；英文完全支持、他语未评估 |
| Alibaba Wan 2.2 | 未载明（README 无 prompt 语法） | 未载明 | 未载明 | I2V；size 跟随原图比例 | 480P/720P；TI2V-5B 720P@24fps | 未载明 | 未载明 |
| Tencent HunyuanVideo | 未载明 | 未载明 | 未载明 | README 未载明 I2V | 720p 推荐；129 帧；cfg 6.0；seed | 未载明 | 未载明 |
| 智谱 CogVideoX | 英文 prompt；224/226 token 上限 | 未载明 | 未载明 | I2V 版存在 | 1360×768；81 帧；5/10s；16fps | 未载明 | 「Prompt Language English」＋token 限 |
| Vidu Q3 | prompt ≤20000 字符（A: platform.vidu.cn/docs） | 未载明（另有首尾帧/参考生视频端点） | 未载明 | start-end-to-video / reference-to-video | 1–16s；540p/720p/1080p；seed；audio | 未载明 | 字符上限 20000 |
| LTX-Video | 8 条清单：主行动一句→动作细节→外观→环境→**机位与运动**→光色 | 自然语言 | 未载明 | multi-keyframe conditioning | <720×1280；帧<257（8n+1）；32 倍数 | 未载明 | 分辨率须整除 32、帧数 8n+1 |

## 二、我们现行提示词包与官方文档冲突处

1. **「禁精确秒数」被当成 Seedance 官方律——官方明说 2.5 响应整数秒时间戳。** 我们在 `PROMPT-SPEC-v2-I2V.md §二律五` 与 `INTENT-TO-KEYWORD-v1.md §八` 写「Seedance…禁精确秒数」，lint A3 见秒数判负。官方原文：「Seedance 2.5 可以响应整数秒时间戳」，示例「第 5 秒向左快速横移」。后果：32 条 2–8s 窗口无时间锚，官方自己说「内容太少时，模型会自由补充」——我们的「half beat」类节拍词落不到秒，动作早晚不可控。
2. **「单镜单运镜」写成全局硬门，官方示例本身就是多运镜。** `PROMPT-GATE-星晴-i2v-PACK-A-v1-B4.md` E1 见第二运镜即判负；但 MiniMax 官方请求示例是 `picks up a book [Pedestal up], then reads [Static shot]`，官方 cheat sheet 还给出叠加式 `[Truck right, Pan left, tracking shot]`。后果：合法的「推后静止/环绕跟拍」被我们自己判负；同时 H3 单里一个方括号都没用，官方唯一有语法保证的运镜通道被绕开。
3. **40–90 词硬预算压掉官方四段式的后两段。** `PROMPT-SPEC-v2-I2V.md §二律五` 定 40–90 词；Seedance 官方四段式要求「素材绑定」与「全局约束（机位、光线、色彩、画幅、无字幕、无 BGM）」，Vidu 允许 20000 字符。后果：多素材/多拍点镜写不下，被 lint 逼成散文压缩，素材归属与无声约束双双缺位。
4. **lint 把画幅写进 prompt 判 FAIL，官方把它列为必填段。** `§四 lint 3` 见 `16:9|720p` 即判「参数入文」；Seedance 四段式第 4 段原文要求补「画幅，以及『无字幕、无 BGM』等限制」。后果：Seedance 无独立音轨开关时，文本层没有合法位置压字幕/BGM。
5. **只做首帧延伸、不用尾帧/多关键帧。** `PROMPT-GATE…B4` D1 要求「动作必须是首帧自然延伸」；官方给了更强约束：Seedance「以图片 1 至图片 N 的顺序作为关键帧」，Veo「first and last frames … interpolation」，Luma `end_frame`。后果：8s 长窗端点不可控，只能靠抽卡；官方现成能力闲置。
6. **「H3 需时间戳切镜」的官方依据不成立。** `PROMPT-SPEC-v2-I2V.md §二律四` 称 H3 官方案例 0.0–1.2s；官方 API 文档示例无时间戳，只有方括号命令。后果：H3 本地路由单按秒写，最坏被忽略；且漏掉方括号语法，运镜命中率无保障。

## 三、每类镜头该用哪个模型

| 镜头类 | 首选 | 一句理由 |
|---|---|---|
| 脸镜/微表情 | Veo 3.1 | 官方明写「Enhance the facial details … using the word portrait」＋3 张参考图锁脸 |
| 空镜/氛围 | Luma ray-3.2 | 官方 prompt 规范直接点名 motion/camera/lighting/pacing，5s 成本低 |
| 超现实 | Seedance 2.5 | 官方支持图 1..N 关键帧序列＋整数秒时间轴，云人这类轮廓可分段钉住 |
| 大运动 | Wan 2.2 I2V | 官方 720P@24fps、size 随原图比例，开源可复现；Kling 官方正文未取到，不作首选 |
| 对嘴/台词 | Veo 3.1 | 对白用引号、原生音频同步；Vidu 另有对口型专用端点 |
| 慢放 | 后期变速 | 11 家官方文档均无「慢动作」参数；Veo 固定 24fps、CogVideoX 16fps，生成端不做慢放 |

## 四、官方明令禁止清单（可直接进 lint，仅收官方原文）

- Seedance：时间段必须连续，不许无法解释的空档；宫格故事板建议 <15 格；图≤30、视频≤10 段且总长≤30s、音频≤10 段≤30s。
- Luma：`duration=10s` 不得与 `hdr`/`start_frame`/`end_frame` 同用；`loop` 不得与 `10s`/`hdr`/`end_frame`/`keyframes` 同用。
- Veo：不支持 multi-video prompting；1080p/4k 仅限 8s；EU/UK/CH/MENA 的 personGeneration 仅 `allow_adult`；非英文未评估。
- CogVideoX：prompt ≤224/226 tokens；仅英文。
- LTX：分辨率须整除 32，帧数须 8n+1，最佳 <720×1280。
- Vidu：prompt ≤20000 字符，duration 1–16。
- Wan 2.2：上限 720P。
- **不是官方红线（本厂自订，lint 文案不得写「官方禁止」）**：禁精确秒数、禁多运镜、禁多人、禁文字/字幕、40–90 词。官方无一条如此规定；Seedance 反而要求全局约束里写「无字幕」。

## 五、拿不到官方文档的模型

- **Kling**：kling.ai quickstart 与 document-api 均返回 JS 空壳，正文不可取 → 结构/运镜/负面词一律「未载明」，仅时长借 Runway 官方目录转述。
- **Runway**：help.runwayml.com 两篇 prompting guide 均 403；只取到 docs.dev.runwayml.com/guides/models 的模型目录。
- **Pika / Higgsfield**：未取到任何官方提示词文档，不写。
- **HunyuanVideo 提示词语法**：README 仅参数表，无 prompt 规范 → 未载明。

---
**验证声明**：读数 16 次网页取源（非仓内文件）；成源 11 家（A 级官方站/官方 repo），Kling 与 Runway prompting 正文失败面已列 §五；结论分级：表内事实=直读原文，转述处已标「Runway 目录」；未用第三方博客充当官方。抓取日 2026-10-20。