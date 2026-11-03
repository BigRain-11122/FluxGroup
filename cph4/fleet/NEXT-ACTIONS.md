# 所有业务的下一步（2026-11-04T06:27:14+0800）

运行 2 · 排队 9 · 停滞 4（其中工程可自解 0）

| 业务 | 优先 | 状态 | 下一个产物 | 承办 | 卡点 |
|---|---|---|---|---|---|
| 资产储备（角色 LoRA + 音色库） | P0 | RUNNING · asset-lib-voice-assemble-2026-11-03 | 传家宝出第一批角色图（8 角色 × 6 视角） | bm-c | ENGINE(char-probe 在 bm-c 上 rc=2 零回执，未定位（疑 checkout 落后）) |
| 游戏（39 款在册 / 0 上线） | P0 | QUEUED · R-PLAN-BIGGAME-20261104 | 36 款隐私政策 + 台账补登（机队能做完的那一半） | bm-a | CEO(截图需跑游戏取图，受 2026-10-28『不许自动跑游戏包』令约束，等放行) |
| MV（41 曲 / 爱在西元前） | P0 | RUNNING · bigstream-mv-transition-2026-11-04 | 发布回执，或下一首的选题+立意六轴案 | bm-m | ENGINE(发布决定权在 CEO，但工程侧可先做下一首立意案) |
| 量化（19.9 算力包） | P1 | QUEUED · R-PLAN-BIGMONEY-20261104 | 下月持仓信号 CSV + 四件齐结论一页 | bm-b | ENGINE(回测产物需在 bm-b 本地生成；主控无 quant 仓) |
| 前台 / 19.9 商城主页 | P1 | QUEUED · R-PLAN-BIGDOMAIN-20261104 | 一页可下单页（商品+价格+支付入口占位+退款说明） | bm-a | CEO(商户号/支付资质未签（物理件）) |
| 硅基城市 / 元宙（看板） | P2 | QUEUED · R-PLAN-FLUXVERSE-20261104 | 城市每日投影（指标快照+包体成熟度+体征变化） | bm-c | ENGINE(四仓不在本机，需在对应机器生成投影) |
| 硅基生命 / 居民 | P2 | QUEUED · R-PLAN-BIGLIFE-20261104 | 20 人端到端回执（每人一条事件链） | bm-a | ENGINE(城市仓不在本机) |
| 算力池 | P3 | QUEUED · R-PLAN-BIGCOMPUTE-20261104 | bm-d 入网验收回执（3×V100 48G 可接卡） | bm-d | CEO(机器未接线/未装系统，需人到现场) |
| 竞品拆解 | P3 | QUEUED · R-PLAN-RECON-20261104 | 小游戏榜单一周拆解（前 10 的核心循环+商业化点位） | bm-b | ENGINE(缺工序表与榜单抓取口径) |
| 平台运维（机队自身） | P3 | QUEUED · CHK-DUPES-20261103 | 本周自动化面 12 项全绿（现 8 绿 4 部分/风险） | bm-m | ENGINE(I2 存量 125 条卡面路径债、vault 缺盘 651 条) |
| 漫剧 | P9 | STALLED | 第 2 集（角色一致性用角色包锁） | bm-c | CEO(CEO 令暂停（先铺资产库/MV/游戏/城市）) |
| 短视频（B站运营） | P9 | STALLED | 一条可发短内容（切片或梗） | bm-a | CEO(CEO 令暂停（先铺资产库/MV/游戏/城市）) |
| BigHouse | P9 | STALLED | — | - | CEO(无需求证据，恢复需 CEO 明令) |
| 车机（吸嘟嘟家庭版） | P9 | STALLED | OEM 一页材料送出（需 CEO 渠道） | bm-m | EXTERNAL(等 OEM 意向，不投产能) |
| 短剧 | P9 | QUEUED · Q-TTS-QC-R1-20261103 | 素材盘点 + 配音质检报告 | bm-b | CEO(CEO 令暂停（先铺资产库/MV/游戏/城市）) |
