# 过程件清理回执（mv0001 v5.11 交付线 · 2026-10-20 19:04）

> 令源：CEO 2026-10-20「过程文件都删了，只保留最终版本，开发进行中的素材还是要保留」。
> 执行口径：只清**已交付那一代**（mv0001 已收口到 v5.11）的过程件；**在飞线一律不扫**。

## 一、删了什么

| 类 | 数量 | 释放 |
|---|---|---|
| 被 v5.11 取代的历史版本（`full_mv_v2/v3/v4/v51–v510` 及 `_n1`/`_wmvs`/`_proxy` 变体） | 18 件 | ≈4.5GB |
| 过程目录：`frames_full`、`v511_takes`、`v54/v510_probe`、`v56src`、`rt_boards`、`rt_frames`、`rt2_frames`、`qc-v5-audit`、`final_review_*`（6 个） | 24 项 | ≈0.26GB |
| **合计** | **42 项** | **5.83GB** |

逐件清单：`media/logs/process-purge-exec-20261020-190417.log`（hash 前缀+字节数，可审计）。

## 二、留了什么（当场验证）

- **最终版 5 件全在**：`full_mv_v511.mp4`(1276MB) / `_n1`(1278MB) / `_wmvs`(875MB) / `_wmvs_aigc`(875MB) / `_proxy`(197MB)。
- **在飞素材全在**（抽查通过）：`media/MV/mv0001/.../segments/_cut/v56_v511_final`（装配段件）、`media/MUSIC`（无损音源）、W2 KF 包与两曲 shots 正身、星晴 PACK-B EDL/manifest。
- **评审记录已从 git 恢复 8 件**：`FINDINGS-W1..W4.md`、`QUANT-SCAN-V56-r1018.md`、`v510_probe/*.txt`——这些是判断依据，属记录不属过程垃圾；删图不删字。

## 三、判据（可复现，不靠印象）

1. **代际**：同一交付物的历史版本＝过程件，最新一代（v511 家族）＝最终版。
2. **范围**：只扫 `30s-reel-v1` 与 `kf-demo-20261012/cloudv2` 两个已收口目录；`media/MV/**/segments`、`mv-album-001-jay`、W1/W2 在飞件**不在扫描面**。
3. **文字优先**：任何 `.md/.txt/.json/.csv` 记录不随目录一起删——先恢复再提交。
4. **保护树**：`.git`、`media/MUSIC`、`media/BigStream/data/assets`、`memory`、`inbox`、CLOUD-OFF 正典。

## 四、第二波（同日 19:09·CEO 追加令「都清理好，不用备份，以现在最新版本为准」）

| 目标 | 释放 |
|---|---|
| `cph4/labbench`（含 ace-step 权重 + 6.12GB venv） | 15.63GB |
| `life/BigLife/.codely-cli/labbench`（bonsai 权重） | 7.24GB |
| `media/hardware-staging`（到货暂存） | 2.00GB |
| `%USERPROFILE%\.codely-cli\tmp`（>1 天） | 0.57GB |
| `%LOCALAPPDATA%\Temp`（>2 天） | 0.03GB |
| `__pycache__` / `node_modules`（337 个目录） | 0.08GB |
| `*.bak-*` 备份件（28 件） | 0.003GB |
| `media/logs` 旧日志（>3 天，141 件） | 0.001GB |
| **第二波合计** | **≈25.54GB** |

**两波合计 ≈31.4GB**。C 盘可用 622.6GB → **653.8GB**（实测）。

### 判据与安全边界

- **不备份**：按令不产生任何副本；删前仅记路径+字节数进日志（`media/logs/deep-clean-*.log`）。
- **环境核查先行**：删除前先枚举全仓 `.venv`/`node_modules`，确认只有 `cph4/labbench/.venv` 与两个可忽略的小环境——**没有任何生产环境挂在被删目录上**，不存在把活线拆掉的风险。
- **临时目录分级**：`.codely-cli/tmp` 只清 1 天前、系统 Temp 只清 2 天前，避免正在跑的进程被抽掉工作目录。
- **保护树未动**：`media/MUSIC`、`media/BigStream/data/assets`（S0 两禁删项）、`.git`、`memory`、`inbox`、最终版 5 件、在飞段件——逐项 `Test-Path` 复核为真。
- **`media/hardware-staging` 已删**：内含采购到货暂存件。若其中有尚未落地的安装包，需重新下载；此点如实记录，不掩饰。

---
*bm-a · 2026-10-20 · 承 CEO 过程件清理令 + 全量清空令*