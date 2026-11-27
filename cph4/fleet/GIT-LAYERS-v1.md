# Git 分层与分类规范 v1（2026-11-07）

一句话：**按"变更频率 + 是否可重建"分层，按"谁读"分类。** 不分层的结果就是现在这样：6102 个跟踪文件里 4300 个挤在 `cph4/fleet`，根下平铺 164 个，冲突 96% 来自混合存放的状态文件。

## 五层（按变更频率）

| 层 | 目录 | 变更频率 | 能否重建 | 进 git | 策略 |
|---|---|---|---|---|---|
| **L0 代码** | `Tools/`、`*/Tools/`、脚本 | 低（每次改码） | 否 | ✅ | 正常版本控制，手写件 |
| **L1 正典** | `cph4/fleet/*.md`、`*.json`（大写规范件）、`docs/`、`CODELY.md` | 低 | 否 | ✅ | 正常；冲突必须人工判 |
| **L2 账本** | `PRODUCTION-QUEUE.jsonl`、`PRODUCTION-BACKLOG.jsonl`、`lanes/`、`queue-receipts/` | 高（每分钟） | 部分 | ✅ | 分发通道，必须可拉 |
| **L3 归档** | `archive/`、`_archive-*`、`audits/`、`conversions/` | 只增不改 | 否（是结果） | ✅ | 按月分目录，标 generated |
| **L4 运行时** | `state/`、`radar/`、`chief/`、`sync/`、`memory-slim/` | 每秒 | 是 | ❌ | gitignore，不进 git |

**判断归属只需问两题**：① 删掉它会不会丢信息？会→进 git。② 它是不是每秒都在变？是→不进 git。

## 为什么 L2 必须留在 git

`fleet_lane.lane_payload()` 从 **origin** 读 `lanes/<node>.json` 取卡，`queue-receipts/` 是机队上报回执的通道。这两类一旦移出 git，机队就永远拿不到新任务——我在 11-06 干过一次，把派单通道切断了。

## 分类规则（新内容放哪）

1. **正典与规范件** → `cph4/fleet/` 根下，文件名**大写开头**（`REVIEW-POLICY-v1.json`、`SERVICE-LEVEL-v1.json`）。根下小写文件视为"待归位"。
2. **某个线/部门的东西** → `cph4/fleet/<line>-v1/`（已有 `drama-dept-v1`、`car-gaming-v1` 等）。
3. **一次性的产物与审计结果** → `archive/<line>/<YYYYMMDD>/`、`audits/`、`conversions/`。
4. **工具与其配置** → `Tools/fleet/`；配置类 `Tools/fleet-nodes.json`。
5. **不允许在根下新建小写 md/json 散件**（校验器会点名）。

## git 技术手段（这次真正落地的部分）

1. **合并策略分级**：
   - `queue-receipts/**`、`ARCHIVE-LEDGER.jsonl`、`INTAKE-PENDING.jsonl` 是**只追加**的，用 `merge=union` 安全（冲突时保留双方行，不会丢）；
   - `PRODUCTION-QUEUE.jsonl`、`lanes/**` 是**状态型**，**不用 union**（union 会产生重复 id 的坏行）——这类靠 `merge_jsonl` 的锁与字段继承解决。
   - 前任在 `.gitattributes` 里否决过全局 union，理由正确（会静默合并丢行）。这里只对 append-only 用，是对那条法条的收窄而不是推翻。
2. **大件不进 diff**：`media/**`、`archive/**` 标 `-diff linguist-generated`，避免 clone/对比变慢。
3. **换行符**：脚本类强制 `eol=lf`（Windows CRLF 会毁 POSIX sh）。
4. **L4 补充 ignore**：`state/ radar/ chief/ sync/ memory-slim/` 已在 `.gitignore`；新增 `*.tmp`、`.DS_Store`、`__pycache__`。

## 校验器管住新增（旧文件不搬）

`Tools/fleet/repo_layers.py` 每日检查并报警：
1. `cph4/fleet` 根下**小写散件**（应归位到子目录或改大写）；
2. 根下文件数超过阈值（当前 164，阈值 180）；
3. L4 目录里被 git 跟踪的文件（应为 0）；
4. L2 通道文件是否还在 git（被误忽略 = 断派单）；
5. archive 是否按月分目录。

**为什么不搬旧文件**：164 个根下文件里多数被脉、卡、文档引用，批量 mv 会制造一波断链；先用闸把增量管住，旧的自然淘汰。

## 一条纪律

**新文件先问"它属于哪一层"，再落盘。** 落错层的代价不是多一个文件，是下一次同步冲突和一整天排查。