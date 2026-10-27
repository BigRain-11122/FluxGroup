# P2 三曲词锚批回执 — @bm-b r1007（承 orders 2026-10-18 13:5x「利用好机队的本地算力！」令②派单）

**dispatch**: 13:5x 本地算力优先令②【@bm-b】P2 三曲 whisper 词锚批（龙卷风/斗牛/黑色幽默·word_timestamps·锚点入 anchors/ 同构·MV 面 480P animatic 备援位待命）
**回执窗**: 2 轮（本件=第 1 轮即窗回执）

## 1. 查重定位（零重跑）
- 三曲 `-words.json` word_timestamps 面已全部在册：commit 1bd21af（bm-b r992·POOL-0018 批·whisperX word-level 全 10 曲）——本派单的 words 面按反重复铁律不重烧。
- 音源披露：POOL-0018 批用 `audio/` 320k mp3 同源件（media/MUSIC/jay 无损源本机不存在）——词级对齐用途下与无损等效。

## 2. 本轮新增实物（校准面=MV 歌词层消费面）
| 曲 | 官方词面 | 校准面 | exact/approx/none |
|---|---|---|---|
| 斗牛 | `lyrics/斗牛.txt` 91 行 | `anchors/斗牛-calibrated.{json,txt}` | 66 / 19 / 6 |
| 黑色幽默 | `lyrics/黑色幽默.txt` 42 行 | `anchors/黑色幽默-calibrated.{json,txt}` | 36 / 6 / 0 |
| 龙卷风 | （v1 批已有） | （v1 批已校准） | — |

→ **P2 三曲校准面自此齐备**（v1 批六曲之外的两缺口补齐）。

## 3. 词面来源与交叉核验
- 斗牛：lyrics.net.cn/lyrics/24 全文 × TRACK05 锚句件（仓内已核原文）交叉一致（「有种不要走」定谳）。
- 黑色幽默：lyrics.net.cn/lyrics/73487 × mulanci.org sl114776 双源交叉；「心理→心里」按二源+听感判据修正为官方「心里」。
- 校准算法=仓内 lyric_calibration.py 现行 DP（whisper 行段 × 官方行单调对齐），确定性可复跑。

## 4. 诚实披露（斗牛曲首喊话段）
- 斗牛前奏喊话两轮（词面行 1-16，音频 ~15-44s）= whisper 掩蔽洞（crowd-noise 遮蔽·听写零覆盖；44.0-46.5s 仅有「有话就接受/马上三分钟」尾部误听碎片）→ 校准面 none=6 + approx=10，窗口压在 10.82-46.50。
- 词层消费建议：喊话段行按器乐段手定或入 animatic 时人工对齐；说唱/桥/副歌主体（行 17+，46.5-276s）exact 面扎实。
- 黑色幽默 42 行全带时窗零 none；行 26「败给你的黑色幽默」窗口 125.20-163.88 [approx] = 器乐间奏段（正确行为）。

## 5. 工具面
- `lyric_calibration.py` 新增 argv 过滤器：`python lyric_calibration.py 斗牛 黑色幽默` 只跑指名曲（单曲幂等重跑不动他曲产物）；裸跑=全集，行为不变。

## 6. 附带收口
- LEDGER union heal：本机记忆门首跑 2 回执行（BIGMONEY 记忆治理班 10:30 ×2）入账，bm-a 10:27/10:21-10:30 两行保位（陈旧基座写穿修复·行级 union）。

— via bm-b r1007（值守轮·2026-10-18 14:2x）
