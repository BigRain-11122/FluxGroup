# 养号线智能体监控（2026-11-17T18:43:46）

整体：**AMBER**

| 任务 | 周期 | 状态 | 说明 |
|---|---|---|---|
| threads_tick | 0.5h | OK | 产出 0.3h 前更新 · threads-events.jsonl=4行 |
| learn_cycle | 0.7h | OK | 产出 0.0h 前更新 · bilibili.jsonl=430行 |
| audit_surface | 12.0h | OK | 产出 0.0h 前更新 · SURFACE-REPORT.md=193行 |
| corpus_refresh | 12.0h | OK | 产出 0.9h 前更新 · 无行数 |
| taste_filter | 12.0h | OK | 产出 0.0h 前更新 · QUALITY-PASS.jsonl=2245行 |
| segment_report | 12.0h | OK | 产出 0.0h 前更新 · QUALITY-PASS.jsonl=2245行 |
| sweep_targeted | 24.0h | NEVER | 从未跑过 |
| train_weekly | 168.0h | NEVER | 从未跑过 |
| monitor_board | 1.0h | OK | 产出 0.1h 前更新 · SOCIAL-AGENT-BOARD.md=55行 |

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
  "com.fluxgroup.socialagentday": {
   "pid": "93152",
   "exit": "0"
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
