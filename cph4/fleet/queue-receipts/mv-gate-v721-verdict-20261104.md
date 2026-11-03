# MV 交付闸判决 · v721 60fps 1080p（2026-11-04 03:2x·R6 事件班实跑）

- 片：`cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/full_mv_v721_60fps_1080p.mp4`
- 闸：`Tools/mv_delivery_gate.py`（cv2 5.0.0·bm-a 实跑）· 回执 `cph4/fleet/queue-receipts/mv-gate-v721-2026-11-04.json`
- 规模：14064 帧 / 60.0 fps / 80 个镜头
- **VERDICT: FAIL**

## 判负项（逐条）

1. **D1 重复镜**：D1 shot reused on screen: 6 pair(s), first 45.20s vs 223.93s
2. **D2 近静止镜头**：24 处（D2 near-static shots: 24 (first 14.57-17.48s mean_mad=0.24)）
3. **D3 死停**：D3 dead holds >=0.25s: 1 of 2 freeze runs (worst run=13 frames at 234.18s)
4. **冻结（stability.freezes）**：[{'t': 114.483, 'frame': 6869, 'run': 5}, {'t': 234.183, 'frame': 14051, 'run': 13}]
5. **未申报复现镜**：6 处（`reprise_unlisted`），已申报卡窗=38.79-40.21s / 219.71-223.88s

## 判读（真缺陷 vs 未申报卡窗）

- **D1 属真缺陷**：首对 45.20s vs 223.93s，两处都不在已申报的两个卡窗里，属于镜面复用未申报。
- **D2 需导演席复核**：近静止 24 处按 `mean_mad` 阈值判出，MV 语法里「定格/静场」可以是设计；但 24 处数量级偏大，建议逐条看前 5 条（首处 14.57-17.48s）。
- **D3/冻结属真缺陷**：234.18s 处 13 帧死停（0.22s）在 60fps 下肉眼可见卡住。
- **不构成 FAIL 的项**：seams 空、flicker 空 = 接缝与闪烁已清零。

## 下一步（导演席）

重复镜只能用重烧或换素材解决，**禁用推近裁切冒充**（CEO 2026-10-24 红线）。
冻结 13 帧优先修（单点、成本最低），随后处理 D1 的 6 对重复。
