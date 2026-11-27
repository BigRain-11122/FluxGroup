# BigLoom 智能体与完工判据（2026-11-25 立）

> CEO 令：「不要问我，自己科学推进，并建立好智能体，直到确认完美完成。」

## 一、六席（已并入 AGENT-TEAMS-v1.json，v2-20261125，不另立一套）

契约仍是 `id/name/duty/cls/out/judge/cad`，v2 增补两项：
`numbers="rule-only"`（数字由规则算）与 `facts_cmd`（数字从哪条命令来）。

| 侧 | 席 | 职责 |
|---|---|---|
| control（账与标准） | `C-LOOM-STD` | 守去 AI 味/严谨/审美三闸的阈值与负控 |
| | `C-LOOM-BOOK` | 两本账分账，只判"够不够开训" |
| | `C-LOOM-DISPATCH` | 派单收执；逾期 72h 升 BLOCKED-JUDGE |
| visual（生产） | `V-LOOM-COLLECT` | 三通道采集执行 |
| | `V-LOOM-DRAFT` | 出稿（写完自过三道闸才交） |
| | `V-LOOM-PUB` | 上架（默认草稿，--live 三保险） |

节奏写在 `AGENT-CAPACITY-v1.json` 的 `seat_policy`（记账/派单/采集 `gate=time`，
标准/出稿/上架 `gate=event`）。**新席不注册 policy 就永远被判"输入未变"跳过**。

## 二、数字绝不交给模型（本日最重要的一条）

首跑 C-LOOM-BOOK 时，2B 模型把入参 `style_n=20` 直接抄成 `trainable_n=20`
（真实是 14）——`judge` 只看"键齐不齐"，于是**假绿通过**。

正解：带数字的席一律
- `out.keys` 里**不出现数字字段**，只留判断键（verdict/gate/why）；
- `numbers="rule-only"` + `facts_cmd`（如 `python3 Tools/fleet/gzh_trainset.py`）；
- 探针会检查"标了 rule-only 却没给 facts_cmd"并报硬红。

## 三、两件仪器

| 器 | 作用 | 自检 |
|---|---|---|
| `Tools/fleet/fleet_sync_probe.py --status` | 软链 / 各机车道新鲜度 / 问询卡逾期 / 席表完整性 / 体检硬项 / 两本账 | 9/9 |
| `Tools/fleet/bigloom_done.py` | **完工判据八条**，全绿才可宣布完成 | 10/10 |

八条判据：softlinks / audit_hard / seats_contract / loom_seats_ran（今日台账里
必须有 BigLoom 席 ok=true，防"设了不跑"）/ sync_probe / corpora / archive（归档件必须
全在 git 里，可回滚）/ selftest。

## 四、本日修掉的五个真缺陷（都由仪器抓出）

1. **数字由模型算**（见 §二）。
2. **审计器自噬**：`REPO-AUDIT.json` 自己列出"不存在的工具"，下一轮又把它当引用 →
   真失效引用 3→10。修法：`SELF_OUTPUTS` 排除自身产物与 `cph4/fleet/state/`。
3. **判据器递归（事故）**：把判据器自己列进"要自检的器"，`--self-test` 调 `--self-test`，
   **指数级起 881 个进程、负载冲到 8.5**。修法双保险：自检清单里跳过 `__file__`
   ＋ 子进程注入 `BIGLOOM_DONE_CHILD=1`，入口见哨兵直接短路返回。
   （姊妹实锚 2026-11-11：fleet_doc 调 quality_score 形成递归，靠 pkill 清场。）
4. **引用三分类**：真失效 / `planned`（行内含 未建·先建·待建·needs_build·下一步·"写 `"）/
   `historical`（LESSONS*、LEARNING-LEDGER 里的 evidence 记的是"当时存在过"）。
   不分类会把 7 个待建工具与 1 条历史证据全报成断链。
5. **判据器自检用子串判负控**：`"0 行" in why` 被"风格 **20 行**"误命中 → 自己假红。
   子串判定不能用于负控，改成"路径指到不存在目录必须判 False"。

## 五、路径常识（会咬人）

- **脚本**在 `Tools/fleet/`；**数据**在 `cph4/fleet/`。两者同名不同物，
  混用会让判据器把"脚本不存在"报成 6 个器全挂。
- `Tools/repo_audit.py` 在 `Tools/` 下（只剥一层），`Tools/fleet/*.py` 在 fleet 下（剥两层）。

## 六、当前状态与残留

- 判据 **8/8 全绿**；26 个工具自检 0 失败；今日席台账 4 条（C-LEAD 如实记失败）。
- 外部依赖未解：传家宝（bm-c）22/5985/8790/445 全不通 → visual 三席未在其本机跑，
  114 个问询卡等它同步 git；1124 处硬编码绝对路径是可移植性债。
- 7 个 `planned` 工具待裁：`submit_batch` / `order_sink` 在队列链路上是硬缺口，
  其余（cost_attrib、slo_budget、domain_page、pricing_sheet、game_shots）要么建、要么从计划里删，
  不许挂在文档里当假待办。
