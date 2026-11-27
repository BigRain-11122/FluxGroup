# 2026-11-06 机队自动化复盘正身（闲置根因 / 同步本质 / 实测标定 / 仍开口子）

> 来源：CEO 2026-11-06 复盘会话（「7×24 无监管」「主控只调度」「MLX 优化」「32G 不许换页过热」「素材机队自取」「测完就删」「要有人盯着」「复盘同步与联合」）。
> 用途：后续任何「机队为什么闲置 / 为什么同步冲突 / 本地模型参数怎么定」的问题，先读本文件再动手，不要重新试错。

## 一、机队闲置的总根因（盘上证据）

1. `fleet_lane` 镜像写入口只写 `state` 字段，不写 `cmd` → **347 张卡降成空壳**，车道扫到即跳过 → 全机自述 `SELF-DISPATCH`。修好后水位 `0/0/2/0` → `34/40/36/57`。
2. 执行器跑旧码不重载（改码=零效果）。
3. `load_watch.py` 被删但 launchd 仍在调用（悬空引用）。
4. `supply_batch` 缺失（无供卡源）。
5. 监管脚本一天内被冲掉 **13 个**（git 手术删未提交文件）→ 全部从历史提交取回并入库。

## 二、同步问题的本质

- `main` 与 origin 分叉 **482/85**，单日提交 **722 次**，冲突 **96% 来自 `cph4/fleet` 状态文件**。
- 结论：**把「记账」当成「代码」提交**。
- 处置：`state/ lanes/ radar/ chief/ sync/` 移出 git 跟踪。

## 三、假绿与假完成（判定类缺陷）

1. `soak` 窗口绿 80% 仍写 GREEN（单轮判定，缺窗口聚合）。
2. quick 模式不测磁盘/swap（少测即假绿）。
3. `incoherent=4`（四机全空闲且有活）只有生产方，没有消费方 → 告警无人处理。
4. `lease-heartbeat-timeout(1000000000s)`：心跳缺失被算成 31.7 年 → 秒杀卡。缺失应判「未知/重排」，不能当超时。
5. 素材智能体报「17 张可用」，实测 **6 个文件根本没被替换**（mtime 停在 18:2x）→ 验收必须看 mtime，不看自述。

## 四、本机实测标定（32G Mac，硬数字）

| 项目 | 结论 |
|---|---|
| CPU 并发拐点 | **8 核**（57→518 u/s，第 10 路仅 +3.6%） |
| 新增不可压内存 | **≈8GB**（填零页会得到 26GB 假上限，必须用不可压负载测） |
| 过热判据 | 读不到温度 → **用吞吐衰减 >15% 判降频** |
| 打标提速 | 降采样到 1024：31.2s → 5.2s；批量 23.9 → **4.1s/张** |
| 运行时选型 | ollama **1.63s** < mlx-vlm 4.13s → **不换 MLX** |
| 新模型排除 | `qwen3-vl:4b` 是思考型，单句 **9.1s**，禁用于批量 |
| 打标完成度 | store 实为 **529 张**（不是 788），完成 **528/529** |
| 磁盘 | 当天释放 **~82G**，现 **218G** 可用 |

**方法论纠错（最贵的一条）**：同一张图反复调用测到的是**缓存命中**，不是推理成本 —— 曾据此误判 mlx-vlm「慢 16 倍」。测推理成本必须换图/清缓存。

## 五、已落地能力

1. 素材自供给两层：pyenv 读盘（有 TCC 权限）回环 **8791** + 系统 python 转发 **8790**（防火墙已放行）；`asset_pull` 取不到返回 `rc=3`，**不计失败预算**。
2. 本机也是机队一员：`com.fluxgroup.locallane` 每 60s 跑车道；`capacity_guard` 开工前过闸（swap 只看增量、可用内存减 4G、GPU 前退模型）。
3. 供给闭环：`demand_gen`（缺口→卡，带去重闸）+ `supply_guard`（水位 ≥3）+ `closer`（零输出 6h 硬释放）。
4. 哨兵：`tool_watch` 每 10 分钟查「launchd 指向的脚本还在不在」；`useful_load` 每小时查「占着算力有没有产出」。

## 六、仍未闭合（不许宣称 7×24）

1. bm-b 有卡无产物（`E-ARTIFACT`）——唯一「看着在跑其实没交付」的点。
2. 队列仍靠 git 分发 → 需给 `tailnet_hub` 加 `GET /queue` 才能彻底解耦。
3. **「入库 ≠ 重载」**：改码后必须重启对应 launchd 作业，否则修复为零。
4. 素材 P0 缺 `voices`（6 套）与 `audio-bgm`（10 段）。
5. 角色包 96 张里近重复 **321 对**（每角色 3 张 2×2 拼图切四象限）→ 多样性虚高，训 LoRA 会过拟合。
6. 道具 6 件仍返工，2 张等云端额度（已记 `ASSET-GEN-PENDING.json`）。

## 七、一句话

能不能 7×24：**现在还不能宣称**。断点已从「玄学」收敛为三条具体事项：状态别进 git、执行器要重载、缺料要有源。当天修好两条半，四台机已同时在出活。
## 八、自改闸落地（2026-11-06 18:00 补记）

**做了什么**：`Tools/fleet/self_improve.py`（每台机自查码龄不重载/空壳卡/缺依赖并修，回执入 `queue-receipts/self-improve-<node>-latest.json`）+ 四张 `SELF-IMPROVE-<node>-20261106` 卡 + `Tools/fleet/fork_close.py`（分叉安全收口）。

**实测结果**：bm-m 车道自动领卡→执行→回执→提交 artifact，**闭环成立**（state=DONE，17:48:32）；三台 Windows 仍 OPEN——它们拉不到新码。

**三处自己犯的假绿（同一类病，值钱）**：
1. `env_selfheal.ensure()` 返回 `(ok, detail)`，外层套 `bool()` → 非空元组恒真 → 每次「安装成功」都是假的（bm-m 首跑就报装好 python，实际没装）。教训：调用返回元组的函数前先看签名；判成败只认第一个元素。
2. reload 检查用自己的回执判新鲜度 → 度量自指 → 永远判 OK。判据必须排除 `self-improve-*` 前缀。
3. posix 上 `python` 不存在只有 `python3` → 误报缺失；执行器本就双写。

**分叉死锁的确切机制**：poke worker 只做 `merge --ff-only`（hot-sync 也禁 rebase，C-20261104 硬法）；节点一旦 ahead>0 就永远 ff 失败 → 改码零效果。`fleet.cmd` 的 `sync` 原来只 fetch，远程清不掉。修法=`fork_close.close_out()`：ahead 提交**全为记账路径**才 `reset --mixed`（保留工作树），有一个真产物就拒绝并列文件；已接进 `fleet_agent` 的 `sync` 动作。

**仍然只能人工一次**：三台机器必须先本地 `git fetch origin main && git reset --mixed origin/main`（保留工作区），因为无 SSH/WinRM 且 sync 升级要等它们先拿到新码。重置后全自动。

## 九、指挥层高频任务表（2026-11-06 23:5x 上线并实跑）

**正身**：`cph4/fleet/COMMAND-CADENCE-v1.json`（机读六节拍）+ `COMMAND-CADENCE-v1.md`（CEO 人读）+ `Tools/fleet/commander.py` → `cph4/fleet/COMMAND-BOARD.md`（一屏），已接 `master_pulse` 的 `commander` 阶段（180s、零 token、排在 census 之后）。

**六节拍**：A 45s 值守四件（补卡/释放超时/空壳隔离/账本健全）；B 3m 机队（为何停/假完成/分叉不算在线）；C 15m 线（产出年龄/3X 停线/预算硬停）；D 60m 一屏与告警五类归因；E 6h 指挥质量（命中率/返工率）；F 1d 只交 CEO 三件 + 僵尸线挂起。

**分工铁律（写进表里防复发）**：数字一律规则算（4B 算术有实锚全错）；模型只做归类/摘要/打分且可规则复核；模型挂了一律降级为规则不停工；只留三类人工闸（不可逆/对外/花钱超限）。

**实跑证据**：脉日志 `commander=0/0.1s` 每轮出现，一屏 mtime 自动前进（23:55:58 → 23:58:04），非人工触发。

**首屏读数（真实现状）**：可派卡 2 张、在飞 0、空壳隔离 9 张、8 条线超 72h 无产物（短剧 173h / 竞品拆解 173h / 短视频 107h / 车机 100h / 元宙城 81h / 游戏 78h）、队列 1219 行（DONE 398 / FAILED 52 / UNVERIFIED 77 / CANCELLED 511）。

**同轮暴露的另一个断点（未修，如实记）**：主控脉自己 `push=rejected(non-fast-forward)`，主树 ahead 120 / behind 508，且 ahead 含 230 个真文件（Tools/*.py 等），`fork_close` 按安全线拒绝收口。根因=脉每轮把产物提交进 git；单次 reset 会复发，正解是让产物不进 git 或让脉 ff 失败时受控重提。影响面有限：commander/self_improve/fork_close 本体已在 origin，只有脉自己的产物推不上。

## 十、指挥节奏表 v2 与同步死锁（2026-11-07 00:1x）

**交付**：`COMMAND-CADENCE-v2.json` 30 条可排期单元（period/phase/depends_on/actor/input/output/accept/on_fail/backoff/budget），四规则=错峰（同周期同相位判 ERROR）、串行（写同一文件必须 depends_on）、退避（2x 上限 8 周期）、降级（模型挂了降规则不停工）；`Tools/fleet/cadence.py` 校验器（表自检 + 与 STAGES 一致性 + 排期），首跑 **PASS 0 错 0 警**；新增 `ceo_three.py`（每天只交 CEO 三件，规则排优先级）；6 个阶段接线进脉并实测：`self_improve=0/0.1s ceo_three=0/0.0s card_contract_check=0/0.1s fork_close=1/4.9s tool_watch=0/0.1s useful_load=0/8.6s`。

**同步死锁的真机制（两次修错才认清）**：push 被拒的原因是 behind，合远端要干净树，而 `git status` 把**落后于 origin** 的文件也报成 M。
- 第一版「内容==origin 就 checkout 归位」→ checkout 恢复的是**落后 HEAD 的旧内容**，反而把文件变旧（实测 master_pulse.py 被自己回滚）。
- 第二版「内容==origin 才放行」→ 漏掉「本地只缺 origin 内容」这一类，game_submit_pack.py 被误判手改。
- 正确判据=**diff --numstat 看方向**：本地有新增行=真手改（阻塞，绝不 autostash，会把人改动藏进 stash）；只有删除行=本地落后（checkout origin 安全对齐）；无差异=假脏（放行走 autostash）。

**仍未解（结构性，别再当 bug 修）**：脉与人工会话共用同一工作树且手改持续不提交，判据修好后仍每轮换一个文件被判手改（fleet-nodes → game_submit_pack → self_improve → 又回 fleet-nodes）。正解只有两条：①改完立刻 commit（纪律）；②脉迁独立工作树（但队列是权威账，双树会双写，必须先定单一写入者）。定案前 `skipped:dirty(hand-edit X)` 是如实告警，不是故障。

**观察方法**：多次 kickstart 后脉会起新实例（etime 归零），判断效果只看日志时间戳，不看 PID。
