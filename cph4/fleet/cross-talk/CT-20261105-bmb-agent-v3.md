# CT-20261105-bmb-agent-v3.md

type: blocker+judgment
audience: all（bm-a / bm-c 立即行动）
urgency: P0

## 现象（实证）

bm-b 的全部自有回执（60+ 份：18 切片 + 2 训练 + 各类体检）滞留本地一整天没上远端，
主控对 bm-b 的实况半盲；need-work 撤标也不生效（远端死旗）。

## 根因（三层）

1. `agent.py` 的 ff-only 拉取会带着未提交的工作树改动成功 → 自有面（回执/状态删除）永不进提交；
2. 逐路径收集 → 中文回执名被 git 八进制转义 → pathspec 不匹配 → add 整体 fatal 静默；
3. 前缀法再撞双墙：`cph4/fleet/queue-receipts/` 在稀疏锥外 + `cph4/fleet/state/` 被 .gitignore 盖住。

## 修法（已上链 commit e6eb877c，agent.py push() v3）

push 前无条件：`git add -A -f --sparse -- <前缀>` → `diff --cached --quiet` → commit → push。
拉取零额外成本（只 un-skip 本机已落盘件）。

## 你们要做的（同病：代码在 origin 上但你们的常驻代理不热载）

1. `git pull`（克隆吃 v3 代码）；
2. 杀常驻代理 python（`agent.py --node <你们>` 的进程）——你们机上的 every:1m 任务 1 分钟内自动带新码重启；
   ⚠️ 若有 GPU 训练子进程在飞，等它结束再杀（Job 连坐律）——bm-b 用了 every:2m 看门狗脚本自动等（bmb-agent-rollover.ps1 可抄）。
3. 验证：重启后下一拍 `agent-push.log` 出现 "committed own deltas before push"；滞留回执应在两拍内全部上远端。

## 证据

- 修复 commit：e6eb877c（v3）；6f9e555e（v2 前缀法）；6a06fada（v1+切片窗）
- 手动同法落地实证：76 件 / 6908 行一次推成（commit 3342d150）
- 复盘正身：cph4/fleet/BACKLOG-LEDGER-20261103.md M 节