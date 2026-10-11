# R-20260930-audio-design-01 · 吸嘟嘟音频批调研：休闲游戏音效/BGM 设计规范与 Earworm 理论

- 调研员：C（集团后台调研）
- 日期：2026-09-30
- 委托用途：为「吸嘟嘟」音频批（休闲吸取玩法 · 治愈系糖瓷卡通 · 马卡龙色板 · 全年龄 · 微信小游戏）提供设计规范依据
- 证据纪律：结论逐条标注【确认】（有公开信源）/【待证】（业界传闻、合理推断或信源不足），信源 URL 随条附注；无信源断言一律降级【待证】。

## 0. 摘要（TL;DR）
**六条核心结论（全部有信源支撑，详见对应章节）**：

1. **头部三消 BGM 基线**＝「30 秒～几分钟主循环＋少量 intro/ending/stinger」（PopCap 音频师 Guy Whitmore 直接引语）；Candy Crush 实践为关型专属 15–20s 循环×19 曲（社区 wiki 待证），并已升级为 **stems 分轨动态混音**（连胜加速/需要时更平静，King 音频总监 Vanesa Tate）。→ §1
2. **连击音高阶梯是品类标配且有两种正路**：同一样本逐次升调（Peggle Blast「escalating pitch」直接引语）或**沿当前 BGM 调式音阶逐级取音**（Peggle Blast peg 音系统）；辅以 Candy Crush 式**里程碑播报阶梯**（Sweet→Tasty→Divine…）。→ §1.4、§3.2
3. **Earworm（洗脑）五要素**（Jakubowski et al. 2017，3000 人研究）：更快 tempo、**先升后降的儿歌型轮廓**、平易旋律中埋**意外跳进或超常重复**、短而熟的动机反复、**曝光与近期性**共同起作用；90% 的人每周至少卡脑一次，多发于低认知负荷时段。**勘误**：Durham 的大规模研究是 2016/2017；2010 年正式发表的是 Reading 大学 Beaman & Williams。→ §2
4. **UI/SFX 硬参数**：点击 30–150ms、成功叮 ≤500ms、多数提示音 <300ms；上行音高=确认/积极、下行=否定；同一产品同一音色家族（同一混响/voice）；微信小游戏 **Android 同时最多 10 路 InnerAudio（官方）**，短高频音效必须走 WebAudio；预算建议 ≤8 路。→ §3
5. **多通道齐拍**：反馈须 ≤100ms 才「瞬时」（NN/g 0.1s 法则）；音画异步可检测阈 **+45ms/−125ms**（ITU-R BT.1359-1）；即时效果会被**意图绑定**到玩家动作（Haggard 2002）——结论是**反馈音不做微延迟，同帧起步**，可变的只有 ducking 让位曲线与事件帧锚点。→ §4
6. **无缝循环**＝乐句边界+零交叉的**采样级循环点**（禁淡入淡出式循环），氛围类才用等功率交叉淡化（节奏 ~20ms/pad 200–500ms），段落边界靠混响「冲过边界」平滑；30–60s 循环靠 **stem 加层＋stinger 打断**压疲劳，单曲舒适区 45–90s。→ §5

**对吸嘟嘟的落点**：底座四项已同向（连击阶梯/ducking/三通道 1.2s 同窗/节流）；最大缺口是 BGM（章界换轨未落实、无 stem 动态层、循环工艺未定标）与成文规范（UI 长度文法、发声预算表）；性价比最高的补强是**嘟嘟奶音里程碑播报**与**音色家族白名单**。→ §6

## 1. 头部休闲/三消音频设计手法（Royal Match / Piggy Match / Lily's Garden / Candy Crush Saga 等）
### 1.1 Candy Crush Saga（King）

- **制作规格（音频即品牌投资）**【确认】：King 音频团队由 head of audio Dominique Devoucoux 领衔；Candy Crush 系列音频重制历时约一年、动用 57 名现场乐手在伦敦 Abbey Road 录音，团队自述「像制作电影一样制作游戏音乐」。信源：https://www.pocketgamer.biz/inside-audio-design-at-king/（正文经抓取核验）。Candy Crush Soda 上市时同样在 Abbey Road 用伦敦交响乐团录制配乐【确认】：https://www.youtube.com/watch?v=7lNUl7RnKbs
- **BGM 动态化 = stems（分轨）+ 情境混音**【确认】：King 音频总监 Vanesa Tate：「音频 10 年没更新过」→ 重制时**全部音乐按 stems 分轨录制**，按玩家状态动态生成听感——「玩家连胜时音乐更快、玩法需要时更平静」（fast-paced on winning streak / calmer when gameplay requires）。这是头部三消从「一条循环」升级到「分层动态配乐」的直接证据。信源：https://www.pocketgamer.biz/kings-vanesa-tate-on-re-crafting-the-soundtrack-to-candy-crush-saga/（正文经抓取核验）
- **曲目结构**【待证（社区 wiki，未见官方文档）】：Candy Crush Saga 共 19 首曲子；**关卡类型专属 BGM 以 15–20 秒循环播放**，失败曲等一次性播放；2022-11-14 十周年整体换新配乐（作曲 Sebastian Aav，2024 年发布官方 OST 专辑）。信源：https://kingcom.fandom.com/wiki/Music_(Candy_Crush_Saga) ／ https://candycrush.fandom.com/wiki/Candy_Crush_Saga_(Original_Soundtrack)
- **级联（cascade）正反馈阶梯**【确认（游戏内可听+语音素材可核，细节来自 wiki）】：连锁反应触发**人声播报阶梯** Sweet→Tasty→Divine→Delicious→Sugar Crush（连锁数越高播报越夸张），构成三消品类标志性的「连锁越高、反馈越大」阶梯。信源：https://candycrush.fandom.com/wiki/Cascades ；语音素材存在性可核：https://www.101soundboards.com/sounds/64047199-juicy-tasty-divine-soda-crush-soda-delicious
- 备注：2023-07 起多数音效被替换为 Candy Crush Friends Saga 同款【待证】：https://candycrush.fandom.com/wiki/Sound

### 1.2 Royal Match（Dream Games）

- **音频供应商家族化**【确认】：Royal Match 游戏内 BGM 由 Moonwalk Audio 的 Adam Gubman 作曲（"Gameplay Theme 1 - Royal Match — Composer: Adam Gubman, Moonwalk Audio, Developer: Dream Games"）：https://www.youtube.com/watch?v=qhe9ek7EmLk ；Moonwalk Audio（作曲 Adam Gubman ＋ 音效/实现 Alex Cox）同时服务 Royal Match / Township / Royal Kingdom：https://www.linkedin.com/company/moonwalk-audio 、https://www.linkedin.com/in/alex-cox-7ba9916 、https://www.moonwalkaudio.com/ 。头部休闲厂把音乐+音效+语音打包给同一音频供应商，是「音色家族一致性」的组织化做法。
- **广告/CG 音频**【确认】：Royal Kingdom 旗舰短片＋Royal Match 配套片的音乐音效混音由 Pollen Music Group 制作，在伦敦 AIR Studios 以约 60 人规模管弦录制：https://www.pollenmusicgroup.com/branded/royalkingdom
- **BGM 循环结构一手资料未获取**【待证】：Dream Games 内部音频博客（Medium "A Day in the Life of an Audio Designer at Dream Game Studios"，https://medium.com/dreamlockerroom/a-day-in-the-life-of-an-audio-designer-at-dream-game-studios-4c7d673e4dfc）被反爬拦截，无法核验其循环/分层细节；Royal Match in-game 音乐的具体 loop 结构在公开渠道未见披露。

### 1.3 Lily's Garden（Tactile Games）

- 产品明确定位「relaxing / cozy / calming world / no forced ads」【确认（商店页）】：https://play.google.com/store/apps/details?id=dk.tactile.lilysgarden&hl=en-US
- **未检索到任何公开音频制作访谈或文章**【待证】：仅能由产品定位推断其音频目标为低刺激、高重复容忍度（治愈系装饰玩法）；BGM/音效的具体手法无公开信源，本报告不对其音频手法下无信源断言。

### 1.4 Piggy Match 及替代标杆 Peggle Blast

- **Piggy Match - Win Cash**（Android 现金奖励三消）真实存在【确认（商店收录）】：https://apps.qoo-app.com/en/app/141447 ；但**无任何公开音频设计资料**【待证】，其音频手法不可考。
- 替代标杆：**Peggle Blast!（PopCap，休闲弹珠，与三消同族的「小项目、高音质」标杆）**，资料来自其 GDC 2015 演讲《Peggle Blast: Big Concepts, Small Project》配套博客系列（Game Audio Network Guild 镜像，正文经抓取核验）：
  - GDC Vault 页【确认】：5MB 音频足迹 = MIDI 音乐 + 程序化音频合成 + 音频逻辑集成：https://www.gdcvault.com/play/1022188/Peggle-Blast-Big-Concepts-Small
  - **预算对比**【确认】：制作指令「全部音频 <5MB」；对照 Peggle 2（Xbox One）音频达 783MB。最终以 **1.3MB 音效 + 3.5MB 音乐**交付数百条音效与 30 分钟以上互动音乐。信源：https://www.audiogang.org/realtime-synthesis-for-sound-creation-in-peggle-blast/
  - **实时合成、贴画面调音**【确认】：音效在 Wwise 内用音调发生器+DSP 实时合成，「与画面实时对齐」调整；引语——「同一样本上做升级音高（escalating pitch over time）是制造变奏与兴奋感的大赢家，且不需要新资产」。信源：同上
  - **叮声=键内音阶逐级上行**【确认】：peg 命中音跟随**当前音乐段的调/音阶**（Wwise User Cue 广播 key/scale），每命中一个 peg 就取音阶表的下一个音——即「连击音高阶梯」是**沿当前调式音阶爬升**而非任意移调；5 个 wav 经 Wwise MIDI 转置扩展成整组命中音、48 个调/音阶组合实时生成。信源：https://www.audiogang.org/peggle-blast-peg-hits-and-the-music-system-2/
  - **音乐结构（反行业惯例）**【确认】：Guy Whitmore 引语——手机游戏音乐行业惯例=「**一条 30 秒到几分钟的主循环 + 少量短 intro/ending/stinger**」；Peggle Blast 不用静态循环，改为**每一杆结束就做和声推进（升五度、反向五度圈）**，12 个调性段循环、倒数第二段 A 大调铺垫胜利时全编制 PCM 的《Ode to Joy》或失败段，「像影视转场一样给每一杆做情绪抬升」。信源：https://www.audiogang.org/scoring-peggle-blast-new-dog-old-tricks/
  - **stinger 与音乐咬合**【确认】：凤凰蛋孵化=铜管 riff、免费球=合唱 sus9 和弦、超常表现=合唱喊「awesome!/pegglicious!」；**stinger 必须与底层音乐和声、节奏咬合**，每类 stinger 备 12–15 个 MIDI 文件（每调一个）；peg 音=竖琴（普通 peg）＋橙 peg 叠 marimba 重音层；**所有采样乐器送同一实时混响统一空间感、并让段落边界更顺滑**（reverb cascades over the boundaries）。信源：同上

### 1.5 头部产品共性小结

| 维度 | Candy Crush | Royal Match | Peggle Blast（标杆） | 行业基线（Whitmore 引语） |
|---|---|---|---|---|
| BGM 结构 | 关型专属 15–20s 循环 ×19 曲【待证 wiki】＋stems 动态混音【确认】 | 未公开【待证】；单一供应商家族化【确认】 | 无静态循环，按回合和声推进（12 调性段）【确认】 | 「30s–数分钟主循环＋intro/ends/stinger」【确认】 |
| 正反馈音 | 级联人声阶梯 Sweet→…→Sugar Crush【确认】 | 未公开【待证】 | 键内音阶逐级上行叮＋stinger【确认】 | 上行=积极【确认】 |
| 高潮时刻 | Abbey Road 现场乐/LSO【确认】 | AIR Studios 60 人管弦（广告层）【确认】 | 胜利=全编制 PCM《Ode to Joy》【确认】 | — |
| 音色统一 | 同厂音频团队【确认】 | 同一供应商跨三作【确认】 | 同一实时混响统一空间【确认】 | 同产品同一音色家族【确认】 |

- 共性结论【确认】：(1) BGM 以 30 秒以上循环为基线，变奏靠**分段/分轨(stem)/stinger**；(2) 正反馈=**上行音高阶梯（键内或采样转置）＋里程碑播报**；(3) **高潮时刻用超出日常成本的特殊音乐**（现场乐/全编制 PCM）；(4) 音色家族统一（同供应商/同一混响空间/同一 voice）。

## 2. Earworm（耳朵虫/洗脑）研究落到 BGM 设计
### 2.1 INMI / earworm 研究谱系（并勘误「Durham 2010」）

- **术语与研究链条**【确认】：earworm 直译德语 Ohrwurm；学术名「不自主音乐意向」INMI（Liikkanen, 2008）。谱系：Kellaris（2001/2003，消费心理学会报告，**未发表系列研究**，「认知痒 cognitive itch」）→ Liikkanen 2008（约 12,000 名芬兰网民调查）→ **Beaman & Williams (2010)**《Earworms (stuck song syndrome): Towards a natural history of intrusive thoughts》**British Journal of Psychology 101(4), 637–653**（正式发表）→ **Jakubowski, Finkel, Stewart & Müllensiefen (2017)**《Dissecting an Earworm: Melodic Features and Song Popularity Predict Involuntary Musical Imagery》*Psychology of Aesthetics, Creativity, and the Arts*（研究在 Goldsmiths 执行，第一作者 Kelly Jakubowski 现任 Durham 大学音乐心理学教授；APA 于 2016-11 发布新闻稿）。信源：https://centaur.reading.ac.uk/5755/ ；https://www.apa.org/pubs/journals/releases/aca-aca0000090.pdf
- **勘误**【确认】：任务书中「Durham University 2010 earworm 研究」实为两支：① 2010 年正式发表的 earworm 自然史研究出自 **University of Reading（Beaman & Williams）**；② **Durham 大学**牵头的旋律特征大规模研究是 **2016（APA 新闻稿）/2017（期刊发表）** 的 Jakubowski 等。引用时请按此更正。
- 普及率【确认】：Kellaris 调查「约 98% 的人经历过」（媒体报道，原研究未发表）：https://www.nytimes.com/2003/08/12/health/when-the-brain-grabs-a-tune-and-won-t-let-go.html 、http://news.bbc.co.uk/2/hi/science/nature/3221499.stm ；Liikkanen 2008：**>90% 每周至少一次、33.2% 每天**（经 Beaman & Williams 2010 正文核验）；Jakubowski 团队调查中 **90% 受访者每周至少一次**，且**多发于低认知负荷活动**（洗澡、走路、打扫）：https://www.smithsonianmag.com/smart-news/earworm-begone-study-explores-why-certain-songs-get-stuck-our-heads-180961016/

### 2.2 易洗脑旋律的音乐学特征（Jakubowski et al. 2017）

方法【确认】：3,000 名受访者提名最常「卡脑」曲目，与**同流行度、同榜单近期性**的对照组曲目做旋律特征对比（首个大规模 earworm 旋律特征研究；2010–2013 年采集）。

特征结论【确认】（APA 新闻稿 + ScienceDaily 全文核验：https://www.apa.org/news/press/releases/2016/11/earworms 、https://www.sciencedaily.com/releases/2016/11/161103122229.htm ）：
1. **速度更快**：earworm 曲目 tempo 显著快于对照组平均（「usually faster」；随机森林模型仅用 tempo＋两个轮廓常见度特征即可区分）。
2. **「常见」全局轮廓**：整体旋律形状属于西方流行乐最高频型——典型如**先升后降**（"Twinkle Twinkle Little Star" 上句升、下句降的儿歌轮廓；"Moves Like Jagger" 前奏同型）。儿歌同型使其「好记」。
3. **不寻常音程结构**：在平易旋律中埋**意外跳进（leap）或超常重复音**——如 "Smoke On The Water" 前奏、"Bad Romance" 副歌、"My Sharona" 间奏、"In The Mood"。
4. **曝光与近期性同样重要**：earworm 曲电台播放更多、榜单位置更高——旋律特征与曝光**共同**预测「卡脑」。Jakubowski：「你可以在一定程度上根据旋律内容预测哪些歌会卡在脑子里……这能帮助词曲作者或广告人写出让人记几天几个月的 jingle」。
- 研究内最高频 earworm 榜【确认】：Bad Romance / Can't Get You Out Of My Head / Don't Stop Believing / Somebody That I Used To Know / Moves Like Jagger / California Gurls / Bohemian Rhapsody / Alejandro / Poker Face。

### 2.3 Beaman & Williams (2010)：自然史与「不要主动压制」

【确认】（原文经 docslib 镜像核验：https://docslib.org/doc/383601/earworms-stuck-song-syndrome-towards-a-natural-history-of-intrusive-thoughts ）：
- 体验**广泛存在但通常不被视为问题**；认为「音乐对我重要」的人报告 earworm 更长、更难控制（与 Liikkanen 音乐性相关发现一致）。
- 卡脑曲目**因人而异，但总是自己熟悉的曲子**；**复发少见、罕见持续超过 24 小时**；单次 earworm 及其体验总时长**常超过听觉记忆容量的标准估计**（即反复自发重播）。
- **主动压制不如被动接受有效**（符合 Wegner 讽划性讽刺理论）。
- 对设计的含义：①「洗脑」依赖熟悉度=**重复曝光**是前提；②被卡住的常是 unwanted 的——**「记得住」与「听不腻」要分开设计**。

### 2.4 音高轮廓与情绪关联（「上行=积极？」）

- **先升后降**是最高频洗脑轮廓【确认】（Jakubowski；见 2.2）。
- **上行音高=积极/确认、下行或不协和=否定/错误**：UI/交互音设计的行业共识【确认】（"rising pitch reads as positive (success, confirm); falling or dissonant pitch reads as negative (error, cancel)"）：https://violetrecording.com/how-to-design-ui-sounds/
- **纯上行阶梯**（连击进程感）：Peggle Blast peg 命中音沿当前调式音阶**逐级上行**，制造「越连越高」的兴奋感【确认】（见 §1.4）。
- 泛化的「上行旋律=积极情绪」跨模态映射【待证】：本报告未核到一手文献（Ohala 频率码、Hevner 1936 等方向），仅以上述两条具体来源支撑设计用法。

### 2.5 对 BGM 写作的直接规范含义（由上述研究推导，推导项标注）

| Earworm 证据 | BGM 写作规范 | 标注 |
|---|---|---|
| 快 tempo 显著预测 | 休闲 BGM 主题段 tempo 不宜拖；律动明确 | 【确认】特征→【推导】参数 |
| 先升后降儿歌轮廓 | 主题动机用「上行句+下行句」拱形，而非单向上行到底 | 【确认】 |
| 意外跳进/超常重复 | 平易旋律里埋 1 个识别点（跳进或重复音型） | 【确认】 |
| 短、熟悉、重复（Beaman：总是熟悉曲子） | 主 hook 动机 4–8 音符、在循环内多次重现；章节边界重复动机（曝光+近期性） | 【确认】→【推导】 |
| 曝光与近期性共同作用 | 每季/每章 BGM 固定复用同一主题变奏，勿每章全新无关联 | 【推导】 |
| earworm 多发于低认知负荷、常 unwanted | 音频不必填满每秒；BGM 留呼吸窗；避免超短循环高频轰炸 | 【确认】现象→【推导】规范 |
| 罕见持续>24h、总是熟悉曲 | 「洗脑度」以多日留存播放行为验证，而非单次问卷 | 【推导】 |

## 3. SFX 设计规范
### 3.1 UI 音长度分层（点击音多长合适）

【确认】交互/UI 音设计的可核参数（https://violetrecording.com/how-to-design-ui-sounds/ ，正文经抓取核验）：
- **轻点/点击类（taps & clicks）：30–150ms**；「多数界面提示音 <300ms」；
- **通知/成功叮（notifications & success chimes）：最长约 500ms**；
- 「**反复高频触发的音若更长就开始有侵入感**」（anything longer starts to feel intrusive when a user triggers it repeatedly）——高频事件音要往短做。
- 频域：中高频段（mid-high）更悦耳、避免刺耳峰值；同一产品共享混响/音色/voice。

【确认】交互文法分层（https://uxdesign.cc/a-game-sound-designers-guide-to-button-interactions-6837dd5cc977 ，Denis Zlobin）：把按钮听觉反馈拆为**输入反应（按下即响）／结果音（consequential，随情境）／系统响应**三类——按下瞬间响的是「输入反应」，结果音对齐事件帧，系统响应用于状态变化。另见情境化适配思路【待证（仅摘要核验）】：https://sfxengine.com/blog/best-practices-for-game-ui-sounds

**分层规范建议（推导）**：点击≤150ms｜确认/升级叮 150–300ms｜结算/奖励短句 ≤500ms｜胜利 sting 1–3s（对齐结算屏时长的 1/3 以内）。捕获类「结果叮」取 300–500ms 档合理；纯按钮咔哒应压进 150ms 内。

### 3.2 正反馈音高阶梯（连击 pitch ladder 业界用法）

- **同一样本升级音高**【确认·直接引语】：Peggle Blast 音效师 Jaclyn Shumate——「**effects like escalating pitch over time on the same sound were a big win for creating sound variability and excitement, without requiring a new asset**」（同一样本上随次数/时间升调=变奏+兴奋感，零新增资产）。https://www.audiogang.org/realtime-synthesis-for-sound-creation-in-peggle-blast/
- **键内音阶阶梯**【确认】：Peggle Blast peg 命中音沿当前音乐段调式音阶逐级取音（User Cue 广播 key/scale，命中一次进一音）——阶梯是**乐音阶**而非任意线性移调，与 BGM 永远和声咬合。https://www.audiogang.org/peggle-blast-peg-hits-and-the-music-system-2/
- **里程碑播报阶梯**【确认】：Candy Crush 级联语音 Sweet→Tasty→Divine→…（连锁越高播报越大）：https://candycrush.fandom.com/wiki/Cascades ；Peggle Blast 超常表现触发合唱喊「awesome!/pegglicious!」【确认】。
- **语义方向**【确认】：上行=成功/确认、下行或不协和=错误/取消（见 §2.4）。
- 奖励音的动机学证据（博彩类比）【确认】：Dixon et al. (2010, *Addiction*)——「伪装成赢的输（LDW）」配庆祝音后，新手玩家的皮电与心率唤起**与真赢无差别**（SCR/HR, n=40）：https://onlinelibrary.wiley.com/doi/10.1111/j.1360-0443.2010.03050.x ；后续《Using Sound to Unmask Losses Disguised as Wins》进一步研究声音对「输赢感知」的扭曲（标题/摘要可核，全文未获取）：https://www.researchgate.net/publication/258336797_Using_Sound_to_Unmask_Losses_Disguised_as_Wins_in_Multiline_Slot_Machines 。→ 奖励音的强度与规模是被实证的动机操纵手段，休闲游戏应只把它用在「真赢」上。
- Candy Crush「级联叮声逐级升调」的说法在玩家侧广为流传，但未找到一手信源【待证】。

### 3.3 音色家族一致性

- 【确认】同产品所有音效应共享：同一混响、相近音色、同一「voice」——「整个 app 听起来像一个产品」（https://violetrecording.com/how-to-design-ui-sounds/ ）。
- 【确认】Peggle Blast：**全部采样乐器送同一实时混响**，把所有声音拉进同一声学空间，同时平滑段落边界（https://www.audiogang.org/scoring-peggle-blast-new-dog-old-tricks/ ）。
- 【确认】组织化做法：头部休闲厂把音乐+音效+VO 交给同一音频供应商（Moonwalk Audio × Dream Games 三作，见 §1.2）。
- 【推导】治愈系糖瓷卡通（吸嘟嘟）适配音色家族参照：竖琴/marimba/拨弦/八音盒类软启动、短衰减音色（Peggle peg 音=竖琴+marimba 即此思路）＋奶音人声点缀；避免长残响金属与刺耳合成峰值。

### 3.4 听觉疲劳防治（频次限制 / 变奏 / 静默窗口）

- **变奏（业界标准做法）**【确认】：①同一样本转置变奏（Shumate 引语）；②情境变奏——每类 stinger 备 12–15 个 MIDI（每调一版）（Whitmore）；③键内自动变奏——48 调/音阶组合让同一叮声在不同 BGM 段落自动变音高（Mattingly）；④短而多能的音色选择（staccato 管弦/pizzicato 弦乐「短样本多用途」）（Whitmore）。
- **重复暴露效应**【确认·存在性】：Zajonc 1968 以降的 mere exposure 研究经 Bornstein (1989, *Psychological Bulletin*) 20 年元分析确认「重复暴露提升好感」，且受复杂度/时长/延迟等调节：https://psycnet.apa.org/record/1990-00422-001 ；**「好感随重复先升后降的倒 U 曲线」**在音乐循环场景的具体形态未见定量一手研究【待证】。
- **静默窗口**【确认·现象→推导】：INMI 多发于低认知负荷时段、earworm 常为 unwanted、罕见持续 >24h（见 §2）→ 音频不必填满每一秒；BGM 呼吸窗、结算前静默半拍再起 sting，都是可辩护的手法。
- **频次限制**：行业**无统一毫秒标准**【待证·未找到成文规范】；可核的是微信官方红线——「Android 最多同时播放 10 个音频，超出做有损处理，开发者应尽量避免同时播放过多音频」（https://developers.weixin.qq.com/minigame/dev/guide/base-ability/audio.html ，正文核验）→ 高频事件必须有节流/合并（本项目 60ms 节流即此类实现，属内部约定参数）。

### 3.5 小游戏同时发声路数（polyphony）预算

- **微信小游戏硬限制**【确认·官方】：Android **同时最多 10 路** InnerAudio，超出有损处理；建议**短音频、高频音效走 WebAudio**（性能好、能力丰富但占内存）；复用实例、及时 `destroy()`；退后台回来用 `onShow`/`onAudioInterruptionEnd` 恢复播放。信源：https://developers.weixin.qq.com/minigame/dev/guide/base-ability/audio.html （全文核验）＋ https://developers.weixin.qq.com/minigame/dev/api/media/audio/InnerAudioContext.html
- **实例与延迟的社区实证**【确认·多方一致】：InnerAudioContext 在 Android 真机延迟严重、iOS 不明显；实例过多触发 "Too many InnerAudioContext instance" 告警；WebAudio 预解码 AudioBuffer 近零延迟。信源：https://forum.cocos.org/t/topic/147670 、https://ask.layaair.com/d/55484-yin-xiao-bo-fang-zai-wei-xin-zhen-ji-yan-chi
- **引擎默认参照**【确认】：Unity 全局 Max **Real Voices 默认 32**（讨论帖可核）：https://discussions.unity.com/t/max-real-voices-always-limited-to-32/910855
- **预算建议（推导）**：微信小游戏同时发声预算 **≤8 路**（10 路硬限内留余量）；优先级＝玩法反馈（捕获叮）＞结算/奖励 ＞ UI ＞ 氛围/装饰；同质事件合并＋oldest-stealing；BGM 1 路 + ducking，不占音效预算。

## 4. 音频-视觉-触觉「多通道齐拍」反馈一致性设计
### 4.1 感知同步阈值（人能察觉多少毫秒的不同拍）

- **0.1 秒法则**【确认·原文】：Nielsen Norman Group——「**0.1s 是让用户感觉系统『瞬时响应』的上限**」，即按下的效果须在 100ms 内可见/可闻才被视为「直接操纵」；1.0s 是思路不被打断的上限。信源：https://www.nngroup.com/articles/response-times-3-important-limits/ （正文核验）
- **音画异步检测阈值**【确认·标准原文】：ITU-R BT.1359-1《Relative timing of sound and vision for broadcasting》——**可检测阈约 +45ms（声音超前）至 −125ms（声音滞后）**，可接受阈约 +90ms 至 −185ms；即声音**略超前画面**比滞后更不容易被察觉。信源：https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1359-0-199802-S!!PDF-E.pdf ；解读可参照 https://www.forasoft.com/learn/audio-for-video/articles-audio/lip-sync-itu-r-bt-1359-tolerance-windows
- **动作-效果绑定（intentional binding）**【确认】：Haggard, Clark & Kalogeras (2002, *Nature Neuroscience*)《Voluntary action and conscious awareness》——主动动作与其感官效果在意识中**被时间压缩、绑定**在一起（效果被提前感知）；该压缩对**短延迟**最强，随延迟增大而衰减（时间进程研究：https://link.springer.com/article/10.3758/s13414-017-1292-y ）。→ 设计含义：**效果音越即时，越被归因于「我按出来的」**（agency 感）；把效果拖到 100ms 之外就开始「掉绑」。
- **移动端平台底噪**【确认】：Android CDD 5.6 建议**持续输出延迟 ≤45ms、往返 ≤50ms**（冷启动 ~200ms 强烈建议）：https://android.googlesource.com/platform/compatibility/cdd/+/refs/heads/master/5_multimedia/5_6_audio-latency.md ；术语定义（cold/warm/continuous、touch latency）：https://developer.android.com/ndk/guides/audio/audio-latency
- **视听-触觉三通道同时性感知**【待证】：存在专项研究《Audiovisual-Haptic Simultaneity Perception Across the Body》（EuroHaptics 2024）：https://link.springer.com/chapter/10.1007/978-3-031-70058-3_4 ；其具体 ms 阈值未核到原文（PDF 反爬）。跨模态组合响应时间研究可参照：https://arxiv.org/abs/2305.17180

### 4.2 同拍 vs 微延迟的设计权衡（业界做法）

- **同拍（ASAP）用于输入反应类**【确认+推导】：按下即响的 UI/捕获音必须在 **≤100ms**（0.1s 法则）且尽量同帧；结合 intentional binding，即时效果会绑定到玩家的动作上。触觉脉冲与音效应**同帧**发出（同一逻辑帧调用），不做感知上的先后。
- **对齐事件帧（非固定延迟）用于结果类**【确认】：Peggle Blast 的做法是「**声音直接贴着画面实时调**」（matching sounds directly to visuals, real-time；在游戏内边看画面边改声音参数）——即以**视觉事件帧**为对齐锚点，而非加固定延迟。信源：https://www.audiogang.org/realtime-synthesis-for-sound-creation-in-peggle-blast/
- **微延迟的合法用途**【确认+推导】：①**让位（ducking）**：音乐在音效/播报下自动压低——业界用 sidechain/ducking 实现（Audiokinetic 官方教程与文档：https://www.audiokinetic.com/en/library/edge/?source=Help&id=using_sidechaining 、https://blog.audiokinetic.com/learn/videos/dLO1Yk-NXm8/ ）；②**结果音随动画飞抵帧**（如金币飞入计数器时叮）——属「对齐事件帧」而非延迟。声音**滞后画面 >125ms** 才违反 ITU 阈；工程上没有理由允许任何反馈音晚于其视觉事件一帧以上。
- **结论**：反馈音不主张「微延迟」；唯一可变的是**让位曲线**（attack/release/深度）与**事件帧锚点**。

### 4.3 微信小游戏/移动端落地约束

- 【确认·官方】短音频高频音效必须走 **WebAudio**（预解码 AudioBuffer），InnerAudio 仅用于 BGM/长音频（流式、性能低）：https://developers.weixin.qq.com/minigame/dev/guide/base-ability/audio.html
- 【确认·社区多方】InnerAudioContext 在 **Android 真机有严重固有延迟**（iOS 不明显）——玩法反馈音若走 InnerAudio 会直接撞穿 0.1s 法则：https://forum.cocos.org/t/topic/147670 、https://ask.layaair.com/d/55484-yin-xiao-bo-fang-zai-wei-xin-zhen-ji-yan-chi
- 【推导】验收口径：捕获叮从 touch 到出声（真机实测）≤100ms；音+触觉同一逻辑帧；视觉粒子/飞线同一渲染帧起播；BGM ducking 起始与风暴/章界事件同帧，恢复时间（1.5s/13s 档）按事件长度配置。
- 本项目三通道共用 1.2s 连击窗（音高阶梯/咀嚼拍/旁观者跳，`ActorDudu.cs L60` 注释「音画同源节拍」）与上述「同帧绑定」原则一致【确认·项目证据：R-20260929-u314-opt-gameplay-01.md L83】。

## 5. BGM 循环设计
### 5.1 无缝循环做法（淡入淡出 vs 采样级精确循环点）

业界可核的两种正路 + 一种过渡工艺：
- **① 采样级精确循环点（首选）**【确认】：在**同一乐句/小节边界**（同节拍位置）切点、零交叉对齐，导出时预置 loop 区间，播放器直接跳回——不叠加、无音量凹陷。游戏音频中即「sample-accurate loop」：Unity 社区有专门的采样级循环工具链（metadata 扫描＋播放 helper）：https://github.com/rabbitlin-web/Unity-Seamless-Loop-Toolbox ；OpenMPT 文档对「把 loop 前一段混入 loop 尾」的样本交叉淡化器亦有正式说明：https://wiki.openmpt.org/Manual:_Sample_Crossfader
- **② 等功率交叉淡化（仅救急/氛围类）**【确认】：在循环点做 **equal-power crossfade**——节奏型素材 ~20ms，pad/氛围类 200–500ms 可让接缝完全消失；线性淡化会造成音量凹陷、不推荐。工具文档（参数即行业默认口径）：https://vibesdj.io/dj-tools/audio-looper
- **③ 复制-修接点-交叉淡化（工作流法）**【待证（全文反爬，仅目录级核验）】：《LOOPS: How To Create Seamless Looping Music and Sound Effects Files》列出三法：复制音轨→修接点→交叉淡化等。信源：https://www.scribd.com/document/616195257/LOOPS-How-To-Create-Seamless-Looping-Music-and-Sound-Effects-Files
- **④ 段落边界的「混响跨越」工艺**【确认·直接引语】：Peggle Blast——每个采样乐器送实时混响 send，「**reverb cascades over the boundaries**（混响冲过段落边界）」使段落切换/循环点更顺滑。https://www.audiogang.org/scoring-peggle-blast-new-dog-old-tricks/
- **结论**：BGM 必须做成**采样级无缝循环**（乐句边界+零交叉），**禁止用「结尾淡出→开头淡入」冒充循环**；交叉淡化只用于氛围 pad 与救急。

### 5.2 30–60s loop 的听觉疲劳曲线与变奏策略

- **循环长度基线**【确认·直接引语】：手机/休闲游戏音乐行业惯例=「**一条 30 秒到几分钟的主循环 + 少量短 intro/ending/stinger**」（Whitmore）。超短循环（15–20s）在 Candy Crush 的实践是可行的，但前提是**按关卡类型多曲轮换**（19 曲体系）【待证·wiki】——短循环靠曲目数量压疲劳，长循环靠内部变奏压疲劳。
- **重复偏好曲线**【确认存在性→待证形态】：mere exposure 元分析确认重复暴露提升好感并受复杂度/时长调节（Bornstein 1989）；但「30–60s 循环第 N 遍时好感下降的定量曲线」**无一手研究**【待证】。可辩护的工程口径（推导）：同一循环连续曝光按**分钟级**计——30s 循环 5 分钟=10 遍，疲劳速度约为 90s 循环的 3 倍；故 30s 档循环必须配 AB 段内变奏或高频 ducking/stinger 事件打断记忆锚点。
- **变奏策略（头部产品实证）**：
  - **stems 分层（加层）**【确认】：全部音乐按分轨录制，按玩法状态实时混音（连胜加速、需要时更平静）（Tate，§1.1）。→ 「AB 段/加层」的行业正名即 stem 分轨＋情境混音。
  - **和声推进（水平推进）**【确认】：Peggle Blast 每杆升五度、12 调性段循环、终局段铺垫胜利曲（§1.4）——把「变奏」做成玩法驱动而非定时驱动。
  - **stinger 打断**【确认】：stinger 与音乐和声/节奏咬合，每调备 12–15 个 MIDI 版本（§1.4）。
  - **章/季换轨**【确认·为头部通用做法的推导+本项目规划】：Candy Crush 按关型多曲轮换【待证·wiki】。
- **对 30–60s 循环的落地规范（推导）**：单曲循环 45–90s 为舒适区（≥30s 基线、避开 15–20s 高疲劳档）；结构 AAB' 或 AB+尾部加层（每 2–3 遍自动加/减一层）；循环点置于乐句边界（第 8/16 小节）；章界用「章界铃」等 stinger 衔接换轨（本项目已有 sfx_ui_chapter＋duck 0.14/1.5s，与此一致）。

## 6. 对吸嘟嘟的落地建议（现有底座 vs 行业手法差距评估）
### 6.1 现有底座盘点（任务书口径 + 项目证据）

| 底座项 | 现状 | 项目证据 |
|---|---|---|
| 捕获叮（连击） | 合成叮 0.35s；**60ms 节流**；1.2s 连击窗；**音高阶梯 8 段×+6%、封顶 +48%**（≈+7 半音，接近纯五度） | `SfxBus.cs L23-L25`、`ActorDudu.cs L60`（R-20260929-u314-opt-gameplay-01 L76/L83） |
| 签名五键专属音 | sock/furball/snake/coins/fuzzhill，真声优先、合成回退，`SfxFlow` 五槽路由 | R-20260929-u314-opt-flowux-01 L135 |
| BGM | 规划三季轮换（30–90 关四轨）；**实测关 1–30 全部 bgm_main、5 个章界无换轨**（仅章界铃补偿） | R-20260929-u314-opt-flowux-01 L123（差距证据） |
| ducking 让位 | 风暴 0.10/13s；章界 0.14/1.5s；WinSting 0.16/1.0s | R-20260929-u314-opt-flowux-01 L139 |
| 按钮 | 咔哒合成音（长度/音高文法未见成文规范） | 【待核】 |
| 嘟嘟三态奶音 | 入场/胜利/失败短句 3s；大餐嗝彩蛋（Cleared≥20） | R-20260929-u314-opt-flowux-01 L139 |
| 触觉 | light 120ms 节流；过关 light 句点 | R-20260929-u314-opt-flowux-01 L64/L139 |

### 6.2 差距对照表（行业手法 vs 我们）

| # | 维度 | 行业手法（信源见上） | 吸嘟嘟现状 | 差距判定 |
|---|---|---|---|---|
| 1 | 连击音高阶梯 | 采样转置升调【确认·Peggle 引语】＋**沿 BGM 调式音阶**逐级【确认】 | 8 段×+6% 封顶+48%（线性） | **方向正确**；缺「与 BGM 调和」——+6%/段≈+1 半音（×1.0595），建议段距量化为半音或对齐当前 BGM 音阶，避免连击高点与 BGM 半音打架 |
| 2 | 里程碑播报 | Candy Crush 级联语音阶梯【确认】；Peggle 合唱「awesome!」【确认】 | 仅过关/彩蛋有奶音 | **低成本高收益**：连击达 8 段顶格、章节连过 3 关等节点复用已有嘟嘟奶音短句做播报阶梯 |
| 3 | UI 音长度文法 | 点击 30–150ms、成功叮 ≤500ms；上行=确认/下行=取消【确认】 | 咔哒合成音，无成文长度/音高规范 | 缺规范：咔哒 ≤150ms 定标；确认/取消配上行/下行音高对 |
| 4 | BGM 循环结构 | 基线=30s–数分钟主循环+stinger【确认·引语】；Candy Crush 15–20s×多曲【待证·wiki】 | 三季四轨为规划；实测 1–30 关单曲无变化 | **最大缺口**：章界换轨未落实（项目自证）；单曲长度建议 45–90s、AAB'/AB 结构、采样级无缝循环 |
| 5 | 动态分层 | stems 全分轨+情境混音（连胜加速）【确认·Tate】 | 有 ducking、无 stem 分层 | 缺动态层：BGM 拆 3–4 stem（旋律/和声/律动/点缀），连胜≥3 加层、风暴减层（与现有 ducking 正交） |
| 6 | 高潮特殊化 | 胜利=全编制 PCM《Ode to Joy》【确认】；Abbey Road 现场乐【确认】 | WinSting 3s 奶音+duck 0.16/1.0s | 方向一致（3s 特殊化 sting vs 常规叮）；可加「与 BGM 同调铺垫」（Peggle 终局 A 大调手法） |
| 7 | 无缝循环工艺 | 采样级循环点+零交叉；混响跨越边界【确认】 | 循环制作工艺未见文档 | 缺验收口径：杜绝淡入淡出式循环；BGM 资产入库前做小节边界循环点检查 |
| 8 | 多声部预算 | 微信 Android 10 路硬限、短音效走 WebAudio【确认·官方】 | 60ms 节流已有；预算未见成文 | 缺预算表：≤8 路、优先级（捕获叮＞结算＞UI＞氛围）、捕获叮强制 WebAudio 预解码通道（0.1s 法则） |
| 9 | 多通道齐拍 | 0.1s 瞬时阈值【确认】、ITU +45/−125ms【确认】、intentional binding【确认】、音贴画面实时调【确认】 | 三通道共用 1.2s 窗、音画同源节拍（项目证据） | **已对齐原则**；缺真机验收：touch→出声 ≤100ms、音+触觉同帧 |
| 10 | 洗脑写作 | 快 tempo、先升后降轮廓、埋 1 个跳进/重复、短动机重复、曝光+近期性【确认】 | 三季四轨内容未知 | 写作规范缺位：每季 1 个 4–8 音符主题动机（先升后降+1 跳进），章界铃动机化复用，形成品牌音标 |
| 11 | 疲劳防治 | 变奏三法（转置/每调 stinger/键内变奏）＋静默窗口【确认】 | 60ms 节流＋ducking | 已有骨架；补同事件 2–3 变奏轮播与 BGM 呼吸窗（INMI：低负荷时段多发，勿填满） |
| 12 | 音色家族 | 同混响/同 voice/同供应商【确认】；软音色参照竖琴+marimba【确认·Peggle】 | 糖瓷治愈系（竖琴/marimba/八音盒方向未成文） | 缺「音色家族白名单」：治愈系限定软启动短衰减音色，禁长残响金属与刺耳峰值 |

### 6.3 分优先级建议

- **P0（先修底座缺口，不动资产内容）**
  1. 落实章界换轨：关 1–30 五个章界从单曲 bgm_main 换到四轨体系（项目自证的差距 #4）；
  2. 捕获叮/按钮音全部走 WebAudio 预解码通道，真机验收 touch→出声 ≤100ms（#8/#9；0.1s 法则+binding+Android InnerAudio 延迟证据）；
  3. UI 音定标：咔哒 ≤150ms；确认=上行、取消=下行（#3；violetrecording 30–150ms/音高文法）；
  4. 连击阶梯段距半音化（每段 ×1.0595）或对齐 BGM 调式，封顶维持 ≈+7 半音（#1；Peggle 键内阶梯）。
- **P1（低成本增量）**
  5. BGM 拆 3–4 stem：连胜加层、风暴减层，与现有 ducking（0.10/13s、0.14/1.5s）并行（#5；Tate stems 实证）；
  6. 嘟嘟奶音接入里程碑播报阶梯：连击顶格、三连胜、章界（#2；Candy Crush/Peggle 对标，资产已有）；
  7. BGM 循环工艺验收：小节边界+零交叉采样级循环、禁淡入淡出循环（#7）；
  8. 发声路数预算表 ≤8 路＋优先级+oldest-stealing（#8；微信 10 路硬限）。
- **P2（内容升级）**
  9. 按洗脑五要素重审/重制三季主题动机：4–8 音符、先升后降、埋 1 个跳进或重复音型、tempo 偏快、章界铃动机化复用（#10；Jakubowski 特征）；
  10. WinSting 与 BGM 同调/转调铺垫（Peggle 终局 A 大调→Ode to Joy 手法）（#6）；
  11. 同事件变奏库（每音效 2–3 转置/力度变体）与 BGM 呼吸窗设计（#11；Shumate 变奏引语+INMI 低负荷证据）。

> 总评：吸嘟嘟底座在**连击阶梯、ducking 让位、三通道同窗齐拍、节流**四项上与行业手法同向且参数量级合理；主要缺口集中在 **BGM（换轨未落实、无 stem 动态层、循环工艺未定标）**与 **UI/发声预算的成文规范**；里程碑播报与音色家族白名单是性价比最高的两处补强。

## 7. 信源清单
**A. 头部休闲/三消音频（§1）**
- PocketGamer.biz：Inside audio design at Candy Crush maker King — https://www.pocketgamer.biz/inside-audio-design-at-king/ （正文经抓取核验）
- PocketGamer.biz：King's Vanesa Tate on re-crafting the soundtrack to Candy Crush Saga — https://www.pocketgamer.biz/kings-vanesa-tate-on-re-crafting-the-soundtrack-to-candy-crush-saga/ （正文经抓取核验）
- King 官方 YouTube：Candy Crush Soda at Abbey Road / LSO — https://www.youtube.com/watch?v=7lNUl7RnKbs
- Candy Crush Music（社区 wiki） — https://kingcom.fandom.com/wiki/Music_(Candy_Crush_Saga) 、https://candycrush.fandom.com/wiki/Sound 、https://candycrush.fandom.com/wiki/Cascades 、https://candycrush.fandom.com/wiki/Candy_Crush_Saga_(Original_Soundtrack) 【待证级】
- 语音素材可核 — https://www.101soundboards.com/sounds/64047199-juicy-tasty-divine-soda-crush-soda-delicious
- Royal Match 音乐署名（Adam Gubman / Moonwalk Audio） — https://www.youtube.com/watch?v=qhe9ek7EmLk ；Moonwalk Audio — https://www.moonwalkaudio.com/ 、https://www.linkedin.com/company/moonwalk-audio 、https://www.linkedin.com/in/alex-cox-7ba9916
- Royal Kingdom 广告音频（Pollen Music Group） — https://www.pollenmusicgroup.com/branded/royalkingdom ；Janet Grab（多长度剪辑） — https://www.janetgrab.com/royal-kingdom/ 【待证级】
- Dream Games 内部音频博客（Medium，反爬未核） — https://medium.com/dreamlockerroom/a-day-in-the-life-of-an-audio-designer-at-dream-game-studios-4c7d673e4dfc 【待证级】
- Lily's Garden（Google Play 定位页） — https://play.google.com/store/apps/details?id=dk.tactile.lilysgarden&hl=en-US
- Piggy Match - Win Cash（商店收录） — https://apps.qoo-app.com/en/app/141447 【无音频资料】
- **Peggle Blast GDC 2015**：GDC Vault《Peggle Blast: Big Concepts, Small Project》 — https://www.gdcvault.com/play/1022188/Peggle-Blast-Big-Concepts-Small ；配套博客三篇（audiogang.org 镜像，均正文核验）：
  - Jaclyn Shumate《Realtime Synthesis for Sound Creation in Peggle Blast》 — https://www.audiogang.org/realtime-synthesis-for-sound-creation-in-peggle-blast/
  - RJ Mattingly《Peggle Blast! Peg Hits and the Music System》 — https://www.audiogang.org/peggle-blast-peg-hits-and-the-music-system-2/
  - Guy Whitmore《Scoring Peggle Blast! New Dog, Old Tricks》 — https://www.audiogang.org/scoring-peggle-blast-new-dog-old-tricks/
  （Audiokinetic 原帖 — https://www.audiokinetic.com/en/community/blog/real-time-synthesis-for-sound-creation-in-peggle-blast/ ，403 反爬）

**B. Earworm / INMI 学术（§2）**
- Jakubowski, Finkel, Stewart & Müllensiefen (2017)《Dissecting an Earworm》*Psychology of Aesthetics, Creativity, and the Arts* — 论文 PDF：https://www.apa.org/pubs/journals/releases/aca-aca0000090.pdf ；APA 新闻稿（2016-11，正文核验）：https://www.apa.org/news/press/releases/2016/11/earworms ；ScienceDaily 转载（全文核验）：https://www.sciencedaily.com/releases/2016/11/161103122229.htm ；Smithsonian（补充：90%/周、低认知负荷场景）：https://www.smithsonianmag.com/smart-news/earworm-begone-study-explores-why-certain-songs-get-stuck-our-heads-180961016/ ；Durham 作者页：https://www.durham.ac.uk/staff/kelly-jakubowski/
- Beaman & Williams (2010)《Earworms (stuck song syndrome): towards a natural history of intrusive thoughts》*British Journal of Psychology 101(4):637-653* — 仓储页：https://centaur.reading.ac.uk/5755/ ；全文镜像（docslib，正文核验）：https://docslib.org/doc/383601/earworms-stuck-song-syndrome-towards-a-natural-history-of-intrusive-thoughts ；DOI：https://doi.org/10.1348/000712609X479636
- Kellaris（2003 媒体报道） — NYT：https://www.nytimes.com/2003/08/12/health/when-the-brain-grabs-a-tune-and-won-t-let-go.html ；BBC：http://news.bbc.co.uk/2/hi/science/nature/3221499.stm ；SFGate（98%）：https://www.sfgate.com/news/article/Researcher-confirms-existence-of-earworms-98-2561479.php （原研究未发表，数字以媒体为准）
- Liikkanen 2008（>90%/周、33.2%/天）— 经 Beaman & Williams 2010 正文转引（见上 docslib 链接）

**C. SFX / UI 音规范（§3）**
- Violet Recording《How to Design UI and App Sounds》（30–150ms/≤500ms/音高文法/音色家族，正文核验） — https://violetrecording.com/how-to-design-ui-sounds/
- Denis Zlobin《A game sound designer's guide to button interactions》（交互文法，正文核验） — https://uxdesign.cc/a-game-sound-designers-guide-to-button-interactions-6837dd5cc977
- SFX Engine《Best Practices for Game UI Sounds》（情境化，摘要级） — https://sfxengine.com/blog/best-practices-for-game-ui-sounds 【待证级】
- Ross Tregenza 谈 UI 音（asoundeffect，部分核验） — https://www.asoundeffect.com/game-ui-sound-design/
- Dixon et al. (2010)《Losses disguised as wins in modern multi-line video slot machines》*Addiction* — https://onlinelibrary.wiley.com/doi/10.1111/j.1360-0443.2010.03050.x ；Templeton 等《Using Sound to Unmask LDWs》（标题/摘要级） — https://www.researchgate.net/publication/258336797_Using_Sound_to_Unmask_Losses_Disguised_as_Wins_in_Multiline_Slot_Machines
- Bornstein (1989)《Exposure and affect: Overview and meta-analysis of research, 1968-1987》*Psychological Bulletin* — https://psycnet.apa.org/record/1990-00422-001

**D. 同步阈值 / 平台（§4）**
- Nielsen Norman Group《Response Times: The 3 Important Limits》（0.1s/1s/10s，正文核验） — https://www.nngroup.com/articles/response-times-3-important-limits/
- ITU-R BT.1359《Relative timing of sound and vision for broadcasting》（+45/−125ms 检测阈，原文 PDF） — https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1359-0-199802-S!!PDF-E.pdf
- Haggard, Clark & Kalogeras (2002)《Voluntary action and conscious awareness》*Nature Neuroscience* — https://www.nature.com/articles/nn827 ；时间进程研究：https://link.springer.com/article/10.3758/s13414-017-1292-y
- Android 音频延迟定义 — https://developer.android.com/ndk/guides/audio/audio-latency ；CDD 5.6（45/50ms 建议） — https://android.googlesource.com/platform/compatibility/cdd/+/refs/heads/master/5_multimedia/5_6_audio-latency.md
- 视听-触觉同时性（EuroHaptics 2024，PDF 反爬） — https://link.springer.com/chapter/10.1007/978-3-031-70058-3_4 【待证级】；跨模态响应时间 — https://arxiv.org/abs/2305.17180
- Wwise ducking/sidechain（官方） — https://www.audiokinetic.com/en/library/edge/?source=Help&id=using_sidechaining 、https://blog.audiokinetic.com/learn/videos/dLO1Yk-NXm8/

**E. 循环工艺 / 平台多声部（§5、§3.5）**
- 微信小游戏官方《音频》指南（10 路限制/WebAudio/复用与销毁，正文核验） — https://developers.weixin.qq.com/minigame/dev/guide/base-ability/audio.html ；InnerAudioContext API — https://developers.weixin.qq.com/minigame/dev/api/media/audio/InnerAudioContext.html
- Cocos 论坛（InnerAudio Android 延迟/实例告警） — https://forum.cocos.org/t/topic/147670 ；LayaAir 论坛（WebAudio 近零延迟） — https://ask.layaair.com/d/55484-yin-xiao-bo-fang-zai-wei-xin-zhen-ji-yan-chi
- Unity Max Real Voices 默认 32（讨论帖） — https://discussions.unity.com/t/max-real-voices-always-limited-to-32/910855
- Unity-Seamless-Loop-Toolbox（采样级循环） — https://github.com/rabbitlin-web/Unity-Seamless-Loop-Toolbox ；OpenMPT Sample Crossfader — https://wiki.openmpt.org/Manual:_Sample_Crossfader ；等功率交叉淡化参数 — https://vibesdj.io/dj-tools/audio-looper ；《LOOPS》指南（目录级） — https://www.scribd.com/document/616195257/LOOPS-How-To-Create-Seamless-Looping-Music-and-Sound-Effects-Files 【待证级】

**F. 本项目证据（§6，只读引用）**
- `Design/research/调研学习/R-20260929-u314-opt-flowux-01.md`（L64/L112/L123/L135/L139：三通道反馈、章界铃+duck 0.14/1.5s、BGM 1–30 单曲证据、签名五键、WinSting）
- `Design/research/调研学习/R-20260929-u314-opt-gameplay-01.md`（L76/L83/L251：音高阶梯 8 段封顶+48%、1.2s 三通道同窗、`SfxBus.cs L23-L25`、`ActorDudu.cs L60`）

状态：完成
