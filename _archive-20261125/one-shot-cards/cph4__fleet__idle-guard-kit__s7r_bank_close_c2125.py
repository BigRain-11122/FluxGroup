"""C2125 closeout: flip bank job s527-conform-labels-v1 to done, prestow the next
successor (S7R family ratification index board), and write the conform receipt.
"""
import json
import os
import time

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
S7R = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing\abatch_s7r"

bank = json.load(open(BANK, encoding="utf-8-sig"))
now = time.strftime("%Y-%m-%dT%H:%M:%S")

for j in bank["jobs"]:
    if j["id"] == "s527-conform-labels-v1":
        j["status"] = "done"
        j["done_ts"] = now
        j["done_note"] = (
            "CONFORM-LABELS-END ok=1 by tick-C2125. The S7R board family was rebuilt from the "
            "variant files already on disk (no variant pixel rewritten, zero GPU): BOARD-1/BOARD-2 "
            "column headers now read s7rA grain 0.14 / s7rB shoulder+grain / s7rC esrgan4x+LANCZOS "
            "(was bare A/B/C), the S5-26 strip header spells ORIGINAL (was ORGINAL), and the S0-03 "
            "strip reads s7rA/s7rB. All four boards + the receipt were mirrored byte-identically into "
            "cph4/fleet/mv-album-001-jay/ and the S5-26 compare was placed at media/MV/mv0001/xingqing/ "
            "for the bank require gate. Mechanical check: zero 'ORGINAL' in every output name and label."
        )

if not any(j["id"] == "s7r-conform-ratify-board" for j in bank["jobs"]):
    bank["jobs"].append({
        "id": "s7r-conform-ratify-board",
        "status": "pending",
        "priority": 33,
        "auth": "r1017 sec-8 item-6 closed by C2125; the four conformed boards are separate files, so the "
                "director still has to open four images to ratify the family",
        "require": {"files_at_least": [["media/MV/mv0001/xingqing/abatch_s7r",
                                        "xq-S7R-CONFORM-LABELS-c2125.json", 1]]},
        "cmd": ["D:\\ComfyUI\\python_embeded\\python.exe",
                "K:\\Fluxgroup\\FluxGroup\\cph4\\fleet\\idle-guard-kit\\s7r_ratify_board_c2126.py"],
        "log_out": "media/mv-album-001-jay/log-s7r-ratifyboard.out.txt",
        "log_err": "media/mv-album-001-jay/log-s7r-ratifyboard.err.txt",
        "note": ("One-page ratification index: the four conformed S7R boards as labeled thumbnails plus the "
                 "label map (s7rA/s7rB/s7rC), the frame count per board, board sizes and sha256 short ids, so "
                 "bm-a director can ratify the family in a single look. Zero GPU, reads the boards on disk only. "
                 "PASS gate = RATIFY-BOARD-END ok=1 in log tail + board >= 150KB + 4 thumbnails drawn."),
        "prestow_ts": now,
        "prestow_note": "C2125 pre-stow right after the label conform landed (bank law: never empty).",
    })

json.dump(bank, open(BANK, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("BANK+DONE " + now)