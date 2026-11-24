# 同步后第一件事（ONBOARD-AFTER-SYNC）· 2026-11-11

> 两个时点都按本页做：**动手改之前**先过第 -1 步同步闸；**同步之后**从第 0 步往下走。
> 上位：`cph4/registry/CANON-V3-20261111.md`（唯一权威）。你的岗位：`cph4/fleet/stations/<你的工位>/CHARTER.md`。
> 系统差异：主控是 macOS（`python3`），其余三台是 Windows（`python`，不存在 `python3`，实测 rc=9009）。

## 第 -1 步：动手前先同步（CEO 2026-11-18 令 · 硬门）

原话：「每次动手改之前都要更新 git，然后再去做」。**任何改文件、改脚本、改台账的动作之前**，先跑：

    python Tools\fleet\prechange.py           # Windows
    python3 Tools/fleet/prechange.py          # macOS

它只读（fetch + 统计，不动你的工作树），给一个结论，按结论做，不许凭感觉直接改：

| verdict | 含义 | 动作 |
|---|---|---|
| `READY` | 已与 origin/main 对齐且工作树干净 | 直接改 |
| `SYNC` | 只落后、本地无自己的提交 | `git merge --ff-only origin/main`，再跑一次确认 READY |
| `WORKTREE` | 分叉（ahead>0）或工作树有未提交改动 | `prechange.py --worktree <名字>` 建隔离工作树，**在里面改、在里面提交推送**，完了 `git worktree remove _wt-<名字> --force` |
| `FAIL` | fetch 失败 | 先修网络/凭据；状态不明时禁止改文件 |

**为什么不是直接 `git pull`**：本机 main 长期 ahead 数十 / behind 数百（多机推送 + 自动 rebase 造成），
`git pull` 会拉出一堆冲突并把别人没提交的东西搅进来；`git reset --mixed origin/main` 又会丢掉别人本地未推的提交。
隔离工作树是唯一既不丢别人提交、又保证「基于最新」的路径。

纪律三条：
1. 一次会话里每改一轮就跑一次，不许拿「刚才同步过」当理由跳过。
2. 提交只 `git add` 点名的文件（工作树里常有他窗未提交的改动）。
3. 推完把工作树删掉，别在仓里留 `_wt-*` 垃圾。

## 第 0 步：确认你是哪个工位

| 机器 | 工位 id | 岗位书 |
|---|---|---|
| 公司生产力机（DASHENG） | `delivery` | `cph4/fleet/stations/delivery/CHARTER.md` |
| 传家宝（FLUXGROUP） | `visual` | `cph4/fleet/stations/visual/CHARTER.md` |
| 小钢炮（BIGMONEY） | `audio` | `cph4/fleet/stations/audio/CHARTER.md` |
| 算力大脑（3×V100） | `brain` | `cph4/fleet/stations/brain/CHARTER.md` |
| MacBook | `control` | `cph4/fleet/stations/control/CHARTER.md` |

机器与硬件口径见 `cph4/fleet/STATIONS.json`；交付物与判据见 `cph4/fleet/PRODUCTS.json`。

## 第 0.5 步：声明"我是谁"（不声明会拒绝运行）

自驱与巡检都按身份干活，身份来源优先级：`FLEET_STATION` 环境变量 > hostname 匹配 `STATIONS.json`。
**识别不出会直接拒绝运行（rc=2），不会默认成主控**——这是 2026-11-11 修的静默错：以前默认 `control`，
真机上忘带参数就会以主控身份读主控分片。

    # Windows（计划任务里也要带上）
    set FLEET_STATION=visual        &  python Tools\fleet\station_drive.py --once
    # macOS
    FLEET_STATION=control python3 Tools/fleet/station_drive.py --once

## 第 0.6 步：报一次环境底色（每天一次，主控据此对齐）

    python Tools/fleet/env_probe.py --write      # Windows
    python3 Tools/fleet/env_probe.py --write     # macOS

产物 `cph4/fleet/env/<工位>.json` 随 git 同步；主控用 `env_align.py` 判 PASS/GAP/STALE（超 24h 算 STALE）。
Windows 可用 `Tools/fleet/env-probe-daily.ps1`（schtasks 每天 08:20）。
**不报环境＝口径缺失，主控会把该机算作未探测，不给它排依赖环境的活。**

## 第 1 步：读自己的岗位书（全文）

它写清了：你的领域、禁做清单、时段与前置、输入输出、判据、坏了怎么报、上岗自检。
**与旧提示词冲突时，以岗位书为准。**

## 第 2 步：跑三条自检命令

    python3 Tools/fleet/station_shards.py --list          # 分片在不在
    python3 Tools/fleet/station_status.py --remote       # 全队谁有活（只读 origin）
    python3 Tools/fleet/station_drive.py --once                  # 自驱一轮（认身份，不传 --station 也行）
    python3 Tools/fleet/station_agent.py --station <id> --once   # 巡自己一遍

任何一条失败：先报 BLOCKED + 具体缺什么，不要开始领卡。

## 第 3 步：确认自己的队列

    git show origin/main:cph4/fleet/rt/<id>/queue.jsonl

- 只读；不要改别人的分片。
- 只领本工位的卡；卡上必须带 `product_id` 与可执行判据，否则拒收并说明。

## 第 4 步：起自己的循环

    python3 Tools/fleet/station_drive.py --loop 300      # 自驱：感知→供给→领活→执行→验收→写回执
    python3 Tools/fleet/station_agent.py --station <id> --loop 300   # 巡查：巡自己、报发现

Windows 用计划任务每 5 分钟跑一次 `--once`（静默包装，不带窗口）。
自驱的边界写在 `AUTONOMY-V3.md`：不对外、不自封人判（manual 停 PENDING_HUMAN）、
无 cmd 判 NEED-CMD 不假跑、无产物契约不造活。巡查不改卡、不自证验收。
规格见 `cph4/fleet/stations/AGENT-SPEC.md`。

## 第 5 步：需要判断时，调主控算力

- 端点：`http://100.75.133.10:8792/api/generate`（主控网关）。
- 令牌：环境变量 `FLUX_LLM_TOKEN`；没有令牌就纯规则跑，不许自己装大模型。
- 白名单模型、上下文、并发、死线由网关强制；拿不到就排队。

## 第 6 步：生产时守三条新规

1. **无产品不入队**：卡必须挂到某产品的某道工序。
2. **无验收不入队**：判据必须可执行（路径/哈希/尺寸/条数）。
3. **机制活不进业务队列**：审计巡检修复只在夜窗，白天一张不出。

## 第 7 步：内容线（漫剧/MV）开工前多跑一条

    python3 Tools/fleet/drama_rules.py --self-test     # 14/14 必须通过

判据（镜长、抽卡、响度、盲评、AIGC 标识等）全在引擎里，文档不复述数字。

## 出问题时按这个顺序报

1. 环境缺失 → `BLOCKED` + 缺什么（不重试）。
2. 输入缺失 → `BLOCKED` + 缺哪个文件（不造数据）。
3. 同一错误两次 → 停下写根因，第三次不许再试。
4. 一个工位连续报同一 BLOCKED → 主控派修卡，并在一屏上点名。
