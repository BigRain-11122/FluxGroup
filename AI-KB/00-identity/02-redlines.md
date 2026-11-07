---
id: identity.redlines
title: 红线与治理摘要
layer: identity
questions: ["什么不能做", "谁能拍板", "怎么汇报"]
facts: ["docs/governance.md", "docs/orders.md", "CODELY.md"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: local-llm
---
## 铁律（违反即返工）
每张卡必须包含 line 且路径存在。卡内严禁出现机器名或绝对主机路径。回执必须有 rc 码，rc 非零时需带 error_class。

## 决策边界
P0 线 24 小时必须产出交付物。资产必须有 provenance 溯源信息。每个队列只能有一个写入口。GPU 租约需携带身份标识。

## 不许做的事
禁止发布件缺少 AIGC 隐式标识。禁止产品配方缺失 kill_criteria。禁止存在无调用者的孤儿脚本。禁止 state/ 目录被 git 跟踪。

## 汇报形式要求
当前版本为 1.0-20261102，新违规数为 118。需检查 I1 至 I14 共 14 项指标状态。未测项目一律标记为未测/未知。
## 我不知道的
本页只覆盖仓库里可核验的事实；各机运行时状态、商业数据与对外承诺不在本页。
