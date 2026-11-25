# REPO-MAP — 给机队的总图（先读这一份，再动手）

> 2026-11-25 立。本件回答三件事：**东西在哪 / 谁说了算 / 怎么自查**。
> 只写指针与判据，不复述内容——正文各在各的正身件里，避免出现第二份真理。

## 一、动手前的三步

```bash
python3 Tools/repo_audit.py --scan      # 1 全仓体检（可复算，出 REPO-AUDIT.json/md）
python3 Tools/fleet/gzh_loop.py --status # 2 看当前该做什么（唯一事实，别靠记忆）
cat cph4/fleet/SYNC-CONTRACT-v1.md      # 3 看跨机规则与共享边界
```

## 二、目录总表（14 个顶层目录）

| 目录 | 是什么 | 谁管 | 正身件 |
|---|---|---|---|
| `cph4/` | 集团运营与产线（最大，24G） | 主控统筹，各条线拥有者写 | `cph4/fleet/STATIONS.json`（机器）· `AGENT-TEAMS-v1.json`（席位） |
| `Tools/` | 全集团共享工具（1339 个 .py） | 主控，改动需自检 | `Tools/fleet/` 下各器自带 `--self-test` |
| `docs/` | 对外材料与说明 | 主控 | `docs/governance.md`（治理）· `docs/orders.md`（令台账） |
| `gaming/` `house/` `domain/` `life/` | 游戏 / 安家 / 城市 / 硅基生命 | 公司生产力机 | `cph4/fleet/PRODUCTS.json` |
| `quant/` | 量化工位 | 小钢炮 / 算力大脑 | `quant/` 下各策略 README |
| `media/` | 内容资产（不入 git，仅本机） | 传家宝 | 移交书 `cph4/fleet/HANDOVER-20261120-CONTENT-TO-VISUAL.md` |
| `软著申请材料/` | 版权申请件 | 主控 | 目录内清单 |
| `AI-KB/` `research/` `compute/` `state/` | 知识库 / 调研 / 算力 / 运行时状态 | 各自 | — |
| `_archive-YYYYMMDD/` | 归档区（**只增不删**） | 主控 | 各自 `LEDGER.md` + 回滚命令 |

## 三、四份"谁说了算"（冲突时按这个顺序）

1. **归属** → `cph4/fleet/STATIONS.json`（机器）＋ `SYNC-CONTRACT-v1.md`（规则）
2. **当前该干什么** → `cph4/fleet/social/gzh/NEXT-STEP.json`（每拍重算，不看记忆）
3. **一个文件是否过时** → `cph4/fleet/REPO-AUDIT.json`（零引用 + 多久没动 + 是否被拼接调用）
4. **跨机判断** → `cph4/fleet/ASK-<日期>-*.jsonl` 发卡 → `order-bus/receipts/` 回执

## 四、三条铁律（踩过的坑，别再犯）

1. **零引用 ≠ 没用**。`gzh_daily.py` 用 `"gzh_%s.py" % step` 拼路径，`gzh_trainset` 等
   活工具字面零引用。所以"零引用"必须再过"多久没改动"这道闸；近期改过的一律不动。
2. **两本账分开**。风格语料（能进文笔训练）与产业语料（只做形态/事实）不许混着数。
3. **删前先归档**。一律 `git mv` 到 `_archive-YYYYMMDD/` 并写台账；
   「可回滚」比「省空间」重要。

## 五、当前仪器（都能自己重跑，别信口头结论）

| 器 | 作用 | 自检 |
|---|---|---|
| `Tools/repo_audit.py --scan` | 零引用/低版本/重复/绝对路径/断链/失效引用 | 13/13 |
| `Tools/fleet/gzh_loop.py --status` | 公众号线当前该做什么 | 19/19 |
| `Tools/fleet/gzh_trainset.py` | 语料门槛：总篇数 vs **可训篇数** | 8/8 |
| `Tools/fleet/harvest_generic.py` | 任意站点采集（feed/sitemap/列表/单篇） | 31/31 |
| `Tools/fleet/fleet_sync_probe.py --status` | 同步探针：软链/车道新鲜度/问询逾期/席表完整性 | 9/9 |
| `Tools/fleet/bigloom_done.py` | **完工判据八条**（全绿才可宣布完成） | 8/8 |
| `Tools/fleet/res_alloc.py --status` | 当前哪个平台有租约 | — |

## 五之二、BigLoom 六席（2026-11-25 立于 AGENT-TEAMS）
账与标准在 control：`C-LOOM-STD`（内容标准）`C-LOOM-BOOK`（两本账）`C-LOOM-DISPATCH`（派单回执）
生产在 visual：`V-LOOM-COLLECT`（采集）`V-LOOM-DRAFT`（出稿）`V-LOOM-PUB`（上架）
带数字的席必须 `numbers=rule-only` + `facts_cmd`——数字由规则算，模型只判不下数。

## 六、已知缺口（写在这里，免得下次重新发现）

1. 传家宝（visual）22/5985/8790/445 全不通，发给它的卡只能等它自己同步 git。
2. 小钢炮离线 14 天，算力大脑未入网。
3. `cph4/fleet/social/gzh` 等三处是指向 `~/BigLoom` 的**绝对路径软链**，异机不可用，
   落实同步前不要推远端。
4. 硬编码 `/Users/junsheng.sun/...` 1124 处（多在文档与 Windows 机专属脚本里），
   这是可移植性债，未清。
