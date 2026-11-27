# R-20260924-server-city · 服务器端技术·硅基生命体城市运行适配架构件

> 溯源：CEO 令 2026-09-24 ~15:00「实验室开始进行服务器端技术，适配我的硅基生命体城市运行」。
> 定位：infra-6 自建建造书的**城市运行增补件**——商业承载七件之外，把硅基生命体城市（FluxVerse+BigLife 人口层+BigDomain 共创面）的公共运行面纳入同一自建后端。栈/安全治理/时间线全部沿 infra-6 不重立，本件只补「城市面」。
> 分工不变：实验室=本件+bootstrap 扩展；BigDomain=API 承建；BigLife=census 公开面定稿；FluxVerse=公开快照导出件；CEO=物理件四件（infra-6 §0）。

## §0 边界与三律（服务器律 v2 对齐版·T2·2026-09-24 零服务器死命令废止后改写）

**城市两分法**（依据=服务器律 v2 必要性闸·server-governance §〇.1/§七.1）：城市大脑（内部运转面=world-events 装配/scan/探针/tick/机队/git 流）=bm-a 本地维持——**技术最优+最简形态选择，非法律禁令**（迁移须过必要性闸+真实收益证据一行）；城市公面（参观端只读面/大厅/census 公开查询/居民之声投喂/共创化身注册/用户行为回流）=server 新承载对象（已过必要性闸=infra-6+本件立项依据）。

**三律**（结构性实现见 §2/§6）：
1. **服务器禁写 world/**——单写者律延续（P-43 案 2：唯一写者=bm-a scan）。结构性保证=容器对城市数据挂载 `:ro`。
2. **数据入服走 git 只读通道**——本地生成→push→server 定时 pull。服务器零新增采集、零探针（时间/天气等 L0 现实链接数据从公开快照包读取，数据同源单一真相，探针仍是 bm-a 内部面功能）。
3. **回城走摘要 inbox**——用户公共面行为=公共面事件方言（六字段+evt_id·R-2 §4 P3）增量 inbox 文件→bm-a 轮拉→scan 合并；禁内容载荷（脱敏律不变）。

内部面迁移按服务器律 v2 §七.1（原「永禁迁上」条款已随死命令废止——允许但默认不迁·localhost 仍是最简形态）；泄密红线+**界面敏感面律**（金融视觉面永不出任何用户界面）适用于参观端全部呈现面。

## §1 城市运行面盘点（server 承载六面·数据源全部现成）

| # | 面 | 数据源（现成件） | server 行为 | 承建 |
|---|---|---|---|---|
| 1 | 参观端实况只读 | 城市公开快照包 world-public/（**新导出件**·白名单脱敏版 state 子集+events 尾摘要·tick 轮末产出）+ world-events 日档案（T+1 编年史·P-43 已定入 git） | read API 投喂白名单字段 | FluxVerse 导出+BigDomain API |
| 2 | census 户籍查询 | BigLife `census/export/citizens-light.jsonl`（万行·~6MB·schema 见 §4） | 导入 SQLite+查询 API | BigLife 定稿+BigDomain API |
| 3 | 居民之声 | BigLife `cognition/pools.json`（648 条确定性台词池）+spotlight 预生成件 | 只读投喂（**零 LLM on server**） | BigLife 供件 |
| 4 | 大厅聊天（脑环广场意象） | — | WebSocket 房间（infra-6 §2 既有·P-47-1 规格已开写） | BigDomain |
| 5 | 共创化身注册 | BigLife T-04 受理程序+census 注册面（BigDomain BLUEPRINT「用户入城即硅基生命」） | intake→inbox→BigLife 受理 | BigDomain+BigLife |
| 6 | 用户行为回流入城 | 公共面事件方言 | 每日 jsonl 导出+增量 inbox 双轨（infra-6 §2 既有） | BigDomain+bm-a scan |

CityWatch（本机观城台）维持现役不动——参观端=CityWatch 的公网脱敏姊妹面，非替代。

## §2 数据流（单向双通道·ascii）

```
[城→服 只读通道]  bm-a 生成 world-public/ 快照包+日档案+census/pools（git push·每轮/每日）
                       → server cron 每 10min git pull --ff-only（双仓 read-only clone·deploy key 走 /etc/fluxvault）
                       → /data/city/（容器挂载 :ro）→ 参观 API 只读投喂
[服→城 回流通道]  用户行为摘要（api append inbox.jsonl·六字段+evt_id）
                       → bm-a 10min 轮拉 → scan 合并装配单流（P-43 案 2 机制原样）
                       → 尾延迟 ≤10-20min（与机队通信 SLA 同量级）
```

**近实时设计**：公开快照包=tick 轮末（10min）产出→server pull→参观端延迟 ≤20min——异步生活感合规（实时同屏 MMO 仍禁·BLUEPRINT 诚实边界不变）。

## §3 智能层适配（零 token 服务器律）

- 2C2G 无 GPU→**server 永禁跑 LLM**（qwen2.5:7b 需 5GB+ RAM·诚实排除）。
- 居民智能全走「**本地生成→git→server 只读投喂**」：台词池 648 条情境抽词（确定性零 LLM）/spotlight 事实级/census brain_digest——全部现成件，server 端零 token 零 API。
- 实时对话（点居民问答）=Phase 3 后路：云端 API 留痕+CEO 授权（token-economy 三问门）；bm-a 代理通道=内部面暴露**否决**。
- 诚实边界：参观端 v1=异步生活感（池+digest+快照），不宣称实时智能。

## §4 census 公开面白名单（初版·@BigLife 定稿·T-04 同线）

- **公开字段**：id/name/species/faction/gender/age/district/block/profession/creed/brain_digest/behavior_hint
- **初版排除**：recent_ring/recent_ring_date（私生活年轮细节·留点选深水区）·hook（叙事深水区留参观端 v2）
- 荣誉市民席 C-00001~09=CEO 保留席：空席零渲染（人设权红线）。
- 泄密红线核：census 本身零策略/零盈亏/零机队面——白名单仅是纵深防御。

## §5 资源包络（2核2G 起步档诚实预算表）

| 项 | 预算 | 说明 |
|---|---|---|
| 系统+docker | ~500MB | Ubuntu LTS 基线 |
| nginx | ~30MB | TLS 终结+静态+反代 |
| api（FastAPI） | ~300MB | 城市+商业同一进程（nginx 路由 /city/*→api·零新服务） |
| SQLite 页缓存 | ~200MB | WAL·单写者 |
| 余量 | ~1GB | cron pull+突发 |
| 数据件 | <15MB 常驻 | census 6MB+快照包 <1MB+日档案按日 150-400KB |

- 大厅=百人级单机（infra-6 既有判据）；CPU 峰值面=WebSocket 广播+查询。
- **升配触发判据不变**：大厅并发>500 或 CPU 均值>60% 持续一周→2核4G 1020 元/年档。
- 备案期（无域名）：IP+自签内网试运行城市 read 面（infra-6 §3.1 同款）。

## §6 bootstrap-server.sh city 扩展（批 2·IaC 已随本批落·待服务器到位首验）

1. compose：api 服务增挂载 `/opt/fluxcity:/data/city:ro`（**结构性单写者**：城市数据只读进容器）。
2. 新增 `citysync` 块：双仓 read-only clone 目录 `/opt/fluxcity/{fluxverse,biglife}` + cron `*/10 git pull --ff-only`；首次 clone 前置=deploy key 入 `/etc/fluxvault`（密钥律·server-governance §二）——bootstrap 只备目录+cron 骨架，clone 步=runbook 手动段（key 物理件就位后）。
3. nginx 零改动（api 统一路由）；探针/监控面零新增（infra-6 §4 照旧）。

## §7 转办面（ledger P-2026-09-24-52）

- **@BigDomain**：P-47 五件规格**吸收城市运行面**——参观 read API/census 查询/化身注册 intake 并入既有 AC（大厅规格已开写·顺延吸收·勿另起炉灶）。
- **@BigLife**：census 公开白名单定稿（§4 初版→定稿·T-04 受理程序接化身注册 intake）。
- **@FluxVerse-DevLoop**：tick 轮末**城市公开快照导出步**（world-public/ 白名单包·P-22 人口面板/CityWatch v2 同线消费）——判据=导出件过 secret-scan+白名单字段断言+禁词扫描（密钥/盈亏绝对值/策略细节/金融行情）。
- **@CPH4 本批直办**：bootstrap citysync 扩展（§6·本批已落）+本件。

## §8 判据预注册（沙箱可验先行·服务器到位补全）

| AC | 判据 | 可验时点 |
|---|---|---|
| AC-1 | `bash -n` + `docker compose config` 语法过 | 本批 |
| AC-2 | 沙箱（bm-a docker）：census 万行导入查询 p95<100ms；快照读<50ms；大厅 100 mock 并发 5min 稳定 0 drop | 服务器到位前（BigDomain 沙箱） |
| AC-3 | 城市数据挂载 `:ro` 实证（容器内写试→EACCES） | 部署日 |
| AC-4 | 回流件过 world verify（六字段+evt_id·scan 合并零坏行） | 沙箱+部署 |
| AC-5 | 公开面 secret-scan=0 P0+白名单字段断言+禁词扫描 0 命中 | 每导出轮+部署 |
| AC-6 | bootstrap 幂等重跑+15min 重建演练 | 部署日（infra-6 既有） |

## §9 待 CEO 裁/物理件（不催·现状一行）

服务器到位→`bootstrap --baseline-only`→city 扩展启用（备案期 IP 试运行）→备案过→公网试运行→**参观端开门=CEO 令**（M4 合规三件套+AIGC 标识前置）；实时 LLM 后路=CEO 授权过三问门；升配=判据触发呈报。物理件四件不变（购机/域名/备案/商户号）。
