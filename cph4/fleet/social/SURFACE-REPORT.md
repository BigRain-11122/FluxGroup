# 养号线面清单（机跑判据·2026-11-18T15:13:50）

| 工具 | 做什么 | 存在 | 有自检 | 自检 |
|---|---|---|---|---|
| social_collect.py | 只读采集（页面内公开接口） | Y | Y | 未跑 |
| social_sweep.py | 批量补货（评论分页+弹幕 seg.so） | Y | Y | 未跑 |
| social_ingest.py | 入库（矩阵校验/打码/去重/冷却） | Y | Y | PASS |
| social_drafts.py | 三通道草稿（人味闸+品味闸） | Y | Y | 未跑 |
| social_comment_gen.py | 养号评论出稿（三车道并发+观众口径闸） | Y | Y | PASS |
| social_practice.py | 实战闭环（发真评论→回验→留或撤→记账） | Y | Y | PASS |
| social_review.py | 人工批审回流 few-shot | Y | Y | PASS |
| social_eval.py | 黄金集评测（红线/分类/人判） | Y | Y | 未跑 |
| social_profile.py | 风格画像（长度/问句/催更率） | Y | Y | PASS |
| social_learn.py | 24h 学习循环 | Y | Y | PASS |
| social_autopilot.py | 三层自动化（限额/熔断/审计） | Y | Y | PASS |
| social_browser.py | T3 浏览器代操作（有头+标定） | Y | Y | 未跑 |
| social_riskguard.py | 风控闸（配额/抖动/熔断） | Y | Y | PASS |
| social_comment.py | 自视频回复（wbi+csrf+回验） | Y | Y | 未跑 |
| social_douyin.py | 抖音只读采集 | Y | Y | 未跑 |
| social_threads.py | 会话状态机（Chatwoot 模型） | Y | Y | PASS |
| social_topics.py | 选题 | Y | Y | PASS |
| human_corpus.py | 语料清洗+训练门槛 | Y | Y | PASS |
| train_build.py | 造集（品味闸/去重/段位配额） | Y | Y | PASS |
| train_lora.py | LoRA 训练+运行卡 | Y | Y | PASS |
| train_eval.py | 按质量选点+分段评测 | Y | Y | PASS |
| train_sample.py | 基座 vs LoRA 对拍 | Y | Y | PASS |
| blind_ab.py | 盲评表 | Y | Y | PASS |
| comment_taste.py | 五维品味判据 | Y | Y | PASS |
| segments.py | 人群细分识别 | Y | Y | PASS |
| train_pipe.py | 训练工作流总入口 | Y | Y | PASS |
| social_agent_day.py | 循环任务单一执行体（矩阵驱动+窗口+内存互斥） | Y | Y | PASS |
| social_agent_monitor.py | 智能体监控屏（产出年龄/产出量/漂移） | Y | Y | PASS |

## 磁盘事实

```
{
 "corpus": {
  "corpus_all": 31819,
  "corpus_pass": 3466,
  "raw_comments": 26719,
  "train_rows": 965
 },
 "latest_run": {
  "run": "CMP-204622-500",
  "EVAL.json": {
   "base": {
    "n": 18,
    "avg": 59.4,
    "pass_rate": 33,
    "avg_logic": 18.1,
    "reject": 0
   },
   "iter0000500": {
    "n": 18,
    "avg": 62.4,
    "pass_rate": 17,
    "avg_logic": 17.5,
    "reject": 0,
    "sample": [
     "以前，有些歌，就是该在歌单里短暂的一鸣，唱几句，别升高潮就赶紧下台，逐客。现在太多这样的歌了，没给机会，不管懂不懂，硬是把part推到KTV的high区，下次还唱，还疯狂",
     "虽然我很喜欢，但那是一些充满活力的风格，你很难不喜欢它们。那些[那些歌曲]是那些已经流行的歌曲。",
     "我觉得表达了一些很好的见解，但是问题是，我最讨厌那些让我跳票、追不到最新视频的人！",
     "说真的，她就是我不怎么喜欢的那种，但是也不至于太讨厌而已，只是觉得有点一般。"
    ]
   },
   "best": "iter0000500",
   "verdict": "建议采用 iter0000500（均分 62.4 vs 基座 59.4，差 +3.0）",
   "prompts": [
    "视频《2025年度最令人讨厌歌曲TOP10！》（简介：今年的最令人讨厌被我赋予了新的诠释，被讨厌的或许从来不是烂歌，而是火到一定程度德不配位的热歌）。你在 B 站这条视频下面留评论。只写评论本身，不要解释，不要加引号。",
    "用 B 站观众的口吻，给《2025年度最令人讨厌歌曲TOP10！》（简介：今年的最令人讨厌被我赋予了新的诠释，被讨厌的或许从来不是烂歌，而是火到一定程度德不配位的热歌）写一句真实评论，不超过 25 字。",
    "刚看完《2025年度最令人讨厌歌曲TOP10！》（简介：今年的最令人讨厌被我赋予了新的诠释，被讨厌的或许从来不是烂歌，而是火到一定程度德不配位的热歌），写一句你最想说的话。就像平时在评论区那样。",
    "视频《“每日一遍，智商再见”》（简介：喜欢的请给一个免费的赞吧\nbgm：猪猪侠——陈洁丽\n素材：《老鼠出售》      《佩克斯.佩斯特》）。你在 B 站这条视频下面留评论。只写评论本身，不要解释，不要加引号。",
    "用 B 站观众的口吻，给《“每日一遍，智商再见”》（简介：喜欢的请给一个免费的赞吧\nbgm：猪猪侠——陈洁丽\n素材：《老鼠出售》      《佩克斯.佩斯特》）写一句真实评论，不超过 25 字。",
    "刚看完《“每日一遍，智商再见”》（简介：喜欢的请给一个免费的赞吧\nbgm：猪猪侠——陈洁丽\n素材：《老鼠出售》      《佩克斯.佩斯特》），写一句你最想说的话。就像平时在评论区那样。"
   ],
   "samples": 3,
   "temp": 0.8,
   "run": "cph4/fleet/social/train/RUNS/CMP-204622-500"
  }
 },
 "threads": {
  "threads": 1,
  "by_status": {
   "waiting": 1
  }
 },
 "launchd": {
  "com.fluxgroup.socialagentday": {
   "pid": "45051",
   "last_exit": "0"
  },
  "com.fluxgroup.social24x7": {
   "pid": "65610",
   "last_exit": "0"
  },
  "com.fluxgroup.modelqueue": {
   "pid": "95349",
   "last_exit": "0"
  },
  "com.fluxgroup.sociallearn": {
   "pid": "91613",
   "last_exit": "0"
  }
 },
 "ts": "2026-11-18T15:13:50"
}
```

## 未决项（0）

