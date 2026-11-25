# -*- coding: ascii -*-
# s527_verify_delivery_c2127.py - integrity re-verification of the S527 delivery
# pack against its manifest (bank job s527-delivery-verify-v1).
#
# Re-hashes every delivery plate from disk, compares with MANIFEST-s527-4k.json
# (sha256 + bytes + dimensions) and with the source plates it was copied from,
# then writes a one-page verification receipt. Zero GPU, read-only on plates.
#
# PASS gate: VERIFY-END ok=6 mismatches=0 in the log tail.

import hashlib
import json
import os
import time

XQ = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing"
DELIVERY = os.path.join(XQ, "delivery")
MANIFEST = os.path.join(DELIVERY, "MANIFEST-s527-4k.json")
SOURCE_DIRS = [os.path.join(XQ, "s7r-4k")]
LOGDIR = r"K:\Fluxgroup\FluxGroup\media\logs"
LOG_OUT = os.path.join(LOGDIR, "s527_verifydelivery.out.txt")


def logline(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(LOG_OUT, "a", encoding="ascii", errors="replace") as f:
        f.write(line + "\n")
    try:
        print(line)
    except Exception:
        pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    from PIL import Image
    if os.path.exists(LOG_OUT):
        os.remove(LOG_OUT)
    logline("VERIFY-START manifest=%s" % MANIFEST)
    man = json.load(open(MANIFEST, encoding="utf-8-sig"))
    entries = man["entries"]
    logline("VERIFY entries=%d" % len(entries))

    rows = []
    ok = 0
    bad = 0
    for e in entries:
        name = e["file"]
        p = os.path.join(DELIVERY, name)
        row = {"file": name}
        if not os.path.exists(p):
            row["status"] = "MISSING"
            bad += 1
            rows.append(row)
            logline("MISSING %s" % name)
            continue
        h = sha256(p)
        size = os.path.getsize(p)
        dims = list(Image.open(p).size)
        src = None
        for d in SOURCE_DIRS:
            cand = os.path.join(d, name)
            if os.path.exists(cand):
                src = cand
                break
        row.update({
            "bytes": size, "dimensions": dims, "sha256": h,
            "manifest_sha_ok": h == e.get("sha256"),
            "manifest_bytes_ok": size == e.get("bytes"),
            "manifest_dims_ok": dims == list(e.get("dimensions") or dims),
            "source_sha_ok": (sha256(src) == h) if src else None,
            "source": src,
        })
        good = (row["manifest_sha_ok"] and row["manifest_bytes_ok"]
                and row["manifest_dims_ok"] and row["source_sha_ok"] is not False)
        row["status"] = "OK" if good else "MISMATCH"
        if good:
            ok += 1
        else:
            bad += 1
        rows.append(row)
        logline("CHECK %s %s %dB %s" % (name, row["status"], size, row["sha256"][:16]))

    rec = {
        "batch": "S527 delivery integrity re-verification",
        "runner": "bm-c C2127",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "manifest": "delivery/MANIFEST-s527-4k.json",
        "ok": ok, "mismatches": bad,
        "plates": rows,
        "note": "byte-level re-hash of every delivery plate against the manifest "
                "and against its source plate; zero pixel touched",
    }
    rp = os.path.join(DELIVERY, "VERIFY-S527-4K-c2127.json")
    json.dump(rec, open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    logline("RECEIPT %s" % rp)
    logline("VERIFY-END ok=%d mismatches=%d" % (ok, bad))
    if bad:
        raise SystemExit("verify failed mismatches=%d" % bad)


if __name__ == "__main__":
    main()