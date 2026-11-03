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