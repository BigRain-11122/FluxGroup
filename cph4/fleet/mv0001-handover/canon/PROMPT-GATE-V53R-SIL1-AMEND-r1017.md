# PROMPT-GATE · V53R SIL1 修帧 prompt 改稿重闸 · verdict

| 项 | 值 |
|---|---|
| 闸位 | PROMPT-EXPERT-GATE v1（独立席 · 禁自审自签） |
| 闸类 | 改稿重闸（同参数两轮实烧两败后复审） |
| 单据 | V53R SIL1 修帧：generate_image · edit_mode=local · edit_region=[0.368,0.286,0.068,0.107] · 1344×768 石碑符带局部 |
| 送审方 | 导演席（改稿起草方） |
| 审方 | 独立提示词专家席（本席 · 未参与起草） |
| 裁决日 | 2026-10-17 |

## 0 · 案卷摘要（两轮病灶）

| 轮 | 实烧结果 | 病灶拆解 |
|---|---|---|
| R1 | 产八角星，不合格 | 平涂贴片（无 V 槽深度）· 色温偏冷 · 横杠越界 |
| R2 | 未产星形，不合格 | 心形轮廓残留 · 平涂覆盖 |

同参数两败 → 改稿重闸成立，本席独立受理裁决。

## 1 · 送审改稿全文（导演席草案）

> Replace the heart-shaped carved glyph with an eight-pointed star votive glyph built from thin single-line V-groove strokes in the same carving manner as the neighboring glyphs: deep dark grooves with the warm golden torch light catching their upper edges, the stone surface visible between the strokes; the star matches the size of the neighboring glyphs and sits in the same cell position the heart occupied; the heart-shaped grooves vanish completely as the new star takes their place; keep the stone surface texture, the torch backlight, the silhouette edges and everything outside the selected area exactly as they are.

## 2 · 六面裁决

### ① 语义完整性——心形残留驱除（对 R2 病灶）｜✓ 过

"the heart-shaped grooves vanish completely as the new star takes their place" 为**显式驱除句**：清除与替换绑定为同一生成动作，模型无法只执行其一。对比原过闸稿仅隐含替换语义，此句直接封死 R2「星未生成 + 心形残留」路径；格位去向另有承接（"sits in the same cell position the heart occupied"），语义闭环完整。

### ② 刻痕风格锚定——「线刻而非平涂」可执行强度（对 R1 病灶）｜✓ 过

四要素齐备，且为**构造式正向约束**（说清"是什么"，优于 "no flat patch" 类负向排除，对局部编辑更稳）：

1. 细线 V 槽 → "built from thin single-line V-groove strokes"（构造语，强于原稿状语式 "carved in the same … style"）
2. 槽内暗影 → "deep dark grooves"
3. 上缘暖金受光 → "the warm golden torch light catching their upper edges"（"golden" 显式对冲 R1 色温偏冷）
4. 线间露石面 → "the stone surface visible between the strokes"（结构性排除实心贴片：若平涂则该句不可满足）

### ③ 尺寸/格位锚——防越界侵邻（对 R1 横杠越界病灶）｜✓ 过

双锚到位：尺寸锚 "matches the size of the neighboring glyphs" + 格位锚 "sits in the same cell position the heart occupied"；区外保全句（见④）构成第三重边界。判强度足够，不要求追加"八尖不出格"类冗余句——过指定反而伤与邻符的一致性。

### ④ 保留句族完整性｜✓ 过

四项齐备：石面纹理（"keep the stone surface texture"）· 火把逆光（"the torch backlight"）· 剪影边线（"the silhouette edges"）· 区外保全（"everything outside the selected area exactly as they are"）。右缘人物发丝剪影由 "silhouette edges" 项覆盖。

### ⑤ 零 API 参数 · 零文化锚 · 零事实冲突｜✓ 过

全文无坐标/数值/工具名/模式名等 API 语汇。"votive glyph" 为原过闸稿已确立的符带既定用语，非新增文化锚。"warm golden torch light" 与火把背光画面事实一致；"neighboring glyphs"（左邻蝶形符）为画面实存引用，风格/尺寸锚合法；无与石碑背光、发丝剪影相抵触的表述。

### ⑥ 英文文法与可执行性｜✓ 过

祈使主句 "Replace … with …" 开篇定动作；冒号引出构造规格；分号四层递进（构造 → 尺寸格位 → 驱除 → 保全）；代词就近指代明确（"their" 指 grooves）。"the same cell position the heart occupied" 省略关系代词属口语化正确用法，图像指令语境无歧义。可直接执行。

## 3 · 微瑕记录（不阻塞 · 备查）

1. 首句替换目标未复述 "in the selected area"（原过闸稿有）：局部编辑模式下选区即硬约束，且保留句已建立 "selected area" 内外二分，判不阻塞。
2. 受光方向由原稿 "upper-left edges" 放宽为 "upper edges"：与「同邻符刻法」锚一致，方向交由邻符画面事实决定，判中性偏稳。
3. "vanish completely" 属生成式驱除（依赖模型在替换动作内消化清除）；若三烧仍现心残，升级 FIX 走显式负面排除句重写（闸内预案，本次不执行）。

## 4 · VERDICT

**PASS-with-notes** —— 可直接烧，带下述烧后帧检注意点。

烧制文本 = 送审改稿全文，**逐字执行 · 零改动**：

> Replace the heart-shaped carved glyph with an eight-pointed star votive glyph built from thin single-line V-groove strokes in the same carving manner as the neighboring glyphs: deep dark grooves with the warm golden torch light catching their upper edges, the stone surface visible between the strokes; the star matches the size of the neighboring glyphs and sits in the same cell position the heart occupied; the heart-shaped grooves vanish completely as the new star takes their place; keep the stone surface texture, the torch backlight, the silhouette edges and everything outside the selected area exactly as they are.

### 烧后帧检注意点（本 verdict 附加条件）

1. **心形根检**：原心形两瓣弧线及下缘完全消失，格内无平涂心影/暗底残留。
2. **线刻四要素**：星=细线 V 槽刻痕（非实心贴片）· 槽内深暗 · 上缘暖金 · 线间露原石面；整格色温不偏冷。
3. **越界三查**：八尖不出原心形格位；左不侵蝶形邻符；右不压发丝剪影；无横杠跨格。
4. **区外保全**：石面纹理 / 火把逆光 / 剪影边线与区外像素一致无漂移。
5. **尺寸对比**：星符与邻符同尺寸、同带宽、格位居中。

帧检任一不过 → 回闸重审；两败已成案底，**三败即冻结该参数组合**，转结构重审（REJECT 级处理）。

## 5 · 闸律签署

- 起草方 = 导演席，本席未参与起草与两轮实烧，独立裁决成立（禁自审自签律 ✓）。
- 裁决依据全部来自本单指令所载案卷与送审文本，零外部读取、零 git 操作。
- PROMPT-EXPERT-GATE v1 · V53R-SIL1-AMEND · r1017 · 2026-10-17 · 裁决 = **PASS-with-notes**
