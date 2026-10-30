| 公司 | 条线 id | 判定 | 断在哪道工序 | 证据龄小时 | 一句结论 |
|---|---|---|---|---|---|
| BigStream | bigstream-drama | BLOCKED | 无具体工序（全线停摆） | null | 漫剧席强制锁定，无活可跑且车道阻塞 |
| BigStream | bigstream-mv | WAITING | 立意/分镜 (mv-plan) | null | MV 41 曲有活但无供给源，处于等待队列 |
| BigStream | bigstream-duanju | WAITING | 试构图 (duanju-board) | null | 短剧线因缺料静默，等待上游注入 |
| BigStream | bigstream-shortvideo | PARKED | 选题/脚本 (sv-script) | null | CEO 指令停机，全链路冻结不可执行 |
| BigGame | biggame | WAITING | 玩法/数值 (game-design) | null | 游戏线空转待命，等待设计稿输入 |
| FluxVerse | fluxverse | WAITING | 场景装配 (city-assemble) | null | 元宙城缺素材，地编席闲置等待 |
| BigMoney | bigmoney | WAITING | 数据 (quant-data) | null | 量化线缺源，回测引擎空转 |
| BigDomain | bigdomain | WAITING | 引流线索 (domain-lead) | null | 商业化域无新单，运营席静默 |
| BigCompute | bigcompute | WAITING | 成交环 (compute-deal) | null | 算力中枢无交易流，等待撮合 |
| BigLife | biglife | WAITING | 人设生产 (life-gen) | null | 数字生命缺种子数据，无人设产出 |

① 最先要修的是 **bigstream-drama**（漫剧），因其状态为 **BLOCKED** 且被判定为全线阻塞，是唯一直连“容量阻塞”的断点。
② 今天该派给 **bm-m** 机器处理 **R-SUBCO-20261029-001** 任务（该任务已在 events 中指向 bm-m 且为 cpu 类型）。
③ 本机 NO-DATA 判不了的：**bigstream-drama (drama-kf)**、**bigmoney (quant-data)**、**recon (recon-scan)**，需调取 **bm-b** 与 **bm-a** 机台实时产出日志。