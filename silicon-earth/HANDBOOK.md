# 工作手册（流程 · 分工 · 仓库 · 提交）

> 原来分散在 PROCESS / TEAM / GIT-POLICY / REPO-MAP / INHERITED-RULES / RULES-TRIAGE / FLEET-ROLES 七份里，现在合成本页。
> **只读这一页，加上 START-HERE 与 DECISIONS，就够开工。**

---

## 一 一条边界

**写世界的活必须串行（一次一人）；不写世界的活可以并行。**
世界状态只有一个写者：`engine.py` / `settle.py` / `derive.py`。

---

## 二 仓库层与进不进 git

```
D:\FluxGroup\                  git 根
└─ silicon-earth\              工程根
   ├─ CONTRACTS\               契约（只有总控改）
   ├─ modules\m-*\             模块（一模块一 owner）
   ├─ tools\                   体检 / 交付 / 测试 / 总览
   ├─ REPORTS\                 测试与评审记录
   ├─ TASKS.json               任务板（可外置）
   └─ STATUS.md                总览（自动生成，不进 git）
```

| 进 git | 不进 git |
|---|---|
| 代码、契约、文档、TASKS.json、seed.json、people.json、origin-map.json、regions.json | `modules/*/dist/`、`__pycache__/`、`*.tmp`、`TASKS.lock`、`.board/`、`STATUS.md` |
| — | `events.jsonl`、`time.json`、`state.json`、`memory.json`（规划中移出，见 B22） |

---

## 三 并发怎么做（现在可用的那一种）

**把任务板放到工作区之外，锁跟着板走。**

```powershell
$env:SILICON_BOARD = "D:\FluxGroup\silicon-earth\.board\TASKS.json"
git -C D:\FluxGroup worktree add ..\wt-T03 -b agent/T03
cd ..\wt-T03\silicon-earth
python tools/world_ops.py claim T03 agent-a
```

实测：A 领走后，B 再领被拒，B 的 `status` 能看到同一份租约。

**仍然只能一个人干的**：world 写入三件套。

---

## 四 分工

| 谁 | 干什么 | 不能干什么 |
|---|---|---|
| 模块 owner | 写自己 `module.json` 里 `writes` 的路径 | 写别人的模块 |
| 总控 | 改 `CONTRACTS/`、`TASKS.json`、`MODULES.md`、本册 | 代写模块代码 |
| 内容 / 表现 | 文案、翻译表、页面（只读数据） | 写 `modules/*/data` |
| 算力池 | 在**副本**里跑长跑与批量实验 | 推主仓 |

现役只开「总控 + 世界 + 人」三席在一台机上；其余标灰，等 B23 远端租约。

---

## 五 一次任务六步

```bash
python tools/ready.py                       # 9 项，全过才开工
python tools/world_ops.py claim T03 <你>     # 领（2 小时租约）
python tools/agent_ops.py status <你>        # 该读什么、该跑什么、只许写哪里
python tools/agent_ops.py guard --agent <你> # 越界即红
python tools/deliver.py T03 <你>             # 越界 / 派生一致 / verify 三道门
git add -A -- . && git commit -m "T03: …"
```

接别人没做完的：`agent_ops.py takeover`；做不完要交班：`agent_ops.py handoff`，写清「做到哪、卡在哪、下一步」。

---

## 六 提交与分支

- 一交付一提交，首行 `T03: 一句意图`，≤50 字。
- **禁止在仓库根 `git add -A`**（会扫进别的业务线），用 `git add -A -- .` 或 `git add silicon-earth`。
- 一任务一分支 `agent/<T>`；合并只由总控 `--no-ff`；**合并后在 main 上重跑** `ready` + `validate` + `verify`。
- 回滚用 `git revert`，不改写已推送历史。

---

## 七 反模式（出现即停）

开两个会话写世界 · 不领活就开工 · 用 `release` 冒充交付 · 手写派生数据 · 贴输出代替退出码 · 为了让 verify 变绿改验收标准 · 交付后不提交。

---

## 八 继承下来的旧规则，接进代码的

| 规则 | 落在哪 |
|---|---|
| 文件名英文、无空格 | `repo_check.py` |
| 单件 >95MB 禁入 git、>20MB 警告 | `repo_check.py` |
| 代码不得含密钥 | `repo_check.py` |
| 提交首行 ≤50 字、带前缀 | `repo_check.py --msg` |
| 一脚本一条命令可跑 | `module.json` 的 run/verify |
| 测试前不许说完成 | `deliver.py` |
| 引用不复制、单一事实源 | 本工程全篇 |

不接的：`/CEO` 派单口令、机器让路律、周报夜轮、集团台账（另建即双账）、品牌登记。

---

## 九 现在还做不到的

| 做不到 | 卡在哪 |
|---|---|
| 两台机器同时推进世界 | 板在本机磁盘（B23 远端租约） |
| 多人同时写同一模块 | 单写者约束 |
| 状态文件与代码分仓 | B22 未做 |

---

## 十 维护

- 任何状态变化后：`python tools/status.py`（`ready.py` 会查它是否过期）。
- 本册只在规则本身变化时改；改一次记一行在 commit 里。
