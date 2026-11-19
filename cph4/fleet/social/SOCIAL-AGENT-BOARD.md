# 养号线智能体监控（2026-11-19T17:08:10）

整体：**RED**

| 任务 | 周期 | 状态 | 说明 |
|---|---|---|---|
| threads_tick | 0.5h | STALE | 产出已 46.7h 未更新（周期 0.5h） |
| learn_cycle | 0.7h | OK | 产出 0.2h 前更新 · LEARNING-LEDGER.jsonl=159行 |
| audit_surface | 12.0h | OK | 产出 10.4h 前更新 · SURFACE-REPORT.md=111行 |
| corpus_refresh | 12.0h | OK | 产出 10.6h 前更新 · 无行数 |
| taste_filter | 12.0h | OK | 产出 10.4h 前更新 · QUALITY-PASS.jsonl=5179行 |
| segment_report | 12.0h | OK | 产出 10.4h 前更新 · QUALITY-PASS.jsonl=5179行 |
| sweep_targeted | 24.0h | FAIL | 上次 rc=2（允许 [0]）[sweep] 学习循环还在跑（pid 42303）。先停：launchctl bootout gu |
| train_weekly | 168.0h | FAIL | 上次 rc=1（允许 [0, 2]）[pipe] 训练失败，停止。 |
| monitor_board | 1.0h | FAIL | 上次 rc=2（允许 [0, 1]）[mon] → cph4/fleet/social/SOCIAL-AGENT-BOARD.md |

## 机队事实

```
{
 "launchd": {
  "com.fluxgroup.practice10": {
   "pid": "-",
   "exit": "0"
  },
  "com.fluxgroup.practicetick": {
   "pid": "-",
   "exit": "0"
  },
  "com.fluxgroup.traindone": {
   "pid": "-",
   "exit": "0"
  },
  "com.fluxgroup.console": {
   "pid": "72729",
   "exit": "0"
  },
  "com.fluxgroup.pulse": {
   "pid": "86505",
   "exit": "-15"
  },
  "com.fluxgroup.corpusbake": {
   "pid": "-",
   "exit": "0"
  },
  "com.fluxgroup.acceptrun": {
   "pid": "-",
   "exit": "1"
  },
  "com.fluxgroup.socialagentday": {
   "pid": "40321",
   "exit": "0"
  },
  "com.fluxgroup.ollamamodel": {
   "pid": "46322",
   "exit": "0"
  },
  "com.fluxgroup.social24x7": {
   "pid": "27816",
   "exit": "1"
  },
  "com.fluxgroup.trainrun": {
   "pid": "-",
   "exit": "0"
  },
  "com.fluxgroup.mlxlora": {
   "pid": "24297",
   "exit": "-15"
  },
  "com.fluxgroup.trainlock": {
   "pid": "-",
   "exit": "0"
  }
 },
 "pulse": null
}
```

> 判据：只认产出文件的行数与 mtime；进程活着不算产出。MISSED=没轮到（amber），STALE/FAIL=该跑没产出（red）。
