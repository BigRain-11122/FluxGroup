# 养号线智能体监控（2026-11-19T19:41:30）

整体：**RED**

| 任务 | 负责人 | 周期 | 状态 | 说明 |
|---|---|---|---|---|
| threads_tick | 养号席·会话 | 0.5h | OK | 事件驱动：本次 0 条待处理（产出 49.3h 未涨属正常） |
| learn_cycle | 养号席·采集 | 0.7h | OK | 产出 0.1h 前更新 · LEARNING-LEDGER.jsonl=163行 |
| audit_surface | 养号席·体检 | 12.0h | OK | 产出 0.9h 前更新 · SURFACE-REPORT.md=103行 |
| corpus_refresh | 语料席 | 12.0h | OK | 产出 1.5h 前更新 · 无行数 |
| taste_filter | 语料席 | 12.0h | OK | 产出 0.9h 前更新 · QUALITY-PASS.jsonl=5180行 |
| segment_report | 语料席 | 12.0h | OK | 产出 0.9h 前更新 · QUALITY-PASS.jsonl=5180行 |
| sweep_targeted | 养号席·补采 | 24.0h | FAIL | 上次 rc=2（允许 [0, 3]）[sweep] 学习循环还在跑（pid 42303）。先停：launchctl bootout gu |
| train_weekly | 训练席 | 168.0h | FAIL | 上次 rc=1（允许 [0, 2, 3]）[pipe] 训练失败，停止。 |
| monitor_board | 主控·监控席 | 1.0h | OK | 产出 0.5h 前更新 · SOCIAL-AGENT-BOARD.md=75行 |

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
   "pid": "29869",
   "exit": "-15"
  },
  "com.fluxgroup.mlxlora": {
   "pid": "72075",
   "exit": "0"
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
