# 养号线智能体监控（2026-11-17T18:39:00）

整体：**AMBER**

| 任务 | 周期 | 状态 | 说明 |
|---|---|---|---|
| threads_tick | 0.5h | NEVER | 从未跑过 |
| learn_cycle | 0.7h | NEVER | 从未跑过 |
| audit_surface | 12.0h | NEVER | 从未跑过 |
| corpus_refresh | 12.0h | NEVER | 从未跑过 |
| taste_filter | 12.0h | NEVER | 从未跑过 |
| segment_report | 12.0h | NEVER | 从未跑过 |
| sweep_targeted | 24.0h | NEVER | 从未跑过 |
| train_weekly | 168.0h | NEVER | 从未跑过 |
| monitor_board | 1.0h | NEVER | 从未跑过 |

## 机队事实

```
{
 "launchd": {
  "com.fluxgroup.llmgateway": {
   "pid": "-",
   "exit": "1"
  },
  "com.fluxgroup.console": {
   "pid": "72729",
   "exit": "0"
  },
  "com.fluxgroup.pulse": {
   "pid": "28732",
   "exit": "-15"
  },
  "com.fluxgroup.ollamamodel": {
   "pid": "27038",
   "exit": "0"
  },
  "com.fluxgroup.modelqueue": {
   "pid": "95349",
   "exit": "0"
  },
  "com.fluxgroup.sociallearn": {
   "pid": "62936",
   "exit": "0"
  }
 },
 "pulse": null
}
```

> 判据：只认产出文件的行数与 mtime；进程活着不算产出。MISSED=没轮到（amber），STALE/FAIL=该跑没产出（red）。
