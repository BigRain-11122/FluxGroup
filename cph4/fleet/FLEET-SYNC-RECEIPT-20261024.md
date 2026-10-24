# 机队全量同步回执（CEO 令 2026-10-24 12:1x「彻底同步，不要有遗漏，共享所有记忆和文档」）

签发：bm-a｜执行时点：2026-10-24 12:10–12:35（北京时间）

## 一、数据通道（git = 唯一数据通道，FleetLink 只发信号）

| 仓库 | bm-a 本机最终态 | 推送 | bm-c 到件 | 说明 |
|---|---|---|---|---|
| `.`（HQ 总控/文档/记忆正典） | 392d8549 | ✅ | ✅ 392d8549（0 ahead / 0 behind） | 含 orders、cph4、Tools、记忆镜像 |
| `gaming/FluxVerse` | a7383446 | ✅ | ✅ a7383446 | |
| `quant/bigmoney` | 5270a15d | ✅（落后 20 笔已 rebase 追平后推） | ✅ 5270a15d | |
| `life/BigLife` | 894e0964 | ✅ | ✅ 894e0964 | |
| `media/BigStream` | 0960877e | ✅ | ✅ 0960877e | |
| `compute/BigCompute` | f4189651 | ✅ | ✅ f4189651 | |
| `domain/BigDomain` | 6958c4bc | ✅ | ✅ 6958c4bc | |
| `gaming/MiniGame` | 4ae00b8f（master） | ✅ | ⚠️ 6222c2b（`machine/C` 分支） | 见 §三.1 |
| `house/BigHouse` | 3634120f | ✅ | ❌ 本机无该仓 | 见 §三.2 |
| `bm-b` 全机 | — | — | ❌ Tailscale 离线（last seen 1d） | 见 §三.3 |

bm-a 本机 8 仓本轮共落账：root 49 件（含 3 次提交）、BigStream 68、FluxVerse 13、BigDomain 7、BigLife 4、BigCompute 2、bigmoney 2、MiniGame 1。
按 REPO-SLIM 律**不入 git**：MV 成片 v514/v515/v516/v517/v518（623–728MB/件）、jitter-clips（23.7MB）、BigStream `release/`（21.4MB 单件）、`original-mv/`+`era-ref/` 源媒体（>5MB 二进制）。

## 二、记忆共享（合规口径）

- **L1 项目层**：仓根 `CODELY.md`（73KB）随 `.` 仓 git 分发，三机同源。
- **L2 主题层**：新增只读镜像 `cph4/fleet/memory/topics/`（30 件，0.57MB）——解决「L1 索引指向 `<home>` 路径、他机取不到原文」的断链。
- **机器快照**：`cph4/fleet/memory/machine-snapshots/bm-a/`（L0 44.8KB / L1 73.1KB 全文快照），供跨机交接与考古。
- **L0 注入层**：仍各机本地治理（`Tools/memory-budget-gate.py` + 4h 闸 + memory-curator）。联合回灌/union replace-down **永久退役，本轮未复活**（CEO 令 2026-10-18，红线）。

## 三、未闭合项（诚实边界，均非本机可单方面修）

1. **bm-c `gaming/MiniGame` 走的是 `machine/C` 分支**：`origin/machine/C`=6222c2b（1 笔独有），`origin/master`=4ae00b8（领先 2925 笔）。这是 bm-c 的分支策略而非拉取失败——若要 bm-c 跟上 master 的最新玩法/生产线代码，须在 bm-c 侧把 master 合入 `machine/C`（owner 动作，远端无命令通道）。
2. **bm-c 无 `house/BigHouse` 工作树**：roster 已加（poke `-Repos` 白名单已放行），但目录不存在时 worker 记 `:no-repo` 并跳过；克隆须在 bm-c 侧执行。
3. **bm-b 整机离线**（Tailscale 1 天未见）：dispatch fail-soft 记为 fail=1。开机联网后一次 `fleet-dispatch -Repos ...` 即可补齐；本轮所有提交已在 origin，无需重做。
4. **媒体件按规不入 git**：跨机取用走 D 盘本地路径或 CDN 地址，不经仓。

## 四、配置变更
- `Tools/fleet-nodes.json`：bm-b / bm-c 的 `repos` 白名单从 1–2 仓扩到全部 8 个产品仓，使 poke 强制拉取覆盖全仓（此前 5 仓被判 `force-deny`）。
- 记忆镜像与快照目录的刷新口径写入 `cph4/fleet/memory/topics/README.md`。