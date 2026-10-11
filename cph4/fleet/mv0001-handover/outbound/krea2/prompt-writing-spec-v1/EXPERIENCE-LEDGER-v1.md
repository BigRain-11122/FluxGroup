# BigStream 内容产线经验台账 v1（EXPERIENCE-LEDGER）

> 定谳律（CEO 令 2026-10-10 13:2x「不断迭代更新这种审查机制，并积累经验，以后不要再犯，提示词技巧和 skill 积累等都要」）
> **回灌总原则：每个判例必须落一个「闸」（检查单/lint 正则/帧级 QC 检项/脚本断言）——只在台账里躺着的教训=没修。复发=闸失效=当窗升格。**
> 维护节奏：每闸收口（设计/帧/视频/成片）→席位回报新判例→本册追加行；治理窗复盘「复发=0」验收。

## 一、判例册（病→例→闸→入册日·两波十三席首版 17 条）

| # | 病 | 实例（本产线实锚） | 现在由哪个闸拦住 | 入册日 |
|---|---|---|---|---|
| J-01 | 服装品类词缺三要素（材质/版型/色名）→AI 发明违禁款 | 「simple knit top」下装零锚→S10 全身背影镜必出修身韩系（CEO 明禁面） | 服装席检查单（三要素缺一=打回）+帧 QC 检 3（宽松廓形） | 10-10 |
| J-02 | 提示词让引擎执行「事件」而非「状态」 | S6「strikes with mallet」但起点帧无独立槌→凭空变道具+粒子=必崩 | VFX 席检查单（击打类=起点帧承载·提示词只写衰减态） | 10-10 |
| J-03 | 帧内无光锚却让视频画面含光体 | KF2 帧光源画外·提示词要「边缘焰闪」→鬼火/色块 | VFX 席检查单（画内光效须有帧内锚·否则改 implied 画外） | 10-10 |
| J-04 | 两物融成一件（道具分离失败） | KF6 旧帧槌融进凿子；KF4 rod+ring 融成单杖 | 帧 QC 检 5（槌凿分离两件物）+服装席浮雕检（rod/ring 两件物） | 10-10 |
| J-05 | 文字类主体无形态学锚→随机划痕/播放键 | S6 凿下零字（歌在唱刻字=词画对撞）；KFT 纯三角无尾读作播放器按键 | 帧 QC 检 4（楔形检·三杀=随机划痕/拉丁排布/等宽机刻槽） | 10-10 |
| J-06 | 光事件批量化（N 个定时事件必崩） | S10「dimming one by one」→齐熄/乱闪风险 | VFX 席检查单（光事件 ≤2 个/镜） | 10-10 |
| J-07 | 剪辑 xfade 出肩吃后块头（桥长算术错） | T 裁 1.80 少算出肩→B 块整体早 0.4s·片尾拍点赶不上 | 剪辑席检查单（桥长=净显+双肩）+TRIMS 注释 | 10-10 |
| J-08 | 音淡出参数吞词尾 | 淡出从歌 46.00 起=吞「深爱的脸」尾 0.54s（句末只剩 36% 音量） | 剪辑席检查单（音淡出起点 ≥ 末句词尾实测锚） | 10-10 |
| J-09 | finishing 颗粒在调色前=被调色扭曲 | noise→eq→vignette 旧序（颗粒吃饱和/伽马·暗角压颗粒） | 剪辑席检查单（调色→暗角→颗粒最后） | 10-10 |
| J-10 | 工作流实配与定谳档位脱节 | 768P 工作流实配 int4·定谳/档案=int8（VFX 席实查 UNETLoader） | VFX 席检查单（开工前验权重文件名与定谳档一致） | 10-10 |
| J-11 | 正典文档新旧两版并存→执行歧义 | 立意案 §四旧时长表 vs 收口切表；「西亞面孔」残留 vs 台湾女生定谳 | 文字席+服装席检查单（定谳落典后全文档扫旧口径·supersede 注记） | 10-10 |
| J-12 | 定谳未落实现（law 在案上、不在链里） | S9「叠字不叠脸」定谳·剪辑链零字层=空转 | 文字席检查单（定谳→实现件清单逐条核对） | 10-10 |
| J-13 | 批脚本静默跳过+假完成 | kf 脚本 lint-fail/超时 continue 仍打 DONE·计数自相矛盾 | **脚本断言**（帧齐断言+missing exit 1=机制级·已入 v4.3.1 帧脚本） | 10-10 |
| J-14 | 帧级冷色渗漏（焰根蓝白） | KF1/KF6 旧帧焰根蓝白辉光=违零冷色硬律 | 帧 QC 检 1（焰根纯琥珀零蓝白） | 10-10 |
| J-15 | 暗场小主体开场=完播崩点 | S1 火焰占画面 2-3%+偏右+黑起吃 1.2s 决策窗 1/3 | 平台席检查单（正典不动·抖音变体冷开场=S6 火花/T 金字前置） | 10-10 |
| J-16 | 横版硬投竖版流量池 | S1/S4/T 三镜中心裁全报废（实帧核验）·T 金字剩三个 | 平台席检查单（发布规格=平台适配律·9 镜静态取景裁+2 镜重做变体） | 10-10 |
| J-17 | 叙事层取舍未明文→后续会话硬塞 | 「同貌轮回」30s 无古代她=缺口还是省略（两轮争议） | 情感席检查单（层取舍明文定谳入正典·省略也是定谳） | 10-10 |
| J-18 | 评审席位代理超限中断（同病两轮） | 席位 7/11 首轮+席位 7 重试全在长输出阶段断线 | **派单纪律**（席位 brief 硬约束：只读指定文件数+终稿 ≤X 字+禁复述文件内容·必要时数据内联省读） | 10-10 |

## 二、提示词技巧册（正锚技术·两波评审实战沉淀·须正反例齐才准入册）

| # | 技巧 | 正锚实例（已入正典） | 反面（禁/病灶） |
|---|---|---|---|
| P-01 | 事件改状态：击打/爆发类动作由起点帧承载，视频提示词只写余震衰减 | "the mallet has just landed, the impact trembling through the chisel and stone, pale stone dust puffing and settling, a few brief embers drifting from the torch flame" | "strikes with a wooden mallet... sparks lifting"（帧里没有的道具+动作=凭空造·必崩） |
| P-02 | 道具分离锚：两件工具写明分离+留空 | "a wooden mallet raised clear of the blade as two separate tools" + "ample clear space above the raised mallet head" | 两物并列即写（AI 融合体） |
| P-03 | 画外光 implied：光效描述不点火焰体 | "unseen torchlight from beyond the frame edge throws raking side-backlight at 2000K" | "the broad flame flickers at the frame edge"（帧内无火=鬼火） |
| P-04 | 器物固定化：held→wedged，消手持穿帮入口 | "a thick reed-bundle torch wedged in a cast bronze sconce bowl at the lower frame edge" | "held low at frame edge"（谁的手？那只手零服装锚=现代袖穿帮） |
| P-05 | 漂移词替换：语义邻域词改直给词 | "wedge-cut grooves"（直给刻痕）替 "relief ridges"（把楔字往浮雕棱带拉） | 概念滑动词 |
| P-06 | 焰收画内锚 | "the whole flame held inside the frame with clear headroom above the flame tip, the flame base a solid amber-gold" | 焰尖出画（引擎脑补收尾=撕裂/上膨） |
| P-07 | 服装三要素+正面廓形词 | 材质+版型+色名三给齐 + "un-fitted relaxed 2001 Taipei street style"（正锚） | 品类词裸奔（knit top）；否定墙 "no slim fit"（反而注入） |
| P-08 | 文字形态学锚：直给可检笔画特征 | "each sign a tight cluster of wedge strokes with clean triangular heads and tapering tails, thin ruled lines between rows" | 只写 "cuneiform marks"（AI 出随机划痕/孤立三角） |
| P-09 | 异步正锚 | "each flame flickering at its own slow breathing pace" | "asynchronously"（引擎读不懂·镜像对易同频闪） |
| P-10 | 倒影/面部钉稳：锁死+唯一微动源 | "held nearly still on the glass, only swaying faintly with her breath" / "her profile holding perfectly steady, only her fringe stirring faintly with her breath" | 裸 "her hair moving faintly"（放大成乱发飘/脸 morph） |
| P-11 | 光事件限流：N 事件→2 事件 | "the nearest case light dims, then the one beyond it" | "dimming one by one"（N 个定时事件=引擎必失败） |
| P-12 | 运镜幅度配引擎档：危险镜=small/静+短曝 | 唯一 large 幅度（S7）必须配降级链预案；静态微动=安全区主力 | 幅度词超出引擎能力=崩坏自触发 |
| P-13 | 词级动作绑定：画面动效绑到可见动因 | "the carved bands breathing in the flickering firelight"（绑火焰脉动） | "each band catches firelight in turn"（编舞式逐行点亮=不执行） |

## 三、回灌状态（截至 v1）

- 已入帧级 QC 六检：J-01（检3）/J-04（检5）/J-05（检4）/J-14（检1）——bm-c 派单已载
- 已入剪辑席检查单：J-07/J-08/J-09（build_30s_v4.py v4.3.1 已实现）
- 已入脚本断言（机制级）：J-13（帧齐断言）+字层选位缘距断言（make_s9_lyric.py ≥120px 边距律）
- 已入派单纪律：J-18（EXPERT-PANEL-PROTOCOL §六·5）
- 待回灌词表（下次 prompt_lexicon 版次）：LIGHT["torch_off"]（现为 kf_fix2_fleet.py 覆盖式正典）+P-04/P-06/P-08 锚词进 CRAFT 常备段
- 台账本体=git 正典（随仓分发全机队）；skill=.codely-cli/skills/bigstream-expert-panel（本地激活面）

## 四、迭代纪律

1. 每闸收口→席位回报判例→台账追加行→「现有闸能否拦住？」（无闸=当窗补闸·复发=闸失效即升格：检查单→lint→QC 检项→脚本断言，能机核不靠人记）
2. 提示词技巧随每次评审增册；新技巧须带正反例才准入册；复用锚词优先回灌 prompt_lexicon（版次递进）
3. 席位评审派单必含读文件数+终稿字数硬约束（J-18 律）
4. 治理窗（10-16 起）复盘验收线：同病复发=0

---
*v1·bm-a·2026-10-10 13:2x·首版=两波十三席全量判例 18+技巧 13·CEO 令 O-20261010-1320*
