# KN A 批 768P 伪字幕条闸（C2170 判读件）

时间：2026-10-24 06:4x（Get-Date 实测）
批次：C2170　线：MV-PACK-A / 可爱女人（KN）
性质：缺陷出生地拦截（harvest 站之前新增一道 clip 落地即检的机械闸）

## 一、发现

C2169 预挂的 harvest 闸未运行前，本轮对已落地 3 条 768P（KN01 06:03 / KN02 06:16 / KN03 06:4x）
做批前抽检，发现 **KN02 画面底部中央有一条稳定存在、字幕形态的白色伪文字**（黑描边、
横贯下三分之一的窄条），从第 21 帧（≈0.9s）开始出现并贯穿到 175 帧末尾。

判读证据：
- 原生帧（无缩放，1344×768）：`media/mv-album-001-jay/evidence-c2170/KN02-f10.png`、`KN02-f36.png`、`KN02-f66.png`
- 条带对照（第 60 帧 vs 第 160 帧，3 倍放大）：`evidence-c2170/band-kn02-compare.png`
- 逐帧亮像素计数：0..20 帧 = 0，21 帧起 1000-2000 px，尾部随背景变亮递减但文字仍在

**出生地 = 生成器，不是关键帧**：源关键帧 `frames/KN_KN02.png` 底部干净（已原生复核），
故伪文字是 i2v 模型先验，属"字幕形态吸引子"一类。

对照：KN01（手部特写、俯角）与 KN03（近景、扶住纸飞机）**全帧干净**。KN02 的区别是
**中景全身正面 + 画面下三分之一大面积空平**——构图给出"可加字幕"的空低区。

## 二、为什么此前没拦住

C2167/C2168 的 480P 验证只烧了 **KN04 / KN21 / KN22b** 三条代表系（批前抽检律）。
三条都不是全身正面中景，所以这一类没进样。**抽样覆盖的不是缺陷类，是"省时间的单位"**。
另：harvest 闸只查 ffprobe / framemd5 复读 / 抽帧拼板，没有文字类检查。

## 三、本轮落地（机械闸，不靠人眼）

新增 `cph4/fleet/mv-album-001-jay/kn_pseudotext_probe.py`：
- 只扫字幕带（横向 30%-70%，纵向 84.5%-97.5%），不做全帧 OCR
- 判据 = 近白（>215）且 **局部对比度高**（v − 5×5 均值 ≥ 60，即黑描边白字），
  排除白球鞋/亮地砖一类"白但没有描边"的误报
- 两条同时成立才判 SUSPECT：**承载帧占比 ≥ 0.5** 且这些像素**集中在 ≤32% 行高的窄条**
- 条带可随推镜纵向漂移（KN02 实测 40→120 帧上移 14 行），故不要求位置固定

标定实测：
| 样本 | 数量 | SUSPECT |
|---|---|---|
| KN01 / KN03（768 干净） | 2 | 0 |
| KN02（768 已知坏） | 1 | 1 |
| C2168 480P 验证三条（KN04/KN21/KN22b） | 3 | 0 |
| 星晴 XQ 全量已过审 clip（基线） | 48 | 0 |

XQ31 承载率 0.56 但 narrow=0.10 被窄条条件正确排除、XQ05 0.28 同理——这两条是
误报压力测试位，说明窄条条件是真闸不是摆设。

接线：
1. `kn_pa768_harvest_c2169.py` 每单元加 `pseudo_text` 检查，SUSPECT 即 FAIL（该单元不得进装配）
2. `cph4/fleet/idle-guard-kit/kn_pseudo_guard_c2170.py` = 零 GPU 扫描器，写
   `evidence-c2170/pseudotext-guard.json`（含 landed/suspect/halt_recommended），已入银行队列
   `kn-pseudo-guard-c2170`
3. 顺带修银行潜在崩溃：`bmc_idleguard.py` 原会对 **cmd 为空的 pending 作业**照领，
   `Popen([])` 直接抛异常 = 守卫生死 + 作业永久 stuck claimed。现在空 cmd 作业跳过并记日志
   （本批就有一个空 cmd 的 conform 作业，已同时加 require 闸=必须 harvest verdict 存在）

## 四、波次处置裁决：不喊停

理由（写死备查）：
- 缺陷率目前 n=3 样本（1/3），KN01/KN03 干净；按 n=3 叫停 6 小时产线属过度反应
- 单条报废成本 = 13 分钟；叫停空转成本 = 修法验证期 GPU 全空（CEO 无闲置硬线会直接判负）
- 闸已机械：任何 SUSPECT 单元**不可能**被签进装配，重烧只烧被标记的单元
- guard 里编码了叫停建议线：landed≥5 且 suspect≥2（≥40%），或 landed≥9 且 suspect≥3（≥33%）
  → `halt_recommended=true`，由下一轮 tick 读该文件决定停波（guard 自己从不杀进程）

## 五、prompt 侧为什么不能直接加"无字幕"锚

`prompt_lexicon.py` 的 lint 三名单（正典律）**禁否定词**（`_NEG` 正则），且
`CONCEPT_BANNED` 明列 `watermark / typography / logo / letters` —— 写进条件等于注入该概念。
所以"no subtitles / no watermark"一类写法既违 lint 也会强化概念，不能作为修法。

可行的修法方向（下一轮 480P 实验，lint 合法、正向表述）：
- 收窄构图，让下三分之一由主体/衣料占满（去掉"可加字幕的空低区"），即换 framing 而非加否定
- 换种子重烧同构图，先判定是构图先验还是种子单发
- 若换 framing 有效，则对 30 单元中所有"全身正面中景"类统一改 framing（EN 正向描述）

## 六、待办（下一轮指针）

1. KN02 768P 判 CHECK → 出重烧单（同帧同种子族 + framing 变体，先 480P 两轮再 768P）
2. 480P 抽检样集合修订：**必须含 1 条全身正面中景**（本次漏样的直接原因）
3. 波次收尾时读 `pseudotext-guard.json`：`halt_recommended=true` → 停波改 prompt 再续
4. 装配前对全 30 单元跑一次 probe（harvest 已内建），凡 SUSPECT 一律不进 SHOTLIST 装配

## 七、产出清单

- `cph4/fleet/mv-album-001-jay/kn_pseudotext_probe.py`（新，探针）
- `cph4/fleet/idle-guard-kit/kn_pseudo_guard_c2170.py`（新，零 GPU 扫描器）
- `cph4/fleet/idle-guard-kit/c2170_bank_surgery.py`（新，银行手术，幂等）
- `cph4/fleet/idle-guard-kit/bmc_idleguard.py`（改：空 cmd 作业跳过）
- `cph4/fleet/mv-album-001-jay/kn_pa768_harvest_c2169.py`（改：每单元加伪文字闸）
- `cph4/fleet/work-bank/bm-c-gpu-bank.json`（+guard 作业，conform 作业加 require）
- 证据：`media/mv-album-001-jay/evidence-c2170/`（原生帧 6 张、条带对照、mask、三份扫描 JSON）