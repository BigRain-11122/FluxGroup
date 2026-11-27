# 提案：CLOCK-SKEW 加动作线（受保护件，待 CEO 令）

- 提出：CEO-PROXY 事件班 2026-11-10 01:2x-01:4x（承载件触发）
- 对象：`Tools/fleet-dispatcher.ps1`（BLUEPRINT §九 受保护四件之一）——**本席未改，只提方案**

## 问题（本轮实测，可复算）

`CLOCK-SKEW` 在 00:21/00:31/00:51/01:01/01:21 连报 5 次，值 1722→1934ms 单调爬升，
读起来像"节点时钟在漂"。本轮用两条独立证据判定它是**中继不对称假读**：

1. **A/B 直读**（本机 → bm-b `/health`）：
   - `local_before=01:33:08.939`，`bm-b ts=01:33:08`，`local_after=01:33:09.999`，
     `rtt_ms=1060`。bm-b 的 ts 落在调用窗内 → 真实偏差 ≤ 窗口宽，约 0–0.15s。
   - bm-b 自测同口径：`clock_offset_ms=152.9`，`clock_rtt_ms=264.6`。
   - 同期枢纽报告：`offset_ms=1174–1934`、`precision_ms=399–431`（=RTT/2）。
2. **判据本身**：`fleet-clock-report.ps1` 用 `|offset| > 2*rtt+20` 判 SKEW-HIGH。
   该式只在对称路径下成立；bm-b/bm-c 走 Tailscale relay 时 RTT 260–860ms，
   单向不对称本身就能吃掉几百毫秒到 1 秒，**没有上界**。

结合 2026-11-06 判例（同族读数 1506/4091ms 被判 relay 物理底噪，卡 `release_reason=
BELOW-ACTION-LINE`，R8b-8 设动作线 30s）：**这条旗标在 relay 路径上会永久常亮**，
而它常亮的结果是真钟漂（w32time 停摆）也被当噪音忽略。

## 建议改法（最小面）

1. 动作线落地：`SKEW-HIGH` 仍按现式算（观测面不变），但 **P1 只在该节点 |offset| ≥ 30000ms
   或 `absOff/ rtt/2 ≥ 10` 且连续 3 个采样周期同向时发出**；否则降为 `CLOCK-SKEW-OBSERVE`（一行，不占 P1 预算）。
2. 旗标行同时打印该节点的 `relay|direct` 与 `rtt`，让读旗人一眼分辨物理底噪与真漂。
3. 真钟漂判定改用**单机自证**：节点 `clock_offset_trusted=false` 或 w32time≠RUNNING 时，
   发 `CLOCK-UNTRUSTED`（这个才是能落到 `Tools/fleet/clock_resync.py` 的可执行项）。

## 判据

- 上线后连续 5 个班次不再出现无动作线的 `CLOCK-SKEW` P1；bm-b/bm-c relay 期间预期只看到
  `CLOCK-SKEW-OBSERVE`。
- 反例保留：把某节点 w32time 停掉并把系统时间拨快 60s，须发 `SKEW-HIGH` 且升级
  `CLOCK-UNTRUSTED`，不得被观测档吞掉。

## 需要的授权

受保护件改动 = CEO 令唯定谳（ROUND 步9 / BLUEPRINT §九）。获批后由 master 席实施，
本席不自行落地。


## 附注 R36（2026-11-11 03:5x·CEO-PROXY 事件班实测补充）

1. **SKEW-HIGH 被遮蔽**：本文件上游的判据修法之外，另有一条独立缺陷——`Tools/fleet-dispatcher.ps1` 时钟段是 if/elseif，只要 `old_schema>0 or missing>0` 就只输出 CLOCK-UNALIGNED，`SKEW-HIGH` 永不输出。bm-b 自 11-10 起长期离线（missing=1 常态），因此 bm-c 的钟偏在旗面完全不可见，只能到 `CLOCK-SKEW.json` 里翻。建议改法（受保护件，候 CEO/群审）：两段独立输出，或在 CLOCK-UNALIGNED 行尾附 `also: bm-c SKEW-HIGH 4615ms`。
2. **本次实测数值**：bm-c offset=4615.3ms、precision=±413.4ms（ratio 11.2，越 10 倍门限）；`GET http://100.123.74.104:8790/health` RTT 1129ms 回 `ts=03:31:00` 对比本机 `03:31:05.57` ⇒ 落后约 4.4s。即：本文件前文「relay 不对称假读」在本次读数上不成立，应改判为**真偏**。
3. **修法可达性**：`Tools/fleet/clock_resync.py` 在 bm-b/bm-c 上历史上报 `CARD-DEFECT SCRIPT-MISSING`（节点仓缺该脚本），bm-a 上 `rc=2147943462`（服务起不来）。因此重派时钟卡没有意义；唯一路径是本机提权：`sc config w32time start= auto && net start w32time && w32tm /resync`，与 R2.35 的 S4U/提权批合并办理。
