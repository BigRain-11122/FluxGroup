# 隔离区（2026-11-03）

| 技能 | 原因 | 取代者 |
|---|---|---|
| model-routing | 内容是外部通用版（gpt-5-codex / gpt-5 / gpt-4.1-nano），本集团无这些模型，照用即误判；且无 description，路由永远匹配不到 | `fleet-doctrine`（模型路由）+ `cph4/fleet/LOCAL-LLM-ROLE-20261103.md`（本地模型实测职责） |

规则：隔离件不出现在激活面；需要复活必须先本土化并加 description。
