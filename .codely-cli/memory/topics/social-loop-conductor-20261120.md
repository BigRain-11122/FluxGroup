# 养号自驱环路（social_loop）：采/训/验/调各有人负责（2026-11-20 立）

## 一、为什么要有它

采集（social_learn）、训练（trainloop）、验收（accept_run）、调参（tune_loop）四件工具都在，
但**没有主人**：谁决定"这段采多少算够"、"训完谁验"、"验不过怎么调"没人答。实测三处空转：

1. `tune_loop` 连续三轮 `proposals=[]`——只扫 `maxlen`/`min_human` 两个参数，
   后者被 `APPLY_SAFE` 禁用（降 min_human 能提通过率，但那是放水）。
2. 段内语料差 16 倍（traditional 1 行 / shallow 2294 行），没人按缺口补。
3. 判 KEEP 只用 n=10，而同件两次评测差 24 分（79.9 / 55.9）——验证没有功率。

## 二、它只做三件事

`Tools/fleet/social_loop.py`（launchd `com.fluxgroup.socialloop`，300s 一拍）：

1. **SENSE**：每段一张矩阵（可用行 / 目标 / 缺口 / 最近判词 / 评测 n / 龄期），落 `SOCIAL-LOOP.md`；
2. **DECIDE**：一拍只派一件事，优先级 **缺料 > 功率不足 > 调参**；
   采集让路（会话时段 / 10 分钟内采过）时**顺延**到下一优先项，不整拍空转；
3. **ACT**：派工并以**产物**验收，落 `SOCIAL-LOOP-LEDGER.jsonl`。

训练仍归 `train_forever`（它按数据增长自己开训）——本器只发现"该训却没训"并标红，
**不另起一套调度**，避免两处判据互相打架。

## 三、三条硬判据（都是踩出来的）

1. **采集按段定向**：先把 `VIDEO-TITLES` 的标题分类到段，只采该段已知视频；
   该段没有已知视频才退回按评论数总榜（并在台账写明"退回"）。
2. **采集以"本段净增行数"验收**：采到一堆别段的行、本段零增长 = `NOPROGRESS`，
   连续两次进 24h 退避；崩溃（delta=None）记 `FAIL` 而不是 NOPROGRESS。
3. **验证必须落判词**：n=30 重验后调用 `train_forever.judge_keep`（同一份阈值，不另立），
   把 KEEP/REJECT 写回 `TRAIN-LOOP-LEDGER`；只跑评测不落判词等于验了个寂寞。

## 四、这一轮抓到的两个假绿（都已修）

1. **判据读退役文件**：`QUALITY-PASS.jsonl` 自 16:11 起全仓无人再写，真实产物是
   `own_collected → corpus_bake → BAKED-v1.jsonl`（带 seg/verdict）。旧判据把可用行数
   少算一个数量级（5720 vs 50157），`social_24x7.segment_counts` 同病，一并改读 BAKED。
2. **n=10 的 KEEP 是噪声**：craft_learner 的 n=10 KEEP 在 n=30 重验下是 **-3.2 分**（判 REJECT）。
   相关：`segments.style_block` 直接取 `row["do"]`，而该段规格只有 `note` → 该段评测整段崩，
   只崩一段极难发现。

## 五、操作面

| 动作 | 命令 |
|---|---|
| 看矩阵/一屏 | `python3 Tools/fleet/social_loop.py --status` |
| 只判不做 | `... --once --dry` |
| 跑一拍 | `... --once` |
| 自检（9 条含退化控制） | `... --self-test` |
| 供给目标（只决定先补谁） | `cph4/fleet/social/SUPPLY-TARGETS.json` |
| 调参单源（eval_n / kind_share / maxlen / min_human） | `cph4/fleet/social/TUNE-PARAMS.json` |

解释器是分裂的：`playwright` 只在 `.venv-housing/bin/python`，`mlx_lm` 只在
`~/.pyenv/versions/3.13.18/bin/python3`，脚本按能力探测（`_py_with`），不许写死。

## 六、已知边界（别当成已完成）

- `traditional`(1) / `family`(9) 这类段采集源本身供给极少，可能到不了目标；
  到量后按实测决定继续补还是接受现状，**不许一直挂红当 KPI**。
- `kind_share` 已作废，换成 `ask_floor=0.20` 并被 `train_build` 真实读取（低于下限只报警）。
  原因见下节决策 1：重配比本身被判有害。
- 出稿侧的开头撞车、具体性约束仍靠闸外的整批判据，未进本环路。

## 七、2026-11-20 三项科学决策（依据 + 可证伪方式）

1. **训练集复刻真实分布，取消人工重配比。**
   依据：真实 PASS 8893 条 = 提问 25.1% / 挑刺 2.3% / 夸奖 15.1%；
   旧重配比产出 = 提问 9% / 挑刺 36% / 夸奖 55%。根因是 `_kind()` 的 4 分类：
   命中"不/没/别/差/难"即判挑刺（"没想到""不难"全中），48.8% 的"其他"被折成夸奖。
   → "12 条稿 9 条泛夸"是**训练分布被自己做偏**，不是模型能力问题。
   可证伪：同语料两种配方各训一件，n=30 同题对决；若重配比不差于自然分布，本决策即错。
2. **稀薄段记"供给空"，不许天天挂红。**
   依据：traditional 1 行 / family 9 行，且无已知视频可定向。
   处置：连续两次零增长且无已知视频 → `SUPPLY-EMPTY.json` 记时间，7 天后复探。
   可证伪：复探若采得到，说明"空"是采集姿势问题而非供给问题。
3. **验证功率 n=30，高功率否可推翻低功率留。**
   依据：同件两次 n=10 差 24 分；craft_learner 的 n=10 KEEP 在 n=30 下 -3.2 分。
   可证伪：n=30 同件重复两次仍差 >10 分，则 30 仍不够。


## 2026-11-20 养号四环主人（L1 迁入原文）
[2026-11-20 16:40:46] [2026-11-20] 养号四环（采/训/验/调）有了主人=`Tools/fleet/social_loop.py`（launchd `com.fluxgroup.socialloop` 300s 一拍）：SENSE 出每段矩阵（行/目标/缺口/判词/n/龄期）→ 一拍只派一件事（缺料>功率不足>调参）→ 按产物验收落台账；采集让路时顺延不空转，训练仍归 train_forever 不另起调度。三条硬判据=①采集按段定向（标题分类到段，只采该段已知视频，无则退回总榜并写明）②以"本段净增行数"验收，零增长两次进 24h 退避，崩溃记 FAIL 不记 NOPROGRESS ③验证必须落判词（n=30 重验后调 `train_forever.judge_keep` 同一阈值写回台账）。同轮两个假绿：`QUALITY-PASS.jsonl` 自 16:11 起无人写、真实产物是 BAKED-v1.jsonl（两处判据少算一个数量级 5720 vs 50157）；craft_learner 的 n=10 KEEP 在 n=30 下是 -3.2 分（已下架，路由加"高功率 REJECT 推翻低功率 KEEP"）。解释器分裂：playwright 在 `.venv-housing`、mlx_lm 在 pyenv 3.13.18，按能力探测。全文=`topics/social-loop-conductor-20261120.md`
