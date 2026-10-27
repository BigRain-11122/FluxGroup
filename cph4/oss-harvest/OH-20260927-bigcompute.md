# OH-20260927-bigcompute — OSS 借力首窗切片件（BigCompute）

- **窗**：首窗 2026-09-26 21:40 → 2026-09-29 21:40（P-2026-09-26-08·正典=cph4/oss-harvest.md v1.0·T2 否决窗至 10-03·台账位裁定=D-20260927-03 同律口径：本目录本司单文件=唯一许可实体→集团仓写盘面·收账 commit 归收取轮）·切片交付 2026-09-27 ~08:05 +08:00（窗内·OSLoop 哨兵触发轮）
- **实搜面**（2 处实录·采时 2026-09-27 08:01-08:04 +08:00·UA=BigCompute-OSLoop·礼貌节流 3 次外部请求零登录墙零翻页）：
  - ①GitHub API search `q=tiktoken&sort=stars&order=desc&per_page=5`（total_count=730）→ 5 结果全录：openai/tiktoken（19,332★·MIT·pushed 2026-08-17·fast BPE tokeniser）/jimmc414/onefilellm（2,019★·MIT·网页仓库/论文聚合入 LLM 摄入件）/dqbd/tiktokenizer（1,697★·MIT·在线 token 演练场 web 件）/pkoukk/tiktoken-go（957★·MIT·Go 移植）/niieani/gpt-tokenizer（849★·MIT·JS 移植）
  - ②GitHub API search `q=douyin&sort=stars&order=desc&per_page=5`（total_count=8,902）→ 5 结果全录：yikart/AiToEarn（26,456★·MIT·多平台自动发布〔抖音/快手/小红书/视频号〕）/Evil0ctal/Douyin_TikTok_Download_API（20,344★·Apache-2.0·抖音/TikTok 数据采集+无水印下载自托管 API）/putyy/res-downloader（20,213★·Apache-2.0·视频号/小程序/抖音等资源下载）/JoeanAmier/TikTokDownloader（16,328★·GPL-3.0·抖音作品下载/数据采集）/dreammis/social-auto-upload（15,201★·MIT·自动化上传视频到抖音/小红书/视频号等）
  - 许可验证面：raw.githubusercontent.com/openai/tiktoken/main/LICENSE 原文直采（MIT·「Copyright (c) 2022 OpenAI, Shantanu Jain」grant 段逐字在案）
- **候选**：openai/tiktoken（https://github.com/openai/tiktoken · MIT · 19,332★ · 契合点=P-67 计价双口径 B 口径/配额成本台账计量核数面——1M token 粒度结算需确定性本地计数能力·Tools/cost_ledger.py 现 tokens=消费方自报缺独立核数/预估面）
- **采用→落点**：采用（接入评估单）→ 任务板 T-20260926-23 行注记「计量核数面」有界步（引入轮判据预注册：selftest 扩测+encoding BPE 文件离线预取验证+口径注记）——认领轮先行·非本轮直装
- **parked+理由**：douyin 生态 top5 全件判负（第 1 门合规即负：协议逆向/采集/批量自动化类=平台 ToS+账号封禁风险·权利第一下商业自动化仅走官方开放平台 API 路线·物理件/资质随开店·→ 本司风险台账 R-27 立行）｜onefilellm/tiktokenizer/tiktoken-go/gpt-tokenizer（形态/语言面不契合本司 Python 台账栈·Go/JS/Web 件）
- **下窗指针**：次窗 09-29 21:40→10-02 21:40·线索=①T-22 A 族推理服务化外围（Ollama serve 常驻标准 API 兼容层生态件）②B 族成本经济学锚点源（电价/折旧基准数据面）③小店官方开放平台 SDK 线（资质物理件到位后）

## 一 五门评估（采用件：openai/tiktoken）

| 门 | 判定 | 证据 |
|---|---|---|
| 1 契合 | 过 | P-67 计价双口径 B 口径（内部成本锚·结算唯一口径）1M token 粒度记账=O-20260926-2253 ②件+赋能目录 v1 §三+T-23 台账件现役；Tools/cost_ledger.py quota-issue/quota-consume 的 tokens 输入=消费方自报（本司 Tools 实勘无计数面）→缺独立核数/预估/审计面；tiktoken=替自研 BPE 计数轮子（CEO 三律②不重复造轮子） |
| 2 反重复 | 过 | 三面查证：cph4/README.md 注册表 grep token/计数/tokenizer/BPE=3 命中行均=token 经济机制面（轮账本计量行/L3 收缩层）非文本计数器能力行；本司 Tools 清单实勘（cost_ledger/fulfillment/iteration_loop/order_sentinel）无 BPE 计数面；Ollama eval_count=服务端计数依托（local-llm-pipeline 面）非独立核数工具=真缺口非双建 |
| 3 许可 | 过 | MIT 原文逐字直验（raw…/LICENSE·「MIT License Copyright (c) 2022 OpenAI, Shantanu Jain」+grant 段 Permission is hereby granted, free of charge…）→直用类（CC0/MIT/Apache/BSD） |
| 4 健康 | 过 | stars=19,332·pushed=2026-08-17（月内活跃）·open_issues=133（占比 <0.7%）·OpenAI 官方组织维护非死项目 |
| 5 成本/安全 | 过（带注记） | 纯本地 BPE 运算零外发零密钥面；注记①=encoding BPE 词表文件首次按 encoding 自 openaipublic blob 拉取（一次性网络面·离线部署须预取缓存=引入轮判据）；注记②=OpenAI 编码≠Qwen 词表——Qwen 侧精确计数以 Ollama 服务端 eval_count 为准·tiktoken 定位=OpenAI 兼容面/预估/审计核数（诚实边界·禁当 Qwen 结算唯一计数源） |

## 二 结论应用表（research-protocol 落点强制·无表=未交付）

| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| 采用 tiktoken（计量核数/预估/审计面候选） | ①任务单接线=T-20260926-23 行注记「计量核数面」（引入轮判据预注册·selftest 扩测+离线预取+口径注记） | 接线中 |
| douyin 生态 top5 判负（灰产工具合规门·官方 API 唯路线重申） | ④判负留痕（+本司风险台账 R-27 立行·联动 R-03/R-08/R-11/R-21） | 已闭环 |
| tiktoken 衍生件 4 件不采（onefilellm/tiktokenizer/tiktoken-go/gpt-tokenizer） | ④判负留痕（形态/语言不契合） | 已闭环 |

## 三 验证声明

读源：GitHub API search 2 查询+raw LICENSE 直采 1 次=3 次外部请求（2026-09-27 08:01-08:04 +08:00·礼貌节流零翻页零登录墙）。分级：tiktoken 五门证据=A 级直采（GitHub 官方 API 字段+raw LICENSE 原文）；douyin top5 判负=🟡 描述级判断（repos description+topics 面判断·未逐仓深审代码——第 1 门即判负无需深审·深审留用前门）；反重复门=cph4/README.md grep+本司 Tools 实勘在案。本件落 cph4/oss-harvest/（D-20260927-03 同律·收账 commit 归收取轮）·T-20260927-26 行级更新随本司 commit。

## 四 2026-09-28 13:3x 续窗切片 2（serve 生态线·窗内滚动·次窗线索①）

- **候选**：PrismML-Eng/llama.cpp（https://github.com/PrismML-Eng/llama.cpp ·**MIT**〔GitHub 仓库页侧栏+README「License: MIT」直读·2026-09-28 13:3x +08:00 采〕·809★·155 forks·prism-b10743 release 在发）——Ternary-Bonsai PTQ1_0 私有三元核唯一本地载具（上游 llama.cpp 拒载·fork README 明示）。
- **评估语境**：非新搜采=**实弹消费后回账**（机队分发令 P-2026-09-28-07 @BigCompute 赋能摘要批对照试验直接采用本件跑通四件套回执——评估=本机真实运行态·五门最强证据形态）。
- 五门：①契合 过=serve 底座（BigCompute 赋能目录 §二.3 常驻标准对接面·OpenAI 兼容 /v1/chat/completions）；②反重复 过=Ollama 栈拒载 PTQ1_0〔fork 专属载具非双建〕·与现役栈共驻实测零冲突；③许可 过=MIT 直用类；④健康 过=release 在发+本机实弹（health ok 4.1s·tg128 3.20 tok/s CPU 档·27B@5.95GB 字节锚 PASS）；⑤成本/安全 过（带注记）=本地回环 127.0.0.1 零外呼零密钥·进程 RAM 6.56-7.99GiB〔注记=-ngl 0 下 CUDA 上下文显存增量实测 +0.3GiB〕。
- **结论应用表**：采用（试验态载具·已用）→ ①任务单接线=T-20260928-31 四件套回执〔结论三态=observe·adopt 判定须 GPU 档重验后过 O-2175+fleet-allocations §8.4〕；证据指针=BigCompute docs/research/R-20260928-bonsai-empowerment-summary-trial+state/trial-bonsai-20260928-1332/（本司仓原始档）。
- 验证声明：本节 GitHub 页面 1 次外部请求（2026-09-28 13:3x +08:00·礼貌节流零翻页）·许可=页面直读 A 级；运行数字=本机实弹 A 级（原始档在 BigCompute state/）。

## 五 2026-09-28 22:4x-22:5x 续窗切片 3（小店官方 SDK 线·窗内滚动·次窗线索③）

- **实搜面**（3 次外部请求·2026-09-28 22:4x-22:5x +08:00·礼貌节流零翻页零登录墙）：①GitHub API search `q=jinritemai&sort=stars&order=desc&per_page=5`（total_count=23）→ 5 结果全录：iMactool/jinritemai（69★·PHP·license=null·pushed 2021-07）/cnJun/sdk4-jinritemai（63★·Java·license=null·pushed 2021-03）/zsmhub/doudian-sdk（12★·Go·Apache-2.0·pushed 2024-04）/minibear2021/doudian（8★·Python·MIT·pushed 2022-11）/hotpoor/findmaster_jinritemai_autoclick（7★·JS·Apache-2.0·pushed 2023-12）；②GitHub API search `q=doudian&sort=stars&order=desc&per_page=5`（total_count=99）→ 5 结果全录：TonyWang-hub/mcp-cn-commerce（67★·Python·MIT·pushed 2026-09-28 当日）/iamyzc/doudian-scripts（20★·JS·MIT·pushed 2022-12）/Abbotton/laravel-doudian（18★·PHP·MIT·pushed 2022-04）/zsmhub/doudian-sdk（重复件）/whalesky-labs/doudian-sdk（10★·PHP·MIT·pushed 2026-03·710+ API 接口宣称）；③raw.githubusercontent.com/TonyWang-hub/mcp-cn-commerce/main/README.md 全文直采（判官方路线与真店验收状态）。
- **候选**：TonyWang-hub/mcp-cn-commerce（https://github.com/TonyWang-hub/mcp-cn-commerce ·MIT·67★·CI pytest 在跑·PyPI 0.1.5 稳定/0.1.6 工程候选·2026-06 建仓·pushed 当日）——中国电商 8 平台 MCP Server 套件·doudian lane 25 工具注册·**当前已核 SDK 范围=订单列表/详情+售后列表/详情**（=BigCompute 履约管线 OrderSource 替换点 1「订单列表查询」同构面）·官方开放平台 API 凭证面（DOUDIAN_APP_KEY/SECRET/ACCESS_TOKEN 环境变量·直连平台 API 无中间服务器·非采集非后台自动化=R-27 官方 API 唯路线合规）·默认全工具只读。
- **五门评估（mcp-cn-commerce doudian lane）**：①契合 过=OrderSource 替换点 1 同构（订单列表/详情+售后列表/详情只读合同·fulfillment 骨架 44/44 PASS 现役的订单源接线窗候选）+Python 3.11+ 台账栈同语；②反重复 过=本司 Tools 实勘无抖店 API 客户端面（E14=官方文档 URL 锚在册·接线未做）·真缺口非双建；③许可 过=MIT 双源直验（GitHub API spdx 字段+README 徽章/LICENSE 引用·开源 Core 永久免费·Pro 闭源商业面=不采只采 Core）；④健康 **过（带关键注记）**=pushed 当日+CI 在跑+工程诚实面强（「注册数量不代表已核合同或真店可用数量」「所有 SDK live_verified 仍为 false」「真实店铺验收尚未执行」逐字在案）——**live_verified=false=采用前置缺口**（工程验收≠真店验收·README 自证）；⑤成本/安全 过（带注记）=本地运行零遥测（「无数据收集」自述）+凭证环境变量面+只读默认·注记=处理电商敏感凭证（接入须入风险台账）+抖店侧需企业/个体户资质（=开店物理件同窗·blocked 如实）。
- **parked+理由（8 件判负留痕）**：iMactool/jinritemai+cnJun/sdk4-jinritemai（第 3 门 license=null 未声明·且 2021 起停更）/minibear2021/doudian（Python 同语契合但 8★+2022-11 停更=第 4 门健康负·签名算法参考位留用）/zsmhub/doudian-sdk（Go·doudian-sdk Go 语言面不契合 Python 台账栈）/whalesky-labs/doudian-sdk+Abbotton/laravel-doudian（PHP 语言面·710+ 接口宣称件=订单 API 结构参考位留用）/iamyzc/doudian-scripts+hotpoor/findmaster_jinritemai_autoclick（**第 1 门合规即负：商家后台脚本自动化/后台自动点击=非官方 API 路线·R-27 同律**·与切片 1 douyin 生态判负族同源）。
- **结论应用表**：mcp-cn-commerce=**④判负留痕（本轮采用面）+观察位接线候选**——采用态两窗双 blocked：本司侧 OrderSource 接线随开店物理件（M4/E14 同窗）+候选侧 live_verified=false 真店验收未执行；**采用路径预注册**=开店物理件到位→官方 SDK 渠道（抖店开放平台开发者站点分发）为主路线对照评估·mcp-cn-commerce=AI Agent 原生 MCP 形态次路线候选（pip install mcp-cn-commerce 低摩擦·真店验收状态翻绿为前置）·评估单挂 BigCompute main M4 接线窗；8 件判负=已闭环。
- 验证声明：本节 3 次外部请求（GitHub API search ×2+raw README ×1·2026-09-28 22:4x-22:5x +08:00·礼貌节流零翻页）。分级：搜索结果与许可证字段=A 级直采（GitHub 官方 API）；mcp-cn-commerce 五门证据=A 级（README 全文直采·关键句逐字引用在案：live_verified=false/真实店铺验收尚未执行/无数据收集）；8 件判负=🟡 描述级判断（repos description+language+pushed 字段面判断·第 1/3/4 门即判负无需深审）。本件落 cph4/oss-harvest/（D-20260927-03 同律·收账 commit 归收取轮）·T-20260927-26 行级更新随本司 commit。

## 六 2026-09-28 23:1x 续窗切片 4（成本锚点源线·窗内滚动·次窗线索②=B 族成本经济学锚点源〔电价/折旧基准数据面〕·T-22 族 B 续窗同对象）

- **实搜面**（3 次外部请求·2026-09-28 23:1x +08:00·GitHub API search ×3·礼貌节流零翻页零登录墙）：①`q=llm+pricing&sort=stars&order=desc&per_page=5`（total_count=2,508）→ 5 结果全录：AgentOps-AI/tokencost（2,006★·MIT·Python·pushed 2025-09-05·400+ LLM token 价格估算）/ikatsov/tensor-house（1,460★·Apache-2.0·Jupyter·pushed 2024-01·企业 ML 参考集）/tigicion/dao-code（1,083★·MIT·TS·编码 agent 不契）/dalisoft/awesome-hosting（936★·MIT·托管价目清单）/pydantic/genai-prices（384★·MIT·Python·pushed 2026-09-25·LLM 推理 API 价格计算）；②`q=cloud+gpu+pricing&sort=stars&order=desc&per_page=5`（total_count=116）→ 5 结果全录：arc53/llm-price-compass（223★·MIT·TS·pushed 2024-12·云 GPU 基准比价）/dstackai/gpuhunt（57★·MPL-2.0·Python·pushed 2026-09-28 当日·云厂商 GPU 价格聚合）/devinschumacher/cloud-gpu-servers-services-providers（31★·license=null）/zlatin777/LLM-chatbot（13★·Apache-2.0·不契）/wilsonwen123/CloudGPU（5★·license=null·2023 停）；③`q=electricity+price+china&sort=stars&order=desc&per_page=5`（total_count=4）→ 4 结果全录：ronaldowzy/price_forecast（12★·MIT·Python·pushed 2026-06·中国电力现货价格预测工具箱）/ZionLuo/Electricity-Price-Forecasting-with-Hybrid-Transformer（5★·license=null·2025-08）/hubianluanma/mac-power-monitor（2★·MIT·Mac 功耗面板分档电价展示）/yaolinderek-max/electricity-prices（0★·license=null·省级电价 tracker）。
- **候选（3 件=锚点源在册·观察位·非即装）**：①**AgentOps-AI/tokencost**（MIT·2,006★）——400+ LLM token 价格估算库→口径 A 外锚带化+云端 API 成本预估面候选；②**pydantic/genai-prices**（MIT·384★·pydantic 组织·pushed 当周）——同族第二源（组织信誉+最活跃）；③**dstackai/gpuhunt**（MPL-2.0·57★·pushed 当日）——云 GPU 租价聚合→自建 vs 云租对照锚点（赋能目录定价叙事「真算力」对照面）·**MPL-2.0=文件级 copyleft 注记：参考位（数据引用）合规·交付链集成须过许可复审门**。
- **五门评估（三件合评·锚点源定位）**：①契合 过=族 B 成本经济学 R- 件 Q3/Q5 外锚源位（口径 A 呈现/对照/预估面）·R-24「口径 A 禁入结算式」边界不变；②反重复 过=本司 Tools 实勘无 API 价格/云租价数据面（tiktoken=计数器非价格库·DeepSeek $0.15/1M=单点在册非库）=真缺口非双建；③许可 过（带注记）=tokencost/genai-prices MIT〔GitHub API spdx 字段 A 级·raw LICENSE 逐字直验=引入轮判据〕·gpuhunt MPL-2.0 参考位注记；④健康 过=三件全活跃（2,006★/pushed 2026-09-25/pushed 当日）；⑤成本/安全 过=纯本地估算零密钥面〔遥测注记随引入轮验〕。
- **结构性判负留痕（本线核心发现）**：**电价/折旧 OSS 数据线=结算面结构性判负**——R-20260928-compute-cost-economics Q3 在册铁律「电价=实缴电费单回填 ⬜ 唯一合法电价源·防估算污染」→ OSS 电价件（现货预测=交易侧非工商业目录电价/省级 tracker=0★ license null）**至多作对照参考位·永不入结算式**；折旧基准=财务/税法域锚点（R- 件已注记随凭证窗人工补核·GitHub 无可信开源折旧基准库如实）——**定谳=成本锚点源合法形态=口径 A 呈现/对照/预估面专用锚·口径 B 结算锚恒为凭证制**。
- **结论应用表**：tokencost+genai-prices=观察位锚点源在册（接入窗=云端成本归集轨预估面/口径 A 带化需求窗·引入轮判据预注册=raw LICENSE 直验+selftest+口径注记〔OSS 价格数据禁入结算式·R-24 同律〕）；gpuhunt=参考位（对照叙事面·集成须过 MPL 许可复审）；tensor-house/dao-code/awesome-hosting/llm-price-compass=④判负留痕（形态不契/2024 停推/清单面/9 月级 stale）；电价线 4 件+CloudGPU 后 3 件=④判负留痕（结构性判负/license null/低活跃/不契）——**首窗四切片毕（1=tiktoken 采用接入/2=PrismML fork 试验载具/3=mcp-cn-commerce 观察位接线候选/4=锚点源三候选在册）·首窗 09-29 21:40 自然关门·次窗指针随集团正典滚动**。
- 验证声明：本节 3 次外部请求（GitHub API search ×3·2026-09-28 23:1x +08:00·礼貌节流零翻页）。分级：搜索结果与许可证字段=A 级直采（GitHub 官方 API）；三候选五门=🟡 描述级+API 字段级判断（description/stars/pushed/license 面·未逐仓深审·深审留引入轮）；电价线判负=结构性判负（R- 件 Q3 铁律在册·非项目质量问题·如实分列）。本件落 cph4/oss-harvest/（D-20260927-03 同律·收账 commit 归收取轮）·T-20260927-26 行级更新随本司 commit。
