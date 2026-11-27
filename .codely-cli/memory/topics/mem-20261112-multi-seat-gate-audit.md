# 多专家席审查：六种"假绿闸"与未修的 P0（2026-11-12）

CEO 指令：「你多专家测试，不要仅从一个维度」。执行方式=五个后台子代理各扮一个专家席（运维/数据一致性/安全权限/算力成本/可维护交接）+ 主控自审"闸是否真管用"（gate-rigor 六问）。

结论：**推翻了前一轮"内部全绿、82.5 分"的判断**。绿是真的（39/39），但绿本身不可信——闸在报绿，现实是红的。六席中四席独立指到同一批根因。

---

## 一、六种"假绿闸"形态（可复用到任何闸的审查）

1. **闸从不打开被检对象**。`fleet_doc --check` 只比"源与源是否打架"，从不读 `FLEET-SPEC.md`：手改 `16C→999C` 仍报"漂移 0 处" rc=0。判据=改一个字看闸红不红。
2. **用例名与实现不符**。`run_all_tests` 的 L3 叫"测试目录新鲜"，实际跑 `test_catalog --self-test`（内存 build+render 断言自己）；`--check` 压根不存在（rc=2）。全绿时文档已陈旧。
3. **旗标/语法错了也判绿**。排班写 `git pull --rebase --autostart`（git 无此旗标，rc=129），校验器只查"脚本文件在不在盘"，对无脚本命令直接跳过。正法=拿 `<tool> <sub> -h` 的 usage 核对每个旗标，且**绝不把待测旗标一起传进去**（否则报错文本让它"看起来存在"）。
4. **判据靠字符串存在性而非真实调用形态**。只认 `/api/generate` 字样 → 审计器把自己和探测常量判成"直连模型"。正法=正则匹配带括号的调用 `(urllib\.request\.(urlopen|Request)|requests\.(get|post|Session))\s*\(`。连带：两个工具互为被检对象时，任何一方写进对方要扫的常量名都会互相误判。
5. **静态估算冒充实测**。排班只算任务自身进程的模型调用，而 `station_drive` 用 `shell=True` 跑卡上的生产命令，那才是消耗大户。实测活跃期 30 次/时 → 730 次/天，预算 300。正法=实测对账（读本机账、排掉 `embed-cache-hit`，它占 42-53% 会把量虚高一倍）+ 速率外推（用 7 天窗口标活跃小时，24h 窗口在服务停着时标不出速率）。
6. **"没有在执行者"被算成"可用"**。19 条排班全绿、自检 13/13，但 44 个 LaunchAgent 全在 disabled/、无 crontab、无进程。正法=单独一档 `PLAN-ONLY`；表合法 ≠ 在跑。

**通用自检问法**：把被检对象改坏一个字 / 把执行体停掉 / 把调用改错一个旗标，闸红不红？不红就是没有闸。

---

## 二、人判护栏的两个可绕过洞（安全席实锤，已修）

- `judge` 大小写敏感：`MANUAL`/`Manual` 不在 `MANUAL_JUDGES=('manual','human')` → 卡上写大写就自标 DONE。
- 卡级 judge 覆盖权威表：`T-OPS-CEO`（taxonomy 唯一人判类型）在卡上写 `judge:"path"` 也能自标 DONE。
- 正法：`strip().lower()` + **taxonomy 说人判则卡级只能保持/升级，不许降级**。负控 6 条（含大写四种 + 降级）。

---

## 三、五席查出的 P0（未修，按"先让一台机真跑一轮"排序）

### 3.1 自驱主干（同一根因，三席独立复现）
1. **跨工位交接必崩**：`station_drive.handoff()` 直接 `ss.upsert(别家分片)`，`write_queue` 在 root=None 时抛 `PermissionError`；`once()` 与 `while True` 都无 try → 崩在 `record()` 之后、`append_log()` 之前：卡已 DONE、回执已落盘、日志没有、守护死亡。正法=写自己分片的 `handoff_to` outbox，由目标机 SENSE 时读 origin 自行入队。
2. **并发 claim 重复执行**：`claim()` 无 CAS，三个进程同跑一张 OPEN 卡 → 执行 3 次、回执 2 份（同秒撞名覆盖）、钱扣 3 遍。正法=锁内 CAS（`state` 仍为 OPEN 才写 RUNNING）+ 进程级单例锁。
3. **坏行被洗白**：`read_queue` 数了 `bad` 却丢弃；下一次 upsert 整表重写把半行永久抹掉（一次撕裂丢 2 张卡），无异常无计数。正法=返回 `(rows,bad)`、发现坏行拒绝覆盖并另存 `.corrupt-<ts>`。
4. **8 种状态是死卡**：`TERMINAL`（shards）= DONE/CANCELLED/ARCHIVED/FAILED，`DONE_STATES`（drive）= DONE/CANCELLED/SHELVED，两套不一致；FAILED/BLOCKED/REVISE/PENDING_* 既不执行也不重建。评审团判"返工"（REVISE）的卡直接躺死。
5. **reclaim 只覆盖 1/5 形态**：owner≠本机、无 claimed_at、时间戳乱码的 RUNNING 永久卡死；且 reclaim 排在状态/磁盘闸之后，机器 paused 时根本不执行。
6. **命令超时未捕获**：`subprocess.run(..., timeout=1800)` 无 `except TimeoutExpired`，`shell=True` 只杀 shell，真子进程继续写同一产物目录，45 分钟后 reclaim 退回 OPEN → 两个写者同写。

### 3.2 安全
7. **卡里的 cmd 无任何校验且 `shell=True`**：`card_gate` 只被 `lane_agent` 调用，自驱主路径零校验；能往分片提交一行（或能 push 仓库、能改 `PRODUCTS.json.commands`）＝能在五台机以本机用户身份执行任意命令。实际防线只是"少数人有 push 权"（权限边界，非系统边界）。
8. **一机一写者护栏三种静默失效**：传 `root` 即跳过校验；`FLEET_STATION` 自改即放行；`local_model` 导入失败（普通编辑语法错即可）→ `_own_station()` 返回 None → fail-open 且无告警。而失效后是**整文件重写**别人队列（有过一次把 visual 分片清成 1 行，靠 git 还原）。
9. **抽验 A3 恒不触发**：`record()` 回执不写 `judge` 字段，`master_patrol` 的 A3 永远判不了"人判件被标 DONE"；且零抽验时打印"本轮无待抽验件"、`sample_fails=0` = 绿。

### 3.3 算力
10. **`keep_alive="10m"` 强制覆盖调用方**：resident 席策略压掉显式传参（连 `0` 也被改），11-10 模型常驻 1443/1440 分钟（100%），真干活 87 分钟，占空 6%。
11. **8 个 brain 席额度记给未入网机器**：`MODEL-COMPUTE.brain.url=null` → 阶梯里没有这一级；`agent_schedule` 按"声明端点"记账 → 活全压 MacBook，账记到大脑（3000/天额度用 0）。
12. **无 AVX2 禁令是死条目**：`forbid` 里 `*llm-cpu*` 匹配不到任何活类（8 个类名无此串），且 `cpu_alloc` 只被自测和文档生成调用，派单/执行路径从不查。
13. **`fork_repair` 每 240s 跑 122.3s 且 rc=1 被视作允许**：12.2 小时/天，占主控半天。

### 3.4 可维护
14. **正身入口断链**：`AI.md` 仍指 CANON-V2 为"现行"；README 五步阅读顺序不含 `cph4/fleet/`，新人永远读不到 CANON-V3。
15. **上岗文档第 2/4/7 步全是 `python3`**（三台 Windows），而同一文件第 5 行自己说没有 python3；`brain`/`control` 两份岗位书也仍有 `python3`。
16. **同一事实多套数**：测试层数 32/36/38/26/28 五处；TOOL-PENDING 55/56/16 三处；CPU 核数在 `AI.md`/`resource-chain.md` 按线程当核（差 2 倍）；"看谁有活"有四个互不相认的界面，`fleet_status` 还打印 abcd 代号（CEO 已明令禁止）。
17. **`docs_curate --check` 只扫 `cph4/fleet/registry/` 一个目录**，AI.md 7 条死指针、CODELY.md 3 条（含旧队列路径三处）全部漏检。
18. **回归编号缺 RG-36/37**，CANON 却写"RG-01..38"。

---

## 四、P0 之外：测试照不到的十个盲区（价值最高）

护栏与交接的交互、并发 claim 的执行次数（R-04 只断言行数=1，不数执行次数）、坏行被下一次 upsert 洗白（R-03 断言带 `or len(rows)>=1` 兜底，几乎不可证伪）、状态机只测 DONE→RUNNING 一条、同秒回执（R-05 刻意错开时间戳）、Windows 锁超时降级（`except: pass` 无任何用例）、fsync/掉电持久性（`test_catalog.GAPS` 自己标注未测）、零抽验=假绿、长期增长与写放大、测试自身写生产分片。

---

## 五、本轮已修（提交 940f75dc4，全量 39/39 全绿 191s）

假绿闸 6 条（旗标校验、两份文档真比对、并发判据、实测对账+速率外推、PLAN-ONLY）、人判绕过 2 条（大小写+卡级降级）、调用账按工位分离（`rt/<station>/local-model.jsonl` + station 字段 + status 两本并读）。

新增负控共 15 条：错旗标、手改文档、同工位 6 任务并发、400 次真生成判超支、缓存命中不计、会推理写 0 次、audit_deep 不推理、`MANUAL/Manual/HUMAN` 判人判、卡级降级、探测两方向。

---

## 六、下一步顺序（等 CEO 拍板）

先让**一台机真正能自驱一轮**：交接通道改 outbox（3.1-1）→ claim CAS + 单例锁（3.1-2）→ 状态迁移表带退避（3.1-4）→ cmd 白名单/验签 + 去掉 shell=True（3.2-7）。这四件不做，注册执行体只会放大错误。之后再谈 `go-live --apply` 与恢复服务。
