# 主控工作台（MASTER-CONSOLE-v1）· 2026-11-11

> 令源：CEO 2026-11-11「主控要做到对每个机器和任务面了如指掌，随时可以给他们命令啊修改啊什么的，但平常自动化靠机队自己」。
> 两个工具：`Tools/fleet/fleet_view.py`（了如指掌，自检 7/7）+ `Tools/fleet/fleet_cmd.py`（随时下令，自检 14/14）。
> 数据面：全部读盘上事实（分片队列、回执、配置），不读心跳、不信自述。

## 一、了如指掌：一屏看到五件事

`python3 Tools/fleet/fleet_view.py`

1. **每台机**：状态、席位数、能接几类任务、背几道工序、队列 O/R/D/B、最后回执多久前、本地模型通不通。
2. **任务面**：59 道工序各自由谁承接、产物路径、产物年龄、有没有契约。
3. **需要主控介入**：`--gaps` 只列这些——
   - `MACHINE-DOWN` 机器不可用
   - `WORK-QUEUED-NO-WORKER` 有卡没人干
   - `NO-RECEIPT-24H` 24 小时没回执
   - `NO-OWNER` 工序没有承接方
   - `NO-OUTPUT-CONTRACT` 工序没写产物路径（自驱无从下手）

机队当前实测（2026-11-11 15:2x）：

| 工位 | 机器 | 状态 | 席位 | 类型 | 工序 | 队列 O/R/D/B |
|---|---|---|---|---|---|---|
| delivery | 公司生产力机 | network_ok_not_registered | 8 | 11 | 15 | 0/0/0/0 |
| visual | 传家宝 | blocked_no_comfyui | 9 | 8 | 9 | 1/0/0/0 |
| audio | 小钢炮 | offline | 7 | 4 | 8 | 3/0/0/2 |
| brain | 算力大脑 | not_installed | 7 | 2 | 2 | 0/0/0/0 |
| control | MacBook | ready_paused | 8 | 19 | 24 | 0/0/0/0 |

**任务面：59 道工序，只有 2 道有产物契约。** 这是主控最该先补的一件事。

## 二、随时下令：五个动词

```bash
# 1 下卡（必须落在该工序的承接方，否则拒绝）
fleet_cmd.py card add --station visual --product PROD-MV-SINGLE --stage mv-kf \
    --title "重跑 v716 第 12 镜" --why "首帧糊" --cmd "python3 ..."

# 2 撤卡（必须写原因；已终结的卡不许重复撤）
fleet_cmd.py card cancel --station visual --id SD-... --why "改派给新卡"

# 3 改状态（OPEN/RUNNING/BLOCKED/FAILED/PENDING_HUMAN/SHELVED）
fleet_cmd.py card state --station audio --id ... --state BLOCKED --why "TTS venv 缺"

# 4 停/恢复一台机（写 STATIONS.status + 原因与时间）
fleet_cmd.py station pause --station delivery --why "CEO 白天在用"
fleet_cmd.py station resume --station delivery --why "夜间窗口"

# 5 改承接方（改 TAXONOMY，改完跑 work_matrix 复验）
fleet_cmd.py assign --task-type T-ASM-SUB --stations visual,control
```

规矩：
1. **默认 dry-run**，加 `--yes` 才落盘；每次都打印"会变成什么"。
2. **每条命令进台账** `state/command-ledger.jsonl`（人、原因、前后值），可追溯、可回滚。
3. **不许无原因撤卡**；不许把卡塞给非承接工位（强行塞会被拒，改派请用 assign）。
4. 落盘即生效：机队按既有同步机制取，主控不去"推"。

## 三、边界：平常不插手

1. 日常派活、判据、记账一律归机队自驱（`AUTONOMY-V3`）；主控只在 `--gaps` 出现真缺口时出手。
2. 主控出手的三种情形：跨机依赖卡住、工序无承接方、机器不可用需要改派。
3. 主控不改阈值、不改判据内容——那些走 `voice_gate`/`drama_rules` 的常量与自检。

## 四、还差的一步

一屏与命令面已经能对着盘上事实工作，但**命令下发后没有回执确认**：目前只能靠机队下一轮同步时读到自己分片。
下一步给 `fleet_cmd` 加 `--await`（等该机回执出现再返回），并在 `fleet_view` 增加"命令执行情况"一栏。
