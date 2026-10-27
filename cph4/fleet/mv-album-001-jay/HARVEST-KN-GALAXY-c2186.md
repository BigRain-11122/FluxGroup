# 收割档 · KN 银河段 480P 探针 C2186 · KN17 过 / KN18 退回

- **波**：`kn-galaxy480-c2186`（672×384 int4 · lane bmcverify · 15:44:43 起 · 15:52:59 ALBUM LANE DONE ok=2 fail=0）
- **片**：`media/mv-album-001-jay/clips-verify-480/KN_G2-KN17.mp4`（255.2s 烧制 / 260 帧 / 1125KB）、`KN_G2-KN18.mp4`（240.2s / 260 帧 / 1388KB）
- **审**：每片抽 3 帧（1.5s / 5.0s / 9.0s）人眼 → `media/mv-album-001-jay/qc-frames-c2186/`
- **机检**：`kn_framing_drift_gate --scan-dir clips-verify-480 --glob KN_G2-KN1*.mp4 --batch C2186` → `KN_G2-KN17 zoom=1.00x@2.5 NOT-JUDGED (intent is not a zoom)` · `FRAMING-END scanned=1 flat=0 undecided=0 regress_diff=0`（KN18 出片晚于首跑，未入本轮扫描）

## 逐片判

| 片 | 判 | 证据（抽帧实读） |
|---|---|---|
| KN_G2-KN17 | **过** | 三帧一致：暗调尘埃带低对比、云脊未点亮、暖金点=离散可数圆点，无缠绕环／枝状／近虫形；C2183 判负的「金色线状环状缠绕」已消除 |
| KN_G2-KN18 | **不过** | 三帧一致：尘埃带仍被 i2v 放大成**明亮橙金发光星云带**（远亮于其关键帧），即 C2183 判负的「金色条带」原症 |

## 根因（KN18）

关键帧 `frames/KN_KN18.png` 实读完全正确（淡色低对比尘埃带 + 针尖星点），错在位移动画段：**prompt 里把缺陷写进了正向文本**（"no glowing nebula, no bright orange clouds"）——点名缺陷本身即条件化模型朝该缺陷渲染；再加 4-step turbo 对暖色高光放大，带部整体提亮成星云。

## 处置（已发 C2187 链）

1. **KN17 过闸 → 768P 生产重烧**：manifest `run-bmc-kn-galaxy-prod-c2187.json`，lane bmc int8 1344×768，id `KN_G3-KN17`，prompt 原样沿用（过闸那一版不改）。
2. **KN18 探针第三轮（480P）**：manifest `run-bmc-kn-galaxy480-c2187.json`，prompt 改为**纯正向无否定无颜色词**：band = 同一批针尖点略密、亮度几乎等同周边天空、边缘柔软开放、每粒可分辨。
3. 两段顺序执行（同卡不并发）= `cph4/fleet/mv-album-001-jay/c2187_kn_chain_launch.py`（pythonw 脱离式，log=`media/mv-album-001-jay/logs/kn-galaxy-c2187.log`）。
4. KN18 过闸后 → 768P 重烧 → 一条命令重跑 `kn_full_assembly_c2183.py` → 整片 v2 → 导演席复签。
5. 装配命名对接：768P 生产件落 `clips-local-768/KN_G3-KN17.mp4`，装配站按 clips-local-768 读片，收割轮需把过闸件对齐装配索引用名（KN_A-KN17 位）后再跑装配。

## 计数

- 本轮探针：2 片烧制 495s，判定 1 过 1 退（50%）。C2185 前轮 0/2，C2186 本轮 1/2——单调收敛。