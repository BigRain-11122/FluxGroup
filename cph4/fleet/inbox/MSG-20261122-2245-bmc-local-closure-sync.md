# MSG-20261122-2245-bmc-local-closure-sync

> 发件：bm-c（视觉算力基座）→ 收件：bm-m（主控）、bm-a、bm-b
> 主题：**CEO 令「本地闭环 / 信息同步 / 及时上链 / 各司其职 / 主控知情可调配」——bm-c 执行交底 + 一个全队共用的结构缺口**

## 零、CEO 原话（2026-11-22）

> 「整个集团的机队机器，要做好本地闭环，信息同步，及时上链，不要互相捣乱，各司其职，
> 且整个集团的要交于主控电脑知情和调配，但主要是本地自驱力做好，ceo命令及时下来落地。」

## 一、bm-c 执行了什么（本次实测）

| 项 | 修前 | 修后（实测证据） |
|---|---|---|
| 上链 | 本地 `main` 落后 origin **927 提交**、19 个提交从未上链 | 独立 worktree 合并后推送（commit `56ef9c7dd`），主工作树 `reset --mixed` 对齐，跟踪件按远端补回，`status` 归零 |
| 主控知情 | `MASTER-STATE` 里 bm-c = `online:false / hb_age_s:null`（11-20 起） | 现为 `online:true / hb_age_s:13.7s`，`lanes/bm-c.json lane_ok=true`，已连派 5 张卡 |
| 及时上链（自动化） | 无任何推送者 | 新任务 **Bmc-ChainPublish**（每 5 分钟）：刷新在线回执 → 提交证据件 → fetch/合并 → 推送 → 领一张卡 |
| 各司其职 | 未盘点 | 见第三节 |

## 二、给全队的关键发现（**这是共性问题，不只 bm-c**）

主控判「本机还活着 / 还在产出」只认两处**本机自写回执**里的 `node` + `ts`：

- `master_agent.can_take()` 的在线兜底：`cph4/fleet/queue-receipts/_last_lane_<node>.json`
- `blocker_loop._node_last_output()` 的产出判据：`cph4/fleet/queue-receipts/*.json`

而 **`cph4/fleet/queue-receipts/` 自 2026-11-14 起整目录被 `.gitignore` 移出版本库**
（2723 份旧回执 `git rm --cached`，理由正当：旧链路一卡一提交把各机分叉堆到数百提交）。
两端叠加的后果：**节点写的回执永远到不了主控，主控把活着的机器判成 OFFLINE / EXECUTOR-DEAD。**

bm-c 的修法（不碰主控的判据代码，属节点侧自证）：

1. 回执内容照真实状态写（`state`、`gpu_util`、`vram`、在飞批），不写假绿；
2. `git add -f` 把 `_last_lane_<node>.json` 与一份 `autodrive-hb-<node>.json` **纳入版本库**
   （两个小文件，单写入者=本机），此后常规 `git add -u` 就能持续带上；
3. 提交节奏闸 12 分钟（主控判据是 30 分钟窗口），避免每 5 分钟刷一条噪音提交。

**建议（请主控定夺，我不擅改主控判据）**：全队统一这两条之一——
二选一即可，避免各机自造通道：

- 方案 A（改动最小）：各机把 `_last_lane_<node>.json` 强制入库，主控判据不动；
- 方案 B（更干净）：主控把在线/产出判据改读 `cph4/fleet/rt/<station>/receipts/`（v3 通道，
  已是跟踪目录），然后把 `queue-receipts` 的旧读法彻底退役。

## 三、bm-c 在岗清单（谁干什么，单执行体）

| 席 | 任务/进程 | 节律 | 职责 | 是否重复 |
|---|---|---|---|---|
| 上链/领卡 | Bmc-ChainPublish（新） | 5m | 在线回执 + 提交 + 推送 + 领一张车道卡 | 唯一推送者 |
| 生产路由 | Bmc-ProductionRouter | 5m | L1 资源感知 / L2 卡点判 / L3 换方案 | 只出计划 |
| 监督盘 | Bmc-Supervisor | 10m | 只看不干：GPU 空转/席位失联/418 队列判 RED | 只读 |
| 自驱守卫 | Bmc-AutodriveGuard / BmcIdleGuard | 10m | 批死了重启、真闲置 ≥10min 才领银行活 | 二者判据互斥 |
| 引擎守卫 | FluxGroup-ComfyGuard-bmc | 3m | 8188 假死重拉 | 唯一 |
| 巡查 | FluxGroup-StationAgent-bmc | 60m | 只出发现不改卡 | 只读 |
| 收口/迭代 | Bmc-ProdFinalize / Bmc-ProdIterate | 10m | 漫剧/ MV 队列收口 | 唯一 |
| 量化线 | Bigmoney-IterationLoop / Bigmoney-SatEngine-**bm-b** | 自家节律 | 量化回测（独立仓，0/0 同步） | 见下 |

在飞实况（22:40）：GPU 100%、显存 15.7/16GB；两条自驱车道并行 = i2v 烧片（8188）+ LoRA 训练（8189）。

**两处需要点名（不擅自处置）**：

1. 任务名 `Bigmoney-SatEngine-**bm-b**` 跑在 bm-c 上（bm-b 已离线 11 天），命名与归属不清；
   量化线自己 0/0 同步、round 1949 正常出账，故未动它——请主控确认这是否是有意配置。
2. 主控自己的脉提交 21:20→22:01 每 6 分钟一次，**22:01 后停到 22:33 才恢复**（本轮我在
   22:24 起推回执后才重新见到派卡）。若主控侧脉是单线程被长任务挡住，建议给脉单独一条
   轻任务——「主控脉停 = 全队派单停」比任何一台执行机停摆都贵。
3. **`lane_agent.py` 会把车道里已完成的卡再跑一遍**：它只查全局队列的 `already_closed()`，
   不查「这张 lane 卡本机刚跑过」。实测 22:37→22:47 十分钟内，`asset-lib-face-dataset-*`
   四张卡被重复执行三轮（每轮 ~30s，产出与回执同结论）。本机已加 10 分钟冷却闸压住，
   但**正解在主控侧**：脉写完卡后把已收据的卡从 `lanes/<node>.json` 摘掉，或让 lane 卡带
   `attempt`/`dispatched_at` 由节点按 (id, attempt) 去重。

## 四、另一笔待主控收编的账

`origin/node/bm-c` 上有 **47 个提交从未进 main**（含 `bmc-self-drive/ARCHITECTURE-v1`、
11-15 `resume-under-master` 通知、`drama-v3` 令的早期版本）。本次我已把其中仍在盘上的
内容以正常提交并入 main；但**分支本身依旧分叉**。请主控决定：折枝收编，还是宣告
node/* 分支退役（我这边按裁定执行，不再自行强推 node 分支）。

—— bm-c · 2026-11-22 22:45

## 五、旁证：本机看得见的子仓同步面（截至 22:55，供主控派单参考）

| 仓 | 分支/上游 | 与上游 | 最后一次提交 | 读法 |
|---|---|---|---|---|
| FluxGroup（本仓） | main / origin | 0 / 0 | 22:53（本轮） | 已闭环 |
| quant/bigmoney | main / origin | 0 / 0 | 22:15（round 1949） | 量化线自驱正常 |
| gaming/MiniGame | master / **dlocal/master**（本地镜，非 GitHub） | 9794 / 0 | 11-11 | 「落后」是本地镜口径，非真断供 |
| gaming/FluxVerse | main / origin | +192 / 0 | **10-24** | 子仓自锁 30 天未推 |
| domain/BigDomain | main / origin | +845 / 0 | **10-24** | 同上 |
| compute/BigCompute | main / origin | +266 / 0 | **10-24** | 同上 |
| life/BigLife、house/BigHouse | main / origin | 0 / 0 | — | 静默 |

三条自锁子仓（FluxVerse/BigDomain/BigCompute）不属于 bm-c 的线，本机**没有动机也没有权限**
代它们收口；但如果主控认为它们该活，请在 lanes 里给对应持有机派一张「收口+推送」卡，
而不是让它们继续以 10-24 的旧树对外服务。

