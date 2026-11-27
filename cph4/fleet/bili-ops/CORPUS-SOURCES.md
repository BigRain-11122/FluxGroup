# 语料与素材来源台账（B站回复线）

| 用途 | 来源 | 许可 | 规模 | 采用情况 |
|---|---|---|---|---|
| 真人回复基准 / 后续 LoRA | linyiLYi/bilibot `data/train.jsonl` | Apache-2.0（仓库级） | 12951 条 chat 格式评论-回复对 | **采用**（本地落 `bili_corpus/train.jsonl`，仅内部分析与训练用，不再分发） |
| 中文词库 | fighting41love/funNLP | 无 license 文件 | 174MB 领域词库 | **未采用**（缺许可；且不含口语/网络用语语料） |
| B站评论数据集 | SunHao0729/bilibili_automobile_comments_2025 | 无 license | 15MB | **未采用**（0 星、无许可、领域受限） |
| 弹幕转换工具 | m13253/danmaku2ass | GPL-3.0 | — | 不需要（与本线无关） |

## 使用边界

- bilibot 语料仅用于：① 统计真人长度/标点/语气词分布以校准闸；② 后续本地 LoRA 微调；③ 盲评时抽真人回复做对照。
- 不把语料原文写入交付物或线上回复（防复读与版权问题）。
- 若后续商业化，需复核 bilibot 数据来源（其原始评论来自 B 站公开评论区，仓库以 Apache-2.0 分发代码与数据，商业使用另行评估）。