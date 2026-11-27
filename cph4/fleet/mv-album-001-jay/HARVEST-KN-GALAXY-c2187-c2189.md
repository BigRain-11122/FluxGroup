# 收割档 · KN 银河段 C2187 双烧收割（KN17 768P + KN18 480P 迭代 3）

- **批**：C2189（收割轮；上游火 = `kn-galaxy-c2187`，15:55:03 起 → 16:23:32 CHAIN DONE，串行单车道）
- **片**：`media/mv-album-001-jay/clips-local-768/KN_G3-KN17.mp4`（1466s 烧 / 260 帧 / 6638KB）、`media/mv-album-001-jay/clips-verify-480/KN_G3-KN18.mp4`（240s / 260 帧 / 1259KB）
- **帧**：每片 3 帧（1.5s / 5.0s / 9.0s）原生分辨率 → `media/mv-album-001-jay/qc-frames-c2189/`（KN17 1344×768，KN18 672×384，另 1:1 带区裁片 `KN17_768p_t9.0_bandcrop.png`）
- **机筛**：watcher 自动档 `HARVEST-KN-GALAXY-c2187-AUTO.md` —— KN17 `p99_max=40 → STARFIELD-LIKE`；KN18 `p99_max=117 → BRIGHT-BAND`；双侧 `kn_framing_drift_gate` rc=0（scanned=1 flat=0 undecided=0 regress_diff=0，零漂移）
- **本轮自测亮度**（GaussianBlur σ=12 后的天空亮度分位）：KN17 p99 = 43.0 / 44.0 / 47.0（阈值 82 以下，且低于 C2186 已知好件 63/66/76）；KN18 p99 = 89.0 / 110.0 / 114.0（阈值以上，且高于 C2186 已知坏件 88/95/102）

## 判读

| 片 | 判 | 证据 |
|---|---|---|
| KN_G3-KN17（768P 正烧） | **半过（亮度面过 / 带边几何不过）** | 亮度面全过：天空均匀暗、点状为分离圆点、暖金色、地平线为无光黑边、无琥珀云团（p99 43-47 远低于阈值）；**几何面不过**：带区在 1:1 裁片下读作一排竖条涂抹/帘状碎片，边缘硬而撕裂，不符「soft open edges」 |
| KN_G3-KN18（480P 迭代 3） | **不过** | 带区整片长成明亮琥珀云团（猎户式星云），与天空亮度严重分离；正语措辞（positive-only）把「band」这个词喂成了星云吸引子，p99 89-114 反比迭代 2 更亮 |

## 病根判读（两条迭代合看）

C2186（缺陷写进正向文本）与 C2187 迭代 3（全正语、不否定）**双双塌进星云像**——共同吸引子不是措辞极性，而是 **「band of the galaxy」这个名词本身**：模型对这个名词的先验就是「拍摄级星云图」。KN17 同 prompt 产出的竖条碎片，是同一条先验在 4-step turbo + int8 下的退化解。

## 正法（已当轮落地为迭代 4）

**取消 band 结构**：只写「均匀暗天空 + 分离圆点 + 一层等亮度、平坦、几乎看不出的暖尘薄雾，边缘柔软开放」，星云/银河/带 三个名词全部不出现；**带区视觉统一由装配站调色层加确定性薄雾**（可控、零星云风险）。

- 迭代 4 manifest：`cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-kn-galaxy480-c2189.json`（KN_G4-KN17 / KN_G4-KN18，两镜同薄雾律）
- 火：`cph4/fleet/mv-album-001-jay/c2189_kn_chain_launch.py`（pythonw 脱钩，16:24:58 起烧，480P 双镜串行，先探后产）
- 交接：`MiniGame/.codely-cli/engine-tick/wave-harvest-pending.json`（C2189 档，含完整收割四步）

## 下一步（未做，如实记）

1. 迭代 4 480P 双镜眼检 + p99 机筛（≈8 分钟烧）；
2. 双绿 → 768P 正烧（KN_G5 ids）→ **才**做 `KN_A-KN17` / `KN_A-KN18` 槽位映射 + `kn_full_assembly_c2183.py` 重跑出片 v2；
3. 导演席拉片签章 → 呈 CEO。

> 本轮未动 `clips-local-768/KN_A-KN17.mp4`（现盘件为 09:53 旧版）——正烧未过闸，装配池不放不合格件。