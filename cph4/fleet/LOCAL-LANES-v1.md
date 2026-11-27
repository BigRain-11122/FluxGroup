# 本机「一线一进程」（LOCAL-LANES-v1）· 2026-11-27

> 令源：CEO 2026-11-27「先把本机自动化任务和算力分配都停了，然后规划好，每条线给一个专用的，
> 比如 b 站的给一条，公众号给一条，好好测试」。
> 机读正身：`cph4/fleet/LOCAL-LANES-v1.json`　执行体：`Tools/fleet/line_runner.py`
> 安装器：`Tools/fleet/lane_install.py`　一屏：`cph4/fleet/LANES-BOARD.md`

## 一、先停：35 项全部卸载，plist 归档不删

- 手法：`launchctl bootout` + `disable` + plist 移入 `~/Library/LaunchAgents/disabled/20261127-ceo-stop/`。
- 留档：`cph4/fleet/STOP-INVENTORY-20261127.json`（每项的标签、命令、触发方式、停机时 pid）。
- 残留进程：按本仓工具路径清理，另停 Ollama 与 8788；实测停完无残留，可用内存 81%。
- 恢复：把对应 plist 移回 `~/Library/LaunchAgents/`，`launchctl enable` 后 `bootstrap`。
- 一键停全线：`touch .codely-cli/state/LANES-PAUSED`（不用卸载）。

### 旧 35 项的去向（不是丢掉，是合并）

| 旧作业 | 新归属 | 说明 |
|---|---|---|
| agent-acct1 / agent-acct3 | **bili** | 两个 24h 守护合成一条线，按会话窗口轮号，不同时动手 |
| usersession / practicetick / practice10 / replytick | **bili** | 会话内已含看/赞/弹幕/偶发评论，不再各挂一个定时器 |
| social24x7 / socialagentday / socialloop | **拆分** | 它们自称"单一执行体"，实际三套都在判"该谁跑"；现按线拆开 |
| sociallearn | **collect** | 浏览器学习改为纯 HTTP 采集，避免与养号抢 profile |
| newsfeed / musiccollect / forumcollect | **collect** | 子任务按 6h/12h 各自到期，一拍只跑一个 |
| gzhloop | **gzh** | 保留原逻辑，去掉"给别的平台让位" |
| trainloop / trainpipeline / acceptrun / selfgen / corpusbake | **train** | 训练→评测→烘焙归一条线，避免训完没人评 |
| mlxlora / ollamamodel / modelqueue | **底座（按线拆）** | 旧的单实例 mlxlora 拆成 `model.bili`(8788) 与 `model.gzh`(8789)；ollama 与 modelqueue 不再常驻 |
| browserd / browserd.reply | **底座** | 两个守护抢同一个 8791，只留一个 |
| socialhealth / socialaudit / duty24 / loopreg / qualityagent / resalloc / fleethb / fleetbus | **ops** | 合成一条只读体检线；旧的会互相"踢一脚"、还能把停掉的作业拉起来 |

## 二、五条线（一条线一个进程）

| 线 | 做什么 | 节奏 | 资源 | 内容判据（认产出不认台账） | 坏了怎么算 |
|---|---|---|---|---|---|
| **bili** | B站双号养号：看→偶尔赞/弹幕→极偶尔评论 | 每 10 分钟看一次，只在会话窗口内真跑 | 浏览器 + 8788 | 24h 内 ≥1 场，且窗口内有真实动作；`need_login` 一出现即 BLOCKED | 连续 6 场 profile_busy/need_login → 停线报 CEO |
| **gzh** | 公众号：采风格池→学结构→造训练集（**发文永远人审**） | 每 30 分钟一拍 | 浏览器 + 8788 | 6h 内必须有一项产出前进：pool_todo 降 / articles 增 / industry 增 / train_rows 增 | 风格池只剩死链 → BLOCKED，要新种子 |
| **collect** | 纯 HTTP 采集：新闻评论、音乐评论、豆瓣短评、公众号产业语料 | 每 30 分钟看一次，子任务 6h/12h | CPU | 入库行数必须真的增加；rc=0 但没长 = FAIL | 连续 24h 全 FAIL 或行数下降 → 停线报源失效 |
| **train** | 语料烘焙（CPU）→ 训练 → 训后评测，占 GPU | 每 30 分钟看一次，只在 01-06 / 13-17 点 | GPU | 72h 内至少一轮 RUN.json；烘焙必须刷新 BAKED-v1.jsonl | loss nan/inf 或连续 3 轮 REJECT → 停线 |
| **ops** | 只读体检 + 刷新一屏；不生产、不踢进程 | 每 10 分钟 | CPU | 一屏 15 分钟内刷新；表外作业必须报红 | 连续 3 次刷新失败 → 报 CEO |

### 为什么不把两个 B 站号拆成两条线

两个号同一个 IP。同时动手是最容易被平台串起来的特征（`ACCOUNTS-REGISTRY-v1` 的跨号隔离条款）。
一条线内按会话窗口**轮号**：上一场是谁，这一场换另一个，天然错峰。

### 底座（不算线，两条）

1. `com.fluxgroup.base.browserd`（8791）：一个已登录上下文，按 profile 隔离；没有它每次冷启动 20–30 秒且抢不到锁。
2. `com.fluxgroup.base.mlx4b`（8788）：出稿用的本地 4B，不占云端 token。


## 三之二、每条线一个专用模型、一个算力槽（2026-11-27 追令）

> CEO 原话：「每条线专用一个模型和一块算力资源 不要重叠，当然如果本地不够同时运行的时候就可以排队」。

| 线 | 专用模型 | 端口 | 算力槽 | 不够时 |
|---|---|---|---|---|
| bili | mlx 4B（独立进程 `com.fluxgroup.model.bili`） | 8788 | 独占，TTL 1h，排队最多 600s | QUEUED，下一拍再来 |
| gzh | mlx 4B（独立进程 `com.fluxgroup.model.gzh`） | 8789 | 独占，TTL 30min，排队最多 300s | QUEUED，下一拍再来 |
| collect | 无（纯 HTTP） | — | 不占槽（CPU 2 并发） | — |
| train | 无（直接吃 GPU 训练） | — | 独占，TTL 2h，排队 300s | QUEUED，下一拍再来 |
| ops | 无（只读） | — | 不占槽 | — |

**不重叠怎么保证**：`Tools/fleet/compute_broker.py` 一把文件租约（flock 原子 + pid 存活 + TTL）。
拿不到就登记到 `queue.jsonl` 按到达时间排队；**同一时刻只有一个线的活能在跑**。
进程被 kill -9 留下的旧租约按"pid 已死/TTL 过期"回收，不会永久卡住。

**实测（2026-11-27 22:42）**：
- 两个模型服务各自独立进程，RSS 各约 2.9GB；加第二个后 swap 仍为 2866.5MB（历史值未涨）。
- 让 bili 先占槽 8 秒，再起 gzh：台账时间戳 `bili granted 22:42:03 / released 22:42:11 / gzh granted 22:42:12`——**没有一秒重叠**。
- `compute_broker --self-test` 9/9（含独占、排队顺序、失效回收、越权释放）；负控：把"有效租约"判成无效，独占用例立刻变红。
- 线路运行器自检 33/33：新增"槽被占 → QUEUED（不是 FAIL、也不是偷偷并行）"与"自检不写生产状态"。

**没验到的（诚实）**：两个端口都做了真实生成（8788「用一句话夸这个视频的转场」、8789「写一句 12 字以内的汽车选购建议」
均返回中文），但 gzh 目前缺料，还没走完"选题→写作→人审"的整段链路；
训练与两个模型服务并存的峰值内存，要等 01:00 训练窗口实测。

## 三、与旧机制的三处硬差别

1. **取消平台时段轮转**。旧的 `res_alloc.may()` 让"本时段轮到 B 站"就把公众号判 DEFER，
   台账里 68 拍空转。现在专用车道只受容量闸（可用内存/浏览器数/训练在跑），不受平台轮转；
   临时调用（没有 FLUX_LANE）仍走轮转，行为不变。
2. **一线一锁一账本**。同一线 flock 非阻塞，撞车记 BUSY 不排队；状态 `.codely-cli/state/lanes/<线>.json`，
   台账 `<线>.jsonl`。不会再有"9 个调度器抢同一个 browser profile"。
3. **判据从"台账长没长"改成"产出涨没涨"**。今天实锚：gzh 台账在涨、状态写 OK，但
   「入库 0 篇、失败 38 次」——如果只看台账就是假绿。现在四类产出任一前进才算 OK。

## 四、测试记录（2026-11-27 21:40–22:0x）

| 项 | 结果 |
|---|---|
| `line_runner.py --self-test` | **21/21 PASS**（含负控：未知车道、总开关、内存 500MB、两个浏览器、训练在跑、会话中训练、假完成、登录失效、死链、表外作业） |
| 负控（把浏览器上限改成 3） | 自检立刻变红（13/14 FAIL），证明测试不是走过场 |
| `res_alloc.py --self-test` | **22/22 PASS**（新增：专用车道不受轮转但受资源闸；推理服务不算训练） |
| 真修掉的一个 bug | `train_running()` 原来只 grep `mlx_lm`，把 8788 推理服务当训练；会让训练线永远让路、一屏永远说"训练在跑" |
| bili 自动场（launchd 自开，非手工） | 22:32:34 定时器自动起线，选中 acct3（许大喵去喵星）：看 1 条 + 赞 1 条成功；随后 `coin` 冷启动抢不到 browserd 的 profile 锁把整场打崩（rc=1）→ 已修（兜住异常、记失败继续） |
| bili 登录态 | **acct1（大喵没鱼吃）失效**：21:44 起 need_login，只能看不能动手；**acct3 正常**（22:33 赞成功）。已加"坏号先停"：登录失效的号不再排班，人工登录后出现成功动作会自动恢复 |
| gzh 真实三拍 | 每拍 0.1–0.5 秒，台账在涨；**入库 0 篇、失败 38 次**，风格池只剩死链 → 判 BLOCKED（不是 OK） |
| collect 真实跑（四个子任务全部验过） | news +472 行、music +27 行、forum +106 行、industry +50 行；语料 117,958 → 119,179 行（含早前一拍 +487）。**前台直接跑超过 5 分钟会被工具取消，必须走 launchd** |
| train 决策 | dry 正确选中最新轮 `20261127-183240` 并出 DRY；烘焙到期会先烘焙；**未实跑一整轮训练**（40–50 分钟，留给 01:00 窗口） |
| ops 真实跑 | 一屏刷新成功，表外作业 0，五条线龄期正常；一屏新增"算力槽：持有者/排队"一行 |

跑采集时顺手修掉的三个真问题（都是"看着在跑、其实不前进"）：

1. `news_comments.py` 没有单拍上限：列表页一次带出上百篇，一拍跑了 8 分钟还没完 → 加 `--max-docs`。
2. `forum_comments.py` 的 `--books N` 先切片再过滤"已采过"，前 N 本采过以后天天采 0 本 → 改成"每拍采 N 本**没采过的**"。
3. 采集器 `rc=3` 的语义是"本轮没有新内容"，不是故障 → 车道判 SKIP；但 `rc=0` 却一行没长仍判 FAIL（假完成）。
4. `user_agent.py` 的 `coin/fav/follow` 走冷启动浏览器，常驻 browserd 握着 profile 锁时必然超时抛错，整场会话被打崩 → 已兜住异常，单步失败不再中断整场。
5. 坏号会白吃一半窗口 → 加 `account_health`：某号 need_login 之后再没成功动作就不再排它，另一个号顶上；登录后有成功动作自动恢复。

## 五、现在的阻塞（都是真问题，不是"在等"）

1. **B站 acct1 登录态失效**（物理件）：需要 CEO 扫码一次
   `.venv-housing/bin/python Tools/fleet/bili_login.py --account acct1`。
   acct3 正常，线会自动只用 acct3 跑；acct1 登录后自动恢复排班。
2. **公众号风格池只剩死链**（38 条全部失败 2 次）：两条路——给 3–5 个新 URL 种子，或修
   chejiahao 解析（`NEXT_DATA 里没有 articleContent`）。给种子最快。
3. **训练今晚是否开跑**：建议 01:00 窗口自动开（现有 377 行 music_seeker 段可训）；
   要我现在手动开一轮也可以。

## 六、常用操作

```bash
python3 Tools/fleet/lane_install.py --status          # 七项作业的加载状态与退出码
python3 Tools/fleet/line_runner.py --lane bili        # 手动跑一拍（其它线同理）
python3 Tools/fleet/line_runner.py --lane gzh --dry   # 只判不做
python3 Tools/fleet/lane_install.py --kick collect    # 立刻跑一拍（launchd 后台）
touch .codely-cli/state/LANES-PAUSED                  # 全线停手（不卸载）
rm .codely-cli/state/LANES-PAUSED                     # 恢复
python3 Tools/fleet/lane_install.py --uninstall       # 七项全卸（plist 一并移走）
```
