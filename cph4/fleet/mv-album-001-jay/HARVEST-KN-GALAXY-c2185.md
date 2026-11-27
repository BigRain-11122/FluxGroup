# HARVEST — KN galaxy segment 480P probe (C2185 → C2186)

批次：C2185 收割（本轮）/ C2186 续烧（已点火，下轮收割）
日期：2026-10-24 15:44
导演席条目：DIRECTOR-REVIEW-KN-FULL-v1-c2183 item 1（galaxy segment FAIL）

## 1. 判据与证据

| 单元 | 机器门 | 人眼三帧 | 判 |
|---|---|---|---|
| KN17（远景 establishment） | framing gate 1.01x on push → **FLAT** | 三帧全为离散圆点 + 暗淡河带，无绞缠金丝（C2183 病灶消失）；**尾帧长出被照亮的橙色云堤**（提示词要求 dark rim） | **内容项过 / 尾帧返工** |
| KN18（近景） | framing gate intent=mobile → NOT-JUDGED（横移不等于变焦，规则如此） | 河带被放大成**连续发亮的橙色星云带**，亮度/饱和远高于其关键帧的细密暗尘；"点与点之间干净的黑"不成立 | **未过（部分修复）** |

证据：
- clips：`media/mv-album-001-jay/clips-verify-480/KN_G1-KN17.mp4`（1.2MB, 255s 烧）、`KN_G1-KN18.mp4`（1.1MB, 241s 烧）
- 三帧抽检：`media/mv-album-001-jay/qc-boards/verify480-c2185/KN1{7,8}_t{1.62,5.42,9.21}.png`
- framing gate 判读：`media/mv-album-001-jay/logs/kn-galaxy480-c2185-framing.json`
- 烧录日志：`media/mv-album-001-jay/logs/kn-galaxy480-c2185.log`（ok=2 fail=0）

## 2. 出生地诊断（保留给下轮，不改动结论）

C2185 已证明关键帧干净（`frames/KN_KN17.png`/`KN_KN18.png` 均为离散点星空），缺陷出生在**运动提示词**。本轮三帧补一条更精确的出生位置：**亮度/对比度语句缺位**——只写了"点小、圆、分明"，没写"河带是暗淡低对比的尘、点与点之间干净的黑"，于是 i2v 把关键帧的细尘当发光星云去放大。KN18 尤其明显：关键帧细密暗尘 → 成片连续橙云。

## 3. 本轮已点火（C2186）

- 提示词 v3.4：KN17 增 `band of the galaxy reads as faint dim dust, low contrast / cloud deck ... unlit dark rim, no lit clouds`；KN18 增 `faint dust band stays dim and low contrast, no glowing nebula, no bright orange clouds`
- 机读件：`cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-kn-galaxy480-c2186.json`（hygiene gate `fail=0 warn=0`）
- 发射器：`cph4/fleet/mv-album-001-jay/c2186_kn_galaxy_probe_launch.py`（hidden，无控制台）
- 日志：`media/mv-album-001-jay/logs/kn-galaxy480-c2186.log`（15:44:43 已 SUBMITTED KN17）

## 4. 工具修复（闸不能只在 768P 上活着）

`kn_framing_drift_gate.py` 只支持短边≥512 的方框裁切，480P 验证道（672×384）喂进去必炸
`operands could not be broadcast (64,512) vs (512,512)`——即**低清验证道永远跑不了构图闸**，等于验证道只能看内容项、看不到运镜项。本轮加 `fit_square()`（中心取最大正方形 + 双线性重采样到 SQ），768P 走原路径零回归，480P 现在可判：

```
KN_G1-KN17.mp4  intent=push    zoom=1.01x@8.0  FLAT  declared push measured 1.01x on 90% of samples
KN_G1-KN18.mp4  intent=mobile  zoom=1.20x@8.5  NOT-JUDGED intent is not a zoom
```

KN17 的 FLAT 是 v3.3 那一版的读法（推镜没渲染出来）；C2186 的 768P 候选批必须重跑本闸复核，不继承此结论。

## 5. 未做（显式移交）

- 768P 重烧 KN17/KN18：**未点火**，等 C2186 人眼 + framing 双过
- `kn_full_assembly_c2183.py` 重跑成片 v2：等两单元齐
- 导演席复看 v2：等装配