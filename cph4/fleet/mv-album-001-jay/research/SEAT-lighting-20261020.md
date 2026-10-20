# SEAT-lighting-20261020 · 摄影灯光席学习件（2000 台式布光 × AI 可控光）

> 必读四件已读（CAMERA-DIRECTION-v1 / TONE-FINGERPRINT-W1-W2 / 两曲 GRADE 光锚 / 星晴 SHOTLIST 光位列）。只学不改正典。

## 一、本席 AI 病灶三条（皆有实帧或实词面）

1. **夜戏发青**（A·内源实帧）：星晴 XQ26 夜骑「城光 bokeh 冷青白，非自锚钠光」（PANEL-COLORIST-20261012 判高）；可爱女人 KN05「天墨青黑非银蓝」。根因=模型把混合色温“校正”回中性，蓝通道被强推；钠灯本身缺波长，越校越浑浊（C 外源同判）。
2. **人脸上多出一盏灯**（A·内源实帧+词面）：XQ26 二烧「构图修好但亮脸复发」——尾句 `warm skin tones` 成了画外补光，把该沉进灯池外的脸抬亮（星晴-shots-v2.py 注释实锚）。同族：KN05 纸机顶光与探照光柱光向脱节。
3. **室内像棚拍**（A·内源词面）：S4-23 光块全文只有 `single 2200K warm lamp light`——无灯位、无衰减、无遮挡。模型按训练先验补成均匀柔光，单光源戏被拍成双柔光箱。

## 二、可执行工艺 8 条（判据 → 做法 → 本片验证点）

1. **光句五槽定序**（A）：SOURCE→DIRECTION→QUALITY→RATIO→KELVIN。判据=光块必须同时含相机相对方位词与 K 值，缺一退稿；照 Hailuo 原句格式 `warm key light from 45 degrees screen right` 写。▸验：S4-23 现句零方位。
2. **光比写数不写形容词**（A/C）：日戏 2:1、室内单源 4:1、夜外景 8:1–16:1、剪影 ≥32:1。判据=光块出现比值或 `two/three stops under`；`dramatic`/`moody` 不计分。▸验：S5-29 背对背应 32:1，现块无比值。
3. **测光点写死**（C 工艺，本片实测有效）：每个有人脸的镜指定唯一曝光基准物。做法=`exposed for her face, the street falling three stops under`。▸验：XQ26 亮脸即无测光点所致。
4. **光源可见性优先入画**（A）：2000 实景戏先让 practical 入画（窗/灯/车灯/路灯），再写它落在什么表面。判据=光块含 `its light laying … across …`，或明写 off-frame。▸验：warm_window 块=正例，KN05=反例。
5. **一镜一主光**（B 内源）：第二光源只许反射或小面积 practical（<10% 画面），禁对称 key+fill。判据=光源名词 ≤2 且其一为 practical。▸验：S4-23 只该有一盏；W2 全片唯一暖源=一窗。
6. **钠灯不校正**（C）：环境 2000–2200K 保橙，脸只吃反射；白平衡词一律不写。判据=肤色 Hue 15–40°，青绿 140–200° 像素 <5%。▸验：XQ26 发青。
7. **halation 必有源**（A）：只有太阳/月/灯入画或压边 15% 才写 halation，且同句给过曝理由。判据=halation 与可见光源同句。▸验：S3-20 写 `strong halation rim` 却无源，应补“太阳压在山脊下缘”。
8. **年代灯型白名单**（B）：钠 2000–2200K / 钨丝 2800–3200K / 荧光 4000K 冷绿 / 车灯 3000K。判据=光块所有 K 值落区间；6500K 冷白 LED 与 RGB 渐变霓虹=穿帮。▸验：XQ26 bokeh 冷青白=越界。

## 三、来源分级清单

- **A**｜Hailuo 官方《Maintaining Lighting Consistency》：主镜光句须**逐字复用**到每镜；`Chiaroscuro/Noir/Moody` 对模型歧义，必须换成灯位语言；点光源比大面积光更真。https://hailuoai.video/pages/knowledge/lighting-consistency-ai-video-campaigns
- **A**｜Kodak VISION3 500T 技术数据：+2 档高光宽容、暗部染料降噪——负片“高光耐操、暗部易脏”的量化底。https://www.kodak.com/content/products-brochures/Film/VISION3_500T-Color-Negative-Film-7219-TECHNICAL-DATA.pdf
- **A（内源实帧）**｜PANEL-COLORIST-20261012：XQ26 冷青白 / KN05 墨青黑 / 纸机顶光与光柱脱节。
- **A（内源词面）**｜星晴-shots-v2.py L32-45、可爱女人-shots-v2.py L26-40：光块原文与 K 值。
- **B**｜星晴 MV 摄于淡水海边/草地/旧屋（bilibili/新浪/抖音三处同述）→ 实景自然光拍摄的制片事实。https://www.bilibili.com/video/BV1zQSUYKEtR/
- **B**｜街灯色温谱：HPS 约 1800–2000K、汞灯偏冷绿。https://frameandfocal.com/photography-glossary/set-white-balance-common-types-streetlights
- **C**｜cinematography.com 钠灯帖：钠灯缺波长不可完全校正；白平衡压到 3200K 以下=强推蓝通道，只得浑浊低饱和。https://cinematography.com/index.php?/forums/topic/39681-sodium-vapor/
- **C**｜David Mullen 帖 / Creative COW：2000 前后胶转磁=极高反差、高光少拐点易爆。https://cinematography.com/index.php?/forums/topic/90377-late-1990searly-2000s-look/
- **C**｜Artlist / QuestStudio：提示词五槽序（源/向/质/平衡/色）+ 逐镜复用同一光块；两站为商业博客。https://artlist.io/blog/ai-lighting-prompts/ ｜ https://queststudio.io/blog/camera-lighting-prompt-cheatsheet
- **GitHub**｜Rylaispirit/cinematic-video-prompt-skill **152★ MIT**：references/02-lighting.md 80+ 光词；但过半是 studio/softbox/beauty-dish——照抄就是「室内像棚拍」的病源，只取自然光与时点词。
- **GitHub**｜artnebo/cinematic-frame-director **3★ MIT**：60:30:10 光预算 + contre-jour 默认，适合单帧定调。
- **GitHub**｜中文 2000 年代台湾 MV 布光词表：**无适配**（未找到可用轮子）。

## 四、落到在产四曲（每曲一条可立刻改）

- **星晴**｜S3-21（B 批未烧，她低头笑半拍）：`dusk warm light` → `2900K rim from behind screen-left, her face one and a half stops down in open shade, the last warm band on the horizon`。先定光向再烧，省一次回炉。（S4-23 若回炉：补灯位与衰减，见工艺 1。）
- **可爱女人**｜KN09（他夜天台仰脸，KF 未烧）：`roof_night` 现块无 K 无向。改 `the city's sodium glow rising from below the parapet at 2200K, lighting the underside of his jaw, the sky at 8000K three stops darker`——仰脸的面红来自血色，不来自补光。
- **龙卷风**｜场 5 拉窗帘·浅方形显形：写死 `flat grey daylight through the window camera-left, the pale rectangle on the wall one stop brighter than the wall around it, dust turning in the beam`；测光点=那块墙，人脸压到 1.5 档下——「光=显影液」才成立。
- **简单爱**｜场 3 影子先牵手 + 场 8 两代单车：同一条光句跨场复用 `the sun ten degrees above the far embankment, behind them, their shadows stretching toward camera about three times their height`；两场影长/影向不一致=直接判负。

## 五、验收判据（可机检 / 可盲评）

1. 直方图：夜戏黑位 3–5%（不纯黑、不抬灰）；除光源外无 >98% 大面积死白。
2. 肤色采样：脸 ROI Hue 15–40°、S 15–45%；夜戏 S≥12%（不死灰）；青绿 140–200° 像素 <5%。
3. 光向一致：同场连续镜，脸高光侧（左/右）与 catchlight 位置一致率 100%；catchlight 数 ≤1。
4. 光比：脸与背景亮度差落预设带（日 1 档 / 室内 2 档 / 夜 3–4 档）。
5. 光源计数：入画光源 ≤2，其一必为 practical 或天体。
6. 盲评：十席做「实景 or 棚拍」二选一，正确率 ≥8/10；「太阳在哪边」指认 10/10。

## 六、禁用清单

- `cinematic lighting` / `dramatic lighting` / `moody` / `chiaroscuro` 单词裸用（引擎正主明示歧义）。
- `studio lighting` / `softbox` / `beauty dish` / `two-point lighting` / `even lighting` / `perfectly lit face`。
- `key from left, fill from right` 类对称双光（=人脸上两盏灯）。
- 夜戏写 `neutral white balance` / `color corrected`（钠灯必发青）。
- 无源的 `glow` / `halation` / `bloom`（塑料感）。
- `soft ambient light with no visible source`（棚拍默认值）。
- 6500K 冷白 LED、RGB 渐变霓虹（年代穿帮）。
- 夜戏尾句无条件挂 `warm skin tones`（隐形补光，XQ26 实锚）。

## 七、SKILL-PATCH 建议（若沉淀 cph4/skills/mv-lighting）

1. **光块 lint**：五槽齐全（源/向/质/比/K），缺方位词或 K 值即 FAIL——直接接现有 prompt_lexicon lint。
2. **光锁表**：一曲一份 LIGHT dict 逐字复用，改景不改光句；跨镜只换主体与运镜。
3. **夜戏三律**：保钠橙、脸为测光点、背景压 3–4 档；禁中性白平衡与无源补光尾句。
4. **单源室内模板**：一盏 practical + 灯位 + falloff 句 + 暗角，studio 词进黑名单。
5. **验收三件套**：face ROI 肤色直方图 + 光向/catchlight 一致性 + 「实景/棚拍」盲评，接成片闸。