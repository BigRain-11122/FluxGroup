# -*- coding: ascii -*-
"""C2135: surgical byte fix of the doubled-backslash cmd paths in the bank file.

The bank file is CRLF + ensure_ascii=False + indent=1, which json.dumps cannot
reproduce (it always writes LF). Re-serialising the whole file would rewrite every
line, so patch the two literal cmd strings in place instead, then re-parse.
"""
import json
import os

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
JOB = "packA-conform-origin-verify-v1"

OLD_PY = b"D:" + b"\\\\" * 4 + b"ComfyUI" + b"\\\\" * 4 + b"python_embeded" + b"\\\\" * 4 + b"python.exe"
NEW_PY = b"D:\\\\" + b"ComfyUI\\\\" + b"python_embeded\\\\" + b"python.exe"

OLD_SCRIPT = (b"K:" + b"\\\\" * 4 + b"Fluxgroup" + b"\\\\" * 4 + b"FluxGroup" + b"\\\\" * 4 +
              b"cph4" + b"\\\\" * 4 + b"fleet" + b"\\\\" * 4 + b"mv-album-001-jay" + b"\\\\" * 4 +
              b"xq_packa_origin_verify_c2133.py")
NEW_SCRIPT = (b"K:\\\\" + b"Fluxgroup\\\\" + b"FluxGroup\\\\" + b"cph4\\\\" + b"fleet\\\\" +
              b"mv-album-001-jay\\\\" + b"xq_packa_origin_verify_c2133.py")

raw = open(BANK, "rb").read()
print("OLD_PY count=%d" % raw.count(OLD_PY))
print("OLD_SCRIPT count=%d" % raw.count(OLD_SCRIPT))
assert raw.count(OLD_PY) == 1, "anchor count mismatch (py cmd)"
assert raw.count(OLD_SCRIPT) == 1, "anchor count mismatch (script cmd)"

new = raw.replace(OLD_PY, NEW_PY).replace(OLD_SCRIPT, NEW_SCRIPT)
tmp = BANK + ".tmp"
with open(tmp, "wb") as f:
    f.write(new)
os.replace(tmp, BANK)

chk = json.loads(open(BANK, encoding="utf-8-sig").read())
jobs = [j for j in chk["jobs"] if j.get("id") == JOB]
assert len(jobs) == 1
cmd = jobs[0]["cmd"]
print("PARSED_CMD=%r" % (cmd,))
assert cmd[0] == r"D:\ComfyUI\python_embeded\python.exe"
assert cmd[1] == r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay\xq_packa_origin_verify_c2133.py"
for part in cmd:
    assert os.path.exists(part), part
print("BANK-CMD-FIX ok=1 job=%s parts=%d bytes %d->%d" % (JOB, len(cmd), len(raw), len(new)))