# B站账号运营 Agent v3 — 大喵没鱼吃（2026-10-14 定版）

> 溯源：CEO 令 2026-10-14「放行+慢速删+私信监控回复」「好好研究B站风控规则…维护账号…合理评论引流」「全方位调研调集专家打磨 agent 做到健壮高效科学」
> 执行体：bm-a 本地 C:\Users\sjs20\bili-bot\（凭据只存 git 外·cookie-handoff2.json）
> 风格研究底座：research\REPLY-STYLE-RESEARCH.md（CEO 121 条真实回复提炼+QQ音乐精选热评 210+网易云晴天 15+本频道粉丝 105）

## 一、系统总览（五模块·全部计划任务·隐藏链）

| 模块 | 文件 | 任务 | 频率 | 状态 |
|---|---|---|---|---|
| 评论回复 | bili_bot.py | bm-a-BiliAutoReply | PT15M | LIVE（新 persona v2） |
| 私信监控+回复 | bili_dm.py | bm-a-BiliDM | PT15M | LIVE |
| 重复回复慢清理 | research\delete_dups.py | bm-a-BiliSlowDel | PT60M | LIVE（队列 23→0 后自动停） |
| 对外评论引流 | bili_outreach.py | bm-a-BiliOutreach | daily 20:23 | **enabled=false 待 R2 回填** |
| 回复质量夜审 | bili_qc.py | bm-a-BiliQC | daily 09:17 | LIVE（首轮 10/12 过线） |

## 二、文案系统（真人化三层）

1. **persona v2**（config.json·正身）：照 CEO 真实手感——大多数回复 2-15 字（哈哈/嗯确实/瞎看的）；有梗必接（夜曲一响→上膛）；聊歌只给一句具体的；不装懂；不吵架；不追火；被问 AI 幽默承认。禁：颜文字/emoji/宝子/搬运/客套话/自称大喵。
2. **四道机械闸**（gate_lib.py·代码层强制·不靠 LLM 自觉）：开头查重 / 短语撞车（4 字 n-gram 治口头禅复读）/ 歌名错配 / 超长压短。35B 实测会自我复读（"DNA动了"×3 实锚），闸比 prompt 可靠。
3. **overlay**：私信模式=稍微热络+求资源客气拒；引流模式=纯老杰迷视角，禁词墙（链接/主页/关注/资源/频道名/4K/修复 全禁）。

## 三、安全护栏总表（防风控第一原则）

- 评论：每轮 ≤5·**每日 ≤15**·条间 30-90s·同评论永不重发（台账键 str 归一）·连续 2 发送失败=当轮熔断
- 私信：每轮 ≤3·每日 ≤8·每对话人终生自动回 1 次（后续只监控）·系统/推送/自动问候/营销链接=静默跳过·商务类只标记不代回
- 引流：每日 ≤3·每视频终生 1 条·条间 5-15 分钟·**默认关**——R-20261014-bili-growth-01 安全参数回填后才开闸
- 慢清理：每小时 ≤2 条删除·随机间隔 50-110s
- 停机纪律：任何异常（风控码/连续失败/cookie 失效）第一动作=停任务停进程，绝不带病运行；账号写操作变更需 CEO 点头（CEO 令 10-14「不要瞎搞导致我封号」）

## 四、专家评审记录 v1（2026-10-14·四席）

| 席位 | 意见 | 处置 |
|---|---|---|
| 风控合规 | ①15+8+3 的日写量需 R1 官方条款背书；②cookie 单点失效会四模块同炸；③引流是新视频下发评，与站内回复风险特征不同 | ①R1 回填后复核数值；②待办：DM cycle 加 nav 健康自检；③引流水位从 1/天起步灰度 |
| 账号运营 | ①回复积压(月前老评论)UP 翻牌属正常生态；②QC 夜审要防persona 漂移（规则改动后回归集过闸）；③置顶评论/动态运营=后续phase2 | ①在跑；②QC 已挂 daily；③入 backlog |
| LLM 工程 | ①粉丝评论文本=不可信输入（注入面），四闸+长度帽+禁词墙是主防线；②重写最多 4 轮，最坏单条 ~40s，一轮 5 条 ≈5.5min<15min 节拍，贴上限需监控；③35B 单槽双 8k 与 coder 会话共享，注意抢占 | ①已入闸；②QC/日志双监控在位；③错峰：QC 09:17/引流 20:23 均避开 coder 高峰 |
| 产品 | ①dm-watch.md 无主动提醒机制，biz-flag 会被埋；②「需CEO过目」类应升到 CEO-PROXY 巡班视线 | ①巡班接管 dm-watch 变更检查（接线中）；②已记 DEADLINES 侧待接线 |

## 五、待研究接线（回填位）

- R-20261014-bili-riskcontrol-01（调研中）：官方红线条款+处罚阶梯 → 复核 §三 全部数值
- R-20261014-bili-growth-01（调研中）：引流实操+翻车死因 → 决定 outreach 开闸与目标池

## 六、文件地图

- 执行体：C:\Users\sjs20\bili-bot\（bili_bot/bili_dm/bili_qc/bili_outreach/gate_lib/config/replied.json/dm-replied.json/dm-seen.json/outreach-done.json）
- 日志：media\logs\bili-bot.log（主日志）/ dm-watch.md（私信监控摘要·含【需CEO过目】区）/ bili-qc-last.md（夜审报告）
- 语料与风格研究：bili-bot\research\REPLY-STYLE-RESEARCH.md + corpus-*.{json,txt}

## 七、运营 SOP（人工动作面）

1. CEO 随时可看：私信摘要 `C:\Users\sjs20\Desktop\FluxGroup\media\logs\dm-watch.md`（搜「需CEO过目」）
2. 夜审报告每日 09:17 出：`C:\Users\sjs20\Desktop\FluxGroup\media\logs\bili-qc-last.md`
3. cookie 失效症状=四模块连续 LIVE-FAIL → 手动重新取 cookie（ckext2 扩展已留底）填 cookie-handoff2.json
4. 全停一句话：`schtasks /change /tn bm-a-BiliAutoReply /disable`（其余任务同理）
