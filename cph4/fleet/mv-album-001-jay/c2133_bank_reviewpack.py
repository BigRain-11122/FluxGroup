# -*- coding: ascii -*-
# c2133_bank_reviewpack.py - record the in-round review pack as a done bank job.

import json

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"


def main():
    raw = open(BANK, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    crlf = b"\r\n" in raw
    doc = json.loads(raw.decode("utf-8-sig"))
    if not any(j.get("id") == "packA-conform-review-pack-v1" for j in doc["jobs"]):
        doc["jobs"].append({
            "id": "packA-conform-review-pack-v1",
            "status": "done",
            "priority": 37,
            "auth": ("C2133 rendered the 44MB conform; the director needs a light proxy and "
                     "one page that shows the whole cut order."),
            "done_ts": "2026-10-20 07:42",
            "done_note": ("REVIEWPACK-END ok=1 by tick-C2133: 960px proxy 15,250,951B (vs the "
                          "44.6MB master) plus a 33-tile cut strip (204,273B) carrying the first "
                          "frame of every unit in cut order. Ran in the same round as the conform, "
                          "so no guard slot was consumed; receipt is "
                          "review/REVIEW-PACK-c2133.json."),
        })
    out = json.dumps(doc, ensure_ascii=False, indent=1)
    if crlf:
        out = out.replace("\n", "\r\n")
    data = out.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    with open(BANK, "wb") as f:
        f.write(data)
    back = json.loads(open(BANK, "rb").read().decode("utf-8-sig"))
    st = {j["id"]: j["status"] for j in back["jobs"]}
    print("jobs=%d pending=%d done=%d" % (
        len(back["jobs"]),
        sum(1 for v in st.values() if v == "pending"),
        sum(1 for v in st.values() if v == "done")))
    print("reviewpack=%s" % st.get("packA-conform-review-pack-v1"))


if __name__ == "__main__":
    main()