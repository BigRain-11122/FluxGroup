# 养号线面清单（机跑判据·2026-11-17T18:30:26）

| 工具 | 做什么 | 存在 | 有自检 | 自检 |
|---|---|---|---|---|
| social_collect.py | 只读采集（页面内公开接口） | Y | Y | PASS |
| social_sweep.py | 批量补货（评论分页+弹幕 seg.so） | Y | Y | PASS |
| social_ingest.py | 入库（矩阵校验/打码/去重/冷却） | Y | Y | PASS |
| social_drafts.py | 三通道草稿（人味闸+品味闸） | Y | Y | PASS |
| social_review.py | 人工批审回流 few-shot | Y | Y | PASS |
| social_eval.py | 黄金集评测（红线/分类/人判） | Y | Y | PASS |
| social_profile.py | 风格画像（长度/问句/催更率） | Y | Y | PASS |
| social_learn.py | 24h 学习循环 | Y | Y | PASS |
| social_autopilot.py | 三层自动化（限额/熔断/审计） | Y | Y | PASS |
| social_browser.py | T3 浏览器代操作（有头+标定） | Y | Y | PASS |
| social_riskguard.py | 风控闸（配额/抖动/熔断） | Y | Y | PASS |
| social_comment.py | 自视频回复（wbi+csrf+回验） | Y | Y | PASS |
| social_douyin.py | 抖音只读采集 | Y | Y | PASS |
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

## 磁盘事实

```
{
 "corpus": {
  "corpus_all": 20253,
  "corpus_pass": 2245,
  "raw_comments": 14280,
  "train_rows": 1884
 },
 "latest_run": {
  "run": "20261117-175135",
  "RUN.json": {
   "ts": "20261117-175135",
   "run_dir": "cph4/fleet/social/train/RUNS/20261117-175135",
   "rc": 0,
   "plumbing_only": false,
   "base_model": "/Users/junsheng.sun/.fluxgroup/models/qwen3.5-4b-4bit",
   "argv": [
    "mlx_lm",
    "lora",
    "--train",
    "--model",
    "/Users/junsheng.sun/.fluxgroup/models/qwen3.5-4b-4bit",
    "--data",
    "/Users/junsheng.sun/FluxGroup/cph4/fleet/social/train",
    "--batch-size",
    "1",
    "--iters",
    "300",
    "--num-layers",
    "8",
    "--learning-rate",
    "1e-05",
    "--max-seq-length",
    "256",
    "--steps-per-eval",
    "60",
    "--adapter-path",
    "/Users/junsheng.sun/FluxGroup/cph4/fleet/social/train/RUNS/20261117-175135/adapter",
    "--seed",
    "20261117",
    "--mask-prompt"
   ],
   "train_rows": 1884,
   "data_sha": {
    "train.jsonl": "12e84c74dfea8f57",
    "valid.jsonl": "793d8bf6edddb69e"
   },
   "iters": 300,
   "train_loss_last": 4.042,
   "val_loss_last": 3.906,
   "train_loss_head": [
    4.937,
    4.341,
    3.75
   ],
   "val_loss_all": [
    5.126,
    4.04,
    3.951,
    3.619,
    3.878,
    3.906
   ],
   "wall_sec": 640.6,
   "models_unloaded": [
    "qwen3.5:4b-mlx"
   ],
   "adapter": "cph4/fleet/social/train/RUNS/20261117-175135/adapter"
  },
  "EVAL.json": {
   "base": {
    "n": 12,
    "avg": 50.5,
    "pass_rate": 33,
    "avg_logic": 16.2,
    "reject": 0
   },
   "iter0000100": {
    "n": 12,
    "avg": 76.8,
    "pass_rate": 67,
    "avg_logic": 28.3,
    "reject": 0,
    "sample": [
     "老师求素材，剪辑小白从您这里少走弯路，求工作流求素材资源，谢谢",
     "老师大佬！已三连，求后面没有14集了吗？",
     "但是，我没有任何相关的信息或材料，因此无法提供关于B站观众对“自学剪辑教程”的评论。",
     "今天这个老师真的不一样，素材量质平价，帮我直接省了好几年的学费[笑哭][笑哭]"
    ]
   },
   "iter0000200": {
    "n": 12,
    "avg": 72.0,
    "pass_rate": 67,
    "avg_logic": 28.3,
    "reject": 0,
    "sample": [
     "视频素材已全部收集完毕，工作流已全部整理完毕，等待素材，contact:15631156928",
     "有没有想听的老师，如果帮忙的话，希望可以学习一下，谢谢了，老师求老师，谢谢了",
     "有没有up主，想知道这个教程在哪找或者具体什么素材包的[doge_哭哭]",
     "自律的人看剪辑教程，不靠谱的人就看看说他自己可以吧……"
    ]
   },
   "iter0000300": {
    "n": 12,
    "avg": 72.5,
    "pass_rate": 67,
    "avg_logic": 27.9,
    "reject": 1,
    "sample": [
     "求素材包呀，一直想学但是总是剪辑的痛点，求老师能不能给一个素材包和软件安装包，我保证点赞和三连，谢谢老师了",
     "有没有up主呀，求工作流和pr和ve使用教程",
     "up主这个教程有很多，我看了[具体集数]集，感觉还挺可以的，后续求素材",
     "说好的持续更新了，怎么讲完一个合集就没了"
    ]
   },
   "best": "iter0000100",
   "verdict": "建议采用 iter0000100（均分 76.8 vs 基座 50.5，差 +26.3）",
   "prompts": [
    "视频《【全289集】比付费还强10倍的自学剪辑全套教程，全程通俗易懂，别再走弯路了，小》（简介：视频持续更新中，感谢各位观众老爷们的观看！）。你在 B 站这条视频下面留评论。只写评论本身，不要解释，不要加引号。",
    "用 B 站观众的口吻，给《【全289集】比付费还强10倍的自学剪辑全套教程，全程通俗易懂，别再走弯路了，小》（简介：视频持续更新中，感谢各位观众老爷们的观看！）写一句真实评论，不超过 25 字。",
    "刚看完《【全289集】比付费还强10倍的自学剪辑全套教程，全程通俗易懂，别再走弯路了，小》（简介：视频持续更新中，感谢各位观众老爷们的观看！），写一句你最想说的话。就像平时在评论区那样。",
    "视频《Ai原创短片《丧尸清道夫》-重制版，国产“爱死机”！》（简介：本视频由小云雀Seedance2创作生成）。你在 B 站这条视频下面留评论。只写评论本身，不要解释，不要加引号。",
    "用 B 站观众的口吻，给《Ai原创短片《丧尸清道夫》-重制版，国产“爱死机”！》（简介：本视频由小云雀Seedance2创作生成）写一句真实评论，不超过 25 字。",
    "刚看完《Ai原创短片《丧尸清道夫》-重制版，国产“爱死机”！》（简介：本视频由小云雀Seedance2创作生成），写一句你最想说的话。就像平时在评论区那样。"
   ],
   "samples": 2,
   "temp": 0.8,
   "run": "cph4/fleet/social/train/RUNS/20261117-175135"
  },
  "BEST.json": {
   "from_checkpoint": "0000100_adapters.safetensors",
   "path": "best/adapters.safetensors",
   "eval": "EVAL.json"
  }
 },
 "threads": {
  "threads": 1,
  "by_status": {
   "waiting": 1
  }
 },
 "launchd": {
  "com.fluxgroup.modelqueue": {
   "pid": "95349",
   "last_exit": "0"
  },
  "com.fluxgroup.sociallearn": {
   "pid": "62936",
   "last_exit": "0"
  }
 },
 "ts": "2026-11-17T18:30:26"
}
```

## 未决项（0）

