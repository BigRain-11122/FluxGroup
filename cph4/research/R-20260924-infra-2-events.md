# R-20260924-infra-2 · world-events 多机并发写：诊断与目标架构简报

- 波次：CEO 五技术底层问题调研波 · 第 2 路（world-events 多机并发写）｜调研员：CPH4 Labs 并行调研员
- 日期：2026-09-24（Asia/Shanghai）｜方法：代码实读（scan.ps1 / verify.ps1 / tick.ps1）+ world\ 全量实测（严格 UTF-8）+ 机制文献（scheduling.md / cadence.md / FLEET-OPS.md）
- 纪律声明：机制规格不写产品代码；唯一写入=本文件；无任何 git 写操作。

## §0 一页架构卡

**总裁决**
1. **CEO 判断「机队一扩就崩」——机制层确认，实况层尚未发作。** 现行锁（world/scan.lock）是单机文件锁，对异机进程零效力；且实测**异机今天根本不写 world 文件**——world-events.jsonl 唯一写者是 bm-a 的 scan.ps1（tick :x6 + DevLoop :x5 + 手动会话三触发源），事件流实为「bm-a 只读采集各仓本地 clone 后的派生投影」。「5 机同写一个 jsonl」是假设未来，不是现状。
2. **推荐案 2「单写者收编」**：异机自发事件走**各自 git 仓 inbox 文件**（写域=机）→ bm-a scan 合并装配进单流。与 FLEET-OPS 控制面（git 10min）同构；verify / CityWatch / 引擎**零改动**；异机事件入城尾延迟 ≤20min（与今日探针派生路径同量级，无退化）。
3. **内部总线不需要换存储引擎**：实测 ~4.4k 条/日；20 机外推 ~16k 条/日（每 10min 轮批 ~113 行）——「单写者+批追加+行数游标」绰绰有余。「崩」的正解=**禁止跨机直写 + 写域分片运输**，不是数据库。
4. **×100 公共商业面（≈44 万条/日，峰值 50-250 条/s）与内部总线分属两个系统**：公共面需要常驻服务端（入口/鉴权/并发/持久化），触及零服务器红线，**依赖 infra-1 红线修正案**（R-20260924-infra-1-backend.md 经查不存在，本波独立推导）；本简报仅预对齐事件方言（6 字段核+evt_id 超集），内部总线不动。
5. **旁发现（比竞写更早爆的雷）**：world/ 被 FluxVerse 仓 .gitignore 排除 → **编年史+快照+游标仅存 bm-a 单盘、零云备份**（FLEET-OPS 三级备份无一覆盖）。P0 立即修，不涉任何红线。

**分阶段**：P0 备份缺口+tick.lock 补 PID（立即·零裁决依赖）→ P1 inbox 收编（案 2 核心）→ P2 装配机可移植 runbook+指标 → P3 公共面（等 infra-1 裁决）。

## §1 现状审计（代码级事实，全部实读）

### 1.1 写者与锁
- world 文件唯一写者=Tools/perceptor/scan.ps1（事件经 Add-WorldEvent 出口→内存批→轮末一次 AppendAllText 追加）；触发源：FluxVerseTick（车道 :x6，每 10min）+ FluxVerse-DevLoop（:x5，每 10min）+ 交互会话手动 scan（cadence.md §0 实测台账）。tick.ps1 只编排 scan→verify，自身不写 world。
- scan.lock（scan.ps1，P-11）：锁文件=world/scan.lock；活锁判定=owner PID 存活**且**锁龄<15min → 后来者 skip exit 0；死 PID/损坏/超龄 → 立即接管（fail-open 永不死锁）；轮末 Remove-Item 释放（硬崩溃由超龄接管兜底）。
- tick.lock（tick.ps1 v1.1）：logs/tick.lock，**仅锁龄判定**（<15min 跳）——无 PID 存活检查，与 scan.lock 不一致（挂死>15min 的活轮会被新轮并行接管；scan.lock 仍护流，轮级双跑面存在）。
- 脏树退避（tick.ps1 v1.2）：轮首 `git status --porcelain -- Tools/perceptor schema` 脏 → 本轮跳 scan+verify（16:57 先例：半改栈假 FAIL）；git 出错 → 照跑（fail-open）。
- 竞写修复史三例，全部文件锁法（CEO 定性「本质还是文件锁方案」属实）：scan 双跑竞流（17:37/17:42 窗）→ P-11 scan.lock；tick 慢轮撞下轮 → S1 tick.lock；FluxVerseTick 与 MiniGameEngineTick 同 :x7 竞 MiniGame 心跳 json → 迁 :x6（cadence §2.1）。

### 1.2 事件出口与写侧门禁
- 门禁：Add-WorldEvent 对照 schema/events-registry.json（实测登记 31 型；流中已用 15 型，16 型预留）；未登记 → 当场进 world-events.quarantine.jsonl（带 reason，取证保留）；registry 加载失败 → fail-safe 空=全隔离。
- 行格式：ts_utc/type/actor/repo/zone/summary 六字段，ConvertTo-Json -Compress 全转义（S2 律），UTF-8 无 BOM 追加。
- 隔离区 7 天生命周期（r7/P-14）：整文件 7 天未动整清；否则按行 ts 淘汰；无法判龄的行永不删（forensic bias）。

### 1.3 轮转与游标
- 日轮转（r3）：首个跨日 scan 见活流 LastWriteTime<今日 → 整档归档 world-events-YYYYMMDD.jsonl（按 LastWriteTime 命名；已存在则追加合并不覆盖=时钟跳变安全）；活流清零只装当日。档案供引擎 L2 回放（v0.4 头注）。
- verify 游标：verify-state.txt `events_verified=N` 为**行数游标**，增量校验 O(new)（S3）；游标自检：N>行数（轮转/截断）→ WARN+rebase 0 全量复查，坏游标不盲信。
- verify 自愈：坏行移隔离+**整文件重写**活流（sanctioned 例外：活流可整形，档案永只增）。
- scan 内容寻址游标：perceptor-state.txt（实测 31,083B，~250 键：git SHA/订单号/心跳 last_seen/github_last_id/fx/mgtp/res/task 等），轮末读-改-写全文件（锁内安全，锁外即丢更新面）。
- 两阶段晋升：scan → world-state.json.new；verify PASS → Move 晋升，FAIL → 弃 .new 保旧档。

### 1.4 消费者（只读）
- verify.ps1 门禁（§1.3）；CityWatch（watch/city-watch.ps1 实测 L26/L30 读 world-state.json + world-events.jsonl，尾 40=背景给定）；引擎事件路由器 M2（背景给定只读，代码未实读=待证）；引擎 L2 回放读档案。

### 1.5 健康实况（今日 12:16 快照）
- tick 今日 72 轮全部跑满（logs/tick-20260924.log，末轮 VERIFY PASS）；verify 游标 events_verified=1812=活流行数（无积压、无漂移）；严格 UTF-8 全量复检两流 0 坏行；隔离区仅 3 行手注测试样本（GHOST_TYPE/GHOST2/broken json=门禁工作证明）。

### 1.6 旁发现（本波新增）
- **F-A 编年史零备份**：FluxVerse/.gitignore 实测含 `world/`（git check-ignore exit=0）→ 事件流/档案/快照/双游标全部不入 git；FLEET-OPS §4 三级备份无一覆盖 → bm-a 单盘=全史唯一副本（实测全史 3,653 行/1.93MB，起点 2026-09-23T08:16:24Z）。
- F-B tick.lock 无 PID 判活（§1.1）。

## §2 定量（world\ 实测，2026-09-24 12:16-12:40 窗口）

### 2.1 存量
| 文件 | 行数 | 字节 | 备注 |
|---|---|---|---|
| world-events.jsonl 活流 | 1,812 | 610,601 | 当日 00:07–12:16 本地 |
| world-events-20260923.jsonl 档案 | 1,841 | 1,325,662 | 全史起点 09-23T08:16Z，仅 7.7h |
| world-events.quarantine.jsonl | 3 | 266 | 全为门禁测试样本 |
| perceptor-state.txt | ~250 键 | 31,083 | 随订单/任务单调增 |
| world-state.json | — | 36,886 | 两阶段晋升产物 |

### 2.2 速率
- 当日活流 1,812 行/12.15h ≈ **149 条/h**（逐时实测 81–200 波动）≈ 3,578 条/日外推。
- 归档日（09-23 上线高强度日）1,841 行/7.7h ≈ 239 条/h。
- 全史综合 ≈ 184 条/h ≈ **4,400 条/日量级**（诚实区间 3.6k–5.7k/日：1.5 天样本）；文件增速 ≈ 1.2–1.9MB/日。

### 2.3 类型与 actor 分布（合并 n=3,653）
- 类型：COMMIT 2,811（76.9%）｜GITHUB_EVENT 411（11.2%）｜HEARTBEAT 245（6.7%）｜CEO_ORDER 145（4.0%）｜TASK_CLAIM 19｜RESIDENT_SAY 10｜GAME_STAGE 6｜MEDIA_OUTPUT 2｜FX_TICK/MARKET_OPEN/MARKET_CLOSE/HQ_FEEDBACK 各 1。
- actor（活流实测）：bigmoney 969｜github 274｜minigame 180｜bigstream 79｜fluxverse 49｜机器侧合计 bm-a 45+bm-c 44+BG-A 40+bm-b 36+BG-C 8+BG-B 4=177（9.8%）｜CEO 38。
- **机队线性增长主张=确认（结构性）**：COMMIT/HEARTBEAT/TASK_CLAIM 合计 84.2%，源头均为「每机 10min 轮的 commit/心跳/认领」→ 量随机器数线性。actor 字段多记 repo 名（bigmoney 969=三机共写一仓的聚合视图），不改变「每机节律→线性」的源结构。

### 2.4 扩容外推
- **内部 5→20 机**：线性型 ×4 + 仓外源 ×~1–2 → **~16,000 条/日 ≈ 11.3 条/min ≈ 每 10min 轮批 ~113 行 ≈ 5MB/日**。对「单写者+轮末批追加+行数游标+verify O(new)」毫无压力（PS5.1 逐行处理 20k 行活流为秒级）。**结论：内部总线到 20 机不需要换存储引擎。**
- **公共面 ×100**：4,400×100 ≈ **44 万条/日 ≈ 5.1 条/s 均值**，公网用户面典型峰均比 10–50× → **50–250 条/s 突发**（业界常识，非实测）。三重不可行于内部总线：①10min git 控制面 SLA 与用户事件节奏不匹配；②PS5.1 单进程扫描管线吞吐不匹配「每用户动作即事件」；③**零服务器红线下无公网常驻入口可安放鉴权/TLS/并发写/持久化**。→ 公共面必须另立系统（§4 P3）。

## §3 三案对比（四约束全检：零服务器 / 只增 / 消费者平滑迁移 / PS5.1+Python3 双环境）

### 3.0 对比表
| 维度 | 案1 分片写 | 案2 单写者收编（推荐） | 案3 本地 SQLite |
|---|---|---|---|
| 写者数 | M 机各写各片 | 1（bm-a scan） | 1（DB 进程） |
| 跨机运输 | 仍需 git 同步分片 | git inbox（既有范式） | 无解（DB 单盘仍单机） |
| verify 改造 | M 分片游标+跨片自愈（~50% 重写） | **零** | 重写（python 接缝） |
| CityWatch 改造 | M 路尾读合并 | **零** | jsonl 导出层或 python |
| 引擎 M2 改造 | 合并读改造 | **零** | 同上 |
| 入城延迟 | ≤10–20min | ≤20min（同今日） | 同今日（单机） |
| 仓容影响 | 分片入 git ~2–5MB/日·禁清史 | inbox 小件（KB 级） | world/ 仍不入 git |
| 新语言面 | 无 | 无 | PS↔Py 接缝×3 处 |
| 复杂度/收益 | 高/低（20 机量级无收益） | **低/高** | 高/低（内部收益≈0） |

### 3.1 案1 分片写（events-<machine>.jsonl 每机一片）
- 原理：写域=机，读侧合并+evt_id 内容寻址去重。分片要被异机消费者读到，仍须走 git 同步（world/ 须解除 gitignore 或另立受控目录）——**分片没有消除运输，只消除「同文件竞写」，而后者今天本不存在**。
- 改动面清单：scan（分片写+evt_id 生成）；verify（M 分片行数游标+跨片自愈+轮转×M，事件段约半数重写）；CityWatch（M 路尾读合并排序）；引擎 M2（合并读）；gitignore/仓策+retention 裁决（20 机 ~2–5MB/日入 git，禁 force-push=永不清史 ≈1.8GB/年）。
- 迁移步骤（追加式）：①bm-a 单机双写（分片+旧流）对账 N 天 ②消费者切分片读 ③旧流冻结归档。
- 风险：合并/去重正确性成为每个消费者各写一遍的负担=三处 bug 面；仓容永久增长需独立治理裁决；evt_id 全链路纪律成本。
- 验收判据：双写期「分片合并视图 vs 旧流」逐行对账脚本输出相等；重放注入→合并视图 0 重复；各片独立轮转过 verify。
- 评：复杂度摊给每个消费者；其真正优势（免中心装配机）在 20 机量级无收益——不推荐为主线。

### 3.2 案2 单写者收编（推荐）
- 原理：异机不写 world。各机把「探针派生之外」的自发事件写**自己仓**的 inbox 文件（写域=机 → git 零冲突，与 FLEET-OPS §2.2 写域同构），随轮 commit+push（10min SLA）；bm-a scan 新增 ingest 步：枚举各仓本地 clone 的 inbox → 复用同一登记门禁（Add-WorldEvent）→ 单流追加 → 已消费批文件移 processed/（git 史只增）+游标键 `inbox:<batch>=done` 防重放。
- 改动面清单：scan.ps1 +1 ingest 步（估 ~40 行）；异机 emit 助手（~20 行）+各机轮 prompt 一句；**verify/CityWatch/引擎 M2 零改动**。
- 迁移步骤（追加式）：①registry 两步律（先在 FluxVerse 仓登记新类型→全机 pull→再 emit）②ingest 上线先「只记日志不写流」观察 1 天 ③放行。inbox/processed/主流全程只增。
- 延迟面评估（CEO 关切）：异机事件入城=生产轮 push（≤10min）+bm-a scan（≤10min）→ **尾延迟 ≤20min**。与今日探针派生路径（git 状态→10min 采集）同量级，**无退化**，符合 FLEET-OPS 单跳≤10min/闭环 20–30min 口径 → **可接受**。
- 风险：bm-a 单点（现状既有非新增；P2 runbook 缓解）；registry 拉取竞态（新类型注册未达 bm-a 即 emit → 隔离区存证可人工重放，forensic 保留）；bm-a 停机期 inbox 在 git 内天然缓冲（不丢）。
- 验收判据：AC-A/B/C/E/F/G（§5）。
- 评：改动最小、消费者零迁移、与机队既有通信范式完全同构。

### 3.3 案3 本地 SQLite（Python3 stdlib sqlite3）
- 原理：sqlite3 单写者（BEGIN IMMEDIATE/WAL）+行级游标+UNIQUE(evt_id) 去重+按日导出 jsonl 兼容层。
- 诚实评估（复杂度/收益比=差）：①PS5.1 无原生 sqlite3——scan/verify/CityWatch 三处都须走 python 子进程或依赖导出兼容层，双语言接缝（编码/错误面/环境依赖；异机 python3 可用性待证）×3；②若最终仍导出 jsonl 供消费者，DB 只是内部细节，而 §2.4 已证 16k/日量级单写者文件绰绰有余 → **内部收益≈0**；③SQLite 在网络文件系统不安全（官方明示）→ 跨机单库仍不可能，未解 CEO 真问题；④引入 schema 演进纪律，与「jsonl+登记表=即 schema」现行极简律相悖。
- 唯一正当场景=**公共面后端备选**（若红线修正）：44 万条/日对 SQLite WAL 单写者+批插可行；INSERT-only 用法保「只增」；日分区导出 jsonl 供引擎 L2 回放。→ 内部总线不落地，移交 infra-1 备选清单。
- 改动面清单（若强行内部落地）：scan/verify/CityWatch 三处重写+python 每次 spawn；验收=吞吐/一致性/崩溃恢复基准。
- 评：内部总线 3/10；公共面备选 7/10（待裁决）。

## §4 推荐案与分阶段实施序

推荐=**案 2**，内嵌案 1 的「写域=机」命名律（inbox 文件天然分片，零冲突）；案 3 移交公共面备选。

- **P0（不裁决红线也能先做·立即）**
  1. F-A 编年史备份缺口三选一（推荐 b）： 档案 gzip 入受控备份目录进 git（~200KB/日，需 T2 仓容裁决）； 按 FLEET-OPS §4 二级走数据面（TRANSFER croc/云桶）每日备份 world\； 接受风险并在 TECH.md §四登记。任一选择都先让「编年史仅存单盘」进入治理台账。
  2. F-B：tick.lock 补 PID 判活（对齐 scan.lock 范式，~5 行）。
  3. 测量律补条：对 world\ 的一切测量必须显式 UTF-8（本波教训，见 §6）。
- **P1（案 2 核心）**：scan ingest 步+异机 emit 助手+registry 两步律+`inbox:<batch>` 游标键。验收 AC-A/B/F。
- **P2（韧性与护栏）**：装配机可移植 runbook（任一机 clone FluxVerse+以档案种子重建 world\，verify/CityWatch 即可续跑）；scan 输出增「inbox 积压/最大入城延迟」两行指标；接 cadence §6 五信号监控面。验收 AC-C/E/G。
- **P3（阻塞于红线裁决·公共面）**：本波只交付「事件方言预对齐」规格：公共面事件=内部六字段核+evt_id 的超集（引擎 L2 回放同构消费）；服务端/存储选型（SQLite WAL/分区 jsonl/云服务）待 infra-1 裁决后另立简报。验收 AC-H。

## §5 验收判据（机器可验）

- **AC-A 锁回归（护 P-11）**：并发起 2×scan → 恰一者追加、另一者输出 `skip (single writer)`；事后 events_verified==活流行数。
- **AC-B ingest 正确性（P1）**：投测试 inbox 批（1 合法型+1 未登记型+同名重放）→ 主流 +1、隔离 +1、processed/ 收编、`inbox:<batch>` 落账；重放 → 主流 +0（去重）。
- **AC-C 延迟 SLO（P2）**：异机 emit → 主流出现 ≤25min（P100，24h 浸泡；日志=事件 ts_utc vs 装配轮 ts 差）。
- **AC-D 轮转/游标重定基（护 r3）**：副本目录内把活流 LastWriteTime 改昨日模拟跨日 → 档案行数=搬移前行数；verify 输出 rebase WARN；events_verified 重归一致。
- **AC-E 20 机演练（P2）**：合成 20 机 inbox 语料 → scan 单轮墙钟 ≤120s；verify 增量校验实测不随全量增长（O(new)）。
- **AC-F 消费者零回归（P1）**：固定 world 测试目录上 CityWatch 输出字节级 diff=0；引擎 M2 冒烟同断言（实现面待证）。
- **AC-G 只增审计（P2）**：inbox/processed 的 git log `--diff-filter=D`=零删除；档案创建日后 hash 抽验不变；活流除 sanctioned 自愈外只增（自愈计数留痕 verify 输出）。
- **AC-H（公共面·BLOCKED on infra-1）**：100 ev/s ×1h 持续、拒收 <1%；日分区导出 ≤5min。——红线裁决前不启动。

## §6 诚实自检

- **确认**（代码行/实测输出为证）：锁语义及 tick/scan 两锁不一致（两脚本实读）；门禁/隔离生命周期/轮转/双游标/两阶段晋升（实读+今日实况 1812=1812）；速率与类型/actor 分布（严格 UTF-8 全量复检 3,653 行 0 坏行）；world/ gitignored（check-ignore exit=0）；CityWatch 读路径（L26/L30）；车道 :x5/:x6（cadence 实测账）；FLEET-OPS SLA（§1）；tick 今日 72 轮全 PASS；infra-1 简报不存在（read_file 404）。
- **推测**：20 机 ×4 外推系数（假设新机与现机同 commit/心跳节律；实测 BG-B/C 日仅 4–8 事件=重机低发，×4 属上界口径）；公共面峰均比 10–50×（业界常识非实测）；「84.2% 线性型」源结构（由 actor=repo 聚合视图+每机 10min 轮结构推断，非逐机归属实测）。
- **待证**：引擎 M2 路由器实现（背景给定只读，未实读）；异机 python3 可用性（案 3 面）；bm-b/BG-B/BG-C 是否各持 FluxVerse clone（registry 分发路径设计前提）。
- **测量教训（诚实记录）**：首轮定量用 PS5.1 默认编码（GBK 系）Get-Content 读 UTF-8 流，**误报 316 条「PARSE_FAIL」**；严格 UTF-8 复检=0 坏行。教训已入 §4 P0-3。此教训同时反证：**流本体干净，现行单写者纪律实测健康，竞写损坏在当下不存在**。
- **样本局限**：速率=1.5 天样本（09-23 上线高强度日+09-24 一上午），日级区间 3.6k–5.7k/日（±50%）；归档仅覆盖 7.7h（上线日）非完整交易日。
- **红线依从自查**：三案全部零服务器（案 2 运输=既有 git 控制面）；编年史只增（案 2 全程追加式；案 1 需仓容独立裁决）；本简报唯一写入=本文件；全程未做任何 git 写操作。
