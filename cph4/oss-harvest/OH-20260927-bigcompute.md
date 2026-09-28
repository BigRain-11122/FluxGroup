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
