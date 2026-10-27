# OH-20261011-bigdomain — OSS 借力第六窗切片件（BigDomain）

- **窗**：第六窗 2026-10-11 21:40 → 2026-10-14 21:40（P-2026-09-26-08+P-2026-09-28-01 承传·正典=cph4/oss-harvest.md）·交付 2026-10-10 ~23:2x +08:00（窗开前 ~22.3h 提前交付·R837 ~24.8h/R1131 ~26.8h 先例链带内侧偏近侧如实注·安全侧=72h 巡检线 10-11 08:36 与 10-11 03:07/15:07 双班值守扫之前全达·OH-20261008 件 mtime 10-08 08:36 起算 72h 线前置兑现）
- **实搜面**（5 次外部请求全录·采时 2026-10-10 ~23:1x-23:2x +08:00·宿主只读通道零登录墙零翻页零密钥）：
  - ①search「y-py ypy-websocket python yjs CRDT collaborative server」→ 得 6 结果（PyPI ypy-websocket+GitHub Pages 文档+**y-crdt/pycrdt-websocket〔现役正身〕**+y-crdt/ypy-websocket〔前代〕+PyPI pycrdt-websocket+三方 Yjs/CRDT 实操文）——**关键发现=改名谱系**：本司在册指针记「y-py/ypy-websocket 族」（OH-20261008 §五 评估闭注记）→ 搜索面直证该族已改名 **y-py→pycrdt、ypy-websocket→pycrdt-websocket**（同 org y-crdt·同作者 David Brochart）=候选按正身采
  - ②api.github.com/repos/y-crdt/pycrdt 元数据直采（A 级全字段：description=CRDTs based on Yrs·license spdx_id=MIT·stars=208·forks=39·open_issues=27·pushed_at=2026-10-05T21:50:28Z〔采时 5 日内〕·updated_at=2026-10-05·created_at=2023-09-20·archived=false·disabled=false·default_branch=main·topics=crdt/python/yjs）
  - ③api.github.com/repos/y-crdt/pycrdt-websocket 元数据直采（A 级全字段：description=WebSocket Connector for pycrdt·license spdx_id=MIT·stars=49·forks=21·open_issues=18·pushed_at=2026-09-20T11:43:32Z〔采时 20 日内〕·created_at=2023-12-08·archived=false·disabled=false·default_branch=main·homepage=y-crdt.github.io/pycrdt-websocket）
  - ④raw.githubusercontent.com/y-crdt/pycrdt/main/LICENSE → MIT 原文全文直采（「The MIT License (MIT) Copyright (c) 2023 David Brochart」+授权条款+免责声明·与 ② spdx 双源互证）
  - ⑤raw.githubusercontent.com/y-crdt/pycrdt-websocket/main/LICENSE → MIT 原文全文直采（「MIT License Copyright (c) 2022 David Brochart」·与 ③ spdx 双源互证）
  - 反重复预检（仓内零外部请求·2026-10-10 本轮）：集团切片面 cph4/oss-harvest 全目录 grep `y-py|ypy|yjs|crdt|pycrdt`=唯一命中 OH-20261008-bigdomain.md（=ygo 切片本件·指针源非重复采·预期内）·cph4/README.md 能力注册表 grep=零命中·司内 src 面 grep=零 Python CRDT 件（ygo-poc/ 沙箱=协议参照评估遗物〔yjs node_modules 回归对手件+Deln0r/ygo Go 模块〕·R1552/R1553 评估闭在册·非现役引擎）
- **候选**：y-crdt/pycrdt + y-crdt/pycrdt-websocket 双件套（https://github.com/y-crdt/pycrdt · https://github.com/y-crdt/pycrdt-websocket · 双件 MIT（各自 API spdx+raw LICENSE 原文双源验） · 208★/49★ · 契合点=P-47① 大厅共创状态收敛层 Python 正身：OH-20261008 §五 ygo 评估闭（终态=仅协议参照·Go 运维超承载定谳）明注「Python 自建信封服务端=y-py/ypy-websocket 族下窗五门候选」→ 本窗兑现=族正身 pycrdt（Yrs/Yjs Rust 核的 Python 绑定·CRDT 文档收敛免自研合并协议）+pycrdt-websocket（CRDT 文档 WebSocket 同步 connector·Jupyter 协作生态同源组件线〔David Brochart=jupyter-collaboration 维护者·生产背书面〕）〔入池≠采用·lobby 传输层 websockets 现役保持〕
- **采用→落点**：入池（非即采用）→①司级登记簿入池记录面（六）行（domain/BigDomain docs/oss-harvest/README.md·入池≠采用不入采用表）+接线轮五前置=**A** yjs@13 JS 客户端 wire-compat 实测（ygo-poc 既有 yjs node_modules 回归对手件直接复用·判负核心沿 ygo 案）+**B** lobby 现役语义保真对照（chat 幂等闸 E_DUPLICATE_MSG/重连恢复序列 AC-S8c~e/SecGate msgSecCheck 前置闸——共创文档面新居民文本接入点先过 SecGate+AIGC 服务器权威面保持）+**C** MIT attribution 双件携带+**D** PyPI 发布/轮子面复验（Windows wheel·pycrdt=Rust 扩展面）+**E** websockets 传输层现役保持注记（CRDT=应用层收敛·传输层不同层非双建·lobby-websocket-spec L83 不破）——触发=bootstrap 期启动（CEO 物理件到位后）或 P-47① 共创面功能窗（先于 bootstrap 的沙箱评估合法·ygo-poc 同型）
- **收益透镜**（P-2026-10-04-02 §六）：预期收益形态=省工时型（共创文档状态收敛协议 off-the-shelf=免自研 OT/合并协议·Jupyter 生产背书降低评估工时）·收益回访时点=接线后 30 天内首笔可测收益（wire-compat 实测过+共创面沙箱往返收敛实测）否则接线单降级 parked
- **parked+理由**：slice5 指针①真钥双接线=维持 gated（wechatpayv3+houbb 词库=CEO 物理件真钥到位即燃·三前置已备）｜slice5 指针②granian 接线轮=维持 gated（bootstrap 启动触发·五前置在册）｜slice5 指针③观测线=维持 gated（bootstrap 期启动前再评·structlog/loguru 方向线索已预置）｜L10 本地提效类=**本窗未开新实搜面如实记**（全部实搜面投 pycrdt 强指针方向=在册指针兑现优先·上窗零发现态承传·非空报「查了」）
- **下窗指针**：第七窗 10-14 21:40→10-17 21:40·线索=①真钥双接线（维持 gated·三前置已备）②granian 接线轮（bootstrap gated）③pycrdt 接线评估轮（触发=P-47① 共创面功能窗或 bootstrap 启动·五前置 A-E 在册·ygo-poc 对手件复用降工时）④观测线（bootstrap gated·structlog/loguru 预置）

## 一 五门评估（入池件：y-crdt/pycrdt + y-crdt/pycrdt-websocket 双件套）

| 门 | 判定 | 证据 |
|---|---|---|
| 1 契合 | 过 | 在册指针直承：OH-20261008-bigdomain.md §五 ygo 评估闭明注「Python 自建信封服务端=y-py/ypy-websocket 族下窗五门候选」=本窗兑现；P-47① 大厅共创状态收敛层需求在册（lobby-websocket-spec v0.3 §三 同步层选型节）；搜索面 ① 直证族正身改名谱系（y-py→pycrdt）；pycrdt=Yjs/Yrs 生态官方 Python 绑定（y-crdt org=yrs Rust 端口官仓）·topics=crdt/python/yjs；共创文档收敛=UGC 共创面（商业化收入域④）支撑件·非模型类 P-17 矩阵不涉 |
| 2 反重复 | 过 | 三面查证（R597/R837/R1131/R1460 同律）：集团切片面 grep 唯一命中=ygo 切片本件（指针源·预期内）+能力注册表零命中+司内 src 零 Python CRDT（ygo-poc=协议参照遗物非现役）；**非双建注记**：入池≠采用·lobby 传输层 websockets 沙箱现役保持（AC-S8b/S8c~e 基线在册）·pycrdt=应用层文档收敛件·传输层/应用层不同层（lobby-websocket-spec L83 注记不破）·ygo 终态=仅协议参照维持 |
| 3 许可 | 过 | 双件各自双源直验：pycrdt=API spdx_id=MIT+raw main/LICENSE「Copyright (c) 2023 David Brochart」MIT 全文；pycrdt-websocket=API spdx_id=MIT+raw main/LICENSE「Copyright (c) 2022 David Brochart」MIT 全文；MIT=直用类（slice1 canon 枚举）·GPL 禁入不涉；接线轮 attribution 双件携带前置在册 |
| 4 健康 | 过 | pycrdt：stars=208·forks=39·open_issues=27·pushed_at=2026-10-05（采时 5 日内·半年活跃线内远超）·created 2023-09-20（3 年存续）·archived=false；pycrdt-websocket：stars=49·forks=21·open_issues=18·pushed_at=2026-09-20（采时 20 日内·活跃线内）·created 2023-12-08·archived=false；connector 面 49★=生态位小众如实注·补偿面=Jupyter 协作生态生产背书（davidbrochart=jupyter-collaboration 维护者·ypy-websocket→pycrdt-websocket 同线承续）+core 208★ 双件同 org 同作者同活跃节奏 |
| 5 成本/安全 | 过 | 本地库件零遥测零密钥（CRDT 库+WS connector 非 SaaS）；pycrdt=Rust 扩展=PyPI 轮子分发面（Windows wheel 可用性=接线轮复验前置🟡）；非模型类零显存；源码公开可审；成本=纯本地依赖零 API 触点（三问门未涉·入池面） |

三问门（OSS 寻源 web 直采）：必要=窗 6 正典令文自证（P-2026-09-26-08「寻找开源社区」+P-2026-09-28-01 重申·第六窗承传·72h 巡检线在册）；无本地替代=外部仓元数据/许可原文无本地等效源（司内 ygo-poc=评估遗物非替代源·ygo Go 件已判超承载不采·pycrdt=Python 正身无司内等价物）；宿主既有只读通道（search MCP+api.github.com 直采+raw 直采）非新 API 接入零密钥——过门在案（R266/R320/R597/R837/R1131/R1460/R1550 先例口径）。

## 二 结论应用表（research-protocol §二.1 落点强制·无表=未交付）

| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| 入池 y-crdt/pycrdt+pycrdt-websocket（P-47① 共创状态收敛层 Python 正身候选·ygo 案下窗指针兑现） | ①司级登记簿入池记录面（六）行（domain/BigDomain docs/oss-harvest/README.md）+接线轮五前置 A-E（wire-compat 实测〔ygo-poc 对手件复用〕+lobby 语义保真对照+MIT 双件携带+PyPI 轮子面+websockets 现役保持注记·触发=bootstrap 或 P-47① 共创面功能窗） | 入池在册 |
| slice5 指针①真钥双接线 | ③门控留置（CEO 物理件真钥到位即燃·三前置已备） | 已闭环 |
| slice5 指针②granian 接线轮 | ③门控留置（bootstrap 启动触发·五前置在册） | 已闭环 |
| slice5 指针③观测线 | ③门控留置（bootstrap 期启动前再评·方向线索预置随册） | 已闭环 |
| L10 本地提效类 | 本窗未开新实搜面如实记（实搜面全投 pycrdt 强指针·上窗零发现态承传·非空报） | 已留册 |

## 三 认领行（radar v1.1 §6.4 固定格式·BigDomain R1847·2026-10-12）

- **认领行**：认领|y-crdt/pycrdt+y-crdt/pycrdt-websocket 双件套（CRDTs based on Yrs·Python 绑定+WebSocket 同步 connector·MIT）|来源=雷达窗 2026-10-11 第六窗切片（OH-20261011-bigdomain.md·P-2026-09-26-08+P-2026-09-28-01 承传）|转任务单指针=domain/BigDomain src/os/backlog.md pycrdt 接线前置 A+D 切片行
- **认领注记**：入池（六）行指针兑现链闭合（ygo §五「y-py/ypy-websocket 族下窗五门候选」→窗 6 入池→窗 6 内认领·两窗未领时钟清零）；接线轮五前置 A-E 中 **A（wire-compat 实测·ygo-poc 对手件复用）+D（PyPI Windows 轮子面 live 复验）** 双切片先执行——沙箱评估合法（ygo-poc 同型·先于 bootstrap）；B（lobby 语义保真对照）/C（MIT attribution 双件携带）/E（websockets 传输层现役保持注记）=接线窗（bootstrap 启动或 P-47① 共创面功能窗）执行；收益透镜=省工时型+接线后 30 天回访（P-2026-10-04-02 §六）；回执=BigDomain state.json log R1847 行+收账 commit 含窗号与件名（D-20260930-20 送达律）。

- **结果行（前置 A+D 切片·2026-10-12 R1847 当轮闭环）**：**A wire-compat 双向闭合 PASS**（正向=ygo-poc fixtures 三面全过：fx1 单客户端快照逐键==fx1-expected.json+fxA/fxB 双客户端并发对合并态==fx-merge-expected.json+sv-a 差分探针 sv_len=5 diff_len=96；反向=pycrdt 镜像 doc get_update 189B V1→node yjs@13.6.33 applyUpdate→快照逐键等）+**D 轮子面 live PASS**（pycrdt-0.14.8+pycrdt-websocket-0.16.5 cp314 Windows 轮子净装零源码构建）——AC-YC1..YC6 全过·证据=qa/pycrdt-wire-R1847.log（domain/BigDomain）+backlog R1847 行 done 注；ygo 未验之 wire-compat 门在 Python 正身上过线=指针兑现链实证闭合；B/C/E=接线窗执行（接线触发不变）。
