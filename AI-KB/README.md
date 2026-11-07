# AI-KB｜集团资料库（给 AI 读的）

> 本目录由 `Tools/kb/build_kb.py` 生成，**不要手改产物**；要改就改事实源或生成器，再跑一次。

## 给 AI 的三步读法
1. 读 `INDEX.json`：每篇文档的 id、路径、回答哪些问题、事实来源、生成时间。
2. 按层读：`00-identity`（是谁、红线）→ `10-business`（做什么）→ `20-engineering`（怎么做）
   → `30-operations`（怎么跑）→ `40-progress`（做到哪）→ `50-skills`（有什么能力）。
3. 要数字时读 `90-machine/facts.json`——正文里的数字都是它的转述，冲突时以它为准。

## 目录
| 目录 | 内容 | 什么时候读 |
|---|---|---|
| `00-identity/` | 组织、红线、术语 | 任何任务开始前 |
| `10-business/` | 15 条业务线逐线一页 + 组合总表 | 判断优先级与归属 |
| `20-engineering/` | 架构、工具目录、产物清单 | 动手改代码前 |
| `30-operations/` | 机队、主控脉、队列与卡 | 派单、排障 |
| `40-progress/` | 进度快照、在飞清单、缺口 | 汇报与决策 |
| `50-skills/` | 技能库、席位分工 | 选技能、找人 |
| `90-machine/` | facts.json（机读事实） | 需要精确数字 |

## 每篇文档的固定骨架
`front-matter`（id/title/layer/questions/facts/generated_at/written_by）+
`一句话 / 结构 / 关键约定 / 怎么验证 / 我不知道的`。
「我不知道的」一节是硬要求：写不出来就说明这篇在装懂。

## 新鲜度
`generated_at` 超过 24 小时即视为过期，重新生成：
```
python Tools/kb/build_kb.py            # 调本地模型写叙述
python Tools/kb/build_kb.py --no-llm   # 只刷事实与模板
python Tools/kb/build_kb.py --check    # 校验齐全与新鲜
```
