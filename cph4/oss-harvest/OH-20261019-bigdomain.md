# OH-20261019-bigdomain — OSS 借力第八窗切片件（BigDomain）

- **窗**：第八窗 2026-10-17 21:40 → 2026-10-20 21:40（P-2026-09-26-08+P-2026-09-28-01 承传·正典=cph4/oss-harvest.md）·交付 2026-10-19 ~05:3x-05:5x +08:00（窗开 ~55.9h 后·窗余 ~39.9h）·本件=72h 新鲜度点名面前置收口件（末片 OH-20261015-bigdomain.md 10-15 ~18:0x → 本片 10-19 05:3x=约 83.5h 超窗·值守夜报 72h 过期点名面前置应答·自领窗承传 R1757/R2000 先例）
- **过目面**（新到三切片全录·2026-10-19 05:2x-05:3x）：①OH-20261015-bigstream（漫剧/短剧部门窗·15 候选全 TTS/lip-sync/i2v 漫剧域=index-tts/GPT-SoVITS/LivePortrait/Wan2.1/LatentSync/MoneyPrinterTurbo 等·采用落点全 BigStream 漫剧线）=零 @BigDomain 候选零认领合法；②OH-20261016-biglife（BigLife 第四窗切片 1+2·jq 成本门判负 parked+Ollama harness 族 parked 维持+自建 update_status_export.py 通用续鲜工具采用）=零 @BigDomain 候选零认领合法（自建工具=BigLife export 面自有 schema·本司 export=F3 派生+自有续鲜机制·非强契合不认领）；③OH-20261016-cph4（radar §七 日扫首跑候选落库·mattpocock/skills+agency-agents 全 CPH4 智能体库映射+Strata=BigCompute 观察位+magpie=token 经济学实现维持+Ebony-Vinyl/dsh 判负合规红线件）=零 @BigDomain 强契合零认领合法——三片全他司域映射（R1154/R1155 先例口径·收益透镜照判均非商业化/增长域）
- **实搜面**（13 次外部请求全录·采时 2026-10-19 05:2x-05:3x +08:00·api.github.com 匿名直采通道〔search MCP 工具面 401 Bad credentials 凭据故障如实注·直采替代=R2000 先例口径同族〕）：
  - ①search_repositories MCP ×2（sensitive-word chinese filter / text moderation chinese）→ 401 Bad credentials（工具面凭据态故障·如实注·未重试硬闯）
  - ②api.github.com batch1 三查：`sensitive-word chinese stars:>400` → total=0（词组 AND 过窄如实注）；`text moderation stars:>1000 language:python` → total=0；`profanity filter stars:>500` → total=1（nyvorin/badwords 698★ MIT JS·英文 profanity 域外判负）
  - ③api.github.com batch2：`sensitive dfa stars:>300` → total=3：**houbb/sensitive-word 6078★ Apache-2.0 pushed 2026-03-23**（中文敏感词 DFA 正典件·繁简互换+全角半角+单词标签分类分级）+houbb/sensitive 713★（日志脱敏域外）+FireLustre/php-dfa-sensitive 756★（lic=null PHP 2022 停更判负）；其余四查（引号短语/中文关键词/topic/wordfilter）→ 请求故障（匿名 search 配额窗·如实注·降批重试）
  - ④api.github.com batch3：`sensitive word filter language:python stars:>100` → total=1（ML 教程件域外判负）；`textfilter stars:>100` → total=5：**toolgood/ToolGood.Words 5188★ Apache-2.0 pushed 2025-12-04**（高性能敏感词检测过滤组件·繁简互换+全角半角互换+汉字转拼音+模糊搜索）+observerss/textfilter 2110★（lic=null 2021 停更判负）+bosnzt/wordscheck 601★（lic=null 判负）+abelzhou/PHP-TrieTree 220★（MIT PHP 2021 停更判负）+toolgood/ToolGood.TextFilter 127★（GPL-3.0 系统件判负）；`moderation filter language:python stars:>400` → total=0
  - 反重复预检（仓内零外部请求·2026-10-19 05:2x 本轮）：①houbb 面=**已采用在册回访**（R837/R838·OH-20260102 窗 3 切片五门在案：词库数据面 65,143 行 verbatim+NOTICE+LICENSE-Apache-2.0 携带+wordlist.py 自写 trie 匹配器在役+R1155 pyahocorasick 评测先例——本轮 6078★/活跃面再证=canonical 地位回访维持·非新发现如实注·slice6/7 真钥双接线指针中的「houbb 词库」同源件）；②toolgood 面=三面查证 CLEAN（cph4/oss-harvest 全目录 grep「ToolGood|toolgood」零命中+cph4/README 能力注册表零命中+司内 src/docs 零命中）
- **候选**：toolgood/ToolGood.Words（https://github.com/toolgood/ToolGood.Words · Apache-2.0（API 直验） · 5188★ · pushed 2025-12-04〔近月活跃线内〕· 契合点=中文敏感词检测过滤的**变体归一预处理工艺**〔繁简互换+全角半角互换+汉字转拼音+模糊搜索〕——本司 L1 本地预筛现役面=wordlist.py 自写贪心 trie 裸文本扫描（R838 接线·OH-20260102 词库数据面）·变体逃逸对抗（繁简混写/全半角混写/拼音替代）=已识别工艺空白·L2 msgSecCheck 真接线前 L1 单层防御纵深补强参照）
- **采用→落点**：零入池零直采——**学实现参照位登记 1 件**（ToolGood.Words·类型=学实现·C# 库本体零采用=Python 栈零引入纪律同 houbb Java 本体不采用先例）→落点=司级登记簿（七）行+消费窗=P-47③ UGC+msgSecCheck 管道 spec 升版窗（变体归一预处理层设计参照·工艺借鉴零代码搬运）；收益透镜（P-2026-10-04-02 §六）=设计件质量型·预注册降级条件=P-47③ 面无升版动作则参照位降级观察位
- **parked+理由**：slice7 五指针全维持 gated（①真钥双接线 wechatpayv3+houbb 词库=CEO 物理件真钥到位即燃·三前置已备｜②granian 接线轮=bootstrap 启动触发｜③pycrdt 接线 B/C/E=接线窗触发〔前置 A+D 已闭环 R1847〕｜④观测线=bootstrap 期启动前再评｜⑤skill-suite=bootstrap 触发+90 天停滞判负条件在册）+本轮零新 parked（Python 族判负四件全带理由：observerss/textfilter lic-null 停更·bosnzt/wordscheck lic-null·FireLustre lic-null 停更·abelzhou 停更低星；**Python+许可+活跃三角=零候选真空白确认**→本司自建路线维持背书〔R838 自写 trie 在役·CEO 轮子律履约链完整：先搜→判负留痕→自建合法〕）
- **下窗指针**：第九窗 10-20 21:40→10-23 21:40·下次 72h 到期=10-22 ~05:3x（本片后 72h）·线索=①维持 gated 五指针②P-47③ spec 升版窗=ToolGood 参照消费时点③核心域④新实搜角（AIGC 合规工具链方向·承 slice7 下窗指针）

## 一 五门评估（学实现参照件：toolgood/ToolGood.Words）

| 门 | 判定 | 证据 |
|---|---|---|
| 1 契合 | 过（参照级） | P-47③ 管道设计件工艺参照=真需求面（L1 变体归一空白已识别·L2 真接线前防御纵深）；**保留注记**=参照级非接线级（C# 本体零采用·工艺借鉴面） |
| 2 反重复 | 过 | 三面查证 CLEAN（cph4/oss-harvest 全目录+cph4/README 能力注册表+司内 src/docs grep 零命中）；与在册 houbb 件正交（houbb=词库数据面已采用·ToolGood=归一工艺参照面·非同面重复） |
| 3 许可 | 过 | API 直验 Apache-2.0（学实现参照面零代码搬运·许可面仅为登记完备性注记） |
| 4 健康 | 过 | 5188★·pushed 2025-12-04（近月活跃线内）·非 archived |
| 5 成本/安全 | 过 | 参照件零接入零遥测零密钥（工艺知识面非 CPE 非 SaaS）；三问门未涉（零新 API 接入·api.github.com 匿名直采=既有先例通道） |

## 二 结论应用表（research-protocol §二.1 落点强制·无表=未交付）

| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| houbb/sensitive-word（6078★ 回访） | 已采用在册维持（R837/R838 词库数据面在役·本轮 canonical 地位再证） | 已闭环（回访维持） |
| toolgood/ToolGood.Words（学实现参照） | 司级登记簿（七）行+P-47③ spec 升版窗消费（变体归一预处理工艺参照） | 参照位在册 |
| Python 族候选（observerss/textfilter 等） | 诚实判负零候选（lic-null/停更/域外·三查全不过） | 已留册（真空白确认→自建路线维持） |
| 过目面三切片（bigstream/biglife/cph4） | 零 @BigDomain 强契合零认领（全他司域映射·R1154/R1155 先例口径） | 已留册 |
| slice7 五指针（真钥/granian/pycrdt B-C-E/观测线/skill-suite） | ③门控留置（维持·触发条件不变） | 已闭环 |
