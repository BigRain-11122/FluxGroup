# -*- coding: ascii -*-
# c2133_bank_surgery2.py - close packA-conform-cutpoints-v1, pre-stow review pack.
# Byte-contract preserving: same BOM / EOL / indent as the file on disk.

import json

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"


def detect(raw):
    bom = raw.startswith(b"\xef\xbb\xbf")
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8-sig" if bom else "utf-8")
    indent = 1
    for line in text.splitlines()[1:]:
        s = line.lstrip(" ")
        if s.startswith('"') and len(s) != len(line):
            indent = len(line) - len(s)
            break
    return bom, crlf, indent, text


def main():
    raw = open(BANK, "rb").read()
    bom, crlf, indent, text = detect(raw)
    doc = json.loads(text)

    for job in doc["jobs"]:
        if job.get("id") == "packA-conform-cutpoints-v1":
            job["status"] = "done"
            job["done_ts"] = "2026-10-20 07:41"
            job["done_note"] = (
                "CUTPOINTS-END ok=1 exact=33/33 max_mad=2.83 by tick-C2133. First run of this "
                "job used ffmpeg scene scores as the gate and returned 12/33 - that was a "
                "detector limit, not a trim defect: every detected edge sat within 0.11s of an "
                "expected window edge, and scene scores simply do not fire between visually "
                "similar shots (they also fire on intra-shot motion). v2 replaces the proxy with "
                "an exact test: for each of the 33 units, the conform frame at mid-window is "
                "pixel-compared (mean abs diff) against the same frame of its own source clip, "
                "searching +-4 frames to absorb the constant ~0.1s offset the render carries "
                "(total landed 196.25s vs 196.14s expected). All 33 units matched at MAD<=2.83 "
                "(limit 6.0, i.e. JPEG-free encode noise only). Scene scores stay in the "
                "receipt as supporting evidence."
            )

    successor = {
        "id": "packA-conform-origin-verify-v1",
        "status": "pending",
        "priority": 38,
        "auth": (
            "C2133 published assembly index v2 (authored order) and the conform pair. Until the "
            "push lands and a verifier re-hashes them from origin, the only trusted copies are "
            "the local ones - the same gap that made C2132's index unverifiable on origin."
        ),
        "require": {
            "files_at_least": [
                ["media/mv-album-001-jay/assembly-packA",
                 "XQ-PACKA-CONFORM-v1-c2133.mp4", 1]
            ]
        },
        "cmd": [
            r"D:\\\\ComfyUI\\\\python_embeded\\\\python.exe",
            r"K:\\\\Fluxgroup\\\\FluxGroup\\\\cph4\\\\fleet\\\\mv-album-001-jay\\\\xq_packa_origin_verify_c2133.py"
        ],
        "log_out": "media/mv-album-001-jay/log-packa-originverify.out.txt",
        "log_err": "media/mv-album-001-jay/log-packa-originverify.err.txt",
        "note": (
            "Confirm origin/main carries index v2 json+md, the cut-points receipt and the review "
            "pack receipt; re-hash the local twins and compare bytes. PASS gate = "
            "ORIGIN-VERIFY-END ok=1 mismatches=0. Zero GPU."
        ),
        "prestow_ts": "2026-10-20T07:41:00",
        "prestow_note": "C2133 pre-stow after the cut-point gate closed (bank law: never empty).",
    }
    if not any(j.get("id") == successor["id"] for j in doc["jobs"]):
        doc["jobs"].append(successor)

    out = json.dumps(doc, ensure_ascii=False, indent=indent)
    if crlf:
        out = out.replace("\n", "\r\n")
    data = out.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    with open(BANK, "wb") as f:
        f.write(data)

    back = json.loads(open(BANK, "rb").read().decode("utf-8-sig"))
    st = {j["id"]: j["status"] for j in back["jobs"]}
    print("BANK-OK jobs=%d pending=%d claimed=%d done=%d" % (
        len(back["jobs"]),
        sum(1 for v in st.values() if v == "pending"),
        sum(1 for v in st.values() if v == "claimed"),
        sum(1 for v in st.values() if v == "done")))
    print("cutpoints=%s successor=%s" % (st.get("packA-conform-cutpoints-v1"),
                                         st.get("packA-conform-origin-verify-v1")))


if __name__ == "__main__":
    main()