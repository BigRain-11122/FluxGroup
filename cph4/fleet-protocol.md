# Fleet-Protocol — 集团机队协议共享层 v1.0（CPH4 Labs）

> 溯源：governance §6 第 11 条（T2·否决窗至 2026-10-01·组织审计 G7 判决配套）+ ledger P-63③（CEO 令 09-24「全面开工」即时律）。
> 定位：**心跳/任务认领/传输三条款的集团共享正典**——BigMoney fleet v1.0 与 Biggame 08 号同构归一；共享的是结构不是细节，两司改指针引用随回执（P-51 送达判据）。细节归各司协议（引用不复制）。
> 关系：本件=三条款结构+推送声明+借算补法；`fleet-allocations.md`=配置分配/借池/台账旗标；`scheduling.md`=在哪跑；`cadence.md`=何时跑；`onboarding.md`=新机部署三层模型。重叠立法禁。

## 〇、一句话

**心跳各自写全队读、认领 commit 即锁、传输 git 唯一通道——三条款集团同构；推送策略司自决保留（两边实战淬炼，仓库冲突面不同，禁互换强归一）。**

## 一、三条款（集团同构·两司机队既有实践的归一，非新法）

1. **心跳条款**：每机**只写自己的心跳文件**（BigMoney=`fleet/machines/<id>.json`·Biggame=`Design/configs/GLOBAL/fleet/<id>.json`），写权分治=零跨机合并冲突；git 同步=全机队只读互见（governance §6 资源互见）。共享最低字段=`last_seen`+资源余量（RAM/GPU）+`verdict`+在途任务；**verdict=INFO 判定非门禁**（语义司自定·须成文于司协议·`|RAM_LOW` 低内存后缀同构）；集团旗标与失联处置=`fleet-allocations.md` §五（GREEN-IDLE/YELLOW-HEAVY/STALE/OFFLINE·夜轮审计）。**身份文件（machine.json）=本机私有永不入库**（X104/#48：tracked 身份必被跨机合并静默覆写）。
2. **任务认领条款**：任务单=结构化文件落 git；**认领=改 `status=claimed`+`claimed_by`+`claimed_at` 并 commit push——commit 即锁**（U067 同制）；两机同窗撞认领=行级手术按 commit 时间序**后到让路**（排序权威=git %ci）；超时释放（默认 24h·司可调须成文）；**failed 必写死因；done 必带 `result_ref`**（指向产物）。共享核心六字段=`id/priority/status/claimed_by/claimed_at/result_ref`（司可扩禁减）；同款/同车道双开=事故（仲裁=司登记簿或任务板唯一面）。
3. **传输条款**：跨机传输**唯一合法通道=git clone**（禁文件夹直拷——防锁文件/临时态/被忽略物·两司同源铁律）；大资产=司自建通道选型矩阵（范式=BigMoney `fleet/TRANSFER.md`：A git 分批/B2 croc 直传/B1 组网/C 云中转/D 离线+保险丝+决策顺序）。集团强制最低线三条：①**交付判据=校验锚点双侧一致**（manifest/字节数/文件数——无校验不算 done）；②**收件 `git checkout <分支> -- <path>` 后必 `git restore --staged <path>`**（R90 收件腿坑律：checkout 会把 gitignored 件自动 STAGE 进 main index）；③**常驻网络服务装机=CEO/用户逐次授权**（安全红线·两司同源）。

## 二、推送策略=司自决保留

- 现行两制：BigMoney=**X128-lite**（直推 main→被拒 `pull --rebase` 一次→machine/<id> 兜底）；Biggame=**X128 机器分支制**（B/C/D 推 machine/<id>·A 机 :13 fold 收口=master 唯一写手·merge 优于 rebase 坑#45 定案）——仓库冲突面不同，**禁互换禁强归一**。
- 集团统摄不变（versioning §5）：**禁 force-push**（例外仅新仓 stub 覆推 --force-with-lease+记档）；凭证/密钥永不入库；push 失败禁无限重试（挂起+轮报告）。
- 新司接入=两制任选或自定，**推送策略声明必写入本司协议头部**（小队直推宜 X128-lite·多机常撞面宜 X128）。

## 三、借算三缺口补法（fleet-allocations 扩法·G7 判决配套）

1. **fleet-audit 心跳源开闭原则**：新司机队心跳上线=`Tools/fleet-audit.ps1` **加一个源行**（零改主逻辑·探针插件同构）——新司接入清单必含此步；未加源行=该司机队对集团审计面不可见。
2. **跨司借算工单规范**（fleet-allocations §二 扩法）：跨司借算一律**走被借方机队协议认领**（保主律·借方协议优先）；工单五字段强制=`借出方司/借入方司/机器id/归还判据/超时`；归还判据=产出回流 git+**批末当场清本地临时件**（权威副本唯一=git 库内）；护栏三条=借算不抢主归属高优（优先级降档/释放阀让路）+同 stem/同任务禁双机双产+借算域禁入对方核心写域。范式=fleet §5 借算+08 号 §7.9（🤝借算@机id 标记→闲机认领→git 回流→当场清理）。
3. **机×司占用矩阵**：周轮资源节呈现每机一行——`主归属司(保主)｜借入作业(司/任务)｜空闲旗标`；数据源=各司心跳+任务单（fleet-audit 聚合底账）；判据=接入借池的每机可在此矩阵读出「谁在用/谁借了/闲多少」。

## 四、新司机队接入面（集团级顺序·细节归司）

①司协议落位（三条款结构+推送策略声明+verdict 语义成文）→②机器接入走 `cph4/onboarding.md` 三层模型→③心跳落位（§一.1）→④`fleet-allocations.md` §一表加行（主归属/兼任/可借状态）→⑤fleet-audit 加源行（§三.1）→⑥首单派工（clone 完成即有活干不空转）→⑦新机 48h 内交首条接入踩坑记录（U039 义务制·落司机队经验面）。验收门范式=BigMoney `fleet/EXPANSION_ACCEPTANCE.md` §6（smoke+心跳+循环注册+首单七门）；双角色机参照其 §3 身份模板（`main_owner` 保主）。

## 五、接线

- governance §6 第 11 条「建立中」→v1.0 已建（本批）+changelog 行；cph4/README 注册表行+AI.md 调度行+ledger P-63③ 交付注记。
- **转办 @BigMoney+@Biggame**：各自协议头部加指针引用本件（内容不重写·随回执销单）——夜轮催办口径沿 P-63 转办列。
- 借算缺口②③ 的实施件（fleet-audit 源行随新司接入滚动；周轮资源节矩阵模板）=周轮立法流程自领（本件只立 spec 禁自建工具）。

### Changelog
- 2026-09-24: v1.0 首版（P-63③ CPH4 自领交付：BigMoney fleet v1.0〔README/FLEET-OPS/TRANSFER/EXPANSION_ACCEPTANCE〕+Biggame 08 号 V1.2 三条款同构归一+推送司自决注记+借算三缺口补法 spec）。
