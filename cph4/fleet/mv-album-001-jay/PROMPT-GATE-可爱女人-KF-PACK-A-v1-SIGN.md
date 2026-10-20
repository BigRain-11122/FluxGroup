# PROMPT-GATE-可爱女人-KF-PACK-A-v1-SIGN（第 3 层导演席合并·复检·签发）

- **gate id**：PROMPT-GATE-可爱女人-KF-PACK-A-v1-SIGN · 2026-10-20 12:5x · 签发面=bm-a 导演席（承 O-20261020-1124 W1-W2 多曲加速排产令 @bm-a 份额；三层闸=PROMPT-EXPERT-GATE-v1 + 独立审 verdict + 导演席合并签发）
- **审对象**：`可爱女人-shots-v2.py` NEW 30 帧（A 批 28 帧：B1 KN01-07 / B2 KN09-16 / B3 KN17-23+KN20b / B4 KN25/28/29/30；KN08/KN24 不在 A 批审面）· 人读稿 `可爱女人-KF-PACK-A-v1-DRAFT.md`
- **verdict 源**：`PROMPT-GATE-可爱女人-KF-PACK-A-v1-L2.md`（2026-10-18·独立评审席·四块·整包 FIX 级 28 帧 PASS15/FIX13/REJECT0）

## 一 FIX 并入表（8 条最小改法 · 逐条落位实证）

| # | 位 | 改法 | 落位证据 |
|---|---|---|---|
| F-1 | KN06 | kf 补 `tex="film_night"`（5279） | 全包零日戏：`5246` 命中数=0 / `5279` 命中 30/30 帧 |
| F-2 | KN02 | `a black corrugated-tin water tower` + 随 HIM 补发型句 | 命中 1 · 168 词 |
| F-3 | KN09 | 随 HIM 补发型句 | 命中 1 · 167 词 |
| F-4 | KN23 | 随 HIM 补发型句（临界 190 词） | 命中 1 · 190 词 <200 |
| F-7 | city_bowl 块 | 尾加 `a low-rise 2000 Taipei skyline of apartment rooftops and water towers` | 受益帧实测 **10**（KN07/10/11/12/13/22a/22b/23/25/29）= verdict 勘正数一致 |
| F-8 | KN22b | 铁皮水塔词面 | 命中 1（KN02/KN22b 双帧） |
| F-9① | KN25 | 中句换她窗+城钠对位定稿 + 尾句去 sodium 重复 | 命中 1 · 134 词 |
| F-29 | KN29 | `one plain white and one cream paper plane with its wing tip dipped in red`（HER_PLANE 同款律回锚） | 命中 1 · 144 词 |

## 二 复检回执（机核 · 2026-10-20 12:5x）

- runner=`media\BigStream\.c3-tmp\r2413_recheck_keai.py`（import 正身模块 → 逐帧 `LX.lint(mode='t2i')` 三名单 + 词数 + FIX 特征串）
- **lint：30/30 帧零命中（issues=0）**
- **词数：min 105（KN21）/ max 190（KN23）· 全包 ≤200 闸过**
- 共享块：PLANE 逐字挂 16 帧 + 行内 2（KN20b 对偶再生成态 / KN29 现按 F-29 回锚 HER_PLANE）；HER_PLANE 链 KN21/28/29/30 词面闭合
- 外观项勘正（verdict 移交④）：DRAFT 头注 v2.6 更新为 PLANE「16 常量挂+2 行内」、F7「受益 10 帧」

## 三 移交注记（不阻塞 A 批）

1. **i2v 同步位**：KN25（两灯句）/KN29（红尾回锚）+ KN01/KN18 slide FLAT → 随 KF-PACK-i2v 合并执法（F11 并案）。
2. **KN12/KN29 `towers` vs F7 `low-rise`**：判相容（前景参照 vs 全城轮廓）；导演席保留 `towers→blocks` 微调权，非 FIX。
3. **模板副作用（如实记录·非缺陷）**：`kf()` 对 light 块 `.capitalize()` 会把块首字符大写、并把块内专名小写化（`Taipei`→`taipei`）。历史全包同态，本轮不改模板（避免全包重烧）；若后续要求专名保留大写，作为模板级变更单独评审。
4. 烧制侧执行：海选制单口径（672×384 8 步 → 两级海审 → 1344×768 refine 0.30）· 烧制前后各跑一次 t2i lint · 28 帧词数必检。

## 四 签发

- **判定：准烧（A 批 28 帧）**——独立审 verdict + 8 条 FIX 全落位 + 机核复检回执（lint 零命中 / 词数闸 / 纹理闸 / 受益帧数）构成完整过闸链；烧制侧可即点火。
- 执行口径：POOL-0022（多曲 KF 先行+滚动 i2v），签发即烧；抽检位=F-29（KN29 v2.4 渲染翻车判例）+ KN23（190 词临界）。

—— bm-a 导演席 · 2026-10-20（审=独立评审席 2026-10-18 · 签=导演席）