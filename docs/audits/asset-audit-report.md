# Asset Audit Report (auto-generated)

- scope: gaming\FluxVerse\City\Assets\UI\btn_main.png
- png files scanned: 1
- time: 2026-09-28 17:16:57
- rules: naming lowercase-ascii [a-z0-9-_]; icon<=128 free-size else power-of-two; UI assets need alpha; meta textureType=8 (Sprite) for UI; MD5 duplicates = atlas candidates

| verdict | check | file | detail |
|---------|-------|------|--------|
| PASS | format | btn_main.png | .png
| PASS | naming | btn_main.png | lowercase-ascii ok
| PASS | size-icon | btn_main.png | size 48x48 (icon class <=128)
| PASS | ui-alpha | btn_main.png | alpha channel present
| PASS | weight | btn_main.png | 1 KB
| PENDING | meta | btn_main.png | no .meta yet - open project in editor to import, then re-run audit

## Summary: pass=5 fail=0 warn=0 pending=1 info=0
## Verdict: PASS-WITH-PENDING - re-run after editor import refresh
