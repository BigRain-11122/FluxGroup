# -*- coding: ascii -*-
# c2133_bank_surgery.py - close packA-assembly-index-verify-v1, pre-stow successor.
# Byte-contract preserving: same BOM / EOL / indent as the file on disk.

import json
import os

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"


def detect(raw):
    bom = raw.startswith(b"\xef\xbb\xbf")
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8-sig" if bom else "utf-8")
    indent = None
    for line in text.splitlines()[1:]:
        s = line.lstrip(" ")
        if s.startswith('"') and len(s) != len(line):
            indent = len(line) - len(s)
            break
    return bom, crlf, indent, text


def main():
    raw = open(BANK, "rb").read()
    bom, crlf, indent, text = detect(raw)
    indent = indent or 1
    doc = json.loads(text)

    done_note = (
        "INDEX-VERIFY-END ok=1 mismatches=0 by tick-C2133 against origin/main 651a0bf. "
        "The 07:25:59 claim had no runner run: the C2132 verifier died at its first "
        "step (os.remove of its own guard-redirected log -> PermissionError WinError 32), "
        "so nothing was ever verified. C2133 replaced it with xq_packa_index_verify_c2133.py, "
        "which never touches its own log and adds two checks the v1 gate lacked: (a) the "
        "unit ORDER is compared to the authored pack manifest, (b) the rendered conform is "
        "present. Re-hashed all 33 clips from disk (sha256 + bytes), confirmed the same 33 "
        "unit set in v1 and v2, and confirmed the published v1 pair still resolves on origin. "
        "ORDER FINDING: the C2132 index was built by walking the clip folder, so it opened "
        "the film with the finale block (F5-33a/b/c/F5-34). v2 restores authored order."
    )

    for job in doc["jobs"]:
        if job.get("id") == "packA-assembly-index-verify-v1":
            job["status"] = "done"
            job["done_ts"] = "2026-10-20 07:38"
            job["done_note"] = done_note
            job["cmd"][1] = r"K:\\Fluxgroup\\FluxGroup\\cph4\\fleet\\mv-album-001-jay\\xq_packa_index_verify_c2133.py"

    successor = {
        "id": "packA-conform-cutpoints-v1",
        "status": "pending",
        "priority": 37,
        "auth": (
            "C2133 rendered the A-pack conform (196.14s, 33 units, windows from the authored "
            "pack manifest). The conform is only trustworthy if every cut lands where the index "
            "says: this job measures the actual cut points in the rendered mp4 and compares them "
            "to the cumulative window table."
        ),
        "require": {
            "files_at_least": [
                ["media/mv-album-001-jay/assembly-packA",
                 "XQ-PACKA-CONFORM-v1-c2133.mp4", 1]
            ]
        },
        "cmd": [
            r"D:\\\\ComfyUI\\\\python_embeded\\\\python.exe",
            r"K:\\\\Fluxgroup\\\\FluxGroup\\\\cph4\\\\fleet\\\\mv-album-001-jay\\\\xq_packa_cutpoints_c2133.py"
        ],
        "log_out": "media/mv-album-001-jay/log-packa-cutpoints.out.txt",
        "log_err": "media/mv-album-001-jay/log-packa-cutpoints.err.txt",
        "note": (
            "Detect scene cuts in the conform (ffmpeg select=gt(scene,0.30) + showinfo) and match "
            "each detected cut to the cumulative window edge from the v2 index. Report per-unit "
            "drift and the count of missing/unexpected cuts. PASS gate = CUTPOINTS-END "
            "matched>=30/33 max_drift<=0.12s. Zero GPU."
        ),
        "prestow_ts": "2026-10-20T07:38:00",
        "prestow_note": "C2133 pre-stow right after the conform landed (bank law: never empty).",
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
    print("BANK-OK jobs=%d done=%d pending=%d claimed=%d" % (
        len(back["jobs"]),
        sum(1 for v in st.values() if v == "done"),
        sum(1 for v in st.values() if v == "pending"),
        sum(1 for v in st.values() if v == "claimed")))
    print("verify=%s successor=%s" % (st.get("packA-assembly-index-verify-v1"),
                                       st.get("packA-conform-cutpoints-v1")))
    print("bytes=%d bom=%s crlf=%s indent=%d" % (len(data), bom, crlf, indent))


if __name__ == "__main__":
    main()