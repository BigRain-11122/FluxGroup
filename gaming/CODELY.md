## Codely Structured Memories

# CODELY 全局结构记忆 — 分层制 v3（2026-10-15 立·2026-10-18 记忆治理席 memory-curator 接管）
> 机制：注入面预算（预警 35KB/80 条·执法 50KB/120 条）·Tools/memory-budget-gate.py v2 每 4h 静默闸（S4U·快照零删除·法条自动保留+同题去重）；长文/状态/领域细节=memory/topics/（按需读·索引见 ### Reference）；>300 字新条目=先落主题文件再回写指针；跨机价值一律走 git 正典+L1（memory.md §8/§10·联合回灌已退役）；写入纪律正身=skill memory-curator（cph4/skills/）。

### User
- [2026-09-24 15:14:57] CEO 花钱决策律（2026-09-24 服务器案实证）：资本项/采购项=先本地验证、可实证后再掏钱——服务器购买卡备好后 CEO 裁「你先开发好服务器端，本地测好再说」＝钱花在验证过的东西上、零返工风险优先于速度（并接受备案 1-4 周时钟后移的对价）。How to apply：今后向 CEO 提采购/订阅/付费方案时，标配「零成本前置验证路径」选项（沙箱/试用/本地测），勿默认推「先买」；验证判据预注册先行（AC 全绿+独立复核）再呈购买建议。与既有「速度优先律（token 可以烧）」的边界：token/算力消耗=速度优先；资本项采购=验证优先。

### Feedback
- [2026-09-23 16:17:31] MiniGame 人设域与管理域分离常设律 U172 已落册（2026-09-23·X767 批·commit 7e4961ce·CEO令「对 以后我说的其实都是虚拟人设， → 全文档案: .codely-cli/memory/mem-20260930-g-002.md
- [2026-09-28 14:58:11] CEO 纠偏令（2026-09-28 原话「我要你去unity引擎实际拼出来2D地图 不是出图！」）：FluxVerse 2D 大地图必须是引擎真拼接——Unity Tilemap + 真 Tile 资产逐格 paint / 物体 SpriteRenderer 逐个摆放；严禁把整幅 AI 生成图当一个 Sprite 贴场景（出图=死图：不可编辑不可扩格不可逐格迭代，且与拼接工具链方向[Unity-MCP/RuleTile 链]相悖）。AI 只可用于「素材件」（角色/建筑/树等个体 sprite，去底入引擎后拼装），地图装配必须在引擎内完成。城市版式数据驱动（Tools/city/td-organic-layout.py 的路网/水系/广场格数据）+瓦片 autotile（邻接掩码选变体）为正身做法。
- [2026-09-30 18:56:56] [2026-09-30 18:5x] CEO 定谳令 O-20260930-1706（09-30 ~17:0x 原话「以后2D 动作和特效，全部采用本地生成短视频取关键帧的做法，好好按这个思路去学习和调研，并写好机制和流程，全面赋能每个游戏项目！」·18:5x CEO 再申「我说了游戏项目全部走C方案啊！然后合理取关键帧」当场纠我窗汇报）：**全游戏项目 2D 动作/特效美术内容生产径恒＝本地生成短视频→科学取关键帧→sprite 图集→引擎逐格播放**（图集正典律 O-2026-0930-001 承接）；A 部件骨骼/B 3渲2 不再作游戏项目主径（O-002 在飞批收口即止不续投·完成件留用·产出转对照档案；城市线 B〔硅基居民 3渲2〕域外照旧〔O-031 载体边界〕）；取帧法＝五律+极值采样 5-8 关键帧（CEO 亲定档）+相邻帧连续性探针+漂移过滤+循环缝选优；正典件＝《2D 动作与特效生产管线 SOP（本地视频取关键帧）》落 MiniGame/_共享与总控/；试点＝嘟嘟待机/步态+胜利特效帧；边界＝程序化 UI 动效与引擎实时粒子系统不在本径；收口判据＝SOP 入仓+试点图集引擎播放取证+审核板呈审；承接＝@CPH4 实验室窗（2dlive-spike）自领在飞。**判负教训（本窗实录）**：被问「怎么做 X」类方案问题时按旧 T1 对比结论（O-023 A 主径/B 辅助/C 降级）直接作答，与 1.5h 前已注册的 O-1706 直接相悖——方案/定谳类汇报前必先 grep orders.md 最新相关令（新鲜验证律违例实证）。How to apply：游戏 2D 动画/特效一切批按本管线走（先读 SOP·工具链在 MiniGame/Tools 共通面）；答「方案/计划」类问题先查台账再开口；A/B 线范式件＝对照档案可引不可续投。
- [2026-09-30 20:55:18] [2026-09-30 19:2x] CEO 呈审门自律令（原话「我现在的研究标准非常的高，不要轻易的就让我看」·orders O-20260930-1925③·与同令①Biggame 全速研发②存量游戏全量回流程一体落地）：一切呈 CEO 的交付物必过全闸链后才呈——闸0 真包实跑像素取证+五闸链全绿+独立复审（执行侧不自证）+玩法/系统批 8 分硬闸+呈审必附五闸执行记录；未全绿呈 CEO=呈审质量事故（U324 呈审素材事故/O-1610 首页判负两先例同源）；呈审降频提质=宁可少呈不可滥呈。存量回流程九步链（逐款记分卡入仓+FAIL 返工闭环）：闸0→五闸链→十维 8 分→黄金前置律→音频 14号门+机器耳 8 分线→图集正典律→2D 动画 C 管线→板·引擎同源律→包体四值微信官方口径（主包≤4M/总≤30M/单普通分包不限/独立分包≤4M）。How to apply：任何呈 CEO 面收口前自检三问——真包取证在板？全闸绿？独立复审过？缺一禁呈；款级回流程走九步链逐款记分卡；CEO 只看全绿件=呈审面新常态。
- [2026-10-01 22:10:28] [2026-10-01 22:1x] Biggame 资产标准化 SOP 令（CEO 原话「尤其子公司要全面做好资源的复查、尺寸。又按小游戏的标准去做…一个 Button 或者一个 Icon 需要多大，这些都是可以在业界查到资料的〔「业绩」=「业界」STT 误写〕。不要超限，然后该抠图的抠图，抠干净。就是资产一定要有一个标准化地 SOP」·orders O-20261001-2209·O-1925 深化批）：五件套=①控件尺寸业界标定（Button/Icon 规格表·WeUI/HIG/Material 触控界标·调研件 R-20261001-asset-size-standards-01）②限额面（包体官方四值/单件尺寸帽/纹理 POT/密度律）③抠图干净门=去底机检判据（背景残留/halo/毛边检测化·入五闸闸2 收件三查）④存量资产逐件复查（与九步回流程并轨·FAIL 返工）⑤《小游戏资产标准化 SOP》立典（挤旧不新增：图谱 U275/SOP U276/母版 U284/产件律 U285 照旧·新件=总纲+尺寸表+限额+抠图门+复查流程）。How to apply：Biggame 一切资产批先查尺寸规格表+限额面+抠图门三件；抠图验收=机检（非目测）；资产收口必附规格符合度记录。
- [2026-10-09 12:11:15] bm-a CEO 小游戏按钮密度律（2026-10-09 ~11:5x 原话「现在按钮的信息密度太高了！怎么越改体验越差！你做的是小游戏！」·Biggame UI 长期硬门·U362·U274「完成度≠信息密度」在游戏按钮面延伸定谳）：①按钮=名字一物，状态全视觉化（色/锁标/高亮），零状态句（「在身上～」「通关第X章解锁」「，点一下！」类全判负）②计数=纯数字（0/30）不带头词不拼奖励句③说明行单句化（「每天零点刷新」「每日签到」——机制解释句=密度垃圾）④修按钮缺陷禁缩字号硬塞排版——砍信息优先。Why：衣橱 19 钮双行+任务行三连句为历史批累积，CEO 判「越改体验越差」。How：新 UI 批呈前过密度自检（每钮≤1 行≤1 短语）；正身实例=WardrobeScreen 锁标视觉件/DailyTaskScreen 句式瘦身+签到 44 档回 56（文案锁 TestCheckInUi/TestDailyTaskUi 同步）；权威=登记簿 U362+矩阵 §9.99+orders 10-09 密度令行。
- [2026-10-09 22:29:40] bm-a B1686 律再犯实录+姊妹坑（10-09 16:5x P 系改名同步批）：①根仓 `git commit -F` 不带 pathspec=吞他窗 index 暂存面 97 件（outbound krea2 交付件 untrack 半途操作+oss-harvest 1 件）误删上链已推送→正法收口=`git checkout <事故提交>~1 -- <误吞路径>`+pathspec 限定 commit 恢复推送（13dc4f3→aec05e0 实录·同批 README 改动保留·他窗磁盘文件本就未删）；②**姊妹坑=pathspec 过窄**：MiniGame 重提时 pathspec 只写四目录+白名单=漏 102 件工程/作者档/登记面（首提 03d41416f 86 件·补提 e30e7e80a 102 件）——正法=add 与 commit 双用**全量显式路径清单**（一次写全两处同用·勿缩写）；③git mv 目录会触发 GitBloatGate 对全目录件按新路径重检（历史在库 PNG 算「新件」）→改名批须预扫 >1.4MB 件补 dated 白名单条目（P06/P08 提审截图 5 条实录）；④P 系改名定谳在案：镇魂师→提灯斩鬼（P01·LanternSlayer）/宿命之门→异界行者（P02·FateGate）/寻香记→调香师（P06·SongOfScents）/阴差不良人→奈何桥（P08·GhostMarshal）——权威=软著申请材料 generate_copyright.py PROJECTS（CEO 10-09 16:41 亲改+重生四款材料）；同步律=工程 productName(escaped)/i18n 提审红线字段/登记簿款名行/工具探针 tag 与白名单路径必须同批全改（E-030 探针漂移前科）；保护面=_归档存量软著源件原名法定不动+evidence 史行+像素字库（4 缺字斩奈何桥转像素镇 owner 窗）。

### Project
- [2026-09-28 19:19:10] U285 CEO 原话立典判例（2026-09-28·MiniGame a0c968988 已推·HQ 879479f）： → 全文档案: .codely-cli/memory/mem-20260930-g-033.md
- [2026-09-28 21:55:16] City lowpoly 3D 转型立项判例（2026-09-28·CEO 令原话「全面转型lowplay 3D风格…我说的是硅基生命城市美术风格」）： → 全文档案: .codely-cli/memory/mem-20260930-g-035.md
- [2026-09-29 17:21:42] 吸嘟嘟双版本并行定谳（2026-09-29 CEO 令原话「吸嘟嘟分2个版本，并行推进开发，2个风格我都觉得可以」）：A 版=3D 渲染定谳风格（现七屏线延续·主角从 A 批挑）｜B 版=2D 水彩（夸张记忆点线·主角从 B 批挑）——U279 单一定谳就此修订为双轨（新令驭旧令·04号 V3.0 定谳宣言面待补双轨注记）。B 版基底=U281 三层保全的水彩 R6 资产组（C:\Agent\ui-forge\U279_prep\art_backup_v2_watercolor 61 件+U274 R6 证据）可直接复活省整轮 UI 量产。两版主角=审核板 A/B 批各挑一款（CEO 回复编号）。台账登记待 U307 收口合并落行（落行前重扫撞号定 U 号）。
- [2026-09-30 14:50:59] [2026-09-30 14:5x] U326 判例收口：吸嘟嘟音频 v2 复听回执批（CEO 回执原话「口哨音不好听，去掉缓存奶音嘟嘟试试，或者别的也行。 → 全文档案: .codely-cli/memory/mem-20260930-g-084.md

### Reference
- [memory-gate] 记忆分层主题索引（按需读·verbatim 全量在档）：
archive-misc.md（43 条）=../.codely-cli/memory/topics/archive-misc.md
fleet-dispatcher.md（31 条）=../.codely-cli/memory/topics/fleet-dispatcher.md
game-dev.md（45 条）=../.codely-cli/memory/topics/game-dev.md
git-surgery.md（11 条）=../.codely-cli/memory/topics/git-surgery.md
governance-council.md（3 条）=../.codely-cli/memory/topics/governance-council.md
hardware-procurement.md（3 条）=../.codely-cli/memory/topics/hardware-procurement.md
local-inference.md（3 条）=../.codely-cli/memory/topics/local-inference.md
mv-production.md（23 条）=../.codely-cli/memory/topics/mv-production.md
quant-backtest.md（7 条）=../.codely-cli/memory/topics/quant-backtest.md
shortvideo-bili.md（5 条）=../.codely-cli/memory/topics/shortvideo-bili.md
tool-pitfalls.md（41 条）=../.codely-cli/memory/topics/tool-pitfalls.md
- [memory-gate] 历史瘦身快照=memory\cleanup-* 与 cleanup-gate-*（零删除回滚通道·联合正本冻结件=cph4/fleet/memory/archive/）

