# R-20260923-02a 治理层 v2 · 波A 内部审计（量化实测）

> 溯源：CEO 令 2026-09-23 ~22:40（R-20260923-02-govscale.md 章程 §三 波A）。全部数字当场实测（22:45-23:10·HQ 会话）。
> 方法：chars×0.7 ≈ CJK token；立国日特例=各文件全量即当日增量，外推按「今日 20% 斜率」保守假设，假设显式标注（诚实律）。

## §1 治理面 20 文件实测（114,211 chars ≈ 8.0 万 token）

| chars | est tok | 文件 | chars | est tok | 文件 |
|---|---|---|---|---|---|
| 35,765 | 25,036 | CODELY.md（根记忆·49 条·**自动注入**） | 3,889 | 2,722 | cph4/README.md |
| 13,949 | 9,764 | docs/orders.md | 3,874 | 2,712 | cph4/retention.md |
| 13,243 | 9,270 | cph4/evolution-ledger.md | 3,667 | 2,567 | AI.md |
| 12,210 | 8,547 | docs/governance.md | 3,491 | 2,444 | RULES.md |
| 3,055 | 2,139 | BRAND.md | 2,884→* | 2,016 | cph4/evolution.md |
| 2,862 | 2,003 | docs/architecture.md | 2,508 | 1,756 | gaming/README.md |
| 2,446 | 1,712 | cph4/onboarding.md | 2,208 | 1,546 | README.md |
| 1,779 | 1,245 | cph4/fleet-allocations.md | 1,690 | 1,183 | cph4/scheduling.md |
| 1,464 | 1,025 | cph4/local-first.md | 其余 4 件 | ≈3,866 | quant/media/domain 线 README |

## §2 记忆面 10 文件实测（178,887 chars ≈ **12.5 万 token**——比治理面更重）

| chars | est tok | 文件 |
|---|---|---|
| **149,345** | **104,542** | **quant/bigmoney/CODELY.md（BigMoney 产品记忆·单文件超 10 万 token）** |
| 11,282 | 7,897 | media/BigStream/CODELY.md |
| 7,915 | 5,540 | gaming/CODELY.md（线记忆） |
| 6,037 | 4,226 | gaming/MiniGame/CODELY.md |
| 1,724 | 1,207 | quant/CODELY.md（线记忆） |
| 其余 5 件 | ≈3,050 | media/life 线记忆 + BigLife 产品记忆 |

**对照官方基准**：Claude Code 官方对自动加载记忆的限值=**200 行 / 25KB 截断**、CLAUDE.md 目标 **<200 行**；根 CODELY.md 已≈25k token（约 3× 官方 25KB 级限值的 token 量），BigMoney 记忆则超其 4×+。

## §3 单令复述系数（抽 3 令·仅 HQ 四文件面）

| CEO 令 | 复述处数 | 复述总 chars | 备注 |
|---|---|---|---|
| 18:20「立项集团级元宇宙可视化项目」 | 4 处 | 2,235 | 未计 FluxVerse 仓 TECH/BLUEPRINT+commit 信息=低估 |
| 18:55「所有可视化项目以这个美术风格为准」 | 3 处 | 2,206 | 同上 |
| 21:30「把city可视化做出来」 | 1 处 | 930 | 在途件（分发包未全落） |

**系数结论**：一道令 ≥3-4 处复述、每处 500-900 chars；首登处之外纯复述贡献 ≈ 文本面增量的 **60-70%**。

## §4 冷启动两场景

- **场景1（集团根会话）**：自动注入根 CODELY.md ≈25k tok + 按 AI.md 指引读 governance/orders/ledger 尾部 ≈5-10k → **冷启动 ≈3 万 token 起**。
- **场景2（产品仓会话）**：quant/bigmoney 目录会话自动注入面最高可达 ≈10 万 token（§2）——超出一切合理预算。
- 区分：自动注入=不可选成本；按需阅读=可选。**当前最大不可选成本=记忆面**，最大可选成本=orders/ledger 全文阅读。

## §5 开线成本基线（git show --stat 实测）

| 开线事件 | 触碰文件 | 插入行 |
|---|---|---|
| BigLife（d857a8b） | **10 文件** | 42 行 |
| BigDomain（b1767d9） | **6 文件** | 33 行 |

验收线目标「≤2 处」——现状超 3-5 倍；触碰面=BRAND §8/governance §2/architecture/线 README/线 CODELY/gitignore/cph4 注册表/orders 行。

## §6 增速与外推（立国日 2026-09-23 全量即当日增量）

- 今日实测：根记忆 +35.8k chars（49 条）·orders +14k·ledger +13.2k·记忆面 +17.9 万 chars（BigMoney 记忆为最大项）。
- **保守外推（假设：立国日斜率的 20% 为常态——5 司在营+CEO 多窗持续下 令）**：日均记忆面 +3.6 万 chars·治理面 +6.6k chars → 90 天后：治理面 ≈2.6×（20.7 万 chars）、记忆面≈8×。冷启动成本 3-5 倍膨胀——CEO「谁受得了」成立。
- 局限标注：斜率样本仅 1 天；20% 假设待周轮复测校准。

## §7 Top-10 膨胀源（按 90 天预计贡献排序）

1. BigMoney 产品记忆 14.9 万 chars（机队协议+策略账全进 CODELY.md）
2. 根 CODELY.md 49 条/日写入速度+条目≈commit 信息复述 1:1
3. orders.md 行=commit 信息全量复述（每行 ~900 chars）
4. evolution-ledger 行=P 件长文复述（每行 1000-2000 chars）
5. 记忆条目与 commit 信息双写（append 习惯）
6. governance changelog 与 orders 行重复
7. CEO 原话逐字进 3-4 文件
8. 线 CODELY 与产品 CODELY 主题重复（gaming 线 5.5k 与 MiniGame 4.2k 同主题面）
9. BigStream 记忆 7.9k 且五轮令全落条目
10. .codely-cli/auto-saves 噪音（retention R3 面·次要）

## §8 结构化注册表候选清单

| 现散文文件 | 建议登记处（机器可读） | 人读视图 |
|---|---|---|
| docs/orders.md | orders.jsonl（一令一行：ts/quote/落点/状态/溯源） | 尾部滚动窗 30 天→自动归档 orders/archive/ |
| governance §2 登记簿+BRAND §8+architecture 线表 | org.yaml（公司/线/仓库/remote/状态一行一实体） | 由 yaml 生成三处视图或指针 |
| evolution-ledger 提案区 | proposals.jsonl（P 件一记录） | 进度面板+周报派生 |
| 根 CODELY.md 集团记忆 | 薄索引（≤200 行）+ 主题文件分档（工具原生支持引用模式） | 按主题按需读 |
| fleet-allocations | machines.yaml | 表格派生 |
| 记忆条目纪律 | 长件→外部 md+记忆只存一行指针（append_memory 工具规范同向） | — |

## §9 方法与局限

- token=chars×0.7 近似（CJK 混排误差 ±20%）；立国日单日样本；git --numstat 汇总因 PowerShell 管道两次失败改用文件级实测（对结论无影响——文件全量即当日增量）。
- 复述系数未计产品仓回声与 commit 信息全量（=系统性低估，结论方向不变）。
- 结论一句话：**不可选成本（自动注入记忆）已是最大项且增速最快；可选成本（orders/ledger 散文）里 60-70% 是复述**——两条都可治：注册表化+索引化。
