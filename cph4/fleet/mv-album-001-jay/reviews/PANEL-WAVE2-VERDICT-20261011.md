# PANEL-WAVE2-VERDICT-20261011 · 《星晴》《可爱女人》分镜表 v2 四席评审（KF/i2v 生产前工程闸）

> 对象=星晴-shots-v2.py（33 NEW+7 REUSE）/可爱女人-shots-v2.py（30 NEW+4 REUSE）·机读正身；基准=anchors 词级实测（星晴尾 248.76/可爱女人尾 247）+mv_full_shots.py 范式+prompt_lexicon lint；配额=云端 100 单/日机队共享·mv0001 44 在飞。

## 一、分镜工程席 6.5/10 FAIL

判词：副歌卡点是全表最亮的活——XQ18-22/26-33、KN05-09/21-30 逐镜 start-land 词窗行首，抽验 30 处零偏差；REUSE 降速阶梯（XQ17 1.00→0.98→0.96）有想法。但 mv0001 的窗口连续性 assert 整个被丢：星晴漏窗 11 处（51.80-54.28/110.94-111.84/116.74-117.60/132.82-133.31/138.00-138.63/172.38-173.48/181.44-182.54/192.80-195.70/202.62-203.68/219.16-219.82/224.50-225.42，合计 13.2s）、可爱女人 3 处（55.66-56.94/85.82-89.36/183.28-184.60，合计 6.1s）——「零空档」是预注册律不是选修。XQ06-09 词链整体迟一行（「云掉落」38.52 起唱，云影镜 43.22 才开）；数步段单镜 5.78s，自打脸自家头注「一步一剪」。

修项：
1. 两 py 照抄 mv_full_shots.py 的 WINDOW GAPS assert；14 处漏窗按「≤3s=前镜尾帧定格延展·>3s=邻镜双挂」补齐（51.80-54.28 挂 XQ07 后半·192.80-195.70 挂 XQ26 前半·85.82-89.36 挂 KN05 后半）。
2. XQ06-09 重切贴词：XQ06 30.00-33.16 / XQ07 33.16-38.52 / XQ08 38.52-43.86 / XQ09 43.86-51.80。
3. XQ17 拆 4 子窗步点交替（一步一剪）；补 XF_T1/T2 叠化常量（星晴=XQ18 内·可爱女人=KN20 内·1-2s=24-48 帧承 RESEARCH §三）。
4. 星点连续性互怼：XQ21「线已成形」vs XQ33「最后一连补完」——XQ31 改「第六星初醒」、XQ33 改「第六星光丝落定」。
5. 相邻同速四对改梯：XQ17/18（1.00/1.00）、XQ29/30（0.92/0.92）、KN20/21（0.90/0.90）、KN23/24（0.85/0.85）；XQ20 三连 0.85 改 0.85/0.80/0.90；REUSE 尾注「夜版重演」名不副实（源本就是夜镜）改「重演」。

## 二、可生成性席 6.0/10 FAIL

判词：i2v 三维（Motion+幅度+Speed）全表齐整、单镜单动作大体守纪、PLANE 块「单翼折痕」记忆锚是好活。但三处 `CM["macroslide"]` 把 mv0001 巴比伦原句整段搬进来——XQ14 线轴/KN01 叠机手/KN18 银河近景的运镜句全写着「slides across carved cuneiform marks」，楔形文字渗进 2000 台北。星晴 8 镜 KF 指代无实体（XQ03 his/XQ04·05·06 her·两人/XQ10 their/XQ13 her/XQ26 riding double 只声明 HIM/XQ30 the two of them）——被指代者从未写进主体串，i2v 现场抽脸；ponytail 漂移 3 镜（XQ01·XQ04 i2v，XQ06 KF 自写 ponytail 又与自家 i2v「side-fringed」互怼）+XQ01 i2v「pale-yellow blouse」对 XQ_HER 针织背心——ID 漂移第一镜就开闸。星线「i2v 现场画光丝」=细线幻影/文字化噪点高危。

修项：
1. XQ14/KN01/KN18 运镜换 CM["static"] 或新铸无 cuneiform 的 macroslide 变体。
2. 指代补声明：XQ04/06/26 注入 XQ_HER；XQ05/10/30 改「two distant figures」；XQ03 补 HIM；XQ13 补「a distant girl figure chasing a white butterfly」；XQ02 i2v 背景位 the girl 补「distant, soft-focus」。
3. XQ01/04 i2v 与 XQ06 KF 的 ponytail/blouse 逐字改回 XQ_HER 正典（medium straight black hair with a soft side fringe+knit tank top）。
4. 星线生长改 KF 双帧叠化交付（XQ18a 无丝→XQ18b 成丝·1-2s），i2v 只留 tiltup+「threads holding steady」；XQ31/33 同改 in-place 增亮/落定，禁 i2v 现画线。
5. 伪影锚：星空 i2v 加「each star holding its place with a slow twinkle」；KN17/18 加「soft round points, the dust cloudlike」；KN04 掷出保持 cu 满幅+burst（最稳写法勿改远景）。
6. 光块错配：XQ17 lamp_grass（手电筒照草）配公路街灯池内容——换 night_road 或新铸 streetlamp_pool；star_field 的 flashlight pool 在 XQ19/22/32/33 无动机，铸 star_field_pure 变体。
7. jman：trigger+strength 全表零声明，KF 工单补 LoRA 挂载元数据；数据集=2001-03 范特西期，对 2000《Jay》期脸有漂移，strength 0.6-0.8 先扫网格。人物占比：星晴 22/33（脸级约 13）·可爱女人 6/30——脸级镜全落 LoRA 甜区。

## 三、年代质感席 7.0/10 FAIL

判词：光照叙事骨架立得住（星晴 暮 0-30→日 30-86.8→蓝调铰链 86.8-95.6→夜 95.6-248.8，日暮夜三段成立；可爱女人 黄昏 0-30→夜 30+ 两段干净），道具年代全对（圆灯机车/木骨纸鸢/竹线轴/水塔晾衣绳/手电筒避手机光），tw2001 奶黑两表一致。扣分在边界失控：星晴 6 镜黄昏 kf 吃默认参数滑回 film_day（XQ01-05+XQ16，250D 扛 8000K 蓝调=欠曝粗颗粒），可爱女人 KN01-04 同病——黄昏落 5279 还是 5246 全案没成文。KN09 在夜段中央亮回 roof_dusk 黄昏且 KF 写 dusk/i2v 写 night 自相矛盾；KN14 streak 块写「dusk sky」配 78.5 夜空——时间倒流两处。

修项：
1. 成文律：黄昏/蓝调段=5279（XQ01-05/16、KN01-04 补 tex="film_night"），纯日戏留 5246——禁吃默认参数。
2. KN09 改夜天台（新 roof_night 块或 city_bowl+tex film_night）对齐 i2v「night rooftop」；KN14 streak 块「dusk」改「night」。
3. 年份钉死：GRADE tw2001「2001 telecine」vs STYLE_LEAD「2000」、ID_F_VVR「year 2001」——《Jay》=2000，统一 2000 面或换 2000 版 GRADE 串。
4. 招牌渗漏锚：street_dusk/city_bowl 的「shop signs」易被 AI 写成 LED 现代门头——补「aged hand-painted signboards and old neon tubes」。
5. KN_HER 声明了从未入镜（她全程剪影/灯窗）——选角案降级为「身形发型约定单」，别占 CEO 点选带宽。

## 四、成本配额席 6.5/10 FAIL

判词：63 i2v 单 vs mv0001 占 44 后余量 ~56——单日装不下还叫「一波」；REUSE 吃了没吃够：KN27 就是 KN05 复读、KN26 就是 KN09 夜版、XQ32=XQ21 全貌+剪影合成，三镜白烧。窗口-素材账没人算：按 源长=窗长×变速 折算，星晴 21/33、可爱女人 21/30 新镜超单条 5s 供血，全表零填充策略声明；>8s 窗 13 处（星晴 XQ05/06/26/28·可爱女人 KN03/04/15/16/21/22/27/28+KN13R）——XQ26 需 10.1s、KN22 需 15.5s，这不是分镜表是欠条。

修项：
1. 先钉云端时长政策：单任务可出 8-15s 同价→仅 KN21/KN22 需拆；锁死 5s→13 处全拆/双挂：XQ26@168.18、XQ28@186.66、XQ05@25.5、XQ06@33.16、KN03@17.5、KN04@26、KN15@94、KN16@104、KN21@148、KN22@155+163、KN27@222.7、KN28@232。
2. REUSE 三换省 3 单：KN27→REUSE KN05、KN26→REUSE KN09（夜改后）、XQ32→REUSE XQ21+剪影合成层；63→60。
3. KN12R/KN13R 拆：@204.42/@214.84（正好卡「可愛的女人」hook 行首，一石二鸟）；副歌1 飞姿切点整体提前到 hook 行首（59.14/62.66/66.26/69.80）——现状四连切全落在 hook 尾上，声称卡拍点实为迟半句。
4. 排产：今日云端只放第一波 52 单；第二波待 mv0001 收尾+女主定版。

## 四席汇总

| 席 | 分 | 判 | 要害 |
|---|---|---|---|
| 分镜工程 | 6.5 | FAIL | 漏窗 14 处·verse 链迟一行·数步违律·无 assert |
| 可生成性 | 6.0 | FAIL | cuneiform 污染 3 镜·指代无实体 8 镜·ID 漂移 3 镜 |
| 年代质感 | 7.0 | FAIL | 黄昏胶片滑档 10 镜·KN09/14 时间倒流·年份漂移 |
| 成本配额 | 6.5 | FAIL | 63>56 余量·13 窗口>8s 无拆案·REUSE 少吃 3 镜 |

## 过闸结论

不过闸。四席全 <7.5：顶层设计（副歌贴锚/光照块系统/REUSE 阶梯）过线，账本（窗口账+提示词账）没盘就上闸。退回打 v2.1 机械补丁——全部为改窗/改词/改挂，不动立意不动结构；补丁跑绿 WINDOW GAPS+lint+时长 assert（源长=窗长×变速≤5s 或声明拆挂）后复闸。KF 批（本地 bm-c·零云端配额）63 帧即刻挂单不必等。
阻断件：女主定版（星晴 11 脸级镜）·云端时长政策（13 长窗）·jman strength 网格（人物 KF 前）。

## 第一波最小可产集（52 单·不依赖女主定版）

- 星晴 22：XQ02,05,07,08,10,13,14,15,17,18,19,20,21,23,24,25,26,28,30,31,32,33（空镜/物件/远景剪影/男主镜；XQ26/30 修指代后进）
- 可爱女人 30：KN01-30 全量（她=剪影/灯窗·零脸依赖·全表可产）
- 押后：XQ01,03,04,06,09,11,12,16,22,27,29（女主脸级/近身镜·等 CEO 点选定版）
