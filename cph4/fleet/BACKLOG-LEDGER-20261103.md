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

- F1 的 2243 个删除文件是否恢复：需判断是否为 bm-c 迁移后的有意清理，**不自动恢复**。
- A2 的 `remote_data: true` 逃生门：给确实"由本机生成整棵树"的卡使用；目前无卡需要。
- 队列里 `R-ART-PUSH-B/C`（rc=127）尚未定谳——需在 bm-b 实跑 `artifact_push.ps1` 取真实 stderr。