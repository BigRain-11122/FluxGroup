# 机队产出备份规则 v1（2026-11-02）· 2026-11-11 变更

> **2026-11-11 变更（CEO 令：Mac 不再使用移动硬盘）**：
> 1. L3「主控写入移动盘」**退役**；主控不再保存产物字节。
> 2. 产物字节留在产出机本地盘，按保留策略管理；主控只收清单（L1）并核哈希。
> 3. 需要取件时按清单点对点从产出机拉取，不再经过外置盘。
> 4. 冷备（代码与历史）由 git 远端 origin 承担；`backup_sync.sh` 已改为留痕退出。

> 上位：CEO 令「让机队把他们的实际产出，都给我备份到移动盘去，并建立规则」。
> 本件是契约正身；实现件=`Tools/fleet/artifact_intake.py`（主控收件口）、
> `Tools/fleet/artifact_push.ps1`（机队推送器）、`Tools/fleet/artifact_status.py`（覆盖度核对）。

## 一、为什么需要这条规则（问题不是猜的）

`lane_agent.git_publish` 明确跳过 `media/`、`gaming/`、`quant/`，而队列里的
deliverable 大量指向各机本地盘（`D:\`、`C:\Fluxgroup`、`K:\`、`D:\FleetWorker`、
`C:\Users\sjs20\Desktop`）。两边一夹，机队真正产出的成片/配音/混音/审计 JSON
**从来没有回到主控这边**。主控只能看回执，看不到东西——「DONE 但盘上没文件」
就是这么来的。本规则补的就是这条断链。

## 二、什么必须备份（「实际产出」的定义）

**必须**：
- 队列卡 deliverable 指向的、实际存在的文件或目录内容（成片 mp4、配音 wav、混音、
  图集、封面、机器判据 JSON、评审报告 md）。
- 任何在机器本地盘上、且不是源码的产物。

**不备**（明文豁免）：
- 源码与文档——它们在 git 里，另有备份通道（`Tools/fleet/backup_sync.sh`）。
- 缓存与临时件：`__pycache__/`、`*.part`、`*.tmp`、`.DS_Store`、`node_modules/`。
- **凭据与密钥：一律不上盘**（token、oauth、私钥、cookie）。表现层禁止打印其内容。

## 三、三层通道（各管一件事）

| 层 | 走什么 | 落点 | 为什么 |
|---|---|---|---|
| L1 元数据 | **git** | `cph4/fleet/artifacts/<node>/MANIFEST.jsonl`（声明）、`PUSHED.jsonl`（已推凭证）、`cph4/fleet/artifacts/COVERAGE.md` | 小、可 diff、跨机可见 |
| L2 字节 | **HTTP PUT** 到主控收件口 | 内存流式，不落中转 | 大文件不进 git，Windows 不必配 SMB 凭据 |
| L3 归档 | ~~主控写入移动盘~~（2026-11-11 退役） | 产物留在产出机本地盘；主控只存清单 | Mac 不落媒体，磁盘余量留给主控与模型 |

方向选择：**机队推（push）→ 主控收**，不让主控去拉。理由：盘和写权限都在主控；
Windows 侧只需一次 `Invoke-WebRequest`，不引入新的常驻服务端。

## 四、契约（机器可执行）

### 机队侧（Windows）
```
powershell -ExecutionPolicy Bypass -File Tools\fleet\artifact_push.ps1 ^
    -Root <本机仓根> -Node bm-a|bm-b|bm-c|bm-d
```
- 从 `PRODUCTION-QUEUE.jsonl` 取本机名下的 deliverable，展开目录成文件；
- 按 `sha256+bytes` 去重（`PUSHED.jsonl` 作账），**重跑不重传**；
- 默认单件上限 2048MB（`-MaxMB` 可调），超限记 SKIP 不静默丢；
- 每次运行都会重写 `MANIFEST.jsonl`（声明全量），成功件追加 `PUSHED.jsonl`；
- 收发件口地址默认 `http://100.75.133.10:11436`（tailnet 内的主控）。

### 主控侧
```
python3 Tools/fleet/artifact_intake.py     # launchd 常驻，端口 11436
python3 Tools/fleet/artifact_status.py     # 生成 COVERAGE.md
```
- 只监听 tailnet 地址（`100.75.133.10`），局域网/公网到不了；
- 校验 `X-Sha256`，不匹配**拒收**；写盘用 `.part → rename` 原子落地；
- 收件记录进 `cph4/fleet/artifacts/INDEX.jsonl`（不再写外置盘）；
- 2026-11-11 起：收件口只做校验与登记，不落字节；落盘职责回产出机。

## 五、铁律（违一条即判备份失效）

1. **声明必须可核验**：`MANIFEST.jsonl` 里的 sha256+bytes 必须与该机实际文件一致。
2. **不收无法校验的东西**：没有 sha256 的一律拒收。
3. **未备必须显性**：`COVERAGE.md` 的「未备」不为 0 时，主控简报必须显示；
   **禁止用回执/心跳冒充备份**。
4. **凭据永不上盘**：token/oauth/私钥进不进入归档区，发现即删。
5. **盘未挂载 = 备份停摆**，必须报出来，不得静默跳过当没事。
6. **单件上限 8GB**（收件口硬限）；超过的拆卷或走人工。
7. **保留策略**：暂不自动删除，按日期分目录；盘 595GB，够长期存放。

## 六、部署状态与谁做什么

| 项 | 状态 |
|---|---|
| 收件口 `artifact_intake.py` | **已实现并端到端验证**（正常件落地、哈希错拒收、原子写） |
| 覆盖度核对 `artifact_status.py` | **已实现并验证**（声明 1 → 未备 1 → 推送 → 未备 0） |
| 机队推送器 `artifact_push.ps1` | **已入仓，未在 Windows 机上实跑验证** |
| 各机启用 | 待各机在自己的收口链里调用（见下） |

**主控侧有一个前置条件**：macOS 的 TCC 会拦住 launchd 进程写「可移除卷」，
实测报 `Operation not permitted`。要让收件口常驻自动工作，需一次性在
系统设置 → 隐私与安全性 → 完全磁盘访问权限 中加入 `/usr/bin/python3`。
**未授权时**：收件口只能在有权限的会话里手动启动，备份不能无人值守。

## 七、已知限制（如实）

1. **bm-c 离线期间的产出上不了盘**：COVERAGE 会显示该机未备，恢复上线后补推。
2. **盘会掉电**：这块 USB 机械盘实测曾 70 秒内被断电 4 次。因此落地必须原子化 +
   sha 校验；重传必须幂等（已按 sha 去重）。
3. **HFS+ 只有 Mac 能写**：本设计假定盘常驻主控。若将来要把盘拿到 Windows 机上插，
   必须改格式为 exFAT，届时本规则第二、三层不变，只换成机直写。
4. **推送器未经 Windows 实跑**：首次上机需盯一轮，参数（路径、盘符）按各机实际调整。