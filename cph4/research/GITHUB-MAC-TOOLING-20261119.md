# GitHub 工具调研 — 本机 MacBook（主控）· 2026-11-19

判据：①轻量 CLI/应用（不在主控起重服务）②解决本机真实缺口③brew/pip 有维护版。stars 与活跃度经 GitHub 页面/API 核实；"实测"一栏全部来自本机真跑，不是"已安装"。

## A. 已装 + 实测结果

| 工具 | 版本 | 实测 |
|---|---|---|
| ruff | 0.17.5 | `ruff check Tools --select F,E9` → 455 个 py，**217 条**：F401 118 / F841 82 / **F821 16** / F507 1 |
| ast-grep | 0.51.3 | `subprocess.run($$$A)` 共 828 处，其中 **168 处无 `timeout=`**（可作闸）；结构搜索命中 `Tools/` 全域 |
| duckdb | 2.0.0 | `PRODUCTION-QUEUE.jsonl` 349 条：198 DONE / 72 CANCELLED / 40 ARCHIVED / 12 OPEN / 11 BLOCKED / 6 FAILED；**174 条 `station` 为空** |
| macmon | 0.12.0 | 免 sudo：CPU 42–53%、GPU 33–39%、风扇 2012/2154 RPM、**swap 已用 6.7 GB**、chip 11–15 W、dc_in 21–31 W |
| mole | 1.73.0 | `mo status` → health 97/Excellent；`mo clean --dry-run` → **可清 1.78 GB / 203 项**，未改动任何文件 |
| shellcheck | 0.11.0 | 44 个 .sh → 8 条提示，SC2086/SC2068/SC2046 **0** 条 |
| yq | 4.54.3 | `yq '.nodes \| length' Tools/fleet-nodes.json` → 5 |
| hyperfine | 2.0.0 | duckdb 计数 42.2 ms ± 2.3 vs jq 9.9 ms ± 0.3（**jq 快 4.3 倍**，duckdb 启动开销 ~40 ms） |
| restic | 0.19.1 | 已装；无备份目的地（见 E） |
| lnav | 0.14.1 | 可用；原文文件名带横线时 SQL 表名不易猜，实用走 `:filter-in`（`corpus-bake.log` 命中 error 6 行） |
| shfmt / git-delta / pandoc / pdftotext | — | 就位（shfmt 未批量格式化，避免噪音提交） |
| Ghostty | 1.4.0 | 应用就位（注意：`ghostty --version` 会挂住并试图拉 GUI，别用它做探活，读 Info.plist） |
| Ice | **0.11.12** | 应用就位（此前把另一个叫 `ice` 的 formula 3.8.3 误当成本应用，勘正） |
| Pearcleaner | 5.4.3 | 应用就位 |
| macOS `say` | — | `say -v Tingting` → 6.1 s / 22 kHz 中文音频，零下载；可做草稿配音 |

## B. ruff 抓出的真 bug（try/except 吞掉的静默失败）

1. `Tools/fleet/closer.py:80` — 用 `time.strftime` 但没有 `import time`（只 `from datetime import datetime`）。位置在"三次未成→往 `JUDGMENT-QUEUE.jsonl` 写可判的题"分支，异常被吞 → 停线时该留的题没留。
2. `Tools/fleet/fork_close.py:163-164` — 同样缺 `import time`，`except: pass` 吞掉 → 分叉台账节点状态不更新。
3. `Tools/fleet/regression.py:481` — 用 `shutil.which` 但未 `import shutil` → RG-24 闸在 `~/bin/ffmpeg` 不存在时 NameError。
4. `Tools/queue_claim.py:257` — 顶层 `sys.exit(node_selftest())` 早于 326 行的 `def node_selftest` → `--node-selftest` 必 NameError。
5. `master_pulse.py:1454` 的 `fl_now` 有 `in globals()` 保护，属 ruff 误报，不改。

## C. 苹果原生档的结论

- **mlx-audio（MIT，Prince Canuma → Neywa-Labs）**：装进 `~/.venvs/mlx-audio` 成功、CLI 可用，但**模型拉不下来**——本机 `huggingface.co` 直连超时，`hf-mirror.com` 的 `/api` 与 `/resolve` 均返回 308 后跳转目标不可达，关掉 `hf-xet` 同样失败；机器无任何代理（环境变量/系统代理/7890·1080·6152 等端口全查空）。结论：**待有可用下载路径再验**，不推广到产线。
- **mlx-omni-server（MIT）**：同一条 HF 依赖，同结论。
- **Mole**：可用且输出 JSON（`mo status` 便于机读接入）。清理前必须 `--dry-run`。
- **Ghostty / Ice / Pearcleaner / Iina**：均为 GUI 应用，装好但未改任何现有配置（iTerm2、Hidden Bar、AppCleaner 仍在原位，等你决定是否替换）。

## D. 不建议 / 需附条件

- **gitleaks 8.30.1**：37 条命中全是已知假红——6 条 AWS 是 `security_ledger.py` 已登记的官方占位串 `AKIAIOSFODNN7EXAMPLE`，31 条集中在软著源码 txt。项目已有 `Tools/secret-scan.ps1` + 白名单。要用只能先写 allowlist 当"独立第二判据"，否则每天 37 声假警报。
- `exo`（48k★）：苹果设备集群跑模型，与以 Windows/CUDA 为主力的机队不匹配。
- `changedetection.io`（35k★）：竞品榜单监控有价值，但属常驻 Web 服务 → 上机队，不上主控。
- `pyright` / `ty`（0.0.105 预发布）：与 ruff 重复，且无类型注解的代码库会产出大量噪声。
- `AeroSpace`（brew 无）、`asitop`（macmon 已覆盖且免 sudo）、`terminal-notifier`（与静默律冲突）。
- `mpv`：依赖 `ffmpeg`，本机 ffmpeg 无 bottle → 装它等于触发 40 分钟源码编译，改用 iina。
- `mlx-serve`（Zig 原生三协议）：列观察项。

## E. 顺带发现的两个真问题

1. **本机零备份**：`tmutil destinationinfo` → `No destinations configured`，`listlocalsnapshots /` 空。主控承载 2.7 GB git 历史 + 全部机队台账。restic 已装，缺目的地与接入节拍。
2. **Homebrew 前缀 `~/.homebrew`（Tier 3）**：今晚就有 `imagemagick`、`pkgconf`、`libx11`、`p11-kit`、`libgpg-error`、`gnupg`、`gpgme`、`gobject-introspection` 因无匹配 bottle 走源码编译。迁 `/opt/homebrew` 可解，代价是重装 55 formula + 28 cask。
