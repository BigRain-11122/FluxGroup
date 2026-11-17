# 真人话术语料与微调路线（HUMAN-CORPUS v1）

> 令源：CEO 2026-11-17「github和开源论坛上有相关的话术素材就拉下来微调，我不喜欢ai感，要有真人带入 有情绪 有思想」
> 工具=`Tools/fleet/human_corpus.py`（拉取/清洗/打标/许可闸），语料落 `cph4/fleet/social/corpus/human/`。

## 一 先说清一条硬边界：能不能拿来训，看许可不看技术

| 源 | 内容 | 许可 | use | 结论 |
|---|---|---|---|---|
| `FunnySaltyFish/bilibili_comments_crawl` | 真实 B 站评论对话（含颜文字、口语、互怼） | 仓库自述「仅学习交流、不可商用」 | **reference** | **只做风格参照与评测，不进训练集** |
| 自有采集（我方账号可见的公开评论） | 平台评论/弹幕 | 自有 | **train** | 唯一可以训练的料 |

技术上都拉得下来、都洗得干净，但拿"仅学习交流"的数据去训商业模型，是把风险藏进权重里。这条闸写在代码里（`use != train` 永不进训练集），不靠记性。

## 二 本轮实拉结果（2026-11-17）

- 下载 9 个文件、**302 句**原始 utterance
- 清洗后 **152 句**入库：去重 115、超长 29、含联系方式/链接 6
- 分布：类型「其他 109 / 提问 33 / 夸奖 3 / 打卡 2 / 玩梗 2 / 挑刺 2 / 催更 1」；情绪「平 144 / 喜 5 / 怒 2 / 哀 1」
- 读数：这批是早期视频的闲聊式对话（"兄弟你还在吗""貌似没人来"），**人味够、类型分布偏**；打标规则也偏 B 站短视频语境，需要按平台调词表。

## 三 微调可行（本机实测过）

- `mlx_lm 0.32.2` + `python -m mlx_lm lora` 入口可用 → **Mac 上可以直接 LoRA 训 Qwen 4B/9B**，不需要 CUDA、不需要 peft。
- 建议参数（4B，rank 8，lr 1e-5，batch 1-2，iters 300-600）：训完产出 adapter，`mlx_lm.generate --adapter-path` 挂上即用；ollama 侧可用 Modelfile 引用（下一版再做）。

## 四 训练门槛（不到就不训，这是纪律）

1. **train 集 ≥2000 条**自有采集（现在 0 条，因为 B站 还没登录、评论还没进语料）。
2. **评测集就位**：现有 38 题 + 新增"情绪/观点/人味"题各 10 条，红线题必须 100% 安全。
3. **对照组**：同题集上，LoRA 版 vs few-shot 版人工盲评，LoRA 版通过率高出 ≥10pt 才留。
4. 内存：训练时只驻 4B（不叠 9B），训完 `ollama stop` 释放（本轮实测 runner 会膨胀到 8.8GB）。

## 五 不用训练也能立刻降 AI 感（先做这个）

真人语料的 80% 价值在**示范**而不是**权重**：把 reference 语料按类型/情绪取样进提示词（few-shot），今天就能让回复像人说话。正典 `REPLY-VOICE-SPEC-v3` 已证过这条路径（纯正向判据 + 好样本，7B 达到"B站中位数"）。

所以顺序是：**先 few-shot 吃满人味 → 再攒够自有语料 → 最后 LoRA 精修**。跳过前两步直接训，只会把 152 条的风格训成口头禅。

## 六 下一步（按优先级）

1. 扩源：继续找**许可干净**的中文评论/对话语料（GitHub 优先，HF 本机不通），每个源先登记 license/use 再拉。
2. 打标升级：按平台分词表（B站/抖音/小红书/微博各一套情绪与类型词），当前规则是 B站短视频口径。
3. 自有采集：B站 登录后把评论灌进 `corpus/`，`use=train` 自动成立。
4. 攒够 2000 条后跑 LoRA，按第四节四道门槛验收。

## 七 复跑

```bash
python3 Tools/fleet/human_corpus.py --src bili_comments_crawl    # 拉+洗+打标（reference）
python3 Tools/fleet/human_corpus.py --from-dir cph4/fleet/social/corpus --use train  # 自有采集
python3 Tools/fleet/human_corpus.py --stats                      # 看可训练量
python3 Tools/fleet/human_corpus.py --gate                       # 三条门槛（量/红线/盲评）rc=0 才许开训
python3 Tools/fleet/human_corpus.py --self-test                  # 9/9 判据自检
```

## 八 批量补货（2026-11-17 立）

24h 学习循环每 20 分钟只抽 1 条视频 3 页评论，一天撑死几百句；要凑 2000 条得用
`Tools/fleet/social_sweep.py` 成批拉，但节奏仍按真人：视频之间过 `social_riskguard`
（20-60s 抖动 + 会话休息）。

```bash
launchctl bootout gui/$(id -u)/com.fluxgroup.sociallearn     # 同一 profile 不能两开
python3 Tools/fleet/social_sweep.py --videos 8 --comment-pages 8
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.fluxgroup.sociallearn.plist
python3 Tools/fleet/human_corpus.py --from-dir cph4/fleet/social/raw
```

两个接口事实（踩过，别再试）：

1. 评论：`/x/v2/reply?type=1&oid=aid&pn=N&ps=20&sort=2` 带登录 cookie 直接 code=0，
   一次 20 条；DOM 侧评论区在封闭 shadow DOM 里，`inner_text` 取不到（永远 0 条）。
2. 弹幕：`x/v1/dm/list.so` 与 `comment.bilibili.com/<cid>.xml` 都返回 **raw deflate**，
   Playwright 的 `APIRequestContext` 解不开（`failed to decompress 'deflate'`），加
   `Accept-Encoding: identity` 也照旧。正法是 `/x/v2/dm/web/seg.so?type=1&oid=cid&pid=aid&segment_index=N`
   （protobuf，字段 1=DanmakuElem、其中字段 7=正文），6 分钟一段，实测一段 77 条。
   弹幕要过"像人话"筛：≥4 字符、含中文或字母、非纯刷屏（字符种类 ≤2 直接丢）。
3. 采源要按**评论数倒序**（`--sort-by-reply --min-reply 500`）：爆火视频一条能给上千条，
   同样的时间先吃油水大的。实测好评论密度 7%→11%（评论比弹幕产出高得多）。

## 九 训练工作流（2026-11-17 立·对齐社区口径）

社区做法对照（只偷机制，不引框架）：

| 社区做法 | 出处 | 我们落地成什么 |
|---|---|---|
| 少而精胜过海量（1k 精选 > 50k 抓取） | LIMA (NeurIPS 2023) | 品味闸只放 PASS 进集，2245 条也照训 |
| 用强模型给每条打分再筛 | AlpaGasus (ICLR 2024) | 五维确定性判据替代（无云依赖，可复算） |
| 近重复必须清（MinHash/SimHash+LSH） | NeMo Curator / Milvus | `train_build.near_dedup`（SimHash 64bit，汉明≤6） |
| 复杂度/质量/多样性三维选 | DEITA | 单视频占比上限 + 句长分桶切分 |
| **checkpoint 按任务质量选，不按 loss 选** | 2026 实践综述 | `train_eval.py` 逐点跑同一批题、按均分+PASS 率排名 |
| 先有评测闭环再训；fine-tune 管形式不管事实 | 同上 | `comment_taste` + 固定题面 + 事实包在发送口兜底 |

一条命令跑完，三个硬门不过就停：

```bash
python3 Tools/fleet/train_pipe.py            # 门1 门槛 → 造集 → 训练 → 门3 选点 → 盲评表
python3 Tools/fleet/train_pipe.py --build-only
```

- 门1 语料量 + 红线召回（`human_corpus.py --gate` rc=0）
- 门2 训练集 ≥500 条（太少只会抄碎片）
- 门3 最优 checkpoint 必须超过基座，否则不采用、不出盲评表

**选点实测（20261117-165812，12 条/点）**：base 54.7/33% · iter100 65.8/50% ·
iter200 **70.2/58%（逻辑 26.7 最高）** · iter300 66.1/67%。只看 PASS 率会选 300，
只看 loss/最后一个点会掉进 300——**两个指标一起看才不选错**。

解码侧也补了一条：多生成 2 条候选再择优（先按句内 4 字自我重复度升序、再按长度降序）。
开候选择优后同尺比分 75.9/87% vs 基座 67.7/73%（+8.2pt / +14pt）。

**两次踩坑，别再试**：
1. 自写 `logits_processors` 做重复惩罚，scatter-add 一写错就把分布打崩——基座和 LoRA
   同时只吐 `!!!!!!!!`。要治复读用候选择优，不要动 logits。
2. 直接把最后一个 checkpoint 拿去发：iter300 的均分和逻辑分都低于 iter200。选点必须
   走 `train_eval.py`。




### 训练后复测（20261117-191945 · 16 层/500 步/3156 条 · 每段 5 条）

补采按段定向（争议/新手/亲子/整活 5 组关键词→99 源→+1.2 万条评论），
语料 20253→31004、过闸 3381、训练集 3156。总评**首破 10pt**：base 63.5 → LoRA 73.7
（+10.2），选点 iter500（前 400 步都不如它，说明大集+多层需要更多步）。

| 段（5 条/段） | base | LoRA | 判断 |
|---|---|---|---|
| critic | 50.0 | **85.6** | +35.6 |
| shallow | 41.6 | **79.8** | +38.2 |
| ai_creator | 52.0 | **77.2** | +25.2 |
| family | 54.2 | **75.4** | +21.2 |
| student | 41.8 | **72.2** | +30.4 |
| peer_pro | 55.0 | **72.8** | +17.8 |
| feeler | 58.0 | **68.8** | +10.8 |
| music_seeker | 30.0 | **56.8** | +26.8 |
| requester | 72.2 | **79.6** | +7.4 |
| memer | 44.2 | 48.0 | +3.8（仍弱） |
| traditional | 48.0 | 51.4 | +3.4（仍弱） |
| **beginner** | 97.2 | **74.6** | **-22.6 退化** |
| **tech_nerd** | 60.0 | 45.6 | **-14.4 退化** |

两条退化的成因（下一步要治的）：这两个段要的是"耐心/具体"，而训练集主体是
B站口语短句——语气学到了，专业性与耐心反而被冲淡。方向：段位提示前置到最前、
提高这两段配额、或按段训多个 adapter。

硬件上限（实测，别再试）：32GB 统一内存上 4B-4bit **全层 LoRA @256 ctx 直接
Metal OOM**（16.2M 参数）；可行上限 = 16 层 @224。

## 十 人群细分（2026-11-17 立·颗粒度对齐）

要求：**懂得和不同人群打交道，按各人群的口味说话**。落法是"一套段位同时管四处"，
否则打标用一套、生成用一套、评测用一套，颗粒度永远对不齐。

正身 `cph4/fleet/social/AUDIENCE-SEGMENTS-v1.json`（13 段）+ `Tools/fleet/segments.py`：
每段带 **信号词（判据式，不写例句）**、**语言参数（字数带/语气/称呼/emoji 上限/是否用梗）**、
**该做/不该做**、**风险级**。识别多段命中报 primary+secondary，无信号落 generic（不猜）。

| 段 | 语料占比 | 说明 |
|---|---|---|
| generic 未识别 | 39.6% | 纯观感/闲扯，判不出人；按意图回，不硬套段 |
| shallow 浅层 | 19.5% | 谢谢/已三连/前排，一句轻回或不回 |
| tech_nerd 技术党 | 12.8% | 抠像/分镜/一致性/参数 |
| music_seeker 求歌 | 9.1% | BGM/曲名/出处，编错=硬伤 |
| peer_pro 同行 | 4.5% | 甲方/后期/接单 |
| memer 玩梗 | 3.9% | 要素察觉/狗头 |
| feeler 共情 | 3.9% | 想起/哭了/当年 |
| ai_creator AI创作圈 | 2.1% | 抽卡/首尾针/参考图 |
| 其余（beginner/student/requester/critic/family/traditional） | 各 ≤2% | 样本稀缺，见下表短板 |

**分段评测（20261117-175135 iter100，2 条/段）**

| 段 | 基座 | LoRA | 结论 |
|---|---|---|---|
| tech_nerd | 55.0/0% | **97.5/100%** | +42.5，最大收益 |
| feeler | 70.0/50% | **95.0/100%** | +25 |
| student | 60.0/50% | **83.5/100%** | +23.5 |
| traditional | 60.0/50% | **79.0/100%** | +19 |
| music_seeker | 64.0/50% | **79.0/100%** | +15 |
| shallow | 40.0/100% | **60.0/100%** | +20（该短的段按短判） |
| peer_pro / family / requester | — | 小幅提升 | — |
| critic | 85.0/100% | 77.5/100% | **-7.5 退化** |
| ai_creator | 95.0/100% | 92.5/100% | -2.5 |
| beginner | 85.0/100% | 82.5/100% | -2.5 |
| memer | 39.5/50% | 45.0/50% | 双方都不及格 |

**判据必须分段，不能一把尺子量所有段**：玩梗/浅层本来就该 6-12 字、没有逻辑主干，
用通用线量它们必然 0 分——看着像模型差，其实是尺子不对。`comment_taste.SEG_TUNE`
按段给 PASS 线与逻辑下限，`--per-segment` 出分段报表。

**已知短板（下一步补采目标，不是调参）**：critic 17 条、beginner 33 条、family 8 条、
memer 113 条——低样本段训不出来，挑刺段还会退化。补采要按"段"去挑视频，而不是按播放量。
