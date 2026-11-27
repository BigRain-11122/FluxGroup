# -*- coding: utf-8 -*-
"""C2168b KN04 prompt v3.0 (second 480P verify round).

Evidence round 2 (v2.9 take, native frames 4.2/5.5/6.9s): the golden ribbon swarm
is gone and the plane keeps crisp folds, but the rooftop water tower duplicates
into TWO towers by mid-shot (background invented as the camera travels laterally).
Fix = (a) name the tower as the one canonical silhouette, (b) replace the lateral
travel / walk-paced camera with a rise-and-settle follow so the camera invents no
new background. Positive-only wording (gate 3 zero-negation).
"""
import io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "可爱女人-shots-v2.py")
PACK = os.path.join(HERE, "可爱女人-i2v-PACK-A-v1.json")
VERIFY = os.path.join(HERE, "local-i2v", "run-bmc-kn-verify480-kn04.json")

OLD = ("i2v(\"A close-up at eye level\", CM[\"track\"], "
       "\"A single white paper plane with crisp folded edges and sharp creases lifting away in one "
       "clean arc off a rooftop into a wide clear dusk sky, the thrower's open hand still in its "
       "follow-through at the lower right, the water tower sliding past below, clean air and open "
       "dusk sky around that one plane\")")
NEW = ("i2v(\"A close-up at eye level\", "
       "\"the camera picks the plane up at its release and rises with it, easing into a settle as it climbs\", "
       "\"A single white paper plane with crisp folded edges lifting away in one clean arc off a "
       "rooftop into an open dusk sky, the thrower's open hand still in its follow-through at the "
       "lower right, the one black corrugated-tin water tower standing on its steel legs below, "
       "clean air and open dusk sky around that one plane\")")

CAM_OLD = "    (\"KN04\", 22.00, 30.14, 1.20,"
CAM_NEW_TAIL = None

VERSION_ANCHOR = "# v2.9=C2168"


def fail(msg):
    print("FATAL: " + msg)
    raise SystemExit(2)


raw = io.open(SHOTS, encoding="utf-8").read()
if raw.count(OLD) != 1:
    fail("OLD count=%d" % raw.count(OLD))
if raw.count("# v3.0=C2168b") != 0:
    fail("v3.0 already present")

out = raw.replace(OLD, NEW, 1)

VERSION_LINE = ("# v3.0=C2168b 480P 第二轮实测：v2.9 金色飘带群已清零、纸机折边锐利，但横移跟拍使背景水塔复制成两座\n"
                "→镜4 运镜改「起飞即托起·上升中缓落」+水塔点名唯一黑色波纹铁皮筒（正面单数）\n")
out = out.replace(VERSION_ANCHOR, VERSION_LINE + VERSION_ANCHOR, 1)
io.open(SHOTS, "w", encoding="utf-8", newline="").write(out)
print("SHOTS v3.0 written")

# re-run self-check module
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "mv0001-handover", "outbound", "krea2",
                                "prompt-writing-spec-v1", "patched-scripts"))
import importlib.util
spec = importlib.util.spec_from_file_location("knshots_v30", SHOTS)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
import prompt_lexicon as LX

unit = [s for s in mod.NEW if s[0] == "KN04"][0]
prompt = unit[6]
print("KN04 words=%d lint=%s" % (len(prompt.split()), LX.lint(prompt, mode="video")))

sys.path.insert(0, r"K:\Fluxgroup\hq-wt-c2310\Tools")
import preflight_gate as G

tokens = {"shot": "cu", "angle": "eye", "move": "track", "grade": "tw2001",
          "texture": "film_night", "scene": "rooftop", "light": "roof_dusk"}
fails = G.guard(shot_id="KN04", prompt_text=prompt, tokens=tokens, kf_verified=True,
                kf_note="C2166 KN-KF-PACK-A frame gate: KN04 signed (throw frame, water tower + open hand)")
print("KN04 guard=%s" % fails)

pack = json.load(io.open(PACK, encoding="utf-8"))
hits = [u for u in pack["units"] if u["id"] == "KN_A-KN04"]
if len(hits) != 1:
    fail("pack hits=%d" % len(hits))
pu = hits[0]
pu["i2v_prompt"] = prompt
pu["prompt_words"] = len(prompt.split())
pu["prompt_rev"] = "v3.0-C2168b-480P-round2"
pu["guard"] = fails
io.open(PACK, "w", encoding="utf-8").write(json.dumps(pack, ensure_ascii=False, indent=1))

man = json.load(io.open(VERIFY, encoding="utf-8"))
man["units"] = [pu]
man["wave"] = "kn-verify480-kn04-r2"
man["policy"] = ("C2168b KN04 单镜 480P 第二轮（672x384 int4·验证通道 clips-verify-480·永不进正片）。"
                 "v2.9 轮实测：飘带伪影清零/折边锐利，唯背景水塔复制成两座→v3.0 运镜改起飞托举+水塔正面单数点名。")
io.open(VERIFY, "w", encoding="utf-8").write(json.dumps(man, ensure_ascii=False, indent=1))
print("PACK + VERIFY updated; words=%d" % pu["prompt_words"])
print(prompt)
print("SURGERY2 OK")