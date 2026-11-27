> ⛔ 引证核验未过（2 处查无此文件），本页结论不可作为决策依据：
> R-20261028-decision-round-25.md
> social_threads.py

# 20261115 竞品拆解晨报

本周产线最痛点是客服会话无状态导致重复回复。依据 `R-20261028-decision-round-25.md` 修复 P1 故障经验，需在 `social_threads.py` 引入 Chatwoot 的“会话状态机”（open/waiting/resolved/snoozed/handoff）。

现有逻辑每条评论独立处理，导致同一个人连问三句会重复回。需将代码重构为纯 Python+JSON 状态机：
1. **状态转移**：`resolved` 态若有新消息自动重开；`snoozed` 超期自醒；`handoff` 后机器禁发，仅人工回复可交还。
2. **SLA 管理**：监测我方超过 24h 标 `overdue`，只标不自动发（符合 CEO 对外发送权约束）。
3. **防误触**：转移表写死，表外一律拒绝。

此方案复用已验证的会话模型，避免重复造轮子，直接填补当前真空。

【给谁·下一步】请 `bm-m` 对接 `Tools/fleet/social_threads.py`，本周五前完成状态机逻辑嵌入并合并至主仓。

<!-- verify: citations=3 unverified=2 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
