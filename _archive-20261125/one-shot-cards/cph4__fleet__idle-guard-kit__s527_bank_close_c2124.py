"""C2124 closeout: flip bank job s527-shipping-pack-v1 to done, prestow the next successor,
and write the delivery receipt for the six grain-0.10 4K plates.
"""
import json
import os
import time

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
XQ = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing"
RECEIPT = os.path.join(XQ, "xq-S527-SHIPPING-PACK-c2124.json")
DELIVERY = os.path.join(XQ, "delivery")

bank = json.load(open(BANK, encoding="utf-8-sig"))
now = time.strftime("%Y-%m-%dT%H:%M:%S")

manifest = json.load(open(os.path.join(DELIVERY, "MANIFEST-s527-4k.json"), encoding="utf-8-sig"))
entries = manifest["entries"]

for j in bank["jobs"]:
    if j["id"] == "s527-shipping-pack-v1":
        j["status"] = "done"
        j["done_ts"] = now
        j["done_note"] = (
            "SHIPPING-PACK-END ok=6 by tick-C2124. Six grain-0.10 4K plates copied byte-identical into "
            "media/MV/mv0001/xingqing/delivery/ (15.1-15.8MB each, 3840x2194), MANIFEST-s527-4k.json "
            "carries per-plate SHA256/size/dimensions plus the C2123 adjudication summary (0 defects, "
            "0 repair targets) and README-s527-4k.md is the one-page hand-off. Delivery copies were "
            "re-hashed from disk in the same run and all six match their source plate."
        )

if not any(j["id"] == "s527-conform-labels-v1" for j in bank["jobs"]):
    bank["jobs"].append({
        "id": "s527-conform-labels-v1",
        "status": "pending",
        "priority": 32,
        "auth": "r1017 sec-8 item-6 is the only open zero-GPU item left on that transfer list; C2120 pre-stowed it and never executed",
        "require": {"files_at_least": [["media/MV/mv0001/xingqing", "xq-AB-S7R-COMPARE-S5-26-r1058.jpg", 1]]},
        "cmd": ["D:\\ComfyUI\\python_embeded\\python.exe",
                "K:\\Fluxgroup\\FluxGroup\\cph4\\fleet\\idle-guard-kit\\s527_conform_labels_c2125.py"],
        "log_out": "media/mv-album-001-jay/log-s527-conformlabels.out.txt",
        "log_err": "media/mv-album-001-jay/log-s527-conformlabels.err.txt",
        "note": ("Version-management correction from r1017 sec-8 item-6: rebuild the S7R board family with "
                 "the s7rA/s7rB variant labels that match the receipts (the boards still say A/B/C) and fix "
                 "the ORGINAL typo on xq-AB-S7R-COMPARE-S5-26-r1058.jpg. PASS gate = "
                 "CONFORM-LABELS-END ok=1 with a regenerated board list in the log tail and zero 'ORGINAL' "
                 "occurrences in the new output names."),
        "prestow_ts": now,
        "prestow_note": "C2124 pre-stow while the delivery pack closed (bank law: never empty).",
    })

json.dump(bank, open(BANK, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

rec = {
    "batch": "c2124-s527-shipping-pack",
    "spec": "r1017 sec-8 item-1 delivery substrate: six grain-0.10 4K plates packaged with manifest",
    "delivery_dir": "media/MV/mv0001/xingqing/delivery",
    "plate_count": len(entries),
    "plates": [
        {"file": e["file"], "bytes": e["bytes"], "sha256": e["sha256"],
         "dimensions": e["dimensions"], "byte_identical": e["byte_identical"]}
        for e in entries
    ],
    "manifest": "delivery/MANIFEST-s527-4k.json",
    "readme": "delivery/README-s527-4k.md",
    "adjudication": manifest.get("adjudication"),
    "verify": "all six delivery copies re-hashed from disk in the same run and equal to source",
    "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    "by": "tick-C2124",
}
json.dump(rec, open(RECEIPT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("BANK+DONE " + now)
print("RECEIPT " + RECEIPT)