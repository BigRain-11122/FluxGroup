# -*- coding: utf-8 -*-
"""C2168 KN04 prompt surgery (480P verify verdict FIX -> prompt v2.9).

Evidence: clips-verify-480/KN_A-KN04.mp4 native frames 3.9s..6.8s show a golden
ribbon/confetti swarm filling the dusk sky and the paper plane's folds deforming.
KN21 + KN22b passed (GO). Fix = positive-only rewrite of the action clause:
one plane, crisp folds, one clean arc (no implied flash/fast pop), explicit
clean open sky around the single plane. Zero negation (gate 3).
"""
import io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SHOTS = os.path.join(HERE, "可爱女人-shots-v2.py")
PACK = os.path.join(HERE, "可爱女人-i2v-PACK-A-v1.json")
VERIFY = os.path.join(HERE, "local-i2v", "run-bmc-kn-verify480-kn04.json")

OLD_CONTENT = ("\"A white paper plane flashing up off a rooftop into the dusk sky, the hand still open in "
               "its follow-through, the water tower sliding past below\"")
NEW_CONTENT = ("\"A single white paper plane with crisp folded edges and sharp creases lifting away in one "
               "clean arc off a rooftop into a wide clear dusk sky, the thrower's open hand still in its "
               "follow-through at the lower right, the water tower sliding past below, clean air and open "
               "dusk sky around that one plane\"")

VERSION_ANCHOR = "# v2.8=C2167"
VERSION_LINE = ("# v2.9=C2168 480P 验证片闸实测修复：KN04 掷出镜（原生帧 3.9-6.8s 金色飘带群伪影+机翼折叠变形）"
                "→动作句正面重写（单只纸机·折边锐利·一条干净弧线·干净开阔黄昏天空·删“flashing up”快闪暗示）；"
                "KN21/KN22b 实测 GO 零改动\n")


def fail(msg):
    print("FATAL: " + msg)
    raise SystemExit(2)


# ---- 1. shots py surgery ----
raw = io.open(SHOTS, encoding="utf-8").read()
n_old = raw.count(OLD_CONTENT)
if n_old != 1:
    fail("OLD_CONTENT count=%d (expect 1)" % n_old)
if raw.count(VERSION_LINE) != 0:
    fail("v2.9 line already present")
if raw.count(VERSION_ANCHOR) != 1:
    fail("VERSION_ANCHOR count=%d" % raw.count(VERSION_ANCHOR))
out = raw.replace(OLD_CONTENT, NEW_CONTENT, 1)
out = out.replace(VERSION_ANCHOR, VERSION_LINE + VERSION_ANCHOR, 1)
io.open(SHOTS, "w", encoding="utf-8", newline="").write(out)
print("SHOTS REWRITTEN v2.9 (KN04 action clause)")

# ---- 2. re-run the py self-check (lint t2i+video, durations, windows) ----
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "mv0001-handover", "outbound", "krea2",
                                "prompt-writing-spec-v1", "patched-scripts"))
import importlib.util
spec = importlib.util.spec_from_file_location("knshots_v29", SHOTS)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
import prompt_lexicon as LX

unit = [s for s in mod.NEW if s[0] == "KN04"][0]
prompt = unit[6]
print("KN04 words=%d" % len(prompt.split()))
print("KN04 lint=%s" % LX.lint(prompt, mode="video"))

# ---- 3. preflight gate guard ----
gate_dir = r"K:\Fluxgroup\hq-wt-c2310\Tools"
sys.path.insert(0, gate_dir)
import preflight_gate as G

tokens = {"shot": "cu", "angle": "eye", "move": "track", "grade": "tw2001",
          "texture": "film_night", "scene": "rooftop", "light": "roof_dusk"}
fails = G.guard(shot_id="KN04", prompt_text=prompt, tokens=tokens, kf_verified=True,
                kf_note="C2166 KN-KF-PACK-A frame gate: KN04 signed (throw frame, water tower + open hand)")
print("KN04 guard=%s" % fails)

# ---- 4. patch the 30-unit pack entry ----
pack = json.load(io.open(PACK, encoding="utf-8"))
hits = [u for u in pack["units"] if u["id"] == "KN_A-KN04"]
if len(hits) != 1:
    fail("pack KN_A-KN04 count=%d" % len(hits))
pu = hits[0]
pu["i2v_prompt"] = prompt
pu["prompt_words"] = len(prompt.split())
pu["prompt_rev"] = "v2.9-C2168-480P-verify-FIX"
pu["guard"] = fails
io.open(PACK, "w", encoding="utf-8").write(json.dumps(pack, ensure_ascii=False, indent=1))
print("PACK patched: KN_A-KN04 prompt_words=%d" % pu["prompt_words"])

# ---- 5. KN04-only verify manifest ----
kn04 = dict(hits[0])
man = {
    "policy": "C2168 KN04 单镜 480P 复验（672x384 int4·验证通道 clips-verify-480·永不进正片）。"
              "上卷 C2167 三单实测：KN21 GO / KN22b GO / KN04 FIX（金色飘带群伪影+机翼折叠变形）→词面 v2.9 手术后同镜复烧确认。",
    "gate": "同一机械闸：lint(video) 零命中 + preflight_gate.guard(kf_verified=True) 空列表 + 出口 clips-verify-480。",
    "wave": "kn-verify480-kn04",
    "total": 1,
    "total_win_s": kn04["win_s"],
    "units": [kn04],
}
io.open(VERIFY, "w", encoding="utf-8").write(json.dumps(man, ensure_ascii=False, indent=1))
print("VERIFY manifest written: %s" % VERIFY)
print("SURGERY OK")