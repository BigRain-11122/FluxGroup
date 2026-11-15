# 锁机位措辞实证 + 漂移闸标定（2026-11-15 · bm-c）

## 一、同 KF、同 seed、同 3.0s 档，只改一句措辞 → 结果完全不同

对照对象都是 `kf/XQ01.png`，长度同为 73 帧（3.0s），seed 相同。

| 版本 | 头部措辞 | 末帧 | 像素闸（mean / max_cell） | 人脸闸（shift / IoU） |
|---|---|---|---|---|
| 试点档 `i2v-xq3/XQ38_01.mp4` | `camera completely locked off with no zoom and no push-in; the framing stays exactly as the first frame.`（+ 句中再补一次 `camera locked off…`） | 与首帧几乎一致 | 20.20 / 40.35 → HOLD | 0.012 / 0.75 → HOLD |
| 整批档 `i2v-xq3-batch/XQ38_01.mp4` | `camera completely locked off, no zoom and no push-in.`（只有这一句） | **明显推成近景** | 48.60 / 86.68 → DRIFT | 0.055 / 0.17 → DRIFT-CAMERA |

人眼复核（首末帧并排）：试点档机位纹丝不动；整批档从中景推成半身/近景，颗粒同步变细——
这正是 11-14 判定的 A 类「相机漂移」。**所以 A 类的正解不只是「缩短时长」，而是「措辞写全」**：
时长 3 秒只是把漂移幅度压小，真正压住靠的是那句 `the framing stays exactly as the first frame`。

## 二、当窗处置（不做无用烧）

1. 批次跑到 **10/38** 时停掉 runner（不杀 ComfyUI），把 manifest 38 单的头部全部换成强锁句
   （`Tools/smoke/patch_i2v_lockphrase.py`，原文件备份 `i2v-xq3-manifest.json.bak-20261115-145154`，
   写后复验 38/38 命中）。
2. 重启用同一 runner（SKIP 判据按目标文件存在，已出的 10 镜不重烧），续烧剩余 28 镜。
   代价对比：换词续烧 ≈ 28×226s；跑完再全批重烧 ≈ 38×226s，省掉约 40 分钟。
3. 已出的 10 镜里 8 镜 DRIFT（弱措辞烧的），挂 `Tools/smoke/chain_reburn_drift.py`：
   等整批跑完 → 跑量子闸 → 把 DRIFT 镜移进 `_archive-drift-<ts>/`（归档不删，既让 SKIP 失效又留证据）
   → 用强锁句 manifest 重烧这几镜 → 复跑闸 → 出 `QC-DRIFT-REBURN-*.json`。

## 三、像素闸标定（这次发现单阈值会误报）

同一批 10 镜实测：

| 镜 | mean_abs | max_cell | 人眼复核 | 单阈值(55) 判定 |
|---|---|---|---|---|
| XQ38_09 | 26.24 | 71.94 | 首末帧基本一致（挥手动作，夜空星点） | 误报 DRIFT |

真推镜的镜 mean_abs 都在 45~65；锁住的镜在 20~26。所以改成**双阈值**：
`max_cell > 55 且 mean_abs > 35` 才判 DRIFT；只过一条判 `SOFT`（必须人眼复核）。
改后同一批：8 DRIFT / 1 SOFT / 1 HOLD，与目视一致。

`qc_i2v_face.py` 的 yaw 通道在这批上噪声偏大（小脸/侧脸时常给出 dnx≈1.0），
只能当「值得看一眼」的提示，不能直接进重烧单——这与 `DATASET-AUDIT` 里那条
「机械报警必须人工复核」同一条纪律。

## 四、给下个会话的两句话

1. i2v 提示词头三句是硬约束，不是修辞：`camera completely locked off with no zoom and no push-in` +
   `the framing stays exactly as the first frame`；缺后半句就会推镜。
2. 判 DRIFT 前先看 `max_cell` 与 `mean_abs` 两条，再看一眼首末帧对照板；只信一条会把 36 小时烧成废片。
