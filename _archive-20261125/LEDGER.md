# 归档台账 2026-11-25（第一批·可逆）

> 只动高置信项：0 字节 Python、被高版本取代的 MV 主控、名字即一次性的脚本。
> **没有删任何文件**，全部 `git mv` 到本目录；回滚见文末。

| 原路径 | 归档到 | 类别 | 理由 |
|---|---|---|---|
| `Tools/resident_loop.py` | `_archive-20261125/empty-python/resident_loop.py` | empty-python | 0 字节，无实现也无引用 |
| `Tools/work_scheduler.py` | `_archive-20261125/empty-python/work_scheduler.py` | empty-python | 0 字节，无实现也无引用 |
| `Tools/mv_master_v722.py` | `_archive-20261125/superseded-mv/mv_master_v722.py` | superseded-mv | 已被 mv_master_v730.py 取代 |
| `Tools/mv_master_v723.py` | `_archive-20261125/superseded-mv/mv_master_v723.py` | superseded-mv | 已被 mv_master_v730.py 取代 |
| `Tools/mv_master_v727.py` | `_archive-20261125/superseded-mv/mv_master_v727.py` | superseded-mv | 已被 mv_master_v730.py 取代 |
| `Tools/mv_master_v728.py` | `_archive-20261125/superseded-mv/mv_master_v728.py` | superseded-mv | 已被 mv_master_v730.py 取代 |
| `Tools/mv_master_v729.py` | `_archive-20261125/superseded-mv/mv_master_v729.py` | superseded-mv | 已被 mv_master_v730.py 取代 |
| `Tools/mv_rebuild_v718.py` | `_archive-20261125/superseded-mv/mv_rebuild_v718.py` | superseded-mv | 已被 mv_rebuild_v732.py 取代 |
| `Tools/mv_rebuild_v719.py` | `_archive-20261125/superseded-mv/mv_rebuild_v719.py` | superseded-mv | 已被 mv_rebuild_v732.py 取代 |
| `Tools/mv_rebuild_v720.py` | `_archive-20261125/superseded-mv/mv_rebuild_v720.py` | superseded-mv | 已被 mv_rebuild_v732.py 取代 |
| `Tools/mv_rebuild_v721.py` | `_archive-20261125/superseded-mv/mv_rebuild_v721.py` | superseded-mv | 已被 mv_rebuild_v732.py 取代 |
| `Tools/mv_rebuild_v727.py` | `_archive-20261125/superseded-mv/mv_rebuild_v727.py` | superseded-mv | 已被 mv_rebuild_v732.py 取代 |
| `Tools/mv_rebuild_v728.py` | `_archive-20261125/superseded-mv/mv_rebuild_v728.py` | superseded-mv | 已被 mv_rebuild_v732.py 取代 |
| `Tools/mv_rebuild_v729.py` | `_archive-20261125/superseded-mv/mv_rebuild_v729.py` | superseded-mv | 已被 mv_rebuild_v732.py 取代 |
| `Tools/mv_rebuild_v730.py` | `_archive-20261125/superseded-mv/mv_rebuild_v730.py` | superseded-mv | 已被 mv_rebuild_v732.py 取代 |
| `Tools/_night_report_20261108.py` | `_archive-20261125/one-shot/_night_report_20261108.py` | one-shot | 名字即一次性（_前缀/日期/test）且无近期改动 |
| `cph4/fleet/idle-guard-kit/_build_s527_starfilter_grain_c2123.py` | `_archive-20261125/one-shot/_build_s527_starfilter_grain_c2123.py` | one-shot | 名字即一次性（_前缀/日期/test）且无近期改动 |
| `cph4/fleet/idle-guard-kit/_harvest_c2122_bank.py` | `_archive-20261125/one-shot/_harvest_c2122_bank.py` | one-shot | 名字即一次性（_前缀/日期/test）且无近期改动 |
| `cph4/fleet/mv-album-001-jay/_c2173_kn_timeline_probe.py` | `_archive-20261125/one-shot/_c2173_kn_timeline_probe.py` | one-shot | 名字即一次性（_前缀/日期/test）且无近期改动 |
| `docs/audits/entry_pacing_test.py` | `_archive-20261125/one-shot/entry_pacing_test.py` | one-shot | 名字即一次性（_前缀/日期/test）且无近期改动 |

## 回滚（任一条）

```bash
git mv _archive-20261125/<类别>/<文件名> <原路径>
```

整批回滚：`git reset --hard HEAD~1`（本批单独一次提交）。

## 第二批：主控自判为 obsolete 的一次性脚本（50 个）

判据：按卡号做完的"银行手术/结案"脚本、定点修复脚本、带日期的一次性报告。
保留未动：Tools/recon 拆包件、conflict_marker_scrub、docs/audits 量化证据脚本。

- `cph4/fleet/idle-guard-kit/c2089_bank_surgery.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2089_bank_surgery.py`
- `cph4/fleet/idle-guard-kit/c2114_bank_surgery.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2114_bank_surgery.py`
- `cph4/fleet/idle-guard-kit/c2114_f533c_qc.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2114_f533c_qc.py`
- `cph4/fleet/idle-guard-kit/c2114_packA_full_board.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2114_packA_full_board.py`
- `cph4/fleet/idle-guard-kit/c2119_closeout.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2119_closeout.py`
- `cph4/fleet/idle-guard-kit/c2120_board_append.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2120_board_append.py`
- `cph4/fleet/idle-guard-kit/c2120_closeout.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2120_closeout.py`
- `cph4/fleet/idle-guard-kit/c2120_ledger_fix.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2120_ledger_fix.py`
- `cph4/fleet/idle-guard-kit/c2120_ratify_append.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2120_ratify_append.py`
- `cph4/fleet/idle-guard-kit/c2120_tsfix.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2120_tsfix.py`
- `cph4/fleet/idle-guard-kit/c2123_closeout.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2123_closeout.py`
- `cph4/fleet/idle-guard-kit/c2123_ledger.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2123_ledger.py`
- `cph4/fleet/idle-guard-kit/c2125_closeout.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2125_closeout.py`
- `cph4/fleet/idle-guard-kit/c2136_bank_surgery.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2136_bank_surgery.py`
- `cph4/fleet/idle-guard-kit/c2136_closeout.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2136_closeout.py`
- `cph4/fleet/idle-guard-kit/c2137_closeout2.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2137_closeout2.py`
- `cph4/fleet/idle-guard-kit/c2139_renumber.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2139_renumber.py`
- `cph4/fleet/idle-guard-kit/c2140_bank_surgery.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2140_bank_surgery.py`
- `cph4/fleet/idle-guard-kit/c2140_bank_surgery2.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2140_bank_surgery2.py`
- `cph4/fleet/idle-guard-kit/c2140_bank_surgery3.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2140_bank_surgery3.py`
- `cph4/fleet/idle-guard-kit/c2140_conflict_resolve.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2140_conflict_resolve.py`
- `cph4/fleet/idle-guard-kit/c2142_bank_flip.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2142_bank_flip.py`
- `cph4/fleet/idle-guard-kit/c2142_bank_update.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2142_bank_update.py`
- `cph4/fleet/idle-guard-kit/c2142_closeout.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2142_closeout.py`
- `cph4/fleet/idle-guard-kit/c2142_verdict_addendum.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2142_verdict_addendum.py`
- `cph4/fleet/idle-guard-kit/c2143_bank_close.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2143_bank_close.py`
- `cph4/fleet/idle-guard-kit/c2143_bank_prestow.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2143_bank_prestow.py`
- `cph4/fleet/idle-guard-kit/c2159_bank_surgery.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__c2159_bank_surgery.py`
- `cph4/fleet/idle-guard-kit/s08_bfly_crop_c2120.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s08_bfly_crop_c2120.py`
- `cph4/fleet/idle-guard-kit/s08_locate_c2120.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s08_locate_c2120.py`
- `cph4/fleet/idle-guard-kit/s08_probe2_c2120.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s08_probe2_c2120.py`
- `cph4/fleet/idle-guard-kit/s08_probe_c2120.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s08_probe_c2120.py`
- `cph4/fleet/idle-guard-kit/s08_probe_strip_c2120.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s08_probe_strip_c2120.py`
- `cph4/fleet/idle-guard-kit/s527_4k_board_c2119.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s527_4k_board_c2119.py`
- `cph4/fleet/idle-guard-kit/s527_4k_grain010_c2120.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s527_4k_grain010_c2120.py`
- `cph4/fleet/idle-guard-kit/s527_4k_grain010_monitor_c2121.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s527_4k_grain010_monitor_c2121.py`
- `cph4/fleet/idle-guard-kit/s527_4k_probe_c2119.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s527_4k_probe_c2119.py`
- `cph4/fleet/idle-guard-kit/s527_artifact_locate_c2121.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s527_artifact_locate_c2121.py`
- `cph4/fleet/idle-guard-kit/s527_bank_close_c2120.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s527_bank_close_c2120.py`
- `cph4/fleet/idle-guard-kit/s527_bank_close_c2122.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s527_bank_close_c2122.py`
- `cph4/fleet/idle-guard-kit/s527_bank_close_c2123.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s527_bank_close_c2123.py`
- `cph4/fleet/idle-guard-kit/s527_bank_close_c2124.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s527_bank_close_c2124.py`
- `cph4/fleet/idle-guard-kit/s527_proxy_c2129.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s527_proxy_c2129.py`
- `cph4/fleet/idle-guard-kit/s527_readme_refresh_c2130.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s527_readme_refresh_c2130.py`
- `cph4/fleet/idle-guard-kit/s527_shipping_contact_c2123.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s527_shipping_contact_c2123.py`
- `cph4/fleet/idle-guard-kit/s527_verify_delivery_c2127.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s527_verify_delivery_c2127.py`
- `cph4/fleet/idle-guard-kit/s7r_bank_close_c2125.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__s7r_bank_close_c2125.py`
- `cph4/fleet/idle-guard-kit/v040_stage_dl_c2108.py` → `_archive-20261125/one-shot-cards/cph4__fleet__idle-guard-kit__v040_stage_dl_c2108.py`
- `cph4/fleet/meme-daily-v1/outbound/v1-zunjie-brake/fixwork/append_order_svfix.py` → `_archive-20261125/one-shot-cards/cph4__fleet__meme-daily-v1__outbound__v1-zunjie-brake__fixwork__append_order_svfix.py`
- `cph4/fleet/meme-daily-v1/outbound/v1-zunjie-brake/fixwork/qc_clip_s2fix.py` → `_archive-20261125/one-shot-cards/cph4__fleet__meme-daily-v1__outbound__v1-zunjie-brake__fixwork__qc_clip_s2fix.py`
