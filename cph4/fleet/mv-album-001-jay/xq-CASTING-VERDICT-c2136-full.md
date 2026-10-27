# 星晴女主定妆判读 · c2136-full（正档 1344×768）

> 执行=bm-c C2137 tick 收割轮 · 2026-10-20 09:42–09:5x · 承 `xq-CASTING-READ-c2136.md` §五-1「主推 A、B 双线，各出 1344×768 × 3 种子定妆照，锁定 1–2 张作定脸基准」
> 波发=`2026-10-20 09:32:43`（C2137-casting-ab-full）· 收片 `09:37:58`
> 回执=`xq-CASTING-RECEIPT-c2136-full.json`（3807B）· 拼板=`xq-CASTING-BOARD-c2136-full.jpg`（2708×1152 / 230,093B）
> 素材=12 张原生 1344×768 PNG（A 马尾 / B 柔顺长直发 × 黄昏逆光 / 夜景街灯 × 3 种子）

## 〇 零、当轮闸结论（先给结论）

| 闸 | 结论 | 依据 |
|---|---|---|
| 烧制完整性 | **PASS 12/12** | log `CASTING burns: ok=12/12 fails=none` + `CASTING-FULL-END ok=12/12` |
| 提示词 lint | **PASS** | NEG / VAGUE / CONCEPT 三名单 zero-hit；seeds unique 12/12 |
| 帧级 QC（原生分辨率） | **PASS，零淘汰级缺陷** | 拼板 12 格 7.5–9.0；top3 原生复核 8.9 / 9.0 / 9.0 |
| 骨龄门（v1 判负项） | **PASS** | 12/12 落 19–21；无 14–17 少年感回流 |
| 夜场蜡感门（v1 判负项） | **PASS** | 夜景三件皮肤保留毛孔/油光，无磨皮假面 |
| 反向测试（撞脸） | **PASS** | 无一格可指向现实艺人；无肖像风险 |
| 年代门 | **PASS** | 素颜、无韩式平眉/网红唇/修容；白衫 + 黄昏草地 + 靛蓝夜空 = 2001 台湾校园 MV |
| 受众门 | **PASS** | B「安静干净、夜里看星星」= 名字即人设（星晴）最贴 |

**定谳：B 型（柔顺长直发）为正典女主脸，A 型（高马尾）为备选/变体线。**

---

## 一、候选全表与评分（原生 1344×768 复核）

| 排序 | 候选 ID | 文件 | 种子 | 光 | 评分 | 判 |
|---|---|---|---|---|---|---|
| **1** | `XQ-CAST-c2136full-B-dusk-s3` | `CAST_B_soft-long_dusk_s578950.png` | 578950 | 黄昏 | **9.0** | **首选 · 正典脸锚** |
| **2** | `XQ-CAST-c2136full-B-night-s2` | `CAST_B_soft-long_night_s514974.png` | 514974 | 夜 | **8.5→9.0** | **正典夜场基准**（表情最自然） |
| **3** | `XQ-CAST-c2136full-A-night-s2` | `CAST_A_ponytail_night_s439906.png` | 439906 | 夜 | **8.5→9.0** | **备选 · 跨发型一致性锚** |
| 4 | B-dusk-s1 | `CAST_B_soft-long_dusk_s775362.png` | 775362 | 黄昏 | 8.5 | 备 |
| 5 | B-night-s1 | `CAST_B_soft-long_night_s984412.png` | 984412 | 夜 | 8.5 | 备 |
| 6 | A-night-s1 | `CAST_A_ponytail_night_s79128.png` | 79128 | 夜 | 8.5 | 备 |
| 7 | A-dusk-s2 | `CAST_A_ponytail_dusk_s757434.png` | 757434 | 黄昏 | 8.0 | 备 |
| 8 | B-dusk-s2 | `CAST_B_soft-long_dusk_s42613.png` | 42613 | 黄昏 | 8.0 | 备 |
| 9 | B-night-s3 | `CAST_B_soft-long_night_s901816.png` | 901816 | 夜 | 8.0 | 备 |
| 10 | A-dusk-s3 | `CAST_A_ponytail_dusk_s341614.png` | 341614 | 黄昏 | 7.5 | 备 |
| 11 | A-dusk-s1 | `CAST_A_ponytail_dusk_s583046.png` | 583046 | 黄昏 | 7.5 | 备 |
| 12 | A-night-s3 | `CAST_A_ponytail_night_s88208.png` | 88208 | 夜 | 7.5 | 备 |

> 评分口径=八维（面部解剖 / 易崩部位 / 发丝 / 光照自洽 / 服装肩部 / 文字杂物 / 皮肤质感 / 构图）多模态逐维打分取均。

### Top3 逐维

**① B-dusk-s3（首选）**：解剖 9 · 易崩 9 · 发型 8 · 光照 8.5 · 服装 9 · 杂物 10 · 皮肤 8.5 · 构图 9 = **8.9**
可修点仅两处：右侧肩前几缕发丝与背景亮草轻微粘连；两颊轻度平滑（该分辨率极限）。黄昏逆光光晕位置、发丝边缘光与光源自洽，面部亮度需以「现场反光板」解释才完全物理自洽——**MV 拍摄语境内成立**。

**② B-night-s2（夜景基准）**：解剖 9 · 易崩 9 · 发型 8.5 · 光照 9 · 服装 9 · 杂物 10 · 皮肤 9 · 构图 9 · 表情 9 = **9.0**
暖主光来自镜头侧偏上、下颌投影像自洽，深蓝暮色冷暖分离干净，无青/绿污染；闭口浅笑有眼下肌肉参与，**全批最自然的一格**。

**③ A-night-s2（备选/一致性锚）**：解剖 9 · 马尾 9 · 光照 8.5 · 易崩 9 · 服装 9 · 杂物 10 · 皮肤 9 · 构图 8.5 = **9.0**
马尾发根起势方向正确、发流可读、发梢有层次，无「塑料壳」硬边。唯一建议处理点=左下角斜向暗块（前景阴影）来源略含糊，装配端可压暗/裁除。**与 B-night-s2 脸型最接近**，故同时充当跨发型同一人验证锚。

---

## 二、正典固化（可复现配方）

**模型链**：`krea2_turbo_fp8_scaled.safetensors` + `qwen3vl_4b_fp8_scaled`(type=krea2) + `qwen_image_vae` · `euler` / `simple` / steps 8 / cfg 1.0 / denoise 1.0 / `jman`（男性 ID LoRA）**刻意不挂** · 尺寸 1344×768

**ERA 块（v2 骨龄修正版，逐字）**
```
a woman of about nineteen or twenty, first-year university student in 2000 era Taipei, mature facial structure with a defined jawline, calm confident bearing, simple summer outfit, natural skin texture with visible pores and subtle unevenness, natural hair texture, head-and-shoulders portrait, facing the viewer
```

**B 型 ID 块（正典）**
```
long straight dark hair with a soft air fringe, gentle rounded brows, quiet smiling eyes, small clean face
```

**光位块**
- 黄昏：`lit by 2800K dusk backlight with a warm halo, standing in a golden grass field, rim of warm light along her hair`
- 夜景（v2）：`lit by practical warm street-lamp light with soft falloff against an indigo night sky, film grain visible in the shadows, standing outdoors after dark`

**收尾块**：`35mm film grain, telecine texture, 2001 Taiwan music video look`

**组装式**：`f"{ERA}, {TYPE}, {LIGHT}, {CLOSING}."`

**正典种子**
| 角色 | 光 | 种子 | 文件 |
|---|---|---|---|
| 正典脸锚 | 黄昏 | **578950** | `CAST_B_soft-long_dusk_s578950.png` |
| 正典夜场 | 夜 | **514974** | `CAST_B_soft-long_night_s514974.png` |
| 备选/一致性锚 | 夜（A 型） | **439906** | `CAST_A_ponytail_night_s439906.png` |

> 复现法：`XQ_CAST_FULL=1` 跑 `xq_casting_c2136.py` 即同链同参数；单格重烧按上表 type/light/seed 直配。

---

## 三、判读驱动的前置拦截（记录）

- v1 判负面（14–17 骨龄 / 夜场蜡感）**在两站内被拦下并修复**：出生站=提示词层（年龄句 + 夜景改 practical lamp + 颗粒句），未流入正档——符合「缺陷出生地拦截律」。
- v1 判负面（A 夜格马尾存在感消失 / 跨种子不是同一人）在本批**已消解**：3 种子马尾结构全成立，A-night-s2 与 B-night-s2 脸型接近。
- **回执勘误**：`xq-CASTING-RECEIPT-c2136-full.json` 的 `out_dir` 字段为脚本硬编码旧值 `.../xq-casting-c2136`，实际产物目录=`.../xq-casting-c2136-full`；板/图/种子均正确，仅该元数据字段失真，不影响复现（重跑脚本按 FULL 分支自动落 `-full`）。

---

## 四、下一步（导演席排程）

1. **定脸正典采用**：B（578950 黄昏 + 514974 夜）双光位锁脸；A（439906）保留为马尾线备选。
2. **`KF-PACK-B` 解锁**（承 READ §五-3）：`S1-08 / S3-17 / S3-21 / S5-31` 四帧 + B 补 2 帧，**逐帧复用上列 ERA+B 块与光位块**，妆造随场景但 ID 块不动。
3. A 包 + B 批 6 帧合装后可覆盖全曲时间轴（现 A 包 196.14s / 全表 238s / 原曲 259.4s）。
4. 定脸后任何 i2v 镜的 first_frame 必须锚定本三张正典，禁另起脸。

*导演席代裁定稿（承 2026-10-11 19:4x CEO 零卡点流线令：中段过目门就地撤销，导演席定稿含定脸）· bm-c C2137 · 素材与参数全部可复现*

---

## 五、B-EX2 锚点修复令（C2142·原生像素实证）

- 实测：672×384 三种子（204921 / 206038 / 207158） + 1344×768 双种子（206038 / 207158）共 5 帧，**手指全部粘连（3–4 团块）、拇指不可辨**——手部条款 0/5 PASS。结论：非种子问题，锚点本身不可渲染（手占画幅过小 + Krea2 手部结构弱点）。
- 判据升级（机械可查）：**手部近景类锚点（手占画幅 >8%）出生即拒**；B-EX2 改为「手被遮挡」构图——她的手没入外套下摆后侧、镜头自她肩后看，手势由手臂角度读出，画面内无可点数手指。
- 证据：`xq-KFPB-BEX2-RECEIPT-c2140.json`（672 档） / `xq-KFPB-BEX2-RECEIPT-hd-c2142.json`（1344 档）；板 `xq-KFPB-BEX2-BOARD-c2140.jpg`；帧目录 `xq-kfpb-bex2-reroll-c2140/`、`xq-kfpb-bex2-hd-c2142/`。
- 附属发现：两档皮肤均为光滑磨皮感（无毛孔），主片需在 GRADE 层补颗粒（既有 GRADE-LAW 已含颗粒/halo 位，此为再证）。

## 五之二、B-EX2 换锚验收（C2143·重拍实证）

- 执行：按上节裁定换锚重拍，runner=`cph4/fleet/idle-guard-kit/kfpb_bex2_occl_c2143.py`（遮蔽手构图，1344×768，3 确定性种子 204921/209030/211892），3/3 烧成 284s。
- **原生尺寸判读（非拼板）3/3 PASS**：
  - o1 s204921——手完全没入外套下摆，画面内无可点数手指；他的视线单向落在她脸上，眼线成立；皮肤在黄昏主光下可接受。→ **B-EX2 主片种子锁定 204921**。
  - o2 s209030——手势落成搭在他小臂上的轻握，四指清晰、拇指位于手臂背面（合法遮挡），眼线成立，无融化解剖。→ 备选一。
  - o3 s211892——同上，握持落在小臂近肘处，四指可数、拇指背面遮挡。→ 备选二。
- 结论：缺陷确在锚点的手部近景，把近景移出画面即消失；「手部近景 >8% 出生即拒」闸生效并被本轮反向验证。
- 证据：帧目录 `xq-kfpb-bex2-occl-c2143/`（1.05–1.18MB ×3）·板 `xq-KFPB-BEX2O-BOARD-c2143.jpg`（80,444B）·回执 `xq-KFPB-BEX2O-RECEIPT-c2143.json`。
- 下步：KF-PACK-B 六帧 1344×768 主批（其余 5 帧锚照旧），银行已挂 `kfpb-mainpass-author-c2144`。
