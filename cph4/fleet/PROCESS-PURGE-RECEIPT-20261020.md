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

## 四、还没动的（等你传完网盘再执行）

`Tools/local_cleanup_r1020.ps1` 管的那 34.4GB：labbench 权重、venv/node_modules、hardware-staging、tmp、系统 Temp。这些是**可重建**件，不是过程件，按你「传完再清」的次序走，且需 `.uploaded-ok.json` 凭据才允许删。

---
*bm-a · 2026-10-20 · 承 CEO 过程件清理令*