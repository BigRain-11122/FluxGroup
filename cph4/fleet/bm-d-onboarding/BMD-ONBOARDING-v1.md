# BMD-ONBOARDING-v1 — bm-d 六卡机上机手册（2026-10-16 21:48 立·O-20261016-2148-bm-a）

> 正典=C-20261016-01（bm-d 六卡机分层分配定谳案·大脑机+草稿厂+回测厂）；本件=执行手册（Tier1→Tier2→Phase1 分期+验收）。
> bm-d 硬件（CEO 配置）：3×V100 16G + 3×P104 8G + 2×E5-2695v2（**24C48T·无 AVX2**）+ 256G DDR3 RECC + 512G SSD。
> 定位对金融公司：**L3/L4 CPU+RAM=BigMoney 回测厂主承接**（O-20261015-1055 金融 CPU 排满令·W 波链+千人题库/矩阵线·256G 解 RAM-GATE）。

## 一、当前态（2026-10-16 21:4x 实测）
- **bm-d 未入 tailnet**（bm-a `tailscale status` 仅三节点）=唯一物理缺口——入网前机队无法触达（办公网 10.86.96.0/22 大段无凭据不可直连·机队法律通道唯一=tailnet）。
- 本窗已备四件：①一键引导脚本 Tools/bmd-bootstrap.ps1（CDN 直链见 §二）②fleet-nodes.json bm-d 行（enabled=false·候 IP 由 join-report 回填）③resource-chain §9.1 bm-d 车道行（RAM>8G 分片归口改道 bm-d 首选）④本手册。

## 二、CEO 唯一物理步骤（一条命令·bm-d 上管理员 PowerShell）
```powershell
iwr 'https://tuanjie-ai-prd.tos-cn-shanghai.volces.com/mcp-upload/7072ec79f02223f6bea2dbee7817b809/bmd-bootstrap.ps1' -OutFile bmd-bootstrap.ps1; .\bmd-bootstrap.ps1
```
- 脚本全程幂等可重跑；会引导两次登录（Tailscale 浏览器一次 + GitHub 浏览器一次·均用集团账号）。
- 自动完成：规格盘点落盘（CPU/RAM/六卡+ECC/磁盘/OS=「好好看看」实数据）→ 24/7 电源档 → 入 tailnet（拿 100.x IP）→ git → 双仓 clone（FluxGroup+BigMoney 落 C:\Fluxgroup\FluxGroup）→ **join-report 上链**（JOIN-REPORT-<时间戳>.md）→ FleetLink :8790 监听器注册（S4U）+自检。

## 三、Tier 1 完成后（机队侧自动接线·≤10 分钟）
- 各循环班见 join-report 即执行（O-20261016-2148 §三）：回填 fleet-nodes.json bm-d 行（host/tailnet_ip/enabled=true）+pathspec 推送+poke bm-d :8790 /health 验证。
- bm-d 即成机队第 4 节点（秒级可指挥·心跳面+IdleWatch+自领引擎纳入）。

## 四、Tier 2（金融回测厂开线·需 codely CLI 登录一次）
- codely CLI 装机+登录（CEO 账号）→ 按宽拷 bm-b/bm-c 任务定义注册 BM 循环班（Bigmoney-IterationLoop/SaturationEngine 等宽）→ 心跳入 quant/bigmoney/fleet/machines/bm-d.json → **BM 席位协议纳入 W 波轮换**（链序律不变·bm-d 领回测主承接位）。
- RAM>8G 分片（screens/JUDGE 类）自 bm-d 在队起改道 bm-d 首选（256G）·bm-a 降 fallback。
- 验收（case §九）：W 波单机吞吐 vs bm-b/c 基线对照（py≥70% 满载审计线）。

## 五、Phase 1（大脑线·case §六 先行正典路径·Tier 2 后排）
- Windows+R580 数据中心驱动（V100 TCC）→ llama.cpp 自编 sm_70 → 35B Q8 三卡验收 ≥70字/秒+-np4 24h 稳 → LiteLLM 网关接线 → 各机 BRAIN_URL 一行切 bm-d → bm-a :8090 退役。
- 模型下载：ModelScope unsloth 镜像（35B Q8 ≈37G）——可由 bm-a 预下载后 Taildrop 中继（候 bm-d 入队再执行·免 bm-d 侧走 GFW 慢道）。

## 六、验收判据（case §九 预注册·装机后回填 orders）
| 面 | 判据 |
|---|---|
| Tier1 | bm-d 入 tailnet+listener /health 200+join-report 上链（CEO 一条命令后 ≤10 分钟全自动） |
| Tier2 | 心跳入 fleet/machines/bm-d.json+席位轮换纳入+RAM 分片改道生效 |
| 回测厂 | W 波单机吞吐 vs bm-b/c 基线（py≥70% 满载审计线） |
| 大脑 | 35B Q8 三卡 ≥70字/秒+24h 稳+盲测 10 件记档（Phase 1） |
| 全机 | 六卡 72h 拷机零 ECC/零掉卡（Phase 0 实测回填） |

## 七、坑律速记（case §八 提炼）
- **P104-101（4G 变体）=无 AI 价值**——Phase 0 设备消歧（nvidia-smi 名串+GPU-Z+卡身标签）·命中即退出草稿厂按残值处置。
- E5-2695v2 无 AVX2 → llama.cpp CPU 卸载路线禁（全 GPU 驻留路线）。
- 512G SSD 配给律：OS+工具 80G/模型库 110G/工作区 120G/保留 ≥15%——**回测数据集不驻本盘（留 bigmoney 域）**·扩盘触发线=剩余 <20% 才提 2T SSD。
- 六卡分线供电（禁共线）+功率墙（V100 150-200W/P104 135W 压 nvidia-smi -pl·94°C 上限）。
- P104 单 8pin=推定·装机实物核（case §三 L6）。
