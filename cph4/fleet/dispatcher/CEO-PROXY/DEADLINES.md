# DEADLINES — 死线台账（CEO 总调度代理席维护）

> 用法：每轮步2 死线雷达逐行核对 orders 最新回执翻新状态列；新死线=当窗入行（来源=orders 行/O- 号）；已过窗死线如实标注（延误披露禁抹除）。
> **waiting-CEO 区=物理件/保留面登记，零催办**（CEO 有空弄·本席只记账）。
> 基线快照 2026-10-14 12:0x（O-20261014-1210 建席件）。

## §一 在轨死线

| 死线 | 归属 | 来源 | 状态 |
|---|---|---|---|
| 10-14 13:00 V3.5 预览剪呈 CEO | bm-a 装配站 | O-20261014-1035 ⑥ | **延误·如实披露**（17:0x 审查轮核注：13:00 未呈·波1 六镜 16:4x 收齐/波2 点火·装配站接管中——是否并轨深夜终剪由 21:43 死线班跟核） |
| 10-15 08:43 MV V3 全本地终剪→成片闸→呈 CEO（CEO 死线·O-20261014-1855） | bm-a 装配站+@bm-c 缺件补产 | O-20261013-2200+NJ bigstream 10-15 00:33 | in-flight（事件班 01:2x 点火：wave2 39 件 CDN 收割+FLUX 11 件改名落 DL+cloudv2 21 件归档避让→预检 CLOUD-ONLY 35→7；V3.5 预览剪 540P 后台在跑；7 独立缺件已派 @bm-c POOL-0012〔INT1-5/D03b/E01c·INT8 768P〕；终剪候 7 件回执→asm 云引用=0→768P 终剪→QC/盲评→成片闸） |
| 10-15 03:30 bm-b git 手术决断线（R2 裁决=A 案宽限观察·预注册决断树：a origin 见 bm-b push→自然恢复闭环 b r956 报 fetch 卡死/驱动死→即刻手术单 c 03:30 零心跳恢复→手术单〔预草案=bigmoney-shiftlog 枢纽决断行：kill blobfill pid 28880+C2 payload 抢救导出+re-clone S0 先例+push+selftest+回执〕） | 枢纽代理席（03:33 探针 cron 主承载+02:43/05:43 夜班+域席 R3 备份） | NJ bigmoney R2 01:33+LOG Round 1.3 | **resolved-手术作废（02:47 枢纽事件班 R1.4 亲测 a 闭环：r956 侧枝已落 origin〔ls-remote 3eaa15f1〕+listener 活〔02:43:55·心跳 r956@02:36:32=r955 push receipt consumed PUSHED_VERIFIED+recovery drivers 在飞〕→域席修正树③命中·手术单作废；03:33 探针=确认节奏零手术；残余=r957 提交轮 main push+faces 复原·bm-b.json weak 传感旗 main push 前复发=已知恢复态非新升级）** |
| C02/R05 源帧重制→重 i2v（装配邻段兜底） | @bm-c ✅已随 wave2 r1010 交付（C02_sand_bury/R05_gold_threads 修复 URL·事件班 01:2x 收割入 DL） | 10-14 11:0x 四抓 | done（r1010 消费面·字节校验过） |
| 10-14 V100 P0=bm-a 夜窗 MoE 卸载跑 35B（验收 ≥30 字/秒） | bm-a 夜窗 | V100-EXPANSION-SPEC v2 | pending-夜窗 |
| 10-14 软著 B/C 机 18 款源程序复跑批（CPU 面） | bm-c ✅C机8款上链（fc1b936·G02 7425/G03 8376/G06 6260/G09Y 3666/G10 5252/G12 10347/G17 8439/G18 12007 行）+@bm-b ✅B机10款上链（bfa61b6 03:55 GEN_DONE·txt/pdf 10/10+CCPC 10/10+报审台账§四销账）=18/18 | O-20261014-1035+事件班 NJ biggame R5 10-15 14:2x 翻行 | done（verified 18/18 全上链：09:06 bm-b 复跑 10/10 keys green〔O-20261015-0906-bm-b〕+POOL-0011 origin status=done〔result_ref GEN_DONE_OK〕四锚全验；事件班 10-15 14:3x 翻行收口=同签 re-fire 根面清·snooze 21:47 夜审复核即清；A机14款收编=POOL-0013 另轨 open·48h 窗 ~10-17 01:30 零催办） |
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

## §二 waiting-CEO（物理件/保留面·零催办）

| 件 | 说明 |
|---|---|
| meme V1《慢慢踩》发布窗（18:00 首选） | 成片候 CEO 终审+发布授权 |
| B站 cookie+aid（**已闭环销账 10-14 15:5x**） | cookie=浏览器扩展提取在用（回复线 15:03 已真回复）；凭据=CEO 已交接·仓外 auth-handoff.json（零入库）；aid=频道 API 自动发现 |
| V100 16G 阶梯 P1 一键下单（¥900-1300 成套） | CEO 已裁·采购基金台账挂钩 |
| 3090 双触发蹲价（≤¥4200）+A30 24G 观察（≤¥4500） | 触发信号=定版镜头/日>INT8 产能连续 3 天 |
| 软著定名待定区 6 款（G03/G06/G17/G18/G23/G28）+硅基域平台名 | 命名=CEO 保留面 |
| Steam 分支评级点选（★★★★★=P01/P05/P07） | O-20261010-1650 存量件 |
| BigLife census 造人线解禁 | 唯 CEO |
| 抖音/视频号等账号注册、devtools/AppID/商户号/域名备案族 | 物理件域·有空弄 |
| **G12 台账机核=BP+pre-push 全机提案（Phase 1-β-③·O-20261014-1745·命令级实施稿=cph4/fleet/dispatcher/MASTER-AGENT/G12-BP-PREPUSH-PROPOSAL.md）**：①GitHub branch protection 轻档（10 仓 main：禁 force-push+禁删·不开 required-PR——机队直推 main 工作流不能断）；②三机 `core.hooksPath=.githooks` pre-push 钩子（反转闸必拦+受保护件哈希漂移提示） | 账号治理面·**CEO 一次同意即三机同夜落地+回执**（登记制零催办） |
