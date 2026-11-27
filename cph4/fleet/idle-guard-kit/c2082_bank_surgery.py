# Bank surgery (tick-C2082): harvest latentsync-weights-dl2 (OK 4/4) + re-arm latentsync-trial
# Bank write law (C2074 precedent): json.loads re-verify after write; contract-aware (BOM/EOL/indent).
import json
import os
import datetime

FG = r"K:\Fluxgroup\FluxGroup"
BANK = os.path.join(FG, "cph4", "fleet", "work-bank", "bm-c-gpu-bank.json")

raw = open(BANK, "rb").read()
has_bom = raw[0:3] == b"\xef\xbb\xbf"
text = raw.decode("utf-8-sig")
eol = "\r\n" if "\r\n" in text else "\n"
# indent detection from second non-empty line
lines = text.splitlines()
indent = 1
for ln in lines[1:]:
    if ln.strip():
        indent = len(ln) - len(ln.lstrip(" "))
        break

bank = json.loads(text)
jobs = {j["id"]: j for j in bank["jobs"]}
assert "latentsync-weights-dl2" in jobs and "latentsync-trial" in jobs, "job ids missing"

now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# 1. harvest weights-dl2: claimed -> done
j = jobs["latentsync-weights-dl2"]
assert j["status"] == "claimed", "dl2 status=%s not claimed" % j["status"]
j["status"] = "done"
j["done_ts"] = now
j["done_note"] = ("OK 4/4 by tick-C2082 harvest: unet v1.5 5072348184B + whisper tiny 75572083B + "
                  "2DFAN4 96316515B + sfd 89843225B all on disk; verdict weights2_verdict.json ts 16:14:39 "
                  "status OK fail=[]; WEIGHTS2-END sentinel OK in log-wdl2.out; trial leg unblocked")

# 2. re-arm trial: claimed -> pending (soundfile + decord-shim fix applied and IO-verified)
j = jobs["latentsync-trial"]
assert j["status"] == "claimed", "trial status=%s not claimed" % j["status"]
j["status"] = "pending"
j["rearm_ts"] = now
j["rearm_note"] = ("C2082: first fire 16:16:09 FAIL ModuleNotFoundError soundfile (import chain fail-fast, zero GPU burn). "
                   "Fix v2 (fix tag c2082-soundfile-decordshim): soundfile 0.14.0 pip --no-deps into PYLIBS overlay; "
                   "decord no-cp313-wheel -> real ffmpeg-subprocess shim package in overlay (AudioReader/VideoReader, musepose av precedent). "
                   "Verified fresh-process: 6-module import chain GREEN + AudioReader real decode 51200 samples/3.2s finite + "
                   "VideoReader 250f + write_video libx264 12f + face_detector J-30 shim live (bak in place) + unet 5072348184B. "
                   "Guard refire expected <=10min; remaining unknowns = unet v1.5 state-dict reconcile + inference (trial's own gate).")

out = json.dumps(bank, ensure_ascii=True, indent=indent)
if eol == "\r\n":
    out = out.replace("\n", "\r\n")
if has_bom:
    out = "\ufeff" + out
with open(BANK, "w", encoding="utf-8-sig" if has_bom else "utf-8", newline="") as f:
    f.write(out)

# re-verify
rt = json.loads(open(BANK, "rb").read().decode("utf-8-sig"))
jobs2 = {x["id"]: x for x in rt["jobs"]}
assert jobs2["latentsync-weights-dl2"]["status"] == "done", "dl2 flip failed"
assert jobs2["latentsync-trial"]["status"] == "pending", "trial rearm failed"
assert "soundfile" in jobs2["latentsync-trial"]["rearm_note"]
n_done = sum(1 for x in rt["jobs"] if x["status"] == "done")
n_pending = sum(1 for x in rt["jobs"] if x["status"] == "pending")
print("BANK-SURGERY OK dl2=done trial=pending(refire armed) done=%d pending=%d indent=%d bom=%s eol=%r"
      % (n_done, n_pending, indent, has_bom, eol))
