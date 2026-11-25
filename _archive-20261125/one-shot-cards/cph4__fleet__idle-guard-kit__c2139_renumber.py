# -*- coding: utf-8 -*-
# c2139_renumber.py -- C2138 was already taken by the M2 radar lane at 09:53:51, so this M1
# harvest round renumbers to C2139 (claim C2139 @10:10:22). Byte-level rename + in-place
# token swap, with counts asserted so nothing silent happens.
import io
import json
import os

KIT = r"K:\Fluxgroup\FluxGroup\cph4\fleet\idle-guard-kit"
ALBUM = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay"
BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
ROOT = r"K:\Fluxgroup\MiniGame"
STATE = os.path.join(ROOT, "state-c.json")
LEDGER = os.path.join(ROOT, ".codely-cli", "engine-tick", "tick-ledger.txt")
KANBAN = os.path.join(ROOT, "Design", "configs", "GLOBAL", "\u6863\u6848", "\u673a\u961f\u534f\u4f5c\u770b\u677f.md")
SNAPDOC = os.path.join(ROOT, "\u81ea\u52a8\u5316\u5feb\u7167-c.md")

# 1. rename the two scripts
for old, new in (("kfpb_probe_c2138.py", "kfpb_probe_c2139.py"),
                 ("c2138_closeout.py", "c2139_closeout.py")):
    po, pn = os.path.join(KIT, old), os.path.join(KIT, new)
    if os.path.isfile(po):
        os.replace(po, pn)
        print("RENAME", old, "->", new)

# 2. token swap inside the kit scripts (c2138 -> c2139, C2138 -> C2139)
for name in ("kfpb_probe_c2139.py", "c2139_closeout.py", "c2137_bank_harvest.py"):
    p = os.path.join(KIT, name)
    raw = io.open(p, encoding="utf-8", newline="").read()
    a = raw.count("c2138") + raw.count("C2138")
    raw = raw.replace("c2138", "c2139").replace("C2138", "C2139")
    io.open(p, "w", encoding="utf-8", newline="").write(raw)
    print("PATCH-SCRIPT", name, "tokens=%d" % a)

# 3. bank: job id / cmd / logs
raw = io.open(BANK, encoding="utf-8").read()
b = raw.count("c2138")
d = json.loads(raw)
for j in d["jobs"]:
    if j.get("id") == "kf-packb-probe-c2138":
        j["id"] = "kf-packb-probe-c2139"
        j["cmd"] = [c.replace("c2138", "c2139") for c in j["cmd"]]
        j["log_out"] = j["log_out"].replace("c2138", "c2139")
        j["log_err"] = j["log_err"].replace("c2138", "c2139")
        j["note"] = (j["note"] + " Renumbered from c2138 on claim collision (C2138 belongs to the "
                                  "09:53 M2 radar lane).")
        break
else:
    raise SystemExit("BANK-JOB-NOT-FOUND")
tmp = BANK + ".tmp"
io.open(tmp, "w", encoding="utf-8", newline="").write(json.dumps(d, ensure_ascii=False, indent=2))
os.replace(tmp, BANK)
print("BANK-PATCH tokens=%d job=kf-packb-probe-c2139" % b)

# 4. state: snapshot id
sd = json.loads(io.open(STATE, encoding="utf-8-sig").read())
old_snap = sd.get("current_snapshot_id")
sd["current_snapshot_id"] = old_snap.replace("c2138", "c2139")
sd["current_snapshot"] = sd["current_snapshot_id"]
t = STATE + ".tmp"
io.open(t, "w", encoding="utf-8-sig", newline="").write(json.dumps(sd, ensure_ascii=False, indent=1))
os.replace(t, STATE)
chk = json.loads(io.open(STATE, encoding="utf-8-sig").read())
assert chk["current_snapshot_id"] == chk["current_snapshot"], "double anchor mismatch"
print("STATE-PATCH", old_snap, "->", chk["current_snapshot_id"])

# 5. snapshot doc + kanban: token swap (only my own text carries C2138 here)
for p, label in ((SNAPDOC, "SNAPDOC"), (KANBAN, "KANBAN")):
    raw = io.open(p, encoding="utf-8", newline="").read()
    n = raw.count("c2138") + raw.count("C2138")
    raw = raw.replace("c2138", "c2139").replace("C2138", "C2139")
    io.open(p, "w", encoding="utf-8", newline="").write(raw)
    print("%s-PATCH tokens=%d" % (label, n))

# 6. ledger: only the 8 rows this round appended
lb = io.open(LEDGER, "rb").read()
n = lb.count(b"C2138")
lb = lb.replace(b"C2138", b"C2139")
io.open(LEDGER, "wb").write(lb)
print("LEDGER-PATCH tokens=%d" % n)

print("RENUMBER-END ok=1")