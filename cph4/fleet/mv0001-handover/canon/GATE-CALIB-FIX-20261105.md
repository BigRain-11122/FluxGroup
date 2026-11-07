# 交付闸标定修正 · 2026-11-05（承 PATROL R45-1 判定）

## 改了什么

`Tools/mv_delivery_gate.py`（两处，均为标定缺陷，非放宽标准）

1. **D2 近静止 · 帧率归一**
   - 原：`avg < STILL_MAD and avg_s < SHOT_SHIFT_MIN`
   - 现：`(avg * fps/24) < STILL_MAD and (avg_s * fps/24) < SHOT_SHIFT_MIN`
   - 缘由：`STILL_MAD=0.45` / `SHOT_SHIFT_MIN=0.35` 是**逐帧**量，按 24fps 标定。
     逐帧 MAD 与帧间隔成正比，60fps 母版被判定的严格度是 24fps 的 ~2.5 倍。
     实证：同一窗口 14.57-17.48s，24fps 判 mad=0.6 非静止，60fps 判 mad=0.24 静止。
   - 影响面：`fps/24 == 1.0` 时数值完全不变 → **24fps 历史判决一律不改**。

2. **D3 死停 · 门限单位**
   - 原：`f["run"] >= 6`（6 帧）
   - 现：`f["run"] >= DEAD_HOLD_S * fps`（0.25s，新增常量）
   - 缘由：报错文案一直写 `>=0.25s`，代码却比帧数；60fps 下 6 帧=0.1s，
     比自述标准严 2.5 倍，还出现过「13 帧=0.217s 判负」这种自相矛盾。
   - 影响面：24fps 下 0.25*24=6 → **与原门限等价，历史判决不改**。

## 正反样例验证（闸工程铁律：新判据须双组实证）

样例取自 V7.21 母版 20-26s（60fps），存 `.codely-cli/tmp/gate-calib/`。

| 样例 | 构造 | 期望 | 实测 |
|---|---|---|---|
| `POS_motion_6s.mp4` | 正常运动段 | PASS | `static_shots=0 freezes=0` → **PASS** |
| `NEG_freeze_0p6s.mp4` | 插入 0.6s 冻结（35 帧） | FAIL D3 | `freezes=1` → `FAIL D3 dead holds ... worst run=35 frames at 3.03s` |

结论：判据不失效——该拦的仍拦得住，同时不再因帧率误杀。

## 连带修（卡面参数，防每日假红）

- `cph4/fleet/ri/content/lines/mv.json` gate 段：补 `--whitelist MV0001-REPRISE-WHITELIST.json` + 卡窗 198.92:200.71
- `cph4/fleet/lanes/bm-a.json` 同名卡 cmd：同上
- 缘由：原 cmd 缺白名单 → 6 对设计复现永远被判 D1；卡窗缺一个 → 该段永远算未申报。
  这是 11-04/11-05 每天 3 次 ×~370s 全白跑的直接原因。

## 未做 / 边界

- 未改 `mv_stability_gate.py`（freeze 检测本身仍在原阈值 FREEZE_MAD/RUN 上跑）。
- D2 修好后若仍报近静止，那就是**真的设计静镜或真停**，须导演席按镜头表逐条判，闸不代判创作。

---
执行 = 主控（本窗）· 2026-11-05