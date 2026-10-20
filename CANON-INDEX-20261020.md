# 正身索引（CANON-INDEX）· 2026-10-20

> 一张表回答「现在哪个文件算数」。**同一主题只认本表指向的那一件**；其余为历史、记录或过程件。
> 维护律：新增版本→改本表指针→旧版可删（git 留痕）。**本表不指向任何已被取代的版本。**

## 〇、冷启动读序（新窗口 5 分钟）

1. `AI.md`（集团全局速览）
2. `RULES.md`（红线）
3. `docs/orders.md` 尾行（最新 CEO 令）
4. 本文件（当前正身是谁）
5. `cph4/fleet/MACHINE-ROLE-bm-a-EXECUTOR-20261020.md`（本机现在是执行位，只做票据）

## 一、规则层（硬法·最高优先）

| 主题 | 正身 | 说明 |
|---|---|---|
| 集团红线/协作律 | `RULES.md` | 顶层约束 |
| 治理闭环/AI 诚实律/提交规范 | `docs/governance.md` | 五律+三道防线 |
| CEO 令台账 | `docs/orders.md`（尾行=最新）· 归档 `docs/orders-archive-*.md` | 唯一审计面 |
| 决策台账 | `docs/decisions.md` | D- 编号 |
| 法条登记（何者被废/被冻） | `cph4/registry/law-registry.md` | 引用前必查 |
| **云道停用（T0）** | `cph4/fleet/CLOUD-OFF-LOCAL-ONLY-v1.md` | 业务一律本地；例外仅 CEO 亲批 |
| 云道落地记录 | `cph4/fleet/CLOUD-OFF-LANDING-20261020.md` | 22 件改口径 + 机械闸 |
| **本机角色** | `cph4/fleet/MACHINE-ROLE-bm-a-EXECUTOR-20261020.md` | 票据制·无票不做 |
| 机队分工/算力 | `cph4/fleet-allocations.md` + `cph4/scheduling.md` | 云道段已按 T0 改口径 |

## 二、工作流层（照这个跑）

| 主题 | 正身 | 备注 |
|---|---|---|
| MV 全链条方法论 | `cph4/fleet/mv-album-001-jay/MV-PIPELINE-PLAYBOOK-v1.md` | 起点 |
| MV 生产系统 | `cph4/fleet/mv-album-001-jay/PRODUCTION-SYSTEM-v2.md` | **v2 为当前**（v1 仍在库但非指针） |
| MV 产线总图 | `cph4/fleet/mv-album-001-jay/PRODUCTION-PLAN.md` | 含机队分工（已改本地） |
| 提示词闸（十一面） | `cph4/fleet/mv0001-handover/outbound/krea2/prompt-writing-spec-v1/PROMPT-EXPERT-GATE-v1.md` | 每包必过 |
| 提示词规范（i2v） | 同目录 `PROMPT-SPEC-v2-I2V.md` | |
| QC 总表 | `cph4/fleet/mv-album-001-jay/QC-MASTER-CHECKLIST-v1.md` | §7/§8/§9/§10/§12 为常用门 |
| 出库闸（三线） | `cph4/fleet/VIDEO-QC-GATES-GSV-v1.md` | 短视频/短剧/漫剧 |
| 五站尾环执法 | `cph4/fleet/DIRECTOR-STEP-GATE-v1.md` | 每片收口三连 |
| 派单/调度 | `cph4/fleet/dispatcher/DISPATCHER-CHARTER.md` + `POOL.json` | §五.6 云道闸；`Tools/cloud_lane_lint.py` 机检 |
| 审读-签发分权 | 同上 + `PROMPT-GATE-*-L2.md`（审）/ `-SIGN.md`（签） | 禁自审自签 |
| 自动打磨 | `cph4/fleet/mv-album-001-jay/AUTO-POLISH-LOOP-v1.md` | 引擎已改本地 35B |
| 剧本打磨循环 | `cph4/fleet/mv-album-001-jay/SCRIPT-POLISH-LOOP-v1.md` + `SCRIPT-REVISION-LEDGER.md` | 每轮登记 |

## 三、内容资产层（当前正身）

| 资产 | 正身 | 状态 |
|---|---|---|
| MV 成品（mv0001） | `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/full_mv_v511*.mp4`（5 件） | **最终版·v511 家族唯一保留** |
| 装配段件 | `media/MV/mv0001/kf-demo-20261012/segments/_cut/v56_v511_final/` | 在飞/可重装 |
| 曲目剧本（当前版） | 星晴/可爱女人 `-剧本-v3.md`；简单爱/龙卷风 `-剧本-v2.md` | 旧版已删（git 留痕） |
| 分镜词面（机器正身） | `mv-album-001-jay/<曲>-shots-v2.py` 的 `NEW` 元组 | **词面唯一权威**，人读稿服从它 |
| KF 包 | 星晴/可爱女人 `KF-PACK-A-v1.md`（已签）；龙卷风/简单爱 `-DRAFT.md`（未签·禁烧） | |
| 音源库 | `media/MUSIC/` | **S0 禁删**（无损源） |
| 模型运行时 | `media/BigStream/data/assets/` | **S0 禁删**（9.8GB 非废料） |
| 词锚/结构锚 | `cph4/fleet/mv-album-001-jay/anchors/` + `POOL-0018/0019-*.json` | bm-b 供 |
| 选角/衣橱/调色律 | `CASTING-LAW.md` / `WARDROBE-LAW.md` / `GRADE-LAW.md` | 同目录 |

## 四、记录与台账（可查不可改）

`docs/orders.md`（令）· `docs/decisions.md`（决策）· `cph4/fleet/memory/`（记忆）· `cph4/fleet/PROBLEM-REGISTRY.md`（问题）· `RESULTS-LEDGER-v1.md`（结果）· `CONTENT-WINS-LEDGER-v1.md`（惊喜账）· `cph4/fleet/mv0001-handover/canon/`（导演终审/脚本）· `cph4/council/`（立法案卷）· `docs/audits/`（审计）。

**记录不适用「以最新版为准」**——它们是史实，删=伪造。只清理过程件与已被取代的草稿。

## 五、本次整理做了什么

1. **删 9 件被取代草稿**（git 留痕可追）：`SCRIPT-v5.1/v5/v1`、`可爱女人-剧本-v1/v2`、`星晴-剧本-v1/v2`、`简单爱-剧本-v1`、`龙卷风-剧本-v1`。
2. **修 4 处陈旧引用**：两曲 shots 脚本里指向 v1 剧本的注释改为 v3（词面正身同步）。
3. 前两波已清 31.2GB 过程件与可重建件（回执=`PROCESS-PURGE-RECEIPT-20261020.md`）。

## 六、已知不一致（**未擅自改**·待定）

| # | 现象 | 风险 | 建议 |
|---|---|---|---|
| 1 | `FRAME-GATE-WHITELIST-v1.4.md` 已存在，但 `POOL.json` 与两个脚本（`bmc_kf_i2v_chain.py:37`、`bmc_night_factory.py:159`）仍按 `v1.md` 读取 | 删 v1 会直接断链；且"单一事实源"已分叉 | 先比对 v1.4 是否为 v1 超集，再统一改指针；**未验证前不动** |
| 2 | `星晴-shots-v2.py:318` 输出仍写 `星晴-SHOTLIST-v2.md`，而 v3 已是当前分镜 | 重跑脚本会覆盖/生成旧代文件 | 改输出路径或显式声明 v2=生成件、v3=正身 |
| 3 | `PRODUCTION-SYSTEM-v1.md` 与 v2 同存，README/STEP-GATE/drama INDEX 仍引 v1 | 读者可能据 v1 施工 | 确认 v2 是否覆盖 v1 全部范围后改指针 |
| 4 | `PREPRO-V1.md` 与 `PREPRO-V2.md` 同存，短视频线 `SPEC-ACCOUNT.md` 仍说"以 PREPRO-V1 判例为准" | 口径分裂 | 同上 |
| 5 | 龙卷风/简单爱 KF 包整包 FIX（模板主语误绑），签发席未定 | 两曲 KF 停在草稿 | 新主力机接手后由非起草席签 |

**整理纪律**：正身指针可以改，代码与配置的读取路径要**先验证再改**；不一致只登记不擅动，避免「整理」变成新的断链源。

---
*bm-a · 2026-10-20 · 承 CEO「最新资源/资产/规则/工作流/文档，好好清理整理」*