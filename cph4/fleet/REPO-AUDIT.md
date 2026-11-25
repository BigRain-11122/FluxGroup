# 全仓体检台账

> 由 `Tools/repo_audit.py --scan` 生成，可随时复算。**本件只报事实，不自动删。**
> 判据写在器里；每条结论都能被负控推翻（见 --self-test）。

- 生成时间：2026-11-25T18:26:52
- 扫描文件：6454 个（不含语料大文件与二进制）

## 汇总

| 项 | 条数 |
|---|---|
| orphan_tools | 190 |
| superseded | 33 |
| duplicates | 299 |
| zero_byte | 19 |
| abs_path | 1126 |
| stale_ref | 0 |
| dangling_link | 0 |
| orphan_high | 0 |
| orphan_stale | 117 |
| orphan_recent | 73 |

## 目录规模

| 目录 | 文件 | 体积 | 最新改动 |
|---|---|---|---|
| cph4 | 4686 | 41.5MB | 2026-11-25 |
| Tools | 1011 | 8.4MB | 2026-11-25 |
| 软著申请材料 | 239 | 6.2MB | 2026-11-24 |
| docs | 137 | 5.9MB | 2026-11-24 |
| house | 84 | 0.9MB | 2026-11-24 |
| .codely-cli | 78 | 0.7MB | 2026-11-25 |
| gaming | 107 | 0.2MB | 2026-11-10 |
| AI-KB | 32 | 0.2MB | 2026-11-08 |
| (root) | 13 | 0.2MB | 2026-11-25 |
| media | 30 | 0.1MB | 2026-11-22 |
| quant | 21 | 0.1MB | 2026-11-22 |
| state | 2 | 0.1MB | 2026-11-24 |
| life | 10 | 0.0MB | 2026-10-30 |
| compute | 2 | 0.0MB | 2026-10-30 |
| domain | 1 | 0.0MB | 2026-10-30 |
| research | 1 | 0.0MB | 2026-10-30 |

## 零引用的 Tools 脚本（疑似过时，删前须再看一眼）

- `Tools/agents/contract_render.py`（6447 字节）
- `Tools/agents/portfolio_archive.py`（3981 字节）
- `Tools/agents/rule_auditor.py`（14168 字节）
- `Tools/duanju_ep01_d3.py`（5660 字节）
- `Tools/face_build_all.py`（3184 字节）
- `Tools/face_fill_gaps.py`（4054 字节）
- `Tools/face_material_quality_study.py`（4651 字节）
- `Tools/face_natural_collect.py`（6496 字节）
- `Tools/face_natural_score.py`（7104 字节）
- `Tools/face_recurate_all.py`（3556 字节）
- `Tools/face_video_fill.py`（4606 字节）
- `Tools/fleet/biggame_onepager.py`（1836 字节）
- `Tools/fleet/bmc_pipeline_evolution.py`（4509 字节）
- `Tools/fleet/check_local_llm.py`（6261 字节）
- `Tools/fleet/gzh_metrics.py`（9263 字节）
- `Tools/fleet/gzh_render.py`（7417 字节）
- `Tools/fleet/gzh_theme.py`（9855 字节）
- `Tools/fleet/gzh_topics_v2_check.py`（7542 字节）
- `Tools/fleet/gzh_visual_check.py`（10946 字节）
- `Tools/fleet/harvest_weread.py`（15414 字节）
- `Tools/fleet/practice_experience.py`（7523 字节）
- `Tools/fleet/seg_propose.py`（9564 字节）
- `Tools/fleet/silence-hook/install_silence_hook.py`（2664 字节）
- `Tools/fleet/taste_dims.py`（13101 字节）
- `Tools/fleet/train_showcase.py`（5224 字节）
- `Tools/gsv_zero_shot.py`（2282 字节）
- `Tools/house/cash_balance.py`（7651 字节）
- `Tools/house/ck_probe.py`（2108 字节）
- `Tools/house/down_payment_lab.py`（9153 字节）
- `Tools/house/equal_principal.py`（6773 字节）
- `Tools/house/ke_cookie.py`（5982 字节）
- `Tools/house/ke_cookie2.py`（5618 字节）
- `Tools/house/ke_login.py`（2918 字节）
- `Tools/house/parse_ke_sector.py`（4893 字节）
- `Tools/house/probe_chengjiao.py`（1653 字节）
- `Tools/house/probe_city_links.py`（1031 字节）
- `Tools/house/probe_clf_query.py`（1541 字节）
- `Tools/house/probe_deals.py`（2373 字节）
- `Tools/house/probe_ke_sector.py`（1824 字节）
- `Tools/house/probe_missing_cities.py`（1767 字节）
- `Tools/house/probe_yinshanhu.py`（1996 字节）
- `Tools/house/probe_zfcj_links.py`（1249 字节）
- `Tools/house/scrape_city_prices.py`（3417 字节）
- `Tools/house/selfuse_calc.py`（4005 字节）
- `Tools/house/selfuse_cost.py`（4672 字节）
- `Tools/mv_cuneiform_stele_v2.py`（12577 字节）
- `Tools/mv_hei_animatic.py`（3265 字节）
- `Tools/mv_hei_d2_v2.py`（9210 字节）
- `Tools/mv_hei_kf_plan.py`（6663 字节）
- `Tools/mv_lyrics_srt.py`（5102 字节）
- `Tools/mv_words_anchor.py`（2411 字节）
- `cph4/fleet/hardware/brain-X9DR3-F/工具/bmc_scan_deep.py`（1980 字节）
- `cph4/fleet/hardware/brain-X9DR3-F/工具/bmc_watch.py`（2800 字节）
- `cph4/fleet/idle-guard-kit/c2082_bank_surgery.py`（3285 字节）
- `cph4/fleet/idle-guard-kit/c2082_bank_surgery2.py`（3441 字节）
- `cph4/fleet/idle-guard-kit/c2092_bank_surgery.py`（7647 字节）
- `cph4/fleet/idle-guard-kit/c2092_bank_surgery_p2.py`（5745 字节）
- `cph4/fleet/idle-guard-kit/c2125_addendum.py`（2391 字节）
- `cph4/fleet/idle-guard-kit/c2137_bank_harvest.py`（3391 字节）
- `cph4/fleet/idle-guard-kit/c2139_closeout.py`（11304 字节）
- ……另 130 条见 JSON

## 同名多版本的低版本（被高版本取代候选）

- `cph4/fleet/COMMAND-CADENCE-v1.json` → 已被 `cph4/fleet/COMMAND-CADENCE-v3.json` 取代
- `cph4/fleet/COMMAND-CADENCE-v2.json` → 已被 `cph4/fleet/COMMAND-CADENCE-v3.json` 取代
- `cph4/fleet/COMMAND-CADENCE-v1.md` → 已被 `cph4/fleet/COMMAND-CADENCE-v3.md` 取代
- `cph4/fleet/COMMAND-CADENCE-v2.md` → 已被 `cph4/fleet/COMMAND-CADENCE-v3.md` 取代
- `cph4/fleet/MODEL-MONITOR-MATRIX-v1.json` → 已被 `cph4/fleet/MODEL-MONITOR-MATRIX-v2.json` 取代
- `cph4/fleet/TEST-PLAN-v1.md` → 已被 `cph4/fleet/TEST-PLAN-v2.md` 取代
- `cph4/fleet/mv-album-001-jay/PIPELINE-DIRECTOR-FLOW-v1.md` → 已被 `cph4/fleet/mv-album-001-jay/PIPELINE-DIRECTOR-FLOW-v2.md` 取代
- `cph4/fleet/mv-album-001-jay/PRODUCTION-SYSTEM-v1.md` → 已被 `cph4/fleet/mv-album-001-jay/PRODUCTION-SYSTEM-v2.md` 取代
- `cph4/fleet/mv-album-001-jay/星晴-SHOTLIST-v2.md` → 已被 `cph4/fleet/mv-album-001-jay/星晴-SHOTLIST-v3.md` 取代
- `cph4/fleet/mv-album-001-jay/黑色幽默-D2-SHOTLIST-v1.md` → 已被 `cph4/fleet/mv-album-001-jay/黑色幽默-D2-SHOTLIST-v2.md` 取代
- `cph4/fleet/mv0001-handover/data/lyrics_v2.ass` → 已被 `cph4/fleet/mv0001-handover/data/lyrics_v3.ass` 取代
- `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v2.py` → 已被 `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v510.py` 取代
- `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v3.py` → 已被 `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v510.py` 取代
- `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v5.py` → 已被 `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v510.py` 取代
- `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v51.py` → 已被 `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v510.py` 取代
- `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v52.py` → 已被 `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v510.py` 取代
- `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v53.py` → 已被 `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v510.py` 取代
- `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v54.py` → 已被 `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v510.py` 取代
- `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v55.py` → 已被 `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v510.py` 取代
- `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v56.py` → 已被 `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v510.py` 取代
- `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v57.py` → 已被 `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v510.py` 取代
- `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v58.py` → 已被 `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v510.py` 取代
- `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v59.py` → 已被 `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/build_full_mv_v510.py` 取代
- `cph4/fleet/mv0001-handover/scripts/build_v6.py` → 已被 `cph4/fleet/mv0001-handover/scripts/build_v10.py` 取代
- `cph4/fleet/mv0001-handover/scripts/build_v7.py` → 已被 `cph4/fleet/mv0001-handover/scripts/build_v10.py` 取代
- `cph4/fleet/mv0001-handover/scripts/build_v8.py` → 已被 `cph4/fleet/mv0001-handover/scripts/build_v10.py` 取代
- `cph4/fleet/mv0001-handover/scripts/build_v9.py` → 已被 `cph4/fleet/mv0001-handover/scripts/build_v10.py` 取代
- `cph4/fleet/social/AGENT-SPEC-v1.json` → 已被 `cph4/fleet/social/AGENT-SPEC-v2.json` 取代
- `cph4/fleet/voicebank/discover/discover_v01.json` → 已被 `cph4/fleet/voicebank/discover/discover_v08.json` 取代
- `cph4/fleet/voicebank/discover/discover_v02.json` → 已被 `cph4/fleet/voicebank/discover/discover_v08.json` 取代
- `cph4/fleet/voicebank/discover/discover_v07.json` → 已被 `cph4/fleet/voicebank/discover/discover_v08.json` 取代
- `cph4/fleet/voicebank/discover/jobs_v01.txt` → 已被 `cph4/fleet/voicebank/discover/jobs_v02.txt` 取代
- `cph4/research/R-20260924-silicon-watch-v5.md` → 已被 `cph4/research/R-20260924-silicon-watch-v6.md` 取代

## 内容完全重复

- 305 字节：`Tools/fleet/fill_loop2.sh` · `Tools/fleet/fill_loop3.sh`
- 8565 字节：`Tools/fleet/patrol_local.py` · `Tools/fleet/patrol_seats.py`
- 2409 字节：`cph4/fleet/CAPABILITY-BRIEF.md` · `cph4/fleet/archive/group/20261110/fab9b4cd-CAPABILITY-BRIEF.md`
- 1133 字节：`cph4/fleet/DAILY-BRIEF.md` · `cph4/fleet/reports/morning-digest-20261111.md`
- 2243 字节：`cph4/fleet/SITREP-142521.md` · `cph4/fleet/archive/group/20261110/3f9d67cd-SITREP-142521.md`
- 2591 字节：`cph4/fleet/_legacy-root-fleet-20261027/mv0001-handover/outbound/A-DIRECTION-v1.1.md` · `cph4/fleet/mv0001-handover/outbound/morning-best/A-DIRECTION-v1.1.md`
- 11033 字节：`cph4/fleet/_legacy-root-fleet-20261027/mv0001-handover/outbound/REVIEW-PACKAGE-v1.md` · `cph4/fleet/mv0001-handover/outbound/morning-best/REVIEW-PACKAGE-v1.md`
- 295 字节：`cph4/fleet/archive/asset-lib/20261107/25510469-vault-verify-20261107.json` · `cph4/fleet/archive/asset-lib/20261108/25510469-vault-verify-20261107.json`
- 548 字节：`cph4/fleet/archive/asset-lib/20261107/33ece8ff-asset-face-2026-11-07.json` · `cph4/fleet/archive/asset-lib/20261108/33ece8ff-asset-face-2026-11-07.json`
- 325 字节：`cph4/fleet/archive/asset-lib/20261107/3c9d8a2d-asset-gen-props-2026-11-07.json` · `cph4/fleet/archive/asset-lib/20261108/3c9d8a2d-asset-gen-props-2026-11-07.json`
- 1515 字节：`cph4/fleet/archive/asset-lib/20261107/7b79adf5-voice-corpus-bm-c-2026-11-07.json` · `cph4/fleet/archive/asset-lib/20261108/7b79adf5-voice-corpus-bm-c-2026-11-07.json`
- 481 字节：`cph4/fleet/archive/asset-lib/20261107/7c79c7b9-asset-caption-2026-11-07.json` · `cph4/fleet/archive/asset-lib/20261108/7c79c7b9-asset-caption-2026-11-07.json`
- 4937 字节：`cph4/fleet/archive/asset-lib/20261107/90316304-asset-index-2026-11-07.json` · `cph4/fleet/archive/asset-lib/20261108/90316304-asset-index-2026-11-07.json`
- 685 字节：`cph4/fleet/archive/asset-lib/20261107/94ba3bc4-voice-corpus-2026-11-07.json` · `cph4/fleet/archive/asset-lib/20261108/94ba3bc4-voice-corpus-2026-11-07.json`
- 252 字节：`cph4/fleet/archive/asset-lib/20261107/a50bddd5-quality-asset-lib-2026-11-07.json` · `cph4/fleet/archive/asset-lib/20261108/a50bddd5-quality-asset-lib-2026-11-07.json`
- 1039 字节：`cph4/fleet/archive/asset-lib/20261107/c5ba6c73-char-gen-plan-2026-11-07.json` · `cph4/fleet/archive/asset-lib/20261108/c5ba6c73-char-gen-plan-2026-11-07.json`
- 3007 字节：`cph4/fleet/archive/asset-lib/20261107/d87c7ff8-asset-library-2026-11-07.json` · `cph4/fleet/archive/asset-lib/20261108/d87c7ff8-asset-library-2026-11-07.json`
- 255 字节：`cph4/fleet/archive/asset-lib/20261109/932a6c59-comfy-bm-c.json` · `cph4/fleet/archive/asset-lib/20261110/932a6c59-comfy-bm-c.json`
- 794 字节：`cph4/fleet/archive/asset-lib/20261109/d70e7b1b-asset-voice-2026-11-09.json` · `cph4/fleet/archive/asset-lib/20261110/d70e7b1b-asset-voice-2026-11-09.json`
- 252 字节：`cph4/fleet/archive/asset-lib/20261110/295960af-quality-asset-lib-2026-11-10.json` · `cph4/fleet/archive/asset-lib/20261111/295960af-quality-asset-lib-2026-11-10.json`
- 1388 字节：`cph4/fleet/archive/asset-lib/20261110/347757d4-GAP-ASSETLIB-P0-20261110.md` · `cph4/fleet/archive/asset-lib/20261111/347757d4-GAP-ASSETLIB-P0-20261110.md` · `cph4/fleet/repairs/GAP-ASSETLIB-P0-20261110.md`
- 2099 字节：`cph4/fleet/archive/asset-lib/20261110/38912ee1-asset-lib-face-dataset-2026-11-08.md` · `cph4/fleet/repairs/asset-lib-face-dataset-2026-11-08.md`
- 75 字节：`cph4/fleet/archive/asset-lib/20261110/52fcf987-asset-lib-asset-gen-2026-11-10-unblock.md` · `cph4/fleet/repairs/asset-lib-asset-gen-2026-11-10-unblock.md`
- 1787 字节：`cph4/fleet/archive/asset-lib/20261110/5334e04b-GAP-CHARGEN-PROBE-20261110.md` · `cph4/fleet/archive/asset-lib/20261111/5334e04b-GAP-CHARGEN-PROBE-20261110.md` · `cph4/fleet/repairs/GAP-CHARGEN-PROBE-20261110.md`
- 1949 字节：`cph4/fleet/archive/asset-lib/20261110/7e7f91d1-asset-lib-library-check-2026-11-08.md` · `cph4/fleet/repairs/asset-lib-library-check-2026-11-08.md`
- 2241 字节：`cph4/fleet/archive/asset-lib/20261110/98863c33-asset-lib-face-dataset-2026-11-10.md` · `cph4/fleet/repairs/asset-lib-face-dataset-2026-11-10.md`
- 42 字节：`cph4/fleet/archive/asset-lib/20261110/9b9b22c4-asset-lib-face-dataset-2026-11-10-unblock.md` · `cph4/fleet/archive/asset-lib/20261111/9b9b22c4-asset-lib-face-dataset-2026-11-10-unblock.md` · `cph4/fleet/repairs/asset-lib-face-dataset-2026-11-10-unblock.md`
- 522 字节：`cph4/fleet/archive/asset-lib/20261110/c3261e46-triage-asset-lib-20261111.md` · `cph4/fleet/archive/asset-lib/20261111/c3261e46-triage-asset-lib-20261111.md` · `cph4/fleet/reports/triage-asset-lib-20261111.md`
- 2328 字节：`cph4/fleet/archive/asset-lib/20261110/d3da5e73-GAP-ASSETLIB-CAP-20261111.md` · `cph4/fleet/archive/asset-lib/20261111/d3da5e73-GAP-ASSETLIB-CAP-20261111.md` · `cph4/fleet/repairs/GAP-ASSETLIB-CAP-20261111.md`
- 4390 字节：`cph4/fleet/archive/asset-lib/20261110/e97bd8d3-asset-index-2026-11-10.json` · `cph4/fleet/archive/asset-lib/20261111/e97bd8d3-asset-index-2026-11-10.json`
- 1797 字节：`cph4/fleet/archive/asset-lib/20261110/f0641574-GAP-ASSETLIB-AUDIT-20261110.md` · `cph4/fleet/archive/asset-lib/20261111/f0641574-GAP-ASSETLIB-AUDIT-20261110.md` · `cph4/fleet/repairs/GAP-ASSETLIB-AUDIT-20261110.md`
- 522 字节：`cph4/fleet/archive/asset-lib/20261111/00730d54-triage-asset-lib-20261111c.md` · `cph4/fleet/reports/triage-asset-lib-20261111c.md`
- 1923 字节：`cph4/fleet/archive/asset-lib/20261111/279448f5-GAP-ASSETLIB-C-20261111.md` · `cph4/fleet/repairs/GAP-ASSETLIB-C-20261111.md`
- 72 字节：`cph4/fleet/archive/asset-lib/20261111/58cac3de-asset-lib-voice-assemble-2026-11-11-unblock.md` · `cph4/fleet/repairs/asset-lib-voice-assemble-2026-11-11-unblock.md`
- 522 字节：`cph4/fleet/archive/asset-lib/20261111/65281a4d-triage-asset-lib-20261111b.md` · `cph4/fleet/reports/triage-asset-lib-20261111b.md`
- 2198 字节：`cph4/fleet/archive/asset-lib/20261111/f161b4b1-asset-lib-env-check-2026-11-11.md` · `cph4/fleet/repairs/asset-lib-env-check-2026-11-11.md`
- 81 字节：`cph4/fleet/archive/asset-lib/20261111/f4ebc27d-asset-lib-face-caption-2026-11-10-unblock.md` · `cph4/fleet/repairs/asset-lib-face-caption-2026-11-10-unblock.md`
- 329 字节：`cph4/fleet/archive/asset-lib/20261114/5fe3c02a-comfy-probe-bm-c-20261112.json` · `cph4/fleet/archive/asset-lib/20261115/5fe3c02a-comfy-probe-bm-c-20261112.json`
- 1362 字节：`cph4/fleet/archive/asset-lib/20261115/1991fd83-asset-env-2026-11-15.json` · `cph4/fleet/archive/asset-lib/20261116/1991fd83-asset-env-2026-11-15.json`
- 2900 字节：`cph4/fleet/archive/asset-lib/20261115/bcfe5082-asset-library-2026-11-15.json` · `cph4/fleet/archive/asset-lib/20261116/bcfe5082-asset-library-2026-11-15.json`
- 794 字节：`cph4/fleet/archive/asset-lib/20261115/f19b57b5-asset-voice-2026-11-15.json` · `cph4/fleet/archive/asset-lib/20261116/f19b57b5-asset-voice-2026-11-15.json`
- 417 字节：`cph4/fleet/archive/asset-lib/20261116/aacd9e4b-voice-corpus-2026-11-16.json` · `cph4/fleet/archive/asset-lib/20261117/aacd9e4b-voice-corpus-2026-11-16.json`
- 1015 字节：`cph4/fleet/archive/asset-lib/20261117/ae4a9c00-char-gen-plan-2026-11-17.json` · `cph4/fleet/archive/asset-lib/20261118/ae4a9c00-char-gen-plan-2026-11-17.json`
- 335 字节：`cph4/fleet/archive/bigcompute/20261109/04e0c8a4-triage-bigcompute-20261109.md` · `cph4/fleet/archive/bigcompute/20261110/04e0c8a4-triage-bigcompute-20261109.md`
- 1146 字节：`cph4/fleet/archive/bigcompute/20261111/fc139b1b-R-PLAN-BIGCOMPUTE-20261111.md` · `cph4/fleet/repairs/R-PLAN-BIGCOMPUTE-20261111.md`
- 434 字节：`cph4/fleet/archive/bigdomain/20261107/507f7040-triage-bigdomain-20261107.md` · `cph4/fleet/archive/bigdomain/20261108/507f7040-triage-bigdomain-20261107.md` · `cph4/fleet/archive/fleet-ops/20261107/507f7040-triage-bigdomain-20261107.md` · `cph4/fleet/archive/fleet-ops/20261108/507f7040-triage-bigdomain-20261107.md`
- 188 字节：`cph4/fleet/archive/biggame/20261107/0161ea18-_已封存_盛永康旧软著.json` · `cph4/fleet/audits/soft/_已封存_盛永康旧软著.json`
- 111 字节：`cph4/fleet/archive/biggame/20261107/025f084e-G26_ExileFarm.json` · `cph4/fleet/audits/soft/G26_ExileFarm.json`
- 112 字节：`cph4/fleet/archive/biggame/20261107/06e3f826-P05_NightWatch.json` · `cph4/fleet/audits/soft/P05_NightWatch.json`
- 6106 字节：`cph4/fleet/archive/biggame/20261107/0a723f14-game-packs-2026-11-07.json` · `cph4/fleet/archive/biggame/20261108/0a723f14-game-packs-2026-11-07.json`
- 113 字节：`cph4/fleet/archive/biggame/20261107/14e87f2b-G16_CrazyEstate.json` · `cph4/fleet/audits/soft/G16_CrazyEstate.json`
- 787 字节：`cph4/fleet/archive/biggame/20261107/1813713c-triage-biggame-20261107.md` · `cph4/fleet/archive/biggame/20261108/1813713c-triage-biggame-20261107.md` · `cph4/fleet/archive/fleet-ops/20261107/1813713c-triage-biggame-20261107.md` · `cph4/fleet/archive/fleet-ops/20261108/1813713c-triage-biggame-20261107.md`
- 112 字节：`cph4/fleet/archive/biggame/20261107/30b273a7-G20_MonsterInn.json` · `cph4/fleet/audits/soft/G20_MonsterInn.json`
- 111 字节：`cph4/fleet/archive/biggame/20261107/34cb3486-G06_ArrowRush.json` · `cph4/fleet/audits/soft/G06_ArrowRush.json`
- 170 字节：`cph4/fleet/archive/biggame/20261107/450f12b7-__pycache__.json` · `cph4/fleet/audits/soft/__pycache__.json`
- 110 字节：`cph4/fleet/archive/biggame/20261107/60125680-G09_GimmeAll.json` · `cph4/fleet/archive/biggame/20261108/60125680-G09_GimmeAll.json` · `cph4/fleet/audits/soft/G09_GimmeAll.json`
- 121 字节：`cph4/fleet/archive/biggame/20261107/71365b8b-G13_我想有个农场.json` · `cph4/fleet/archive/biggame/20261108/71365b8b-G13_我想有个农场.json` · `cph4/fleet/audits/soft/G13_我想有个农场.json`
- 532 字节：`cph4/fleet/archive/biggame/20261107/784c8578-quality-biggame-2026-11-07.json` · `cph4/fleet/archive/biggame/20261108/784c8578-quality-biggame-2026-11-07.json`
- 135 字节：`cph4/fleet/archive/biggame/20261107/7b37e9a1-G16_我有一栋楼_CCPC提交格式.json` · `cph4/fleet/archive/biggame/20261108/7b37e9a1-G16_我有一栋楼_CCPC提交格式.json` · `cph4/fleet/audits/soft/G16_我有一栋楼_CCPC提交格式.json`
- 131 字节：`cph4/fleet/archive/biggame/20261107/8696d994-_报审提交区.json` · `cph4/fleet/audits/soft/_报审提交区.json`
- ……另 239 条见 JSON

## 空文件

- `cph4/fleet/.supply-batch.lock`
- `cph4/fleet/production/logs/PROD-DRAMA-EP002.err.log`
- `cph4/fleet/production/logs/PROD-DRAMA-EP003.err.log`
- `cph4/fleet/production/logs/PROD-DRAMA-EP004.err.log`
- `cph4/fleet/production/logs/PROD-DRAMA-EP005.err.log`
- `cph4/fleet/production/logs/PROD-DRAMA-EP006.err.log`
- `cph4/fleet/production/logs/PROD-DRAMA-EP007.err.log`
- `cph4/fleet/production/logs/PROD-DRAMA-EP008.err.log`
- `cph4/fleet/production/logs/PROD-DRAMA-EP009.err.log`
- `cph4/fleet/production/supervisor.cmd.log`
- `cph4/fleet/voicebank/discover/jobs_v01.txt`
- `cph4/fleet/voicebank/discover/jobs_v02.txt`
- `docs/audits/fused-scan-30d.err`
- `docs/audits/model-pull.log`
- `docs/audits/pull-27b.log`
- `软著申请材料/G15_萌宠开店啦_CCPC提交格式/提交材料/.gitkeep`
- `软著申请材料/G19_我的小花园_CCPC提交格式/提交材料/.gitkeep`
- `软著申请材料/_gen_r996.err.log`
- `软著申请材料/_已封存_盛永康旧软著/P01_镇魂师/提交材料/.gitkeep`

## 硬编码本机绝对路径（换机器就断）

- `.codely-cli/memory/mem-20261017-o-001.md`（1 处）
- `.codely-cli/memory/topics/fleet-dispatcher.md`（1 处）
- `.codely-cli/memory/topics/game-dev.md`（4 处）
- `.codely-cli/memory/topics/git-surgery.md`（1 处）
- `.codely-cli/memory/topics/governance-council.md`（1 处）
- `.codely-cli/memory/topics/mem-20261111-fleet-arch-audit.md`（2 处）
- `.codely-cli/memory/topics/mem-20261115-bm-m-disk-cleanup.md`（1 处）
- `.codely-cli/memory/topics/mv-production.md`（4 处）
- `.codely-cli/memory/topics/quant-backtest.md`（2 处）
- `.codely-cli/memory/topics/train-concurrency-segment-acceptance.md`（1 处）
- `AI-KB/00-identity/01-who-we-are.md`（1 处）
- `AI-KB/90-machine/facts.json`（6 处）
- `AI-KB/INDEX.json`（1 处）
- `CODELY.md`（2 处）
- `REMOTE-EXEC-FIX.cmd`（1 处）
- `REPO-MAP.md`（1 处）
- `Tools/SilentShimRunner.vbs`（1 处）
- `Tools/_pin_v730.py`（2 处）
- `Tools/_pin_v730_fix.py`（1 处）
- `Tools/_r1552_pin_card.py`（1 处）
- `Tools/agents/build_fold.ps1`（2 处）
- `Tools/agents/register_game_loops.ps1`（1 处）
- `Tools/ai_smell_gate.py`（2 处）
- `Tools/aigc_label.py`（3 处）
- `Tools/asset_index.py`（5 处）
- `Tools/audit-sentinel.ps1`（1 处）
- `Tools/automation_health.py`（4 处）
- `Tools/banned_waste.py`（1 处）
- `Tools/bench_coder.py`（1 处）
- `Tools/bili/bili_repurpose.py`（3 处）
- `Tools/bmd-bootstrap.ps1`（1 处）
- `Tools/cloud-off-gate.ps1`（1 处）
- `Tools/coder-serve.ps1`（3 处）
- `Tools/comfy_mode.py`（3 处）
- `Tools/decisions-arch-certify.py`（1 处）
- `Tools/decisions_split_once.py`（1 处）
- `Tools/decisions_trim_20261027.py`（1 处）
- `Tools/delivery-watch.ps1`（1 处）
- `Tools/director.py`（2 处）
- `Tools/duanju_ep01_d3.py`（1 处）
- `Tools/face_build_all.py`（2 处）
- `Tools/face_fill_gaps.py`（1 处）
- `Tools/face_lora_train.py`（3 处）
- `Tools/face_material_quality_study.py`（2 处）
- `Tools/face_natural_collect.py`（1 处）
- `Tools/face_natural_score.py`（1 处）
- `Tools/face_recurate_all.py`（2 处）
- `Tools/face_source_batch.py`（2 处）
- `Tools/face_source_collect.py`（2 处）
- `Tools/face_video_collect.py`（3 处）
- `Tools/face_video_fill.py`（2 处）
- `Tools/fleet-agent-c.cmd`（2 处）
- `Tools/fleet-align.ps1`（4 处）
- `Tools/fleet-dispatch.ps1`（2 处）
- `Tools/fleet-dispatcher.ps1`（1 处）
- `Tools/fleet-idle-watch.ps1`（1 处）
- `Tools/fleet-node-status.ps1`（1 处）
- `Tools/fleet-nodes.json`（5 处）
- `Tools/fleet-oversight.ps1`（4 处）
- `Tools/fleet-reality.ps1`（2 处）
- ……另 1066 条见 JSON

## 引用了不存在的文件

（无）

## 断链软链

（无）

---

## 怎么用这份台账

1. 先看**硬编码绝对路径**与**断链**：这两类是错误，不是风格问题，优先修。
2. 再看**零引用**与**低版本**：这是「过时」的候选，但删前必须人看一眼（动态调用识别不到）。
3. 清理一律**移到 `_archive-YYYYMMDD/` 并写台账**，不硬删——可回滚比省空间重要。
