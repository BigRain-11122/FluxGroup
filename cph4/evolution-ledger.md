# Evolution Ledger — 集团进化台账

> 唯一进化台账（章程=`cph4/evolution.md`）。任何机器任何会话可追加提案；五字段一行。
> 状态：open（待裁决）/ applied（已落地）/ rejected（CEO 驳回）/ transferred（转办@公司）/ self-healed（自愈闭环）。

## 提案区

| ID | 日期 | 现象 | 证据 | 建议 | 级 | 状态 |
|---|---|---|---|---|---|---|
| P-2026-09-23-01 | 09-23 | 旧 SMTP 授权码已入 MiniGame git 历史（send_report.py），按集团安全律视为泄露 | gaming 记忆 U161/U165 | CEO 轮换 QQ 邮箱授权码；恢复邮件简报时一律用新码（旧码永久作废） | T1 | open |
| P-2026-09-23-02 | 09-23 | HQ 仓 `.codely-cli/settings.json` 本机改动长期未提交，入库与否无法可依 | git status 长期 M | 立法：仓库级 settings 入库、本机 override 走 gitignored 私件 | T1 | self-healed（R1 巡检：已随 4ca948e 入库且 git clean；「settings 随仓提交」实践已在集团记忆在册） |
| P-2026-09-23-03 | 09-23 | MiniGame 根级存在乱码孪生目录 `09_鍚稿槦鍢烥immeAll`（PS5.1 GBK 坑遗迹） | ls 实测 | 转办@Biggame：其 Housekeeping/NameCheck 按编码律与命名律处置 | T1 | transferred |
| P-2026-09-23-04 | 09-23 | bigmoney `.gitignore` 未白名单分机轮账本（round_reports-*.md / state-*.json 跨机不可见） | bm-a R2 轮账本自检发现 | bm-a 循环自愈进行中；登记为自愈案例：机队自检发现并自行修复=体系自进化首例实证 | T2 | self-healed |
| P-2026-09-23-05 | 09-23 | 线 README 曾长期漂移（Stack TBD vs 实况），修过一轮但无常态化巡检 | 本日 gaming/quant README 实况刷新 | 周进化轮感知面内置「线 README × 产品实况」对照探针 | T2 | applied（章程 §1 已内置） |
| P-2026-09-23-06 | 09-23 | Media/BigStream 开线批次在途未收口：BRAND §8 命名行+governance §2/changelog+产品仓脚手架均为未提交工作树态（remote 待建） | BRAND.md diff（mtime 14:53）+governance changelog 新行+裁决区「是我点的，保留」 | 本轮让路零触碰；下轮复核 HEAD 存真与开线五步齐备性（含 .gitignore 隔离行+独立 remote） | T1 | open |
| P-2026-09-23-07 | 09-23 | 线 README 漂移：旧 gaming/README「19 任务 OS 机队」vs 实况 20 | Get-ScheduledTask 实测 19 个 MiniGame*+GimmeAll-AutoSentinel=20（U165 体检基线同源） | R1 修正 19→20 后旋被并发 CEO 会话 15:03 线 README 重写覆盖：新版移除机队数表述、机队细节归产品仓（引用不复制），漂移面消除无需重做 | T2 | self-healed（并发重写代偿·P-05 探针首轮实证有效） |
| P-2026-09-23-08 | 09-23 | OS 任务层存在 BigMoney 域孤儿任务 MoneyAutoGuardian（Disabled，产品文档零记载） | Get-ScheduledTask 实测 Disabled；HANDOVER/fleet 台账/轮账本无此名 | 转办@BigMoney：判前代遗产则按其机队协议注销或标记退役留档 | T3 | transferred |
| P-2026-09-23-09 | 09-23 | 心跳/轮账本写入 git 控制面仓造成脏树卡死 pull --rebase 通道（bm-a R1 卡死→R2 checkout 还原+定向 commit 修复） | state-bm-a.json R2 + round_reports-bm-a.md R1/R2 实录 | 入册机队时代共享坑：控制面仓内机器局部态=定向 commit 或 gitignore 白名单分机（P-04 同源机制） | T3 | applied |

## 反馈区（子公司 → 集团 · 收取与回访 · CEO 令「顶层机制务必听子公司的反馈」）

> 各公司反馈面登记：BigMoney=`quant/bigmoney/HQ-FEEDBACK.md` ✓｜BigStream=`media/BigStream/HQ-FEEDBACK.md` ✓｜Biggame=待其按自治法选定落位（其根级冻结清单法优先；落位前其 CODELY.md 机制类条目为临时反馈面）。收取 SLA=周轮必扫；未处理超两周自动升级 CEO 待办（docs/orders.md）。

| ID | 来源公司 | 反馈（现象/证据） | 建议方向 | 级 | 状态 |
|---|---|---|---|---|---|

## 裁决区

| 日期 | 提案 | CEO 裁决原文 |
|---|---|---|
| 2026-09-23 | 体系设立（本章程+周轮） | 「帮我引入AI时代最先进最牛逼最能自我进化的集团化治理体系！」 |
| 2026-09-23 | Media 线定名 BigStream（BRAND §8 新登记行，跨会话点名、本会话对账核实） | 「是我点的，保留」——T0 合法登记；开线五步由点名会话执行（产品仓脚手架搭建中：README/PLAN/docs×3） |
| 2026-09-23 | 集团级 GO（全速迭代令） | 「开始全速迭代 规范的情况下，自己发展！」——三产品引擎 + 进化轮全速运转；铁律门禁（预注册/禁未来数据/认领制/反重复/T0-T3 分级立法）照常生效——**全速只加速，不放规范** |
| 2026-09-23 | 法条复核包 + T1 决策权（本会话呈报） | 「你自己决策，我随时会复查和过问」——今日法条全部生效（委托代批·复查权保留）；T1 由 AI 代决+7 天否决窗；T0 仍须 CEO 明令 |
| 2026-09-23 | 反馈通道令 + R1 待裁决项清零 | 「顶层机制务必听子公司的反馈什么的，然后自我迭代，科学决策」——§7 反馈通道立法（HQ-FEEDBACK.md 面制+SLA+闭环回访条款）；**P-01 随判**：旧码视为泄露不变，轮换=CEO 物理件且为恢复邮件简报的前置条件（U166 三步之首），集团层不再挂待办；**P-02 依 R1 结案**（settings 在库 clean，本机 override 需要时走 settings.local.json=gitignored） |
| 2026-09-23 | FluxVerse 风格（CEO 委托「你自己决定」→ AI 代决·否决窗 7 天） | 代决=探索稿 **1 号「高清赛博像素」**为主风格——依据=CEO 概念图令原话「还是高清像素风格」同向命中+两次风格令语义一致；4 号暗黑像素HUD 仅作 HUD/仪表层局部参考；M0 就此收口，元宙会话全面开工 M1（底座六项修复并行不等待） |

## 进化轮报告区

- 2026-09-23 R0（CEO 会话轮 · 体系设立日）：四步循环立章、分级立法权 T0-T3 立法、周进化轮部署、台账以今日 5 提案播种（1 open 安全项待 CEO / 1 open 立法项待 CEO / 1 转办 Biggame / 1 自愈闭环 / 1 已落地）。
- 2026-09-23 15:12 R1（周进化轮首跑·FluxGroup-EvolutionTick 点火）：CEO 新裁决在册=BigStream 定名（「是我点的，保留」）+集团 GO 令（「开始全速迭代 规范的情况下，自己发展！」）→进化轮入全速运转态；感知=三级记忆+两产品仓活数据面只读巡检（gaming X754 快照全绿·quant bm-a R2 退避护会话/bm-b R26 维护轮·HANDOVER round25 对账无缺件）；发现与动作=①旧 gaming/README「19 任务」漂移：R1 修正后旋被并发线 README 重写代偿（移除机队数表述归产品仓·P-07 结案 self-healed·P-05 探针首轮实证）②P-02 结案 self-healed（settings.json 在库 clean）③MoneyAutoGuardian 孤儿任务转办@BigMoney ④心跳脏树卡 pull 坑入册共享教训（T3）⑤Media/BigStream 开线批次在途→让路并立 P-06 下轮复核（.gitignore 预护 media/BigStream/ 已实证·remote 待建）；安全=集团仓跟踪件零明文凭据·产品目录零入库·.gitignore 密钥面齐备（DailyDigest 禁用=U166 有意暂停，未当故障修）；让路声明=在途 CEO 会话批次件（settings.json/gaming 线记忆/media 件）本轮零触碰零提交、轮提交用路径限定 commit 非 add -A（防误并 T0/T1 未收口件与产品目录）；待 CEO 裁决清单=P-01 SMTP 授权码轮换（唯一 T1 open 安全项·账号物理件归 CEO）。
