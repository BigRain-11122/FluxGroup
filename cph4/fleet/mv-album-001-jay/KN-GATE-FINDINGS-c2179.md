# KN 出生站 C2179：三段"推镜不推"被闸放过（UNDECIDED 洗白 FLAT）＋ 重烧 480P 已装弹

## 一句话

C2178 修的是"镜头句里的实物名词被渲染成布景"。这一轮查出**同一句的另一个后果**：
"eases in from almost still on a slow floor dolly" 这半句，在 5 个用的单元里有 **3 个渲染成完全静止**
（KN03 / KN11 / KN21 实测 1.00x，31 个采样点全 1.000），而**运镜闸把它们报成了 UNDECIDED「需人工过眼」**——
闸把最干净的静态证据推给了人眼，这正是闸本该免掉的那一步。

## 证据

| 单元 | 判决 | 实测 | 作者层镜头句 |
|---|---|---|---|
| KN03 | FLAT（原 UNDECIDED） | 1.00x @100% 采样 | slow **floor dolly** push |
| KN11 | FLAT | 1.00x | 同上 |
| KN21 | FLAT（原 UNDECIDED） | 1.00x @100% 采样 | 同上 |
| KN08 | UNDECIDED | 1.09x | 同上（贴压 1.10 门，留人眼） |
| KN17 | PASS | 1.16x | 同上 |
| KN15 | PASS（运镜合规） | 1.00x | 但整条布景化（C2178） |

被删掉的旧词已在 C2178 改成 `eases in from almost still on a slow level move`（纯运动、无器材名词），
但**在飞波次的 manifest 是启动时一次性读进内存的**，盘上这 21 条全按旧句烧的——所以"改了词"没有"改到落片"。

## 本轮做了什么

1. **闸的病灶修掉（`kn_framing_drift_gate.py`）**：新增 `still_frac`——
   若 ≥90% 采样点的中值缩放 ≤1.005 且最大值 ≤1.03，判 **FLAT**，不再让一次相关峰噪声把整条片洗成 UNDECIDED。
   理由写进 docstring：整条片每个采样点都读 1.000，就是"没有任何运动"的测量结果；峰噪声是静帧上的相关噪声，
   不是相机运动的证据。KN08（1.09x）不受影响，仍在 UNDECIDED 走人眼。
2. **全量复扫 23 条落片**（含扫描期间新落的 KN22a）：flat=3 / undecided=1 / PASS 其余；与上一版对照有 2 处判决翻面
   （KN03、KN21：UNDECIDED→FLAT），无回退。
3. **重烧清单装弹（`kn_reburn_manifest_c2179.py` → `local-i2v/run-bmc-kn-reburn480-c2179.json`）**：
   KN03 / KN11 / KN21（推镜落空）+ KN15（布景化）四单，**提示词从作者层现文件重新派生**，
   所以重烧用的是 C2178 修好的纯运动镜头句；出厂前过 hygiene 闸 4/4 PASS（无器材/人员名词）。
   480P 验证切片（672×384 int4·`clips-verify-480`），不是正片。
4. **装弹链（`kn_waveend_chain_c2179.py`，已后台武装）**：盯 768P 波次 PID 29056，波一退出、沉淀 25s 后
   自动起 bmcverify 车道烧这 4 单，日志 `media/mv-album-001-jay/logs/kn-reburn480-c2179.log`。
   为什么必须等：第二个 runner 启动时会 `/free` 卸模型，会把在飞单元脚下的 int8 模型踢掉，16G 卡也装不下两条流水线。

## 判例

**镜头句里的器材名词会以两种方式失败，闸要分两头管**：
一是被画成布景（C2178 tripod→三脚架+舷窗），二是被画成"架上器材不动"（本轮 floor dolly→整片零运动）。
同一个词两种坏法，而"UNSTABLE/UNDECIDED"这种兜底判决会把第二种悄悄交回人眼——**兜底判决必须带"样本占比"证据**，
否则它就成了缺陷的洗白通道。

## 待办

- (红) 4 单 480P 重烧：波次退出后由装弹链自动起烧（无需人工），出片后逐单过 framing＋hygiene＋眼睛站；
      过了才排 768P。
- (黄) KN22b/KN23/KN24/KN25/KN29/KN30 仍在飞（旧句），落片后照本轮口径过闸。
- (黄) KN17 10.5s 无锚空镜＝分镜预算问题（承 C2178），不在这张闸的射程内。
- (黄) KN08 1.09x 贴门 → 人眼判：真推（进装配）还是静止（进重烧队列）。

## 产物

- `cph4/fleet/mv-album-001-jay/kn_framing_drift_gate.py`（still_frac 规则）
- `cph4/fleet/mv-album-001-jay/kn_reburn_manifest_c2179.py` + `local-i2v/run-bmc-kn-reburn480-c2179.json`
- `cph4/fleet/mv-album-001-jay/kn_waveend_chain_c2179.py`（后台装弹链）
- `cph4/fleet/mv-album-001-jay/_c2179_camera_clause_probe.py`（镜头句 × 实测对照探针）
- `media/mv-album-001-jay/evidence-c2179/{framing-all-c2179,framing-all-c2179b,pseudotext-kn21}.json`（media 不入 git）