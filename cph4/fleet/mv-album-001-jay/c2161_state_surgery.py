"""C2161 closeout surgery: state-c.json three fields only (indent=1, BOM probed)."""
import json
import os
import sys
import time

P = r"K:\Fluxgroup\MiniGame\state-c.json"
raw = open(P, "rb").read()
bom = raw.startswith(b"\xef\xbb\xbf")
enc = "utf-8-sig" if bom else "utf-8"
with open(P, encoding=enc, newline="") as f:
    s = json.load(f)

now = time.strftime("%Y-%m-%d %H:%M")
s["last_round"] = {
    "ts": now,
    "result": "C2161 R6-1/R6-3 landed at assembly layer (window-level, CPU only): "
              "monarch desaturated+warm-tinted+gblur (sat proxy ratio 0.218), "
              "montage second pass punched 1.34x with calibrated +3 code lift "
              "(dup frames 81->0, YAVG 40.14). No v6 film: R4 re-render still burning.",
    "build_ok": True,
}
s["current_snapshot_id"] = "tick-20261024-0125@C2161"
s["next_round_at"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() + 600))

out = json.dumps(s, ensure_ascii=False, indent=1)
data = (b"\xef\xbb\xbf" if bom else b"") + out.encode("utf-8")
tmp = P + ".tmp"
with open(tmp, "wb") as f:
    f.write(data)
os.replace(tmp, P)
# write-then-reparse gate
with open(P, encoding=enc) as f:
    chk = json.load(f)
assert chk["current_snapshot_id"] == s["current_snapshot_id"]
print("STATE_OK snapshot=%s bom=%s bytes=%d" % (chk["current_snapshot_id"], bom, len(data)))