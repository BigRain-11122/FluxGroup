# 立意→关键词转译法 v1（2026-10-20·CEO 令「立意很好，但关键词怎么写，如何让AI准确的执行」）

> 定位：**补闸不管的那一段**。`PROMPT-EXPERT-GATE-v1` 管「提示词别写错」（十一面：否定词/双真值源/起帧对抗…）；本件管「立意怎么变成模型真能执行的关键词」，以及**烧完怎么证明它真执行了**。
> 铁律一句：**AI 不执行立意，只执行可见证据。** 停留在"单恋的距离感"这种层面的词，模型只能自由发挥——这就是"立意很好、画面不对"的根因。

## 一、立意衰减的三层（为什么好想法拍不出来）

```
立意（创作层·永不进提示词）
  → 场面事实（谁·在哪·做什么）        ← 90% 的人停在这一层就开写
  → 可见证据（光/物/动作/构图 至少 2 项，摄影机能拍到）
  → 词面（具体名词+动作动词+光向色温+媒介声明）
```

每往下掉一层，模型自由发挥的空间就翻倍。**跳过第三层直接写词面=把导演的工作交给模型**。

## 二、转译四步（每镜一次，写进镜卡）

| 步 | 产出 | 判据 |
|---|---|---|
| ① 立意 | 一句话（只给自己看） | 提问："这一镜观众该感觉到什么" |
| ② 场面事实 | 谁·在哪·做什么 | 三个要素缺一=不算事实 |
| ③ 可见证据 | 光/物/动作/构图，**≥2 项** | 每项都能被摄影机/测光表拍到 |
| ④ 词面 | 见 §三 配比 | 每个名词都能回答"AI 会画出什么" |

## 三、词面配比与顺序（权重即顺序）

**主体 40% → 动作/表演 25% → 光 20% → 环境/时代 10% → 媒介 5%**

- 主体放最前（官方：最重要的一律先写），主体块必须是全段最长块。
- 动作写**动词+身体部位**（`his thumb rests on the key without pressing`），不写情绪。
- 光写**方向+色温+质感**（`late side light from the right, warm and low, raking across the paper grain`），不写"氛围感"。
- 媒介声明必须独立成立（`live-action 35mm film frame`）——防媒介漂移。

## 四、具体性四级标尺（写到第几级，AI 就补到第几级）

| 级 | 写法 | 结果 |
|---|---|---|
| L1 品类 | `an old bicycle` | AI 自己发明形制（穿越高发） |
| L2 形制 | `an old single-speed steel bicycle` | 大致对，细节随机 |
| L3 部件 | `single-speed steel frame, chrome fenders, wire basket` | 可控 |
| L4 状态痕迹 | `+ the bell's thumb pad polished bright, the basket wire bent inward once` | **有生活**（本季最缺的一级） |

**规则：主角物件与关键道具必须写到 L3/L4；背景物件 L2 即可**（否则提示词过长，模型会漏）。

## 五、执行契约卡（每镜一张·烧后逐条打勾）

```
镜号：KN-A1
意图（不进词面）：他每天都在叠同一架飞机
必须出现（3）：①一排 6-8 架泛黄卷边旧纸机 ②手里那架素白锐利 ③右侧低位暖光扫过纸纹
必须不出现（2）：①现代卡纸光泽 ②任何人物正脸
可判失败点：纸机数量 <4 / 新旧无对比 / 光从正面平打
```

- 烧完逐条打勾 → **执行准确率 = 打勾数 / 必须出现数**。
- 新包试烧先算这个数：<2/3 不许进批量（批量放大错误=成本最贵的错）。
- 契约卡随镜入库，成片闸抽检回收（复发=该镜重写提示词，不是重摇碰运气）。

## 六、两个真实镜的完整示范（立意→词面）

### 例 1｜可爱女人 A 段「每天每天想着你」

- 立意：思念是重复劳动
- 事实：傍晚天台，他在叠纸飞机，窗台上一排旧的
- 证据：①旧纸机一排（泛黄/卷边/一架翼塌）②手里新的素白锐利 ③右后方低位暖光扫纸纹
- KF 词面（Krea2）：
  `seven aged paper airplanes lined along a concrete water-tower ledge, edges yellowed and soft, wings curled, one crumpled flat; in the foreground a fresh white paper airplane held between two fingers, crisp sharp creases; late afternoon side light from the right, low and warm, raking across the paper grain and casting short shadows on the concrete; live-action 35mm film frame, shallow depth of field, 2001 Taiwan rooftop`
- i2v 词面（H3/Seedance）：
  `The camera holds a locked-off tripod frame. His fingers press the last crease flat, then set the new plane at the end of the row; the row does not move. Wind lifts one old wing a few millimetres and lets it settle. He does not look up.`
- 为什么这样写：**没有出现"思念""每天""孤独"任何一个词**——全部由"一排旧的 + 一架新的 + 风掀一下"承担。观众自己读出重复。

### 例 2｜星晴 C2「它一定实现」

- 立意：把散落的星连起来，是人在许愿
- 事实：夜里，他抬手用食指逐颗点星
- 证据：①手指从画面下缘入画 ②星不移动 ③嘴型无声数数 ④靛蓝夜空+星光勾指缘
- i2v 词面：
  `His hand enters from the lower frame edge, index finger extended, settling on one star, then moving to the next; the stars hold still. His mouth shapes a count without sound. Indigo night sky, starlight rim along the finger. The camera holds a locked-off tripod frame.`
- 关键：**"连线"这个词不写**——写"手指逐颗移动"，星不动，连线的错觉由观众的眼睛完成。

## 七、反例五对（左=立意式无效写法，右=可执行写法）

| 无效 | 可执行 |
|---|---|
| `a sense of loneliness` | `one chair left pulled out at the table, the other pushed in` |
| `time passing` | `the same window light, now raking at a steeper angle; the casing worn pale where the thumb rests` |
| `she is waiting for him` | `she sits on the step, both shoe toes aimed at the alley mouth, her umbrella still folded` |
| `he is reluctant` | `his thumb rests on the key without pressing; the shoulder drops only after the reel starts` |
| `cinematic, dreamy` | `sodium streetlight from behind at frame right, halation on the rim, fine 35mm grain` |

## 八、模型分轨（只引不重写）

- Krea2（KF）：八块序、权重 3-5 条、零否定（否定词会注入概念）→ `PROMPT-SPEC.md`
- H3（云端 i2v）：三字段结构化长文、需时间戳切镜、微表情是官方强项 → 同上 §四
- Seedance：中文八要素 60-100 词、**单镜单运镜**、禁精确秒数、防崩尾句逐字用官方口径 → 同上
- 跨模型禁套用（Seedance 禁秒数 vs H3 要时间戳，是两套语法）

## 九、判定与落闸

- 提示词专家审新增一条前置：**镜卡四步齐全 + 执行契约卡在场**（缺=退回，不进十一面审）。
- 执行准确率 <2/3 的包不进批量；连续两包 <2/3 = 对标尺本身复盘（不是继续重摇）。
- 成片闸回收契约卡打勾结果，与 QC §12 lint 结果并列记账。

---
*执笔 bm-a 导演席 · 2026-10-20 · 与 PROMPT-EXPERT-GATE（查错）分工：本件管"从立意生成关键词"与"执行是否命中"；每镜示范可直接抄用*