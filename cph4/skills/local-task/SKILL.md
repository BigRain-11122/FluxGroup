---
name: local-task
description: 用本机常驻轻量模型做分类/摘要/打分/抽取，走统一题型与 JSON schema，带调用账与规则复核。当需要把一段文本归到固定类别、压成一句摘要、给产出打完成度、或抽出"谁等什么"关系时使用；不要自己临时拼 prompt。
---

# local-task：本地模型的任务层

## 何时用
- 需要**固定题型**的轻量判断：分类（classify）、摘要（summarize）、打分（score）、抽取（extract）。
- 需要标量小、可核验、能记账的模型调用——而不是让它自由发挥写一段话。
- 需要"先本地后云端"：本机模型不可达时会回落到共享脑；两边都不可达就明确失败，不静默降级成付费云调用。

## 四条硬规矩
1. **模型只做初筛，不做裁决**。凡结论会改变派单/结案/对外说法的，必须再用规则复核（数字用规则算，不交 4B）。
2. 输出必须是 JSON 且含该题型的必填键；过不了就重试一次，再不过记 FAILED，不许把"看起来像"当通过。
3. 一次一件、串行调用（本机统一内存与常驻模型共用，并发没有收益）。
4. 有日上限（默认 300 次），超了明确返回 `daily-cap`。

## 用法
```bash
# 单次
python3 Tools/fleet/local_task.py run --task classify --text "bm-a 打包卡连续 3 次 E-ARTIFACT"
# 用文件
python3 Tools/fleet/local_task.py run --task summarize --file some.log
# 入队（供脉冲慢批持续消化）
python3 Tools/fleet/local_task.py enqueue --task classify --text "..." --tag supply:MiniGame
# 手工消化一批
python3 Tools/fleet/local_task.py drain --limit 3
# 账与自检
python3 Tools/fleet/local_task.py stats
python3 Tools/fleet/local_task.py self-test
```

## 题型与 schema
| 题型 | 必填键 | 用途 |
|---|---|---|
| classify | `label` + `reason` | 归到 需派单/需工具/需CEO/需挂起/不用管 |
| summarize | `one_line` + `facts[]` | 一屏摘要 |
| score | `score` + `why` | 产物完成度 0-100 |
| extract | `items[{who,what}]` | 抽"谁在等什么" |

## 已知能力边界（实测）
- 2026-11-04 自检 4/4 通过，单次 0.7–2.0s。
- 同一天对"缺料归因"做过 3 条分类：4B 三条全判错（把工具缺失判成需 CEO），规则复核全部纠正并留痕（`rule_override`）。**所以 classify 的输出必须过规则复核**，标记为 `supply:` 的请求会自动复核。
- 不适合：算术、跨文件推理、需要事实核对（这类交给脚本或上云席位）。

## 退出码
- 0 正常；2 有失败/题型自检未通过；3 模型不可达或入参非法。