# -*- coding: ascii -*-
"""C2135 bank surgery: harvest the origin-verify job and pre-stow its successor.

Why: IdleGuard fired packA-conform-origin-verify-v1 at 07:55:59 and the runner wrote
ORIGIN-VERIFY-END ok=1 mismatches=0, but the guard never flipped the job, so the bank
still shows it claimed. Harvest it from the runner log, then pre-stow the v2 verifier
(the bank law is "never empty").

The bank file is CRLF + ensure_ascii=False + indent=1, so blocks are rebuilt with that
exact style instead of re-serialising the whole file.
"""
import json
import os

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
JOB = "packA-conform-origin-verify-v1"
NEXT = "packA-conform-v2-origin-verify-v1"
LOG = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay\log-packa-originverify.run.txt"

raw = open(BANK, "rb").read()
text = raw.decode("utf-8-sig")
data = json.loads(text)
jobs = data["jobs"]

# 1) harvest: read the runner's final line
tail = open(LOG, encoding="ascii", errors="replace").read()
end_lines = [l for l in tail.splitlines() if "ORIGIN-VERIFY-END" in l]
assert end_lines, "runner log has no ORIGIN-VERIFY-END"
assert "ok=1" in end_lines[-1] and "mismatches=0" in end_lines[-1], end_lines[-1]
print("HARVEST-READ", end_lines[-1][-90:])

tgt = [j for j in jobs if j["id"] == JOB]
assert len(tgt) == 1
job = tgt[0]
job["status"] = "done"
job["done_ts"] = "2026-10-20 07:56"
job["done_note"] = ("ORIGIN-VERIFY-END ok=1 mismatches=0 by IdleGuard fire 07:55:59 "
                    "(origin/main=7c63121): index v2 json+md, cut-points receipt and conform "
                    "receipt all MATCH byte-for-byte. Harvested by tick-C2135 from the runner "
                    "log; the guard never flipped the job.")

# 2) pre-stow successor
jobs.append({
    "id": NEXT,
    "status": "pending",
    "priority": 39,
    "auth": ("C2135 shipped the loudness-normalised conform v2 (I=-14.2 LUFS, TP=-2.3 dBTP, "
             "4710/4710 video frames identical to v1). Its receipt is local until the push "
             "lands and a verifier re-hashes it from origin."),
    "require": {"files_at_least": [
        ["media/mv-album-001-jay/assembly-packA",
         "XQ-PACKA-CONFORM-v2-loudnorm-c2135.mp4", 1]]},
    "cmd": [
        r"D:\ComfyUI\python_embeded\python.exe",
        r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay\xq_packa_v2_origin_verify_c2135.py",
    ],
    "log_out": "media/mv-album-001-jay/log-packa-originverify-v2.out.txt",
    "log_err": "media/mv-album-001-jay/log-packa-originverify-v2.err.txt",
    "note": ("Re-read all five receipts from origin/main and re-measure the v2 film "
             "(4710 frames, -14 LUFS +-0.6, TP <= -1.3). PASS gate = ORIGIN-VERIFY-V2-END "
             "ok=1 mismatches=0. Zero GPU."),
    "prestow_ts": "2026-10-20T08:04:00",
    "prestow_note": "C2135 pre-stow after the loudness gate closed (bank law: never empty).",
})

for c in jobs[-1]["cmd"]:
    assert os.path.exists(c), c


def block(obj):
    body = json.dumps(obj, ensure_ascii=False, indent=1)
    return "\r\n".join("  " + line for line in body.split("\n"))


# 3) surgical rewrite of the target block + append the successor
old_block = block({"id": JOB, "_": None})  # not used; locate by scan below
start_marker = '  {\r\n   "id": "%s"' % JOB
start = text.index(start_marker)
end = text.index("\r\n  }", start) + len("\r\n  }")
old_text = text[start:end]
assert old_text.count(JOB) == 1
new_text = block(job)
text = text[:start] + new_text + text[end:]

tail_marker = "\r\n ]\r\n}"
assert text.count(tail_marker) == 1
text = text.replace(tail_marker, ",\r\n" + block(jobs[-1]) + tail_marker)

out = b"\xef\xbb\xbf" + text.encode("utf-8") if raw.startswith(b"\xef\xbb\xbf") else text.encode("utf-8")
tmp = BANK + ".tmp"
with open(tmp, "wb") as f:
    f.write(out)
os.replace(tmp, BANK)

chk = json.loads(open(BANK, encoding="utf-8-sig").read())
assert len(chk["jobs"]) == len(jobs), (len(chk["jobs"]), len(jobs))
assert chk["jobs"][-1]["id"] == NEXT
assert [j for j in chk["jobs"] if j["id"] == JOB][0]["status"] == "done"
print("BANK-OK jobs=%d pending=%d bytes %d->%d" %
      (len(chk["jobs"]), sum(1 for j in chk["jobs"] if j.get("status") == "pending"),
       len(raw), len(out)))