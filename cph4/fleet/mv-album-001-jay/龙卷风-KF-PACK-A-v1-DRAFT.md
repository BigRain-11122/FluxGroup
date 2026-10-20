# 龙卷风-KF-PACK-A-v1-DRAFT（A 批 29 帧·bm-c 烧制用稿）

> **状态=草稿·未过闸·禁烧**。本件只做 A 批人读稿，过闸链未走完：独立评审席 verdict（待出）→ 导演席合并复检签发（待）→ 才可点火。无 verdict 派单=烧制侧拒收（QC §12 v1.2）。
> **权威=龙卷风-shots-v2.py**（词面正身·v2.0）。本稿按词面机核抽取，不改一个词；人读稿与正身冲突时以 py 为准（零转录律）。
> **机器提取口径**：`python Tools/kf_pack_extract.py cph4/fleet/mv-album-001-jay/龙卷风-shots-v2.py`（读模块 `NEW` 元组逐帧跑 `prompt_lexicon.lint(mode='t2i')` + 词数 + 光块/纹理/镜头块反查）。原始输出=同目录 `_kf_tornado.json` / `_kf_tornado.md`。

## 〇、共享词块（每帧装配时套用）

1. **男主 ID 块（HIM·逐字）**：`jman, a 20-year-old Taiwanese student with heavy-lidded monolid eyes, a thick lower lip, softly rounded cheeks, a flat round nose tip, a blunt rounded jaw and natural unretouched skin with visible pores, in a charcoal grey wool crewneck sweater, loose dark trousers, bare feet on the wooden floor`
   - `jman LoRA` strength **0.6**（影射档·本曲剧本硬约束）；ID 体=`prompt_lexicon.ID_M_2001_BONE` 同源，禁本地改字。
2. **女主 ID 块（HER·逐字·禁跨曲复用）**：`a 24-year-old Taiwanese woman with a clear oval face and calm almond eyes, long straight black hair tied loosely back, in a soft knitted scarf and a plain cream knit top`
   - 选角律=CASTING-LAW：陈怡蓉系清纯初恋脸，**只活闪回**；词面零真名、真照不入管线；与星晴/可爱女人/简单爱 ID 块互斥。
3. **官方尾段（py `kf()` 全额）**：`Shot on <lens>, 2000 telecine grade, warm skin tones, milky lifted blacks, blooming practical highlights, slight color bleed, <texture>, as a film still from a 2000 Taiwanese music video`
   - GRADE_2000=`LX.GRADE["tw2001"]` 逐字把 `2001 telecine` 本地覆写为 `2000 telecine`（本曲年代=2000）。
4. **光块清单（本曲自建 7 块）**：
   | key | 用法 |
   |---|---|
   | `room_grey` | 6200K 雨后窗光·低饱和·房间角落入冷影（现实线主光） |
   | `room_lamp` | 3000K 旧台灯·青灰小光池·周围家具近黑（现实线夜/演唱锚） |
   | `storm_lead` | 5600K 铅蓝风暴街·斜雨·湿地反白闪（闪回线主光） |
   | `her_warm` | 2200K 残烛级暖残光·只落在她脸上（**闪回唯一暖点**） |
   | `day_white` | 5600K 正白日光·开帘光束·浮尘可见（收束段） |
   | `patch_light` | 斜射白光·墙面浅方形两档更浅（相框原位） |
   | `window_rain` | 雨水顺旧铝窗流下·灰街在玻璃后溶解 |
5. **一歌一律（本曲=全专最冷色）**：现实线青灰、闪回线铅蓝黑；**全片唯一暖点=她的 2200K 残光**。做旧克制，禁暖调铺底。
6. **长期律（剧本层已定，烧制侧不得违反）**：匀速判负（现实线 0.82-0.95 慢稳 / 闪回线 1.10-1.25 burst 双速对撞）；禁看镜头（她越往后越侧越背）；物质转场；音轨=画面+原曲零 AI 音轨；AIGC 显著标识。
7. **剧情记忆钉**：相框浅方形（场 0 埋 / 场 5 显 / 场 7 收）+ 停摆的钟（场 7 扶正上弦）+ **两把椅子只拖一把**。
8. **发布话术红线**：禁称复刻邝盛版分镜；周杰伦/徐若瑄真名禁入提示词与物料；词曲双权注记随物料。

## 一、A 批 29 帧装配表（逐帧·词面机核）

> 全部 29 帧=`shots-v2.py NEW`，无重复 i2v 画面。`window`=py 原始窗口；`speed`=变速系数；`words`=kf 提示词实数词；`lint`=t2i 三名单机检。

| id | window | dur | speed | light | tex | lens | words | lint | note（py note 列逐字） |
|---|---|---|---|---|---|---|---|---|---|
| T01 | 0.00-10.00 | 10.00 | 0.88 | room_grey | film_day | 24 | 109 | CLEAN | 狼藉空房间一帧缓推（倒下的相框/歪的钟/碎玻璃） |
| T02 | 10.00-18.00 | 8.00 | 0.90 | room_grey | film_day | 50 | 102 | CLEAN | 墙上浅方形一瞥（相框原位日晒色差·首刷几乎看不见） |
| T03 | 18.00-30.02 | 12.02 | 0.85 | room_grey | film_day | 35 | 152 | CLEAN | 他背窗而坐（背影剪影①·灰晨光·全片最慢点之一） |
| T04 | 30.02-33.35 | 3.33 | 1.00 | room_grey | film_day | 50 | 97 | CLEAN | 拿起相框擦灰（拇指停在她的脸那格） |
| T05 | 33.35-36.69 | 3.34 | 1.05 | her_warm | film_night | 85 | 135 | CLEAN | 闪回1=她在铅蓝风暴里回头（暖残光·唯一暖点首现） |
| T06 | 37.52-40.02 | 2.50 | 1.00 | room_grey | film_day | 35 | 105 | CLEAN | 空掉的半张床（关系的物质残留） |
| T07 | 40.85-46.69 | 5.84 | 0.95 | her_warm | film_night | 50 | 166 | CLEAN | 闪回2=她替他拂掉肩上的灰（他站着不动） |
| T08 | 46.69-52.48 | 5.79 | 1.20 | storm_lead | film_night | 24 | 104 | CLEAN | 闪回3=黑云降落+两人被风拖走（词面超现实镜·物理轨迹真实） |
| T09 | 52.48-64.19 | 11.71 | 0.90 | room_lamp | film_night | 35 | 154 | CLEAN | 拖椅子归位·两把椅子只拖一把（空的那把不动） |
| T10 | 67.52-73.36 | 5.84 | 1.25 | storm_lead | film_night | 35 | 99 | CLEAN | 暴雨斜打窄街（水从雨棚成片泻下） |
| T11 | 73.36-80.86 | 7.50 | 1.10 | storm_lead | film_night | 35 | 138 | CLEAN | 伞骨外翻+她隔着被风灌满的街（唯一暖点·L1 可读锚） |
| T12 | 80.86-86.69 | 5.83 | 1.10 | storm_lead | film_night | 35 | 99 | CLEAN | 暴风圈来不及逃=牵手奔跑剪影（背影剪影②） |
| T13 | 86.69-94.19 | 7.50 | 1.15 | storm_lead | film_night | 85 | 101 | CLEAN | 他抓她手腕抓得太紧（腕上勒痕一帧·失控外化） |
| T14 | 94.19-100.03 | 5.84 | 0.85 | storm_lead | film_night | 85 | 149 | CLEAN | 静一拍=他抬眼缓推（风暴里唯一清醒的一秒·单硬光低位） |
| T15 | 100.03-107.53 | 7.50 | 0.84 | room_grey | film_day | 50 | 89 | CLEAN | 收拾的手越来越慢（每个「不觉得」=一拍放慢） |
| T16 | 107.53-113.36 | 5.83 | 0.82 | room_grey | film_day | 50 | 92 | CLEAN | 放下手里的东西→手空了才停（v2.1 打磨 #4 动作因果先于情绪） |
| T17 | 113.36-117.53 | 4.17 | 0.88 | room_grey | film_day | 35 | 157 | CLEAN | 同构图房间半净（停手时刻·与开场同机位） |
| T18 | 120.85-126.69 | 5.84 | 1.10 | her_warm | film_night | 50 | 172 | CLEAN | 闪回重演=同一动作更短更淡（回忆在褪色） |
| T19 | 126.69-134.20 | 7.51 | 0.95 | her_warm | film_night | 85 | 130 | CLEAN | 她的暖残光逐次减一档+越往后越侧越背（v2.1 #5 记忆被转过去） |
| T20 | 134.20-143.36 | 9.16 | 0.90 | room_grey | film_day | 24 | 96 | CLEAN | 房间越来越空净+空相框在桌上（完成度递增） |
| T21 | 146.70-151.70 | 5.00 | 0.86 | room_lamp | film_night | 50 | 158 | CLEAN | 演唱锚①=钢琴旁侧影（零脸·2.5s 实拍位 5s 源） |
| T22 | 151.70-164.00 | 12.30 | 0.84 | day_white | film_day | 35 | 142 | CLEAN | 拉开窗帘=日光第一次入房（手臂全程匀速不停顿·接受态） |
| T23 | 164.00-174.20 | 10.20 | 0.85 | patch_light | film_day | 50 | 156 | CLEAN | 浅方形显形+抬手停半空（v2.2 给观众的手指·唯一指路） |
| T24 | 174.20-185.87 | 11.67 | 0.90 | day_white | film_day | 50 | 136 | CLEAN | 演唱锚②=窗前背影哼尾段（最静处理·反向于副歌1） |
| T25 | 185.87-193.00 | 7.13 | 0.88 | day_white | film_day | 85 | 127 | CLEAN | 她最后回望的半张脸（白光收走前一秒·记忆被转过去） |
| T26 | 200.88-212.00 | 11.12 | 0.92 | storm_lead | film_night | 85 | 131 | CLEAN | 「你」渐弱蒙太奇1（她走远·边缘开始发白） |
| T27 | 212.00-224.00 | 12.00 | 0.90 | day_white | mist | 35 | 98 | CLEAN | 「你」渐弱蒙太奇2（只剩轮廓·街已溶解） |
| T28 | 224.00-237.00 | 13.00 | 0.88 | day_white | film_day | 35 | 145 | CLEAN | 推窗全开（接受·光进满屋） |
| T29 | 237.00-250.36 | 13.36 | 0.90 | patch_light | film_day | 50 | 148 | CLEAN | 回望墙上浅方形一拍→满屋白光收黑（v2.1 #1 钟并肩物证·尾窗对齐歌长） |

## 二、REUSE 补窗（6 段·定格延展·零新烧）

| 帧 | 补窗 | 时长 | 说明 |
|---|---|---|---|
| T05 | 36.69-37.52 | 0.83 | 定格延展补窗 |
| T06 | 40.02-40.85 | 0.83 | 定格延展补窗 |
| T09 | 64.19-67.52 | 3.33 | 定格延展补窗（副歌进前空拍） |
| T17 | 117.53-120.85 | 3.32 | 定格延展补窗（C 段→副歌2 间奏） |
| T20 | 143.36-146.70 | 3.34 | 定格延展补窗 |
| T25 | 193.00-200.88 | 7.88 | 定格延展补窗（尾段副歌收） |

时间轴对账：NEW 覆盖 **230.83s** + REUSE **19.53s** = **250.36s** = `FILM_END`（ffprobe 实测片长），零缺口零重叠。

## 三、帧串硬点（装配站执行口径）

- **相框三段式**：T01 倒地（埋）→ T23 浅方形显形（显）→ T29 回望一拍（收）；浅方形=T02/T23/T29 同机位同角度，色差两档。
- **钟的物证**：T01 歪钟（停摆）→ T29 钟并肩物证（v2.1 #1）；两帧钟面读数须一致（停摆=时间未走）。
- **两把椅子只拖一把**：T09 单镜内完成，空椅全程不动（关系的不对等物化）。
- **暖残光递减链**：T05（1.0x 亮度）→ T07 → T18 → T19（逐次减一档）+ 越往后越侧越背 → T25 半张脸 → T26 边缘发白 → T27 只剩轮廓。这是本曲唯一色彩叙事线，**烧制侧不得抬高 her_warm 曝光**。
- **双速对撞**：现实线 0.82-0.95 / 闪回线 1.10-1.25；同镜内禁混速。
- **首尾对位**：T01 狼藉全景（24mm 高角）↔ T29 满屋白光收黑（50mm）；T17 与 T01 同机位（进场=退场的镜像）。
- **零脸原则**：T03/T12/T21/T24 为背影/侧影；T25 是唯一「半张脸」，不得调成全脸。

## 四、自检回执（2026-10-20 机核实跑）

| 项 | 值 |
|---|---|
| 帧数 | 29（NEW） |
| 词数 | min **89**（T15）/ max **172**（T18）· 全包 <200 |
| t2i lint | **29/29 CLEAN**（issues=0） |
| 覆盖 | 230.83s / 250.36s（+REUSE 19.53s = 满片） |
| 纹理分布 | film_day 17 / film_night 10 / mist 1（T27） |
| 光块分布 | room_grey 9 / storm_lead 7 / day_white 5 / her_warm 4 / patch_light 2 / room_lamp 2 |

## 五、待裁与移交（如实记录·不自行改词）

1. **GRADE 尾段与本曲色彩律冲突（新发现·待导演席裁）**：`GRADE_2000` 官方尾段含 `warm skin tones, milky lifted blacks`，而本曲长期律=「全专最冷色、闪回唯一暖点」。2026-10-20 17:47 W2 i2v 包已判该两处为继承缺陷并在 **i2v 尾段**修正（`skin tones kept natural and unlit` / `black point lifted to 10-14 code with shadow crush intact`），但 **KF 面（t2i）仍沿用官方尾段**。
   - 现状：不擅自改词（改则全包 lint/词数须重跑，且属模板级变更）。
   - 选项 A：KF 面同样本地覆写冷版尾段（与本曲色彩律一致，需重跑 lint）；选项 B：KF 保留官方尾段、由调色站统一压冷暖（承 GRADE-LAW）。**请导演席定 A/B。**
2. **`kf()` 模板 `.capitalize()` 副作用**：光块首字符被大写、块内专名被小写化。本曲 7 个光块无专名，**零影响**（可爱女人包 `Taipei→taipei` 同源问题，与本曲无关）。
3. **i2v 面（PACK-B）另开**：本包只审 KF 静态帧；i2v 词面须按 `KF-PACK-i2v` 口径另审（含 slide FLAT 修复、warm-skin/milky-black 清理）。
4. **B 批（她的独立正脸帧）**：本包 A 批她 4 帧（T05/T07/T18/T19）均为侧/背/远景，无全脸近景。**是否另开 B 批补她的独立正脸帧，待导演席定**；定脸前不得跨曲复用。
5. **烧制侧执行口径（过闸后）**：海选制单口径（672×384 8 步 → 两级海审 → 1344×768 refine 0.30）；烧制前后各跑一次 t2i lint；词数必检；抽检位=T18（172 词最长）+ T27（mist 唯一一张）+ T09（两椅叙事）。

---
*bm-a · 2026-10-20 · 承 O-20261020-1124 W1-W2 多曲加速排产令；本件=人读稿，未过闸未签发，禁据以点火。*