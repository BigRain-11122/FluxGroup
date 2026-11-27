# 历史 CEO 原话检索图谱（2026-11-04 立）

## 一、会话记录到底存在哪

本机是 Codely CLI + 桌面版（Tuanjie Cowork）共用一台机，记录分两套：

1. **CLI 会话（有正文）**：`C:\Users\sjs20\.codely-cli\tmp\<projectHash>\chats\<sessionId>.jsonl`
   - 按工作目录分 hash 桶，**共 17 个桶**（2026-11-04 实测）。只扫一个桶会漏掉大部分历史。
   - 每个会话可有 `<sessionId>.genN.jsonl` 压缩代，越早的话在越老的 gen 里。
2. **桌面版会话（只有元数据）**：`C:\Users\sjs20\.codely\sessions\<id>\sessions.sqlite`
   - 表只有 `session_metadata` 与 `session_bookmarks`，**没有消息正文**。想从桌面版捞原话，此路不通。

## 二、CLI JSONL 的实际字段（与 session-history 技能描述有差异）

- 记录用 `t` 字段，不是 `type`；`header` 是首行。
- 消息在 `msg` 里，**角色字段是 `msg.type`（`user` / `gemini` / …），不是 `msg.role`**。
- 正文：`msg.content` 可能是字符串或 `[{text}]` 数组；空时看 `msg.canonicalParts`。
- `thought: true` 的 part 是推理，不是正文。

## 三、过滤噪音的方法

真实 CEO 输入混在大量自动化提示里，以下前缀要排除：

- `[agent-auto] This is the Codely CLI`
- 以 `【` 开头（巡视席 / CEO 总调度代理席 / 事件班）
- `Task MUST complete`
- `<bg_task_done`（子代理完成事件）

## 四、现成脚本

`.codely-cli/tmp/extract_all_user_msgs.py`（全桶扫描，按日期抽用户消息）
- 改 `TARGET = datetime.date(...)` 换日期；输出 `.codely-cli/tmp/user-msgs-<日期>-all.txt`。
- 输出行格式 `[桶hash前8/会话前8 L行号] 正文`，可直接 grep 关键词再回原文件读小窗口。

## 五、判据

- 找不到某人说过的原话时，先说清「扫了哪些桶、命中多少条」，再请对方定位，不要用印象补。
- 2026-11-04 实测：11-03 全天 17 桶共 217 个会话文件、334 条真实用户消息。