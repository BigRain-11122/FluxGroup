# 总览（自动生成，别手改）

> 生成时间 2026-11-27 22:31 · 世界第 **573** 天 · 9 区 · 12361 人 · 573 条事件 · 6481 条记忆
>
> 重新生成：`python tools/status.py`　查过期：`python tools/status.py --check`

## 一 现在能不能干活

- 可执行模块 **11** / 登记 **22**（空位 10 个，是预告不是交付）
- 进行中任务 **0** · 可领 **4** · 被前置卡住 **1** · 已完成 **0**

## 二 现在就能领的活

| 任务 | 模块 | 是什么 | 怎么验 |
|---|---|---|---|
| T01 | m-f4-qa | 坏数据负控 5 例全部拦住 | `python tools/sim_test.py --only T3` |
| T02 | m-w3-settle | 结算可重建且不过期 | `python tools/sim_test.py --only T4` |
| T03 | m-p2-memory | 断电→记忆→认不出 | `python tools/sim_test.py --only T5` |
| T11 | m-f5-onboard | 并发领取恰好一人成功 | `python tools/sim_test.py --only T8` |

### 被卡住的

- T12 世界在变且有因果 —— 等 T02 做完

## 三 模块进度

| 模块 | 名称 | 状态 | 下一步 |
|---|---|---|---|
| `m-b1-output` | 内容与分发 | 可用 | 先出第一条，再谈形式 |
| `m-b2-citizen` | 身份与入籍 | 空位 | 先定三档身份与权限 |
| `m-b3-archive` | 保管 | 空位 | 先定「存什么、找得到什么」 |
| `m-b4-billing` | 结算与定价 | 空位 | 先定「看免费、动收费」的分界 |
| `m-f1-contracts` | 契约与数据 | 可用 | 加事件与模块的校验规则 |
| `m-f2-service` | 服务与 API | 空位 | 先做 /today 与 /region/:id |
| `m-f4-qa` | 质量闸 | 在写 | 把 world_ops validate 扩展成契约测试 |
| `m-f5-onboard` | 协作与接入 | 可用 | 把任务板做成机器可读并自动分配 |
| `m-p1-census` | 居民与户籍 | 可用 | 从 27 扩到 100，保持每人一件未了的事 |
| `m-p2-memory` | 记忆链 | 可用 | 把「断电/删除」写进记忆链并可见 |
| `m-p3-bonds` | 关系与相助 | 空位 | 先做「相助记账」：帮一次记一次 |
| `m-p4-behavior` | 需求与行为 | 空位 | 先做规则版，最后才接模型 |
| `m-r1-intake` | 现实采集 | 空位 | 手工录入版先行，自动采集后补 |
| `m-r2-translate` | 翻译规则 | 可用 | 先定 20 条翻译对照 |
| `m-v1-globe` | 地球渲染 | 可用 | 复用 CityWeb 的 three.js 栈 |
| `m-v2-city` | 城市渲染 | 空位 | 把 CityWeb 接成一个区 |
| `m-v3-interact` | 交互与介入 | 可用 | 先做「点开一个人，看他的记忆链」 |
| `m-v4-audio` | 声音与氛围 | 空位 | 先做一条广播 |
| `m-w1-regions` | 地理与区域 | 可用 | 补地理关系（谁挨着谁） |
| `m-w2-clock` | 时间与推进 | 可用 | 从「一天一条」升级为「八拍一日」 |
| `m-w3-settle` | 状态结算 | 可用 | 把年龄/人口变化也纳入结算 |
| `m-w4-history` | 历史与纪年 | 空位 | 先做「纪年」：用大事给年代命名 |

## 四 已完成的任务

还没有已交付的任务。

## 五 有问题的 / 还没做的

| 编号 | 要做的事 | 模块 | 为什么卡着 |
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
| B17 | writer 身份校验：`engine.py` 启动比对声明主机 | m-w2-clock | 未做；当前靠"只准一台机器跑"的制度 |
| B20 | guard 真门禁：pre-commit/pre-push，身份来自远端 | m-f4-qa | 未做；现在 guard 是自检，`--agent 总控` 可放行一切 |
| B21 | 验收标准防篡改：`verify`/`acceptance` 移出 worker 可改的 TASKS.json | m-f4-qa | 未做；当前 worker 能改自己的验收标准 |
| B22 | 运行时状态出仓：`git rm --cached` + `.gitignore` + `setup.py` | m-f1-contracts | 未做；现在 state/memory 仍被跟踪，与 D2 矛盾 |
| B23 | 远端租约 + fencing（并行前置） | m-f5-onboard | 未做；v1 因此只能单机串行 |
| B16 | 1000 天长跑漂移观测 | m-w2-clock | 未跑；无基线 |

## 六 建议顺序

1. 领 T01（坏数据负控 5 例全部拦住）
2. 领 T02（结算可重建且不过期）
3. 领 T03（断电→记忆→认不出）
4. 先解锁：T02
5. 清待建里风险最高的那条（看第五节第一行）

## 七 怎么维护

- 任何任务状态变化后，重跑 `python tools/status.py`。
- `ready.py` 会检查本页是否过期，过期就不算就绪。
- 本页只汇总，不存事实；事实在 `TASKS.json`、`modules/*/module.json`、`BACKLOG.md`。
