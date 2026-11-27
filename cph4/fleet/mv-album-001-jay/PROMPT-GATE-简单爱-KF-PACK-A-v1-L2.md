# PROMPT-GATE-简单爱-KF-PACK-A-v1-L2 · 独立评审席 verdict（四块·2026-10-20）

> 审席=独立评审席（PROMPT-EXPERT-GATE·**禁自审自签**——本件只出 verdict，合并+复检+签发归导演席）。对象=`简单爱-KF-PACK-A-v1-DRAFT.md`（A 批 30 帧）+词面正身 `简单爱-shots-v2.py` `NEW` 元组（L68-178）。
> 依据=`PROMPT-EXPERT-GATE-v1` 十一面检查单（在册正身路径 `cph4/fleet/mv0001-handover/outbound/krea2/prompt-writing-spec-v1/PROMPT-EXPERT-GATE-v1.md`；**任务行文所指 `mv-album-001-jay/PROMPT-EXPERT-GATE-v1.md` 不存在**，本席按在册正身执行）+`QC-MASTER-CHECKLIST-v1` §7/§8/§9/§12（旁引 §17 胶片型号）+先例 `PROMPT-GATE-可爱女人-KF-PACK-A-v1-L2.md`/`-SIGN.md`。
> **裁定口径**：本席只判「执行细节 + 转录保真 + 词面是否承载设计意图」，不重裁场景/选角/批次划分。一切冲突以 py `NEW` 为准（零转录律）。
> **独立复核方式**：`python Tools\kf_pack_extract.py 简单爱-shots-v2.py` 实跑 + 自写只读比对脚本（落 `%TEMP%`，未改仓内任何文件）。机核结果：帧数 30／词数 min 96(T10)·max 188(T09)／t2i lint 30/30 CLEAN／NEW 时长合计 270.99s／REUSE 0 段／时间轴 0.00→270.99 逐段无缝（30 段首尾严丝合缝）。**与草稿逐格核对：window/dur/speed/light/tex/lens/words 八列全部一致**（唯一系统性差异见 F-10）。

## 〇、共享块与裁定执行面

| 共享块/项 | 判定 | 证据指针（词/行） |
|---|---|---|
| HIM 常量 | PASS | py L36-37 与草稿〇.1 逐字一致（`jman, `+`ID_M_2001_BONE`+`plain white short-sleeve shirt…scuffed canvas shoes`）；常量原文 `prompt_lexicon.py` L189-191 ✓ |
| HER 常量 | PASS | py L39-40 与草稿〇.2 逐字一致（`20-year-old East Asian woman…pleated skirt`）；与星晴/可爱女人/龙卷风互斥 ✓ |
| BIKE 常量 | **FIX** | py L41 定义逐字对，但**实挂仅 2 帧**（T02 L71、T25 L158）；T29/T30 为意译，且 T30 仅以 `the same old city model` 指代——t2i 无跨帧参照，同款律未闭合（F-3/F-9） |
| 官方尾段（kf 全额） | PASS（逐字） | py L44-50 `"Shot on %s, %s, %s, %s."`＋L33 `GRADE_2001=LX.GRADE["tw2001"]`＋L30 `STYLE_LEAD=…2001 Taiwanese music video`；草稿〇.4 重构串与实渲染同义 ✓（冷暖冲突见 F-13） |
| 光块（6 块） | PASS（块键）／**FIX（一处语义）** | py L23-28 六块全部实挂、无冗余；但 `day_back`（L24）内含 `placed behind the two figures, a two-stop bleed around their silhouettes`，被挂到零人物的 T29/T30（F-2） |
| 一歌一律（2001 透明日光） | PASS | 晴段 6200K 高调（`day_clear`）+ 雨段 6800K 青灰（`rain_soft`）+ 钠灯 2200K（`dusk_sodium`）三族分区清晰；`golden_rim` 2800K 回环段收在暖族 ✓ |
| 年限锚（2001 vs 龙卷风 2000） | PASS | `2001 Taipei lane`（L68）·`2001 telecine`（L33）·`2001 Taiwanese music video`（L30）三处一致；**py L32 注释「专辑年代=2000」为抄自龙卷风的残留注释**，与代码实际 2001 相反——草稿写 2001 是对的（勘误归 py，非草稿错） |
| 长期律（五档速度） | PASS | 相遇 1.05（T02/T03）/风与发丝 0.90（T06/T07）/日落静 0.85（T08/T09）/尾牵 0.88（T27/T28）/奔跑棒球 1.15（T12-T14）与草稿§〇.7 逐值一致 ✓ |
| 剧记忆钉·影子先牵手 | PASS | T10 真实的手先入画（L103）→T11 影子镜独立（L106），顺序「先物理后概念」未倒 ✓ |
| 剧记忆钉·积水写字 | **FIX** | T20 `one finger drawing three characters in the water`（L139）=要求模型生成汉字字形，撞 §9「禁 AI 生成文字」一票否决面（F-4） |
| 剧记忆钉·两代单车 | **FIX** | T29 `an old steel bicycle…rusted deep brown`（L172）/T30 `a second bicycle of the same old city model`（L175）——同款部件与“same”指涉均未落词（F-3） |
| `kf()` `.capitalize()` 副作用 | **FIX（表述）** | L47 实渲染把 `6200K→6200k`、`6800K→6800k`、`2200K→2200k`…**30/30 帧全中**；草稿§四.4「无专名，零影响」不实（F-10） |

## 一、B1=T01-07（场0 相遇 + 场0b 主歌1·7 帧）

| 帧 | verdict | 一句理由（证据指针） |
|---|---|---|
| T01 | PASS | 无人空巷；`an empty 2001 Taipei lane at mid-morning`（L68）·107 词·day_clear/film_day/35mm 与表一致·时间轴 0.00 起 ✓ |
| T02 | **FIX** | F-1：实渲染 `…scuffed canvas shoes pushing an old steel…bicycle along the lane`（L71，HIM 块 L36 与动作无句界）；BIKE 逐字挂载 ✓/158 词 |
| T03 | **FIX** | F-1：`…knee-length pleated skirt running into the lane…`（L76）→「裙子跑进巷口」 |
| T04 | **FIX** | F-1：`…pleated skirt catching her canvas shoe on a low stone step…`（L79）主语归属错；绊倒=动作链真实、非情绪标签（K1 合规）✓ |
| T05 | PASS | 手部镜免 ID（`his hand pressed flat against the seam of his trousers once before reaching out`，L82）·三件物质证据（蹭手/多停/掌心擦伤）全落词面 ✓ |
| T06 | **FIX** | F-1：`…pleated skirt standing up with her fingers hooked in his shirt cuff…`（L87） |
| T07 | **FIX** | F-5：HIM 未挂块（词面 `his forearm wiping the leather saddle`，L90）+F-1（HER 块 `…pleated skirt already side-saddle behind him`）——「他」无身份锚，跨帧脸型漂移风险 |

**B1 块面结论**：①主体保真 7/7②年代锚=巷口石板/半卷铁闸/旧钢单车/帆布鞋 ✓·无 AI 禁品③硬点=羞涩三态①（T06 抓袖口又放开）成立·T05 裤缝蹭手=减法治范本 ✓④工艺注=T05 手部镜合规⑤副作用=F-1 毁伤 6/7（仅 T05 无 ID 免伤）。**B1=PASS 2 / FIX 5 / REJECT 0**。

## 二、B2=T08-12（场2 日落 + 场3 副歌1 牵手·5 帧）

| 帧 | verdict | 一句理由（证据指针） |
|---|---|---|
| T08 | PASS | 剪影双人（`two figures sitting shoulder to shoulder…their long shadows`，L95）·无脸免 ID 判可（可爱女人剪影先例）·103 词 ✓ |
| T09 | **FIX** | F-1：双 ID 同句（`…pleated skirt's head dipping…canvas shoes's face just turning back`，L98）——两处所有格均落在衣物上；188 词=全包最长，是任何增补的天花板 |
| T10 | PASS | 手部镜免 ID（`his hand entering the frame from the left`，L103）·96 词为全包最短，与§四一致 ✓·先物理后概念第一环 |
| T11 | PASS | 纯影镜（`two long shadows…the real bodies cropped out above the frame line`，L106）·无人物实体，免 ID 正确 ✓ |
| T12 | **FIX** | F-6：note/§三「扣紧那一下=识别句拍点·拇指压一下」，词面仅 `two figures running hand in hand…away from the camera`（L109）——远景背影下拇指不可见，识别句拍点未落词面 |

**B2 块面结论**：①主体保真 5/5②年代锚=河堤混凝土/低日逆光 ✓③硬点=影子先牵手独立镜（堤面占幅由 `wide/high` 保证）成立·T10→T11 顺序正确④工艺注=T12 是副歌首切 1.15 速，节奏位对，但“扣紧”这一识别动作缺词⑤副作用=F-1 仅伤 T09。**B2=PASS 3 / FIX 2 / REJECT 0**。

## 三、B3=T13-22（棒球 + 雨段·10 帧）

| 帧 | verdict | 一句理由（证据指针） |
|---|---|---|
| T13 | **FIX** | F-1：实渲染 `…scuffed canvas shoes mid-pitch and …pleated skirt at the plate`（L114）——「鞋投球/裙击球」；177 词 |
| T14 | **FIX** | F-1：`…pleated skirt swinging the bat through empty air…`（L117）；笑场=可检测行为（非情绪词）✓ |
| T15 | **FIX** | F-1（`…canvas shoes holding a plain long umbrella tilted hard toward her`，L122）＋F-5（`her` 全帧无 HER 块）＋F-7（日雨段挂 `film_night` 5279） |
| T16 | **FIX** | F-7：`film_night`(5279) 用于日间暴雨 50mm 手部镜（L125），与 QC §17「5279 夜/5246 日」不符；手部镜本身合规 |
| T17 | **FIX** | F-5：`the two of them…both laughing`（L130）双主人物零 ID 块——本帧是全包唯一「两人同时正脸笑」的中近景，身份锚最该在 |
| T18 | **FIX** | F-1：`…pleated skirt sitting on a step…canvas shoes crouched beside her`（L133）——吉他/三根指头/耳根红的物质链在，主语错位；179 词 |
| T19 | **FIX** | F-1：`…canvas shoes walking alone…his reflection travelling with him`（L136）；`reflection` 触发鬼相四查「倒影第二脸」→帧审留位（非词面缺陷） |
| T20 | **FIX** | F-4：`one finger drawing three characters in the water`（L139）=AI 生成文字（§9 一票否决面/§19 字席制字）；F-1 同族 |
| T21 | PASS | 无人空镜（`a rain-washed embankment with shallow water`，L144）·mist 三帧之一与§四一致·104 词 ✓ |
| T22 | PASS | 静物（`a closed umbrella leaning against the concrete railing`，L147）·97 词=次短 ✓·关系静物残留成立 |

**B3 块面结论**：①主体保真 10/10②年代锚=土操场/木棒/旧窗/长柄伞 ✓·无手机/LED/碳纤③硬点=羞涩三态②（T18 三根指头）落词面·伞链 T15→T16→T22 同一把（`a plain long umbrella`→`the umbrella rim`→`a closed umbrella`）语义可接④工艺注=T20 是记忆钉唯一物质镜，但“写字”写法违规⑤副作用=F-1 毁伤 6/10；T21/T22 空镜两帧判 PASS。**B3=PASS 2 / FIX 8 / REJECT 0**。

## 四、B4=T23-30（尾段 + 两代单车·8 帧）

| 帧 | verdict | 一句理由（证据指针） |
|---|---|---|
| T23 | **FIX** | F-12：`sitting on the same embankment concrete`（L150）为 t2i 不可解的跨帧“same”，需以栏杆/铺装条纹等实体锚替代；无 ID 判可（逆光剪影） |
| T24 | PASS | 手部镜（`her palm resting flat on his chest, the cotton…creasing`，L153）·104 词·85mm 与表一致；**但本帧无脸**——正是 F-8 勘正的证据 |
| T25 | **FIX** | F-1（`…canvas shoes riding…bicycle away`，L158）＋F-5（`with her behind him` 无 HER 块）；160 词 |
| T26 | PASS | 无人（`the mouth of an old alley…a single sodium lamp switching on`，L161）·钠灯不校正 ✓·110 词 |
| T27 | **FIX** | F-1：`…pleated skirt reaching her hand out first…canvas shoes pausing half a beat`（L164）；178 词·羞涩三态③反转的设计位在 ✓ |
| T28 | PASS | 手部镜（`two hands laced together…thumbs pressing once`，L167）·109 词；F-14 冠词（`A extreme close-up`）；字帧=后期，词面零文字 ✓ |
| T29 | **FIX** | F-2：光块 `day_back` 写 `behind the two figures, a two-stop bleed around their silhouettes`（L24）而本帧**零人物**（L172）→冷暖/人影双真值源；F-3 BIKE 未回锚 |
| T30 | **FIX** | F-2 同（L175）；F-3 `the same old city model` + `beside the first` 均无跨帧参照；F-12 同族 |

**B4 块面结论**：①主体保真 8/8②年代锚=巷口钠灯/旧堤栏杆/单车铬泥瓦 ✓③硬点=愿望回环（T08↔T23 同景别同焦距）+两代单车（T29/T30 零人物）设计成立，但词面承载不足④工艺注=T28 十指相扣+字帧=识别句收口位 ✓⑤副作用=T24/T28 手部镜判 PASS，不因缺 ID 扣分。**B4=PASS 3 / FIX 5 / REJECT 0**。

## 五、汇总与 FIX 清单（最小改法）

**整包 verdict=FIX 级（结构性但不需重写设计）**：30 帧 **PASS 10 / FIX 20 / REJECT 0**。零起帧对抗、零概念注入、零整包否定词、零现代穿帮词。与龙卷风同源的 **F-1 句界病灶**（HIM/HER 名词块直连动作动词）命中 14 帧；本曲另有两处本包独有硬伤：**T20 要求模型写汉字**（§9 红面）、**T29/T30 光块写「两个人影」而画面零人物**（I1 硬冲突）。

| # | 位 | 最小改法（并入正身·不改设计） |
|---|---|---|
| F-1 | kf() L45 模板级（受益 14 帧：T02/T03/T04/T06/T07/T09/T13/T14/T15/T18/T19/T20/T25/T27） | subject 与动作之间加句界：`"A %s of %s. %s. …"`（句号断句，词数不变，lint 不变） |
| F-2 | T29/T30 | 光块串供修正：新增 `day_back_obj`＝`the low sun at 3200K placed behind the two bicycles, a two-stop bleed around their frames, the embankment wall catching the spill`，或帧内 `extra` 覆写「两人影」句（去 `the two figures/their silhouettes`） |
| F-3 | T29/T30 | 单车同款律回锚：T29 补 BIKE 部件（`chrome fenders, a wire front basket, a worn leather saddle`，锈蚀后仍可辨形制）；T30 以「同款部件清单+差异清单」写死（`the same chrome fenders and wire basket, its bell face clean, a faded red cord…`），删 `the same old city model`/`beside the first` 两处无参照指涉 |
| F-4 | T20 | 文字脱险（§9/§19）：`one finger drawing three characters in the water`→`one finger tracing three short strokes into the water, the marks already illegible and closing over`；“简单爱”三字由**字席后期合成**（PNG），不入 t2i 提示词 |
| F-5 | T07/T15/T17/T25 | 身份锚补挂：T07 补 HIM 块；T15 补 HER 块；T17 补 HIM+HER 双块；T25 补 HER 块。词数预算：T07 131→179；T15 143→175；T17 110→**190**（距 200 仅 10 词，须复验）；T25 160→192（须复验） |
| F-6 | T12 | 识别句拍点落词面：补 `his thumb pressing once into the back of her hand`（note 有·词面无），或把景别从 wide 收到 med 使手部可读（改景别属设计，候导演席） |
| F-7 | T15/T16/T17 | 胶片型号/时段对齐（QC §17）：日间暴雨段挂 `film_night`(5279) → 二选一：改 `tex="film_day"`(5246)，或把场次明确改为「入夜暴雨」（改设定，候导演席）。**本席不擅改，标待裁** |
| F-8 | §四.2 | 勘正：`A 批含她 85mm 近景（T09 磕肩、T24 手放胸口），全脸已在包内`——**T24 是手放胸口特写，kf 无脸**（L153 全文无 face/head），“全脸已在包内”不能以此为据；应以 T14/T18/T27 的中景正脸计，并补一句「85mm 全脸近景仍未覆盖」 |
| F-9 | §〇.3 | 勘正：BIKE「逐字」实挂 **T02/T25 两帧**；T29/T30 为意译（待 F-3 回锚后才算逐字） |
| F-10 | §〇.4 / §四.4 | `.capitalize()` 表述：`无专名，零影响`→`K 值单位被降格（6200K→6200k 等，30/30 帧命中），语义可读，属模板级同态，本轮不改模板` |
| F-11 | §一 表头 | 补数据 provenance：py 头注（L3-6）明载 `resnap cut0/cut1 在 #1-#34 与词行错位（#34 单窗 106.31-150.84=44.5s）＝已知坏行区`，本表窗口实为 `t0_used/t1_used` 重导而非词行 cut 原值；草稿零披露＝读者会误以为窗口=词行原值（QC §15 词级锚点面） |
| F-12 | T23/T29/T30 | 跨帧“same”清理：改用可独立成像的实体锚（同一段栏杆形制/铺装条纹/堤墙高度），与 F-3 一并落 |
| F-13 | 全包尾段（A/B 裁定） | **建议 A**：KF 面本地覆写中性版尾段（理由同龙卷风 F-13；本曲冲突度较低但仍与 i2v 尾段不一致）。替换串：`Shot on <lens>, 2001 telecine grade, skin tones natural and unlit under the daylight, black point lifted to 10-14 code with the toe intact, restrained practical bloom, slight color bleed, <texture>, as a film still from a 2001 Taiwanese music video`。词数 +9/帧：max 188(T09)→197 <200 ✓（仅 3 词余量，烧制侧词数必检） |
| F-14 | T28 | 冠词：`A extreme close-up`→`An extreme close-up`（模板 `A %s` 对元音首词失效） |

**§五.1 的 A/B 裁定建议：选 A（同龙卷风同批）**。
① 本曲「透明日光」对 `warm skin tones` 的容忍度高于龙卷风，但**雨段（T15-T17 青灰）与钠灯段（T26-T28）**仍与该尾句相斥；
② 决定性理由与龙卷风相同：**KF 是 i2v 首帧**，本曲 py L53 `I2V_TAIL` 已写 `skin tones kept natural and unlit`，KF 若仍暖则同一镜起帧与尾句自相矛盾（D1）；
③ 两曲同批统一覆写，避免调色站对同一批做两套冷暖补偿（QC §16「全片单一 grade」精神）。
若导演席坚持 B 案，须同时给出「KF 暖偏可被调色站定量回收」的证据（现无），否则本席不建议。

**移交注记（不阻塞 A 批）**
① **QC §10 光句五槽**：本包 6 块中仅 `golden_rim`（L25）含相机相对方位词（`from camera left`）+K+比值；`day_clear` 有比值 3:1 但与相机方位缺位；其余 4 块无方位/无比值/无灯具尺寸距离——按 §10 v1.10/v1.12 属退稿级。归**摄影指导席/灯光席**，不在本审授权面（任务依据=§7/§8/§9/§12），故不列 FIX，**移交灯光席另开**。
② py L32 注释「专辑年代=2000」为抄自龙卷风的残留（本曲实际 2001，代码与草稿均正确）→ 建议 py 注释勘误，不影响词面。
③ T26 note `暖橙只落在口那里` 为 py 原文笔误（疑为「灯下」），草稿逐字照抄=零转录合规，但建议加勘误注，避免装配站照字面理解。
④ T19 倒影（`his reflection travelling with him`）触发鬼相四查「倒影第二脸」——帧审留位，非词面缺陷。
⑤ T09（188 词）为全包词数天花板，F-5/F-13 的增补均须逐帧复验 <200。

**本审边界**：禁 git 提交、禁改草稿/正身、禁烧制、禁签发。本件=verdict 留档；无 verdict 派单=烧制侧拒收（QC §12 v1.2）。本席不改一个词，所有改法均以“待并入”形式给出。

---

**分权署名**：**审=独立评审席（本件）**，**复检+签=导演席（bm-a），本席不签**。抽点复检建议（供导演席）：①T29/T30 光块是否仍含 `the two figures`（py L24 + L172/L175，本审核心证据）②T20 是否仍为 `three characters`（L139）③BIKE 命中是否仅 T02/T25（L41 vs 全表）④`.capitalize()` 是否把 `6200K` 降为 `6200k`（L47，实渲染可验）。

*证据=`简单爱-shots-v2.py`（NEW L68-178/REUSE L181/FILM_END L183/kf() L44-50/常量 L23-41/头注 L3-6）/`简单爱-KF-PACK-A-v1-DRAFT.md` §〇-§四/`_kf_simplelove.json|md`（已独立复跑，结论一致）/`prompt_lexicon.py` L84-116·L189-191/PROMPT-EXPERT-GATE-v1 十一面/QC-MASTER-CHECKLIST §7-§9·§12·§15·§17*