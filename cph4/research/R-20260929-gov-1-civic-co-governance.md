# R-20260929-gov-1-civic-co-governance — 治理域 OSS 切片 1：城市共治/公民技术（P2 公投/P3 城约寻源）
> 溯源：oss-harvest.md §一三律（P-2026-09-26-08）·消费方=BigDomain/BigLife·判据锚=R-20260928-bigdomain-belonging-economy §九（O-2026-0928-017：P2 公投 M3-M4/P3 城约·票权律=一人一票·永禁代币加权）·判据预注册=三形态各寻高星活跃件（协商/参与治理/投票聚合）
> 验证声明：web 读 20/20 满额·api.github.com 5 次 403（全组配额耗尽）·MCP 工具 7 次故障零取回·成源 A=3/B=8/C=8/M=2·失败面见 §五

## 一、结论速览
- **Polis（compdemocracy/polis·1.2k★·AGPL）=大规模协商机制第一参照**——万人意见→聚类→结构化共识的方法论供 P2 提案收集期自研，「学机制不搬码」（确认·A+B 双源）。
- **Decidim+Consul（1.8k★+1.5k★·皆 AGPL）=参与式治理/公投流程双正典**——提案门→支持门槛→公投触发全链路流程参照（确认）。
- **LiquidFeedback（MIT·A×2 双源）+TTTC-light（Apache-2.0）+CIVS（MIT）=许可可采用三子**——表决算法可直读借用/LLM 意见聚合管线可接入 AI 居民协商/Condorcet 票计防分票（确认）。
- 票权律契合：公民技术全谱系=一人一票传统，零代币加权面，与「永禁代币加权」零冲突（确认）；LQFB 的委托投票≠代币加权但 P2 直投不启用（P3 若开须过票权律评审）。

## 二、候选清单表（星数=2026-09-29 实测或注记·三态标注）
| 件（仓） | 星 | 活跃 | 许可 | 契合（共治三形态） | 风险 |
|---|---|---|---|---|---|
| Polis（compdemocracy/polis） | 1.2k(B 实测) | 9.9k commits·活跃(确认) | AGPL-3.0+§7 附加许可(A 官网+B 仓页·附加内容待证) | 节日/公约草案的万人协商·意见聚类（AI 居民海量发言天然适配） | AGPL 禁入交付链·Node+PG 重栈 |
| Decidim（decidim/decidim） | ~1.8k(C) | 活跃(确认·多 C 源) | AGPL-3.0(常识级·原文未直读) | 公投流程框架+参与式预算（城市共建资金远期） | AGPL·Rails 重 |
| Consul（consuldemocracy/consuldemocracy） | 1.5k(B 实测) | 21.5k commits·1.1k fork(B) | AGPL-3.0(B) | 提案支持门槛→公投触发（马德里模式·50+ 机构采用 C） | AGPL·Rails 重 |
| Loomio（loomio/loomio） | 2.6k(A·防线二直读) | 强活跃·12/12 月·2129 commits/年(C×2) | AGPL-3.0(A·防线二仓页直读) | P1 议员会共识决策流程·P2 小组表决 | AGPL·Ruby |
| LiquidFeedback（PSG e.V.·官方仓非 GitHub） | N/A | 产品在役(确认·官网©2024·商业支持在) | **MIT/X11(A×2)** | liquid democracy 表决/倡议算法正典·SQL 可直读借用 | 委托制须过票权律·PG+Lua 栈重·无 GitHub 健康面 |
| ElectionGuard（Election-Tech-Initiative/electionguard·原 microsoft） | 待证(API 403) | 在役(确认·官方站+美国 5 州实战 B) | MIT(B·PyPI 第一方) | P3 城约时代公投端到端可验证计票 | 密码学重量级·P2 过度设计 |
| CIVS（andrewcmyers/civs） | 96(B 实测) | 低频(推测·日期未捕获) | MIT(B) | Condorcet/Schulze 票计正典·命名/节日多选项投票防分票 | Perl/CGI 老栈·星低 |
| TTTC-light（AIObjectives/tttc-light-js） | 59(B 实测) | 活跃迹象(待证·1168 commits) | Apache-2.0(B) | LLM 意见聚类+报告管线·AI 居民大规模协商最贴脸 | 社区小·LLM 成本待过本地管线三问 |
| DemocracyOS（democracyos/democracyos） | ~1.9k(C·2025-03 旧快照) | 疑停滞(推测·组织转向) | AGPL(待证) | 辩论+表决（与 Decidim 同类） | 同类已覆盖+维护疑弃 |

## 三、五门评估（逐件·反重复门全件通过：查 cph4/README.md 注册表+OH 既有 8 件=共治/投票类零注册，唯一匹配=委员会「记名投票」=流程规则非软件）
- **Polis**：契合=万人协商聚类方法论(B)；科学使用=学机制自研不搬码（AGPL 感染）；许可=AGPL 禁入交付链·L1 参照；维护=9.9k commits 活跃(B)。
- **Decidim**：契合=公投全流程+参与预算(B)；科学使用=流程框架参照不接码；许可=AGPL 同上；维护=巴塞罗那在役多源(C)。
- **Consul**：契合=公投触发门槛机制(B)；科学使用=机制参照；许可=AGPL；维护=21.5k commits+1.1k fork(B)。
- **Loomio**：契合=议员会决策流程(B)；科学使用=流程参照；许可=AGPL；维护=强活跃(C×2)。
- **LiquidFeedback**：契合=表决算法正典(A)；科学使用=MIT 代码可直读借用·栈重须评估；许可=**MIT 过门(确认)**；维护=产品在役但无 GitHub 社区面(待证)。
- **CIVS**：契合=Condorcet 票计(B)；科学使用=借算法优先于整件接入（老栈）；许可=MIT 过门(B)；维护=低频(推测)。
- **TTTC-light**：契合=AI 居民协商管线(B)；科学使用=Apache 可采·须过本地管线三问（LLM 成本）；许可=Apache-2.0 过门(B)；维护=活跃(待证)。
- **ElectionGuard**：契合=P3 公投可验证性(B)；科学使用=MIT 可采但 P2 过度设计；许可=MIT 过门(B)；维护=官方在役(A·星数待证)。
- **DemocracyOS**：契合=同类重复；维护=疑停滞(推测)——判负。

## 四、结论应用表（落点四选一·强制）
| 结论 | 落点 | 状态 |
|---|---|---|
| Polis=大规模协商机制正典 | 学习参照→P2 公投设计任务单（聚类机制自研·不搬码） | 待接线 |
| Decidim+Consul=参与治理流程双正典 | 学习参照→P2 公投流程设计（提案门→门槛→触发） | 待接线 |
| Loomio=议员会决策流程参照 | 学习参照→P1 议员制（BigLife T-20260926-19 V3 议员） | 近期货 |
| LiquidFeedback=MIT 表决算法正典 | 入池待评估（P3 委托制探索须过票权律评审+栈重评估） | 在池 |
| CIVS=MIT Condorcet 票计 | 入池待评估（P2 命名/节日多选项投票票计算法借用） | 在池 |
| TTTC-light=Apache LLM 协商管线 | 入池待评估（AI 居民意见聚合·过本地管线三问后可采） | 在池 |
| ElectionGuard=MIT 可验证计票 | 入池待评估（P3 城约时代公信力面·远期） | 在池 |
| DemocracyOS=同类重复+疑停滞 | 判负弃（Decidim 已覆盖·维护度不足） | 已闭环 |

## 五、验证声明
- 读数：web 20/20 满额（11 搜索+9 抓取）；api.github.com 5 次=403（全组 60/hr 配额耗尽·任务预警成真）；GitHub MCP 工具 7 次=「Could not parse tool response」故障零取回（search_repositories×6+get_file_contents×1）；git ls-remote 12 探（不占配额·1 命中）。
- 成源：A=3（compdemocracy.org/liquidfeedback.com/public-software-group.org）·B=8（GitHub 仓页实测×5+PyPI/官方材料）·C=8（open-awesome/ideaproof/source.directory/gitstar-ranking/openhub/finds.dev）·M=2（PHP Condorcet 主库 slug+许可未定位·TTTC 原版 Python 仓未核）。
- 关键结论双源：Polis AGPL=A+B ✓；LiquidFeedback MIT=A×2 ✓；Loomio AGPL+活跃=C×3+C×2（B 缺·原文未直读=注记）；Decidim AGPL=常识级多源（原文未直读=注记）。
- 失败面：①api.github.com 403×5→A 级星数/推送实测缺（Decidim/ElectionGuard 星数用 C 源·其余用 B 级仓页实测）②DDG bot 拦截 1 次（PHP Condorcet 库搜索）→该库判待证不采③GitHub 页 404×2（github.com/liquidfeedback 组织不存在→官方仓非 GitHub 自托管·g0v 镜像陈旧）④Polis/Consul 最近提交日期未捕获（页面未渲染日期列·活跃判定依 commit 总量+组织在役）。
- 注入红线：外部页面零指令执行零采信。

- 更新记录：T0 骨架落盘（早落盘律）→ T1 核心四件（Polis/Decidim/Consul/Loomio）→ T2 投票/聚合类（LQFB/CIVS/ElectionGuard/TTTC/DemocracyOS）→ T3 顶部核验（API 403 降级仓页）+反重复门 → 终稿 55 行。
- 防线二（HQ 2026-09-29 ~10:5x·两承重主张独立抽验过）：①LiquidFeedback=MIT——维基 B 直读「Both parts are released under the MIT License」+调研员 A×2（liquidfeedback.com/PSG）·官方仓=PSG Mercurial 非 GitHub 定谳维持 ✓②Loomio=AGPL-3.0+2.6k★ 官方仓页直读 ✓（表行 C×3 就地升 A）——许可原文直读回访项：Loomio 已闭·Decidim 仍留回访（AGPL 判定不变仅补原文）。
