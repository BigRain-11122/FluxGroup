# 角色一致性契约（CAST-LOCK v1）

> 适用：龙卷风 mv0002（以及后续所有 MV）。写这条的原因：本机没有 IPAdapter / InstantID /
> PhotoMaker 权重，纯提示词生成时脸会逐镜漂移——必须把「同一个人」做成可执行、可核验的约束，
> 而不是靠肉眼看几张图说"挺像的"。

## 一、锚（唯一权威外观）

| 角色 | 锚图 | seed | 锁定外观串 |
|---|---|---|---|
| 女主 HER | `cast/HER/ref.png` | 92897 | A young woman with long dark hair and fair skin, wearing a gray cardigan over a white shirt |
| 男主 HIM | `cast/HIM/ref.png` | 44923 | A young Asian man with short dark hair and subtle facial stubble wears a white t-shirt under an open denim jacket |

- 锚图是**唯一**判定依据；任何镜头与它不符即为该镜作废，不许"下一镜再拉回来"。
- 锁定串由 VLM 读锚图生成后**剔除场景词**（window/rain/street/standing/light…）——
  否则每镜都会被钉在同一个环境里。
- 改锚必须走 `cast_lock.py add` 重锁，并**重验全片**。

## 二、出镜强制路径（实测结论）

| 方式 | 身份保持 | 场景/姿态变化 |
|---|---|---|
| 纯文字 text2img | **0/2 SAME**（女主） | 自由 |
| 从锚图 img2img（denoise 0.45–0.75） | **5/5 SAME** | **几乎不变**（构图被锚图钉住） |

所以现行纪律：

1. **人物镜头一律走 img2img**：`cast_lock.py shot <film> <ROLE> --scene "..." --denoise 0.45~0.6`；
2. 远/全景、背影、局部（手、肩、雨伞遮挡）等**不需要露脸**的镜头，才允许 text2img，
   以免把整片拍成同一张脸的特写；
3. 中近景要换姿态时必须抬 denoise，但**每次抬完必须立刻 verify**，不过就是作废重出。

## 三、验收闸（机械，不靠肉眼）

```
python Tools/fleet/cast_lock.py verify <film> <ROLE> <shot1.png> [shot2.png ...]
```

- 判据：VLM 两图比对，输出 SAME / DIFFERENT；任一 DIFFERENT 即 `FAIL`。
- 回执落 `<film>/cast/<ROLE>-verify-<date>.json`，含每镜结论与理由。
- 先跑**正控**（锚图自比必须 SAME）再验片，防"模型永远说 SAME"的假绿。

## 四、当前技术边界（须知）

img2img 保住了脸，但也保住了构图——扫了 0.45 / 0.55 / 0.65 / 0.75 四档，
女主始终是同一个机位的中近景，只换了背景。要拍出有景别的片子，只有两条路：

1. **装身份模型**（PhotoMaker / IPAdapter FaceID / InstantID）——`hf-mirror` 探测可达（302），
   但大件下载在队内网络常断，需要单独安排；
2. **训角色 LoRA**（用 img2img 批量出 20–30 张多角度底图再训练）——不依赖下载，但吃 GPU 时间。

在上述任一落地前，**一致性优先于景别丰富度**：先保证是同一个人的同框镜头，不为了好看把脸换掉。