# MV 专业术语词典 v1（AI 可识别术语 · 减少废片）

> CEO 令 2026-10-20：「务必多学习各种专业的术语，尤其是AI能准确识别的，这样才能减少废片」
> 定位：与 `prompt_lexicon.py`（已有 SHOT_SIZE/CAM_*/LENS/LIGHT/GRADE/TEXTURE/SCENE/POSE）**互补不重复**：本件补 **表演微动作**、**景深/焦点**、**剪辑术语**、**年代器物术语** 四类，并把「模型识别不了的说法」列成反例表。
> 用法：写提示词时只从词表取词；词表里没有的概念 = 先补词，不要即兴发挥。

## 一、为什么术语能减少废片

模型对「术语」和「形容词」的处理完全不同：
- **术语**有稳定视觉先验（`split lighting`、`rack focus`、`85mm portrait lens`、`eyelid closed through eight frames`）→ 出片可预期。
- **形容词**没有稳定映射（`cinematic`、`emotional`、`高级感`）→ 每次出片不同，只能靠重摇抽卡 = 废片。

**一条判据**：每个词问一遍「摄影机/测光表/秒表能不能拍到它」。拍不到的，删。

## 二、景别与机位（补 SHOT_SIZE/CAM_ANGLE 之外的可用层）

| 中文 | 可识别术语 | 反例（别写） |
|---|---|---|
| 大特写（只有眼/唇） | `extreme close-up on the eyes` | `face close-up feeling intimate` |
| 破框特写（额头切掉） | `close-up cropped at the forehead, chin below frame edge` | `artistic framing` |
| 过肩 | `over-the-shoulder from behind his left shoulder` | `conversation shot` |
| 低机位仰拍 | `camera at chest height looking up` | `hero angle` |
| 平视中性 | `eye-level, lens at her eye height` | `natural angle` |
| 俯拍 | `camera above head height looking down at the floor` | `bird's eye feel` |

## 三、景深与焦点（现有词库最缺的一层）

| 中文 | 可识别术语 | 用途 |
|---|---|---|
| 浅景深 | `shallow depth of field, background falling into soft bokeh` | 脸镜、物件特写 |
| 深焦 | `deep focus, both the foreground hands and the far wall resolved` | 空间交代、2001 年语法主力 |
| 焦点转移 | `the sharpest point passing from X to Y` | 镜头行为替代机位运动（我们签名的型 5） |
| 前焦虚化 | `out-of-focus foreground element at frame left` | 增加层次，防平 |
| 焦点漂移 | `focus breathing slightly as he leans in` | 手持生活流 |
| 裂焦 | `split diopter, near hand and far window both sharp` | 慎用：年代可用但易假 |

## 四、表演微动作（新增·对应 mv-performance）

| 中文意图 | 可识别术语 | 备注 |
|---|---|---|
| 忍眨 | `eyelid held shut for eight frames, then released` | 眨眼质量可机检 |
| 视线先到 | `eyes reach the target two frames before the head turns` | 双人镜核心 |
| 喉结吞咽 | `one slow swallow, throat moving once` | 紧张外化，最便宜 |
| 呼吸屏住 | `breath held, ribs still, then released after the sound` | 事件后反应 |
| 手指悬停 | `fingertip hovering a breath above the surface without touching` | 留白动作 |
| 重心前压（不迈步） | `weight pressing forward onto the front of the foot, heels staying planted` | 想靠近但不走 |
| 肩先沉后松 | `shoulders dropping before they release` | 郑重 |
| 松手余势 | `fingers staying open after the release` | 掷/放动作的余势 |
| 半途表情 | `caught mid-expression, the smile not yet reaching the mouth` | 防蜡像 |
| 不对称 | `one brow a breath higher than the other` | 防对称 AI 脸 |
| 收束回静 | `then easing back to stillness` | 每条微节拍必须收尾 |

**禁**：`happy / sad / nervous / emotional / natural / alive`（模型无稳定映射，且违反表演席"写动作不写情绪"）。

## 五、剪辑术语（写进装配单，不写进提示词）

`hard cut`｜`dissolve (only for time/space jumps)`｜`cut on action, six frames of overlap`｜`J-cut / L-cut (audio leads/lags)`｜`match cut`｜`smash cut`｜`beat grid`｜`downbeat`｜`bar = 4×60/BPM`｜`hold`｜`ramp`｜`speed ramp 0.25-0.5s with interpolation`。

**禁写进画面提示词**：`fast cuts`、`montage`、`cinematic editing`（模型会乱切或干脆不动）。

## 六、年代器物术语（道具席扩充）

`mechanical piano-key buttons`（机械琴键，非触控）｜`transparent tape window`（透明带窗）｜`AA battery bulge on the back`（电池仓凸包）｜`chrome trim pitted at the edges`（镀铬麻点）｜`yellowed ABS seam line`（泛黄接缝）｜`steel single-speed frame with full fenders and a rear rack`｜`chain guard`｜`wire basket bent inward once`｜`acrylic lightbox with fluorescent tubes`｜`CRT with curved glass, deeper than 40cm`。

**禁**：`sleek`、`modern minimalist`、`matte black anodized`、`touch control`、`LED panel`（年代穿帮源）。

## 七、色调与光学术语（补 LIGHT/GRADE）

`key / fill / rim / practical / bounce`｜`hard light with a crisp shadow edge`｜`soft light wrapping the cheek`｜`key at 45° front-left, 45° high`｜`three stops under on the background`｜`light ratio 8:1`｜`halation blooming off the practical`｜`telecine lift in the blacks`｜`highlight roll-off at 0.98`｜`greenish fluorescent mix`｜`sodium 2200K pool`。

**禁**：`dramatic lighting`、`moody`、`chiaroscuro`（官方明示歧义）、`studio softbox`、`perfectly lit`。

## 八、术语密度检（新增机检项，直接减废片）

写进提示词专家审的前置 lint：

1. **每条提示词至少含 3 个本词典/词库内的术语**（景别/光/镜头/材质任选），少于 3 个 = 退回。
2. **零反例词**：出现第三节/七节「反例」列的词（cinematic/dramatic/moody/alive…）= 自动改写。
3. **术语与镜型匹配**：脸镜必须有 1 个表演微动作 + 1 个光位/光质词；空镜必须有 1 个材质词 + 1 个光源词；动作镜必须有 1 个物理链词（起势/发力/余势）。
4. **一条术语一个主体**：`shallow depth of field` 只能挂一个镜头，禁跨句重复堆叠。

## 九、待官方文档回填

以下术语的**模型侧可用性**正在等官方文档（Seedance/Kling/Hailuo/Runway/Veo/Wan...）回填：
- 哪些模型真正解析 `rack focus` / `split diopter` / 光比数值 / 焦段数值；
- 哪些模型把 `85mm` 当风格词而非光学词；
- 哪些模型支持 `frames 0-8 / 8-18` 这种帧级时序（当前只有 H3 判例支持时间戳写法）。

回填前：帧级时序只用于 H3 轨道；其他模型用「then / after / as」自然语言时序，不用帧号。

---
*执笔 bm-a 导演席 · 2026-10-20 · 与 prompt_lexicon.py 互补；新增四类=景深焦点/表演微动作/剪辑/年代器物；密度检进 gate*