# PROMPT-GATE-龙卷风-KF-PACK-A-v1-L2 · 独立评审席 verdict（四块·2026-10-20）

> 审席=独立评审席（PROMPT-EXPERT-GATE·**禁自审自签**——本件只出 verdict，合并+复检+签发归导演席）。对象=`龙卷风-KF-PACK-A-v1-DRAFT.md`（A 批 29 帧）+词面正身 `龙卷风-shots-v2.py` `NEW` 元组（L65-169）。
> 依据=`PROMPT-EXPERT-GATE-v1` 十一面检查单（在册正身路径 `cph4/fleet/mv0001-handover/outbound/krea2/prompt-writing-spec-v1/PROMPT-EXPERT-GATE-v1.md`；**任务行文所指 `mv-album-001-jay/PROMPT-EXPERT-GATE-v1.md` 不存在**，本席按在册正身执行）+`QC-MASTER-CHECKLIST-v1` §7/§8/§9/§12（旁引 §17 胶片型号）+先例 `PROMPT-GATE-可爱女人-KF-PACK-A-v1-L2.md`/`-SIGN.md`（格式与裁定口径）。
> **裁定口径**：本席只判「执行细节 + 转录保真 + 词面是否承载设计意图」，不重裁场景/选角/批次划分（导演席权）。一切冲突以 py `NEW` 为准（零转录律）。
> **独立复核方式**：`python Tools/kf_pack_extract.py 龙卷风-shots-v2.py` 实跑 + 自写只读比对脚本（落 `%TEMP%`，未改仓内任何文件）。机核结果：帧数 29／词数 min 89(T15)·max 172(T18)／t2i lint 29/29 CLEAN／NEW 时长合计 230.83s／REUSE 6 段合计 19.53s／时间轴 0.00→250.36 零缺口零叠窗。**与草稿逐格核对：window/dur/speed/light/tex/lens/words 八列全部一致**（唯一系统性差异见 F-11）。

## 〇、共享块与裁定执行面

| 共享块/项 | 判定 | 证据指针（词/行） |
|---|---|---|
| HIM 常量 | PASS | py L34-35 `HIM = ("jman, " + LX.ID_M_2001_BONE + ", in a charcoal grey wool crewneck sweater…")`；与草稿〇.1 逐字一致；`ID_M_2001_BONE` 原文=`prompt_lexicon.py` L189-191（heavy-lidded monolid eyes…visible pores）✓ |
| HER 常量 | PASS | py L37-38 与草稿〇.2 逐字一致；`24-year-old Taiwanese woman…cream knit top`；与星晴/可爱女人/简单爱块互斥 ✓ |
| 官方尾段（kf 全额） | PASS（逐字） | py L41-47 `"Shot on %s, %s, %s, %s."`＋L31 `GRADE_2000=LX.GRADE["tw2001"].replace("2001 telecine","2000 telecine")`＋L28 `STYLE_LEAD=…2000 Taiwanese music video`；草稿〇.3 重构串与实渲染完全同义 ✓（但冷暖冲突见 F-13） |
| 光块（定义 7／实挂 6） | **FIX** | py L20-26 定义 7 块；`window_rain`（L26）在 29 帧词面 **0 命中**（比对脚本 light counts 仅 6 键）→ 草稿〇.4「本曲自建 7 块」与 §四「6 键分布」自相矛盾（F-8） |
| 一歌一律（全专最冷色） | PASS | 5600K/6200K 冷主导 + `her_warm` 2200K 唯一暖点（L23）；15 日/13 夜/1 mist 的冷调自洽 |
| 双速对撞 | PASS | 现实线 0.82-0.95（T15 .84/T16 .82/T03 .85…）／闪回线 1.10-1.25（T10 1.25/T08 1.20/T13 1.15…）与草稿长期律逐值一致 |
| 剧记忆钉·相框 | PASS（三段落位） | T01 `an overturned wooden picture frame lying face-down`（L65）→T23 `the paint two stops paler in a tall rectangle`（L143）→T29 `the pale rectangle on the wall`（L165） |
| 剧记忆钉·钟 | **FIX** | 全包仅 T01 有 `clock`（L65 `a stopped mechanical wall clock hanging crooked`）；T29 note 写「钟并肩物证」但词面零钟（F-6） |
| 剧记忆钉·两把椅子 | **FIX** | T09 词面 `left standing where it has drifted`（L91）与「空椅全程不动」直接冲突（F-3） |
| `kf()` `.capitalize()` 副作用 | **FIX（表述）** | L44 `LX.LIGHT[light].capitalize()` 实渲染把 `6200K→6200k`、`5600K→5600k`…**29/29 帧全中**；草稿〇.2/§五.2「无专名，零影响」不实（F-11） |

## 一、B1=T01-09（场0 前奏 + 场1 A 段·9 帧）

| 帧 | verdict | 一句理由（证据指针） |
|---|---|---|
| T01 | PASS | 无人镜；`a stopped mechanical wall clock hanging crooked`=钟的唯一埋点（L65）·109 词·24mm/high/room_grey/film_day 与表一致·REUSE 起段对账 0.00 起 ✓ |
| T02 | PASS | 无人镜；`the paint two stops paler in a tall rectangle`（L68）可拍可测·102 词·与 T23/T29 同景别同焦距（50/eye）✓ |
| T03 | **FIX** | F-1 句界：实渲染 `…bare feet on the wooden floor sitting on the floor at the centre…`（HIM 块 L34 与动作无标点）→「地板坐着」 |
| T04 | **FIX** | F-4：note「拇指停在她的脸那格」，词面仅 `one thumb coming to rest on one corner of the photograph`（L76）——设计意图未落词；F-7：T01 `face-down` 与「擦玻璃」互斥，缺翻面动作 |
| T05 | **FIX** | F-1：实渲染 `…plain cream knit top turning her head…`（HER 块 L37+动作）；135 词·85mm/her_warm 与表一致 |
| T06 | PASS | 无人镜；`the sheet still holding the shallow shape of someone who left`（L82）·REUSE T06 0.83s 补窗与 §二对账一致 ✓ |
| T07 | **FIX** | F-1：`…cream knit top reaching up to brush ash…`；且 HER+HIM 双块同句零分隔（L85），主语归属可漂 |
| T08 | **FIX** | F-14 冠词：实渲染 `A extreme wide establishing shot…`（ext 首元音，模板写死 "A %s"，L42）；词面本体 `low black cloud…two small figures far below` 判可（超现实有物理轨迹） |
| T09 | **FIX** | F-1：`…wooden floor sliding one wooden chair back…`；F-3：`left standing where it has drifted`（L91）与草稿§三「空椅全程不动」冲突 |

**B1 块面结论**：①主体保真 9/9（无改词）②年代锚=2000 Taipei 房间/机械钟/木框/碎玻璃 ✓·无 AI 禁品③硬点=相框埋点+T01 钟 ✓ 但 F-1 句界污染 4/9 帧④工艺注=T15/T16 手部镜免 ID 合规（可爱女人 KN01 先例）⑤副作用=REUSE T05/T06 两段 0.83s 定格与时间轴严丝合缝 ✓。**B1=PASS 4 / FIX 5 / REJECT 0**。

## 二、B2=T10-17（场2 副歌1 + 场3 C 段·8 帧）

| 帧 | verdict | 一句理由（证据指针） |
|---|---|---|
| T10 | PASS | 无人街景；`rain striking a narrow 2000 Taipei street almost horizontally`（L96）·99 词·1.25 速=全包最快，与双速律一致 ✓（伞链待证见移交） |
| T11 | **FIX** | F-2 双真值源：主体句 `the only warm light left in the frame`（L99）vs 光块 `storm_lead` 5600K 冷（L22），`her_warm` 未挂→冷暖同帧竞争（C1/I1 判例族） |
| T12 | PASS | 纯剪影（`two silhouettes running hand in hand`，L102）·无脸免 ID 合规·1.10 速 ✓ |
| T13 | **FIX** | F-5：note「腕上勒痕一帧」，词面只有 `the grip a beat too tight`（L105）——勒痕未落词；F-14 冠词 `A extreme close-up` |
| T14 | **FIX** | F-1：`…wooden floor lifting his eyes…`；单硬光低位/85mm/1.15 夜段设计位在位（L110） |
| T15 | PASS | 手部镜免 ID（`his hands moving over a small pile of objects`，L115）·89 词=全包最短与 §四一致 ✓ |
| T16 | **FIX** | F-7：`laying the wooden frame face-down on the table`（L118）与 T04「擦玻璃」之间缺翻面；“手空了才停”的行为链本身合规（§11 动作因果） |
| T17 | **FIX** | F-1：`…wooden floor sitting on the floor…`；F-12：词面 `the same room`（L121）为 t2i 不可解的跨帧指涉，且草稿§三「与 T01 同机位」不成立（T01 wide/high/24mm vs 本帧 wide/eye/35mm） |

**B2 块面结论**：①主体保真 8/8②年代锚=2000 Taipei 街/瓦楞雨棚/旧木椅 ✓③硬点=副歌1 双速爆发+静一拍插入（T14）成立·T11「唯一暖点 L1 可读锚」设计在册但词面未挂暖光块（F-2）④工艺注=T15/T16 手部镜合规⑤副作用=非 ID 帧（T10/T12/T15）判 PASS，不作无差别加块。**B2=PASS 3 / FIX 5 / REJECT 0**。

## 三、B3=T18-23（场4 副歌2 + 场5 尾奏1·6 帧）

| 帧 | verdict | 一句理由（证据指针） |
|---|---|---|
| T18 | **FIX** | F-1：双 ID 同句（`…knit top brushing ash from …wooden floor's shoulder again`，L126）；172 词=全包最长，任何增补须复验 <200 |
| T19 | **FIX** | F-1：`…cream knit top half turned away…`（L129）；`a stop cooler`＋`face turned away from the lens` 与暖残光递减链自洽 ✓ |
| T20 | **FIX** | F-1；F-7：`one empty wooden frame lying face-down`（L132）——照片何时取出全包无镜，空框状态突现（帧间守恒 F1） |
| T21 | **FIX** | F-1：`…wooden floor at an old upright piano…`（L137）名词短语直粘地点状语；`the keys still level`=先思后唱律的酝酿态 ✓（QC §5 v1.1） |
| T22 | **FIX** | F-1：`…wooden floor drawing the heavy curtains open…`（L140）→「地板拉窗帘」 |
| T23 | **FIX** | F-1 最重：实渲染 `…bare feet on the wooden floor's raised palm stopping in the air…`（L143）——所有格落在“地板”上，主体丢失；此处为 v2.2「唯一指路」硬点，必须修 |

**B3 块面结论**：①主体保真 6/6②年代锚=旧立式钢琴（漆面磨损）/白昼墙面/相框色差 ✓③硬点=暖残光递减（T19 `a stop cooler`）+越侧越背（`face turned away`）成立·T23 手指悬停=留白 ✓ 但句界毁伤 6/6④工艺注=T21→T24 构成「手未落键（思考位）→窗前出声位」链，先思后唱律 PASS⑤副作用=T23 的 patch_light 与 T02/T29 同块同景别，三帧对位可用。**B3=PASS 0 / FIX 6 / REJECT 0**。

## 四、B4=T24-29（场6 尾段副歌 + 场7 Outro·6 帧）

| 帧 | verdict | 一句理由（证据指针） |
|---|---|---|
| T24 | **FIX** | F-1：`…wooden floor standing at the opened window…`（L148）；背影+肩线=演唱锚②最静处理，与副歌1 反向 ✓ |
| T25 | **FIX** | F-1：`…cream knit top turned back for one last look…`（L151）；`only the near half of her face still readable` 与§三「唯一半张脸」自洽 ✓ |
| T26 | **FIX** | F-1：`…cream knit top standing far down the rain-washed street…`（L156） |
| T27 | PASS | 无人镜（`only the faint outline of a figure left standing in the white haze`，L159）·mist 全包唯一命中与 §四一致·98 词 ✓ |
| T28 | **FIX** | F-1：`…wooden floor pressing the old aluminium window fully open…`（L162）；`old aluminium window`=2000 年代正向锚 ✓ |
| T29 | **FIX** | F-1（L165）；F-6：note「钟并肩物证」而词面零钟；F-12：`the pale rectangle` 为跨帧指涉，需以“同墙同高同宽度”具体锚替代 |

**B4 块面结论**：①主体保真 6/6②年代锚=旧铝窗/门框/白墙 ✓③硬点=首尾对位（T01 狼藉 24mm 高角↔T29 50mm 收黑）成立·T29 尾窗 250.36=FILM_END 实证 ✓④尾段「你」渐弱蒙太奇 T26/T27 冷暖二段成立⑤副作用=F-1 毁伤 5/6，T27 因无人免伤。**B4=PASS 1 / FIX 5 / REJECT 0**。

## 五、汇总与 FIX 清单（最小改法）

**整包 verdict=FIX 级（结构性但不需重写设计）**：29 帧 **PASS 9 / FIX 20 / REJECT 0**。零起帧对抗、零概念注入、零整包否定词；核心病灶=**kf 模板 `A %s of %s, %s.` 把 HIM/HER 名词块与动作动词直接相连，无句界**，导致 18 帧主体归属错位（T23 已到 `the wooden floor's raised palm` 的毁伤级）。这是机核（lint/词数/块键）永远抓不到的语义面缺陷，正是本闸存在的理由。

| # | 位 | 最小改法（并入正身·不改设计） |
|---|---|---|
| F-1 | kf() L42 模板级（受益 18 帧：T03/T05/T07/T09/T11/T14/T17/T18/T19/T20/T21/T22/T23/T24/T25/T26/T28/T29） | subject 与动作之间加句界：`kf()` 改为 `"A %s of %s. %s. …"`，或调用侧 subject 后补 `", "`。首选模板改 `"%s of %s, %s."`→`"%s of %s. %s."`（句号断句，词数不变，lint 不变） |
| F-2 | T11 | 光/词双真值源消解：挂 `her_warm` 或把 `the only warm light left in the frame` 改为光染物色句 `a warm band held on her cheek, the storm staying cold around her`（C1 写法） |
| F-3 | T09 | `left standing where it has drifted`→`left standing exactly where it was, untouched`（对齐§三「空椅全程不动」） |
| F-4 | T04 | `on one corner of the photograph`→`on the corner where her face is`（note 意图落词面） |
| F-5 | T13 | 补 `a red pressure line across her wrist`（note「腕上勒痕」落词面），替换 `the grip a beat too tight` |
| F-6 | T01/T29 | 钟链闭链：T01 写死读数 `its hands stopped at ten past four`；T29 补 `the stopped clock now standing level on the shelf, its hands still at ten past four`（对齐剧本「场7 扶正上弦」+§三「读数一致」） |
| F-7 | T04/T16/T20 | 相框状态链：T04 补 `turning the frame face-up in his hands`；T20 把 `one empty wooden frame` 改为 `the frame lying face-down, the photograph already slipped out beside it`（照片取出有物证） |
| F-8 | 〇.4 / 光块表 | `window_rain` 标「定义未用·预留」或删除；「自建 7 块」改「定义 7·实挂 6」 |
| F-9 | §四 自检表 | 纹理分布 `film_day 17 / film_night 10 / mist 1`→**15 / 13 / 1**（机核实查；原数合计 28≠29，本身即自证错） |
| F-10 | §五.4 | 她帧数 `4 帧（T05/T07/T18/T19）`→**7 帧（T05/T07/T11/T18/T19/T25/T26）**；「均为侧/背/远景，无全脸近景」不成立——T05 为 85mm CU 回头（`turning her head`），B 批必要性须按 7 帧重估 |
| F-11 | 〇.2 / §五.2 | `.capitalize()` 副作用表述：`无专名，零影响`→`K 值单位被降格（6200K→6200k，29/29 帧命中），语义可读，属模板级同态，本轮不改模板`（与可爱女人 SIGN 注 3 口径一致） |
| F-12 | T17/T18/T20/T29 | t2i 跨帧指涉清理：`the same room`/`again`/`the pale rectangle` 改为可独立成立的实体描述（同墙同高同宽度、同一块浅方形），避免无参照的“same” |
| F-13 | 全包尾段（A/B 裁定） | **建议 A**：KF 面本地覆写冷版尾段。理由见下节；替换串见下 |
| F-14 | T08/T13 | 冠词：`A extreme…`→`An extreme…`（模板 `A %s` 对元音首词失效，2 帧） |

**§五.1 的 A/B 裁定建议（本席意见，决定权在导演席）：选 A（KF 面本地覆写冷版尾段）。** 四条证据：
1. **不是审美偏好而是在册缺陷**：QC §10 v1.10 明文「夜戏禁无条件挂 `warm skin tones`」，并把 XQ26「亮脸复发」的成因直接指为「无测光点 + 尾句 `warm skin tones` 隐形补光」。本曲 13 夜帧 + 全片冷律，正撞此条。
2. **C1/I1 双真值源**：`storm_lead 5600K / room_grey 6200K` 与 `warm skin tones` 竞争同一“肤色”属性槽——按 C1 判例族，模型会掷骰子。这属提示词面缺陷，调色站救不回被模型先烘进脸的暖偏与 bloom。
3. **KF 是 i2v 的首帧**：本曲 py L50 `I2V_TAIL` 已改为 `Cold 2000 Taiwanese telecine grade, skin tones kept natural and unlit…`。若 KF 仍暖、i2v 尾段已冷，同一镜的起帧与尾句互相打架（D1 起帧主导律的直接风险）。
4. **B 案不可逆的部分**：halation/bloom 与肤色暖偏是像素级烘焙，后级只能压不能还；而 A 案成本仅为“重跑 lint+词数”。
替换串（建议）：`Shot on <lens>, 2000 telecine grade, cold neutral skin left unlit, black point lifted to 10-14 code with the toe intact, restrained practical bloom, slight color bleed, <texture>, as a film still from a 2000 Taiwanese music video`。词数影响：+9 词/帧，全包 max 172→181（T18）<200 ✓；须重跑 t2i lint。

**移交注记（不阻塞 A 批）**
① **QC §10 光句五槽（SOURCE→DIRECTION→QUALITY→RATIO→KELVIN + 灯具尺寸/距离）**：本包 7 块均无「相机相对方位词」，`her_warm`/`day_white`/`window_rain` 无 K 值或无比值，`patch_light` 无 K——按 §10 v1.10/v1.12 属退稿级。该条归**摄影指导席/灯光席**执法，不在本审授权面（任务给的依据是 §7/§8/§9/§12），故不列 FIX，**移交灯光席另开**。
② T10 `a folded umbrella jammed against a wall` → T11 `an umbrella turned inside out` 是否同一把，词面无交代；候导演席或道具席定（伞链物证）。
③ T21 note「2.5s 实拍位 5s 源」与窗 5.00s/速 0.86（源 5.81s）算术不合，note 语义待证（非草稿转录错，py 原文如此）。
④ REUSE T25 定格 7.88s 为全包最长定格，QC §5「5 秒等长判负」不直接适用（定格非等长镜），但长定格观感须帧审兜底。
⑤ py 文件头 L3「专辑年代=2000」与 L31 覆写一致（《Jay》2000 正确），无冲突。

**本审边界**：禁 git 提交、禁改草稿/正身、禁烧制、禁签发。本件=verdict 留档；无 verdict 派单=烧制侧拒收（QC §12 v1.2）。本席不改一个词，所有改法均以“待并入”形式给出。

---

**分权署名**：**审=独立评审席（本件）**，**复检+签=导演席（bm-a），本席不签**。抽点复检建议（供导演席）：①实渲染 T23 是否仍为 `the wooden floor's raised palm`（py L143，本审核心证据）②`window_rain` 是否 0 命中（py L26 vs 29 帧）③纹理分布 15/13/1（比对脚本 tex counts）④她帧是否 7 帧（HER 命中 T05/T07/T11/T18/T19/T25/T26）。

*证据=`龙卷风-shots-v2.py`（NEW L65-169/REUSE L171-178/FILM_END L180/kf() L41-47/常量 L20-38）/`龙卷风-KF-PACK-A-v1-DRAFT.md` §〇-§五/`_kf_tornado.json|md`（已独立复跑，结论一致）/`prompt_lexicon.py` L84-116·L189-191/PROMPT-EXPERT-GATE-v1 十一面/QC-MASTER-CHECKLIST §7-§9·§12·§17*