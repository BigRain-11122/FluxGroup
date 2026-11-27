# -*- coding: utf-8 -*-
"""C2168b step 2: sync the v3.0 KN04 prompt into the 30-unit pack + the KN04-only verify manifest."""
import importlib.util, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "可爱女人-shots-v2.py")
PACK = os.path.join(HERE, "可爱女人-i2v-PACK-A-v1.json")
VERIFY = os.path.join(HERE, "local-i2v", "run-bmc-kn-verify480-kn04.json")

sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "mv0001-handover", "outbound", "krea2",
                                "prompt-writing-spec-v1", "patched-scripts"))
spec = importlib.util.spec_from_file_location("knshots", SHOTS)
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
if LX.lint(prompt, mode="video") or fails:
    raise SystemExit("GATE NOT GREEN")

pack = json.load(io.open(PACK, encoding="utf-8"))
hits = [u for u in pack["units"] if u["id"] == "KN_A-KN04"]
assert len(hits) == 1, "pack hits=%d" % len(hits)
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
print("PACK+VERIFY updated words=%d" % pu["prompt_words"])
print(prompt)