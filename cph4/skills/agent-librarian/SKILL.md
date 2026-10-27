---
name: agent-librarian
description: 智能体库库长席（集团 Agent/Skill 总册管理）。Use when discovering which agent, expert, skill or seat handles a task, registering a new agent or skill into the library, auditing library consistency, running the weekly library review, translating a CEO plain-language request into the right expert invocation chain, or when any session asks who owns a responsibility. Triggers on 智能体库/找专家/找席位/谁负责/登记新专家/库审计/库周审.
---

# 库长席工作法

总册=`cph4/agents/AGENT-LIBRARY.md`（一切答案在册·先读再动）；治理法=同目录 `GOVERNANCE.md`。

## 发现（这事谁干）
1. 读总册 §0 CEO 直达速查 → 命中即按行调用。
2. 未命中 → §三 Skill 索引按域查 → §四 城市线专册（城市任务）→ §一 常设机构位（机制类问题归机构位非席位）。
3. 仍无 → 子代理 explore 搜 cph4 正典与各司 README 技能行；真无 = 缺口 → 走登记。

## 登记（产出新专家·当窗登记律）
- 重复出现的角色被第二次执行、或按技能三问（周频复现/步骤稳定/知识难自持）过三 → 建 skill（走 skill-creator；canon 落 `cph4/skills/<name>/`；命名=小写连字符）+ 总册 §六表 append 一行（格式在表头）→ pathspec 提交上链。
- 登记 SKU 必带调用面（skill 名/canonical 路径/宿主机）；状态如实（ACTIVE/PLAN/RETIRED）。
- 装机面：canon 写毕跑 `Tools\agent-library-sync.ps1` 装本机（次会话生效）。

## 审计（周审步·CEO-PROXY 周日深复盘承载）
1. `python Tools/agent-library-audit.py` → 孤儿（canon 无登记/登记无实体）当窗补。
2. 缺口扫描：近 7 日 orders 各司产出域 vs 总册覆盖 → 有产出无席位=建卡（技能三问裁决是否建 skill）。
3. 回执行：AGENT-LIBRARY.md 更新日志+登记表；LOG 记库行（席位数/新增/孤儿 0）。

## 红线
- 不登记=不存在；禁重复建已有席位（先查册·命令查重律）。
- 总册只做导航不复述正典（复述禁令）；结构变更须更新日志+orders 溯源。
