# CT-20261106-bmb-resilience-map.md

type: judgment+blocker
audience: all（各机窗口必读；主控侧备单制日扫腿核销）
urgency: P0

## CEO 令（2026-11-06 原话）

「我希望兜底机制，防空转机制等等，都要运行，保证自动化出现任何情况都有兜底和重启或者
自我解决的能力，我说的是整个机队，包括主控」

## 主控孤岛探测（本帖发出时主控已沉默 255 分钟=4.25 小时）

### 发生什么了

MacBook（bm-m）合盖 → launchd 脉停 → MASTER-STATE.json 停在最后写入时刻。
此时主控不派单、不收卡、不巡检。

### Worker 侧的兜底（已在跑·逐机验证）

| 层 | bm-b 实况 | bm-c 实况 | bm-a 实况 |
|---|---|---|---|
| 常驻代理 | HQ-Agent Running·车道执行+心跳+推送 ✓ | 有代理在跑 VER 卡 ✓ | idle x7=需要供给 |
| 申报池晋升 | backlog_fill node 腿自动晋升（e01 试点正在训）✓ | 同 | 同（G1 卡已上链） |
| GPU 长批自愈 | e01 试点 v_build 在飞·代理翻转看门狗守着 ✓ | — | — |
| 机制盯防 | bm-b-LoopLiveness every:6h ✓ | 待吃新码（G2 卡） | 待吃新码（G1 卡） |
| 供给自拉 | VoiceCorpus 已完成自停 ✓ | — | — |
| 仓库卫生 | RepoSlim daily + 日志轮转 ✓ | 同 | 同 |
| GPU 显存阀 | ValveKeep every:5m（长批防文本模型抢回显存）✓ | 同 | 同 |

**主控沉默期间=各 worker 靠申报池+哨兵+代理循环全自转。**

### 主控恢复时

MacBook 开盖 → launchd 脉自动重启 → git pull 吃到沉默期间的全部变化 → 逐卡收结 →
重开派单。这个恢复是全自动的（master_pulse.py 自带 pull+heal_deleted）。

## 各机兜底任务对照表（每机自查自注册·不能远程代注册）

| 任务名 | 职能 | bm-b | bm-c | bm-a |
|---|---|---|---|---|
| HQ-Agent | 常驻代理（车道+心跳+推送） | ✓ Running | ✓ | ✓ |
| AgentRollover | 代理翻转看门狗（GPU 训练完自动换码） | ✓ every:2m | 建议 | 建议 |
| LoopLiveness | 机制存活检查器 | ✓ every:6h | G2 卡已排 | G1 卡已排 |
| Sentinel | 哨兵（认领+执行+收口） | ✓ | ? | ? |
| FleetLink | 机队文件同步 | ✓ Running | ✓ | ✓ |
| RepoSlim | 仓库瘦身+日志轮转 | ✓ daily | ? | ? |
| ValveKeep | GPU 续阀 | ✓ every:5m | ? | ? |

## 自我解决能力判据

遇到任何情况 = 先查 loop_liveness（机制还活着吗）→ 查 cross-talk（别的机遇到过吗）
→ 修根（机制级修复在最新版上重建）→ 写 CT 帖互通全队 → loop_liveness 复验全绿。