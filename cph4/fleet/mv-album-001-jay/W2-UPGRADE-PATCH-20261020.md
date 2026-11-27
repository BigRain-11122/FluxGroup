# W2 生产管线升级补丁 v1（2026-10-20·技术→艺术感）

> 依据：本周六席学习 + 五路广泛调研（中文平台/专业媒体/工具链/视频官方/图像官方）+ 本机实测。
> 落点：`可爱女人-shots-v2.py` 的 `kf()/i2v()` 生成器与词库，**改生成器不改正典**；KF 包已签发，改动需导演席重签。
> 原则：每条改动都写明「技术依据」与「艺术收益」，不做纯规则堆叠。

## 一、实测：我们旧提示词的术语密度（这是废片来源之一）

用新闸（≥3 术语/条）回扫 W2 现有三条：

| 镜 | 旧词面 | 术语数 | 判定 |
|---|---|---|---|
| KN02 天台全景 | 旧 i2v | 4 | 过，但**无灯具尺寸/距离**，模型自选布光 |
| KN04 掷出 | 旧 i2v | **2** | 不过（close-up / tracking shot） |
| KN09 他仰脸面红 | 旧 i2v | **1** | 不过（只有一个景别词） |

**结论**：我们不是写得不好看，是**信息量不够**——模型只能自己补，补出来就是我们说的"AI 味"。新写法同一镜升到 5-8 个术语。

## 二、五条管线改动（每条：技术依据 → 艺术收益）

### 1. 光句从五槽升七槽（补尺寸/距离/衰减）
- 技术：单灯教程把柔光箱尺寸（60-90cm）与灯距列为第一变量；我们 S4-23 只写「single 2200K lamp」被模型补成双柔光箱。
- 艺术：**一盏灯的距离=亲密度的度量**。`two metres from her, falling off hard within a metre` = 她在一个暖圈里，圈外是冷的。这是《可爱女人》"一窗暖金"的物理写法。
- 例（KN24 灯窗）：`one practical only: a single 40cm paper-shaded bulb behind the window glass at 2800K, two metres from her, its pool laying across the sill and falling off hard within a metre; the room beyond two stops under; ratio 4:1`

### 2. 补整层「景深与焦点」术语
- 技术：旧词库只有焦段，没有景深/焦点转移；而 2001 年代语法主力是深焦+固定机位。
- 艺术：**焦点转移是我们的签名镜头行为**（用焦点代替机位运动讲"从古到今"）。`the sharpest point passing from the sill to her hand` 比任何推镜都高级，而且不需要运镜。
- 例（KN02）：`deep focus, both the near clothesline and the far water tower resolved`——一个镜头交代整个天台，不靠摇。

### 3. 表演层：意图 + 1-2 个微动作 + 显式先后
- 技术：i2v 词面零时序 → 模型把并列位移压成同帧；单条只承载 1 个 state。
- 艺术：**"她想碰但没碰"** 这种戏，靠的是 `fingertip hovering a breath above the surface without touching` + `then easing back to stillness`，不是写"犹豫"。
- 限：帧号写法只用于 H3；其他模型用 then/after/as。

### 4. H3 用方括号相机命令（此前完全没用）
- 技术：MiniMax 官方唯一有语法保证的运镜通道，官方示例可串联 `[Pedestal up], then [Static shot]`。
- 艺术：**先动后静**＝情绪落点。`[Push in]` 到脸，接 `[Static shot]` 停住——推是靠近，静是屏息。
- 例（KN09）：`[Static shot]` 保持手持微晃，脸不动、只有城市光在皮肤上移动。

### 5. 剪辑与调色两条口径修正
- 副歌小节：龙卷风 4 小节=13.3s 超 8 支经典 MV 样本上限 → **压 3 小节**；可爱女人 136BPM 保持 2-4 小节（1.76s/bar）。
- 黑位：抬黑点 10-14 code，**不做 crush-to-black**；暗角 `angle=0.30`（PI 系禁用）。

## 三、三条镜的改写实样（旧 → 新）

### KN04 掷出（动作镜·旧 2 术语 → 新 6 术语）

**旧**：
```
A close-up at eye level, tracking shot. A white paper plane flashing up off a rooftop into the dusk sky, the hand
still open in its follow-through, the water tower sliding past below. Restrained continuous motion, camera and
subject motion only.
```

**新**：
```
A close-up at eye level on the hand and the plane, [Tracking shot]. He releases the plane; fingers staying open
after the release. The water tower slides past below as the plane climbs. one open sky source, no fixture:
blue-hour daylight at 8000K falling from a wide 180-degree sky behind and above him, the near side of his face
two stops under; sodium haze from the street below 2400K rimming the parapet; soft, low contrast, ratio about 2:1.
shallow depth of field, the background falling into soft bokeh. Every motion eases in and settles out, in the
quiet camera language of a 2000 Taiwanese music video. Preserve film grain and the original color palette.
```

艺术差别：旧版只写了"手还张着"；新版把**余势**写成独立动作位（`fingers staying open after the release`），时间上它发生在释放之后——观众看到的是"他还在等它飞"，不是"他扔了"。

### KN09 他仰脸面红（脸镜·旧 1 术语 → 新 5 术语）

**旧**：
```
A head-and-shoulders framing at eye level, gentle handheld sway. A young man on a night rooftop with his face
tipped up to the first stars, a warm flush on his cheeks, his eyes following something high above.
```

**新**：
```
A head-and-shoulders framing at eye level, gentle handheld sway, [Static shot]. He keeps his face tipped up to
the first stars; eyes reach the target two frames before the head turns; caught mid-expression, the smile not
yet reaching the mouth; then easing back to stillness. Only the city glow moves on his skin. two sources only:
the city glow rising from below the parapet (a broad 2000-2400K sodium wash, bounce-level, no fixture) and a
small 2800K window behind him at frame left; his face lit only by the rising bounce, harsh-cut shadow under the
jaw, ratio about 4:1. shallow depth of field, the background falling into soft bokeh.
```

艺术差别：**面红不向模型要**（交妆效与调色）；模型只负责"抬头慢于眼睛、笑没到嘴、光只在皮肤上动"。这是"活人"的三个证据。

### KN24 灯窗初见（全片唯一露脸·新 8 术语）
见 `mv_prompt_upgrade.py` 内置 demo；核心是 `one 40cm paper-shaded bulb, two metres from her` + `fingertip hovering a breath above the surface` + `[Static shot]`。

## 四、执行顺序（不重签不动 KF）

1. `mv_prompt_upgrade.py` 已入库（七槽光/焦点/微动作/方括号/密度检）。
2. i2v 层先切新生成器（KF 未烧的镜直接受益）。
3. KF 层改动**需导演席重签 KF-PACK-A v1.1**（改的是 prompt，不是镜头数）。
4. 烧后跑 `lint_density` 与执行契约卡，准确率 <2/3 不进批量。

## 五、诚实边界

- 术语密度高的提示词**不等于好看**——它只降低"模型自由发挥"的概率。好看与否仍看帧审与盲评。
- 三条改写未烧，无成片证据；密度数字是词面统计，不是质量分。
- 方括号命令只在 H3 落，Seedance 侧仍用自然语言运镜（官方未载明方括号语法）。