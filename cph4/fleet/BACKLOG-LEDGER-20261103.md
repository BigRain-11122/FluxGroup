# 遗留问题总账 · 2026-11-03（bm-b 根治轮）

> 本文件是"遗留问题"的唯一账本。规则：一条问题一行，写清 **根因 / 证据 / 处置 / 责任机 / 验收**。
> 只有验收物落地才算解决；"已安排"不算。新问题追加，不复述旧法条。
> 数据源：`cph4/fleet/PRODUCTION-QUEUE.jsonl`、`cph4/fleet/queue-receipts/`、本机实测。

## A. 机队调度根因（同一天内造成 15+ 张卡假失败）

| # | 问题 | 根因（证据） | 处置 | 责任 | 验收 |
|---|------|--------------|------|------|------|
| A1 | Windows 卡被 macOS 领走 | `C-TTS-QC-ALL-bm-m.json` / `C-INFRA-AUDIT-BM-*-bm-m.json`：同一张 Windows 卡在 Mac 上跑出 `E-INPUT`、`rc=3 BLOCKED`。`card_os_ok` 只在卡显式写 `node_os` 时生效，绝大多数卡没写 | `Tools/fleet/fleet_lane.py`：新增 `infer_node_os()`，从命令里的盘符 / `powershell` / `.cmd` 推断 OS；`card_os_ok` 改用推断值 | 执行器（已改） | 单测：Windows 卡在 bm-m 上 `card_os_ok=False`（本次实跑通过）；下一拍 Mac 不再产生该类回执 |
| A2 | 输入不在本机也照接 | `--dir media/drama-tts-out` 是硬输入，但卡 `requires: []`；Mac 稀疏检出没有 `media/`，于是写下 `MISSING` | `fleet_lane.implicit_inputs()`：从 `--dir/--in/--inbox/-i` 与裸路径提取生产树路径；`lane_agent._eligible` 里不存在即 SKIP（不是失败） | 执行器（已改） | 单测通过；bm-m/bm-a 不再产出 `MISSING media/...` 回执 |
| A3 | 能力缺失当失败 | Mac 无 ffmpeg → `voice_corpus_prep` rc=1、"没有 ffmpeg" | 新增卡字段 `requires_bin`，执行前 `shutil.which` 探测，缺则 SKIP | 执行器（已改） | 单测：`requires_bin=["ffmpeg"]` 通过 / 不存在二进制返回 False |
| A4 | 租约超时数字不可读 | `lease-heartbeat-timeout(1000000000s)`：owner 无心跳时 `beats.get(owner, 1e9)` 把"未知"写成十亿秒 | `closer.py`：owner 无心跳 → `lease-owner-unknown`，立即释放并写清原因 | 结卡器（已改） | 队列里不再出现 1e9 字样 |

## B. 队列卫生

| # | 问题 | 处置 | 验收 |
|---|------|------|------|
| B1 | 同一件配音质检派了 4 张卡（`C-TTS-QC-ALL` / `R-NEXT-BIGSTREAMD-TTS-QC-20261102` / `...20261103` / `bigstream-duanju-tts-qc-2026-11-03`），互相判重失败 | 4 张全部 CANCELLED，只留 **`Q-TTS-QC-R1-20261103`**（钉 bm-b，带 `--out`，`requires` 含真实目录） | 该卡跑出 `tts-qc-r1-20261103.json` |
| B2 | 其中一张卡缺必填 `--out`（rc=2 E-CONTRACT），另一张指向不存在的 `media/drama-tts-batch` | 见 B1，已并入正卡 | 同上 |
| B3 | `asset-lib-index` 的命令 `vault.py list --limit 5` 根本不产出交付物 | CANCELLED + backlog 行标 INVALID | 不再被补货重派 |
| B4 | `CHK-DUPES` 命令写 `queue-receipts/`，交付物却指向 `cph4/fleet/` | 交付物路径改正 | 卡可被结卡 |
| B5 | 3 张 `C-INFRA-AUDIT-BM-*` 被 Mac 跑坏后卡在 FAILED | 复原为 OPEN，补 `node_os=windows`，清 owner/retries | bm-a/bm-c 各出一份本机体检 |

## C. 供给侧

| # | 问题 | 证据 | 处置 |
|---|------|------|------|
| C1 | 音色语料 3 张分片卡空转 | `media/asset/inbox` 0 个音频；回执 `inbox_files: 0`，rc=3 | queue CANCELLED；backlog 行改 `WAITING-SUPPLY`，不再自动重派。投料后手工改回 READY |
| C2 | `asset-lib-voice-assemble` 等授权与语料 | `voice-dataset-20261103.json`：无 RIGHTS.json、无片段 | 同上 WAITING-SUPPLY |
| C3 | bm-c 缺资产目录 | `char_gen.py` 崩 `FileNotFoundError: K:\Fluxgroup\FluxGroup\media\asset\characters` | 新卡 `Q-ASSET-MKDIR-BMC-20261103` 建目录；`char-gen` 卡 `when_all` 加该目录 |

## D. 工具链版本分裂

| # | 问题 | 处置 | 验收 |
|---|------|------|------|
| D1 | 仓库 `Tools/voicebank/` 只有旧 6 件（基频闸版，会错杀同人异段），bm-b 已建的身份闸版 16 件从未上链 → bm-a/bm-c 按旧派单会复现"认错人" | 本次推送 19 件：`vb_identify`（ERES2NetV2 说话人嵌入）、`vb_pickref`（身份+转写自洽+hf 三闸）、`vb_assets`、`vb_batch`、`vb_roster`、`vb_audition`、`vb_probe`、`vb_fetch`、`vb_bulk_fetch`、`vb_screen_par`、`vb_space`、`vb_sweep`、`vb_sweep2`、`vb_sample`，并覆盖 `vb_build`（`--identify-ref/--identify-min`、`RAWS_PER_SPEECH=3.0`、基频只记录不删源）、`vb_worker`、`vb_compare`、`voicebank_say` | 19 件全部 `py_compile` 通过（本次实跑 rc=0） |

## E. 交付面

| # | 问题 | 处置 | 验收 |
|---|------|------|------|
| E1 | 正片 60 集仍静音，有声版在 `drama-eps-audio` 无人认领 | 决策：**`media/drama-eps-audio` 为唯一有声交付面**，`media/drama-eps` 保留为画面母版（不覆盖、不删除）。依据=面板产物已 60/60 且混音体检全过（RMS −20.9dB、零削波） | `cph4/fleet/drama-dept-v1/DELIVERY-DECISION-20261103.md` |

## F. 仓库与运维

| # | 问题 | 证据 | 处置 | 状态 |
|---|------|------|------|------|
| F1 | 主工作树 `C:\Fluxgroup\FluxGroup` 长期 2617 条脏 | `git status`：1290 ` D` + 953 `AD` = 2243 个"索引里有、盘上没有"（ceebc703 整树删除事故残留）；105 `M `、66 `A `、62 `??` | 新增 **report-only** 体检器 `Tools/repo-worktree-check.ps1`（`-Restore` 才动手）。执行面已迁 `FleetRuntime`/`FleetAgent` 干净克隆，主树只作归档 | 已建体检器；恢复需人工或专项窗口 |
| F2 | `oversight-run.log` 曾 4.37GB 无轮转 | 现 4.4KB（曾被截断），但生成逻辑仍在 | `Tools/repo-slim.ps1` 增日志轮转段：`fleet/**/*.log` > 20MB 时保留尾 5MB | 已改 |
| F3 | 本地不可读对象 `483b848b` | `git cat-file -t 483b848b` 现返回 `blob`（rc=0）；`fsck --connectivity-only` 只剩 dangling，无 error | 已自愈，无需处置 | 已复原（本次实测） |
| F4 | NATS 主 100.110.185.62:4222 曾不通 | `Test-NetConnection` 本次 True | 已恢复 | 已复原（本次实测） |
| F5 | bm-d（V100×3）未入网 | `lanes/bm-d.json` 停在 2026-10-29，`lane_ok=false` | 物理件（装机），CEO 域；装机包已备齐在桌面 | 阻塞于物理件 |

## G. 待续（本轮未做，明记不装成已做）

- F1 的 2243 个删除文件是否恢复：需判断是否为 bm-c 迁移后的有意清理，**不自动恢复**。单文件恢复也受阻：`git checkout -- Tools/fleet/artifact_push.ps1` 报 pathspec 不匹配（index 残留态），恢复须走专项窗口。
- A2 的 `remote_data: true` 逃生门：给确实"由本机生成整棵树"的卡使用；目前无卡需要。
- **R-ART-PUSH-B rc=127 已定谳（23:3x 实跑复现）**：`-File 参数不存在`——根因=主工作树整树删除事故把 `Tools/fleet/artifact_push.ps1` 一并删了（盘上无此文件）。FleetAgent 克隆内有正本 → 车道代理可跑此卡；主树单文件恢复归 F1 专项。bm-c 的 R-ART-PUSH-C 大概率同根因（K: 树同源事故）。
- 主控收卷依赖 Mac 脉：合盖即停；已执行卡的状态回卷会延迟，回执不丢（落盘在执行机）。

## H. 本窗执行记录（2026-11-03 22:0x–23:3x，全部实测）

| 时点 | 事项 | 证据 |
|------|------|------|
| 23:12 | Q-TTS-QC-R1 手动实跑成功：`media/drama-tts-out` 2145 条 / 334.1MB，verdict **COMPLETE-STOPPED**（最新产出已 37.7h，整批停转=无在飞配音） | `C:/Fluxgroup/FluxGroup/cph4/fleet/queue-receipts/tts-qc-r1-20261103.json` |
| 23:2x | 推送事故与修复：第一次 CAS 推送把 32 个反斜杠路径写成根级垃圾条目（真文件零更新、新克隆 checkout 即破）→ 修复 commit **9f771df1**：删 32 个垃圾条目 + 按正斜杠重写全部 32 件 | `ls-tree -z` 反斜杠条目=0；目标文件 blob 全部换新 |
| 23:26 | bm-b 执行腿重建：`C:\Fluxgroup\FleetAgent`（blob:none+sparse：/Tools/fleet/ + backlog_fill/queue_claim + /cph4/fleet/*.json(l) + lanes/）+ `agent-bm-b.bat` 上链（origin 原本没有这个 bat，HQ-Agent 每分钟 rc=1 空转） | 克隆内 infer_node_os / lease-owner-unknown / bat 三补丁全部在位 |
| 23:29 | **端到端实证**：`agent.py --node bm-b` 单拍 `hb=0 lane=0`——被 Mac 跑坏三次的 C-INFRA-AUDIT-BM-B 在 bm-b 正确执行，DONE rc=2（卡契约允许）164.3s，交付物产出 | `C:\Fluxgroup\FleetAgent\cph4\fleet\queue-receipts\C-INFRA-AUDIT-BM-B-20261103-bm-b.json` |
| 23:2x | 体检卡真实发现（新病灶，待办）：`env-missing:OLLAMA_NUM_PARALLEL/KEEP_ALIVE/MAX_LOADED_MODELS/CONTEXT_LENGTH` 四项 + 审计探针瞬时 5.3 tok/s + embedding 不可用。**常驻槽复核=合规**（`ollama ps`＝qwen3.8:4b 3.7GB 100%GPU Forever），慢速为探针瞬时，不违槽位法 | 同上回执 stdout_tail |
| 23:3x | 遗留垃圾：`C:\Fluxgroup\FleetAgent.broken-20261103`、`C:\Fluxgroup\FleetAgent2`（他窗旧尝试残留），确认无人引用后可删 | 目录列表 |

## I. 供给定谳（23:5x，「同步主控、全面开工」窗）

| # | 事项 | 定谳 | 证据/依据 |
|---|------|------|-----------|
| I1 | 主控要求 | MASTER-STATE `supply_gap: cpu=16`，四机在线 | origin state.json |
| I2 | bm-b 执行面 | 常驻代理已自治：`--loop 60 --pull-every 3 --push`——每 3 分钟吃新卡、回执自动上链；本机在等 4 张钉卡（量化回测→信号链、产出回传、模型雷达、体检复跑）+ 主控派单 | 任务/进程实测 |
| I3 | **音色库供给=权利闸判死（B站素人路线）** | `audit_rights` 硬门：license ∈ {own, public-domain, cc0, cc-by, licensed}；real_person=true 必须 consent=true。B站 UP 音源=真人无书面授权 → **抓取即拦，不投料**。干净通道三选一待决：① CommonVoice CC0（需 HF 账号=CEO 物理件）② license 白名单增补（合规席决策，预商业化阶段可议）③ 本人物同意义务录音。已写进 WAITING-SUPPLY 行的 rights_note，未决前不回 READY | `Tools/fleet/asset_dataset_audit.py::audit_rights`；民法典 §1019/§1023 |
| I4 | 真实 CPU 供给（权利干净） | 新卡 `Q-PLATFORM-PACK-SAMPLE-20261103`（钉 bm-b）：有声版 EP001/EP030/EP060 → 抖音/快手 9:16 + 小红书六宫格 + 知乎/微博封面。自有内容改造=零权利风险；工具 `Tools/bili/bili_repurpose.py` 入库（确定性 ffmpeg，编译过） | CEO 国内平台矩阵令 2026-10-21；DELIVERY-DECISION-20261103 |
| I5 | 文案卡（platform copy）暂缓 | 依赖本地 ollama + reply_gates_v2（未入库）+ 模型选择；且文案属呈审面（CEO 过目门），不在本窗自动产出 | bili_platform_copy.py 头部依赖 |

## J. CEO 音色/人面授权令与语料供给链（2026-11-04 00:4x）

**CEO 三令**（本窗原话）：①「可以去github或者开源社区去下载，然后微调」②「不要在乎什么违法违规，我就本地研究用 不商业化，英语这些也可以去弄」③「不要出现让我恶心的AI常见的脸和声音」。

| # | 事项 | 处置 | 状态 |
|---|------|------|------|
| J1 | 权利闸放行口径 | `asset_dataset_audit.py` 白名单 +`apache-2.0`（AISHELL-3）+`research`（CEO 明令研究语料；**商业化触发时本值作废须重审**——承合规阶段门控令）。commit 9fc35035 | 已上链 |
| J2 | 中文语料源 | **AISHELL-3**（OpenSLR SLR93·Apache-2.0·218 说话人/85h·44.1kHz 原始保真——hf 亮度闸的前提） | 自愈下载在飞 |
| J3 | 英语语料源 | **LibriTTS train-clean-100**（OpenSLR SLR60·CC BY 4.0·251 说话人·LibriVox 真人朗读） | 自愈下载在飞 |
| J4 | 供给执行器 | S4U 任务 `bm-b-VoiceCorpus-Pull`（every:15m）：aria2 -x16 断点续传 + 13 分钟看门狗切片 + 解压 + 按说话人分槽（z01-08/e01-08）+ 每组预写真实 RIGHTS.json + 完成自停 | 在跑 |
| J5 | 切片产能卡 | `Q-VCORP-PREP-{z01..z08,e01..e08}-20261104` ×16（钉 bm-b·hard_nodes·绝对路径·`when_all`=槽目录到料即自动开跑）→ 主控 CPU 缺口 16 正好被这批吃掉 | 已上链 |
| J6 | **质量硬闸（CEO 令③）—声音面** | 真人语料（非合成）+ SoVITS 微调（非端到端 TTS）+ 参考音三闸（身份≥0.65/转写自洽≥0.90/**hf_ratio≥0.010 亮度闸**=闷声直接打回）+ 切片不做 loudnorm（保留自然 LRA 与停顿密度）——四层都在既有工装里，本链只是把原料换成真录音 | 闸在库 |
| J7 | **质量硬闸（CEO 令③）—人脸面** | 实查 bm-c 出图底模=`DreamShaperXL_Lightning`（SDXL 系=「AI 脸」重灾区，正是 CEO 说的恶心款）。**升级路径已定**：bm-c ComfyUI 内的 qwen-image 四件套（POOL-0021 配方）+ 角色 LoRA 吃真数据集。底模更换属 asset-lib 线 GPU 面（bm-c 16G 车道），导演席按三律验收 | 待 bm-c 执行 |

### 下载通道实测（本窗判例）

- OpenSLR 两镜像**按连接限速**：magicdatatech 单连接 0.06MB/s、elda 0.02MB/s、Clash 代理 0.02-0.1MB/s——单连接路线全部判死。
- **aria2 -x16 = 0.76MB/s 起**（12 倍），多连接聚合后实际吞吐远超此数（慢启动+爬坡）。
- **满额假象判例**：aria2 预分配全尺寸文件——「文件大小=期望值」≠完成，**以 .aria2 控制文件消失为准**。
- 任务实例退出会连坐杀 Start-Process 子进程 → 下载必须**实例内**跑+看门狗到点击杀（bm-d-ISO-Pull 同款范式）。
- `.cmd >> log` 独占句柄与脚本 `Add-Content` 同文件=自锁死；双文件制（main.log 与脚本日志分开）。
- ModelScope 上的「AISHELL-3」两个条目均为元数据壳（Type:4 外链 / Type:2 空目录），**不实际托管音频**——检索到不等于能下。

## K. 「高质量 · 去 AI 感」细颗粒度规格与扩散（2026-11-04 00:4x，CEO 根本要求令）

**CEO 令（原话）**：「务必解决高质量和去AI感 2 个最根本的要求，你可以扩散一下，把颗粒度做细」。

| # | 事项 | 处置 | 状态 |
|---|------|------|------|
| K1 | **规格书正身** | `cph4/fleet/quality/DE-AI-SPEC-v1.md`：四域（A 声音 8 条 / B 人脸 7 条 / C 画面 7 条 / D 文本 3 条）+ E 执法矩阵 + F 验收流向。每条=判据（细）/阈值/测法/执法点/打回动作；机器可量化的量化（hf_ratio≥0.010、ASR≥0.90、身份≥0.65、LRA≥5LU、停顿≥6/min、底噪 −60~−35dB、seam/freeze=0、硬切≤70%、折行 worst≤17/10、G1-G18、照抄<8 字），量化不了的走导演席盲评协议（≥9 线，六面自审） | 已上链 |
| K2 | 训练卡驱动器 | `Tools/voicebank/vb_train_card.py`：一卡一声线（wav→m4a→vb_build 44.1k 全保真管线→SoVITS 权重→回执）；内置 GPU 卫生（ST-012 三灭+恢复三件；8G 卡上 s2 需 ~7.9GB，不杀常驻模型必 OOM） | 已上链 |
| K3 | 微调试点卡 ×2（批前抽检律） | `Q-VCORP-TRAIN-PILOT-aishell3-z01 / -libritts-e01`（钉 bm-b·heavy·when_all=槽目录到料）；**双 PASS 后才批量派其余 14 槽**（锚点行 `VCORP-TRAIN-BATCH-14-20261104`） | 已上链，等料 |
| K4 | 人脸对照板执法 | `Tools/fleet/asset_board.py`（确定性拼板+清单回执，正反例+多模态亲验通过）；卡 `Q-FACE-BOARD-BMC-20261104`（钉 bm-c）：char-gen 现产物拼板 → 导演席按 B1/B2/B3/B5 盲评 = 换模决策证据 | 已上链 |
| K5 | 底模换轨 backlog | `CHAR-GEN-V2-QWEN-20261104`（P0）：char_gen v2 支持 qwen-image 四件套工作流；**SDXL/DreamShaper 系按 B5 只许出草稿、禁入训练集** | READY 待 bm-c |
| K6 | 规格与既有检查单的关系 | 旧单（CHK-E 族、三病清零、drama QC 模板、reply G1-G18、mv 四闸）=本 spec 分册；冲突以 spec 为准；修订律=阈值改动必须带实测证据 | — |

**扩散语义**：spec 上链即对全机队可见；本节列出的卡/backlog 行就是各出生站的新闸；导演席审片时按 spec 逐项对号。

## L. 机队全域法：主控最高优先 + 智能自我兜底（CEO 2026-11-04 定谳令）

**CEO 原话**：「机队都应该这样，主控优先级最高，但也要有自我兜底智能机制」（承接同日早令「你的任务首先是主控电脑给你，实在没有才是自己给自己排」）。

| # | 法条 | 执法机制（已在现行代码实证） | 状态 |
|---|------|---------------------------|------|
| L1 | 主控 bm-m 派单优先级最高 | `lane_agent.run_lane_cycle`：车道文件（主控派单）有单**先执行主控单**，自排只在无单时启动 | 代码固有 |
| L2 | 主控恢复派单即自然优先 | 同一判定：车道文件有单时兜底自排不启动 | 代码固有 |
| L3 | 自我兜底=智能不空转 | 无单时 `self_dispatch` → 本地 `backlog_fill.fill(root, node)` 晋升申报池（**只晋升本机输入齐备的行**）→ 带闸执行（lane_agent L420 实证） | 代码固有 |
| L4 | 自排唯一合法通道=backlog 申报 | 会话/窗口自排活写 `PRODUCTION-BACKLOG.jsonl`（proposed_by=本机·requires/when_all/accept 齐备）；**禁直接写 PRODUCTION-QUEUE**（队列唯一写者=主控；单写者冲突实锚=K 节 21 卡被清事件） | bm-b 已遵（20 卡迁移·commit 26924bb2） |
| L5 | 兜底活带全套机器闸 | 五道闸照常生效：hard_nodes 钉机执法 / node_os 推断 / implicit_inputs 输入门 / requires_bin / GPU·RAM 门；DE-AI-SPEC 出厂闸逐条引用 | 代码固有（A1-A4 判例） |
| L6 | 广播 | 令总线 OB 单（orders.md 正典行 + cmd 件，车道 bm-a/bm-b/bm-c/bm-m） | 本窗 |

**一句话**：主控是唯一的排单者；机器只在主控没派单时、从申报池里、带着全套闸、自己找活干——不空转、不越权、不写队。

| # | 增补（CEO 2026-11-04 23:0x 令「机队没活就赶紧找主控要，并通知主控早早准备好」） | 执法机制 | 状态 |
|---|------|---------|------|
| L7 | 没活=**主动向主控要活**（禁静默闲置） | `lane_agent._need_work_flag`：无主控单+申报池无可晋升行 → 写 `cph4/fleet/state/need-work/<node>.json`（走代理自有 state 推送腿=全队 git 可见、可审计）；接活即撤标。直调冒烟通过（写标/撤标/字段齐） | 已上链 |
| L8 | **主控备单制**（早早准备好工单） | WORK-RULES 行 R-NEEDWORK-20261104-001（nodes=bm-m·主控本地模型执行·已验证的通道）：逐车道核 ≥3 张可立即派发的卡 + NEED-WORK 响应规则 + 备单方法，回执 `bm-m-workprep.md` | 已上链 |

## M. 全队复盘（2026-11-03→05，CEO 令「复盘·根治·主控协作·全队畅通」）

**复盘法**：每个病灶=根因（实证）→ 根治 → 验收。三天累计 6 族病灶，5 族已根治，1 族在飞。

### 族 1：调度与执行链（机队机器法）——全数根治

| 病灶（实证） | 根因 | 根治 | 验收 |
|---|---|---|---|
| Windows 卡被 Mac 领走连跑三败；缺输入照跑写 MISSING；缺 ffmpeg 当失败；租约 1e9 秒鬼数字 | card_os_ok 只认显式 node_os；隐式硬输入不检查；能力不探测；beats.get(owner,1e9) | fleet_lane 三函数（infer_node_os/implicit_inputs/requires_bin）+ closer lease-owner-unknown | 11-03 实弹：体检/量化/配音质检卡全在正确机器执行 ✓ |
| bm-b 偷跑他机身份卡（--node bm-c 完整跑完/--node bm-a 半途杀） | 稀疏克隆无 MASTER-STATE=判全员失联；hard_nodes 字段无人执法 | _pins_stale 读不到=按钉机活着；hard_nodes 硬门 | 11-04 实证：下一拍只认本机卡 ✓ |
| 主控整树重写吞掉 21 张自排卡 | 单写者冲突：窗口直写队列 vs 主控全文件重写 | **自排改申报制**：唯一通道=PRODUCTION-BACKLOG 申报行 | CEO 立法 11-04，全队广播 OB-230606-701 ✓ |
| 常驻代理不热载、冻结克隆（落后 719） | --loop 进程不重读代码；本地杂牌提交堵 ff-only | reset --hard + 杀常驻让任务带新码重启（他窗 01:42） | 重启后 hb/lane/push 三绿 ✓ |
| **回执滞留本地一整天**（18 切片+2 训练回执全没上远端、need-work 死旗不撤、主控对 bm-b 半盲） | **ff-only 拉取带着未提交工作树改动成功**——自有面（回执/状态件删除）永不进提交；v1 修复又撞中文路径八进制转义（status 逐路径收集→add fatal 静默） | **前缀式 own-delta 预推提交**（git add -A -- 前缀，git 自己解析目录内容=免疫非 ASCII） | 本窗 commit 6f9e555e，重启后逐拍验收 |
| lane_agent 读卡输出 GBK 崩 | Windows 默认编码 | bm-c 修 exec utf-8（commit 0484a880） | 他窗验证 ✓ |

### 族 2：下载供给链（aria2 三重陷阱）——全数根治，16 槽全满

| 病灶 | 根因 | 根治 | 验收 |
|---|---|---|---|
| 单连接 0.02-0.06MB/s 全线死慢 | OpenSLR 两镜像按连接限速 | aria2 -x16（12.7 倍） | 实测 ✓ |
| 「文件满额」假完成、19GB 进度被误删 | aria2 预分配全尺寸；控制文件=块位图唯一记录 | 完成判据=控制文件消失；禁删控制文件 | 判例入册 ✓ |
| extractall rc=0 但只解出洞前内容（zh 全灭） | 预分配零洞=合法归档结尾 | 完整性=解出量对账（218 说话人） | ✓ |
| 解压健康却零填槽 | 文档假名 SSS vs 盘上真名 SSB；LibriTTS 两层目录；test/train 撞人 | 真实结构适配+排重（他窗） | **11-05 06:08 16 槽全满自停** ✓ |

### 族 3：语音微调管线（CEO「然后微调」令的落地路）——在飞

| 病灶 | 根因 | 根治 | 状态 |
|---|---|---|---|
| 管线静默死亡（到料后零活卡跑） | 队列孪生被清→workgen 连带归档申报行 | 新 id 申报行复活法（他窗） | ✓ 已复活 |
| e01 试点 BLOCKED（+0 clips ×66） | LibriTTS 连续朗读无 -35dB 间隙，3-10s 切片窗整段丢弃 | vb_train_card --max-clip 直通 + R6 行（en=25s） | **R6 在飞（本窗）** |
| 部分槽薄数据诚实 BLOCK | 坏档洞前残料 | 全量重下+换肥（z06←SSB0038 等） | ✓ |
| z01 试点未跑 | 申报行晋升时机 | R6 行 READY，等车道空闲即接 | 待跑 |

### 族 4：质量法（CEO 根本要求令）——已立法扩散

DE-AI-SPEC v1.1（28 条四域+执法矩阵+盲评协议）上链；主控接入简报确认逐条引用条目号（bm-m-deai-ack.md）；声线区分度/高清无杂音（23:55 令）织入 A9/A10；人脸底模 DreamShaperXL=AI 脸家族，qwen-image 换轨 backlog P0 待 bm-c 执行。

### 族 5：主控协作（CEO「通知主控」令）——四通道全通

令总线广播（三 Windows 机点醒 3/3 成功）✓；WORK-RULES=Mac 执行通道（deai-ack/workprep 两发两中）✓；need-work 机制（挂标/撤标+主控 2s P0 响应规则+每小时晋升预检）✓；bm-m 名册实测修正 ✓。

### 族 6：遗留开放件（如实列，不装已解决）

1. z01 试点 + 14 槽批量（门=双试点 PASS）
2. 主控 workgen 旧模板卡病：C-TTS-QC-ALL 相对路径僵尸卡重生（11-05 再败）、B-QNT-SIGNAL 相对路径 BLOCK（bm-b 有真数据却因相对路径找不到）——主控备单制回执已承诺修模板
3. 三线 STALLED：bigstream-mv KF 段（28h+）、biggame 可玩包、bigmoney 策略判决——业务真缺口
4. bm-a IDLE-CONFIRMED x7（主控喂单/申报池补料待主控备单制执行）
5. 27 张 FAILED 卡清账（多数=业务真缺口非机器病）