# DEADLINES — 死线台账（CEO 总调度代理席维护）

> 用法：每轮步2 死线雷达逐行核对 orders 最新回执翻新状态列；新死线=当窗入行（来源=orders 行/O- 号）；已过窗死线如实标注（延误披露禁抹除）。
> **waiting-CEO 区=物理件/保留面登记，零催办**（CEO 有空弄·本席只记账）。
> 基线快照 2026-10-14 12:0x（O-20261014-1210 建席件）。

## §一 在轨死线

| 死线 | 归属 | 来源 | 状态 |
|---|---|---|---|
| 10-14 13:00 V3.5 预览剪呈 CEO | bm-a 装配站 | O-20261014-1035 ⑥ | **延误·如实披露**（17:0x 审查轮核注：13:00 未呈·波1 六镜 16:4x 收齐/波2 点火·装配站接管中——是否并轨深夜终剪由 21:43 死线班跟核） |
| 10-15 08:43 MV V3 全本地终剪→成片闸→呈 CEO（CEO 死线·O-20261014-1855） | bm-a 装配站+@bm-c 缺件补产 | O-20261013-2200+NJ bigstream 10-15 00:33 | **延误·如实披露（R1.9 10-16 13:0x 翻新）**：V3 终剪死线未达——线被 CEO Jay 化裁定升格 V4（17 件 jayredo：11 件 i2v 10-15 20:38 bm-a 确认收讫+6 重摇件 @bm-c r1034 补烧 in-flight〔reshake6 复检 6/6 过 10-16 11:4x·DeliveryWatch 契约死线 14:05〕）→17 件齐→bm-a 装配站 V4 装配单已备（V3 时间线在位）→四闸→CERTIFIED 呈 CEO【R2.0 10-16 16:16:06 现势翻新：17/17 齐收口〔13:52 @bm-c 回执全上链+14:01 交付哨 DELIVERED hit=6〕·V4 装配 14:5x 委员会窗亲手执行在飞〔装配班 cron 两连蒸发·批载体改挂常设计划任务面候裁〕】；旧 7 缺件补产线已并入 jayredo 链 |
| 10-15 03:30 bm-b git 手术决断线（R2 裁决=A 案宽限观察·预注册决断树：a origin 见 bm-b push→自然恢复闭环 b r956 报 fetch 卡死/驱动死→即刻手术单 c 03:30 零心跳恢复→手术单〔预草案=bigmoney-shiftlog 枢纽决断行：kill blobfill pid 28880+C2 payload 抢救导出+re-clone S0 先例+push+selftest+回执〕） | 枢纽代理席（03:33 探针 cron 主承载+02:43/05:43 夜班+域席 R3 备份） | NJ bigmoney R2 01:33+LOG Round 1.3 | **resolved-手术作废（02:47 枢纽事件班 R1.4 亲测 a 闭环：r956 侧枝已落 origin〔ls-remote 3eaa15f1〕+listener 活〔02:43:55·心跳 r956@02:36:32=r955 push receipt consumed PUSHED_VERIFIED+recovery drivers 在飞〕→域席修正树③命中·手术单作废；03:33 探针=确认节奏零手术；残余=r957 提交轮 main push+faces 复原·bm-b.json weak 传感旗 main push 前复发=已知恢复态非新升级）** |
| C02/R05 源帧重制→重 i2v（装配邻段兜底） | @bm-c ✅已随 wave2 r1010 交付（C02_sand_bury/R05_gold_threads 修复 URL·事件班 01:2x 收割入 DL） | 10-14 11:0x 四抓 | done（r1010 消费面·字节校验过） |
| 10-14 V100 P0=bm-a 夜窗 MoE 卸载跑 35B（验收 ≥30 字/秒） | bm-a 夜窗 | V100-EXPANSION-SPEC v2 | done-在役（事件班 10-16 00:3x 翻行消费 bigcompute NJ r5〔五班同源 r1-r5 一致核验〕：证据亲验=compute/BigCompute/state/v100-p0-verdict-20261014.txt VERDICT PASS·跨跑 31.6 字/秒 ≥30·run1 29.2/run2 34.0 如实双录+双 JSON·35B :8090 在役=思考路由律本地档承载） |
| 10-14 软著 B/C 机 18 款源程序复跑批（CPU 面） | bm-c ✅C机8款上链（fc1b936·G02 7425/G03 8376/G06 6260/G09Y 3666/G10 5252/G12 10347/G17 8439/G18 12007 行）+@bm-b ✅B机10款上链（bfa61b6 03:55 GEN_DONE·txt/pdf 10/10+CCPC 10/10+报审台账§四销账）=18/18 | O-20261014-1035+事件班 NJ biggame R5 10-15 14:2x 翻行 | done（verified 18/18 全上链：09:06 bm-b 复跑 10/10 keys green〔O-20261015-0906-bm-b〕+POOL-0011 origin status=done〔result_ref GEN_DONE_OK〕四锚全验；事件班 10-15 14:3x 翻行收口=同签 re-fire 根面清·snooze 单帠目 until 10-17 09:15 在位（R8 落·枢纽 R1.8 亲验：载具 L61 词表缺口=永续旗真根·修法提名归并 bigmoney NJ#3 载具修法族候 CEO 令〔受保护件零擅改〕·到期旗复发=值班席续 24h 环直至修法落）；A机14款收编=POOL-0013 另轨 open·48h 窗 ~10-17 01:30 零催办） |
| 10-14 八度空间/叶惠美 音源批复跑→whisper 锚点→词面校准 | bm-a CPU | 10-14 10:3x（10:38 复跑实锚） | in-flight |
| 排队 bm-c：波1.5 SIL4 jman 强度 8 帧探针→波2 云槽位重产→波3 星晴 A 批 34 KF+选角板 16 | bm-c | O-20261014-1035 自链三波 | queued |
| 排队 W1：星晴 SHOTLIST-v3 已派·可爱女人 SHOTLIST v1 接棒 | 导演席+bm-a | O-20261013-1540 资产产线 | in-flight |
| 滚动：早期四专 41 曲全量重制（S 层 11 曲优先·1-1.5 曲/日·90 分入库门槛） | MV 线全员 | O-20261013-1540 | standing |
| 10-16 治理窗：C-20261009-01/02 预注册判据回访+C-20261012-01 Phase 2 合并议程 | 委员会 | decisions 台账 | scheduled |
| 10-19 回访：C-20261012-02/03 判据+总调度席判据（本席判据并入） | 委员会 | DISPATCHER-CHARTER §六 | scheduled |
| 10-28 BigHouse 判据：苏州吴中社区复刻+CEO 首住户安家+≥10 居民轨迹 | BigHouse/bm-b | BLUEPRINT v0.4 | standing |
| 短视频：video-remix 首批 S 池 3 条试产（GO·排 bm-b 音频批后） | bm-b | O-20261013-2245 ⑤ | queued |
| **B站账号运营线（回复/DM/outreach 三件套·已上线·代理席接管巡检 10-14 15:5x）**：护栏审计（每轮 ≤5/日帽/条间 30-90s/永不重发台账/R1 五信号熔断）+续登路（凭据已交接仓外）+回执 | bm-a 本地（车道例外=cookie 最短路·追认·bm-b 迁移待文件通道） | O-20261014-1330+15:1x 接管令 | live-在巡 |
| 事件班 schtasks 承载升级件：**已落地在役（10-14 19:1x·Phase 1-α·origin 2fed6498）——08:43 班勿重派（防双注册）**：HQ-CEOProxyEventCarrier PT15M+HQ-MA-ProxyProbe PT1H 静默在役·19:13 首发射实弹毕（事件班 Round 1.1·origin 75ac965·NJ 清零+锁收口 19:28:21）·代理席巡检面接管 | 已落地在役 | O-20261014-1745 Phase 1-α ①② | done-在役 |
| 10-17（周六）bm-a 周末自由运转边界（口令制 O-202601015-1845 首周末·WorkEnd 退役+pauseLite gamewin cron 挂起=周六无自动复产承载·真机制缺口） | 值守面（周六晨检班/事件班/委员会任一活面） | NJ biggame R8 ②+枢纽 R1.8 预注册 | scheduled（决断树：①默认=候 CEO「开工」口令〔保守向·口令制 §② 唯一开关律〕②CEO 全日未发口令+委员会判「节假日随便」生效→T1 代决 -Mode resume 复产〔常设授权令射程〕·执行前必探 CEO 用机面〔GameViewer/前台重载在跑=让路面优先照旧〕③口令一发即从令·禁以本行代口令④复产即 gamewin cron restore 自归位） |
| 10-16 14:00 @bm-b 欠件追缴五件回执（POOL-0020 销卡/spawn 帽腿回执/哨兵 PROBE_ERR 定谳/POOL-0018·0019 双锚批具名阻塞件/试映片 Taildrop） | bm-b | orders 10-16 13:0x 行+C-20261016-02 普查C/E | 延误·如实披露（R2.0 10-16 16:16:06 翻新）：14:00 窗过·五件回执零落——Taildrop 实测 bm-a media/drama-pilot-out 空缺=真欠交（交付哨 OVERDUE 12:49 hit=0/1·时poke 在哨）+POOL-0020 销卡/spawn 帽腿/PROBE_ERR/双锚批四件 orders 回执零；bm-b 活体在证（13:1x SYNCED 44s）——零重复 poke（防双烧：哨时poke+普查E 全列+21:43 死线班三通道在覆盖）；>24h 零回执=升 E1 委员会通道（10-17 08:43 晨检复核线） |
| 10-16 14:05 jayredo 6 件 i2v 补烧→拼板→bm-a 装配（V4 链前哨） | @bm-c | orders 10-16 11:4x 派单+Cure-1 契约 | done（R2.0 10-16 16:16:06 翻新：13:52 @bm-c 回执 17/17 全量上链〔QC 拼板 JAY-REDO-QC-SHEET-17-r1051〕·交付哨 14:01 DELIVERED hit=6 压哨·V4 装配在飞） |
| 10-16 ~15:0x @bm-c 仓分叉修复（backup 分支+reset --hard origin/main） | @bm-c | orders 10-16 13:0x Cure-2 行 | done（R2.0 10-16 16:16:06 翻新：12:4x 仓头自愈回 origin tip fc468f8+13:1x worker v1.4 判据三机验证全绿〔bm-a 13s/bm-b 44s/bm-c 17s SYNCED〕·19h 假绿病根治） |

## §二 waiting-CEO（物理件/保留面·零催办）

| 件 | 说明 |
|---|---|
| meme V1《慢慢踩》发布窗（18:00 首选） | 成片候 CEO 终审+发布授权 |
| B站 cookie+aid（**已闭环销账 10-14 15:5x**） | cookie=浏览器扩展提取在用（回复线 15:03 已真回复）；凭据=CEO 已交接·仓外 auth-handoff.json（零入库）；aid=频道 API 自动发现 |
| V100 16G 阶梯 P1 一键下单（¥900-1300 成套·**已落地销账 10-16 00:3x**·CEO 亲手执行） | 证据亲验=cph4/fleet/hardware/V100-RIG-BOM-20261014.md 采购状态节：X9DR3-F ¥280 已购+V100 SXM2 ¥950 已下单×1（单卡期=Gemma 26B QAT 全驻留主力·35B 续留 bm-a·第 2 张到位即切双卡迁移）+内存 16×16G 1600 终裁；到货验收三关死线=bigcompute NJ#2 standing 派生面 |
| 3090 双触发蹲价（≤¥4200）+A30 24G 观察（≤¥4500） | 触发信号=定版镜头/日>INT8 产能连续 3 天 |
| 软著定名待定区 6 款（G03/G06/G17/G18/G23/G28）+硅基域平台名 | 命名=CEO 保留面 |
| Steam 分支评级点选（★★★★★=P01/P05/P07） | O-20261010-1650 存量件 |
| BigLife census 造人线解禁 | 唯 CEO |
| 抖音/视频号等账号注册、devtools/AppID/商户号/域名备案族 | 物理件域·有空弄 |
| **G12 台账机核=BP+pre-push 全机提案（Phase 1-β-③·O-20261014-1745·命令级实施稿=cph4/fleet/dispatcher/MASTER-AGENT/G12-BP-PREPUSH-PROPOSAL.md）**：①GitHub branch protection 轻档（10 仓 main：禁 force-push+禁删·不开 required-PR——机队直推 main 工作流不能断）；②三机 `core.hooksPath=.githooks` pre-push 钩子（反转闸必拦+受保护件哈希漂移提示） | 账号治理面·**CEO 一次同意即三机同夜落地+回执**（登记制零催办） |
