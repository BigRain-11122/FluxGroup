# AUDIT-NOTE-C2109 · qwen21-vs-krea2 compare artifacts drift

- ts: 2026-10-20 02:36
- auditor: bm-c M5 C2109 (independent audit lane)
- finding: bank entry `qwen21-vs-krea2-cmp` stayed `claimed` after the C2108 harvest (products 02:02, blind verdict 02:06), so IdleGuard refired the same runner at 02:16:00.
- impact: duplicate ~7 min GPU reburn; during the duplicate run these were overwritten:
  - `qwen_sky.png` 02:16:39, 1,124,215 B (receipt: 1,124,215 B)
  - `krea_sky.png` 02:17:47, 987,435 B (receipt: 981,376 B -> drift)
  - `qwen_cassette.png` 02:20:21, 1,523,733 B (receipt: same bytes)
  - `log-cmp.out.txt` rewritten with the aborted duplicate run
- NOT touched: `QWEN21-vs-KREA2-board-c2099.jpg` (02:02:09, 196,415 B), `compare_receipt.json` (02:02:09), `compare_verdict.json` (02:06:46), cassette/dusk krea PNGs.
- verdict status: unchanged. The blind read was made on the board that is still on disk and matches the 02:02 receipt rows; only the source `krea_sky.png` bytes no longer match the receipt line.
- disposition: bank flipped to `done` (c2109_bank_flip.py, verified parse), duplicate runner PID 41168 stopped with exact command-line match, root cause (harvest did not flip bank) queued as evolution-day wiring candidate.