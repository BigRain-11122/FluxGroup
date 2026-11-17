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
python3 Tools/fleet/human_corpus.py --self-test                  # 9/9 判据自检
```
