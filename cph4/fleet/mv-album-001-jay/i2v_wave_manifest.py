# -*- coding: utf-8 -*-
# i2v_wave_manifest.py - 专辑 i2v 53 单云端波清单机读件（三车道政策令·云道备火件）
# CEO 令 10-11 19:3x：云道并行全量——本件=点火前备妥的全部弹药账（53 单零手抄·py 直抽）
# 波序：波A=KN16/KN21/XQ28 三长窗镜首单实证「8-15s 同价」政策 → 余 50 单按 ≤10 单/波连发
# 点火门：CEO 过目 LOOKBOARD 点头（图过目→才跑视频·质量闸不破）
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util
def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
XQ_M = _load("xq_shots", os.path.join(HERE, "星晴-shots-v2.py"))
KN_M = _load("kn_shots", os.path.join(HERE, "可爱女人-shots-v2.py"))

XQ_HOLD = {"XQ01", "XQ03", "XQ04", "XQ06", "XQ09", "XQ11", "XQ12", "XQ16", "XQ22", "XQ27", "XQ29"}
ALIAS = {"XQ17a": "XQ17", "XQ17b": "XQ17", "XQ17c": "XQ17", "XQ17d": "XQ17"}
POLICY_FIRST = ["KN16", "KN21", "XQ28"]  # 长窗镜（源 >5s·8-15s 档）=同价政策首单实证组

frames = os.path.normpath(os.path.join(HERE, "..", "..", "..", "media", "mv-album-001-jay", "frames"))

def build():
    seen, units = set(), []
    for trk, mod in (("XQ", XQ_M), ("KN", KN_M)):
        for s in mod.NEW:
            sid = ALIAS.get(s[0], s[0])
            key = "%s_%s" % (trk, sid)
            if key in seen:
                continue
            seen.add(key)
            if trk == "XQ" and sid in XQ_HOLD:
                continue  # 押后 12 之 XQ 11（脸级）不在波内
            if trk == "KN" and sid == "KN24":
                continue  # 押后 12 之 KN24（女主定版依赖）
            w = s[2] - s[1]
            src = 5.0 if "定格延窗" in s[4] else w / s[3]
            units.append({"id": key, "track": trk, "win_s": round(w, 2), "speed": s[3],
                          "src_s": round(src, 2), "policy_band": "8-15s" if src > 5.05 else "5s",
                          "frame": os.path.join(frames, "%s_%s.png" % (trk, sid)),
                          "i2v_prompt": s[6], "note": s[4]})
    # 波序：政策首单组置顶（组内按 id），余按字典序
    first = [u for u in units if u["id"].split("_")[1] in POLICY_FIRST and u["id"] in
             [p.replace("|", "_") for p in []] or u["id"] in ["KN_KN16", "KN_KN21", "XQ_XQ28"]]
    rest = sorted([u for u in units if u not in first], key=lambda u: u["id"])
    return first + rest

if __name__ == "__main__":
    units = build()
    waves = [units[i:i + 10] for i in range(0, len(units), 10)]
    out = {"policy": "CEO 10-11 19:3x 三车道令·云道并行全量", "gate": "CEO 过目 LOOKBOARD 点头即点火",
           "engine": "minimax_h3 first_frame 768P（generate_video·云端 100/日共享）",
           "audio": "纯画面出片（音轨禁令·装配端 -an 剥离兜底）",
           "policy_test_wave": ["KN_KN16", "KN_KN21", "XQ_XQ28"],
           "total": len(units), "waves": [[u["id"] for u in w] for w in waves], "units": units}
    path = os.path.join(HERE, "i2v-wave-manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    bands = {}
    for u in units:
        bands[u["policy_band"]] = bands.get(u["policy_band"], 0) + 1
    missing = [u["id"] for u in units if not (os.path.isfile(u["frame"]) and os.path.getsize(u["frame"]) > 100000)]
    print("units=%d bands=%s waves=%d missing_frames=%s" % (len(units), bands, len(waves), missing or "0"))
    print("wave1(policy-first):", out["waves"][0])
    print("written:", path)
