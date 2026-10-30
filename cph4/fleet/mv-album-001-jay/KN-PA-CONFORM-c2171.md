# KN（可爱女人）PACK-A station-4 conform 回执 · C2171（bm-c，2026-10-30 23:31）

银行活：`kn-pa-station4-conform-author-c2169`（bm-c，10-24 起 pending，cmd 一直空）→ 本窗补齐并执行完毕。

## 产物

- 代理剪：`K:\Fluxgroup\FluxGroup\media\mv-album-001-jay\assembly-packA\KN-PACKA-CONFORM-v1-c2171.mp4`
  195.58s / 26,469,607B / 960px 宽 / 24fps / 直切无转场 / 配原曲（首 0.6s 淡入、尾 1.4s 淡出）
- 切点看板：`media\mv-album-001-jay\assembly-packA\KN-PACKA-CUTBOARD-c2171.jpg`（6×5，30 格中点帧）
- 机读回执：`cph4/fleet/mv-album-001-jay/KN-PA-CONFORM-c2171.json`（30 行窗口表 + 每镜 res/fps/frames/bytes）
- 脚本：`cph4/fleet/mv-album-001-jay/kn_pa_conform_c2171.py`（由 xq_packa_conform_c2133.py 同法改写，零 GPU，只读素材）
- 运行日志：`media/mv-album-001-jay/log-kn-conform-c2171.run.txt`

闸：`CONFORM-END ok=1 units=30 cut=195.50s out=195.58s bytes=26469607`。
（cut 195.50 < pack 的 196.35，因为 KN04 授权窗 8.14s 超过该 take 实际长度，已按素材实际长度截断并记 `clamped_units=[KN_A-KN04]`。）

## 看板读片的三个发现（不是 PASS 结论，供导演席判）

1. **KN16/KN17/KN18 连续三镜接近死黑**：中点帧基本只剩星空噪点，主体（纸飞机/屋顶）不可辨。这与 pseudo-guard 把 KN17 判 FLAT（标 push 但实测零推进）互为印证——不是没推，是画面本身就黑到看不见。
2. **KN21 中点帧是一条深红色、密度很高的纹理**（疑似人群/布料），与本曲「纸飞机穿越城市夜色」的主体语言不连贯，属可疑渲染漂移，建议原生帧复核。
3. KN02/KN24 的 DRIFT 与 KN11/KN17/KN21 的 FLAT 已由 C2170 扫描记档，本代理剪未改任何素材。

## 边界

- 这是**评审代理**，不是交付母版：无调色、无字幕、无转场设计、960px。
- 未做任何重烧；上面 1/2 要不要重烧，等导演席或主控裁。