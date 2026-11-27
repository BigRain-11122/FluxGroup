# 待建清单（BACKLOG）

> 这些**不是今天的活**，也没有可跑的 verify。写在这里是为了不丢，不是为了领。
> 领活只从 `TASKS.json` 里领。

## 已闭环（本件只作记录）

| # | 事项 | 结果 |
|---|---|---|
| **B18** | 崩溃重放写重同一天 | ✅ 已修：`engine.py` 推进前检查该 day 是否已有事件，有则 rc=2 拒绝 |
| **B19** | `release` 可被任人调用 | ✅ 已修：必须带持有者；`done` 的任务不许 release；原子写 |

## 待建

| # | 目标 | 所属模块 | 卡住的原因 |
|---|---|---|---|
| B1 | 九区地球视图 | m-v1-globe | 无实现 |
| B2 | 点开一个人看记忆链 | m-v3-interact | 无实现；依赖 T03 |
| B3 | 现实→硅基翻译 20 条 | m-r2-translate | 无实现 |
| B4 | 每日日报 | m-b1-output | 无实现 |
| B5 | 只读接口 /today | m-f2-service | 无实现 |
| B6 | 纪年 | m-w4-history | 无实现 |
| B7 | 相助记账 | m-p3-bonds | 无实现 |
| B8 | 需求与行为 | m-p4-behavior | 无实现 |
| B9 | 入籍 / 命名 | m-b2-citizen | 无实现 |
| B10 | 保管 | m-b3-archive | 无实现 |
| B11 | 结算与定价 | m-b4-billing | 无实现 |
| B12 | 声音与氛围 | m-v4-audio | 无实现 |
| B13 | 现实采集 | m-r1-intake | 无实现 |
| **B17** | writer 身份校验：`engine.py` 启动比对声明主机 | m-w2-clock | 未做；当前靠"只准一台机器跑"的制度 |
| **B20** | guard 真门禁：pre-commit/pre-push，身份来自远端 | m-f4-qa | 未做；现在 guard 是自检，`--agent 总控` 可放行一切 |
| **B21** | 验收标准防篡改：`verify`/`acceptance` 移出 worker 可改的 TASKS.json | m-f4-qa | 未做；当前 worker 能改自己的验收标准 |
| **B22** | 运行时状态出仓：`git rm --cached` + `.gitignore` + `setup.py` | m-f1-contracts | 未做；现在 state/memory 仍被跟踪，与 D2 矛盾 |
| **B23** | 远端租约 + fencing（并行前置） | m-f5-onboard | 未做；v1 因此只能单机串行 |
| **B16** | 1000 天长跑漂移观测 | m-w2-clock | 未跑；无基线 |
