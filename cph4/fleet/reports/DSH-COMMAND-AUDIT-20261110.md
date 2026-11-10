# 机队受令与产出审计（2026-11-10 19:15–19:35）

> 发起：CEO 直问「看一下机队是否听你指挥 并有产出」
> 方式：不读旧结论，直接投真卡，让自主脉冲自己领、自己跑、自己回执；逐环取证。
> 执行面：bm-m（主控）为主，另点名 bm-a 做跨机验证。

## 一、结论（先给判断）

1. **听令：是。** 投卡后 40–120 秒内被自主 `lane_agent` 领取执行，全程无人工跑命令；
   卡上 `created_by=dsh-session/ceo-direct`，回执里 `cmd` 原样保留。
2. **有产出：是。** 4 张测试卡全部落盘产物，3 张已进 git（`job(<卡号>): artifact [via bm-m]`）。
3. **但记账会撒谎。** 快卡（<1s）被记成 `FAILED / E-ARTIFACT / rc=0, no output captured`，
   而产物其实已在盘上并已提交。原因已定位并修复（见 §三）。
4. **不是全队都在线。** bm-c 执行器已死 12.4h（`EXECUTOR-DEAD`，RAM 阻塞），
   bm-d 未装机；bm-a 心跳正常。机队现在是「主控 + bm-a 能干活，bm-c 掉线」。

## 二、取证链（同一张卡：投→领→跑→回执→产物→入账）

| # | 卡号 | 产物 | 回执 | 入账 |
|---|---|---|---|---|
| 1 | CMD-DSH-20261110T1916 | `state/canary/…txt`（274B，含队列分布） | rc=0 / 0.1s | 先 FAILED，修复后 DONE |
| 2 | CMD-DSH-20261110T1922 | `reports/2026-11-10-dsh-command-test.md`（371B） | rc=0 / 0.1s | 先 FAILED，修复后 DONE |
| 3 | CMD-DSH-20261110T1930 | `reports/t3.md`（对照组，sleep 3） | rc=0 / 3.1s，OK | DONE |
| 4 | CMD-DSH-20261110T1938 | `reports/verification-after-fix.md`（含 BLOCKED 字样） | rc=0 / 0.1s，OK | DONE（19:28:01） |
| 5 | CMD-DSH-20261110T1929 | bm-a 跨机卡：19:28:49 已领取（owner=bm-a），产物 5 分钟未落地 | 无回执 | 仍 RUNNING |

对照组 3 说明：卡本身没问题，`sleep 3` 的慢卡一次通过；差别只在「文本产物内容里
有没有出现 BLOCKED 这个词」。

## 三、根因与修复

`Tools/fleet/flux_contracts.py::deliverable_blocked()` 对 `.md/.txt/.csv` 的判断是
「前 400 字符里出现 `BLOCKED` 即视为拒绝回执」。于是任何**如实统计队列状态**的报告
（`"BLOCKED": 6`）都会被当成「守卫拒跑留下的回执」，`artifact_ok()` 返回 False，
`lane_agent` 据此把 `rc=0` 记成 `E-ARTIFACT`。全仓有 18 个正常文档会被这条规则误伤
（`DAILY-BRIEF.md`、`DISPATCH-LOG.md` 等）。

修复（commit `1bc96836d`）：`BLOCKED` 必须在文件**开头**才算拒绝回执，
`RECEIPT_IS_NOT_DELIVERABLE` 哨兵保持全文匹配。真拒绝件仍被拦住，
真报告不再被误判。修复后卡 4 一次通过（`outcome=OK, deliverable_exists=true`）。

## 四、仍然存在的问题（未擅自改）

1. **bm-c 掉线**：`lanes/bm-c.json` = `EXECUTOR-DEAD (12.4h 零产出)`、`CAPACITY-BLOCKED-RAM`。
   这是「机队 4/5 在线」里真正影响产能的一条。
2. **状态收尾滞后**：卡 4 的回执 19:24:43 已是 OK，队列行到 19:28 仍是 `RUNNING`
   （`master`/`closer` 的入账步慢于执行步）。DONE 数最终会补上，但「运行中」计数不可信。
3. **失败账**：修复前 3 条 FAILED 中至少 2 条是本类误判（`…-TRIAGE-…` 的 .md 回执同病）。

## 五、口径边界

- 已验证：投卡→自主领取→执行→回执→产物→git 落地，在 bm-m 上完整闭环（4 张卡）。
- 部分验证：bm-a 的点名卡**已被领取**（听令成立），但 5 分钟内既无回执也无产物，
  队列行停在 RUNNING——bm-a 的「领了能不能交付」这一环没有证据，不能记绿。
- 未验证：bm-b 执行面、GPU 类卡、需组网/账号的卡。
