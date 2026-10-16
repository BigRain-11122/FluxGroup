# 智能体库治理法 GOVERNANCE v1.0

> 正典位=cph4/agents/GOVERNANCE.md｜建库令=CEO 2026-10-16（见 AGENT-LIBRARY.md 头）｜执法主体=库长席（skill `agent-librarian`）+CEO-PROXY 周日深复盘库周审步。
> 承接不重立：建 skill 的工艺与门=技能律 P-2026-09-26-01（技能三问+技能律四条+寻源三路）+官方 skill-creator skill；本件只立**库的增长与保鲜机制**。

## 一 自增长三律（库自己长的机制）

1. **当窗登记律**：任何会话产出新专家行为（角色/流程被第二次执行、或按技能三问过三=建）→ 当窗建卡登记进 AGENT-LIBRARY.md §六登记表（append-only）+ 建 skill 走 skill-creator（canon 落 cph4/skills/）→ pathspec 提交上链。**禁干了不登**（不登记=不存在）。
2. **细分律**：既有席位连续承接 3 次以上跨域任务 → 拆子席位（先例=导演席拆 MV 导演/漫剧导演线；库长/合规/增长/城市生态五席本批先例）。拆分=原席位保留+新子卡登记，禁顶替删除。
3. **退役律**：席位 30 天零调用且正典已废 → 状态改 RETIRED（行不删·史可溯）；skill 同步停装（sync 跳过 RETIRED canon）。

## 二 周审律（持续更新引擎·CEO-PROXY 周日 21:43 深复盘固定片）

1. 跑 `python Tools/agent-library-audit.py`（skills↔总册一致性+孤儿检）→ 孤儿/缺口当窗补登记。
2. 缺口扫描：本周各司产出域（orders 近 7 日行+各司周报）vs 总册覆盖 → 有产出无席位=缺口 → 建卡或建 skill（技能三问裁决）。
3. LOG 记库行：`库审|席位数 N|新增 M|孤儿 0|缺口收窄 K`。判据（10-23 回访首测）：登记席位单调增、孤儿恒 0、缺口每周期收窄。

## 三 审计与分发工具

| 工具 | 用途 | 用法 |
|---|---|---|
| `Tools/agent-library-audit.py` | canon/项目级/用户级三面 skills↔总册一致性+孤儿检测 | `python Tools/agent-library-audit.py`（ASCII 报告·周审步用） |
| `Tools/agent-library-sync.ps1` | canon→本机安装一键（幂等·-WhatIf 先行） | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\agent-library-sync.ps1`（装后次会话生效） |

分发律：**canon=cph4/skills/ 唯一正源**（git 分发三机）；安装副本=.codely-cli/skills/（项目级·gitignored·次会话生效）；用户级 34 件（bm-a）=社区精选工具面，他机需要时按需移植 canon（移植=copy+登记+许可核验）。新机器入网/拉取后第一动作=跑 sync。

## 四 细则

- **CEO 直达面保鲜**：§0 速查表随新席位同步更新（CEO 说人话→秒查到专家）。
- **诚实律**：登记必带可验证调用面；PLAN 状态=如实标注（禁虚报 ACTIVE）。
- **外部池采用**：awesomeskills.dev / alirezarezvani/claude-skills(380·MIT) / CCGS 参照库=素材源；采用一律过 oss-harvest 五门（许可/活性/价值五问），禁裸搬。
- 版本：本件随批升版；库结构变更须 AGENT-LIBRARY.md 更新日志+orders 溯源。
