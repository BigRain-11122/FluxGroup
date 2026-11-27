# 简单爱-KF-PACK-A-v1-DRAFT（A 批 30 帧·bm-c 烧制用稿）

> **状态=草稿·未过闸·禁烧**。过闸链未走完：独立评审席 verdict（待出）→ 导演席合并复检签发（待）→ 才可点火。无 verdict 派单=烧制侧拒收（QC §12 v1.2）。
> **权威=简单爱-shots-v2.py**（词面正身·v2.0）。本稿按词面机核抽取，不改一个词；冲突以 py 为准（零转录律）。
> **机器提取口径**：`python Tools/kf_pack_extract.py cph4/fleet/mv-album-001-jay/简单爱-shots-v2.py`。原始输出=同目录 `_kf_simplelove.json` / `_kf_simplelove.md`。

## 〇、共享词块（每帧装配时套用）

1. **男主 ID 块（HIM·逐字）**：`jman, a 20-year-old Taiwanese student with heavy-lidded monolid eyes, a thick lower lip, softly rounded cheeks, a flat round nose tip, a blunt rounded jaw and natural unretouched skin with visible pores, in a plain white short-sleeve shirt with the collar open, straight dark trousers, scuffed canvas shoes`
   - `jman LoRA` strength **0.6**（影射档）；ID 体=`prompt_lexicon.ID_M_2001_BONE` 同源，禁本地改字。
2. **女主 ID 块（HER·逐字·禁跨曲复用）**：`a 20-year-old East Asian woman with a soft round face and clear dark eyes, shoulder-length black hair tucked behind one ear, in a pale blue cotton blouse and a knee-length pleated skirt`
   - 选角律=CASTING-LAW：日系清纯邻家·气质优先于国籍·禁冷感御姐向/浓妆；与星晴/可爱女人/龙卷风 ID 块互斥。
3. **物件锚（BIKE·逐字块）**：`an old steel single-speed city bicycle with chrome fenders, a wire front basket and a worn leather saddle`
   - **挂载实况（勘正）**：逐字挂载仅 **T02 / T25** 两帧；T03/T06/T07 等只以「车座/后座」等局部指称出现，T29/T30 为**另写的两代车描述**（老车锈深褐 / 同款新车亮漆），不走 BIKE 块。**不得据 BIKE 块推断全包同款**；T29/T30 的同款律靠词面自述维持。
4. **官方尾段（py `kf()` 全额）**：`Shot on <lens>, 2001 telecine grade, warm skin tones, milky lifted blacks, blooming practical highlights, slight color bleed, <texture>, as a film still from a 2001 Taiwanese music video`
   - GRADE_2001=`LX.GRADE["tw2001"]` 逐字沿用（本曲年代=**2001**，与龙卷风 2000 不同，禁串年代）。
5. **光块清单（本曲自建 6 块·四光位+两天气支线）**：
   | key | 用法 |
   |---|---|
   | `day_clear` | 6200K 北向大天光·灰混凝土地面软边影·光比约 3:1（晴段主光） |
   | `day_back` | 3200K 低日逆光·双人影两档外溢·堤墙接溢光（剪影/黄昏段） |
   | `golden_rim` | 末二十分钟日光 2800K·镜头左侧勾发勾肩·其余压两档（回环段） |
   | `rain_soft` | 6800K 阴雨平光·整体去饱和转蓝灰·檐下 2700K 暖池（雨段主光） |
   | `eave_win` | 5600K 旧窗日光·走道地面浅矩形·浮尘在束中（教吉他/写积水） |
   | `dusk_sodium` | 巷口单钠灯 2200K·暖橙只落灯下·未照街面转冷灰（尾段） |
6. **一歌一律（本曲=透明日光）**：晴段高调透明暖白 / 雨段青灰柔软（**伞下是暖的**）/ 钠灯不校正；halation 必有源（QC §10 v1.12）。
7. **长期律**：匀速判负（相遇 1.05 / 风与发丝 0.90 / 日落静 0.85 / 尾牵 0.88 / 奔跑棒球 1.15）；禁看镜头；物质转场；音轨=画面+原曲零 AI 音轨；AIGC 显著标识；**意象分仓（单车归本曲·星晴资产零入镜）**。
8. **剧情记忆钉**：影子先牵手（独立镜·v2.2 #6 + v2.3 #7 先物理后概念）+ 积水写「简单爱」+ 两代单车尾拍（零人物）。
9. **发布话术红线**：识别句「我想就这样牵着你的手不放开」=首帧字幕必用；文案零姓名指向（2015 骑车联读已群像化）。

## 一、A 批 30 帧装配表（逐帧·词面机核）

| id | window | dur | speed | light | tex | lens | words | lint | note（py note 列逐字） |
|---|---|---|---|---|---|---|---|---|---|
| T01 | 0.00-13.00 | 13.00 | 1.00 | day_clear | film_day | 35 | 107 | CLEAN | 前奏=黑场鼓点起→巷口石板路渐亮（无人·只有风与光） |
| T02 | 13.00-26.12 | 13.12 | 1.05 | day_clear | film_day | 35 | 158 | CLEAN | 他推车入画（鼓音）→ 镜头随车轮缓摇 |
| T03 | 26.12-36.08 | 9.96 | 1.05 | day_clear | film_day | 50 | 125 | CLEAN | 她跑进巷口（鼓点落·人群零添加） |
| T04 | 36.08-46.10 | 10.02 | 1.10 | day_clear | film_day | 35 | 137 | CLEAN | 石阶绊倒（失误=动作链真实·裙摆与掌心同框） |
| T05 | 46.10-56.21 | 10.11 | 0.95 | day_clear | film_day | 50 | 103 | CLEAN | 伸手扶起（外化：他先在裤缝蹭一下手·扶起后多停半拍·掌心蹭破一划） |
| T06 | 56.21-65.68 | 9.47 | 0.90 | day_clear | film_day | 50 | 124 | CLEAN | 她抓他袖口又放开（羞涩三态①）→ 视线落到后座 |
| T07 | 65.68-75.60 | 9.92 | 0.90 | day_clear | film_day | 35 | 131 | CLEAN | 他用自己的袖子擦车座（郑重到笨拙·v2.1 #3）→ 她坐上后座发丝逆风 |
| T08 | 75.60-85.68 | 10.08 | 0.85 | day_back | film_day | 35 | 103 | CLEAN | 河堤并肩坐·日落逆光双影一长一短（背影剪影①·原版保真） |
| T09 | 85.68-95.54 | 9.86 | 0.85 | day_back | film_day | 85 | 188 | CLEAN | 她的头一点一点磕在他肩上（困意外化·不煽情）+ 他回头看她一眼（演唱锚②·零口型） |
| T10 | 95.54-105.42 | 9.88 | 0.90 | day_back | film_day | 50 | 96 | CLEAN | 真实的手先入画牵住（低角度逆光·v2.3 #7） |
| T11 | 105.42-113.96 | 8.54 | 0.88 | day_back | film_day | 35 | 102 | CLEAN | 影子先牵手=独立镜（堤面占画幅 ≥60%·多停 4-6 帧·v2.2 #6） |
| T12 | 113.96-121.77 | 7.81 | 1.15 | day_back | film_day | 35 | 104 | CLEAN | 牵手奔跑过整条街（扣紧那一下=识别句拍点·拇指压一下） |
| T13 | 121.77-128.40 | 6.63 | 1.15 | day_clear | film_day | 35 | 177 | CLEAN | 午后操场·他投她打（挥棒起手） |
| T14 | 128.40-135.06 | 6.66 | 1.15 | day_clear | film_day | 50 | 122 | CLEAN | 挥空三次笑场（玩心档·挥拍三连快切） |
| T15 | 135.06-145.28 | 10.22 | 1.00 | rain_soft | film_night | 50 | 143 | CLEAN | 暴雨突至·伞永远斜向她那边（他半肩湿=守护外化） |
| T16 | 145.28-154.94 | 9.66 | 0.95 | rain_soft | film_night | 50 | 101 | CLEAN | 伞下的分歧（她伸手接雨·他轻轻拉回=全片唯一分歧·v2.1 #1） |
| T17 | 154.94-164.66 | 9.72 | 0.90 | rain_soft | film_night | 35 | 110 | CLEAN | 屋檐躲雨笑出声（暖池/青灰分界可见） |
| T18 | 164.66-174.74 | 10.08 | 0.85 | eave_win | film_day | 50 | 179 | CLEAN | 屋檐下教她假装弹吉他（耳根红·指尖只碰三根指头·羞涩三态②） |
| T19 | 174.74-184.64 | 9.90 | 0.95 | rain_soft | mist | 35 | 146 | CLEAN | 独自撑伞漫步街头（间奏·原版记忆点「最青涩最纯情」） |
| T20 | 184.64-194.46 | 9.82 | 0.88 | eave_win | film_day | 50 | 143 | CLEAN | （词面物质镜）他蹲下用手指在积水里写「简单爱」 |
| T21 | 194.46-201.80 | 7.34 | 1.00 | rain_soft | mist | 35 | 104 | CLEAN | 雨停后堤面空镜（水洼反光·无人物） |
| T22 | 201.80-209.26 | 7.46 | 0.95 | rain_soft | mist | 50 | 97 | CLEAN | 收起的伞靠在栏杆上（关系的静物残留） |
| T23 | 209.26-216.50 | 7.24 | 0.85 | golden_rim | film_day | 35 | 101 | CLEAN | 回外婆家=堤面再坐（她的头又磕上肩·愿望回环） |
| T24 | 216.50-223.83 | 7.33 | 0.85 | golden_rim | film_day | 85 | 104 | CLEAN | 她的手放在他胸口（上衣布料起皱=接触的物质证据） |
| T25 | 223.83-231.50 | 7.67 | 1.00 | day_back | film_day | 35 | 160 | CLEAN | 黄昏骑车载她远去（背影剪影·愿望第一项的回收） |
| T26 | 231.50-239.12 | 7.62 | 1.00 | dusk_sodium | film_night | 35 | 110 | CLEAN | 巷口晚灯亮起（钠灯不校正·暖橙只落在口那里） |
| T27 | 239.12-249.19 | 10.07 | 0.88 | dusk_sodium | film_night | 50 | 178 | CLEAN | 她先伸手（坦荡三态③·反转）→ 他愣半拍→扣紧 |
| T28 | 249.19-256.78 | 7.59 | 0.88 | dusk_sodium | film_night | 85 | 109 | CLEAN | 十指相扣特写（拇指压一下）+「就这样」字帧 1s（思源宋体系） |
| T29 | 256.78-264.00 | 7.22 | 0.90 | day_back | film_day | 35 | 107 | CLEAN | 多年后同一段河堤：老单车锈成深褐·车筐野草开花 |
| T30 | 264.00-270.99 | 6.99 | 0.90 | day_back | film_day | 50 | 107 | CLEAN | 旁边一辆同款新车（亮漆/干净铃面/褪色红绳·橡胶把套有磨损）→ 缓摇收→黑场片名 |

时间轴对账：NEW 覆盖 **270.99s** = `FILM_END`（shotgrid inputs.duration_sec），**零缺口、零 REUSE 补窗**（本曲是全专唯一满覆盖曲）。

## 二、帧串硬点（装配站执行口径）

- **羞涩三态递进**：T06 抓袖口又放开（①）→ T18 伞下教吉他耳根红、指尖只碰三根指头（②）→ T27 她先伸手、他愣半拍（③反转）。三帧手势不许同义重复。
- **牵手两条证据（v2.3 #7 先物理后概念）**：T10 真实的手先入画牵住 → T11 影子先牵手独立镜（堤面 ≥60% 画幅、多停 4-6 帧）。顺序不可倒。
- **物质化优先于情绪**：T05 裤缝蹭手 + 扶起后停半拍 + 掌心蹭破；T24 上衣布料起皱；T20 指写「简单爱」。禁把行为写成「他很温柔」这类标签。
- **同镜同款**：T08/T23 同一段堤面同一坐姿（愿望回环）；T29 老车 / T30 新车同款不同代，同框一台、漆面与把套磨损必须不同。
- **伞的因果**：T15 他半肩湿（伞斜向她）→ T16 她接雨他拉回（唯一分歧）→ T22 收伞靠栏杆（关系静物）。三帧同一把伞。
- **光比纪律**：晴段高调透明、雨段青蓝、钠灯段暖橙只落灯下；禁整片统一暖调，禁给雨段补暖铺底。
- **识别句拍点**：T12 扣紧那一下 + T28 十指相扣拇指压一下，两处对应同一句词。

## 三、自检回执（2026-10-20 机核实跑）

| 项 | 值 |
|---|---|
| 帧数 | 30（NEW） |
| 词数 | min **96**（T10）/ max **188**（T09）· 全包 <200 |
| t2i lint | **30/30 CLEAN**（issues=0） |
| 覆盖 | 270.99s / 270.99s（满片·零 REUSE） |
| 纹理分布 | film_day 21 / film_night 6 / mist 3（T19/T21/T22） |
| 光块分布 | day_clear 9 / day_back 8 / rain_soft 6 / dusk_sodium 3 / eave_win 2 / golden_rim 2 |

## 四、待裁与移交（如实记录·不自行改词）

1. **GRADE 尾段含 `warm skin tones, milky lifted blacks`**：17:47 W2 i2v 包已判该两处为继承缺陷并在 **i2v 尾段**修正，KF 面（t2i）仍沿用官方尾段。本曲色彩律=透明日光（晴段暖白），冲突度低于龙卷风（冷色全片），但**是否 KF 面同步覆写冷版尾段，仍待导演席统一裁（与龙卷风同批定 A/B）**。
2. **选角已承载，无需 B 批（证据勘正）**：能证明她全脸在包内的只有 **T09**（85mm、她的头磕在他肩上）；原稿举的 T24「手放胸口」词面**只有手与布料，无脸**，该论据不成立，已删。定脸后仍须跑以图搜人反向测试留档（CASTING-LAW）。
3. **i2v 面（PACK-B）另开**：按 `KF-PACK-i2v` 口径审（slide FLAT、warm-skin/milky-black 清理、H3 括号语法）。
4. **`kf()` 模板 `.capitalize()` 副作用（勘正：非零影响）**：块内单位被小写化——实测 `6200K`→`6200k`，本包 30/30 帧命中（语义无碍）。真正的缺陷是同一模板的**主语误绑**，见 §六。
5. **烧制侧执行口径（过闸后）**：海选制单口径（672×384 8 步 → 两级海审 → 1344×768 refine 0.30）；烧制前后各跑一次 t2i lint；词数必检；抽检位=T09（188 词最长·85mm 近景）+ T11（影子镜·v2.2 #6 判例）+ T30（两代单车·同款不混）。

## 六、独立评审席判读（2026-10-20·verdict 已落盘）

- verdict 件：`PROMPT-GATE-简单爱-KF-PACK-A-v1-L2.md`。整包 **FIX 级**：30 帧 PASS 10 / FIX 20 / REJECT 0，列 **14 条 FIX**。
- **A. 模板主语误绑（与龙卷风同源·须导演席统一裁）**：`kf()` 把 HIM/HER 名词块直接接动作分词。实例（T15）：
  `A medium shot of jman … , straight dark trousers, scuffed canvas shoes holding a plain long umbrella …`
  ——「holding」被绑到「canvas shoes」上。修法=模板加句界（词数/lint 不变），属全包级变更，本席不擅改正身。
- **B. T20 撞文字生成红线**：词面 `one finger drawing three characters in the water` 要求模型写三个汉字，撞 QC §9「禁 AI 生成文字」+ §19 字席制字。**改法建议（须导演同意）**：改为「指尖在积水上划动、水面破而复平」，汉字由字席后期贴字，不进生成。
- **C. T29/T30 光块与零人物帧冲突（I1）**：两帧词面明确无人物，但 `day_back` 光块写着 `placed behind the two figures … around their silhouettes`。须另立无人版光句（如「低日逆光压在栏杆与车身上」），不得沿用双人块。
- 本席已按 verdict 勘正本稿转录失真（BIKE 挂载范围、T24 论据、capitalize 影响）。
- **签署状态**：本席=起草席，按分权不得自签；签发席须为另一窗/另一席。未签前保持「禁烧」。

---
*bm-a · 2026-10-20 · 承 O-20261020-1124 W1-W2 多曲加速排产令；本件=人读稿，未过闸未签发，禁据以点火。*