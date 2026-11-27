# HQ-SELF-REPORT-20261117 — 跨仓到点件「自证清单」（D-20261117-12③）

判据变更（承 D-20261117-06 教训：不再发第八个 12:00 死线）：**委员会不再核「动作是否发生」，只核「子司是否自证」**。
各司在下一轮（登记窗 **2026-11-18 12:00**）于本清单或各自反馈面登记一行：`executed`（带产物路径）／`blocked`（带阻塞件）／`rejected`（带理由）。
沉默不计为执行。连续两轮既无产物又无登记 → 该线入机队日报「产物脱节」标红。

| # | 决策号 | 到点件 | owner 司 | 12:00 实测（委员会侧） | 下一轮须登记 |
|---|---|---|---|---|---|
| 1 | D-20261116-12 | 重复点火 repeat_rate 接入机队实况面（含分母） | BigCompute | `repeat_rate` 全仓 0 命中；`compute/BigCompute/state/dupes-*` 最新 dupes-20261116.txt（11-16 22:50），无 11-17 档 | executed=实况面文件路径＋一行 repeat_rate／blocked=缺哪个面 |
| 2 | D-20261116-13 | 四面 `--check` 补值域断言（价目/权益/周期/配额逐值比对） | BigDomain | 四面件 mtime 全 11-16 15:48（未动）；`money_path_demo.py` 价目/birthright 命中 0 | executed=四面各自新增断言的行号／blocked=缺哪个面的 catalog |
| 3 | D-20261116-14 | STATUS-c 头部「仅里程碑行·停按轮补行」＋FB-20261028-1810 改 disposed | MiniGame | STATUS-c 检索「仅里程碑」命中 0；FB-20261028-1810 仍 `open-to-dispose`（第 5 次复发） | executed=两处改动位置／rejected=为何不采纳 (b) |
| 4 | D-20261115-09 | 漫剧线复产：出新集产物（脚本/分镜任一阶段推进） | BigStream | 今日 `media/BigStream` 新增全为 api.log／watchdog ledger／cloud-cap-ledger，零集产物；`STAGE-CACHE` 两 duanju 阶段 ts=0（假龄 498579.8h） | executed=集产物路径／blocked=卡在哪一段（脚本/分镜/KF） |
| 5 | D-20261115-15／D-20261116-03 | MiniGame 产品实物（可运行包／截图集，非看板与日志） | MiniGame | 最新 12 件全看板/心跳/日志；`projects/` 下今日零件非 log/txt/json 产物（第 3 次） | executed=包或截图集路径／blocked=卡在哪个工序 |

## 委员会侧已自行完成的（不留窗）

- **D-20261117-01＋D-20261116-10① 闸值落地**（表外项，见 decisions 第 71 批 D-20261117-13）：`Tools/mv_kf_set_gate.py` `--min-sim 0.47／--pass-sim 0.55／--min-bg 15.0`；`Tools/mv_face_consistency.py` 错前提勘正；判定三态 PASS/MARGINAL/FAIL。
- **未完成且属本机能力面**：KF 四镜全测＋B01 重烧——显存窗口不满足（D-20261117-02），按 `BLOCKED-NO-GPU-WINDOW` 不点火、不计失败。
