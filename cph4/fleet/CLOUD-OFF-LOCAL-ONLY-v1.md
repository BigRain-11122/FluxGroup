# 云端停用·全面本地化令（2026-10-20·CEO 令）

> **CEO 原话**：「集团业务全部停止走云端，全部走本地了」
> 级别：**T0 集团级政策令·即日生效**。本件为唯一权威口径；与既往「云端放开」类令冲突时，本件优先。

## 一、令的内容

1. **一切业务生成/推理走本地机队**（bm-a / bm-b / bm-c 及后续入网机）；云端 API（视频生成、图像生成、TTS、云端 LLM、云端存储）**停止用于业务生产**。
2. **不得自行切云**：本地不可用/排满/装不下时，动作=**排队 + 报障**，不是自动回落云端。需要例外一律由 CEO 亲批，逐案、限期、留痕。
3. 已购/已配的云端额度与订阅不删除，**冻结备用**；不新增采购。

## 二、被本令覆盖（停止执行）的既往口径

| 既往令 | 内容 | 状态 |
|---|---|---|
| O-20261013-2245 | 「云端放开」并行量产 | **废止** |
| O-20261016-2145 | 游戏公司云道授权（并发受控） | **废止** |
| 2026-10-16 23:59 本地故障→云端恢复律 | 本地故障即切云端续产 | **废止**（改为排队报障） |
| 2026-10-15 token 严管 v3.0 的「白名单免试」 | 部分场景允许云端 | **仅保留为冻结档**，不再执行 |
| 各线默认「云端正式镜头主力」 | MV/H3/Seedance 主路 | **废止·改本地** |

## 三、本地能力对照（现状·2026-10-20）

| 能力 | 本地载体 | 状态 |
|---|---|---|
| 关键帧图像（KF） | bm-c Krea2 turbo INT8（1344×768；可升 2k 待评估） | 在役 |
| i2v 视频 | bm-c INT8 768P 既有链；Wan2.2-Animate（18k★/Apache-2.0，pose+face 双驱动）待装机 | 在役 / 待装机 |
| 图像编辑/修图 | bm-c（Qwen-Image 侧车已上线） | 在役 |
| 口型 | LatentSync（Apache-2.0）本地单镜试点 | 待试点 |
| LLM 推理 | bm-a 35B coder :8090 | 在役 |
| whisperX 词锚 | bm-b | 在役 |
| 节拍/结构 | bm-b madmom（注意模型 CC BY-NC-SA 禁商用） | 在役（内测） |
| 调色/装配/编码 | bm-a CPU | 在役 |

**硬约束**：bm-a 工作日白天零排单；bm-c 16G 显存是 i2v 主战场；bm-b 只有 8G，别派 i2v。

## 四、各条线的影响与替代（不是口号，要落到"哪个模型替哪个"）

- **MV/H3/Seedance 云端镜头** → 改本地 INT8 768P；原云端 Context-IR 类镜头改"本地烧 + 后期修"或改分镜规避（把需要云端强一致性的镜拆成两个本地可做的镜）。
- **游戏/短剧/漫剧的图像与视频** → 全部落 bm-c；批量前先 480P 低清验证（既有效率律不变）。
- **TTS/配音** → 本地 TTS 链（现有本地栈），不再走云。
- **云端 LLM（研究/评审/写作）** → 本地 35B 优先；质量不够时的处理=人工复核 + 拆小任务，不切云。
- **云端存储/CDN** → 交付改本地路径 + 局域网/tailscale 直传。

## 五、迁移清单（按此顺序执行）

1. **盘点在飞云任务**：逐条列"哪个任务、哪个模型、能否本地替、替不了怎么办"。
2. **停云开关**：各线派单模板里的云端分支默认关；派单前查本令。
3. **装机补齐**：Wan2.2-Animate（i2v 表演控制）、LatentSync（口型）先装 bm-c，装不下再评估 bm-a 夜窗。
4. **本地产能预算**：按 GPU 日利用率算可支撑的每日镜头数，超出=排队，不许偷偷上云。
5. **留痕**：任何一次云端调用都要能在台账里查到"谁批的、为什么、花了多少"；无痕=违令。

## 六、例外流程（唯一合法通道）

- 提出：写清「哪一镜/哪一步、本地为何做不了、云端方案、预估成本、时限」。
- 批准：CEO 亲批（口头也算，事后补一行台账）。
- 执行：单次、限期、用完即停；不得变成常设通道。
- 违令判定：未经批准调用云端 = T0 违规，当窗停线复盘。

## 七、与既有制度的关系

- **不动**：静默律 / 让路律 / 账号安全令 / 数据本地化 / 大文件红线 / 三层记忆制度 / 产出计分口径。
- **强化**：本地机队满载与自愈（既有 IdleWatch/dispatcher 照常）；本地故障不再有"切云"这条退路，**故障=最优先修**。

## 八、自动化闸门（2026-10-20 18:3x 落地·CEO 追加令「自动化任务全部走本地，不要再消耗云端 token」）

### 8.1 闸门形式

- **开关=本文件是否存在**：脚本从自身目录向上找仓库根，命中 `cph4/fleet/CLOUD-OFF-LOCAL-ONLY-v1.md` 即在拉起云端会话前退出。
- **拦点=Start-Process 之前**：本地前置工作（读旗、锁、预算、pulse、日志）照常完成，只掐掉云端回合。
- **留痕**：每次拦截写一行 `media/logs/cloud-off-suppressed.log`（时刻｜脚本名｜suppressed cloud round）。
- **解除**：删除或改名本文件即恢复；不必逐台改计划任务，也不必重新注册。

### 8.2 已加闸的 16 个自动化脚本

| 线 | 脚本 |
|---|---|
| 调度/巡视 | `Tools/patrol-runner.ps1`、`Tools/patrol-fleet-carrier.ps1`、`Tools/proxy-event-carrier.ps1`、`Tools/shift-supervisor.ps1`、`cph4/decision-round.ps1`、`cph4/evolution-tick.ps1`、`cph4/night-round.ps1` |
| 子公司循环 | `media/BigStream/src/os/iteration_loop.ps1`、`life/BigLife/Tools/iteration_loop.ps1`、`domain/BigDomain/src/os/iteration_loop.ps1`、`compute/BigCompute/Tools/iteration_loop.ps1`、`quant/bigmoney/Tools/iteration_loop.ps1`、`gaming/FluxVerse/Tools/devloop/iteration_loop.ps1` |
| 游戏 | `gaming/MiniGame/tools/EngineTick.ps1`、`ModeTick.ps1`（8 个 MiniGame 定时任务共用）、`BoardForge.ps1` |

### 8.3 不受影响的自动化（本地/免费）

- `HQ-FleetDispatcher`（规则路由，零 LLM）、`HQ-FleetIdleWatch`（本机 HTTP 探测）、`HQ-MemoryBudgetGate`、`HQ-SilenceGuard`、`HQ-WT-Park`、`HQ-bm-a-Sentinel`、`HQ-OllamaOrphanWatch`、`HQ-OpenClaw-*`（本地 8090 网关）。
- 各司纯 CPU/脚本循环（回测、清理、同步、看板）照跑。

### 8.4 仍然会消耗云端 token 的只剩

- **人开的交互会话**（本窗口及 `--experimental-acp` 编辑窗）——这是执行者本体，不是自动化。若要求连它也断，需要换本地模型跑 CLI，属另一件事，须 CEO 明确。

### 8.5 验证

- 16 个脚本 PowerShell 解析：0 错误。
- 闸门自测：退出码 0，日志落行 `_cloudoff_guard_selftest.ps1 | suppressed cloud round (T0)`。
- 加闸后现场：5 个 `codely.exe` 全为 `--experimental-acp` 交互窗，无 `-p` 无头回合。

---
*立令 bm-a · 2026-10-20 · 执行面=全集团各线派单模板 + 各产线正典抬头注记 + 自动化脚本闸门（§八）*