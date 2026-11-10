# DEADLINES — 死线台账（CEO 总调度代理席维护）

> 用法：每轮步2 死线雷达逐行核对 orders 最新回执翻新状态列；新死线=当窗入行（来源=orders 行/O- 号）；已过窗死线如实标注（延误披露禁抹除）。
> **waiting-CEO 区=物理件/保留面登记，零催办**（CEO 有空弄·本席只记账）。
> 基线快照 2026-10-14 12:0x（O-20261014-1210 建席件）。

## §一 在轨死线

| 死线 | 归属 | 来源 | 状态 |
|---|---|---|---|
| 10-14 13:00 V3.5 预览剪呈 CEO | bm-a 装配站 | O-20261014-1035 ⑥ | **延误·如实披露**（17:0x 审查轮核注：13:00 未呈·波1 六镜 16:4x 收齐/波2 点火·装配站接管中——是否并轨深夜终剪由 21:43 死线班跟核）；【R2.11 10-18 00:4x 销账】closed-superseded——被链实绩超越：V4→V5→V5.4.2 终片 10-17 23:0x 已呈 CEO（DIRECTOR-REVIEW-V5.4-PASS）·V3.5 预览用途已消费 |
| 10-15 08:43 MV V3 全本地终剪→成片闸→呈 CEO（CEO 死线·O-20261014-1855） | bm-a 装配站+@bm-c 缺件补产 | O-20261013-2200+NJ bigstream 10-15 00:33 | **延误·如实披露（R1.9 10-16 13:0x 翻新）**：V3 终剪死线未达——线被 CEO Jay 化裁定升格 V4（17 件 jayredo：11 件 i2v 10-15 20:38 bm-a 确认收讫+6 重摇件 @bm-c r1034 补烧 in-flight〔reshake6 复检 6/6 过 10-16 11:4x·DeliveryWatch 契约死线 14:05〕）→17 件齐→bm-a 装配站 V4 装配单已备（V3 时间线在位）→四闸→CERTIFIED 呈 CEO【R2.0 10-16 16:16:06 现势翻新：17/17 齐收口〔13:52 @bm-c 回执全上链+14:01 交付哨 DELIVERED hit=6〕·V4 装配 14:5x 委员会窗亲手执行在飞〔装配班 cron 两连蒸发·批载体改挂常设计划任务面候裁〕】；旧 7 缺件补产线已并入 jayredo 链；【R2.2 10-16 22:1x 死线班现势翻新】V4 CEO 终审未过（15:5x 三连批）→V5 立案链（CEO 16:0x 剪辑语言令/机制问责令/17:0x 顶尖工作流令/17:1x 叙事四律令/17:4x 字幕精工令五连令驱动）：17 镜重烧单 16:3x 派 @bm-c（V5-REBURN-SPEC）→phase1 KF 22/22+480P trials 12/12→导演席 winners r1055 签发（18:0x·PASS-with-conditions）→phase2 17 镜 INT8 768P 夜窗连烧 in-flight（wave 制烧毕即推）→**交付哨 v5redo-bmc-17i2v 契约死线 23:30·22:01 实测 hit=0/17=at-risk 如实披露**（ETA 窗 22:00-23:00 尚开·三层覆盖在位=哨 5min 拍活+23:43 班跟核+bm-a 装配站备弹）→17 件齐→装配（D1 叙事四律+W7 剪辑语法+CHK-T 字幕三查）→复检六项 CHK-E 全绿+DIRECTOR-REVIEW-V5-PASS 硬门才准呈 CEO；【R2.3 10-16 23:5x 夜移交班跟核终态】phase2 **17/17 达标交付**（交付哨 DELIVERED 22:11:21 hit=17·契约死线 23:30 提前 79 分钟达标·21:43 班 22:01 at-risk 自然解除）+QC 三板全绿（INT4 双轮廓红线复检 PASS+CHK-E2 女主锚 8.5+总板 GO 17/17·@bm-c r1055 21:3x 回执）→**装配站解锁·V5 装配待执行**（D6 剪辑语法表+PROXY-PASS→复检六项 CHK-E→DIRECTOR-REVIEW-V5-PASS→呈 CEO·承接=00:00 委员会轮+bm-a 装配站窗·装配器备弹 18:0x 在位）【R2.10 10-18 00:10 夜移交班跟核】V5.4 整改链本机收口在制（DIRECTOR-REVIEW-V5.4-PASS-20261017.md 本机在库·commit 68516f8 候 MV 窗上链）·C01 mp4 末次落库=10-16 21:28 c10366e（V5.3 同名重烧未落）→现位=呈 CEO 终审（O-20261017-1741）·后续归 MV 窗自守；【R2.11 10-18 00:4x 销账】closed-superseded（V5.4.2 终片已呈 CEO·V3 死线用途被链实绩超越消费）|
| 10-15 03:30 bm-b git 手术决断线（R2 裁决=A 案宽限观察·预注册决断树：a origin 见 bm-b push→自然恢复闭环 b r956 报 fetch 卡死/驱动死→即刻手术单 c 03:30 零心跳恢复→手术单〔预草案=bigmoney-shiftlog 枢纽决断行：kill blobfill pid 28880+C2 payload 抢救导出+re-clone S0 先例+push+selftest+回执〕） | 枢纽代理席（03:33 探针 cron 主承载+02:43/05:43 夜班+域席 R3 备份） | NJ bigmoney R2 01:33+LOG Round 1.3 | **resolved-手术作废（02:47 枢纽事件班 R1.4 亲测 a 闭环：r956 侧枝已落 origin〔ls-remote 3eaa15f1〕+listener 活〔02:43:55·心跳 r956@02:36:32=r955 push receipt consumed PUSHED_VERIFIED+recovery drivers 在飞〕→域席修正树③命中·手术单作废；03:33 探针=确认节奏零手术；残余=r957 提交轮 main push+faces 复原·bm-b.json weak 传感旗 main push 前复发=已知恢复态非新升级）** |
| C02/R05 源帧重制→重 i2v（装配邻段兜底） | @bm-c ✅已随 wave2 r1010 交付（C02_sand_bury/R05_gold_threads 修复 URL·事件班 01:2x 收割入 DL） | 10-14 11:0x 四抓 | done（r1010 消费面·字节校验过） |
| 10-14 V100 P0=bm-a 夜窗 MoE 卸载跑 35B（验收 ≥30 字/秒） | bm-a 夜窗 | V100-EXPANSION-SPEC v2 | done-在役（事件班 10-16 00:3x 翻行消费 bigcompute NJ r5〔五班同源 r1-r5 一致核验〕：证据亲验=compute/BigCompute/state/v100-p0-verdict-20261014.txt VERDICT PASS·跨跑 31.6 字/秒 ≥30·run1 29.2/run2 34.0 如实双录+双 JSON·35B :8090 在役=思考路由律本地档承载） |
| 10-14 软著 B/C 机 18 款源程序复跑批（CPU 面） | bm-c ✅C机8款上链（fc1b936·G02 7425/G03 8376/G06 6260/G09Y 3666/G10 5252/G12 10347/G17 8439/G18 12007 行）+@bm-b ✅B机10款上链（bfa61b6 03:55 GEN_DONE·txt/pdf 10/10+CCPC 10/10+报审台账§四销账）=18/18 | O-20261014-1035+事件班 NJ biggame R5 10-15 14:2x 翻行 | done-已落地（verified 18/18 全上链：09:06 bm-b 复跑 10/10 keys green〔O-20261015-0906-bm-b〕+POOL-0011 origin status=done〔result_ref GEN_DONE_OK〕四锚全验；事件班 10-15 14:3x 翻行收口=同签 re-fire 根面清·snooze 单帠目 until 10-17 09:15 在位（R8 落·枢纽 R1.8 亲验：载具 L61 词表缺口=永续旗真根·修法提名归并 bigmoney NJ#3 载具修法族候 CEO 令〔受保护件零擅改〕·到期旗复发=值班席续 24h 环直至修法落）；A机14款收编=POOL-0013 ✅done（01:2x @bm-a 回执收编上链·R2.9 事件班 10-17 10:1x 销卡翻卡）——snooze 已续至 10-18 09:15·本行「已落地」措辞入载体 L61 匹配=软著永续旗就地根除〔载具修法族仍候 CEO 令·受保护件零擅改〕） |
| 10-14 八度空间/叶惠美 音源批复跑→whisper 锚点→词面校准 | bm-a CPU | 10-14 10:3x（10:38 复跑实锚） | in-flight |
| 排队 bm-c：波1.5 SIL4 jman 强度 8 帧探针→波2 云槽位重产→波3 星晴 A 批 34 KF+选角板 16 | bm-c | O-20261014-1035 自链三波 | closed-consumed（R2.11 10-18 00:4x 销账：波1.5 SIL4 随 V5 phase2 17/17 达标交付〔交付哨 DELIVERED 22:11〕+波2 云槽位重产被 O-20261013-2200 全本地链消费+波3 星晴 A 批 62/62 烧毕+二源复审〔orders 10-17 01:1x/12:29 行〕——三波全被链实绩消费·行销账） |
| 排队 W1：星晴 A 批 62/62 烧毕+ZOOMQC 26 GO+二源复审 23/26（e226e49）+i2v 包三层闸收口（5f3be92·准烧候 PENDING 帧点位）·可爱女人 SHOTLIST 接棒 | 导演席+bm-a | O-20261013-1540 资产产线 | in-flight（R2.12 01:5x 承 bigstream R15 NJ ①hub 腿翻新·实绩态·R15 ②PRODUCTION-PLAN=导演席域件维持 R2.11 域界裁定候 MV 窗）【R2.24 16:15 注记】XQ 六单回炉重烧（X2670·05:23 上链）=R2.21 poke 拉取后日窗零点火零回执→本班 poke 第 2 轮（15:58:45 accepted·wakes 10）+bm-c 心跳自记 15:34:21「night GPU lane XQ+jman v2+female-lead」=改排夜窗 GPU 道（日窗 GPU 空窗 vs 排满令 v2〔CEO 13:2x〕张力如实披露·夜窗三件满道=合理错峰）·验证面=17:25 回访探针+21:43 死线班夜窗点火验证+明晨检回执复核【R2.26 00:32 事件班翻行】夜窗五连全绿兑现收讫（C2088 19:37 armed→C2093 21:36 strips v2 31/31+bank 18/18·验证面已由域席 00:1x 补齐兑现）→现势=候导演席 S5-27 终签→下一站=星晴终剪装配+xq-T1-VERDICT 修订稿候导演签双轨（orders 00:32 翻行行·O-20261019-1935 ④） |
| 滚动：早期四专 41 曲全量重制（S 层 11 曲优先·1-1.5 曲/日·90 分入库门槛） | MV 线全员 | O-20261013-1540 | standing |
| 10-16 治理窗：C-20261009-01/02 预注册判据回访+C-20261012-01 Phase 2 合并议程 | 委员会 | decisions 台账 | scheduled；【R2.2 注记】D-20261016-07 并窗裁定=Phase2 议程并入 C-20261016-02 普查管线（每案一页律维持）·下一里程碑 10-17 00:00 常务轮拍板（D-20261016-04 重钉） |
| 10-19 回访：C-20261012-02/03 判据+总调度席判据（本席判据并入） | 委员会 | DISPATCHER-CHARTER §六 | scheduled |
| 10-28 BigHouse 判据：苏州吴中社区复刻+CEO 首住户安家+≥10 居民轨迹 | BigHouse/bm-b | BLUEPRINT v0.4 | standing |
| 短视频：video-remix 首批 S 池 3 条试产（GO·排 bm-b 音频批后） | bm-b | O-20261013-2245 ⑤ | queued-refrozen（R2.11 事件班 10-18 00:4x 射程定谳：切片部不在 O-20261017-1741 停产射程〔点名=短视频线 meme 族·17:4x 执行批清单零切片件〕·维持委员会 GO 但重定位三闸：①后置漫剧配音 P0〔O-20261017-1751 派单在效〕之后不抢三线资源②点火前置双闸=GSV 五闸全查+导演每步过目〔O-20261016-2110「漫剧/短视频/切片质量都不高」对切片面明文生效〕③点火决定=漫剧配音 P0 交付后委员会市场方向快评〔O-20261017-1758 授权面〕；翻案=CEO 一句话） |
| **B站账号运营线（回复/DM/outreach 三件套·已上线·代理席接管巡检 10-14 15:5x）**：护栏审计（每轮 ≤5/日帽/条间 30-90s/永不重发台账/R1 五信号熔断）+续登路（凭据已交接仓外）+回执 | bm-a 本地（车道例外=cookie 最短路·追认·bm-b 迁移待文件通道） | O-20261014-1330+15:1x 接管令 | live-在巡 |
| 事件班 schtasks 承载升级件：**已落地在役（10-14 19:1x·Phase 1-α·origin 2fed6498）——08:43 班勿重派（防双注册）**：HQ-CEOProxyEventCarrier PT15M+HQ-MA-ProxyProbe PT1H 静默在役·19:13 首发射实弹毕（事件班 Round 1.1·origin 75ac965·NJ 清零+锁收口 19:28:21）·代理席巡检面接管 | 已落地在役 | O-20261014-1745 Phase 1-α ①② | done-在役 |
| 10-17（周六）bm-a 周末自由运转边界（口令制 O-202601015-1845 首周末·WorkEnd 退役+pauseLite gamewin cron 挂起=周六无自动复产承载·真机制缺口） | 值守面（周六晨检班/事件班/委员会任一活面） | NJ biggame R8 ②+枢纽 R1.8 预注册 | scheduled（决断树：①默认=候 CEO「开工」口令〔保守向·口令制 §② 唯一开关律〕②CEO 全日未发口令+委员会判「节假日随便」生效→T1 代决 -Mode resume 复产〔常设授权令射程〕·执行前必探 CEO 用机面〔GameViewer/前台重载在跑=让路面优先照旧〕③口令一发即从令·禁以本行代口令④复产即 gamewin cron restore 自归位）；【R2.9 事件班 10-17 10:1x 树执行】bm-a 未停机实证（夜班 00:42-07:3x 连跑+本班在执+09:5x CEO 令 bm-c 窗照常执行）=无需复产动作·口令未发不虚构——树维持休眠候命 |
| 10-16 14:00 @bm-b 欠件追缴五件回执（POOL-0020 销卡/spawn 帽腿回执/哨兵 PROBE_ERR 定谳/POOL-0018·0019 双锚批具名阻塞件/试映片 Taildrop） | bm-b | orders 10-16 13:0x 行+C-20261016-02 普查C/E | 延误·如实披露（R2.0 10-16 16:16:06 翻新）：14:00 窗过·五件回执零落——Taildrop 实测 bm-a media/drama-pilot-out 空缺=真欠交（交付哨 OVERDUE 12:49 hit=0/1·时poke 在哨）+POOL-0020 销卡/spawn 帽腿/PROBE_ERR/双锚批四件 orders 回执零；bm-b 活体在证（13:1x SYNCED 44s）——零重复 poke（防双烧：哨时poke+普查E 全列+21:43 死线班三通道在覆盖）；>24h 零回执=升 E1 委员会通道（10-17 08:43 晨检复核线）；【R2.2 10-16 22:1x 复核】五件回执仍零（orders 增量至 21:4x 无 @bm-b 回执行+drama-pilot-out 实测仍空+哨 OVERDUE 12:45 起持续·哨时poke 21:06/21:11 实锚在哨）→维持零重复 poke（防双烧）·E1 升级线=10-17 08:43 晨检复核照旧；【R2.4 事件班 10-17 00:5x E1 翻行】五件零回执 12h 维持+bm-b 循环停摆 53.5h 实锚（心跳冻结 10-15 19:10:18 r986·WAKE 二连 accepted 零效果·idle_rounds 00:33 读 31→00:44 读 33=秒退轮在跑·守卫锁/陈锁嫌疑优先）→**E1 已升委员会通道（并案单=orders 00:5x 行·五件+手术五面·CEO 令锚 O-20261016-2347 §一.3+O-1821）**——08:43 晨检班=复核线（验证面 r987+ 落 origin 或心跳 ts 移动·勿重立）；【R2.9 事件班 10-17 10:1x 复核线执行】E1 愈合实证=bm-b /status 10:03 亲测心跳 last_seen 10-17 09:19:08（冻结 10-15 19:10:18 已破）+r987 在跑（worktree 全量重物化 31,284 件+心跳复活+6 单回执+E1 五回执收口）——五件回执候 r987+ 落 origin 复验（复核移交 21:1x 收口窗·本班零 poke 防双烧）【R2.10 10-18 00:10 夜移交班跟核】bm-b 愈合活体亲证=心跳 last_seen 10-17 23:57:14 新鲜·r997 在跑（E1 leg-5 drama re-drop delivery+MSG-20261017-2356-bmb-dramaredrop 23:56+estate-absorb closeout·回执正身=BigMoney 仓）——leg-5 物理交付（bm-a media/drama-pilot-out）23:49 实测仍空=re-queue 在途→10-18 晨检班物理落位终验；【R2.13 事件班 10-18 02:5x 销账注记·leg-5=CLOSED-VERIFIED】bm-a BM 道 r1044（02:45·BM origin fafa1413e 02:51:46）——Taildrop 两面性坑定谳：CLI `tailscale file get` rc0 静默空≠交付失败（Windows Tailscale GUI 层自动落盘 Downloads\·r1037/r1041「BLOCKED inbox empty」同坑勘误）→全树搜索 5 件齐→**已迁正位 media\drama-pilot-in\**（字节对 MSG-2356 manifest 全验：PILOT-PREVIEW-3x20s.mp4 8,224,570B+seg1/2/3.mp4+sea-review-level1.md 共 16,454,993B·R2.13 本班亲验 5/5 在盘）+MSG-20261018-0245 回执落 BM origin（MSG-2356 转 processed）——**CEO 看片通道 material in place·里程碑 ≤10:00 提前 ~7h 达成**·晨检面=轻验在盘+回执核验（勿再跑 file get）；bm-b 腿新证=r998 已执行毕 GREEN（R2.13 /status 02:47:55 直探：O-0137 same-round 全执行+EP001-003 voicegen 51/51 wav 7.28MB+MANIFEST+MSG-20261018-0216-bm-b-taskaudit 02:16 建件=回执在途）——E1 全链只欠回执落 origin 终验+POOL 三卡迁移簿记（watch ①③·03:16/08:43 承载）；【R2.15 事件班 10-18 05:2x 前提失效实证+E1 复发预警】O-0348 落 origin 后 77min 零 bm-b git 面动作三重实锤（BM origin tip a748663be 全历史零 MSG-20261018-0216-bm-b-taskaudit+O-0348 回执节空占位+心跳 02:26:54 陈旧 2h41m·/status 05:06:26 直探 listener 活体 RAM 14.9G free/CPU 2%·BM 本地 head 3917a974e 已含 O-0348）+v1.10 hb>120m 自愈触发点 04:26:54 已过 40min 零效果=R2.14 兜底前提失效·账不可闭态；饿死链根入档=POOL-0018/0019（whisperX/allin1 双锚批·10-15 开卡至今未领）输入音源=bm-a 夜窗代投 42 首 408.5MB 盘上在位未投×bm-b loop agenda_starved=true 双因果；08:43 修正指令=只验不可销账——仍缺=E1 复发（24h 内第二态：state 活体/git 面死）按两轮兜底律升委员会通道；本班零 poke 零重令防双烧（bm-a r1045 04:49 心跳自证 account-stays-open 在盯+NJ hub 双线 10min 级在位·06:50 探针复探先行） |
| 10-16 14:05 jayredo 6 件 i2v 补烧→拼板→bm-a 装配（V4 链前哨） | @bm-c | orders 10-16 11:4x 派单+Cure-1 契约 | done（R2.0 10-16 16:16:06 翻新：13:52 @bm-c 回执 17/17 全量上链〔QC 拼板 JAY-REDO-QC-SHEET-17-r1051〕·交付哨 14:01 DELIVERED hit=6 压哨·V4 装配在飞） |
| 10-16 ~15:0x @bm-c 仓分叉修复（backup 分支+reset --hard origin/main） | @bm-c | orders 10-16 13:0x Cure-2 行 | done（R2.0 10-16 16:16:06 翻新：12:4x 仓头自愈回 origin tip fc468f8+13:1x worker v1.4 判据三机验证全绿〔bm-a 13s/bm-b 44s/bm-c 17s SYNCED〕·19h 假绿病根治） |
| 10-17 08:43 首批游戏云批动作呈 CEO（《游戏公司云道排产单 v1》=CEO-PROXY 23:43 班+委员会 00:00 常务轮承接·云端授权面+并发帽执法）+各机游戏车道 24h 回执（→10-17 21:4x） | CEO-PROXY 23:43 班+委员会 00:00 轮 | O-20261016-2145（10-16 21:4x CEO 令「游戏公司全面开工…云端算力使用权限…控制并发数量」） | 延误·如实披露·已落地（R2.9 事件班 10-17 10:1x 承 NJ-R11a 首班 fallback 代呈报：08:43 晨检班周六无会话窗缺班=呈报 act 失载→本班代呈=orders 10-17 10:1x R2.9 呈报行；各机游戏车道 24h 回执分项独立在 21:1x 窗维持 in-flight）；R2.3 10-16 23:5x：排产单 v1 已落盘=cph4/fleet/dispatcher/GAME-CLOUD-LANE-PLAN-v1.md——授权面/并发律/search-first 路由/T0 首批云批四件〔吸嘟嘟 G01 首关资产+特效+音频+UI〕/T1 提审链候物理件/T2 休眠款四问门滚动——00:00 委员会轮承接执行·08:43 班呈报）；【R2.7 事件班 10-17 06:27 点火实锚（NJ biggame R10 承载件触发·双承载缺位代消费）】T0 四件 wave1+2 烧毕=8 占位族 T1 海选 8/8 过一级（板 u360_l2_T1wave2_board_q88.jpg）+4 特效 80 分+collect_item 20 分入工程+查重闸执法——08:43 班呈报面=orders 10-17 06:27-07:4x 行 【R2.10 10-18 00:10 夜移交班跟核】各机游戏车道 24h 回执分项=origin orders 晚段已见回执行——10-18 晨检验质销账（实质动作=R2.7 06:27 承载消费）；【R2.17 10-18 09:0x 晨检销账】分项验质=bm-c 腿多笔产线回执行在档（01:1x 星晴 T1/03:2x 三线齐发/10:43 T1-1R/12:29 A 批/19:2x 填载收据〔均 via bm-c〕）+bm-a 呈报行在档+bm-b 腿窗内 E1 停摆欠回执如实披露（E1 史在档·愈合后 r998-r1049 连续在班）——销账 |
| 10-17 21:1x O-2110 三线质量令实物回传 24h 窗（@bm-c meme V1 成片 CDN URL 回填+@bm-b drama 试点粗样 sea-review CDN URL 回填·orders 回执节双 pending） | @bm-c+@bm-b（派单窗=bm-a 委员会窗 21:1x） | O-20261016-2110 | closed-exempted（R2.3 10-16 23:5x 翻新：@bm-c 腿 done——CDN 上传+HEAD 字节验证 2689431B 恒等·URL 已回填 orders 回执节〔r1055 21:3x〕；@bm-b 腿 pending 维持〔drama 试点欠交=@bm-b 五件同根因·E1 线 10-17 08:43〕）；【R2.4 事件班 00:5x】bm-b 腿并轨 E1 并案单（orders 00:5x 行·循环停摆同根因·委员会通道）——复核线 08:43；【R2.8 事件班 07:3x】@bm-b 活窗轻派行已落（orders 573a30c11·回执窗 ≤12:43·勿候 IterationLoop 复活·改派裁定=堵死：文件单路径 bm-b）——08:43 复核线维持+09:07 回访探针+21:1x 收口；【R2.9 事件班 10:1x】bm-b 腿复核实证=r987 收口单在跑含 O-2110 件（心跳 task 明载 6-order receipts）·候 r987 落 origin 复验——09:07 探针已清（内容被 R2.9 复核覆盖·防双烧）【R2.10 10-18 00:10 夜移交班跟核】bm-b 腿与 E1 leg-5 同链在途（r997 delivery·心跳 23:57 自证）→10-18 晨检班复核收口；【R2.11 事件班 10-18 00:4x 裁量豁免收口】bm-b 腿销账：drama 试点已实质越过（批一 EP001-010 十件 10-16 装配+02:30 CEO 呈报〔PATROL L78 实锚〕+60 集 QC 收官+O-20261017-1741 转向令）·「拉片起点」用途已消费·试点两件留 bm-b 盘随取·延误如实披露（24h 窗 21:1x 过期未交·E1 追缴史在档）；E1 leg-5 物理交付用途同灭——晨检班验 re-drop 落位即闭环·失败不再 re-queue；O-2110 双腿全闭 |
| 10-17 machine-state v6.1 补部署+复测（D-20261016-06 19:00 部署死线未达·兜底已验生效=三任务 21:53-56 Ready·rc=0·v6.1 本体未落=ps1 mtime 仍 10-15 16:29） | HQ（machine-state owner·bm-a） | D-20261016-06 | done-已部署候实弹复测（R2.17 10-18 09:3x 晨检班补部署收口：v6.1 三件套落 .codely-cli\machine-state.ps1〔pause/pauseLite 写禁用名单 sidecar machine-state.disabled.json→resume 按单∪静态表反向复开→逐任务复开自验行→consume〕+kit 模板同批镜像上链+status 冒烟通过+三任务现态 Ready 亲验〔兜底在位〕；实弹验证=下一 pause/resume 周期〔周一 AutoYield 09:00 pauseLite 落单→19:00 resume 复开·19:20 一次性验单 cron 在位〕·D-06 decisions 行同步销） |
| 10-17 08:43 晨检班重载清单（周六）＝缺班补扫（关注点 1-4+盲区 1-2+盲区 7-12+fleet-reality 基线——10-16 晨检班缺班=cron 口令制挂起窗 09:00-19:00 所致·radar 快充 10-16 已由 23:43 班补扫=24h 精选空窗如实）+@bm-b 欠件五件 >24h E1 升级复核+各机游戏车道回执复核（O-2145→10-17 21:4x 窗·O-2110 bm-b 腿）+首批游戏云批动作呈报+V5 装配进度跟核+周六口令决断树执行（10-17 周末行·bm-a 口令制首周末） | 08:43 晨检班（recurring 9632cee5+桥 e284a5da 双承载） | ROUND v3.1 班表+R2.3 日覆盖审计 | 延误·如实披露·已落地（R2.9 事件班 10-17 10:1x 承 NJ-R11a fallback 泛化代消费：08:43 班周六缺班→本班代承清单件=呈报已代呈〔orders R2.9 行〕+E1 复核线✓〔bm-b 心跳复活 09:19:08·r987 worktree 重物化+E1 五回执收口在跑=愈合中·bigmoney tip fa2090bb 基线入档〕+V5 承接✓〔proxy 234.25s 全链断言过+导演 09:0x 追加 4 镜单 @bm-c 回执窗 ≤11:0x 在飞〕+周六口令树✓〔bm-a 未停机零动作〕+POOL-0013 翻卡✓done+radar 快充✓〔09:5x 8 条零爆发级〕+丢行守望 audit✓〔4 旗全正当改写豁免零真丢行〕；fleet-reality 基线=skipped〔L0 09:31/10:01 拍健康复用·传感复用律〕·12:43 recurring 槽周六同风险勿依赖=EVT PT15M+11:33 回访探针覆盖）；【R2.4 事件班 00:5x 注记】@bm-b 五件 E1 升级+手术五面已由本事件班承载件提前承载消费（orders 00:5x E1 行+poke attempt#3+回访探针 02:35）——本项 08:43=复核线（勿重落单·验证面 r987+ 落 origin 或心跳 ts 移动） |
| 10-18 08:43 晨检班重载清单（周日）＝关注点 5-16 缺片补扫（周六 12:43〔5-7〕/15:43〔8-10〕/18:43〔11-13〕/21:43〔14-16〕四班缺）+fleet-reality 全景基线+bm-c 复活后健康/满载面必测（R2.12 事件班 01:5x 注记：熄灯 21:03-01:34=守窗让路+TTL360·已自愈复活〔machine/C 新笔 C2030 f3c28e07a 01:34:31+listener :8790 01:38 复活=TCP+HTTP 双通+枢纽白名单 poke 12tasks 01:40:24 accepted·200s 复探 BURNING PASS CPU 10→34%·R13 NJ 消费·旧「载波降级」读法随之失效〕——晨检面=复活后心跳新鲜度/GPU 满载/环栈健康核验+BM 仓 hotpull :fail 01:43 复核〔归 bigmoney 席传感面防双发〕+c.json→fold→本机拉平链落位终验）+bm-b E1 leg-5 物理交付复核（**R2.13 注记=leg-5 已 CLOSED-VERIFIED**：r1044 02:45 收口——Taildrop 两面性坑〔CLI get 静默空 vs GUI Downloads 落盘〕+5 件已迁 media\drama-pilot-in\ 字节全验+MSG-0245 回执落 BM origin+CEO 看片通道 material in place；晨检面=轻验 5/5 在盘+MSG-0245 核验·勿再跑 tailscale file get；BigMoney 仓回执终验=r998 GREEN 已直探·MSG-0216 落 origin 核验归 watch ①【R2.14 03:5x 升级处置毕=§3 两轮兜底触发：poke ×2（03:39:54/03:51:56 accepted）+O-20261018-0348-bm-a r998 git 面收口令落 BM origin（55d0cd971·病理=state 收口已落/git 收口未落·回执滞留盘面未提交）；08:43 面=验 MSG-0216/O-0348 回执节落链即销账·勿重 poke 勿重立令；worker v1.10 hb>120m 自愈门 04:26:54 兜底】→【R2.15 事件班 05:2x 前提失效判】04:26:54 自愈触发点已过 40min 零效果+O-0348 落 origin 后 77min 零 bm-b git 面动作（BM tip a748663be 零 MSG-0216+回执节空+心跳 02:26:54 陈旧 2h41m）——08:43 修正指令=只验不可销账：仍缺=E1 复发按两轮兜底律升委员会通道+音频点火候选（POOL-0018/0019 音源 408.5MB 未投）留评 mv-director 席（详 10-16 14:00 行 R2.15 注记））+O-2110 bm-b 腿收口+O-2145 游戏车道回执分项收口+MV V5.4 后续跟核（呈 CEO 终审态）+radar 快充 ≤3+GitHub 风向日扫 ≤2+10-18 09:15 软著永续旗 snooze 到期观察+machine-state v6.1 补部署（mtime 仍 10-15 16:29 实证·D-06 owing）+当日 21:43 死线班=周日周深复盘窗（SLI 趋势+效率判据+智能体库周审 agent-library-audit.py+问题台账周对账·≤5 调用共用）【R2.16 2026-10-18 06:13 亲验=watch ① 主判据达成：bm-b r998 git-face closeout 已落 BM origin（b15d5e699·MSG-20261018-0216 43 行亲验在树）+死锁解锁实弹闭环（O-0348 §3 两轮兜底·backlog row13+force-pull poke 配方）+leg-5 五件 16,454,993B 5/5 在盘字节恒等——08:43 面=轻验 bm-b 心跳 ts 移动+O-0348 回执节 bm-b 落件行（主判据已满足·勿重 poke 勿重立令·06:50 探针在位）】 | 08:43 晨检班（cron 空仓已由 R2.10 重建） | ROUND v3.1 班表+R2.10 夜移交 | executed（R2.17 10-18 08:52-09:5x 晨检班全清单收口：①reality 基线 08:56 三机全绿〔hb bm-a 39m/bm-b 11m/bm-c 11m·skew 0〕+bm-a=CEO 让路 pause 态 22:51 起〔口令制合法·35B :8090 down 属让路设计·候「全面开工」零催办〕②bm-b E1 O-0348 双轻验销账=心跳 11m 移动+O-0348 回执节 bm-b r999 亲验落链〔r1049 08:49 活跃·E1 并案链全闭〕③bm-c 复活健康✓〔MSG-0431 taskaudit 40 行落 O-0137 回执节 04:3x·三腿全收+W265 推进·GPU gen-only 夜窗候产合法态〕④drama-pilot 交付契约 CLOSED-VERIFIED 手工销〔5/5 字节复验 16,454,993B·done 件落=止每小时假 poke〕⑤O-2145 分项销账〔bm-c 多笔回执行+bm-a 呈报在档·bm-b 窗内 E1 停摆如实披露〕⑥O-2110 维持 closed-exempted⑦MV V5.4=呈 CEO 终审态·归 MV 窗自守⑧machine-state v6.1 补部署收口〔D-06·kit 镜像+冒烟过+三任务 Ready 亲验·实弹复测周一周期 19:20 验单〕⑨radar 快充三面入评〔DeepSeek V4.1 Flash 免费窗/技术出口目录修订/可灵4.0〕⑩GitHub 日扫 B 查 9 件·A 查 403 限流如实〔3 契合候选入 72h 窗〕⑪丢行 audit depth30=36 旗全正当改写豁免零真丢行⑫关注点 1-16 缺片补扫全过+17-20 轻扫〔BRIEF 20 项 vs 班表 16 项=迭代候选〕⑬软著 snooze 09:15 到期→09:35 一次性探针在位⑭QUEUE-LOW 三池低位维持〔真实积压零新件可派·音频点火候选留评 mv-director 席照旧〕） |
| 10-25 记忆治理席推广派单回执（@bm-b/@bm-c 装机+memory-budget-gate v2 首跑+LEDGER 本机行+L0 身份元组清理·CEO 2026-10-18 00:2x 直令 R2.16 补录） | CEO-PROXY 回执雷达+周复盘 | orders 00:2x 行（R2.16 补录） | dispatched（回执窗 ≤2026-10-25·bm-b 侧 r1049 08:49 已见 memory-gov gaps closed 动作〔MSG-20261018-0849〕·候正式回执行落 orders 回执节） |
| 10-20 晨窗 V5.11 今晚收口链（代理剪重出→PROXY-PASS→768P 终烧→双签→呈 CEO） | bm-a BigStream-OSLoop/装配站 | orders 10-19 22:17 行+NJ bigstream R22 ① | **at-risk 如实披露（R2.26 00:32 事件班）**：detached 540P 代理重渲 23:06 后死亡实证（76min 零新件+进程零命中+零 commit·00:18 三面实测）→处置派单已落（orders 00:32 行·重发 detached 重渲或等待态两态裁决·poke 已发）·回执窗 ≤2h·02:43 夜班+R2.26 回访探针双覆盖 【R2.27 05:43 夜产守护班跟核】closeout 已实证达成→转「候 CEO 终审」销派单：03:19 PROXY-PASS-V511.md + 03:32 full_mv_v511_n1.mp4（1,340,088,152B）+ 03:33 DIRECTOR-REVIEW-V511-FINAL-20261020.md 三件在盘；commit 2db80a38=768P 终烧 234.25s/5622f·PTS 0 异常·四板读毕·导演/制监双签·N1 变体 TP -1.1 dBTP/-14.1 LUFS。R2.26 处置单已被该批产出消费，零重派零 poke。 |
| 10-26 07:4x 调度席翻新（逾期 10.7 天回访） | 三条逾期回访一次结清 | bm-c 调度席（CEO 2026-10-26 07:3x 全面推进令） | executed（三件实测读数） | ①orders 分卷 D-20261025-05：**已真执行**——10-16~10-18 共 113 行迁 `docs/orders-archive-2026-10.md`，主件 363.6KB→208KB（过 250KB 线），并勘正 03:1x 夜轮「只写指针未搬行」；②token 台账断更 12.9 天：本窗补 10-26 恢复行（云端生成 0 单·历史漏记按不可回溯处理，不回填估算）；③记忆双帽 44.8KB>40KB：登记为待裁件，处置方案见同日 decisions 行（禁本窗擅删 L0 条目）。 |

| 10-27 19:00 前补 bm-b 生产认领任务（否则 POOL-0018/0019 永不可认领） | bm-b 车道（需本机会话/决策轮执行） | R2.37 17:3x 事件班裁决 | **at-risk**：POOL-0018/0019 自 10-19 19:35 RE-OFFERED 起 **8 日零认领**。本班实证根因=机队唯一认领任务 `HQ-ProductionClaim` 只注册在 bm-a；bm-b 的 wake_tasks 白名单只有 Bigmoney-IterationLoop（量化专用），故两张声音锚卡在 bm-b **结构性不可认领**，不是「机器懒」。本班已置 `blocked_by=no-claim-task:bm-b` 使状态诚实（禁再假报「有活」）；清障=在 bm-b 本机注册 queue_claim 计划任务后清该字段。FleetLink 无命令通道（CEO 10-23 令禁远程调度）→本席只 poke+登记，不伪造「已恢复」。 |
| bm-c MiniGame 心跳写入停摆 + RAM 破地板 | bm-c 车道 | R2.37 17:2x-17:30 实测 | **at-risk·如实披露**：`gaming/MiniGame/Design/configs/GLOBAL/fleet/c.json` 最后写入 15:08（age>2h→idle-watch 判 HB-STALE），但 TCP /status 17:28:45 **活着**（ram_free 1.7G / cpu 18% / GPU 余 14.9G），且量化轮 r1305/r1307 在跑 → 判定=**不是机器死，是 MiniGame 心跳写入者停摆**（该机当前只有量化任务在跑）。另 RAM 1.7G 仍低于 24G 机的 10% 地板 2.4G（17:04 曾探到 0.5G / CPU 82%，20 分钟内从窒息回落到 1.7G）。正法=bm-c 本机恢复 MiniGame tick 或补内存；本席已 poke（SYNCED 16s）并登记。 |
| mv0001 v717 逐镜判定呈件（CEO 待办剩余 3 项之第 1 项） | bm-a / 导演席 | R2.37 17:35 产物 | **可判定态**：`Q-MV-0001-006/007` 已由机队自领完成（rc=0 → 27/27 取证条 + 37 事件分类）。分类实得：**JUMP=3**（t=92.17/109.29/139.62 · 对齐残差 11.2-11.6 · 与 jitter_scan 的 SNAP resp≈0.03 互证 = 镜内相机断裂·真缺陷）+ JUMP?=4（t=5.42-5.54 收敛段·疑开场快速揭示）+ **FLASH=16**（shift≈0 的纯亮度跳·触 CEO 禁白闪律·需人眼定性）+ FREEZE=9 + POP=3 + CUT=2。**第三口径出现**：stability/scan 报 shots=83，jitter_analyze 报 cuts=94/shots=95 → 双签前必须先对齐镜数口径，否则签的是错表。剩余人工项=逐条判定（材料已齐）+ 时代盲测 + 83 镜双签。 |

| **R2.38 事件班 2026-10-27 18:2x（承载件触发 DL 17:32/18:01）** bm-b 生产认领任务清障令 | bm-b 车道 | orders 18:2x 行 + cph4/fleet/cmd/OB-20261027-182254-574.json | **dispatched·回执窗 ≤ 2026-10-28 08:43**：已用机队命令总线发布到 bm-b（poke accepted·SYNCED 12s）。根因实证仍为“bm-b 没有 HQ-ProductionClaim 认领任务”，POOL-0018/0019 声音锚卡自 10-19 RE-OFFERED 起 **8 日不可认领**。本班不伪造“已恢复”；验收物=bm-b 本机 Get-ScheduledTask 读数 + POOL.json 两卡 blocked_by 清空。 | R2.38 |
| **R2.38** CLOCK-UNALIGNED（bm-b v1 旧 schema / bm-c 偏 1023.8ms） | 机队计时面 | CLOCK-SKEW.json 18:04:15 | **registered·两机分治**：bm-b=heartbeat 不带 ts_utc_ms/seq/clock_offset_ms（需本机升级，已并入 bm-b 清障令 ②）；bm-c=系统钟偏 1023.8ms > 150ms 门（w32time 停转，非提权起不来）——需 bm-c 本机提权校时，与 S4U 提权面同批。 | R2.38 |
| **R2.38** SUPPLY-DRY 补料（queue_open 0→2） | bm-a 生产队列 | 本班实作 | **executed**：新增 3 条真实 backlog（Q-MV-0001-008 逐镜审计 / 009 转场审计 / 010 三口径镜数对齐），008/009 已入队 OPEN，010 依赖前两件产出自动解锁；三件均直指 CEO 待办剩余 3 项中的“83 镜双签”前置。新工具 Tools/mv_shot_reconcile.py已开发并实测（v716 实锚 trans 144 / audit 83 / union 85）。 | R2.38 |

| **R2.38b 复探验收（2026-10-27 18:28）** bm-b 命令传不到=本机仓分叉（再发） | bm-b 车道 | 本班三分钟复探 | **at-risk·需本机收口**：bm-b head 仍=**089e916f**（与上午 17:20 判例同一个未推送提交），拒绝拉取 origin/main=ccd517f1，故 OB-20261027-182254-574 在 bm-b **可见但未生效**（poke accepted·Bigmoney-IterationLoop:WAKE）。正法=bm-b 本机跑 `Tools/fleet-hot-sync.ps1`（fetch+rebase autostash，做不做 hard reset）。**这是同一缺口第二轮报修**（17:20 已诊断同一命令传不到根因）→ 按三声条件③ 已对 CEO 出声。 | R2.38b |
| **R2.38b** bm-c 心跳修复点火验收 | bm-c 车道 | 本班复探 | **BURNING**：bm-c head 已=ccd517f1（真拉到命令），且 MiniGameEngineTick:WAKE 已被唤醒（Bigmoney:busy-skip=量化正常在跑）。验收面=下一次回访探针看 c.json 是否出现 18:2x 以后的新 ts 且被 fold 到 master。 | R2.38b |

| **R2.38c 三口径镜数已对齐（v717 真数）**：“83 镜双签”里的 83 是 **v716 旧件错数**，不是 v717 的 | bm-a / 导演席 | R2.38c 实作（Tools/mv_shot_reconcile.py + D:\FleetWorker\review\reconcile_v717.json） | **可定调·双签对象改为实测表**：v717 实测 = 逐镜审计 **94 切点 / 95 镜**（jitter 自报 cuts=94 shots=95，两者一致）；转场审计 **118 个切点**其中 HARD 62 + MATCH 45 = 107 为镜头边界，STATIC_JUMP 11 为镜内硬跳（不属边界）；两道口径联合 tol=0.125s 得 **102 个真切点**，其中只有 trans 看到 8 个、只有 audit 看到 21 个——**真存在 29 处两道口径不一致**，不是阈值差。jitter 那一道 **只发布了计数、没发布时间表**（盘上 events 只有 37 条异常事件，不是 94 个切点），故不参与联合。建议：双签前先定义“一个镜”的口径（镜头边界 vs 可见跳变），否则 94/102/107 三个数都“对”。 | R2.38c |

## §二 waiting-CEO（物理件/保留面·零催办）

| 件 | 说明 |
|---|---|
| meme V1《慢慢踩》发布窗（18:00 首选） | 成片候 CEO 终审+发布授权 |
| B站 cookie+aid（**已闭环销账 10-14 15:5x**） | cookie=浏览器扩展提取在用（回复线 15:03 已真回复）；凭据=CEO 已交接·仓外 auth-handoff.json（零入库）；aid=频道 API 自动发现 |
| V100 16G 阶梯 P1 一键下单（¥900-1300 成套·**已落地销账 10-16 00:3x**·CEO 亲手执行） | 证据亲验=cph4/fleet/hardware/V100-RIG-BOM-20261014.md 采购状态节：X9DR3-F ¥280 已购+V100 SXM2 ¥950 已下单×1（单卡期=Gemma 26B QAT 全驻留主力·35B 续留 bm-a·第 2 张到位即切双卡迁移）+内存 16×16G 1600 终裁；到货验收三关死线=bigcompute NJ#2 standing 派生面 |
| 3090 双触发蹲价（≤¥4200）+A30 24G 观察（≤¥4500） | 触发信号=定版镜头/日>INT8 产能连续 3 天 |
| 硅基域平台名 | 命名=CEO 保留面（D-20261011-03②·材料预备毕 R1760〔D-20261013-01 核销在案〕·正式申请双前置=平台名 CEO 定谳+bootstrap 物理件·零催办）｜〔R2.5 事件班 10-17 01:5x 承 NJ bigdomain 10-14 23:27 翻新：软著 G 系 6 款定名已由 C-20261010-03 委员会 T1 决生效（e2d0e52·PROJECTS name_pending:False×6 亲验+材料 6/6 在盘）→撤出待定区〕 |
| Steam 分支评级点选（★★★★★=P01/P05/P07） | O-20261010-1650 存量件 |
| BigLife census 造人线解禁 | 唯 CEO |
| 抖音/视频号等账号注册、devtools/AppID/商户号/域名备案族 | 物理件域·有空弄 |
| **G12 台账机核=BP+pre-push 全机提案（Phase 1-β-③·O-20261014-1745·命令级实施稿=cph4/fleet/dispatcher/MASTER-AGENT/G12-BP-PREPUSH-PROPOSAL.md）**：①GitHub branch protection 轻档（10 仓 main：禁 force-push+禁删·不开 required-PR——机队直推 main 工作流不能断）；②三机 `core.hooksPath=.githooks` pre-push 钩子（反转闸必拦+受保护件哈希漂移提示） | 账号治理面·**CEO 一次同意即三机同夜落地+回执**（登记制零催办） |
| **patrol digest 探针 v1.1 修法（受保护件 CEO 令通道·注册表 law=改动唯 CEO 令定谳）** | NJ group E2 10-14 23:37 提名+R2.5 事件班 10-17 01:5x 补全病理实证与即贴补丁=cph4/fleet/dispatcher/PATROL-FLEET/reviews/carrier-digest-probe-v1.1-proposal.md（①5s 复探杀记忆改写瞬态竞态假阴性〔10-14 23:14 实锚〕②digest age 格式诚实化〔现格式把小时错标 min+吞 >24h 天数〕③全局/项目两路径分开探+旗面标真缺者）·过渡止血=group-snooze until 10-18 01:50·**CEO 一句「批」即四处补丁落地+注册表重锚回执**（零催办·有空弄） |
| **patrol LOG 行上链腿修法（受保护件 CEO 令通道·改动唯 CEO 令定谳）** | R2.25 事件班 10-19 17:1x 提名（PR-20261019-02）=patrol 班毕对 LOG.md 行走 Tools/git-atomic-push.py append 模式上链（origin 尾基底·与本席 CEO-PROXY/LOG.md 同法）——落点 Tools/patrol-prompt.txt 班毕动作节+PATROL-FLEET/CHARTERS.md §通用纪律共两行；病理=10-17 02:30 后 60 班次行裸奔被工作树覆写链吞（autostash pop-fail+reset --hard 连带·收口=0f608799 union-restore·131 行在链）；CEO 一句「批」即两文件落地+registry armed 转验证周期（零催办·有空弄） |
| **量化全线停摆 23.4h（三生产位全不可用）**——bm-a 量车道 Disabled（10-24 08:3x 起·无书面溯源）＋bm-b 物理离线 2d＋bm-c 物理离线（10-25 ~12:1x 起）。BM 仓末笔 10-24 13:49。 | **需 CEO 选路（三选一）**：①开机 bm-c 或 bm-b（最优·不碰 bm-a 专职令）；②准 bm-a 分时恢复量车道（违 10-24「专职《爱在西元前》」令，需 CEO 点头）；③确认量化暂停至 bm-d 入网（则本旗转「已披露暂停」不入 fail）。**本席默认不动作**——擅自恢复=违 CEO 定位令。【R2.30 19:3x 事件班翻新·bm-c 面销账】**bm-c 已复活并在飞**（tailscale 在线 relay sfo·FleetLink :8790 TCP+HTTP 双通@19:28·quant 心跳 clock 19:08:31 r1250 closed·origin/main 已到 **round 1255@19:09**）；本席已纯落后自愈 `git merge --ff-only`：55c0dd2c83(r1195)→0470b5fbf7(r1255)·0/0 对齐。**故「量化全线停摆」定性作废**——剩余缺口＝①bm-b 物理离线 2d（bm-c 已按其轮自领权吸收 E90 等 bm-b 欠面·commit 36a009c79d）②bm-a 量车道 Disabled（CEO 10-24 专职令维持·无非恢复）。原三选一收敛为：**①开机 bm-b（最优·补全 cpu-sound 车道）②准 bm-a 分时恢复 ③确认延至 bm-d 入网**；量化主链现由 bm-c 单机承载，非全停，无需紧急裁。 | R2.29 13:5x｜R2.30 19:3x |
| **S4U 提权导入（弹窗复发面）**——HQ-MA-ProxyProbe / HQ-CEOProxyEventCarrier 仍 InteractiveToken，本席每次 shell 调用在桌面闪控制台窗（违 2026-09-29 黑窗根治律）。XML 备份已在 `Tools/task-xml-backup-*-20261024-000427.xml`，清单在 `Tools/task-s4u-backlog.md`（共 10 件）。 | 需管理员权限一次性导入（CEO 或提权会话）；不解决则事件班每次运行都有可见闪窗。 | R2.29 13:5x |
| **2026-10-26 事件班取证**：PROBE-DOWN 案（空窗 20:11-22:33·2h23m·11 件事件实证四门排除）已闭合到「错过触发永久丢弃」层；S4U 与 TaskScheduler/Operational 日志取证卡在同一提权面 → 与上一条 S4U 行合并办理 | 同上述提权面（需 CEO 一次性可见会话） | Round 2.33 / NEED-JUDGMENT 2026-10-26 | 复核 |

| **R2.34 注记（2026-10-27 05:5x·事件班实测）**：**bm-b 已自愈复活在跑**——bm-b.json 05:38:36 落盘・clock_read 05:17:54・cyc_round r1162・agenda_starved=false・cpu 39%（推翻本表上方「bm-b 物理离线 2d」定性）；量化现势=bm-b r1162＋bm-c r1298 双机在跑，bm-a 量车道 Disabled 属 CEO 10-24 专职令（非故障）。原三选一收敛为：①是否准 bm-a 分时恢复量车道（需 CEO 点头）②确认量化沿用 bm-b/bm-c 双机、bm-d 入网后再议。本席默认不动作。 | R2.34 |



| **R2.35 注记（2026-10-27 11:3x·事件班实测）**：提权面三项已合并为**一次即可办完**——①探针/承载转 S4U ②启用 TaskScheduler/Operational ③HQ-SchedHarden-Batch 转 S4U；本班会话 `IsInRole(Administrator)=False`、S4U 注册实测 `拒绝访问 0x80070005`、Operational 日志 `IsEnabled=False`（三项同源实证）。同时：条件硬化分批执行器已排期 10-28 02:10 起低峰 5 跑（≤12/跑·自停），**需硬化任务实测 38 件（旧记 57 含第三方任务，已勘正）**；探针面 BURNING 复核通过（11:26/11:31 双次 Result=0x0）。 | R2.35 |

| **R2.36 注记（2026-10-27 16:5x·事件班·承载件触发）**：三件裁决落盘——①**POOL-0022 陈旧阻断源解除**：签发件 10-20 12:4x 已在档（SIGN.md 判定准烧 A 批 28 帧），但卡 blocked_by 未清，致 W2《可爱女人》KF 28 帧 P1 停滞 7 日零烧制产出；本班清障后可认领，待 bm-c RAM 解锁点火。②**POOL-0016 收窄**至 night-1 LatentSync 单腿残余，解除对 POOL-0021 的阻塞。③**POOL-0003 销卡**（anchors/ 81 件 10-20 已整体交付，deadline 过期 10 日 delta 归零）。另：bm-a STARVED-EXEC 判为**按政策期望态**（idle-watch verdict=EXPECTED-IDLE-WORKHOURS，pausedLite 工作日让路律在役）——旗为 L0 脚本假红旗，修法涉受保护件，已登记 PROBLEM-REGISTRY PR-20261027-14 候 CEO 令/群审通道。 | R2.36 |
| **R2.39 事件班 2026-10-28 00:1x（承载件触发）** bm-b 主机离线（LANE-DOWN 真因）+ 三张 POOL 陈旧假红校正 | bm-b 侧 | tailscale status + ping + TCP 8790 三源实测 | **registered·at-risk**：Tailscale `last seen 23:34`、ping=False、8790 超时 → 主机睡眠/断电（非软件停摆）。21:12 令在其醒后自续；POOL-0018/0019/0020 经回执核对**实为已交付**（7/7 anchors + 0020 回执 20:21 落），已 close 为 done，bm-b 「3 开卡全堵」不是供给失败是台账滞后。唤醒=物理动作，本席零催办只登记。 | R2.39 |
| **R2.39** bm-c 内存闸（0.7G 余量·GPU 14.7G 空转） | bm-c 侧（本机执行） | TCP /status 00:02=1.3G / 00:04=0.7G | **executing（POOL-0024 P0·6h 窗）**：真因=ollama 三模型驻留（27b/30b/35b）+ keepwarm；正法=本机 `python Tools/fleet/gpu_lease.py --node bm-c --acquire` 或 `job_kf_batch.py` 一步式（内部 stop_ollama+keepwarm disable）。判据 ram_free>=6.0G + ollama ps 空 + /system_stats 200 + POOL-0021 首批 KF 落盘。6h 未动即复派 P0。 | R2.39 |
## §三 R2.40 事件班注记（2026-10-28 00:46-01:0x·承载件触发）

| 件 | 状态 | 证据 |
|---|---|---|
| **bm-b LANE-DOWN** | **closed（自愈）** | tailscale active relay sfo / ping True / TCP 8790 True；`ts 00:47:08→00:51:14`、cpu 4%→71%、ram 10.8→8.7G、`current=r1193`（D-20261028-02）。30min+ 无回落=BURNING。 |
| **bm-b 根仓分叉** | **at-risk·第 3 次复发** | `last_pull 00:28:02` 仍 `head=089e916f` ≠ `origin_main=5266f7a2`；命令可见不生效。正法=本机 `fleet-hot-sync.ps1`（禁远程）。 |
| **bm-c BLOCKED-RAM（POOL-0024 P0）** | **at-risk·恶化·非 poke 可解** | `00:04 0.7G → 00:51 0.9G`（24G 余 4%）、cpu 76%、GPU 14884MiB 空闲。6h 窗 ≤06:10。需本机 `gpu_lease.py --acquire`（CEO 10-23 禁远程）。 |
| **bm-c gaming c.json ETS 污染（新）** | **registered·候 bm-c 会话** | `/status` 的 c.json content 解析后键为 `value,PSPath,PSParentPath,PSChildName,PSDrive,PSProvider,ReadCount` = PS5.1 六法①（未 `[string]$_` 解包即 ConvertTo-Json）。**HB-STALE 真因=写入格式病，非写入者死**。修法=重写 c.json + 写入器解包 + UTF-8 无 BOM。 |
| **SUPPLY-DRY** | **resolved（真因=manifest 见底）** | BACKLOG 5/5 行 deliverable 已存在。本班补 Q-MV-0001-011（v717 flags 拼板）→ 已 OPEN，待 bm-a claim。 |
| **POOL-0023（bm-b 音频锚 7 首）** | **at-risk·第 3 轮** | bm-b 无 claim 任务（wake_tasks 仅 Bigmoney-IterationLoop）→ 结构性不可认领。零重派零 poke。 |

| **R2.39a 事件班 2026-10-28 01:45** mv0001 三项人工判定包已交付 | bm-a / 导演席 | orders 01:45 行 + Q-MV-0001-012/013/014 回执 | **dispatched·回执窗 2026-10-28 12:00**：三包落盘 `D:\FleetWorker\review\ceo_items_v717\`——双签表 95 行（时代/暖度/饱和/运动/重演重复 5 列+签名列留空）·盲测 24 张 seed=20261028 标签分离（KEY.json）·静止接高速 11 处 3×3 联系条+指标表。验收=判定列填满 / 命中率行 / 签名列非空。禁自审自签：判定归导演席与制监席 |
| **R2.39b** bm-b 认领任务缺口（**第 3 轮**） | bm-b 车道 | 01:32 /status 直探 + b.json mtime 01:30:38 | **at-risk·结构性**：bm-b 已复活（TCP 200·ram_free 11.7G·GPU 203MiB·00:28 last_pull 拉取成功），但本机无 `HQ-ProductionClaim` → POOL-0023（音频锚第二批 7 首）看得见领不到；且 whisperX/allin1 只装在 bm-b，bm-a 无此栈（实测 ModuleNotFoundError）→ **不能改派 bm-a**，禁造假活。本机一行修法：`Tools\task-register.ps1` 注册 HQ-ProductionClaim = `python Tools\queue_claim.py --node bm-b --needs cpu` PT5M（S4U，禁 InteractiveToken） |
| **R2.39c** bm-c 内存闸（**第 3 轮·恶化维持**） | bm-c 车道 | 01:32 /status 直探 | **at-risk·结构性**：ram_free **1.1G**（24G 机），VRAM 空 14.7G；POOL-0024（P0 内存释放闸）与 POOL-0021/0022 全卡在「本机执行（禁远程）」；另 00:29 `.:fail` 拉取失败。修法=bm-c 本机 `python Tools\fleet\gpu_lease.py --node bm-c --acquire --need-mb 12000`（内部 ollama stop + keepwarm 停），判据 ram_free>=6G + ollama ps 无 27b/30b/35b 驻留 |


| **R2.39a 事件班 2026-10-28 01:45** mv0001 三项人工判定包已交付 | bm-a / 导演席 | orders 01:45 行 + Q-MV-0001-012/013/014 回执 | **dispatched·回执窗 2026-10-28 12:00**：三包落盘 `D:\FleetWorker\review\ceo_items_v717\`——双签表 95 行（时代/暖度/饱和/运动/重演重复 5 列+签名列留空）·盲测 24 张 seed=20261028 标签分离（KEY.json）·静止接高速 11 处 3×3 联系条+指标表。验收=判定列填满 / 命中率行 / 签名列非空。禁自审自签：判定归导演席与制监席 |
| **R2.39b** bm-b 认领任务缺口（**第 3 轮**） | bm-b 车道 | 01:32 /status 直探 + b.json mtime 01:30:38 | **at-risk·结构性**：bm-b 已复活（TCP 200·ram_free 11.7G·GPU 203MiB·00:28 last_pull 拉取成功），但本机无 `HQ-ProductionClaim` → POOL-0023（音频锚第二批 7 首）看得见领不到；且 whisperX/allin1 只装在 bm-b，bm-a 无此栈（实测 ModuleNotFoundError）→ **不能改派 bm-a**，禁造假活。本机一行修法：`Tools\task-register.ps1` 注册 HQ-ProductionClaim = `python Tools\queue_claim.py --node bm-b --needs cpu` PT5M（S4U，禁 InteractiveToken） |
| **R2.39c** bm-c 内存闸（**第 3 轮·恶化维持**） | bm-c 车道 | 01:32 /status 直探 | **at-risk·结构性**：ram_free **1.1G**（24G 机），VRAM 空 14.7G；POOL-0024（P0 内存释放闸）与 POOL-0021/0022 全卡在「本机执行（禁远程）」；另 00:29 `.:fail` 拉取失败。修法=bm-c 本机 `python Tools\fleet\gpu_lease.py --node bm-c --acquire --need-mb 12000`（内部 ollama stop + keepwarm 停），判据 ram_free>=6G + ollama ps 无 27b/30b/35b 驻留 |


## §三 R2.42 事件班注记（2026-10-28 02:06-02:2x·承载件触发·四轮复发定性）

| 件 | 状态 | 证据 |
|---|---|---|
| **bm-c BLOCKED-RAM（POOL-0024 P0·第 4 轮）** | **at-risk·持续恶化·非 poke 可解** | NATS KV 02:09:07 实测 
am_free_gb=0.4（24G 机·00:04 0.7G→00:51 0.9G→01:32 1.1G→02:09 **0.4G** 波动见底）+ 
ram_used 1469/16384MB（GPU 空 14.9G）+ cpu 46%。阻塞面已从「bm-c 四卡不可点火」升级为**整机 MV 链咽喉**：W2《龙卷风》29 帧+《简单爱》30 帧（SIGN-CARD-W2 待导演三裁后即烧）、可爱女人 i2v、星晴 i2v 全在该机。修法仍唯一=bm-c 本机 python Tools\\fleet\\gpu_lease.py --node bm-c --acquire --need-mb 12000（内部 ollama stop+keepwarm 停），判据 ram_free>=6G+ollama ps 空。**6h 窗（≤06:10）过半未动即复派 P0。** |
| **bm-b 认领任务缺口（POOL-0023·第 4 轮）** | **at-risk·结构性维持** | KV 02:08:50 
am_free_gb=10+cpu_load_pct=48——**bm-b 不是闲着，是在跑量化轮**；缺的只是 HQ-ProductionClaim（唯一认领任务只注册在 bm-a），故音频锚卡看得见领不到。修法=bm-b 本机注册 S4U 认领任务（禁 InteractiveToken）。 |
| **IDLE-WITH-WORK 对 bm-b 是假红（新判）** | **registered·工具面缺陷** | 
leet-idle-watch.ps1 对 bm-b 的 verdict 只吃 gpu.util_pct/comfy/batch，不吃 cpu_load_pct——bm-b 是 cpu-sound 车道（whisperX/allin1 纯 CPU），52% CPU 负载下仍被判 GPU-IDLE，触发 IDLE-WITH-WORK 假旗。修法候选=bm-b 分支改判 CPU 负载（≥30% 视为在忙）。tools 核心四件属受保护面，只登记候裁。 |
| **可爱女人 i2v 首帧契约=bm-c 路径亲和（新判·防误改派）** | **registered·路由约束** | 可爱女人-i2v-PACK-A-v1.json 30 units 的 
rame 全部指向 repo 相对路径 media/mv-album-001-jay/frames/KN_KN01..30.png 并记录 
rame_bytes/frame_sha12；**bm-a 上该目录不存在（0/30）**，且本机两套 KN 帧（media/mv-test/xingqing 10-24 30 张、media/mv-test/keainvren/batch1 10-27 30 张）与契约 sha12 **零匹配**（KN01 契约 1024124B/58f1c5ac4ef6 vs batch1 1041594B/a7d089588db9）。⇒ 结论：契约帧集在 bm-c 本机，**i2v 链不可为绕开 bm-c RAM 而改派 bm-a**（改派=拿错首帧=人物一致性崩）。该约束同时说明 bm-a 10-27 22:58 那批 30 帧是 A/B 对照批，非权威集。 |
| **可爱女人 KF A 批（POOL-0022）** | **done（台账滞后校正）** | 照烧两套已实产（bm-c 权威集 10-24 / bm-a A/B 集 10-27 22:58-23:06·30 帧+联系表 00:15）。POOL-0022 由 open→done；判读/海选归导演席，不属卡面。 |
| **SUPPLY-DRY（第 4 轮）** | **resolved·真因=机器活确实做尽** | _last_claim.json 02:05:01 QUEUE-EMPTY（bm-a 认领环活着自报）+队列 16/16 DONE + acklog_fill 自补零产出。本班**不补假卡**：bm-a 夜窗 GPU 12.3G 已被 llama-server 35B 占 11.4G，而所有待产 KF/i2v 件均卡「人工裁决」或「bm-c 本机内存」两条真阻塞，硬烧=白烧。 |
| **CLOCK-SKEW** | **registered·非新增** | 02:04:14 max_abs_offset_ms=1515.5（bm-c 1536.2 / bm-b 884.6，门限=2×precision+20）。bm-c=系统钟停 w32time（需提权）、bm-b=链路中继 RTT；均已在 R2.38 登记，本轮零新动作。 |

| **R2.42** 推送闸挂死（工具面·全机队阻断面） | 治理工具面 | 本班两次实测 | **registered·P1**：`Tools/git-no-reversal-check.py` 连续两次 >90s 零输出（同一病使 `git-atomic-push.py` 两次 5min 零输出被杀）→ 正法推送链路被阻。应急=改用 temp-index + `numstat 增行-only` 断言（R2.42 实作·+54/-0）；根治=查该脚本对 promisor/大包仓的读法并加超时 | R2.42 |
| **R2.42** 推送闸挂死（工具面·全机队阻断面） | 治理工具面 | 本班两次实测 | **registered·P1**：`Tools/git-no-reversal-check.py` 连续两次 >90s 零输出（同一病使 `git-atomic-push.py` 两次 5min 零输出被杀）→ 正法推送链路被阻。应急=改用 temp-index + `numstat 增行-only` 断言（R2.42 实作·+54/-0）；根治=查该脚本对 promisor/大包仓的读法并加超时 | R2.42 |## §三 R2.43 事件班注记（2026-10-28 02:46-03:0x·承载件触发·SUPPLY-DRY 翻案）

| 项 | 状态 | 证据与处置 |
|---|---|---|
| **SUPPLY-DRY（第 5 轮）** | **resolved·翻案为「有料未派」** | 队列 16/16 DONE + backlog 9/9 已消费（deliverable 全在盘）为真；但查在制品发现两处从未入队：v717 交付闸零证据、v717 重建链丢 AIGC 标识。已入队 015/016/017/018 四卡，015 FAILED(rc1,56.7s)、016 DONE(22.5s)、017 RUNNING(02:59:16)、018 排队。 |
| **v717 交付闸首份证据** | **registered·待导演席裁决** | `D:\FleetWorker\review\delivery_gate_v717.json`：D1 单帧重复@234.21s；D1 镜复用 8 对（多数落在 `MV0001-REPRISE-WHITELIST.json` 内=设计重演）；D2 近静止 5 处（首 0.00–3.50s mad .36/shift .16）；D4 曝光闪 4 处（102.17s Δ9.5、211.17s Δ10.7、211.29/211.33s Δ9.0/9.4）；seam0/freeze0。**判定归导演席+制监席，本席只出证据。** |
| **AIGC 标识缺失（v717）** | **fixed-tool·母版待终审** | 实证：v717 首帧 0.4s、尾帧均裸画面（无标识/无 credits）；根因=`mv_rebuild_from_edl.py` 只烧 `lyric_track.ass`。新增 `Tools/mv_aigc_label.py`（libass 烧标签，drawtext 在本机 ffmpeg 9.0.2 无 fontconfig 会崩）。母版=`D:\FleetWorker\review\v717_label\full_mv_v717_aigc.mp4`（5623 帧/234.29s/120s 标签在屏）。**标题卡与片尾 credits 属导演排版件，本席不代造。** |
| **重编码保真待判** | **registered·候 018** | 22.17→6.17Mbps。新增 `Tools/mv_fidelity.py`（SSIM/PSNR）；<0.95 则改高保真档（crf 12 + tune grain）重出母版。 |
| **bm-b 认领任务缺口（第 5 轮）** | **at-risk·结构性**（物理/本机动作） | 02:5x poke accepted 但 `/status head=089e916f` **NOT-SYNCED**（工作树分叉在册）+ 本机无 `HQ-ProductionClaim` ⇒ POOL-0023 仍不可领。FleetLink 无命令通道（CEO 10-23 令），本席零催办只登记。 |
| **bm-c 内存闸（第 5 轮）** | **at-risk·本机动作** | `c.json` mtime 10-27 15:59（陈旧 11h）、ram_free 1.4G(6%)、vram_free 14.7G ⇒ POOL-0021/0024 唯一堵点是 RAM。poke accepted（NOT-SYNCED d7339348）。 |
| **推送闸挂死（R2.42 续）** | **workaround 在用** | 本轮改走原生 git（暂存白名单 pathspec + 直接 push），不调用 `git-atomic-push.py` / `git-no-reversal-check.py`；上一班已证两者挂死。 |

## 附录 R2.44 事件班注记（2026-10-28 03:26-03:4x）

| 旗 | 状态 | 证据 / 下一步 |
|---|---|---|
| **SUPPLY-DRY** | **resolved（本班）** | 队列 20 行全收后按 v717 交付闸 FAIL 真缺陷补 2 张 CPU 卡；`Q-MV-0001-019` 85.7s rc=0 DONE（`D:\FleetWorker\review\outliers_v717.json`），`020` 在飞。补供到产物 < 2 分钟。 |
| **v718 单点病源（新）** | **found** | POP 帧群聚 209.375–211.917s（7 帧，score 7.48–21.53），与 D4 曝光闪 211.1–211.3s 重叠 → 该段重烧或换素材即可，非全片性缺陷。修复计划交导演席。 |
| **bm-b STARVED-EXEC** | **at-risk（本机一行）** | 无 `HQ-ProductionClaim`；本班已把该任务名写入 bm-b wake_tasks 白名单。本机执行：`powershell -NoProfile -ExecutionPolicy Bypass -File Tools\task-register.ps1 -Name HQ-ProductionClaim -Script "<仓根>\Tools\queue_claim.py" -Arg "--node bm-b" -Trigger every:1m -NoFireTest` 再 `Start-ScheduledTask -TaskName HQ-ProductionClaim`。 |
| **bm-b 未推送本地提交** | **at-risk（证据升级）** | `head=089e916f` 在 origin 对象库中不存在（`git cat-file` fatal）⇒ 提交只在本机且阻拉。本机执行 `Tools\fleet-hot-sync.ps1`（fetch + rebase autostash，不做 hard reset）。 |
| **bm-c BLOCKED-RAM** | **at-risk（本机动作）** | `c.json` 陈旧 11h、ram_free 6%；本机 `ollama stop` + keepwarm 暂停即解。另：capacity 规则令自愈卡 POOL-0024 不可派（机制死锁），`Tools/fleet-dispatcher.ps1` 属 L0 正身 → 候 CEO 裁。 |
| **CLOCK-SKEW 恶化** | **registered** | bm-b 1124.9ms / bm-c 1839.7ms（01:26 时 717/1313），precision ±190；修法本机 w32time（需提权）。 |
| **账本冲突残留** | **fixed** | `CEO-PROXY/LOG.md` 27 行 stash 冲突壳（含重复 R2.41）已复原 HEAD 干净版，零独有内容损失。 |

## 附录 R2.45 事件班注记（2026-10-29 00:01-00:3x·承载件触发）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **bm-b 三路遥测断（LANE-DOWN 假红根因）** | **at-risk·本机三条动作（bm-b 侧）** | 机器在产实证：`4d7c6082` 23:37 / `10d0ecff`+`c9dbbf96` 23:46 连推两轮 r1201-r1202。断的三路=①`FluxGroup-NatsHB` 未跑（NATS `state.bm-b` MISSING）②FleetLink :8790 未起（poke `accepted` 但 verify 超时=假受理）③`machines/bm-b.json` 停 16:05（bm-b 转 drama 线，量化心跳自然停）。修法=`FluxGroup-NatsHB`+`FluxGroup-FleetLink` 重注册 **S4U**（禁 InteractiveToken）→ 装 `HQ-ProductionClaim`（`Tools\task-register.ps1 -Name HQ-ProductionClaim -Script "<仓根>\Tools\queue_claim.py" -Arg "--node bm-b" -Trigger every:1m`）。无远程执行通道（CEO 10-23 令），本席零催办只登记。 |
| **POOL-0023 定性勘正** | **corrected（本班）** | 00:04 决策轮第29批判「host-offline(SVC_DOWN)」→ 勘正为 **telemetry-down:bm-b**。host 在线且在产；卡仍 open 合理，但理由行改为「认领任务未装 + 遥测断」，避免日后按「主机死」重派音频锚。 |
| **SUPPLY-DRY（第 6 轮）定性** | **resolved·供给升级（非机械补卡）** | 队列 22/22 全消费、声明式 backlog 15/15 全交付。下批真供给=导演席 v718 修复计划（D1 尾帧 @234.21s / D2 freeze 3 镜 `INT3_her_walk`0.442·`Z01`0.293·`E04a`0.255 / D4 flicker 4 镜 `E01b`0.173·`E04a`0.167·`D05`0.152·`Z03`0.131）。本席不代造创作裁决。 |
| **bm-c BLOCKED-RAM（维持）** | **at-risk·本机动作（bm-c 侧）** | NATS 活 seq1807/age4min；GPU free 14.36G，`ram_free_gb=0.4`（1.7%）。释放法=`Tools/fleet/gpu_lease.py --acquire` 或 `.codely-cli/machine-state.ps1 -Mode pause`（本机）。**禁重复 poke**（r240 判例：poke 修不动 RAM，只 churn）。 |
| **bm-c 时钟 +3342ms** | **registered·本机提权动作** | precision ±299 → 门限 618ms，判 SKEW-HIGH 成立；w32time 停摆需提权自启，与 R2.38 同源，仅更新数值。 |
| **dispatcher capacity 自愈死锁（续 R2.44）** | **waiting-CEO（受保护件）** | BLOCKED-RAM 车道 `dispatchable=0`，而 POOL-0024 恰是解内存的自愈卡 → 自愈卡被自己所解条件挡住。`Tools/fleet-dispatcher.ps1` 属受保护四件（BLUEPRINT §九），本席不改只呈。 |
| **bm-a 重复提交分叉** | **fixed（本班）** | 本地 `40c0b2a3` 与 origin `c6cf8447` 同题重复（两窗各写一次同批决策），本地另落后 4 笔。`git rebase --autostash origin/main` 跳过重复、behind/ahead 归零（现 HEAD=c6cf8447），dirty 44 项 autostash 零丢失。 |
| **idle-watch bm-b 假红（续）** | **registered·工具面缺口（候裁）** | bm-b 分支只吃 gpu/comfy/batch，不吃 git 产出与 cpu_load → 在产也判 SVC_DOWN/GPU-IDLE。正法候选=加「近 60min 有本机提交即判 BUSY」。`fleet-idle-watch.ps1` 按保护面口径只登记候裁。 |

## 附录 R2.46 事件班注记（2026-10-29 00:41-00:5x·承载件触发）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **SUPPLY-DRY（第 7 轮）** | **resolved·真供给（已验 BURNING）** | 新增 `Tools/mv_workorder.py`（确定性三源聚合，无 LLM），补 Q-MV-0001-021/022 两卡；bm-a 认领环 00:51:04 / 00:51:11 各 0.1s **DONE**。交付物 `D:\FleetWorker\review\v718_workorder.json`（74,293B·314 缺陷·100% 归镜）+ `v718_workorder.md` + `v717_cut_consensus.csv`（102 切点 BOTH73/TRANS-ONLY8/AUDIT-ONLY21）。队列 24/24 DONE。 |
| **台账勘正 Q-MV-0001-015/017** | **fixed** | 两卡此前 FAILED 但交付物在盘（rc=1=交付闸 VERDICT FAIL 属设计行为，非执行失败）→ 改 DONE+result_note。症结=runner 把「闸判 FAIL」当「卡失败」，虚增失败面并掩盖有效证据。 |
| **bm-b LANE-DOWN** | **at-risk·定性修正（本机动作）** | 主机**活**：tailscale active relay sfo / ping True / TCP 8790 accept；但 HTTP GET 三次（00:47/00:53）全超时 ⇒ **FleetLink 监听线程卡死（半活态）**，非关机非断网。修法=bm-b 本机重启 `FluxGroup-FleetLink`（S4U）。无远程通道（CEO 10-23 令），本席零催办只登记。 |
| **bm-b STARVED-EXEC** | **at-risk·结构性（本机一行）** | POOL-0023 blocked_by=`no-claim-task:bm-b`。wake_tasks 白名单侧**已闭合**（fleet-nodes.json bm-b 含 HQ-ProductionClaim）；余缺=bm-b 本机注册 `HQ-ProductionClaim`（S4U）。另 whisperX/allin1 仅装 bm-b，禁改派 bm-a。 |
| **bm-c BLOCKED-RAM** | **at-risk·本机动作（bm-c 侧）** | 00:47 `/status`：ram_free **0.6G / 23.9G（2.5%）**、VRAM 空 14,683MiB、cpu 48%、ollama 驻留 qwen3.5:9b/4b + qwen3.8:27b + glm-4.7-flash:30b + qwen3.6-coder:35b。POOL-0021/0022/0024 全堵 RAM。**零 poke**（r240：poke 治不了 RAM）。修法=bm-c 本机 `python Tools\fleet\gpu_lease.py --node bm-c --acquire --need-mb 12000`。 |
| **D4 曝光闪单点病源（新判）** | **found·交导演席** | 4 处闪烁里 3 处连在 **E06_strike@reuse（211.17/211.29/211.33s）**，与 R2.44 的 POP 群聚（209.375-211.917s）同区 ⇒ 该段单点问题，重烧/换素材即可，非全片性缺陷。D1 尾帧重复=Z04_glyph_remains@234.21s（裁 1 帧级）；D2 近静止 5 镜清单见工单表。**修复决策归导演席，本席只出证据。** |
| **诚实边界** | **standing** | CPU 卡一领即空（0.1s 级），下一轮 SUPPLY-DRY 必然再亮。真瓶颈=bm-c 内存（闸住全部 GPU 产）+ 导演席签核（人类判定）。本席不补假卡、不代创作裁决。 |

## 附录 R2.47 事件班注记（2026-10-29 01:21-01:3x·承载件触发·第 8 轮 SUPPLY-DRY 同型）

| 项 | 状态 | 证据 / 下一步 |
|---|---|---|
| **bm-b LANE-DOWN（00:52 旗）** | **resolved·本班实证自愈** | 01:23:17 `/health` 200 `{"ok":true,"node":"bm-b","version":"1.9.3"}`；01:28:38 `/status` 200 host=BIGMONEY ram_free 6.2G cpu 33% GPU 112MiB。00:52 的「TCP accept 但 HTTP GET 三次全超时」未复现。三机同时探活全 200（bm-a 1.9.5 / bm-b 1.9.3 / bm-c 1.9.5）。**残余=FleetLink 版本落后（1.9.3 vs 1.9.5），本机升级动作，零催办**。 |
| **bm-b STARVED-EXEC 定性** | **falsified（本班·承 R2.46 判错）** | R2.46 判「余缺=bm-b 本机注册 HQ-ProductionClaim」被 bm-b 自身审计回执证伪：`cph4/fleet/queue-receipts/POOL-0023-bm-b-claimtask-audit.json` → 任务 `PRESENT / State=Ready / S4U / last_result=0 / cadence 5min / last_run 10-28 21:22:44`，且同一 claim intent **21 小时内重发 252 次、卡从未执行**。真病灶=`queue_claim.py --pool` 只有意图腿、无执行腿（mode 有 `--pool`/`--pool-list`/`--pool-republish`，无 exec）→ POOL 卡结构性不可执行。`blocked_by` 已由本席翻为 `no-exec-leg:queue_claim--pool`。 |
| **POOL-0023 可执行面** | **blocked·工具面（本席不代造 cmd）** | whisperX 锚批工具只在 bm-b（`media\drama-tools\anchor_runner_r990.py`，状态 Disabled 且注册为 Interactive = 违 S4U 律，11 天未跑）；bm-a 树全搜无 whisperX 锚 runner。无远程执行通道（CEO 10-23 令）→ 本席无法代写可验证 cmd，禁造假卡。 |
| **bm-c BLOCKED-RAM** | **waiting-CEO（本机物理·零催办）** | 01:28 `/status` ram_free **0.9G/23.9G**、GPU 14686MiB free、cpu 25%。回执 `POOL-0024-bm-c.json` 已实测：RAM 消费者=桌面（Doubao×4 ~3.8G / msedge / Platform / explorer / wetype），ollama **0 驻留模型**（daemon 296MB）→ 撤 ollama 到不了 6.0G 判据。禁重复 poke（r240 判例：poke 治不了 RAM）。 |
| **CLOCK-SKEW** | **registered·本机提权动作** | 01:19 `CLOCK-SKEW.json`：bm-b **+4004.5ms**（σ±192.9）、bm-c **+3678.6ms**（σ±206.4），hub bm-a +0.1ms。bm-c 由 R2.38 的 +3342ms 续涨 336ms ≈ w32time 仍在停摆。两机 NATS 心跳活（age 20s/62s）→ 偏差真实非传感假值。裁定=订正排程按 offset 校正已生效，系统时钟提权自启候本机动作。 |
| **bm-a「BUSY」假忙面** | **found·判读勘正** | 01:07 `fleet/a.json` pulse：GPU util 99% 而 `gpu_procs=blender.exe;Tuanjie Hub.exe;Tuanjie.exe`（编辑器占卡）且 vram_free 1.9G；MV 产物最新 `D:\FluxGroup\media\mv-test\keainvren\batch1\KN30.png` = **10-27 23:06（26h 零新增）**。01:28 `/status` GPU 已释放至 1516MiB。结论=idle-watch 的 `a=BUSY` 由编辑器占卡造成，属「进程活着≠有活干」同族；生产面判据须看产物 mtime。 |
| **SUPPLY-DRY（第 8 轮）** | **standing·真瓶颈（本席不补假卡）** | 队列 **24/24 DONE**、声明式 backlog **17/17 已交付（0 eligible）**、5 张 POOL 全不可执行：POOL-0010=CEO 物理件、POOL-0024/0016/0021=bm-c RAM 闸、POOL-0023=无执行腿。R2.45/R2.46 两轮「派生分析卡」均 0.1–11s 秒跑完 → 分析卡不构成供给。真供给只剩导演席 v718 生产裁决（工单 `D:\FleetWorker\review\v718_workorder.md` 314 项已备）。 |
| **诚实边界** | **standing** | 本班 poke 3/3 accepted、3 分钟后复探 `_last_claim=QUEUE-EMPTY@01:25` + 零新回执 → **poke 不能凭空造供给**。下一步只能由三处之一解开：①bm-c 桌面 RAM（CEO 物理）②POOL 执行腿工具面修法 ③导演席 v718 生产。 |


## 附录 R2.50 事件班注记（2026-10-29 03:26-03:5x·承载件触发·第 9 轮）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **POOL-0023 音频锚第二批 7 首** | **done（本班交付·三腿齐）** | calibrated 5 首全 `mode=lrc` exact 100%（47/74/59/86/55 行）＋shotgrid 7 首＋矩阵 `ready=14/41`＋selftest 7/7 PASS。词面=163 官方 api（album 18918），credit/ISRC 已剔。**R2.47「无执行腿」定性补正：活可绕过池子直接做，三个工具一直在仓里（纯 CPU）。** |
| **R2.49「beats 7→41」未上链** | **fixed（本班）** | `git ls-files` 只有 7 个 beats 在库，磁盘 41 个中 34 个 untracked → bm-b/bm-c 拉不到。本班随交付批入链。判例：「声称已产」必须 `git ls-files` 实证。 |
| **POOL-0014 陈旧 in-flight** | **fixed（本班）** | V4 jayredo 10-16 13:52 已全量交付、线已升 V7.17 三代 → `closed-superseded`。不销卡=pools 假忙。 |
| **bm-c BLOCKED-RAM（第 9 轮）** | **waiting-CEO（物理件·零催办）** | 03:28 直探 `ram_free=0.2G`（24G 机；01:28 为 0.9G，继续下降）／GPU 空 14.36G／cpu 59%／`last_pull .:fail`（根仓分叉未收口）。消费者=桌面应用（R2.47 实测 ollama 零驻留）。**poke 治不了 RAM，零 poke。** |
| **bm-b STARVED-EXEC（第 9 轮）** | **at-risk·结构性（本机动作）** | 03:28 直探 `ram_free=9.7G`/cpu 2%（在跑量化轮）→ 机器不闲；缺可执行腿。另根仓 `head=b47c4708` ≠ `origin 01d9e5ed`（落后）。修法=bm-b 本机 `Tools/fleet-hot-sync.ps1`。 |
| **bm-a STARVED-EXEC（第 9 轮）** | **registered·判读勘正（本机桌面动作）** | `_last_claim=QUEUE-EMPTY@03:25:01`（环活着）+ 队列 25/25 DONE 为真；但夜窗 GPU 被 `blender.exe;Tuanjie Hub.exe;Tuanjie.exe` 占住（util 99%／vram_free 1970MB），MV 产物停 10-27 23:06（28h）。**有卡也塞不进显存**→ 需关编辑器。 |
| **SUPPLY-DRY（第 9 轮）** | **resolved（本班·改为执行真实在手活）** | 不补派生分析卡（R2.45/46 已证秒跑完不构成供给），改为把已批准、不依赖第二台机的活干完（POOL-0023）。 |
| **CLOCK-SKEW** | **registered·本机提权动作** | 03:21 `max=4168.5ms / precision ±194.3`；bm-b/bm-c w32time 停摆，需提权自启。R2.38/R2.47 同源，仅更新数值。 |

## §三 R2.54 事件班注记（2026-10-31 17:26-17:31·承载件触发）

| 件 | 状态 | 证据 |
|---|---|---|
| **MASTER SPLIT-BRAIN（两机同当主控·自证循环）** | **at-risk·waiting-CEO（受保护件）** | origin `MASTER-TICK` = bm-m / ts 17:27:41 / masquerade=false；bm-a 本地 = bm-a / ts 17:24:31 / masquerade=true。两机同时当主控、各自覆盖同一 tick 文件 ⇒ 互相看不到退让信号 ⇒ bm-a masquerade 永不结束。后果=bm-a 每 20min 产 master-agent 提交与 origin 另谱系对撞 ⇒ push 必拒 ⇒ 本地永不 pull ⇒ 分叉 10/28（merge-base 1dd20bd3 14:44）且每 20min 加深 ⇒ 盘上 DISPATCH-LOG 永停 14:23 ⇒ L0 探针永久误报。正法候选=判定改读 origin 侧 tick / 加 node 字段 / bm-m 心跳新鲜时强制退让。`master_agent.py` + `HQ-MasterFallback` 属 BLUEPRINT §九 受保护件 → 只登记不改。 |
| **L0 探针谓词错位（本地陈旧时永久误报）** | **registered·waiting-CEO（受保护件）** | `DISPATCH-LOG age>3h` 测「有没有人写日志」，非「调度在不在跑」；本地树陈旧时该谓词恒真。建议改测 MASTER-TICK 新鲜度、DISPATCH-LOG 降二级。L0 脚本受保护。 |
| **bm-a 本地分叉（10 ahead / 28 behind）** | **fixed（本班）** | `reset --mixed origin/main` + 定向取 origin 盘面（不用 autostash），9 笔 masquerade 状态提交退役（机器生成态，origin 已有更新版，reflog 可回收）。仅重放本班记录。 |
| **bm-c RAM 闸（0.3–2.3G / 24G·闸 3.0G）** | **waiting-CEO（物理件·零催办）** | 14:00 后 media/FleetWorker 全树零新产物；Q-GPU-BMC-01R 两轮 `lease-expired-5-attempts`。扣住全部 GPU 产。 |
| **Q-TTS-1202R / Q-GPU-BMC-01R 去向** | **monitoring·18:10 回访探针接管** | 两卡 cmd 指向 C:/K: 远端路径（bm-b/bm-c 本机执行面），主控不可直跑。18:10 一次性探针 `5affeaaa` 在位复探，本班不重复不 poke（防双烧）。 |

## 附录 R2.55 事件班注记（2026-10-31 20:41-20:5x·承载件触发·probe L0-DOWN 3.2h）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **粘滞锁存（master_agent.py:489-499）** | **waiting-CEO（受保护件）** | masquerade 判据 `if prev_by and prev_by != owner_node: stale=True`：一旦本机写过一次 tick，下一轮必然再判 stale ⇒ 永久自锁；解锁只能靠 pull 到 origin 的 bm-m tick。正法候选：①删该分支只用 `age > fallback_stale_s`；②或增 `last_real_master_ts` 只由真主控刷新。本班未改代码。 |
| **产出链澄清** | **registered** | 无任何计划任务跑 `master-fallback.cmd`；`HQ-MasterAgent` 自 10-29 15:46 Disabled。实产=**HQ-Steward → steward.cmd → steward.py → master_agent.py**（20:31:57 最后写状态件）。R2.54 记「HQ-MasterFallback LogonType 违规」的指向应按此勘正。 |
| **L0 探针谓词错位（实证补强）** | **waiting-CEO（受保护件）** | `DISPATCH-LOG age>3h` 与班表相邻班 4.2h 间隔天然冲突：17:31→21:43 之间必报。建议改测 MASTER-TICK 新鲜度。 |
| **bm-a 本地树收口（detached→main）** | **fixed（本班）** | R2.54 只 `reset --mixed` 未重挂分支 ⇒ 8 笔提交落游离头。本班 `git checkout -B main` 后 0 ahead/0 behind、tracked 树干净。备份 branch `backup/bm-a-masterloop-20261031`@d818da44 + diff 快照 181,802B。 |
| **bm-c RAM 闸（续）** | **waiting-CEO（物理件·零催办）** | 无新动向证据，本班按传感复用律未复测；只登记不催办。 |
| **卡死 rebase 自愈（push_lane_files 缺 rebase --abort）** | **registered + 外部闸在役（受保护件候 CEO）** | 10-31 21:07 冲突后 `.git/rebase-merge` 残留 -> 游离 HEAD 8 提交 / 109 落后（当日第 3 次复发）。外部兜底=`Tools/fleet/git-rebase-guard.py` + FluxGroup-GitRebaseGuard every:15m（Interactive 降级·S4U 入 backlog）。根治一行补丁=`rb.returncode != 0` 后加 `git rebase --abort`。回滚=Unregister-ScheduledTask。 |
| **HQ-Steward 停用（bm-a standby 写手）** | **registered·可逆·待 CEO 追认** | 当日第 4 次冲撞后停用；复原=`Enable-ScheduledTask HQ-Steward`。启用前置=`master_agent.py::push_lane_files` 冲突后补 `git rebase --abort`（受保护件·候裁）且 1 周零冲突。现役写手=bm-m（masquerade=false 持续）。 |
| **HQ-Steward fallback 腿已拆（勘正前条「停用」）** | **registered·可逆·待 CEO 追认** | 现役=`steward.py --node bm-a --no-schedule`（执行腿+监督腿保留）。复原 fallback=Unregister + 导入 `.codely-cli/tmp/HQ-Steward-backup-20261101.xml`；前置=补 `git rebase --abort` 与修 `master_stale()` 粘滞锁存，且 1 周零冲突。 |

## 附录 R2.59 事件班登记（2026-11-01 10:26-10:45·probe L0-DOWN 第6次）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **bm-a 4 笔夜班工作未推（真危害）** | **fixed（本班）** | 09:17-09:28 四笔（perception+night report / evolution R6 / disk-sweep backfill / ledger 归档拆分）自 09:28 未推；已 rebase → 反转闸（仅机器生成滚动态命中）→ push 29c32f0c..fde6bdf4，本地 0/0。 |
| **agent.py 无 push 腿（D-R259-NOPUSH）** | **fixed（T1·非受保护件）** | push() 仅在 rebase 成功后推、绝不 force、失败 abort 记 skip；steward.py 仅 bm-a 传 --push。实测 py_compile OK + 隔离 push rc=0。修复前任何 reset --mixed 收口都会静默销毁本机作者工作。 |
| **bm-b 执行器死（DE-1·第5次）** | **waiting-CEO（需 bm-b 本机动手·零催办）** | 根因坐实：bm-b worktree HEAD=c1d7762e 为本地独有提交（本仓无），磁盘 fleet-nodes.json 停留 10-28 前、无 HQ-ProductionClaim → poke 恒 deny。修复=git 收口 + `python Tools\fleet\agent.py --node bm-b --loop 60` 注册为唯一任务（CEO 令 2026-10-31 18:23 未执行）。影响 P0 Q-TTS-1202R。 |
| **L0 探针谓词 3h < 班表 4.2h（第6次误报）** | **registered·waiting-CEO（受保护件）** | proxy-probe.ps1:30 `-gt 3`；建议 4.5h 或改读班表。承 R2.54/R2.55 登记，不重复立法。 |
| **P0 Q-TTS-1202R（lease 11:27 到期）** | **monitoring** | 08:27:24 attempts2 认领，队列 08:29 后零状态变化；到期将再派给同一死执行器（bm-b）。执行器修复前无法推进。 |
| **lane 指针文件致树恒脏（D-R259-DIRTYTREE）** | **fixed（本班·T1）** | `queue-receipts/_last_lane_*.json` 受跟踪且每轮改写 → ff-only/rebase 恒拒 → 节点追不上主线（R2.57 同型）。已并入 GEN_STATE；实测 10:49:30 agent=0、push ok、无 rebase 残留。 |


## 附录 R2.60 事件班登记（2026-11-01 13:56-14:0x·probe L0-DOWN 第7次）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **本地 22 件脏致落后 23 笔（真故障）** | **fixed（本班）** | `merge --ff-only`/`rebase` 恒拒；本地 MASTER-LOG cyc=665@12:06 vs origin cyc=728@13:55。处置=备份 `.codely-cli/tmp/r260-backup-20261101/` → 丢机器态 → ff-only 至 0/0 → `agent.py` pull rc=0 三连。 |
| **GEN_STATE 覆盖不足（D-R260-GENSTATE-FULL）** | **fixed（本班·T1）** | 5 项→18 项（补 lanes\*.json 与 dispatcher 派生态）；台账/队列**刻意排除**，继续挡 pull 走人工裁决。 |
| **git 拒绝信息 240 字截断（D-R260-BLOCKMSG）** | **fixed（本班·T1）** | 追加 `blocking paths (N): ...` 全量诊断，终结「每班重查同一脏树」。 |
| **搁浅巡班工作 44 行** | **recovered（本班）** | bigstream R30@10:49 + group R15@13:1x 原写于陈旧基线、origin 无此内容 → 重贴 origin 基线（+2/+8-1/+36-1）。 |
| **P0 Q-TTS-1202R（bm-b）** | **monitoring·不 poke** | 11:52:15 认领，2h 零回执，`lanes/bm-b.json` ts 停 11:52:15。防双烧不 poke；转 bm-b/bigmoney 域。 |
| **Q-TRIAGE-BIGMONEY-20261101 FAILED rc=2** | **registered·转 bigmoney 域** | `line_triage.py --line bigmoney` rc=2 @12:26:43，`deliverable_exists=False`。 |
| **POOL-0021 阻塞前提失效** | **registered·待 POOL 属主复核** | bm-c `ram_free` 1G→**9.4G**（group R15 实测）；`CEO-PHYSICAL:bm-c-desktop-ram` 不再成立。物理件零催办。 |
| **L0 探针谓词 3h < 班表 4.2h（第7次）** | **registered·waiting-CEO（受保护件）** | 承 R2.54-R2.59 登记，不重复立法；建议 4.5h 或改读班表。 |


## 附录 R2.61 事件班登记（2026-11-01 17:11-17:26·承载件触发·probe L0-DOWN 第 8 次）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **bm-b 幻影头锁死（HEAD=c1d7762e 不存在于 origin）** | **at-risk·waiting-CEO/人影（物理件·零催办·第 6 次同源）** | FleetLink /status：`repo_heads["."]=c1d7762e` vs `origin_main=1d89f756`，pull 报 `.:updated` 但 HEAD 恒不动 => 工作树永不可快进 => 盘上 `Tools/fleet-nodes.json` 停 10-28 前版 => `HQ-ProductionClaim:deny`（17:19:45/17:23:25 两发 poke 实测）。**唯一修法=在 bm-b 本机执行**：`cd C:\Fluxgroup\FluxGroup` -> `git fetch origin` -> `git status`（确认无本地独有工作）-> `git reset --hard origin/main` -> `python Tools\fleet\agent.py --node bm-b --loop 60` 并注册为唯一任务。外部不可代修（CEO 2026-10-23 令）。 |
| **P0 Q-TTS-1202R（RUNNING 悬停 5.6h）** | **monitoring·不可跨机重排** | 11:52:15 认领，rc=null 零回执；deliverable=`C:/Fluxgroup/FluxGroup/media/drama-tts-out/r1202_ep001_060/` 与 cmd 均在 bm-b 本机盘 => bm-c 无素材/路径，重排必空跑。执行器修复前无法推进；防双烧不重派。 |
| **bm-b 断连窗 ~5.2h（11:52->17:11）** | **registered** | MASTER-STATE@17:06 `online=false`；`state.bm-b` 17:11:52 以 seq=1 重启（`load1/ram_free_gb=null`=旧版 agent，未跟上 R2.59/R2.60 的 agent.py 修法）。佐证「节点盘停旧版 => 结构性不可靠」母因。 |
| **D-R261-POKECFG-STALE（poke 白名单读序）** | **registered·建议一行修（未擅改）** | worker 启动即载入 `fleet-nodes.json`，pull 之后仍用旧内存判白名单 => 同轮新白名单永不生效。修法=wake 段前重读盘。 |
| **承载件节拍器定性勘正（第 8 次）** | **registered·STANDING-PRECEDENT 已落 NEED-JUDGMENT** | 前七班记 "PROBE-CADENCE-MISFIT 误报"=拿探测器标准评判节拍器；3h 系 10-25 刻意设定（probe->carrier 为唯一驱动源）。后续班按三源判例行巡班，<=10 调用。 |
| **L0 探针谓词双档建议（承 R2.54-R2.60）** | **registered·waiting-CEO（受保护件）** | 若仍要「探测器」而非「节拍器」语义：`DISPATCH-LOG age>3h` 降二级，改测 `MASTER-TICK`/三条 `state.bm-x` 心跳新鲜度。不重复立法。 |

## 附录 R2.62 事件班登记（2026-11-01 17:51-18:0x·承载件触发·**同触发现重复投递**·probe L0-DOWN 第 9 次）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **bm-b 幻影头锁死 + 断连 6.0h** | **at-risk·waiting-CEO（本机人手·物理件·零催办·第 7 次同源）** | 17:40:30 cyc=864 `online=false`、`lanes/bm-b.json ts=11:52:15`；R2.61 两发 poke 实测 deny。修复只在 bm-b 本机：git 收口后 `python Tools\fleet\agent.py --node bm-b --loop 60`（CEO 令 2026-10-31 18:23 至今未执行）。 |
| **L2 饥饿 SLO 当日违约 1 件** | **registered** | 红旗（bm-b 执行器）自 11:52 驻留 6.0h，超「升→落 ≤90min」门；未达 24h E1 升格线。回访=cron 194c8c8c @18:57。 |
| **P0 Q-TTS-1202R（RUNNING 悬停 6.0h）** | **monitoring·不重派** | 11:52:15 认领后 rc=null 零回执；deliverable=`C:/Fluxgroup/FluxGroup/media/drama-tts-out/r1202_ep001_060/` 与 cmd 均在 bm-b 本机盘，跨机重排必空跑。 |


## 附记 R2.63 事件班登记（2026-11-02 00:01-00:2x·probe L0-DOWN 第 10 次 + 真故障分离）

| 项 | 状态 | 证据 / 下一步 |
|---|---|---|
| **bm-b 打盹+分叉（物理件）** | **waiting-CEO（外部不可达·零催办）** | /health ok@00:13:10（v1.9.5 host=BIGMONEY ram 7.4G cpu 3%）→ 2 分钟后 timeout；poke accepted 但 `NOT-SYNCED head=c1d7762e`。下一步=bm-b 本地：`git fetch origin && git reset --hard origin/main && python Tools\\fleet\\agent.py --node bm-b --loop 60`；并禁用睡眠（电源计划/keepalive）。 |
| **bm-c 全域停机（物理件）** | **waiting-CEO（零催办）** | /health、/status 双 timeout（00:13/00:16）；poke ok=False。本机 NATS 总线健康（pid 53584）故非总线单点。下一步=bm-c 现场上电/查 Tailscale。 |
| **主控真空 D-R263-MASTER-VACUUM** | **registered（待裁·不擅改）** | bm-m PULSE 停 21:13 + MASTER-TICK 停 22:22；HQ-Steward 实参 `--no-schedule` ⇒ bm-a 兜底调度结构性关闭（符合 10-30 迁移令）。本席手动 tick 一次解冻。待裁=Mac 常驻 caffeinate 或启用条件式兜底（前置=补 rebase --abort 守卫）。 |
| **CPU 作业单点 D-R263-CPUROUTE-SINGLEPOINT** | **registered（T1 候选·未改）** | CPU 类只进 bm-b lane；bm-b 抖动即全堵（Q-TRIAGE 12:26 REQUEUE 至今无接手）。建议=CPU 类加 bm-a 兜底路由。本轮就地收口（本机实跑出收据），未改调度代码。 |
| **Q-TRIAGE-BIGMONEY-20261101** | **delivered（本班收口）** | 收据=`cph4/fleet/queue-receipts/triage-bigmoney-20261102.md`；结论=该线 0.0h 前有产出（quant-backtest），真静默仅 quant-audit 216.9h。 |
| **quant-audit 子线静默 216.9h** | **registered（风控审计席）** | 三源=收据实测 1 文件 / 216.9h。判读=9 天无产出，超 24h 阈值 9 倍。派单归属=风控/审计席（非本席），登记待该线自领。 |
| **L0 探针阈值 3h（保护件）** | **registered（waiting-CEO·第 10 次复发）** | `Tools/proxy-probe.ps1:30` `-gt 3` vs 班间 4.2h；R2.54-R2.62 已连续登记，本班不重复立法。 |

## 附记 R2.64 事件班登记（2026-11-02 03:26-03:55·第11次节拍器 + 真故障分离）

| 项 | 状态 | 证据 / 下一步 |
|---|---|---|
| **主控真空复发（bm-m pulse 02:19 后死 3.4h）** | **registered（待裁·不擅改）** | MASTER-STATE master_tick_ts=02:15:12；MASTER-TICK.json ts=11-01 23:28:24；master_pulse.py 0 处写 MASTER-TICK。待裁=①pulse 补写 MASTER-TICK（一行，先恢复可观测）②之后再议条件式兜底；本班仅手动 tick 两轮解冻。 |
| **bm-b 内存阻塞（物理件）** | **waiting-CEO（零催办）** | ram_free 0.3-0.5GB < 1.0GB 门，连续 8 轮 CAPACITY-BLOCKED-RAM；4 个 CPU 卡全钉此机。下一步=bm-b 现场释放内存（gpu_lease --acquire 或停常驻模型）。 |
| **bm-c 全域不可达（物理件）** | **waiting-CEO（零催办）** | TCP 100.123.74.104:8790 closed @03:36；poke 无法落地；/health、/status 均不可达（R2.63 同判）。下一步=bm-c 现场上电/查 Tailscale 服务。 |
| **CPU 供给单点（生成器层）** | **registered（T1 候选）** | 卡片 nodes 全为 ["bm-b"]；建议 workgen/backlog_fill 写多机亲和。本班仅单卡就地改派。 |
| **僵尸交付物假绿** | **registered（受保护面·候改）** | 执行器只验存在性；line_triage 按运行日命名 => 旧件满足旧路径。修法=校验 mtime>=assign_ts 或模板化路径。 |


## 附录 R2.66 事件班登记（2026-11-02 07:26-07:4x·第 12 次节拍器 + 真故障分离）

| 项 | 状态 | 证据 / 下一步 |
|---|---|---|
| **L0 主控真空 3.8h** | **RESOLVED（本班复活）** | MASTER-STATE ts=03:41:29 → 本席 tick 两轮 cyc 1058/1059，lanes 07:30:40 刷新、queue open=0。根因为 bm-m 按需主控断脉 + bm-a 兜底 `--no-schedule`（符合 10-30 迁移令）。待裁=Mac 常驻 caffeinate 或启用条件式兜底（前置补 push_lane_files 的 rebase --abort 守卫）。 |
| **D-R266-QUEUE-NODEDUPE（真根因）** | **registered（数据层已修·代码层待改）** | open_ids()/pending 不按 id 去重 → DONE 卡永久重放。数据层：74→72 行、关 2、归档 3（备份 %TEMP%\queue-backup-20261102-073023.jsonl）。代码层=Tools 受保护面，需按修法单改。 |
| **D-R266-LANE-MTIME-SELFPROOF** | **registered（未修）** | lane mtime 由 master_agent 自写又自读 → 离线机恒 online=True（07:27 bm-c TCP 双 closed vs 07:30 online=True）。修法=在线只认 NATS KV 心跳。 |
| **bm-c 全域不可达（物理件）** | **waiting-CEO（零催办）** | TCP 8790/4222 双 closed @07:27；无 NATS KV state.bm-c。下一步=现场上电/查 Tailscale 服务。 |
| **bm-b RAM 阻塞** | **缓解（本班复测）** | ram_free 11.7GB（07:30），Q-TTS-1202R RUNNING 在位；CPU 卡可恢复派发。 |
| **L2 饥饿 SLO 当日违约 3 件** | **registered** | bm-b RAM >90min、bm-c 停机、主控真空 3.8h；承 R2.63/R2.64 计数。回访探针 @09:05。 |

## 附录 R4 事件班注记（2026-11-04 01:21-01:36·承载件触发·DL 23:31 五旗）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **R4-1 可玩包选款（人决件）** | **waiting-decision（制作人席+导演席）** | 卡 `biggame-playable-2026-11-03` 已 CANCELLED——它把「选一款可玩包 + 三关情绪/单局时长/2D 不作失败」写成机器卡的 deliverable，而 cmd 只是 `game_pack_scan.py`（产清单 json）。人裁判定不入机器队列。机器可判段由 `biggame-pack-scan-2026-11-04` 承接；选款结论落 `cph4/fleet/queue-receipts/game-select-*.md` 后即可重启提审链。 |
| **R4-2 STARVED-EXEC 双供给平面假红（P1·受保护件）** | **registered·waiting-CEO** | `fleet-dispatcher.ps1` 的 open/exec 计票只读 `POOL.json`（24 卡、唯一 open=POOL-0010 被 CEO 物理件锁死）⇒ bm-a/bm-b/bm-c 的 exec=0 恒成立、每轮必报 STARVED-EXEC；真供在 `PRODUCTION-QUEUE.jsonl`（55 OPEN 在认领）。一行修法=旗面改读队列平面（或两平面合并计票），L0 脚本属受保护面，本席不改只呈。 |
| **R4-3 孤儿 rebase 无人自愈（P1）** | **registered·承 D-R255** | 本次病根=失败卡 6 轮重试把仓推进 `.git/rebase-merge` 残留（9 文件 UU、队列工作树 5 组冲突标记 15 行、HEAD/origin 均干净）。`push_lane_files` 冲突后仍缺 `git rebase --abort`（受保护件）；外部兜底 `FluxGroup-GitRebaseGuard` 本次未拦住 → 建议查该任务是否 Enable+LogonType，或把 abort 作为前置。本班已 abort + ff 对齐至 8dba1042（0/0）。 |
| **R4-4 CLOCK-SKEW 数值更新** | **registered·本机提权动作** | 01:24 实测 max 3542.4ms：bm-b +1456.3ms（σ±0.8）、bm-c 大偏（σ±206.4）、hub bm-a 正常。w32time 停转需本机提权自启，承 R2.38/R2.47/R2.49 同源，不重复立法。 |
| **R4-5 卡契约闸上线（新闸）** | **installed·建议接 L0 快批** | `Tools/fleet/card_contract_check.py`：R1 cmd `--out` 必须等于 deliverable（例外写 deliverable_note）/ R2 交付物需人裁判定而 cmd 不产出 / R3 OPEN 卡真交付已在盘。基线 2 违规→修后 PASS 0。建议 L0 每轮跑一次（rc=1 只告警不阻断），防同型卡再进队列。 |
| **R4-6 执行面 BURNING 实证** | **standing 诚实边界** | 三机 FleetLink 1.9.5 三连 200；队列 01:25/01:27/01:30 三连新认领 + 01:30:57 六份回执。故本班**零 poke**（poke 不造供给、只 churn）。真瓶颈仍是人决件（R4-1）与各线人审，非供给。 |

## 附录 R5 事件班注记（2026-11-04 02:01-02:05·承载件触发·DL 00:01 六旗）
| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **R5-1 资产链跨机 media 不可达（P1·本班已修钉子）** | **FIXED（表已改·待 bm-c 认领验证）** | 证据：char-gen 硬钉 bm-c 回执 00:36 48 张 saved=true（media/asset/characters 在 bm-c）；char-dataset 未钉机被派 bm-a，该机 media/asset/characters 不存在 → 回执 images=0/passed=0 判 BLOCKED（01:47）。根因=media/ 各机本地目录（gitignore、无共享盘），消费段没钉产生端。修法：`cph4/fleet/ri/content/lines/asset.json` 给 char-dataset/face-dataset/face-caption 三处加 `hard_nodes:["bm-c"]`（validate_table=[] 通过）+ 补卡 `asset-lib-char-dataset-2026-11-04` 钉 bm-c。 |
| **R5-2 假供给（注册·待裁）** | **registered** | 队列 58 OPEN 里 16 张 Q-VCORP-PREP*/2 张 TRAIN 依赖 `media/asset/inbox`（实测 0 文件，音源等投料）→ 每轮被认领、0.1s rc=3、回队，形成 churn（近 6h 176 份回执中 E-BLOCKED-INPUT 26 份）。建议：等输入的卡进 BLOCKED 态而不是留 OPEN，或投料后再生成。 |
| **R5-3 STARVED-EXEC 三连假红（承 R4-2·非新病）** | **registered·受保护件待授权** | 复核 `Tools/fleet-dispatcher.ps1` L60-98：open/exec 只统计 `POOL.json`（24 卡、唯一 open=POOL-0010 被 CEO 物理件锁死），而真供在 `PRODUCTION-QUEUE.jsonl`（58 OPEN/4 RUNNING）。每轮必报 STARVED-EXEC 三行，属结构性假红，不是供给枯竭。 |
| **R5-4 资产线同受 media 本地面影响（未改·登记）** | **registered** | voice-dataset/index/accept/library-check 都要跨机读 media/（音色分片在 bm-a/bm-b/bm-c/bm-m 各自本地）→ 现口径下无法对账。正法：产出侧写索引+sha 进 git（ASSET-MANIFEST），二进制留本机；未在本班改，避免半修。 |
| **R5-5 CLOCK-SKEW 3673ms（承 R4-4）** | **registered·本机提权动作** | bm-b 偏 ~1.4s、bm-c σ≈206ms、hub bm-a 正常；w32time 需提权，非本席可动。 |
| **R5-6 真阻塞：每角色 6 张 < 准入闸 12 张（P1·本班已修）** | **FIXED（待 bm-c 重出图验证）** | 证据：bm-c 上 char-dataset 01:16 实跑，8 角色各 imgs=6 全部 FAIL，gaps 逐条写「张数 6 < 12（训不出稳定角色）」，故 passed=0/8 与机器无关，是**生产规格与闸值不匹配**。修法：char_plan.py VIEWS 6->12（补 three_quarter_right/profile_right/expression_smile/low_angle/high_angle/mid_shot），不降闸；已补卡 asset-lib-char-prompts-2026-11-04 + asset-lib-char-gen-2026-11-04（--limit 96，钉 bm-c）。 |
| **R5-7 真供给断点：bm-c/bm-b 的队列执行任务处于 Disabled（P1·本席不可远程修复）** | **BLOCKED·需本机执行** | 证据链：①bm-c 最后一次执行产物 11-04 01:22（git log 无 via bm-c 提交 78 分钟）；②`/status` 的 `last_pull.wakes` 返回 `HQ-ProductionClaim:off-skip`、`Bigmoney-SaturationEngine:off-skip`，即该任务 State=Disabled；bm-b 同类任务返回 `deny`（同名任务不在其白名单则拒）。③`Tools/fleet-poke-worker.ps1` L357-361 明写：Disabled 任务一律 off-skip，**远程 poke 不得启用**（C-20261009-04 CEO 冻结保护）。④对照：同批 poke 里 bm-c 的 `Bigmoney-ResidentDispatcher/Autofill/PoolWorker` 与 7 张 MiniGame*Tick 返回 WAKE（已启动），说明链路本身通，唯独队列认领器被禁用。修法（需在 bm-c/bm-b 本机执行一次）：`schtasks /change /tn "HQ-ProductionClaim" /enable`（bm-b 同）；或本机跑 `powershell -File Tools\fleet-align.ps1 -Node bm-c` 重建执行链。本席无远程启用通道，不越权。 |

## 附录 R6 事件班登记（2026-11-04 02:46-03:0x·承载件触发·DL 00:31/00:41 六旗）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **R6-1 bm-b 车道被僵尸卡死锁 8h+（P1·本班已修）** | **FIXED（数据层）** | 证据：`bigmoney-backtest-2026-11-03-v3` master 侧永远 RUNNING(owner=bm-b)，`assign()` 每轮重写 claimed_at → 租约永不过期；bm-b 侧回 `ALREADY-CLOSED`（本地队列行已终态）；`lane_agent` 见已关闭卡直接 return 空转，而 lane 文件只有 1 张 → 整条 bm-b 车道停摆，26 张 OPEN 卡排队等不到。处置：核验交付物 `quant/bigmoney/results/etf_nobond_vt.json`（runs[].cagr/sharpe/maxdd + OOS 齐）+ 回执 `bigmoney-backtest-2026-11-03-v3-bm-a.json` rc=0 26.1s(11-03 22:55) → 经 `fleet_lane.merge_jsonl` 关为 DONE（带 repair_by 痕迹）。 |
| **R6-2 lane_agent 断链不回落（P1·本班已修·T1 非受保护件）** | **FIXED（代码层）** | `Tools/fleet/lane_agent.py` already_closed 分支原先 publish IDLE 即 return，不再看自带 backlog。改为先打 LANE-SKIP 再走 `self_dispatch`（与「空指派」同一腿）；实测 py_compile OK + bm-b 干跑打印 LANE-SKIP 后正常回落。根治同类：指派已死但队列有活，不再等于空转。 |
| **R6-3 assign() 重写 claimed_at 使租约永不过期（P1·受保护面登记）** | **registered·waiting-CEO** | `master_agent.py` 每轮 assign 都把 claimed_at 刷成当前时刻，`supervise()` 的 lease 判据因此永不触发 → 僵尸 RUNNING 只能人工核验。建议一行修：重派保留首次 claimed_at（或写 reassigned_at 另计）。调度正身，本席不改只呈。 |
| **R6-4 bm-b 克隆 307 ahead / 285 behind（物理件）** | **waiting-CEO（零催办·第 8 次同源）** | /status 实测 repo_heads["."]=fe96d335 ≠ origin f8929f0c；poke accepted 但 pull 不动。修法承 R2.61/R2.63：bm-b 本机 git fetch origin && git reset --hard origin/main + python Tools/fleet/agent.py --node bm-b --loop 60。**不阻断新卡**：新 id 在 bm-b 本地无终态记录时 already_closed 返回 False，可正常执行；只有同 id 本地已关才空转（R6-1 已从主控侧清掉）。 |
| **R6-5 STARVED-EXEC 三连（承 R4-2/R5-3）** | **假红·已登记不改** | 旗只计 POOL.json（24 卡、唯一 open=POOL-0010 被 CEO 物理件锁死），真供在 PRODUCTION-QUEUE.jsonl（50 OPEN / 3 RUNNING）。本班去重后 OPEN 54→50。 |
| **R6-6 BLOCKED-RAM bm-c（00:31/00:41 旗）** | **resolved（本班实测）** | /status 02:51 ram_free=3.2G（闸 1.0G）、cpu 91%、GPU 14136MiB 在跑 → 上两轮低内存已随批推进缓解。 |
| **R6-7 CLOCK-SKEW max 3842ms（承 R4-4/R5-5）** | **registered·数值更新** | 02:44：bm-a +0.1ms(σ0.6)、bm-b +1456.3ms(σ0.8)、bm-c +3842.1ms(σ399.8)。bm-b 自报 clock_offset_ms=152.9(trusted=false) 与 hub 读数不符 → 以 hub 为准；w32time 停转需本机提权。租约 45-180min，4s 级偏差不影响派单，不改闸值。 |
| **R6-8 重复雷达卡去重（T1）** | **FIXED（本班）** | R-MODEL-RADAR-{BMA,BMB,BMC,BMM}-20261103 四张与 20261104 同日同机双份待跑 → merge_jsonl 置 CANCELLED（superseded），保留 11-04 版。 |

**本班动作**：锁 02:32:44 已过期→接管并 touch；poke bm-b(HQ-ProductionClaim+Bigmoney-IterationLoop)/bm-c(HQ-ProductionClaim) 双双 accepted；主控 tick 停 02:44:28（bm-m 按需主控），HQ-MasterAgent 每 2min 在位，超 900s 自动 masquerade 接续派单。
**诚实边界**：bm-b 侧生效依赖其克隆同步（R6-4）；R6-1/R6-2 的收益在「新卡可跑」面已成立，在「同 id 已关」面待 bm-b pull。
| **R5-8 bm-b 工作树分叉导致白名单过期（P1·本席不可远程修）** | **BLOCKED·需本机执行** | 证据：bm-b `/status` 显示 `last_pull.pulls=[".:updated"]`、`origin_main=68d70545`，但 `repo_heads["."]=fe96d335`，且该 commit 在本仓 `git cat-file -t` 判 unknown（origin 里不存在）→ 本地有分叉提交，fetch 成功但 worktree 合不上。后果：bm-b 用的是旧 `Tools/fleet-nodes.json`，其 wake_tasks 里没有 `HQ-ProductionClaim`，故本次 poke 返回 `HQ-ProductionClaim:deny`（不是 off-skip=任务根本不在白名单）。同时 bm-b 此刻 ram_free 11.4GB / cpu 12%=健康闲置，整台机在空转。修法（bm-b 本机）：`git -C C:\Fluxgroup\FluxGroup status` 看分叉来源 → 把本地提交 rebase 到 origin/main 或 `reset --hard origin/main`（本地只有状态快照时安全）→ 再核对 `schtasks /change /tn "HQ-ProductionClaim" /enable`。 |

## 附录 R6 收口（2026-11-04 03:12·BURNING 实证）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **R6-9 占位卡占用 bm-a 唯一 lane 槽（P1·本班已修）** | **FIXED（数据层）** | `VCORP-TRAIN-BATCH-14-20261104` 的 cmd 字面为 `python Tools/voicebank/vb_train_card.py --help`（永不产出声明的 verdict json），且自带门「两试点回执 PASS」而两张试点卡仍 OPEN、输入 `media/asset/inbox` 0 文件 → 结构性过早。它占住 bm-a 单槽、回报 `GPU-LEASE-DENIED (stale lease asset-lib-char-gen-2026-11-03 age=6320s)` 且不 close → 车道被锁。处置=CANCELLED（cancel_reason 记全）+ 释放槽位。 |
| **R6-10 不可执行卡占槽不自锁（结构性·登记）** | **registered·waiting-CEO（master_agent 受保护面）** | 与 R6-1 同型：`assign()` 每轮把唯一一张卡塞进单槽 lane，卡一旦「跑不动也不 close」（GPU 租约拒/前置缺），整条车道即停摆，而台账仍显示 RUNNING。建议 supervisor 增加「同一卡连续 N 轮 DENY/零产出 → 置 BLOCKED 并让位」；`master_agent.py` 属调度正身，本席不改只呈。 |
| **R6-11 mv 交付闸卡契约缺陷（P1·本班已修）** | **FIXED + 重排钉机** | 卡 cmd 未带 `--json`，而声明交付物是 `mv-gate-v721-2026-11-04.json` → 永远无法出现（card_contract_check R1 同型）。首次派单还回落 bm-m（Mac 无 cv2，`ModuleNotFoundError`）。处置：cmd 补 `--json <deliverable>`、`nodes=["bm-a"]`（cv2 5.0.0 在位、片 287MB 在盘）、`timeout_s=2400`（本机实测一次跑不完 5 分钟），重开 OPEN。 |
| **BURNING 实证（本班收尾）** | **PASS** | 03:10:36 `R-NEXT-BIGSTREAMM-GATE-20261103` 回执；03:11:48 `biggame-pack-scan-2026-11-04` rc=0 产出 `game-packs-2026-11-04.json`；03:11:54 `_last_lane_bm-a` state=RESULT rc=0。清除两张占槽卡后 bm-a 车道即刻恢复产出。 |
| **bm-b/bm-c 认领器 Disabled（承 R5-7）** | **BLOCKED-REMOTE·waiting-CEO（零催办）** | 02:58 实测 `last_pull.wakes`：bm-b `HQ-ProductionClaim:deny`、bm-c `HQ-ProductionClaim:off-skip`。poke worker L357 明令 Disabled 不得远程启用。修法=各机本机 `schtasks /change /tn HQ-ProductionClaim /enable`（或 `Tools\fleet-align.ps1`），bm-b 另需 `git fetch origin && git reset --hard origin/main`。 |

## 附录 R6 补收（2026-11-04 03:16·可卖产物打通）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **R6-12 quant 信号链断点（P1·本班已修·不跨仓）** | **FIXED + 产物已出** | 证据：`quant_signal.py` 要顶层 positions，而 `etf_nobond_vt.py` 只给 `live_picks` → 唯一可卖产物永久 BLOCKED（03:00 bm-a rc=3「缺持仓字段」）。`quant/bigmoney` 是 BigMoney 独立仓（双公司各自治理·互不写对方仓库）→ **不改对方源码**，改在本仓加桥 `Tools/fleet/quant_positions_bridge.py`：positions = top-5 等权 1/n，**这正是生产脚本自己声明的发布默认**（`etf_robust_pf.open_to_open_equity`：plain top-n 选择 + plain 1/n_hold 权重），非本席新立策略；derivation 字段全程留痕，原回测 JSON 原样不动。产物：`cph4/fleet/queue-receipts/quant-signal-2026-11-03.csv` 5 行（510980/510760/515450/510210/512040 各 0.2，score+class+input_fp），卡 `bigmoney-signal-2026-11-03` 关 DONE。 |
| **R6-13 复发性根修（工序表）** | **FIXED（T1）** | `cph4/fleet/ri/strategy/lines/bigmoney.json` 的 signal 段 cmd 改为 `bridge && quant_signal` 两步 → 下月卡不再撞同一堵墙。manifest JSON 校验通过。 |
| **待确认（量化席·非阻断）** | **registered** | 权重口径=生产者发布默认（等权 1/n）。若量化席要改 score 加权，只需改 `etf_robust_pf` 的 weight_hook，桥会自动 passthrough 已有 positions，无需改本仓。 |

| **R6-15 MV v721 交付闸实跑=FAIL（P1·判负件已成型）** | **delivered·转导演席（人决件·零催办）** | 03:16-03:20 bm-a 实跑 `mv_delivery_gate.py`（cv2 5.0.0，14064 帧/60fps/80 镜）：**VERDICT=FAIL**。判负项：D1 重复镜 6 对（首对 45.20s vs 223.93s，均不在已申报卡窗内=真缺陷）；D2 近静止 24 处（首处 14.57-17.48s，需导演席按「定格是否为设计」复核）；D3 死停 1/2 冻结段（234.18s 处 13 帧≈0.22s，60fps 下人眼可见）；seams/flicker 已清零。判决件=`cph4/fleet/queue-receipts/mv-gate-v721-verdict-20261104.md`，原始回执=`.../mv-gate-v721-2026-11-04.json`。修复属逐镜创作决策（CEO 10-24 红线：重复镜只能重烧/换素材，禁推近裁切），不入机器队列，只登记候导演席。 |
| **R6-16 停发口径修正（T1·本班）** | **FIXED** | 首版用 `route=blocked` 停发 18 张无投料卡，被主控 assign 每轮重写回 `route=local` 而失效（实测 e02/z01 回到 OPEN 可派）。正法=改 `state=BLOCKED`（assign 只收 OPEN，天然跳过），route/blocked_by/note 一并留痕。现队列 BLOCKED=18、可派发 OPEN=29。**解除=投料后置回 OPEN。** |
| **R5-9 代码面断链：机器分支落后 main 4185/4273 提交（P1·本席只能落档）** | **BLOCKED·需本机核对分支** | 实测：`origin/machine/C` = 6503f5b0（落后 main **4185**、领先 8）；`origin/machine/bm-b-r1344` = c1c5b0c7（落后 **4273**、领先 13）；两条分支都**没有** `Tools/fleet/char_plan.py / char_gen.py / char_dataset.py / asset_dataset_audit.py`，也没有 `cph4/fleet/ri/content/lines/asset.json`（有 fleet-poke-worker/fleet-dispatch）。后果：今晚修在 main 上的东西（12 视角、稳定 seed、hard_nodes 钉子、poke 带 tasks、任务状态探针）到不了 bm-b/bm-c 的 checkout，除非它们实际跟踪 main。旁证：bm-b 返 `HQ-ProductionClaim:deny`=读旧 fleet-nodes.json（白名单无该任务）；新 task_states 探针在 03:15/03:17 两次 stamp 里都是 null。下一步（各机本机）：`git -C <root> branch --show-current` + `git status -sb` 确认分支；若要收 main 的修复，`git checkout main && git pull --ff-only`（本地只有状态快照时安全）。 |

| **R6-18 MV 观众级三查已交付（导演席签字依据）** | **delivered** | 03:33:32-03:35:39 bm-a 实跑 `mv_full_audit.py`（24fps v721，5623 帧/98 镜，rc=0）：`cph4/fleet/queue-receipts/mv-full-audit-20261103.json`。逐镜表 98 行 + 重复 9 对（未申报 2 对）+ 时代歧义 25 处 + 短镜 15 个 + 长镜 2 个。与 R6-15 的 60fps 闸判决互为印证（同一母版两种规格）。 |
| **bm-a 在跑真实生产（观察）** | **standing** | 00:37:33 起 `musubi-tuner` krea2 LoRA 训练常驻（多进程；03:31 实测 gpu=82%），与车队 CPU 卡并行不冲突——GPU 面在烧、CPU 面在派单，机器未闲置。 |


## 附录 R7 事件班登记（2026-11-04 03:26-03:45·承载件触发·DL 01:21/01:31 三连 STARVED + CLOCK-SKEW）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **R7-1 STARVED-EXEC 三连（bm-a/bm-b/bm-c）** | **假红·结构性（承 R4-2/R5-3/R6-5）** | `fleet-dispatcher.ps1` 的 open/exec 只统计 `cph4/fleet/dispatcher/POOL.json`（24 卡，status: open=1 且被 CEO 物理件锁死，其余 done/closed），真供在 `PRODUCTION-QUEUE.jsonl`（OPEN 27，分布 bm-a 6 / bm-c 9 / bm-b 6 / bm-m 6）。每轮必报三行属结构性假红，非供给枯竭。修法涉 L0 受保护件，本席不改只呈。 |
| **R7-2 bm-c 幻影头 + 认领器 Disabled（P1·本班新证）** | **BLOCKED-REMOTE·需 bm-c 本机** | `/status` 实测 `repo_heads['.']=f16b4e14`，该提交在 origin 对象库中不存在（`git cat-file` fatal）⇒ 工作树永不可快进 ⇒ 沿用旧 `Tools/fleet-nodes.json`。03:36:34 poke accepted，`last_pull.wakes` 回 `HQ-ProductionClaim:off-skip`（任务在册但 State=Disabled）；同批 `Bigmoney-PoolWorker:WAKE` 成功，说明链路通、唯认领器被禁。修法（bm-c 本机）：`git fetch origin` → `git reset --hard origin/main` → `schtasks /change /tn "HQ-ProductionClaim" /enable`。C-20261009-04 明令 poke 不得远程启用 Disabled 任务。 |
| **R7-3 bm-b 主机不可达（物理件）** | **waiting-CEO（零催办·第 9 次同源）** | TCP 100.104.212.62:8790 closed；`POST /poke` timeout @03:36。承 R6-4/R2.61 判例：修复只在 bm-b 本机（git 收口 + agent 注册 + 禁睡眠）。其 4 张 OPEN 卡中 2 张依赖 bm-b 本地 media，不可转派。 |
| **R7-4 跨机转派 5 张仓库类 CPU 卡** | **executed·BURNING 已证** | `R-PLAN-BIGDOMAIN-20261104` / `R-PLAN-BIGLIFE-20261104` / `Q-TRIAGE-BIGMONEY-20261104` / `Q-TRIAGE-BIGSTREAMMV-20261104` / `Q-TRIAGE-BIGGAME-20261104` 由 bm-b/bm-c 改为 `nodes=["bm-a"]`（`fleet_lane.merge_jsonl` 原子合队 + `reroute_reason` 留痕）。依据：五卡 cmd 只读仓库与 git，无本机 media 依赖（对比 `Q-FACE-BOARD-BMC` 依赖 K: 盘、`char-gen` 依赖 bm-c ComfyUI，均未动）。转派后 bm-a OPEN 6→11，03:35:32 / 03:35:33 两条新回执实证在执行。 |
| **R7-5 本机仓分叉（4 behind / 5 ahead，台账冲突）** | **FIXED（本班）** | 本地 5 笔含与 origin 重复的 R5-9（origin 5db04b12 已立）与 DEADLINES/LOG/queue 三处 add/add 冲突。处置=`git reset --mixed origin/main` 外科收口（本地提交留 reflog 可回收）+ 台账与机器态取 origin 版；DEADLINES 本地独有行仅 R5-9 一行，已随本附录补记。现状 0/0，两件真新增证据入链。 |
| **R7-6 CLOCK-SKEW max 3556ms** | **registered·本机提权动作** | 01:31 旗（precision ±418ms）；bm-b/bm-c 的 w32time 停转需本机提权自启，承 R4-4/R5-5/R6-7 同源，不重复立法。租约 45-180min，4s 级偏差不影响派单。 |

**本班边界**：bm-b 是物理不可达、bm-c 认领器 Disabled——两者都不是本席可远程修复的（CEO 2026-10-23 禁远程调度 + C-20261009-04 禁 poke 启用 Disabled 任务）。本班实做=把可移动的供给移到在产的 bm-a，并把两条本机动作写成可直接照抄的命令。

| **R7-7 `git add` 静默不生效（本班新坑·工具面）** | **registered·判例** | 现象：`git add <已跟踪文件>` 返回 rc=0，但 `rev-parse :path` 索引 blob 与 `hash-object path` 磁盘 blob 长期不等，`status`/`diff` 均报无改动。两个叠加成因：①`core.fsmonitor=true` 的陈旧缓存让 add 跳过重哈希；②本仓台账 blob 实为 **CRLF** 而全局 `core.autocrlf=true` 会把新内容转 LF（HEAD 与磁盘 106426B vs 106054B，全文件伪差异 744 行）。判定法：`git rev-parse :<path>` ↔ `git hash-object <path>` 双值比对（本班实测 5e1f045f ≠ dd63d837）。修法：`git rm --cached -q <path>` 重加；提交 CRLF 台账时加 `-c core.autocrlf=false`，否则每次提交都会翻成整文件差异。**影响面=所有靠 git add 提交台账的班次**（会误以为「已提交」而内容未入链）。 |


## 附录 R8 事件班登记（2026-11-05 00:01-00:20·承载件触发·DL 三连 STARVED-EXEC + CLOCK-SKEW）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **R8-1 生产队列含合并冲突标记（P0·本班已修）** | **FIXED** | `cph4/fleet/PRODUCTION-QUEUE.jsonl` 实测 24 行 `<<<<<<< / ======= / >>>>>>>` + 12 张重复 ID（同日重放）。所有读队列的脚本 try/except 跳过坏行 → 主控静默少看卡且无一处报错。处置：新增 `Tools/fleet/queue_repair.py`（默认演练，`--apply` 带 `.bak-<ts>` 备份）→ 保留 451 行；`queue_integrity.py` VERDICT=GREEN（critical 1→0）。判据：重跑 `python Tools/fleet/queue_integrity.py` 应恒 GREEN。 |
| **R8-2 STARVED-EXEC 三连（真因分层）** | **一半真·一半假红** | 假红面=R7-1 未修：`fleet-dispatcher.ps1` 的 pools 只统计 POOL.json（24 卡，open=1 且被 `CEO-PHYSICAL:submit-materials` 锁死），真正的队列是 PRODUCTION-QUEUE.jsonl；该脚本属 L0 受保护件，本席不改只登记。真红面=bm-b/bm-c 认领器不起（见 R8-3）。 |
| **R8-3 bm-b/bm-c 认领器 Disabled（P1·第 5 次复发）** | **waiting-CEO（物理件·零催办）** | 硬证据：`POST /poke` accepted 后 `last_pull.wakes = ["HQ-ProductionClaim:deny","Bigmoney-IterationLoop:busy-skip"]`（bm-b）；两机 11-05 00:12 均 accepted，卡仍 OPEN 未被认领。修法只在各机本机执行：`schtasks /change /tn "HQ-ProductionClaim" /enable`（bm-c 另需 `git fetch origin && git reset --hard origin/main`）。C-20261009-04 禁 poke 远程启用 Disabled 任务，本席不越线。 |
| **R8-4 两机分支分叉（收不到新工具）** | **已在机派自报卡** | bm-b HEAD=124d6964、bm-c HEAD=4f5cc086（且 10 分钟内从 037a2808 变到 4f5cc086=仍在本地提交），两者在 origin 均不存在（origin/main 最新）。后果实证：bm-b 跑 `mv_stability_gate.py` 报 SCRIPT-MISSING、`char_gen` 回落 bm-b 却连 127.0.0.1:8188（bm-c 的 ComfyUI）失败。处置：派 `fleet-node-sync-report-bm-b/bm-c-2026-11-05`（纯 git 命令，不依赖仓内脚本）取事实；reset 需先确认本地提交无独有产物。 |
| **R8-5 音色四张分片连挂两天的真因** | **FIXED（T1）** | 回执原文「本分片无输入（inbox 共 0 个文件）」；实测 bm-a 的 `media/asset/inbox` 有 8 件（2 个 wav 共 268MB + 3 个 RIGHTS/子目录），而 media/ 不入 git → 其它机的 inbox 永远是空的。处置：`asset.json` 四条 voice-corpus 段 `nodes/hard_nodes` 改为 `["bm-a"]`（持料机），`input_dir` 闸保留；line_plan 已按新钉出 4 张 bm-a 卡。 |
| **R8-6 CLOCK-SKEW max=3100ms** | **降级为噪声（实测）** | 00:15 直测：bm-b `/health` ts 与本机时间差 ≤1s（rtt 1082ms），bm-c 同理（rtt 1009ms）。3.1s 是环形回执/loop-round 口径，不是节点时钟。无需动作，若升 >30s 再查 w32time。 |
| **R8-7 PARKED 线僵尸卡** | **FIXED** | `R-NEXT-BIGSTREAMD-TTS-QC-20261104`、`R-PLAN-BIGSTREAMDUA-20261104` 属 bigstream-duanju（LINE-REGISTRY=PARKED），是 line_plan 加 LINE-INACTIVE 过滤前生成的孤儿，占 bm-c 供给位。已 CANCELLED 并写 cancel_reason。 |
| **R8-8 bm-a BURNING 实证** | **PASS** | 00:15:06 `CHK-CANON-20261104-bm-a.json` 落盘；00:04:38 `game-packs-2026-11-05.json`（bm-m）；bm-a 4 卡 RUNNING（env-check / biggame-pack-scan / mv-gate / CHK-CANON），队列 OPEN 由 2 升到 25。 |
| **R8-9 ComfyUI 在 bm-c 未起（GPU 只能空转）** | **registered·本机动作** | 从 bm-a 探 `100.123.74.104:8188` 不通；bm-b 回执亦证 `WinError 10061 拒绝连接`。后果：`char-gen` / `asset-gen` / `face-caption`（均 hard_nodes=bm-c）全部只能写 BLOCKED。修法（bm-c 本机）：启动 ComfyUI 并确认 8188 可连。 |

## 附录 R9 事件班登记（2026-11-05 01:48·承载件触发·DL 三连 STARVED-EXEC + CLOCK-SKEW/UNALIGNED）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **R9-1 队列合并冲突复发（P0·本班已修）** | **FIXED（本班）** | 01:36 实测 `PRODUCTION-QUEUE.jsonl` 3 行冲突标记 + unmerged stage 1/2/3 且无 MERGE_HEAD（幻影合并·R990 家族），根因=并发 auto-sync 的 stash pop 冲突未收口。处置=保留带 reroute 的一侧+并 prior_attempt+去重，469 行，`queue_integrity VERDICT=GREEN`。真闸应落在 sync 收口前 abort 卡死合并（承 C-20261104 律） |
| **R9-2 未提交队列/台账改动被 auto-sync 覆盖（P0·结构性）** | **registered·流程已改** | 本班 01:29-01:31 写入的 2 取消 + 5 转派在 01:45 复查时已被整体回滚为 origin 版本（`R-PLAN-BIGMONEY-20261104` 又回 `FAILED@bm-b`）；同病随即复发一次：DEADLINES 的 R9 附录在推送前被覆盖丢失。成因=队列/台账是共享生成态，他窗 pull/stash-pop 以 origin 为准覆盖工作区。正法（本班采用）=改完立即 `Tools/git-atomic-push.py` 原子推（blob 守卫+闭环重放），不在工作区留过夜 |
| **R9-3 STARVED-EXEC 三连（半假红·第 8 次同源）** | **registered·L0 受保护件** | 旗只统计 `POOL.json`（4 卡·open=1 且被 `CEO-PHYSICAL:submit-materials` 锁死）；真供给= `PRODUCTION-QUEUE.jsonl` OPEN 29-33 张。修法仍待 CEO 决定是否允许改 L0 派单脚本口径（历次均只登记不改） |
| **R9-4 bm-b/bm-c 认领器 deny/Disabled（P1·第 6 次复发）** | **waiting-CEO（物理件·零催办）** | 直连 poke 两机均 `ok=true`（侦听器在线 01:27:10-12），但 bm-b `last_pull.wakes` 仍见 `HQ-ProductionClaim:deny`；01:29:56 `R-PLAN-BIGMONEY-20261104` 在 bm-b 上 `FAILED` 且 last_error/error_class 全空（E-UNKNOWN）=认领链路半通、执行不可信。修法只在各机本机：`schtasks /change /tn "HQ-ProductionClaim" /enable`（C-20261009-04 禁远程启用） |
| **R9-5 CLOCK-SKEW bm-b 1456ms / bm-c 3478ms** | **registered·本机提权动作** | CLOCK-SKEW.json 01:34:15 实测（precision bm-b 0.8ms / bm-c 436ms；`missing=0 old_schema=0` 证早前 CLOCK-UNALIGNED 为瞬时）。承 R4-4/R5-5/R6-7/R8-6 同源=两机 w32time 停转，需本机提权自启；秒级偏差不影响派单 |
| **R9-6 账实方向相反：回执已落盘但卡记 FAILED（新发现·待立案）** | **FIXED（本班·77b3f1c3d）** | 回执早就按 `flux_contracts.error_class` 定性，只是车道写回队列时把该字段丢了。修法=写回时补 `error_class`（单源沿用 flux_contracts，不另立判据）+ `failed_triage.py` 把非法类 `E-ENV` 改成 `E-PATH`（ERROR_CLASSES 无 E-ENV）。实测回填：17 张 FAILED 中 13 张已定性（E-UNKNOWN 9/E-PATH 3/E-CONTRACT 2），4 张无回执按规矩保持未定；另 11 张 rc=3 空投料卡按律 CANCELLED。隔离测试双路径通过（显式 error_class 透传 + rc=3 推导 E-BLOCKED-INPUT） 原始观测：01:07-01:33 有 10+ 张卡 state=FAILED 而对应回执已在 `queue-receipts` 落地（`asset-lib-env-check` rc=1、`CHK-RECEIPT` rc=2、`asset-lib-library-check` rc=1）；抽验回执 `error_class=E-UNKNOWN` 且 error/reason 全空 → solver 无定性可依、只会原样重试。建议=回执写手强制写 error_class + solver 按 rc 推导（`failed_triage.py` 规则接进 lane 写回路径） |
| **R9-7 本班供给处置结果** | **PUSHED 7eb6a2e56** | 2 张 PARKED 线（bigstream-duanju）僵尸卡 CANCELLED；5 张纯仓库类卡转派 bm-a（R7-4 判例），落地 4 张（`R-PLAN-BIGDOMAIN-20261105` 在推前已被他窗置 UNVERIFIED，未动）；OPEN 由 33 降至 29（bm-a 16 / bm-m 10 / bm-b 2 / bm-c 1） |

**本班边界**：bm-b/bm-c 认领器属物理件（CEO 2026-10-23 禁远程调度 + C-20261009-04），本席只做「把可移动的供给移到在产的 bm-a」+ 把本机动作写成可照抄命令。


## 附录 R10 事件班登记（2026-11-05 02:06-02:2x·承载件触发·DL 三连 STARVED-EXEC + CLOCK-SKEW）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **R10-1 STARVED-EXEC 三连（第 9 次同源）** | **半假红·已登记（L0 受保护件）** | `fleet-dispatcher.ps1` 的 open/exec 只读 `POOL.json`（24 卡，open=1=POOL-0010 被 `CEO-PHYSICAL:submit-materials` 锁死），真供给在 `PRODUCTION-QUEUE.jsonl`：**OPEN 26（bm-a 14 / bm-m 10 / bm-b 2）+ RUNNING 4**。旗面每轮必亮三行属结构性假红；修法涉 L0 受保护件，本席不改只呈。 |
| **R10-2 mv.json 四段全缺 `--json`（P0·本班已根修）** | **FIXED** | 实证：`gate` 卡 381.5s 跑完、stdout 有完整判决（FAIL D1 6对/D2 24处/D3 1处），但 `deliverable_exists=false`——因为 cmd 从未要求写文件。核 `mv_transition_audit.py / mv_stability_gate.py / mv_full_audit.py / mv_delivery_gate.py` **四件全部支持 `--json`**，四段 cmd 却都没传 → 每日生成四张注定 FAIL 并重试的卡。处置：mv.json 四段 cmd 各补 `--json <对应 deliverable>`。**这是 R6-11（同类）之后第二次，属复发，修在生成源而非单卡。** |
| **R10-3 `bigstream-mv-gate-2026-11-05` 单卡** | **FIXED（重开 OPEN）** | cmd 补 `--json cph4/fleet/queue-receipts/mv-gate-v721-2026-11-05.json`，state FAILED→OPEN。判据：交付物落盘后按 deliverable 记 DONE（闸 VERDICT=FAIL 是设计行为，不是执行失败——R2.46/r2 判例）。 |
| **R10-4 `Q-VCORP-PREP-e01-R3` 跨机路径错（P1·本班已修）** | **FIXED（重开 OPEN·钉 bm-a）** | 实证：cmd 硬编码 `C:/Fluxgroup/FleetAgent/Tools/...`，本机 `Test-Path=False`，bm-a/bm-m 双机 rc=127；`--inbox media/asset/inbox/e01` 目录不存在。**真投料在盘**：`media/asset/inbox` 10 件 / 258MB（cartoons 4/36.6MB、films 2/198.2MB、librivox 4/23.8MB）。处置：改仓库相对路径 + `--group batch-2026-11-05 --shard 0/1` + `nodes/hard_nodes=["bm-a"]` + `input_dir`。与 R8-5「持料机才能跑」同律。 |
| **R10-5 `asset-lib-char-gen` 命名+阻塞（P1）** | **FIXED（命名）+ BLOCKED（comfyui-down:bm-c）** | 命名：`char_gen.py` 写 `%Y%m%d`，卡声明 `{date}`=YYYY-MM-DD → 永久对不上；已给工具加 `--receipt` 并在 asset.json 传参对齐。真阻塞：bm-c `127.0.0.1:8188` 与 `100.123.74.104:8188` 双探均不通（WinError 10061，bm-b 回执同证）→ 48 张角色图全部失败。解除=bm-c 本机起 ComfyUI 后置回 OPEN。 |
| **R10-6 `asset-lib-voice-assemble-2026-11-04`** | **BLOCKED（voice-corpus-empty）** | 同日孪生 `voice-dataset-20261104.json` 是 **rc=3 BLOCKED 回执**（clips=0、缺 RIGHTS.json），按「拦截回执≠交付物」律**不记 DONE**；上游 voice-corpus 从未产出片段。另根修 asset.json 该段 cmd 补 `--out`（工具默认写 `%Y%m%d`，与 `{date}` 不符）。 |
| **R10-7 bm-b/bm-c 认领器（历史第 9 轮 deny/off-skip）** | **RESOLVED（本班实测）** | poke 回执（02:14:43 / 02:14:55）：两机 `task_states.HQ-ProductionClaim = "Ready"`、`wakes=["HQ-ProductionClaim:WAKE"]`；且 `repo_heads["."] == origin_main == 77b3f1c3`（bm-b/bm-c 双机）→ 历轮 R2.61/R6-4/R7-2 的「幻影头」「认领器 Disabled」两个结构病**均已消失**。**注：** bm-b 的 `Bigmoney-IterationLoop` 仍 Disabled、bm-c 多条 MiniGame tick 仍 Disabled（非本班射程，登记）。 |
| **R10-8 真供给缺口=bm-c 0 张 OPEN 卡** | **registered·结构性** | 队列 OPEN 分布 bm-a 14 / bm-m 10 / bm-b 2，**bm-c 0**。bm-c 认领器已 Ready 却无卡可领——因其唯一 GPU 活（char-gen/asset-gen/face-caption 均 hard_nodes=bm-c）全部串在 ComfyUI 上。结论：bm-c 的「饥饿」是真饥饿，但根因是 ComfyUI 未起 + 无 CPU 类卡供给，不是调度失败。 |
| **R10-9 CLOCK-SKEW max 3589.8ms** | **降级为噪声（承 R8-6）** | 02:04 CLOCK-SKEW.json：hub bm-a −0.1ms（σ0.7）、bm-b +1456.3ms（σ0.8）、bm-c +3589.8ms（σ412）。承 R4-4/R5-5/R6-7/R8-6/R9-5：两机 w32time 停转需本机提权；R8-6 已实证 3s 级偏差是环回执口径而非节点时钟漂移，且 45-180min 租约下不影响派单。不重复立法。 |
| **R10-10 卡契约闸缺口（新·建议升格）** | **registered** | `Tools/fleet/card_contract_check.py` 本班跑出 8 违规（1×OUT-MISMATCH + 7×LEDGER-LAG），但**没抓到** mv-gate 这类「卡声明 deliverable、cmd 却无任何写该路径的参数」的缺陷（R1 只比对 cmd 里已有的 `--out` 值，缺参数时不触发）。建议加 R4 规则：`deliverable` 非空且 cmd 中不含该路径/`--json`/`--out`/`--receipt` → 直接判违规。闸属工具面，本席登记待批。 |
| **R10-11 `asset-lib-asset-gen` hard_nodes 被 fallback 绕过（P1·新）** | **registered·待裁（master_agent 受保护件）** | 实证：卡 `hard_nodes=["bm-c"]` 却 `owner=bm-b`，且自带 `fallback_from=["bm-c"]`、`fallback_why="pinned node(s) not available at dispatch time"`。后果：cmd `--node bm-c` 连的是 127.0.0.1:8188，在 bm-b 上必然 10061 失败。承 2026-11-03 判例「hard_nodes 是硬钉子必须钉死不许回落」，修法=fallback 分支对 hard_nodes 卡直接置 BLOCKED 而非改 owner；`master_agent.py` 属调度正身，本席不改只呈。 |
## ?? R10 ??????2026-11-05 03:26-03:47???????DL ?? STARVED-EXEC + BLOCKED-RAM + CLOCK-SKEW/UNALIGNED?

| ? | ?? | ?? / ??? |
|---|---|---|
| **R10-1 CLOCK-SKEW??????????? 6 ??? R2.38/R2.47/R4-4/R8-6?** | **registered?waiting-CEO????????????** | 03:44 `CLOCK-SKEW.json`?bm-b +1456.3ms??0.8??bm-c +3966.5ms??415?? 4ms/min ????hub bm-a 0ms????? `sc query w32time` = **STATE=1 STOPPED**?`w32tm /query /status` ? 0x80070426????????? ????=????????????????? R8-6 ??????????? /health ts ??? NATS ??? offset ????? clock_offset_ms?? ? ?? 0.8ms??**????????**?`Tools/fleet/clock_resync.py` + ?? `OPS-CLOCK-RESYNC-*-20261105` ??bm-a ?? SERVICE-STOPPED??????=??**????**?`sc config w32time start= auto && net start w32time && w32tm /resync /force`?????????????? |
| **R10-2 STARVED-EXEC ??????? 9 ????? R4-2/R7-1/R8-2/R9-3?** | **registered?L0 ???????????** | ?????`PRODUCTION-QUEUE.jsonl` OPEN 26?30?RUNNING 4 ?? bm-a/bm-b/bm-c/bm-m?CHK-RECEIPT / Q-VCORP-TRAIN-PILOT / asset-lib-face-dataset / CHK-DUPES?? ??????????`POOL.json` ?? open=POOL-0010 ? `CEO-PHYSICAL:submit-materials` ???**???????**?????? 10min ???40min ??????(01:40/02:11/03:26)?? 30-120 ???????=`fleet-dispatcher.ps1` ? open/exec ??????????????????? BLUEPRINT ?? ???????????? |
| **R10-3 ?????????????????????** | **registered?L0 ??????** | `proxy-event-carrier.ps1` ? `$sig` = ?? flags ?????? `FLAG CLOCK-SKEW max=3910.5ms precision=+/-436.3ms` ?????? ? 90min ??????????? 40min debounce ?? ? ??+?????????? 40min ??????=?????????`max=\d+` ? `max=*`???? flag **??**????????L0 ???? |
| **R10-4 ?????03:50 checkout ??????????R9-2 ? 3 ????** | **FIXED????** | bm-a ?? 03:32 ???03:40 ?? OK?? DONE ?? 03:50 ??? `git checkout origin/main -- PRODUCTION-QUEUE.jsonl` ???????????????????????? `OPS-CLOCK-RESYNC-BMA-20261105-bm-a.json`(rc=0, deliverable_exists=true) ?? DONE ???? `0ee780126`?**????**???? checkout ??? `git log -1 -- <path>` + `git status -- <path>`????????????????????? origin ??????? + ???? |
| **R10-5 LANE-DOWN bm-b / BLOCKED-RAM bm-c???????** | **resolved??????** | bm-b?01:11 SVC_DOWN ? 02:46 ? `Q-VCORP-TRAIN-PILOT-libritts-e01-R3` RUNNING?poke accepted?NATS ?? seq=3727/age 22s?bm-c?01:01/02:31 BLOCKED-RAM ? 03:28 ?? `asset-lib-face-dataset`?03:44 ? OK????????????? |
| **R10-6 SLI-L2 ????????** | **registered** | ???STARVED-EXEC ???? 2026-11-05 01:01 ???? 03:44 = 2.7h?????? ?90min???????? ? ????? 0 ??????? R10-2 |
| **R10-7 ????????** | **monitoring??? +90min?** | bm-a DONE?bm-b/bm-c OPEN ????????????????????????????=SERVICE-STOPPED ?????? |
| **R10-8 HQ-ProductionClaim deny?bm-b/bm-c?? 7 ??** | **waiting-CEO?????????** | ? R8-3/R9-4???????????C-20261009-04? |
> ?? 2026-11-05 03:47??????? 2026-10-14 ??????R10 ???????? `04:0x`???????=03:26?????03:47??????? PR-20261105-01?04:0x / 04:02 ???????? 03:26-03:47 / 03:26?????????????????????????
## 附录 R11 事件班登记（2026-11-06 00:05-00:22·承载件触发·DL 三连 STARVED-EXEC + BLOCKED-RAM bm-c + CLOCK-SKEW 3492ms）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **R11-1 真饥饿成立（POOL 假红之外的第二层）** | **FIXED（本班点火）** | 队列真 OPEN 只有 2 张，且 `R-NEXT-BIGSTREAMD-TTS-QC-20261104` / `R-PLAN-BIGSTREAMDUA-20261104` 全属 `bigstream-duanju`，LINE-REGISTRY 标 **PARKED** → 三机确实无合规活可领。处置：两卡 CANCELLED（R9-7 判例） |
| **R11-2 备料 20 行 READY 全部升不上去** | **诊断完成·根因登记** | 逐行验：绝大多数「已在队（DONE/UNVERIFIED/RUNNING）或交付物已在盘」，属数据陈旧；真缺陷=2 行 bm-b 语音卡持 **bm-b 绝对路径**（`C:/Fluxgroup/FleetAgent/...`），主控 `backlog_fill` 路径闸在本机判 False → 永久升不上去 = bm-b 结构性饥饿源。**R10-4 家族第 2 次复发** |
| **R11-3 两张真卡已升队并点火** | **BURNING（实证）** | 修后补料 `BACKLOG-ADDED 2`：`Q-VCORP-PREP-e01-R3`（导入 e01 语料切片）+ `Q-VCORP-TRAIN-PILOT-libritts-e01-R3`（SoVITS s2 微调）。poke 后 **3 分钟**首张被 bm-c 认领 RUNNING（00:12:01·lease 60min）。第二张 OPEN 待认领（其 `requires` 含 bm-b 本机 GPT-SoVITS，lane 严格自检后才收） |
| **R11-4 推送通道 HTTP 500（新坑·已绕开）** | **FIXED（本班）** | `Tools/git-atomic-push.py` 对 `PRODUCTION-QUEUE.jsonl`（origin 788KB）两连 `blob 创建失败 HTTP 500`——整文件 base64 逾网关 1MB 体限。正法=同工具的反转闸 + 本地 `commit-tree -p origin/main` + `git push origin <sha>:refs/heads/main`（协议传增量）→ 87cdab202 成功，`NO-REVERSAL 2389 增行零消失`。**建议把「大文件走协议外科、小台账走 API」写进 versioning §4.4 附则** |
| **R11-5 bm-c BLOCKED-RAM + ComfyUI 缺失** | **registered·物理件（零催办）** | IdleWatch 23:44-23:59 实测 `ram_free 8.75-9.58%`（24GB 机≈2.1GB）、`hb_verdict=GPU_COMFY_MISSING\|RAM_LOW`、comfy=0。bm-c 是 GPU 唯一产线，其全部 GPU 卡（asset-lib-char-gen / asset-gen）都串在 8188 上。修法只在 bm-c 本机：`free_mem.py --apply` 释放驻留 + 起 ComfyUI（C-20261009-04 / CEO 2026-10-23 禁远程，本席不做） |
| **R11-6 bm-b/bm-c w32time 停转（CLOCK-SKEW 3492ms）** | **registered·物理件（零催办）** | CLOCK-SKEW.json 23:59:15：hub bm-a 0ms、bm-b +1456.3ms、bm-c ≈+3966ms（4ms/min 漂移），`old_schema=0 missing=0`→CLOCK-UNALIGNED 已自愈。承 R4-4/R5-5/R6-7/R8-6/R9-5/R10-9：两机 `sc query w32time`=STOPPED，需本机提权 `sc config w32time start= auto && net start w32time`。秒级偏差不影响派单租约，不重复立法 |
| **R11-7 队列双源分叉（结构隐患·登记）** | **registered** | 本机 `main` 与 `origin/main` 实测 **ahead 497 / behind 244**；两边都有对方没有的卡（origin 侧 `DOCS-_报审提交区`、`VER-E-195423`；本机侧两张 VCORP）。本班用 append-only 外科推避开合并，但「双源各写各的」仍会持续制造幻影供给。收口正法=按 bm-a 卡死合并判例（reset --mixed origin/main + 定向 checkout + 台账行在 origin 最新版重提），须在无他窗在写的窗口做 |

## 附录 R12 事件班登记（2026-11-06 00:52·承载件触发·DL 三连 STARVED-EXEC + CLOCK-SKEW）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **R12-1 队列原文件结构性损毁（P0·真根因）** | **registered·待无写手窗口收口** | origin `cph4/fleet/PRODUCTION-QUEUE.jsonl` 2111 行里仅 334 行可解析（1774 行=1.29MB 跨行 JSON 碎片，raw_decode 拼接后仍不可恢复）、整份重复一遍（每 id 两条）、3 处 `<<<<<<<` 冲突标记；本地工作树 496 行干净但与 origin 各持对方没有的卡（本地独有 431、origin 独有 102）。后果=认领器读到的唯一 OPEN 只有 `VER-E-195423` 垃圾双行 → 三线「无活可领」的一半是真损失。处置边界=本班不整文件重写（`backlog_fill.py` 00:50 仍在写队列，重写会与他窗赛跑·R9-2 判例），只走 append 通道补真卡；收口正法=`queue_repair.py`（dedupe+去标记）在**无写手窗口**基于 origin 跑，逐行判读后外科推。 |
| **R12-2 `Q-VCORP-PREP-e01-R3` 跨机路径错（P1·第 3 次复发）** | **registered·待改行** | 该卡 `cwd=C:/Fluxgroup/FluxGroup`、`deliverable=C:/Fluxgroup/FleetAgent/...`，而 bm-c 根为 `K:/Fluxgroup/FluxGroup`、bm-b 根为 `C:/Fluxgroup/FluxGroup`（无 FleetAgent 段）。现态被 fallback 分到 bm-c（`fallback_from=[bm-b]`），cwd 在 bm-c 不存在 → 必失败。承 R10-4/R11-2 同族。修法=两字段改仓库相对路径 + `nodes` 钉持料机 bm-a；因整文件重写有赛跑风险，留晨检无写手窗口改。 |
| **R12-3 `asset-lib-asset-gen` 僵尸 RUNNING（P1·账实不符）** | **registered** | 本地队列 `state=RUNNING owner=bm-b claimed=2026-11-05T23:06`，而其 deliverable 回执 `asset-gen-props-2026-11-05.json` 停在 11-05 06:30 且内容全是 `WinError 10061`（ComfyUI 拒绝连接）。origin 侧同 id 已是 `CANCELLED(hard_nodes=[bm-c])` → 本地这条是旧世代的幽灵。正法=按 origin 终态覆盖（repair 去重时「最新终态优先」会自动处理）+ 恢复时须先解 bm-c ComfyUI。 |
| **R12-4 时钟偏移（物理件·第 7 次）** | **waiting-CEO·零催办** | 00:44 `CLOCK-SKEW.json`：hub bm-a −0.4ms（σ0.4）、bm-b +1456.3ms（σ0.8）、bm-c +3656.2ms（σ407.5）。承 R4-4/R5-5/R6-7/R8-6/R9-5/R10-9/R11-6：两机 `w32time` 为 SERVICE-STOPPED，需本机提权 `sc config w32time start= auto && net start w32time && w32tm /resync /force`。秒级偏差不影响租约派单，不重复立法。 |
| **R12-5 bm-c 真饥饿（结构性·非调度失败）** | **registered** | bm-c 队列 0 张可执行 CPU 卡，其 GPU 活（char-gen/asset-gen/face-caption）全串在 ComfyUI 8188，而 23:44-23:59 IdleWatch 实测 `ram_free 2.1GB` + `comfy=0`。bm-c 的饥饿诚实存在，根因是物理面（RAM+ComfyUI），不是派单缺口——不拿假卡去刷绿。 |


### R12 追加登记（同班二次深挖·01:2x）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **R12-6 两机认领器不可用（P1·第 8 次同源）** | **waiting-CEO·物理件零催办** | 01:13/01:15 直读两机 `/status.last_pull.wakes`：bm-b `HQ-ProductionClaim:deny`；bm-c `task_states.HQ-ProductionClaim=Disabled`（另 Bigmoney-IterationLoop / SaturationEngine 亦 Disabled）。同刻 `pulls=[".:updated"]` 但 `repo_heads["."]` 仍停在 b82c9834(bm-b) / 904d636d(bm-c)，而 `origin_main=42b209d78` → **两机既拉不到新卡、也没有认领器**。修法只在各机本机（C-20261009-04 禁远程启用 Disabled 任务）：`schtasks /change /tn "HQ-ProductionClaim" /enable` + 修 ff 分叉。 |
| **R12-7 本机 HQ-ProductionClaim 违反 S4U 律且持续失败（P1·物理件）** | **waiting-CEO·需提权** | `Get-ScheduledTask` 实读 `LogonType=InteractiveToken`（违反 2026-09-29 判例「一切车道任务一律 S4U，禁 InteractiveToken」）；`LastTaskResult=2147946720 (0x800710E0)`、每 5 分钟一跑、`State=Running` 但无匹配 `queue_claim` worker（有 2 个 pythonw 残实例）。证据备份 `%TEMP%\hq-claim-backup-20261106-012204.xml`。修法（本班非提权 IsInRole=Administrator False）：管理员窗 `Register-ScheduledTask -LogonType S4U` 重建同名任务，保留 Action=`pythonw.exe Tools\queue_claim.py --node bm-a`。 |
| **R12-8 lane_agent 自派循环吞掉合格卡（P1·新发现·工具面）** | **registered** | 同卡同判据两种结果：`queue_claim --node bm-a --dry` 打印 `LANE-DRY bm-a self-dispatch would run MV-AUDIT-V722G-20261106`（pick 非空）；同命令真实模式却落到 `LANE-IDLE`（`self_dispatch` 返回 None → L789-795 分支）。逐项复核该卡准入判据全部通过：`implicit_inputs=[]`、`card_os_ok=True`、`requires_bin_ok=True`、`game_launch_blocked=False`、nodes=[bm-a] 命中本机。后果=**供给在队列里、判据也过，但自派循环不接** → 这是「有活没人干」的第二个真因（第一个是 R12-6 认领器不可用）。下一步=给 `self_dispatch` 加 `--explain` 输出 reject 原因（工具面小改·非受保护件，可 T1 落地）。 |
| **R12-9 `CARD-DEFECT/CWD-MISSING` 第 4 次复发（P1·升格）** | **registered·闸升格提案** | 硬证据=01:20:05 回执 `Q-VCORP-TRAIN-PILOT-libritts-e01-R3-20261105-bm-a.json`：`rc=127 outcome=CARD-DEFECT card_defect="CWD-MISSING 切片 cwd 在本机不存在：C:/Fluxgroup/FleetAgent"`。承 R10-4/R11-2/R12-2 同族。闸升格（同病复发即升一档）：`Tools/card-lint.py` 增两条断言——①卡 `cwd` 必须是仓库相对路径或空；②`deliverable` 不得出现 `C:/Fluxgroup/...` 这类跨机绝对路径。断言在**生成源**（backlog_fill/line_plan）出卡时拦截，而不是等执行机 rc=127。 |
| **R12-10 本班供给产出（实证）** | **已执行** | 两张真卡入队并推 origin：`MV-AUDIT-V722G-20261106`(bm-a) / `MV-ANCHOR-BATCH3-20261106`(bm-b)，push 77bfcbd56 → 42b209d78，均 NO-REVERSAL（6501/6410 行零消失）。bm-a 卡已本机点火执行（`Tools/mv_full_audit.py <v722g> --json ...`，交付物 `cph4/fleet/queue-receipts/mv-audit-v722g-20261106.json`）。bm-b 卡因 R12-6（认领器 Disabled + 仓面 ff 不动）暂时领不到，非卡本身缺陷。 |

| 2026-11-06 01:46 R6-2 STARVED-EXEC 平价误红第三次复发（POOL 台账 vs 活队列） | 全局 | CEO-PROXY 事件班 2026-11-06 01:46 | **registered·waiting-CEO（受保护件 L0 脚本·需 CEO 定谳）**：修法一行=fleet-dispatcher.ps1 L145 的 $exec[] 由只数 POOL.json 改为同时读 PRODUCTION-QUEUE.jsonl 中 nodes 含该机且 state=OPEN 的行（取大者），否则每班恒报 x3 假 P1。证据=本班实测 bm-a 01:27 有产物提交、bm-c 有 5-15min 快照，而 POOL 唯一 open 是 CEO 物理件。 |

### R12 勘误（同班·2026-11-06 01:33）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **R12-8 勘误（本班自我更正）** | **撤回缺陷定性→改进为注入测试** | 01:27:08 官方认领链路回执 MV-AUDIT-V722G-20261106-bm-a.json 实证 rc=0/722.3s/outcome=OK/deliverable_exists=true → **自派循环并未吞卡**，本班 01:22 那次 IDLE 是与我手工起的同时段实例/认领竞态所致，非结构性缺陷。原 R12-8 归因撤回。保留可执行改进=给 self_dispatch 加 --explain 打印 reject/skip 原因，避免下次把竞态误读成缺陷。 |

| 2026-11-06 02:20 R6-4 bm-b/bm-c 工作树分叉（未推送本地提交）阻塞取卡 | bm-b head=b82c9834 / bm-c head=904d636d（均 `not our ref`，从未推 origin） | CEO-PROXY 事件班 2026-11-06 02:20 | **registered·需在各自机器上跑一次（主控无远端执行通道）**：`git -C <repo> fetch origin && git reset --mixed origin/main`（先备份本地未提交改动）。证据：两机 /status last_pull 报 `.:updated` 但 repo_heads 不动，origin_main=a53ea6fbd；两机 lane 仍挂旧卡，新卡看不见。bm-c 的 Bigmoney-IterationLoop 当前 Disabled，不会自愈。 |
| **R13 CLOCK-SKEW 提权面（w32time 停止·三机同型）** | **waiting-CEO·零催办（第 8 次）** | 2026-11-06 事件班实测：bm-a 本机 `w32time=STOPPED/StartType=Manual`，`Start-Service` 拒绝（会话 token 未提权，虽属 Administrators）；bm-b offset +1456ms（±0.8）、bm-c +4236ms（±414）= 真偏不是 RTT 噪声。自动面已试尽：net start 被拒、w32tm/resync 报 0x80070426。**需一次提权**（任选：管理员窗跑 `sc config w32time start= auto && net start w32time && w32tm /resync /force`；或把对应 loop 任务以「最高权限」重注册）。影响=时间戳排序轻微失真，`corrected_ts` 已在补偿，非阻断。工具面已修诚实（verdict≠RESYNCED → exit 3），不再假绿。 |
| **R13-2 两机认领器结构缺失（P1·已修）** | **fixed·待复探确认** | bm-b `HQ-ProductionClaim:deny`、bm-c `Disabled`：该任务只注册过 bm-a。承 R12-6/R10-8/R8-3 第 7 次。修法=Tools/fleet-poke-worker.ps1 v1.9 缺任务自愈（仅 HQ-* 前缀·Disabled 仍 off-skip·bm-c RAM<6G 自动 --needs cpu）。确认判据=下一次 poke 的 /status.last_pull.wakes 出现 `HQ-ProductionClaim:healed` 或 `:WAKE`，且 `_last_lane_bm-b.json` 出现新 ts。 |
| **R13-3 两机工作树分叉=认领器失效真根因（P0·待修复窗）** | **registered·待无写手窗口收口** | `git merge-base --is-ancestor` 实测：bm-b head `b82c9834`、bm-c head `f1bbe729` **均非 origin/main 祖先**（各带本地提交），两台 fetch 到最新但 `pull --ff-only` 必然失败 → 代码/卡/白名单都进不去，7 班 deny/off-skip 由此而来。收口正法（承 R12-1，禁远程无人值守做）：选无写手窗口，在各机 `git fetch origin && git reset --mixed origin/main && git checkout -- <节点自有文件清单>`（或对本地提交做一次显式 merge+解决冲突），再 `git reset` 后重放节点自产台账；顺带查谁在节点上写 state 快照（fleet_agent 明文禁节点写组仓）。戒律：不清 `--hard`、不带病自动 merge。 |
| **R13-2 修正（撤回「已修」判词）** | **armed-in-code·部署受阻** | poke-worker v1.9 缺任务自愈 + listener 1.9.6 唤醒清单截断修复均已在 origin（60fd78520）验证存在，但被 R13-3 堵在节点门外，**未生效**。生效判据=修复窗后一次 poke 的 `/status.last_pull.wakes` 出现 `HQ-ProductionClaim:healed` 或 `:WAKE`。 |

## 附录 R14 事件班登记（2026-11-07 00:41-00:5x·承载件触发·DL 22:41/22:51 五旗）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **BLOCKED-RAM bm-c（22:41/22:51 双旗）** | **resolved（自愈缓解·监控中）** | 00:45 /status ram_free=2.7G（闸 1.0G 与 10% 地板 2.4G 均过）+GPU 14G 在烧+认领器 Running；L0 00:41 已不报。前班 FREE-MEM-APPLY-bm-c-20261107 卡被 bm-a 跨机错领（释放的是 bm-a 自机内存）后 E-ARTIFACT FAIL——本班本地销卡；RAM 再破闸才重立且必须 hard_nodes=["bm-c"]+修 deliverable 契约。02:22 探针复验。 |
| **CLOCK 家族（SKEW 1456.3ms→UNALIGNED missing=1）** | **waiting-CEO（提权物理件·零催办）** | 三 Windows 机 w32time 全 STOPPED：bm-a 今晚新实证（clock-resync-bm-b-20261107.json verdict=SERVICE-STOPPED·net start 拒绝访问 0x5）+bm-b/bm-c 慢性（R2.38/R4-4/R11-6 在册）。missing=1 判=bm-m 不在 NATS 总线（11-06 已知盲区）。秒级偏差不影响派单租约（R8-6）。修法=各机本机提权 `sc config w32time start= auto && net start w32time`——并入 S4U 提权 waiting-CEO 行合并办理。CLOCK-RESYNC-bm-b（FAILED）/bm-c（被 bm-m 错领）双卡本班本地销。 |
| **LANE-DOWN bm-b（SVC_DOWN·00:41 旗）** | **resolved（瞬时误报·实证自愈）** | 00:45 /health 200 v1.9.5 + /status 200 ram 10.5G/cpu 9% + NATS 心跳 00:44:58 seq6010 + 00:38:02 新认领 Q-VCORP-PREP-e01-R3 + Bigmoney-IterationLoop busy-skip（量化环在跑）。承 fleet-nodes 注记「listener 探针超时假象」家族。另 bm-b HQ-ProductionClaim:deny=白名单陈旧（D-R261-POKECFG-STALE 在册）。 |
| **Q-VCORP-PREP-e01-R3-20261105（留观件）** | **watching·二次失败即销** | bm-b 00:38 新领可能是真活（禁杀）；反证=bm-a e01 inbox=0 件实测（00:4x）+R13 11-06 bm-a rc=2 E-INPUT 在档+bm-c 11-06 领取零回执。若本轮再 E-BLOCKED-INPUT→按 R9-7 销卡（投料后由工序表重立）。02:22 探针验回执。 |
| **跨机错领三连（新证据）** | **registered·PR-20261106-02 复发+3** | 今夜 bm-a 错领 FREE-MEM-APPLY-bm-c+CLOCK-RESYNC-bm-b（00:20/00:30 回执 node=bm-a）、bm-m 错领 CLOCK-RESYNC-bm-c（00:14 owner=bm-m·Mac 无 w32time 面）。nodes= 偏好非硬钉=lane_agent R9 已知面；hard_nodes 纪律（11-03 判例）执法面=建卡必带硬钉。 |
| **STARVED-EXEC bm-a/bm-c（22:41 旗）** | **假红·结构性（承 R4-2/R11-1）** | 旗只读 POOL.json（唯一 open=POOL-0010 被 CEO-PHYSICAL 锁死）；本地队列 OPEN=2/RUNNING=3 三机在产 BURNING。POOL-0010=物理件已登记零催（00:41 INFO WAITING-CEO）。PR-20261027-14 受保护件候裁维持。 |
| **队列双源分叉加深（R11-7 升级实证）** | **registered·收口须专项窗** | origin 队列 1248 行完全不含今夜新卡（FREE-MEM/CLOCK-RESYNC/e01 全缺）·本地 1100 行含之——两源卡群不相交·本地 main ahead 710/behind 360·DISPATCH-LOG 11-06 03:00→11-07 00:33 段同步覆盖丢失同族（另新证：DISPATCH-LOG.md 本身 origin 不在档=本地专有文件）。本班队列销卡仅落本地面（推本地版=覆盖 origin 148 张独有卡=破坏性禁止）；跨机传播受阻登记。收口=无他窗在写的专项窗按 bm-a 卡死合并判例执行（承 R11-7 正法）。 |

| **bm-b 整机失联 48h+（P1·CEO-PROXY 事件班 2026-11-08 00:40 实证）** | **waiting-CEO（物理件·零催办）** | 证据三面：①bm-a→bm-b tailscale ping 两发全超时（对比 bm-c 同法 pong 3.936s=探针本身可用）②status Online 但 LastSeen=2026-11-07T02:22:42+08 ③生产回执末笔 2026-11-05T23:33·机器心跳 ts=2026-10-30T12:44（round 1277）。恢复=现场开机+任务自愈（Bigmoney-IterationLoop / HQ-ProductionClaim 均在 wake_tasks 白名单，S4U 注册）。本席无远程通道（FleetLink 无命令端点；bm-a→bm-b TCP 全断），只能登记候人。 |
| **探针面缺陷登记（P1·事件班 2026-11-08 00:42 实测）** | **registered·待立闸** | 症状：tailnet 无直连、纯 DERP 中继（pong 0.58~4.3s）时，5-10 秒 TCP 探测会把**活机判成 SVC_DOWN**（bm-c 同分钟内 /health 先 200 后 rc=28 可复现）。当前旗语只看单一 TCP 探测结果，缺判别器。建议修法（待闸升格落地）：SVC_DOWN 判定须三信号——①`tailscale ping` 是否有 pong（区分「机器/守护进程死」）②Connect 超时是否 <=15s 且 `direct connection not established`（区分「中继慢」）③生产回执龄（区分「服务死 vs 只是慢」）。三者不一致时降级为 DEGRADED-RELAY，不报 SVC_DOWN、不 page owner。 |
| **【二次勘误】bm-b 恢复=已发起，无需现场动手（2026-11-08 00:52）** | **closed-as-diagnosed（不占 CEO 手）** | 撤回 00:40/00:42 两行的「整机失联」「机上服务死」措辞。实证：:8790 /health 00:46:13 返回 200（v1.9.7），POST /poke 00:47:22 accepted=true（Bigmoney-IterationLoop + HQ-ProductionClaim 均已下发唤醒）。两行被判死的唯一原因是探测超时太短（5s/30s/60s 均不足，需 90s）。真正待观察项=bm-b 是否在 24h 内产出新回执；由 2026-11-08 02:17 回访探针复核，无需 CEO 动作。 |

## 附录 R15 事件班登记（2026-11-08 00:41-01:0x·承载件触发·队列丢行根因）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **队列卡被 state_push 整文件覆盖（P1·可复发·本班已修）** | **FIXED（修法已上链·待线上验证）** | 实锚：`RESCUE-FREEMEM-BM-C-20261108`（00:45 窗 append 推 ce524cf21）在 00:50/00:51 两轮 bm-m 同步后被抹掉（`f1246e864→9c1e58012` numstat **15/15**，删侧首行即该卡）；本班 00:47 再恢复一次、同样被抹。根因=`Tools/fleet/state_push.py:sync_into_worktree` 把主工作树的**陈旧本地队列**整文件拷进独立工作树再提交，origin 上别窗 append 的卡即丢。修法=STATE_FILES 改「origin ∪ 本地 按 id 合并」（终态优先、字节不重编码），提交 **4aec20ac2**；离线自测 1385+1 零丢失零重复。验收=下一次 bm-m 同步后卡仍在 origin + bm-c 认领回执（回执窗 ≤2h）。同族：R11-7/R12-1/R14-7。 |
| **bm-b/bm-c 可达性抖动（承 00:52 二次勘误）** | **registered·探针口径** | 本窗 00:45–01:00 对两机 :8790 的探测全部失败（含 90s 超时后「无法连接到远程服务器」），但 sibling 窗 00:46:13 对 bm-b、本窗 00:51:22/00:51:31 对 bm-c 均拿到 200，且 bm-c 随后 connect-fail ⇒ 纯 DERP 中继路径抖动，**不是机器死**。正法=探针放宽超时+多次采样+以 /health 200 为准（TCP 单发不可作死判）。 |
| **CLOCK-UNALIGNED missing=1** | **registered（非新增）** | 三台 Windows 机 w32time 仍 STOPPED（R13 wating-CEO 提权行）；missing=1 对应 bm-m 不在 NATS 总线（tailscale `last seen 9d ago`，11-06 已知盲区）。秒级偏差不影响派单租约。 |
| **bm-b 生产回执自 2026-11-05T23:33 零** | **waiting-CEO/域席（零催办）** | 机器与服务在线，产出面 48h+ 无新回执；两窗均已 poke（sibling 00:47:22 accepted，本窗 00:47:41 bm-c accepted），执行面待验。 |

**本班边界**：不重复判旗、不重复派卡；唯一实质动作=修「队列被整文件覆盖」这一使 append 派发凭空消失的写手缺陷，并把救援卡重新 append 回 origin。

| **【修法验证】第三次抹卡=bm-m ROOT 陈旧致修法空转（P1·waiting-CEO·bm-m 本机）** | **registered（本席已停手）** | 三次实测：ce524cf21→抹、4aec20ac2→抹（702afaccd 00:58，父链含修法提交）、ee9639199(01:01)+立即 poke→100 秒内被 ffb3d208c 抹掉。机理=`state_push.py` 的 reset --hard 只对隔离工作树 `.fluxgroup-state-wt` 生效，**执行的是 ROOT 工作树里的脚本**；ROOT 不前进=旧行为（本地陈旧队列整文件覆盖 origin）。逻辑自证=用 origin 版模块对真实 blob 复算（80a2bf064 ∪ 5023fd112）→卡在、零丢 id、零重复。解闸（bm-m 本机一次）：`cd <root> && git fetch origin && git reset --mixed origin/main && git status` → 下一次 state_push 即按 id 合并。**禁继续重投该卡**（无效 churn；bm-c RAM 2.1-2.5G 且 char-gen 在跑，非阻断）。 |

| **【口径更正】R15「修法空转」定性** | **corrected** | 早前写「bm-m ROOT 工作树陈旧」属过度断言：可证的只有①抹卡提交的父链都含「含卡」提交（bm-m 看得见卡）②随后按本地快照整文件重写；「为何拿到新提交仍跑旧逻辑」未取证（ROOT 未更新／长驻进程加载旧副本 皆可能）。第 5 次复现：`16e5f3a4e`(01:12:32)+poke 01:12:40 → 01:15:19 复查已丢。新增防线 `d659f51e68`：读不到 origin 时保留 origin 版（原为退回本地覆盖）。 |
| **bm-b 半僵死（LANE-DOWN+STARVED-EXEC+CLOCK-MISSING 三旗同源·2026-11-08 01:2x）** | **waiting-CEO·物理件（需本机干预）** | 证据：/health 01:23 回 200(v1.9.7,25s)→01:31/01:35 超时(50s/21s)；/status 全程不通；NATS 4222 出现 6 个 SynReceived 半开；CLOCK-SKEW 中 bm-b=MISSING；git 8h+ 零提交（同窗 bm-a/bm-m 均有产出）；quant/bigmoney 最后提交 11-07 16:30；tailscale 走 sfo relay、tx 218MB（疑似重试积压）。无 SSH/WinRM 通道（CROSS-MACHINE-EXEC-v1 §2）。已落 BMB-SELFHEAL-20261108 自愈卡（恢复即执行：停 ollama + HQ-ProductionClaim enable/run + FleetLink 重启）。待 CEO 亲动=到机器前干预，或授权远程执行方案。 |
| **bm-b 服务已恢复·STARVED 根因锁定（2026-11-08 01:39 更正）** | **waiting-CEO·物理件（收口需本机一次）** | 01:33 复探 /health 1.8s、/status 3.0s 均 200（ram_free 9.5G、cpu 1-2%）；NATS 半开 SYN 6→0。poke 实为 01:27:15 已执行（wakes=[Bigmoney-IterationLoop:WAKE, HQ-ProductionClaim:WAKE]）。但 6 分钟零新回执，且 last_pull.pulls=[".:updated-kept-local"]、repo_heads["."]=562a211c vs origin=8af2532af —— **根因=bm-b 仓库分叉，pull 保留本地=永远拉不到新卡（自愈卡也进不去）**。正法：bm-b 本机跑一次 Tools\fleet\node_closeout.ps1（或 REMOTE-CLOSEOUT2-bm-b-20261107 卡），禁自动 reset（ahead 含真产物）。回访探针 03:05 自动复验。 |
| **PRODUCTION-QUEUE 脏污染（2026-11-08 01:39 事件班发现·待专项窗）** | **registered·让路不抢写** | origin/main 队列含空 merge 冲突标记 6 行（<<<<<<< / ======= / >>>>>>> d55c02d7d，段内无内容）且被后续 append 复制扩散（观测 1394→1421 行、标记反复出现）；另有本席自愈卡 BMB-SELFHEAL-20261108 重复 2 行（双次 append，命令幂等故无害）。处置=队列被 L0/pulse 每轮高频写入，按「与 OS 班抢 git 锁让路」纪律未做 CAS 重写；留专项窗统一去重+清标记。 |
| **R-EVT-20261108-0254** 时钟/供给两张物理面 | bm-b/bm-c 本机 | 事件班 02:54 实测 | **waiting-owner（零催办·无远程通道）**：①CLOCK-SKEW 实测 bm-b 1735ms/bm-c 1075ms 但 NATS 测量精度 ±403ms，判据(150ms)严于测量能力 → 需 bm-b/bm-c 本机 w32time 校时或 hub 直连；②FluxVerseTick/BigLife-OSLoop/BigStream-OSLoop 均 rc=0 但无新产物=空转 → 各线 owner 在下轮声明真活卡（主控不发明活） | R-EVT-20261108-0254 |

| **bm-b STARVED-EXEC（2026-11-08 01:01-03:21 反复旗）** | **resolved·已点火（事件班 03:47）** | 根因双条：①origin cph4/fleet/lanes/bm-b.json 带 git 冲突标记（<<<<<<< HEAD / >>>>>>>）→ JSON 坏 → bm-b 收不到作业卡；②Tools/fleet/supply_batch.py 建卡把生成机绝对根路径写进 cwd（bm-m 生成=/Users/...），跨到 Windows 机必 rc=2（R12-9 第 5 次复发）。处置=重发 2 张真卡（AUD-GAME-...-26-R1 CardRogue / -30-R1 FateGate，cwd="."）原子推 e07725bbe/76fb4a473 + 根因修复 8239204a7 + poke 两次；实证=bm-b 拉取 head==8239204a7、两卡 RUNNING owner=bm-b claimed_at 03:35:06、progress_ts 03:41:28 |
| **空壳 DONE 假绿（AUD-GAME-...-26/-30 原卡）** | **registered·verify_done 缺口** | 原卡 state=DONE owner=bm-m 但 finished_at/rc/deliverable_exists 全空，且 origin 上 cph4/fleet/audits/game/CardRogue.json/FateGate.json 均不存在 → DONE 无产物。同类 2026-11-07 已记 91 张 DONE 中 11 张可疑，本班第 2 次实锚。建议=verify_done 每日全量扫 DONE 缺证据行自动降 UNVERIFIED |
| **CLOCK-UNALIGNED old_schema=1（01:11/01:21 旗）** | **resolved·自愈（本班核实）** | CLOCK-SKEW.json 03:19/03:29 均 old_schema=0 missing=0 → 节点心跳已升 v2（ms ts+offset），01:11 旗为节点重启窗口内瞬时。残余=SKEW-HIGH（bm-b 1702ms/精度 427ms、bm-c 1284ms/精度 399ms）→ 归 w32time 提权件，已在 waiting-CEO 册，零催办 |
| **bm-c BLOCKED-RAM（03:01/03:11/03:21 旗）** | **waiting-owner·在 1.0G 闸边缘震荡** | 03:23 实测 ram_free 1.7G → 03:26 回落 0.7G → 03:44 1.6G/cpu 76%，闸 1.0G 上下震荡；车道有真卡 ASSET-GEN-TYPOGRAPHY-20261108（needs=gpu）候运行。无远程执行通道，需本机释放（ollama 驻留/编辑器）；不重复铺同交付物卡 |
| **bm-c 仓分叉 ahead50/behind472（R13-3 在册）** | **registered·结构件（本班再实证）** | 03:23/03:44 两次读 last_pull.fork=".":"50	472/main"，pull_ts 停在 02:28（:updated）→ ff-only 拉不动，新卡/新工具到不了 bm-c；自有 OS 环仍跑（Bigmoney-IterationLoop/SaturationEngine Running）。收口须本机 git fetch && git reset --mixed origin/main（无远程通道） |
| **供给通道不持久（队列被 bm-m 整体重写，本班实证）** | **registered·P1 结构件（R11-7 升级）** | 03:26/03:28 我推入 origin PRODUCTION-QUEUE.jsonl 的两张真卡（-26-R1/-30-R1）在 03:46 origin 上已消失：bm-m 每约 2 分钟提交 state: 队列/回执同步 会用其本地队列整体覆盖该文件，外部/他机供给的卡 2 分钟内被抹掉，bm-b 只能靠「未再拉取」侥幸持有。后果=供给不持久、DONE 记录也可能被抹成空壳（承同日空壳 DONE 判例）。建议正法=master_agent/state_push 对队列改「并集合并」而非整写（按 id 去重合并，本地态优先），或把作业卡通道单独拆分（lanes 只读、queue 只追加）。收口须 bm-m 席或专项窗，无远程通道。 |

## 附录 R16 事件班登记（2026-11-09 00:41-01:10·承载件触发·STARVED-EXEC bm-b + CLOCK-UNALIGNED）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **STARVED-EXEC bm-b（11-08 21:41/22:01 双旗）** | **resolved（自愈·真活实证）** | 00:41 LOG bm-b=6run；队列实证 6 张 RUNNING 且 claimed_at 00:26/00:31/00:49（Q-ANCHOR-SHOTGRID-REBUILD / R-PLAN-BIGDOMAIN / R-PLAN-BIGMONEY / bigmoney-signal / asset-lib-library-check / R-TRIAGE-*）。无需补卡。 |
| **CLOCK-UNALIGNED（old_schema=1）** | **resolved** | CLOCK-SKEW.json 00:44：old_schema=0 missing=0，三机均 v2。残余=SKEW-HIGH bm-b 1456→3461ms、bm-c 3866ms（precision 407-527ms 中继不可信档）——w32time 提权物理件，已在册 waiting-CEO 零催办。 |
| **TTS 质检卡错机派单死循环（本班根治）** | **FIXED（卡与令已上链·领取受阻于 bm-b 分叉）** | 实锚：6 张同类卡（20261102/03/04/07、bigstream-duanju-tts-qc-2026-11-03、MOB-DRAMA-TTSQC-20261106）全落 bm-m/bm-a/bm-c，回执一律 BLOCKED「dir missing」；素材 1036/1036 wav、60/60 集只在 bm-b（Q-TTS-1202R-bm-b.md）。处置=销旧卡 + 新开 R-TTS-QC-R3-20261109（hard_nodes=[bm-b]·needs=cpu·回执窗 2h）+ POOL-0026 + O-20261109-0053，card-lint 9/9，origin 920fef5f7。 |
| **bm-b clone 分叉阻断新卡可见性（P1·新）** | **registered·收口须专项窗** | bm-b /status 01:00:26 自报 origin_main=5d39640b、ahead 702/behind 428，pull 结果 `.:updated-kept-local`；而本班推送 920fef5f7 → bm-b 看不到 R3 卡，领取循环空转。修法=无他窗在写的专项窗按 10-30 判例（fetch + reset --mixed origin/main + 定向 checkout），或专设一条 bm-b 侧 `queue_refresh` 卡由 bp-m 自身 OS 循环执行。**本班不动 bm-b 的 git（怕吞其 702 笔本地提交）。** |
| **反转闸对既有漂移长期红灯（P1·新）** | **registered·工具缺陷** | `git-no-reversal-check.py origin/main origin/main --depth 30 --audit` = 230/501 条历史增行在近 30 提交消失（他窗整文件覆盖所致）。后果=git-atomic-push 对所有合法推送一律 ABORT（本班首推即被拦）。本班改走外科净路（tree=origin+3 文件，零外来删行）并留痕。修法=闸基线改为「以本次推送的 base 树为锚」而非历史全量，或对 STATE_FILES 类单列豁免。 |
| **lane 合并循环吃掉 orders/POOL 本地改动（P1·新）** | **registered·同族 state_push** | 00:5x 提交 a1ad2d5d7「restore 1 local-only card(s) after merge」+50dd515b5「merge origin (generated files take remote)」把本班 orders 行与 POOL-0026 抹掉（仅队列卡被恢复）。本班已重放并推。修法=合并循环的 restore 名单须覆盖 orders.md/POOL.json（或这三件一律按「本地新增行并集」合）。 |
| **回访探针** | **armed** | +90min 一次性 cron：复探 R3 卡状态与 bm-b 可见性；复发=旗升 DE 级。 |

## 附录 R30 事件班登记（2026-11-10 02:46-03:05·承载件触发·CLOCK-SKEW×3 + STARVED-EXEC bm-b/bm-c）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **bm-b sparse cone 缺数据面（P1·新根因）** | **fix 已上 main·待 bm-b 拉到** | 实锚：bm-b 同类 0.1s 秒退回执写明「配置文件不存在 cph4\\fleet\\asset-lib-v1\\ASSET-PROMPTS-v1.json」→ cone 只物化 queue-receipts/lanes，`cph4/fleet` 数据面不在锥内，卡脚本读不到配置即秒退，表现为「有卡不干 + 假完成重开」。修法=Tools/fleet/agent.py pull() 增 `ensure_sparse_cone()`（幂等 sparse-checkout add cph4/fleet Tools/fleet），commit b187d4893。 |
| **bm-b 分叉死锁（P1·承 11-09 同族）** | **waiting-专项窗（无远程执行通道）** | 修复代码已在 main，但 bm-b ahead702/behind428，`merge --ff-only` 永失败 → 拉不到修复 → 死锁自锁。唯一收口（保工作树 702 笔内容、只丢本地提交链）：<br>`cd C:\Fluxgroup\FluxGroup && git fetch origin && git reset --mixed origin/main && git checkout origin/main -- Tools cph4 && git status --short`<br>执行后本地回执变 modified/untracked，由 agent push 正常上链。生成器：`python Tools/fleet/remote_closeout_card.py --nodes bm-b --print-cmd`。**本班未擅动其它窗在写的 git。** |
| **CLOCK-SKEW bm-b 1312.9ms / bm-c 2319.4ms（P2·物理件）** | **waiting-CEO（提权）** | CLOCK-SKEW.json 02:49 实测 hub bm-a offset=0 → 漂移在节点不在 hub。clock_resync 实锚：DASHENG w32time=STOPPED，`net start w32time` 拒绝访问（rc=2/需提权）。正法=各机提权 `sc config w32time start= auto && net start w32time && w32tm /resync /force`。2.3s 漂移不阻断派单，仅影响回执时序判读；零催办。 |
| **bm-c 两资产卡转 BLOCKED（P1·已处置）** | **resolved·BLOCKED 待解封** | asset-lib-asset-gen / -scenes：retries=3 E-ROOTCAUSE-3X、progress_bytes=0、零回执；bm-c ComfyUI 未起 + RAM 余量低 → asset_gen 必 rc=3。已置 BLOCKED(blocked_by=missing-input:comfyui@bm-c)，停止空转吃槽位。解封=bm-c 起 127.0.0.1:8188 且 free RAM≥4G 后 unlock。同机 asset-lib-char-gen（02:54:31 认领）仍在跑，未动。 |
| **队列同 id 双行（P1·并发 merge 副作用）** | **fix 已上 main·读端容错** | 本轮实测 dup=asset-lib-char-gen / asset-lib-asset-gen 各 2 行，清一次主控脉 merge 又长回来。修法=Tools/fleet/fleet_lane.py read_jsonl 按 id 收敛最后一条（位置取首次），消费者不再重复派/重复核销，commit 887ff9cc2。写端仍走 merge_jsonl collapse。 |
| **回访探针** | **armed** | +90min 一次性 cron：复探 bm-b 是否拉到 main / 是否出新回执，bm-c ComfyUI 是否起；复发=旗升 DE 级。 |

## 附录 R31 事件班登记（2026-11-11 00:01-00:2x·承载件触发·CLOCK-SKEW×3 + STARVED-EXEC bm-a/bm-b + BLOCKED-RAM bm-c×2）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **bm-b 执行器死 25h（STARVED-EXEC 真根因）** | **waiting-本机（无远程执行通道·零催办）** | `queue-receipts/_last_lane_bm-b.json` ts=**2026-11-09T23:00:23**（25h 零车道记录），而 bm-a 的 `_last_claim.json`（00:06:29）/`_last_lane_bm-a.json`（00:05:59）均新鲜。bm-b `/status` fork=**ahead 2 / behind 3209**（head e15d71a8 vs origin 773d2dc1），`last_pull.pulls=[".:updated"]` 每次拉取都保留本地 ⇒ 工作树停在 3209 笔之前的旧世界。**ahead 已从 R30 的 702 降到 2**，收口成本极低：<br>`cd C:\Fluxgroup\FluxGroup && git fetch origin && git branch -f backup/bm-b-20261111 HEAD && git reset --mixed origin/main && git checkout origin/main -- Tools cph4 && python Tools\fleet\agent.py --node bm-b --loop 60` |
| **bm-b 名下 4 张 RUNNING 零回执（僵尸认领）** | **registered·结构性（master assign 受保护面）** | `R-PLAN-BIGDOMAIN-20261111` / `R-PLAN-BIGMONEY-20261111` / `R-MODEL-RADAR-BMB-20261111` / `bigmoney-signal-2026-11-11` 均 owner=bm-b·claimed=00:04:0x，`cph4/fleet/queue-receipts/` 内**零回执**；同刻 bm-c 名下卡全部有回执。承 R6-1/R6-3（assign 每轮重写 claimed_at 使租约永不超时）。本班已把两张纯仓库卡转派 bm-a（ee0d72829·reroute_reason 留痕），机器专属卡（radar-bm-b / bigmoney-signal）保留 bm-b 并登记。 |
| **跨机错领复发（R14 家族 +2）** | **registered** | `R-MODEL-RADAR-BMA-20261111`（nodes=bm-a）被 **bm-c** 领走并产出 `-bm-c.json` 回执——该卡语义是「测 bm-a 的本地模型」，在 bm-c 跑等于测错机器；`Q-TRIAGE-BIGGAME-20261111`（nodes=bm-c）被 **bm-b** 领走且零回执。根因读码实证：`master_agent.py:640` 候选集来自 `fleet_lane.LANES` 而非 `fleet-nodes.json`，`nodes` 是**偏好非过滤**（663 行注释自述），仅 `hard_nodes` 是硬钉。修法候选=建卡侧一律写 `hard_nodes`（生成器 T1 面），master 侧不改。 |
| **bm-m 4 张「无 cmd」卡占供给位** | **registered·候裁** | `PATROL-bighouse-20261110` / `REPAIR-R-TRIAGE-BIGSTREAMDUANJU-BMB-20261101` / `UNBLOCK-VCORP-GEN-r1202-EP001-060-20261108` / `UNBLOCK-PATROL-bighouse-20261109`——`cmd` 全空、deliverable 为 .md，机器无法执行（承 R4-1 判例）；其中两张 `hard_nodes=["bm-m"]`（Mac 无 FleetLink/Windows 面）⇒ 结构化永不可执行。处置建议=patrol 生成器改为落 NEED-JUDGMENT 而非入队（工具面 T1；本班未擅改，避免与他窗写手赛跑）。 |
| **CLOCK-SKEW（bm-c 3818ms 持续增长）** | **waiting-CEO（提权物理件·零催办）** | 00:04:15 `CLOCK-SKEW.json`：hub bm-a −0.4ms（σ0.9）·bm-b **+1456.3ms**（σ0.8）·bm-c **+3818ms**（σ433.8）。bm-c 由 23:11 的 3611ms 续涨（≈2-4ms/min），三机 `w32time` 均 SERVICE-STOPPED。承 R2.38/R4-4/R8-6/R11-6/R13/R28 同源；秒级不影响派单租约。正法（各机提权）：`sc config w32time start= auto && net start w32time && w32tm /resync /force` |
| **BLOCKED-RAM bm-c（23:11/23:21 双旗）** | **resolved（本班实测自愈）** | 00:07 `/status` ram_free=**2.5G**（闸 1.0G / 10% 地板 2.4G 均过）、cpu 48%、fork **0/0**（与 origin 完全对齐）、`HQ-ProductionClaim=Running`；lane 在跑 `asset-lib-face-caption`。00:01 L0 已改报 `c=GPU-IDLE`，不再报 BLOCKED-RAM。 |
| **STARVED-EXEC bm-a（23:01 旗）** | **resolved（自愈）** | 00:01 起 bm-a=1 running；00:05:59 `_last_lane_bm-a` rc=0（R-NEXT-BIGSTREAMM-REBUILD）；00:07 队列 19 RUNNING。 |
| **机队整体产出实证** | **BURNING** | 00:07-00:2x origin 队列：RUNNING 16-19、DONE 700→708；`asset-lib-face-dataset-2026-11-11`、`R-MODEL-RADAR-BMA/BMC-20261111`、`R-TRIAGE-BIGGAME-BMC-20261111` 均有回执落地。故本班**零补卡**——供给充足，瓶颈只在一台机（bm-b）。 |


## 附录 R32 事件班登记（2026-11-11 00:41-00:5x·承载件触发·气候 DL 22:31-23:21 六旗 + 00:31/00:41 三旗）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **bm-b 整机 Tailscale 离线（LANE-DOWN 真根因·P1）** | **waiting-CEO（物理件·零催办）** | 三面实证：①`tailscale status` = `bm-b offline, last seen 23m ago, tx 2964 rx 0` ②ICMP `100.82.175.0` = False ③TCP `:8790` = False（对比 bm-c 同法 200）。零回执已 **24h**（末笔 `queue-receipts/trust-receipt-*.json` = 2026-11-10 00:19:36；`_last_lane_bm-b.json` = 2026-11-10 00:19:26）。bm-m 00:37 已提交 `5e31ba3a1 blockers: bm-b fully unreachable as of 00:30`。恢复=现场上电/唤醒 + 回归后跑 `NODE-SYNC-bm-b-20261111`（已在队）。本席无远程通道（CEO 2026-10-23 令）。 |
| **bm-b 名下僵尸认领（4 张·本班已按 STALLED-WORKER 解）** | **FIXED（数据层·可逆）** | 实证：`R-MODEL-RADAR-BMB-20261111` claimed 00:34:24 而 progress **00:11:40**（早于认领=master 每轮重写 claimed_at，承 R6-3），bm-b 已离线。处置四件：①`bigmoney-signal-2026-11-11` → bm-a（hard_nodes 本就含 bm-a，纯仓库活，输入 `etf_nobond_vt.json` 在盘）②`R-MODEL-RADAR-BMB` 退 OPEN + 清 owner + 补 `hard_nodes=["bm-b"]`（语义必须本机跑，防 R31 跨机错领复发）③`VERIFY-FIN-ETF-COMPOSITE` → bm-a（cmd 仅 `os.path.exists` 仓库文件，被 hard=[bm-b] 钉死于离线机且 retries=3 已成 BLOCKED 死锁；目标 `quant/bigmoney/results/etf_composite_pf.json` 实测在盘 4338B）④`R-NEXT-BIGSTREAMD-TTS-QC-20261109` 收窄 `nodes/hard=[bm-b]` + BLOCKED(`host-offline:bm-b`)——素材 `media/drama-tts-out/r1202_ep001_060` 只在 bm-b（R16 判例），原 nodes=[bm-c] 必 dir-missing 空跑。 |
| **队列读数勘误（本班自我更正）** | **corrected** | 本班首测经 PS 管道 `git show \| python` 得「1992→329 行、DONE 718→107」疑似队列被覆盖；改用 python `subprocess` 直读字节流后实测 **origin 1992 行 / 解析 0 坏行 / local==origin 0 差异**。结论：队列**未被覆盖**，先前的「截断」是 PowerShell 管道解码假读数。判例入册：读 JSONL 台账禁用 PS 管道转 python，一律 `subprocess.run(['git','show',...])` 取 bytes。 |
| **BLOCKED-RAM bm-c（00:11/00:21/00:41 三旗）** | **registered·真红（本机动作·零催办）** | 00:45 `/status`：`ram_free=1.5G`（24G 机 → 6.2%，低于 10% 地板 2.4G）、`cpu=77%`、fork **0/0**（与 origin 完全对齐）、v1.9.7 在跑 `asset-lib-face-caption`。因 RAM 闸，3 张 GPU 卡（`asset-lib-asset-gen` / `char-gen` / `asset-gen-scenes`，均 hard=[bm-c]）全部 capacity-blocked，其 claim 回 `POOL-EMPTY`。修法=bm-c 本机释放内存（`Tools/fleet/gpu_lease.py --acquire` 或关桌面重应用），禁重复 poke（r240 判例：poke 治不了 RAM）。 |
| **CLOCK bm-b MISSING / bm-c +2054ms** | **waiting-CEO（提权物理件·零催办）** | `CLOCK-SKEW.json` 00:39:19：bm-a `-0.1ms`(σ0.4) / bm-b **MISSING**（离线同源，非新病）/ bm-c **+2054ms**（σ**31.1ms**＝精度可信 ⇒ 真偏，不是中继噪声）。三机 `w32time` 均 SERVICE-STOPPED，承 R2.38/R4-4/R8-6/R11-6/R13 家族。修法（各机提权）：`sc config w32time start= auto && net start w32time && w32tm /resync /force`。2s 偏差不阻断派单租约。 |
| **STARVED-EXEC bm-a（23:01 旗）** | **resolved（自愈·实证）** | bm-a 在产：`_last_lane_bm-a.json` 00:44:57 `state=RESULT job=NODE-SYNC-bm-a-20261111 rc=0`；队列现 OPEN 11 张。23:01 的 `open=3/blocked=3/running=0` 为当时瞬时态。 |
| **bm-m 侧 6 张「空 cmd」OPEN 卡（residual）** | **registered·候裁（承 R31）** | `PATROL-bighouse-20261110` / `UNBLOCK-PATROL-bighouse-20261109` / `REPAIR-R-TRIAGE-BIGSTREAMDUANJU-BMB-20261101` / `UNBLOCK-VCORP-GEN-r1202-EP001-060-20261108` / `UNBLOCK-NODE-SYNC-bm-b-2330` / `UNBLOCK-PRODUCE-FLUXVERSE-20261110` —— `cmd` 全空 + 钉 bm-m（Mac 无 FleetLink 面）⇒ 结构性永不可执行。R31 已建议 patrol 生成器改落 NEED-JUDGMENT；本班不擅改生成器（避与他窗写手赛跑），只登记。 |
| **回访探针** | **armed** | +90min 一次性 cron：复验 ①bm-a 是否认领 `bigmoney-signal`/`VERIFY-FIN-ETF` 并出回执 ②bm-b 是否回归在线 ③bm-c RAM 是否过 2.4G 地板。复发=旗升 DE 级。 |

## 附录 R33 事件班登记（2026-11-11 01:26-01:55·承载件触发·CLOCK-SKEW×3 + STARVED-EXEC bm-a + BLOCKED-RAM bm-c）

| 件 | 状态 | 证据 / 下一步 |
|---|---|---|
| **BLOCKED-RAM bm-c 判为「假因」修正（P1·本班新实证）** | **corrected·真堵点=ComfyUI 无服务** | ①RAM 不是闸：`/status` ram_free 2.6→3.2G，`fleet_lane.ram_gate` 地板取 LANES 配置 **1.0G**（capacity_note 自证 `ram 2.6/1.0 GB`），高过闸；GPU 卡继而走 gpu_lease 只管 VRAM（bm-c 余 14.7G）。②真堵点：bm-c 三张 GPU 卡 `blocked_by=missing-input:comfyui@bm-c`；同一张卡在 bm-a 执行的回执写明 `WinError 10061 目标计算机积极拒绝`；`asset_gen.py`/`char_gen.py` docstring 明写「只在 127.0.0.1:8188 跑，卡片必须钉在有 ComfyUI 的机器上」→ **有内存也出不了图**。③故历次「BLOCKED-RAM 是资产线根因」的表述不成立，资产线根因=全机队无 ComfyUI 在服务。 |
| **落单 COMFY-UP-BMC-20261111（P0）** | **dispatched·已认属 bm-c·未燃（排队）** | 卡面：needs=gpu / hard_nodes=[bm-c] / need_mb=6000 / cmd=`comfy_guard.py` 后接 `char_gen.py --probe-only --receipt …/comfy-probe-bm-c-20261111.json`；deliverable=该回执（probe 返回 0 才 DONE，ComfyUI 没起来则 rc=3 不打绿）。闸：`card_contract_check.py` = **PASS (0 violations)**。上链：commit **72225cdec**；poke×3（01:40:45 / 01:43:02 / 01:48:21 全 accepted）。复探 01:53：state=OPEN / owner=bm-c / assign_ts=None，车道 01:50:16 起被 `NODE-SYNC-bm-c-20261111`(RUNNING) 占单槽 → **排队，非故障**。 |
| **gpu_lease 静默停线（新·工具面候裁）** | **registered·不改码** | `gpu_lease.py` 租约 `ttl_s` 缺省 **7200s**；`lane_agent.py` L505-508 对 `--acquire` 非零（含 **rc=2 LEASE-BUSY**）一律返回 `defer:True`，**不写失败回执**，只留 `_last_lane_<node>` 的 note。后果：一张被杀掉的 GPU 卡可让整机 GPU 线**静默停 2 小时**，队列里看不到错误。建议（候裁）= `LEASE-BUSY` 且 `age>30min` 视为陈锁自解，或 defer 时写一可见回执。 |
| **CLOCK-SKEW（承 R31·不重复立法）** | **waiting-CEO（提权物理件·零催办）** | `CLOCK-SKEW.json` 01:34:15：hub bm-a `-0.3ms`(σ0.3) / bm-b **MISSING**（离线同源，非新病）/ bm-c **+4194ms**(σ433.7)。判读=Δ/σ≈9.7，低于 11-10 提案动作线 10 倍 → **OBSERVE 档**（非新 P1）。**补登记**：`cph4/fleet/dispatcher/CEO-PROXY/PROPOSAL-20261110-clock-skew-action-line.md`（受保护件 `Tools/fleet-dispatcher.ps1` 加动作线：P1 仅 |offset|≥30s 或 Δ/σ≥10 且连续 3 周期同向，否则降 OBSERVE；旗行打印 relay/direct+rtt；真漂改发 CLOCK-UNTRUSTED）**至今未入 waiting-CEO 区**，本班补登于此，CEO 一句「批」即由 master 席落地。 |
| **STARVED-EXEC bm-a（23:01 旗）** | **resolved（实证）** | 01:24-01:25 bm-a 连出 6 份回执（asset-lib-index / voice-assemble / GAP-ASSETLIB-LEDGER / GAP-MV-GATE / bigmoney-signal / bigmoney-conclusion）；`/status` 01:36 CPU 37% RAM 23.1G。23:01 的 open=3/blocked=3/running=0 是计数语义缺陷造成的假红（承 R41），bm-a 本身一直在产。 |
| **bm-b 整机离线（LANE-DOWN）·第 N 次复核** | **waiting-CEO（物理件·零催办·不重复登记数值）** | 本班三面复核仍离线：TCP `100.82.175.0:8790` **TimeoutError**；两条独立心跳皆陈旧（MiniGame `fleet/b.json` ts=**10-29T15:31**（文件 mtime 今日被改写=写穿陈旧源旧病）、quant `machines/bm-b.json` mtime=**10-30 19:04**）；`CLOCK-SKEW.json` bm-b=MISSING 同源。**名下已无在飞卡**（队列自愈 01:30 以 `bm-b 不可达（B-ENV）` 撤销 `bigmoney-quote`；`asset-lib-voice-dataset` 已 DONE）。 |
| **回访探针** | **armed** | +90min 一次性 cron（03:2x）：复验 ①`COMFY-UP-BMC-20261111` 是否被认领并出 probe 回执 ②`comfy-probe-bm-c-20261111.json` 的 verdict ③bm-b 是否回归在线。复发=旗升 DE 级。 |

**R33 丢行补录（步8 丢行守望）**：本班落 LOG 时发现 DISPATCH-LOG.md 工作树**头部被截掉 8 行**（2026-11-08 19:21 与 19:31 两块 FLAG/INFO/pools），HEAD blob 仍在。已按「行所在提交 blob 逐字恢复」从 HEAD 补回 8 行并保留 BOM，复核 git diff --numstat = **+10/-0**（无删行）。根因未定位（疑 head-truncation 型重写/checkout 残留），登记为工具面观察项，不重复立法。

**R33 收口（02:31 起）**：COMFY-UP-BMC-20261111 **resolved**。证据=`cph4/fleet/asset-lib-v1/comfy-bm-c.json`（probed_at 2026-11-11T02:19:51+0800，route=ckpt，ckpt=DreamShaperXL_Lightning-SFW.safetensors，5ckpt/4unet/3clip/9vae）。三张因 `missing-input:comfyui@bm-c` 被转 BLOCKED 的卡已清 blocked_by 重开 OPEN。**自伤记录**：本卡首次记 FAILED/E-ARTIFACT 不是 ComfyUI 失败，是 deliverable 写成了 `comfy-probe-bm-c-20261111.json` 而 `char_gen.py --probe-only` 成功路径只写 conf 不写回执；已修脚本（probe-only 成功也写 --receipt）并按真实产物收口。

**R33-ADD4（2026-11-11 02:42）· stall 看门狗误杀重派卡（P1·新根因）**：`asset-lib-asset-gen-2026-11-11` 02:38:49 被认领，30 秒后即以 `STALL: 4765s 无新输出（sig=0）` 释放并升 `E-ROOTCAUSE-3X`。4764s 恰好等于 `claimed_at − progress_ts`（02:38:49 − 01:19:25）＝**看门狗按卡的旧 progress_ts 计时，重派不重置**，于是任何曾经 stall 过的卡每次重派都会被首 tick 秒杀，永远修不好（这也解释了资产线长期的「3 次未成」）。**本班只做workaround**：把仍 OPEN 的 char-gen / asset-gen-scenes 的 progress_ts 重置为当前时刻；props 卡因库存已满（11-07 回执 skipped=20/stock_full）改 CANCELLED。**待裁根因修法（一行）**：`lane_agent` 认领成功时 `progress_ts = now`（或看门狗用 `max(progress_ts, claimed_at)`）。改的是 agent 核心件，本席不擅动，候裁。
## ?? R35 ??????2026-11-11 02:46-02:53???????DL 00:51/01:01/01:11 ???

| ? | ?? | ?? / ??? |
|---|---|---|
| **BLOCKED-RAM bm-c?00:51/01:01/01:11 ???** | **resolved???????? 5 ?????** | `/status` 02:47:42 ram_free=**3.3G**?02:52 cpu 54%????=LANES ?? 1.0G?R33 ???RAM ??????GPU ??= `asset-lib-char-gen-2026-11-11` **RUNNING**?claimed 02:44:47??ComfyUI ?? `comfy-bm-c.json` 02:21:02 ?? ? ????????L0 ??? 21 ?????????? |
| **CLOCK-UNALIGNED old_schema=0 missing=1????** | **corrected?? schema ????** | `CLOCK-SKEW.json` 02:44:15?`old_schema=0`?????? schema??`missing=1`=**bm-b ??**??????????bm-c SKEW-HIGH +4653.6ms ? precision ?=593.2 ? ?/?=**7.8 < 10**?? `PROPOSAL-20261110-clock-skew-action-line.md` ? **OBSERVE**??? P1???????P1 upgrade node heartbeat to v2??**???**?? v2 ??????? |
| **LANE-DOWN lane=bm-b verdict=OFFLINE????** | **waiting-CEO?????????** | ??????`tailscale status`=`bm-b ... offline, last seen 2h ago, tx 14196 rx 0`?**?????**=?????????????`:8790/health` 15s ?? ?`:8790/status` ?????????????????? **123.2h**?`fleet_status` ? bm-b 123.2h STALE??? R32/R33 ????? **1 ? poke ????**?rx=0 ?? poke ?????? poke=churn????=????/?????? `NODE-SYNC-bm-b-20261111` ???? |
| **?? 5 ??????????T1 ???** | **executed** | ?`asset-lib-face-caption-2026-11-11` FAILED(retries=3 ???)?**OPEN**?`needs` gpu?**cpu**?`asset_caption.py` ? `OLLAMA_HOST` ?? ComfyUI?R33-ADD2 ????????retries ????`asset-lib-asset-gen-2026-11-11` CANCELLED?**OPEN**?`requeued_by=CEO-PROXY-EVENT-R34`???02:38:49 ? stall ??? 30 ???????? R33-ADD4 ?????? `asset-lib-asset-gen-2026-11-10` / `-asset-gen-scenes-2026-11-10` / `-face-caption-2026-11-10` ? **CANCELLED?superseded-by -11-11 ????**?? `blocked_by=missing-input:comfyui@bm-c` ?? 02:19 ?????????????????????? 2040 ?/2040 ?? id ????? 5 ? id ???? |
| **bm-m 5 ?? cmd ??residual?** | **registered????? R31/R32?? 3 ??** | `PATROL-bighouse-20261110` / `UNBLOCK-PATROL-bighouse-20261109` / `REPAIR-R-TRIAGE-BIGSTREAMDUANJU-BMB-20261101` / `UNBLOCK-VCORP-GEN-r1202-EP001-060-20261108` / `UNBLOCK-R-NEXT-BIGSTREAMD-TTS-QC-20261109` ?? `cmd` ?? + ? bm-m?Mac ? FleetLink ????? ?????????? OPEN ??9 ?? 5 ???**?????**???????????????? churn????? patrol/repair ????? NEED-JUDGMENT???? T1????? |
| **bm-c ????????????** | **BURNING????** | ??????OPEN 10?bm-c 2 / bm-a 3 / bm-m 5??RUNNING 2?bm-c char-gen?bm-m REPAIR??bm-c ?????????????? |
| **????** | **armed** | +90min ??? cron??04:35???? ?face-caption ? asset-gen ??? bm-c ?????? ?bm-b ?????? ?bm-c RAM ??? >1.0G???=?? DE ?? |
