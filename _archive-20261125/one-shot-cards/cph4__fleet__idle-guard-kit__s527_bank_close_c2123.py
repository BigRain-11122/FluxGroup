"""C2123 harvest closeout: flip bank job s527-starfilter-grain to done, prestow successor,
and write the adjudication receipt for the shipping (grain 0.10) plates.
"""
import json
import os
import time

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
XQ = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing"
RECEIPT = os.path.join(XQ, "xq-S527-SHIPPING-ADJUDICATION-c2123.json")

bank = json.load(open(BANK, encoding="utf-8-sig"))
now = time.strftime("%Y-%m-%dT%H:%M:%S")

for j in bank["jobs"]:
    if j["id"] == "s527-starfilter-grain":
        j["status"] = "done"
        j["done_ts"] = now
        j["done_note"] = (
            "S527-STARFILTER-GRAIN-END ok=6 candidates=1605 stars=1571 anomalies=34 board=1129727B "
            "by tick-C2123. Delta vs zero-grain raw run (99 anomalies): grain 0.10 suppresses candidate "
            "flood 2535->1605 and anomalies 99->34. 33/34 sit on the frame edge (x>=3817 or y>=2173, "
            "plate 3840x2194) = stars clipped by the frame border, classifier marks edge hits as anomalies "
            "by design. The two interior hits (s20193 @1888,1740 and s20205 @2615,649) are blue-dominant "
            "diffuse nebula-clump regions (native r5->r20 means fall smoothly 67,106,153 -> 46,81,124), "
            "not dot-matrix / periodic / duplicated structure. Zero repair targets."
        )

if not any(j["id"] == "s527-shipping-pack-v1" for j in bank["jobs"]):
    bank["jobs"].append({
        "id": "s527-shipping-pack-v1",
        "status": "pending",
        "priority": 31,
        "auth": "r1017 sec-8 item-1 closed on shipping plates by C2123 adjudication; the six grain-0.10 4K plates are now the delivery substrate for the S5-27 line",
        "require": {"files_at_least": [["media/MV/mv0001/xingqing/s7r-4k", "_4k_grain010.png", 6]]},
        "cmd": ["D:\\ComfyUI\\python_embeded\\python.exe",
                "K:\\Fluxgroup\\FluxGroup\\cph4\\fleet\\idle-guard-kit\\s527_shipping_pack_c2124.py"],
        "log_out": "media/mv-album-001-jay/log-s527-shippingpack.out.txt",
        "log_err": "media/mv-album-001-jay/log-s527-shippingpack.err.txt",
        "note": ("Assemble delivery/manifest for the six shipping plates: copy (byte-identical) into "
                 "media/MV/mv0001/xingqing/delivery/, write SHA256 + size + dimensions per plate plus the "
                 "C2123 adjudication verdict into delivery/MANIFEST-s527-4k.json and a one-page README. "
                 "PASS gate = SHIPPING-PACK-END ok=6 and manifest parses with 6 entries whose SHA256 re-verify."),
        "prestow_ts": now,
        "prestow_note": "C2123 pre-stow right after the shipping-plate adjudication harvest (bank law: never empty)."
    })

json.dump(bank, open(BANK, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

rec = {
    "batch": "c2123-s527-shipping-adjudication",
    "spec": "r1017 sec-8 item-1 closure verified on the SHIPPING plates (grain 0.10), not just the zero-grain diagnostic substrate",
    "source_receipt": "xq-S527-STARFILTER-GRAIN-c2123.json",
    "plates": 6,
    "plate_dimensions": [3840, 2194],
    "candidates": 1605,
    "stars": 1571,
    "anomalies": 34,
    "anomalies_on_frame_edge": 33,
    "anomalies_interior": 2,
    "interior_findings": [
        {"plate": "S5-27_S5-27_s20193_s7rC_4k_grain010.png", "x": 1888, "y": 1740,
         "native_means_r5_to_r20": [[67.3, 105.8, 152.8], [46.0, 81.4, 124.7]],
         "verdict": "diffuse blue nebula clump; smooth radial gradient, no periodic or duplicated structure"},
        {"plate": "S5-28_S5-28_s20205_s7rC_4k_grain010.png", "x": 2615, "y": 649,
         "native_means_r5_to_r20": [[69.5, 92.0, 137.7], [58.9, 74.4, 106.7]],
         "verdict": "diffuse blue nebula clump with a point star; no periodic or duplicated structure"}
    ],
    "defects_found": 0,
    "repair_targets": [],
    "verdict": "PASS - sec-8 item-1 is a detector false-positive class on both substrates (zero-grain: 99/2535, grain-0.10: 34/1605). No dot-matrix, checkerboard, repeating lattice, fine-line hallucination or smear found on the shipping plates.",
    "products": {
        "contact_sheet": "xq-S527-SHIPPING-CONTACT-c2123.jpg",
        "anomaly_crops": "xq-S527-ANOM-CROPS-c2123.jpg",
        "native_check_png": "xq-S527-NATIVE-CHECK-c2123.png"
    },
    "limitations": "Frequency-domain peak test on the candidate windows was inconclusive (a compact star also yields an isolated spectral peak), so the periodic-structure judgement rests on the native-resolution crops plus the smooth radial pixel gradients above.",
    "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    "by": "tick-C2123"
}
json.dump(rec, open(RECEIPT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("BANK+DONE " + now)
print("RECEIPT " + RECEIPT)