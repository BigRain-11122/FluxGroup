# Versioning — 集团 git 版本与分支治理（CPH4 Labs）

> CEO 令（2026-09-23 原话）：「建立git顶层版本和分支设计，做好规划，做好万全又合适的准备，把涉及的机制都梳理一次。」
> 立法级=T2 机制（AI 直接落地·否决窗 7 天至 2026-09-30·CEO 随时否决，git 即回滚）。
> 立法原则：不重复立法——既有 git 相关法条（governance §6 并发纪律 / FLEET-OPS 控制面 / evolution §5 / retention 水位律）全部引用统摄，本件只立**缺口**：主干正典、分支模型、版本模型、保护与回滚、新仓接线。

## 1. 仓拓扑与主干正典（2026-09-23 实测）

| 仓 | 主干 | tag 现状 | remote | 备注 |
|---|---|---|---|---|
| FluxGroup（HQ） | main | 0→本件点火 | ✅ FluxGroup.git | 治理层·低频变更 |
| MiniGame | master | 51（G 系） | ✅ MiniGame.git | **存续豁免**（§1.3） |
| BigMoney | main | 0 | ✅ BigMoney.git | 双机同推主干 |
| BigStream | main | 0 | ✅ Bigmedia.git（仓名待裁） | OSLoop 在跑 |
| FluxVerse | main | 0 | ❌ 待 CEO 建 | DevLoop+Tick 双循环 |
| BigDomain | main（本日 master→main 已对齐） | 0 | ❌ 待 CEO 建 | root 1 commit·零迁移成本窗口执行 |

### 1.1 主干名正典
- **新仓一律 `main`**；开线五步第 3 步（配 remote）前后即须对齐。
- 存量仓改名=拓扑迁移工程，**默认不做**（见 §8 待裁），本日 BigDomain 是唯一例外（1-commit 本地仓、无 remote、无循环引用，零风险窗口）。

### 1.2 多机同主干
- 机队多机（bm-a/bm-b）共推同一 main=正典形态：git 是唯一真源，冲突靠 §4 协议消化，不开机器长分支。

### 1.3 存续豁免（grandfathered，同 RULES §2 legacy exception 范式）
- MiniGame `master` + `backup-prepush-*` 两分支 + 51 枚 G 系 tag 全部存续——19 任务群+08 号多机引用其主干名，强迁风险>收益；迁移提案见 §8。

## 2. 分支模型：trunk-based 主干开发

**选型理由**：集团现实=AI 多执行体无人值守 10 分钟轮直推主干+小步快提交+多机同推——实测健康；git-flow 类常驻分支层会制造 rebase 风暴与合并债务，毁无人值守节律。**分支是例外，不是默认。**

- **唯一长期分支 = 主干**（main/存续 master）。一切日常开发直推。
- 合法分支四类（开前自问：不开行不行？默认答案=行）：

| 类型 | 命名 | 判据（何时才许开） | 生命周期 |
|---|---|---|---|
| 集成面 | `integration/*` | P1 级大改（CEO 署名件）连续多轮会污染主干 | 合并即删 |
| 备份面 | `backup/*` | 推仓前一次性快照（MiniGame `backup-prepush-*` 范式正典化） | 30 天清理（retention 接线） |
| 机器面 | 按 Biggame 08 号自治（X128 机器分支） | B/C 机协议域——**引用不复制** | 其自治理 |
| 试验面 | `exp/*` | 探索/生成对照面 | 当日-当周收口，结论回主干或废弃 |

- **分支纪律**：merged 即删；**分支禁当任务台账**（任务面已有 fleet/tasks、evolution 台账、U 号登记簿——用分支管任务=双台账违规）；单仓非主干活跃分支 ≤8，超限夜轮点名；分支上同禁长期持脏。
- **未入正典的一切分支形态**（develop/release/hotfix 常驻层）=不采用。

## 3. 版本模型：scope 前缀 + semver + tag 档案律

### 3.1 tag 格式正典
`<scope>/vX.Y.Z[+buildN]` —— MiniGame `G04/v2.1.0+build1` 先例升格集团法。
- **scope = 登记制命名空间**，当前三类：产品/组件号（G04、P06…各司自治注册）· 里程碑号（FluxVerse `M1/v1.0`…对应大脑开发度路线图）· 治理号（HQ `gov/vX.Y`）。
- **semver 语义**：MAJOR=宪法级/里程碑级/破坏性改动；MINOR=新机制新能力；PATCH=修正；`+buildN`=同版本多次构建。

### 3.2 打点规则（何时打 tag）
| 面 | 打点节律 | 例子 |
|---|---|---|
| HQ 治理层 | **每次 T0/T1 立法落地**打 `gov/vX.Y` | 本批=`gov/v1.0`（2026-09-23 治理件齐备锚：CEO 复查/回滚/引用的定位锚） |
| FluxVerse | **每 M 档达成**打 `M<x>/v1.0` | M1 判据过=打（CityWatch milestones.json 与建设进度面对应） |
| 产品仓 | 各司门禁节奏自治 | MiniGame G 系 tag=范式，BigMoney/BigStream 按其 PLAN 自定 |

### 3.3 tag 档案律（不可变）
- tag=R1 活账本（档案），**打上即冻结，禁移动重指向**；须改=删旧打新+该司台账记档。
- tag 随 push 同步上云（`git push --tags` 或显式推 tag）——云端备份三级模型适用于 tag 面。

### 3.4 发布锚律
- **对外发布物（游戏端/产品端/SaaS 版本）必须先有 tag**——任何对外状态可定位到唯一 commit（诚实律「宣称←证据指针」在发布面的形态）；无 tag 的对外发布=不可追溯=禁。
- 发布物本身（安装包/小程序包/产物归档）管理=各司自治；集团只统摄「tag 先于发布」这一条。MiniGame G 系 tag=既有范式。

## 4. 同步与并发协议（统摄引用·不另立）
- **git=唯一真源**；GitHub 私库=持续增量云备份（FLEET-OPS 三级模型）。
- 节律：交互会话开工 fetch/收工即推；无人值守轮 10min `pull→干活→定向 add→commit→push`。
- **push 被拒律（X128-lite 集团版）**：`pull --rebase` 重试一次，再拒=本轮顺延让路——禁强推解决（evolution §5 先例升格全集团）。
- 脏树纪律、行级追加面、撞写让路、单仓单执行体：全按 `governance.md` §6 执行（引用不复制）。
- `.git` 水位：单仓 2GB 触发 `git gc`（只压不删）——`retention.md` §4.2。

### 4.1 提交者身份律（产权/执行两层分离·2026-09-23 实测立法）
- **author 层=所有者身份**：全机队全局 `user.name=junsheng.sun` / `user.email=junsheng.sun@unity.cn`（集团产权归属；新机=bootstrap P3 相写入全局身份；仓库级 override=公司自治存续面不强制，如 MiniGame `sjs20`）。
- **机器归属层=commit 尾标**：无人值守轮 commit 信息尾部必带 `[via <机器代号>]`（bm-a/bm-b/BG-A/BG-B/BG-C——fleet 令签名 `via <bm-x>` 先例升格）；交互会话推荐携带。编年史（城市档案库）靠尾标回答「哪台机器人干的」。
- 存量异机对齐=进化台账 P-23 转办（各司循环自领 mandate 尾标纪律+身份对账）。

### 4.2 密钥泄露机核（governance §7 安全律的第二道防线补缺）
- **`Tools/secret-scan.ps1`**：扫近 N 天（默认 1）各仓 commit diff 的高危密钥模式（API key/私钥块/授权码——P-01 SMTP 授权码入史案为实证教训），报告落 `.codely-cli/secret-scan/`（gitignored·防报告自膨）；夜轮感知面接线（night-round-prompt ①）。
- 命中分级：P0 高置信模式（AWS key/GitHub PAT/私钥块）=立即台账记档+按泄露流程（轮换+留档·FLEET-OPS L54 同源）；低置信=周轮复核。**执行侧不得自证无泄露——扫出来才算数**（诚实律 10.3 门禁机核）。

### 4.3 提交消息规范（CEO 令 2026-09-24「从顶层开始梳理git提交规范和版本分支控制」·2026-09-24 实测锚：FluxVerse 均值 1989/max 3709 字符=token 重灾区·其余五仓 85-219 健康·via 尾标 9/10）

**四层结构正典**（一条 commit=一个意图+一层溯源+克制要点+一个尾标）：

```
<标题：意图一句话 ≤50字>（<溯源指针>）：①<要点> ②<要点> [via <机器代号>]
```

1. **溯源指针制**：`CEO 令 09-23 23:15`（日期时间→orders 台账行定位）/ `P-<号>`（ledger 提案）/ `T2`（分级立法权）——**禁在 commit 消息复述 CEO 原话全文**（原话唯一存储面=orders 台账；govscale 复述禁令同源——commit 是检索锚不是复读机）。
2. **长度水位三档**：标题 ≤50 字 · 要点正文 ≤200 字 · **硬顶 500 字符**；超限=详情落正典件/research/台账，commit 只留指针。**git log 是新会话必读面——长 commit=向全体执行体征 token 税**（CEO 令「文本读一次多少 token 谁受得了」在 git 面的形态）。
3. **原子律**：一 commit 一意图，跨主题混合=违规（小步快提交的语义面）。
4. **语言与各司适配**：中文正典（集团先例固化）；**各司依据自己业务特点优化后执行**（CEO 令 2026-09-24）——保底三条不可低于：①溯源可定位（指针制——各司用自己的台账号：Biggame=U 号/X 批号·BigMoney=fleet O 号/任务单·BigStream=R 轮次号·BigLife=T 单号·FluxVerse=P 号/R- 号，皆天然指针源）；②`[via <机器>]` 尾标；③500 字符硬顶。适配自由面=要点格式/编号引用惯例/轮式细节——各司把适配结论落自己章程或 mandate 一行（自领后夜轮消点）；只许更克制不许更松（governance §1 铁律 3 同源）。
5. **自动化轮式**：`<轮名> <日期>: <一句话>`（夜轮先例）——轮产出详情落台账不进 commit。
6. **执法面**：超 500 硬顶=周进化轮抽审点名（诚实律扫描附带·不建新工具）；与治理层 v2（R-20260923-02c 登记处迁移）同向——登记处落地后溯源指针升级为 `orders.jsonl 行号`，结构不变。

**三面速查**：分支=trunk-based 主干开发（分支是例外四类§2）｜版本=`<scope>/vX.Y.Z` tag 档案律（§3）｜提交=四层结构+500 硬顶+指针溯源（§4.3）。

## 5. 保护与回滚

- **禁 force-push**（FLEET-OPS 先例升格集团律）。例外面唯一：新仓 remote 含自动 init stub 的首推，须 `--force-with-lease`+台账记档（FluxVerse 分发监听器先例）。
- **历史保全律**：已进公共历史（已 push）的 commit 禁 reset/rebase 改写；**回滚一律 revert 追加式**——git=城市编年史档案库（BLUEPRINT L1 塔基世界观），只增史不改史；本条与「集团永不删子公司历史」（governance §3）同源。
- **revert 权限分级**：AI 执行体 revert 自己本轮错件=T2 域内自由；跨域/跨天/可能吞他人在途=违规，走提案或 CEO；治理件大回滚=CEO 一句话（「git 秒回滚」承诺的操作面=按 tag `gov/vX.Y` 定位+revert）。
- 未 push 的本地 commit=私有面，reset 自由。
- 删仓/删历史=CEO 保留类。

## 6. 新仓 / 新远端接入 checklist（待 CEO 建 remote 两件的接线预案）

1. 仓内主干=main（§1）；2. `git remote add origin git@github.com:BigRain-11122/<Repo>.git`；3. 首推 `git push -u origin main`（remote 带 stub init→按 §5 例外面覆推+记档）；4. GitHub 默认分支确认=main；5. governance §2 登记簿 onboarding→active+changelog；6. 新机 clone 冒烟（`bootstrap-machine.ps1` P2 相）。
- **待 CEO 物理件两件**（建仓参数：Owner=BigRain-11122 · 名=FluxVerse / BigDomain · Private · 不勾 README 自动初始化）：FluxVerse（remote 已配置待远端存在）/ BigDomain（remote 未配置）。

## 7. 机制交互全景（CEO 令「涉及的机制都梳理一次」·git 面一览）

| 机制 | 节律 | git 动作面 | 法条出处 | 本件增补 |
|---|---|---|---|---|
| 交互会话（CEO 对话窗） | 即时 | 开工 fetch→小步快提交→收工即推 | governance §6.1 | 按原样 |
| 各司 OS 循环（Bigmoney/BigStream-OSLoop/MiniGame 群） | 10min | pull→定向 add→commit push | FLEET-OPS L8 | 轮末 push 含 tag 同步（有 tag 时） |
| 集团周轮 EvolutionTick | 周日 09:17 | 同上+提案转办只读产品仓 | evolution §5 | X128-lite 升格统摄（§4） |
| 集团夜轮 NightRound | 每日 03:07 | 同上+残留分支点名 | evolution §1 | **新增感知项：非主干分支>30 天/超水位点名** |
| FluxVerseTick / DevLoop | 10min | scan 只读+轮末推送 | TECH/iteration_loop | 按原样 |
| 机队多机同仓 | 随各轮 | 多写者同推 main | FLEET-OPS | §1.2/§4 统摄 |
| 新机部署 bootstrap | 一次性 | clone→拉仓→任务注册 | onboarding.md | P2 相+§6 冒烟 |
| CityWatch 观城台 | 双击 | 只读 git log/commits 面 | watch 件 | 里程碑面可消费 tag（§3.2） |
| 诚实律三防线 | 轮内/门禁/周审 | 证据=commit sha | governance §10 | tag 面=档案证据（§3.3） |
| 开线/收线五步 | 事件式 | gitignore 隔离+登记簿 | governance §3 | 开线即对齐 §1 主干正典 |
| 退役机器 | 事件式 | GitHub 撤钥匙=唯一真断权 | FLEET-OPS L24 | 按原样 |
| retention 水位 | 周测 | .git 2GB gc 只压不删 | retention §4.2 | backup/* 30 天并入其清理面 |

## 8. 执行面与待办

- **2026-09-23 第一批已执行**：①BigDomain master→main（e3a08ed 历史完好验证✓）；②HQ 首个治理 tag `gov/v1.0`。
- **2026-09-23 第二批已执行（本批·CEO 令「还有什么相关要建立的，统一这次搞定顶层设计」）**：③发布锚律+身份律+密钥机核立法（§3.4/§4.1/§4.2）；④`Tools/secret-scan.ps1` 落地实测；⑤bootstrap P3 相写全局 git 身份；⑥夜轮感知面接 secret-scan；⑦ledger P-23 转办异机身份对齐。
- **待 CEO 物理件**：①FluxVerse / BigDomain 建 remote（§6 参数）；②GitHub 各仓开 branch protection（Settings→Branches→main/master：Block force pushes + 禁删主干——把 §5 禁 force-push 从纪律升为远端机核，每仓 2 分钟）。
- **待 CEO 一句话裁（均有默认）**：①MiniGame master→main 迁移（**默认不动**·存续豁免覆盖）；②**GitHub org vs 个人账号**（**默认维持 BigRain-11122 个人账号**；org 迁移=BigDomain B 端入驻/参观端公众面上线前的一次性工程——涉全机队 deploy key 重授权，届时再裁）；③**HQ 第二远端镜像**（**默认不开**·FLEET-OPS 先例；一句话开=CEO 建 mirror 私库+夜轮加 push --mirror 一行）。
- **悬置件照旧**（不重复列）：Bigmedia 仓名正典（orders.md 17:50 行）。
