# bm-a 降位执行位 + KF 模板主语误绑（2026-10-20）

> L2 主题记忆。因 project-scope `append_memory` 在本机 EEXIST 故障（在册判例），本条暂以独立主题文落盘；待工具修复后由 L1 索引补挂。

## 一、bm-a 降位（CEO 令 2026-10-20 18:3x）

**原话**：「全部提交git或者看怎么处理，以后这台机器不作为主力机了，只能远端提单子过来帮忙本地跑跑」。

- **新定位**：远端提单执行位。不再自称主控、不再自派产线、不做主力生产。
- **票据制**：唯一入单口 `cph4/fleet/inbox/MSG-<HHMM>-bm-a-<topic>.md`；每票必含产出物 / 验收判据 / 输入路径 / 时限 / 失败回退；回执 `RCPT-<HHMM>-bm-a-<topic>.md`；**无票不做**。
- **存量职责如实未停**（停=断供）：NATS 心跳面、FleetLink、CEO-PROXY 轮、PATROL、decision/night round、各司 OS 循环、MV W1 装配、Taildrop 收件。
- **移交五步**：指定新主力机 → 主控任务改注册 → 产线宿主迁移 → NATS 起新 server 双写过渡 → 数据按票交付绝对路径。
- **待裁（未代决）**：新主力机 = bm-c 单卡 3070 / bm-d 六卡未入网。
- **正典**：`cph4/fleet/MACHINE-ROLE-bm-a-EXECUTOR-20261020.md`（orders 台账 2026-10-20 18:3x 行）。

**Why 记**：以后在本机开工，第一件事是看有没有票；自派产线=违规。写作/汇报也要按「执行位」口径，不再冒充主控。

## 二、KF 包模板主语误绑（跨曲缺陷·机检抓不到）

`<song>-shots-v2.py` 的 `kf()` 用 `"A %s of %s, %s."` 把 **HIM/HER 名词块直接接动作分词**，无句界，渲染出：

- `… scuffed canvas shoes crouching at the edge of a shallow puddle …`（简单爱 T20）
- `… scuffed canvas shoes holding a plain long umbrella …`（简单爱 T15）
- `… bare feet on the wooden floor … stopping in the air`（龙卷风 T23 同类）

结果=动词绑到「鞋/地板」而非人。修法=模板内加句界（词数、lint 都不变），但属**全曲模板级变更**，须导演席统一裁，起草席不得擅改。

同批实测到的另三条（均为词面事实，非推测）：
1. `LX.LIGHT[...].capitalize()` 会把 `6200K` 写成 `6200k`（全帧命中）——不可称「零影响」。
2. 简单爱 T20 词面 `drawing three characters in the water` 撞「禁 AI 生成文字」+ 字席制字红线。
3. 简单爱 T29/T30 为零人物帧，却沿用 `day_back` 双人光块（`behind the two figures … their silhouettes`）=I1 硬冲突。

**Why 记**：这三类缺陷 lint/词数闸都查不出，只有人读 + 独立评审能抓；后续任何新曲 KF 包起草都要按此三条自查。

## 三、当前产线实况（2026-10-20 18:4x 快照·易过期）

- 可爱女人 A 批 28 帧：已签发（12:4x），**未烧**——bm-c GPU 在跑星晴 PACK-B i2v。
- 星晴 PACK-B：18:18 C2154 补齐 238.000s / 238s 满覆盖，零缺口。
- 星晴装配 mp4：**未回传 bm-a**（收件目录零件），bm-c 侧 conform 日志为绿。
- 云道机械闸 `Tools/cloud_lane_lint.py` 已可用（在役 9 卡 block=0；负例判 REFUSE）。

## 四、正身索引（2026-10-20 立·仓根 `CANON-INDEX-20261020.md`）

**先读它，再决定改哪个文件**。一张表回答「现在哪个文件算数」：规则层（RULES/governance/orders/law-registry/CLOUD-OFF/机器角色）、工作流层（MV PLAYBOOK→PRODUCTION-SYSTEM-v2→PROMPT-EXPERT-GATE→QC-MASTER→VIDEO-QC-GATES→DIRECTOR-STEP-GATE→DISPATCHER-CHARTER）、资产层（v511 最终版、四曲当前剧本 = 星晴/可爱女人 v3、简单爱/龙卷风 v2、`<曲>-shots-v2.py` 的 `NEW` 元组为词面唯一权威）、记录层（orders/decisions/council/audits）。

**维护律**：新增版本→改索引指针→旧版可删（git 留痕）。**记录层不适用「以最新版为准」**——删=伪造。

### 五处已知不一致（登记未改·动前须验证）

| # | 现象 | 动它的前提 |
|---|---|---|
| 1 | `FRAME-GATE-WHITELIST-v1.4.md` 已存在，但 `POOL.json` + `bmc_kf_i2v_chain.py:37` + `bmc_night_factory.py:159` 仍读 `v1.md` | 先比对 v1.4 是否 v1 超集，否则改指针=断链 |
| 2 | `星晴-shots-v2.py:318` 输出仍写 `SHOTLIST-v2.md`，而 v3 为当前 | 改输出路径，或明示 v2=生成件 |
| 3 | `PRODUCTION-SYSTEM-v1.md` 与 v2 同存，README/STEP-GATE/drama INDEX 仍引 v1 | 确认 v2 覆盖 v1 全部范围 |
| 4 | `PREPRO-V1.md` 与 v2 同存，短视频 `SPEC-ACCOUNT.md` 说「以 PREPRO-V1 判例为准」 | 业务判定口径归属 |
| 5 | 龙卷风/简单爱 KF 包整包 FIX，签发席未定 | 非起草席签发（禁自审自签） |

## 五、清理判据（2026-10-20 两波实弹·可复用）

CEO 令链：「过程文件都删了，只保留最终版本，开发进行中的素材还是要保留」→「都清理好，不用备份，以现在最新版本为准」。

**四分类，缺一不可**：
1. **过程件**＝同一交付物的旧代版本 + 抽帧/探针/重烧源/评审抽帧目录 → 删。判据=「代际」不是「时间」（mtime 在整个活跃仓里没有区分力）。
2. **最终版**＝最新一代（如 `full_mv_v511*` 5 件）→ 留，且是唯一保留代。
3. **在飞素材**→ 留。做法=**扫描面锁死**在已收口目录，`media/MV/**/segments`、`mv-album-001-jay` 根本不进扫描面（比事后判断更可靠）。
4. **记录**（.md/.txt/.json/.csv）→ 留。**踩过的坑**：删目录会把 `FINDINGS-W*.md`、`QUANT-SCAN-*.md` 一起带走——正法是删图后从 `git checkout HEAD --` 恢复文字件。

**安全序**：先枚举 `.venv`/`node_modules` 确认没有生产环境挂靠，再删目录；临时目录按龄分级（`.codely-cli/tmp` >1d、系统 Temp >2d），避免抽掉在跑进程的工作目录。

**实绩**：32.2GB（过程件 5.83 + 权重/暂存/临时 25.54 + 会话自动存档 1.04）；工具=`Tools/process_purge_r1020.ps1`（定向枚举，全仓递归会被 venv 拖死）、`Tools/local_cleanup_r1020.ps1`（`.uploaded-ok.json` 凭据闸）、`Tools/doc_inventory.py`（版本簇/重复件/孤儿件盘点）。