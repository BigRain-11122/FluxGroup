#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drama_rules.py - 漫剧/短剧的规则引擎与状态机（纯逻辑，零模型、零机器）。

Why（2026-11-11）：先把"什么算过了"写成可执行的判据，再谈生产。判据取自
cph4/fleet/drama-dept-v1/AI-DRAMA-WORKFLOW-MINDMAP-20261111.html（七支·带数字），
本文件只做三件事：校验一集的数据是否满足硬规则、按状态机推进、给出失败码。

设计原则：
  1. 确定性优先：能算的绝不用模型判。
  2. 失败要指名：每个 BLOCKED 必须带失败码 + 一句人话。
  3. 不许跳步：状态机只允许相邻推进，跳步一律拒。
  4. 反例优先：自检里 10 个反例必须全部被拦，漏一个就是规则不够。

用法：
    python3 Tools/fleet/drama_rules.py --self-test
    python3 Tools/fleet/drama_rules.py --check cph4/fleet/drama/samples/good.json
"""
import argparse
import json
import os
import sys

# ---- 规则常量（唯一源；改这里，别在别处再写一遍）----------------------------
FORMS = ("2d-i2v", "3d-asset", "sim-human")
DUR_RANGE = {"manju": (60, 90), "duanju": (90, 120)}   # 秒
SHOT_DUR_MAX = 5.0
SHOT_DUR_HARD_WARN = 3.0
KF_SIZE = (1080, 1920)
I2V_MAX_TAKES = 3
I2V_HIT_RATE_MIN = 0.50
IDENTITY_STRENGTH = (0.70, 0.85)
LOUDNESS = (-16.0, -12.0)          # -14 ±2
SAMPLE_RATE = 48000
SUBTITLE_MAX_CHARS = 17
FIRST3S_DIFF_MIN = 0.02
BLIND_SCORE_MIN = 9.0
VERSIONS_MAX = 3
FPS_MIN = 30
BANNED_TRANSITIONS = ("white_flash", "shake", "zoom_punch", "sticker_text")
FAKE_MOTIONS = ("push_in", "pull_out", "pan", "ken_burns")

STAGES = ("script", "assets", "storyboard", "kf", "i2v", "audio", "assembly", "qc", "publish")
GATE_OF_STAGE = {
    "script": "R-SCRIPT", "assets": "R-ASSET", "storyboard": "R-SHOT",
    "kf": "R-KF", "i2v": "R-I2V", "audio": "R-AUDIO",
    "assembly": "R-ASSEMBLY", "qc": "R-QC", "publish": "R-PUBLISH",
}


def _fail(code, msg, warn=False):
    return {"code": code, "msg": msg, "warn": bool(warn)}


def check_script(ep):
    f = []
    arc = (ep.get("episode") or {}).get("arc") or {}
    dur = (ep.get("episode") or {}).get("duration_s")
    kind = (ep.get("series") or {}).get("kind", "manju")
    lo, hi = DUR_RANGE.get(kind, DUR_RANGE["manju"])
    if not (dur and lo <= dur <= hi):
        f.append(_fail("F-DUR", "单集时长 %s 秒，应在 %d-%d" % (dur, lo, hi)))
    if not arc.get("hook_3s"):
        f.append(_fail("F-HOOK-3S", "前 3 秒没有钩子"))
    if int(arc.get("conflicts") or 0) < 3:
        f.append(_fail("F-BEATS", "动作→反应节拍 %s 个，要求 ≥3" % arc.get("conflicts")))
    if not arc.get("closed_loop"):
        f.append(_fail("F-CLOSURE", "单集没有闭环（开场冲突→升级→钩子）"))
    if float(arc.get("ending_hook_strength") or 0) <= float(arc.get("max_conflict_strength") or 0):
        f.append(_fail("F-END-HOOK", "结尾钩强度未超过本集最强冲突"))
    return f


def check_assets(ep):
    f = []
    assets = ep.get("assets") or []
    if not assets:
        return [_fail("F-ASSET-NONE", "没有资产清单")]
    byid = {a.get("id"): a for a in assets}
    chars = [a for a in assets if a.get("type") == "character"]
    if not chars:
        f.append(_fail("F-ASSET-CHAR", "没有角色资产"))
    for a in chars:
        aid = a.get("id")
        ident = a.get("identity") or {}
        if int(a.get("refs") or 0) < 4:
            f.append(_fail("F-ASSET-REFS", "%s 参考图 %s 张，要求 ≥4" % (aid, a.get("refs"))))
        for k in ("face_ref", "identity_string", "seed"):
            if not ident.get(k):
                f.append(_fail("F-ASSET-LOCK", "%s 身份锁缺 %s" % (aid, k)))
        s = ident.get("strength")
        if s is None or not (IDENTITY_STRENGTH[0] <= float(s) <= IDENTITY_STRENGTH[1]):
            f.append(_fail("F-ASSET-STRENGTH", "%s 参考强度 %s，应在 %.2f-%.2f"
                           % (aid, s, IDENTITY_STRENGTH[0], IDENTITY_STRENGTH[1])))
        if not (a.get("voice_ids") or []):
            f.append(_fail("F-ASSET-VOICE", "%s 没有固定音色 ID" % aid))
    return f


def check_storyboard(ep):
    f = []
    shots = ep.get("shots") or []
    assets = {a.get("id") for a in (ep.get("assets") or [])}
    if not shots:
        return [_fail("F-SHOT-NONE", "没有镜表")]
    for s in shots:
        no = s.get("no")
        dur = float(s.get("dur_s") or 0)
        if dur <= 0 or dur > SHOT_DUR_MAX:
            f.append(_fail("F-SHOT-DUR", "镜 %s 时长 %s 秒，硬顶 %.0f"
                           % (no, dur, SHOT_DUR_MAX)))
        elif dur > SHOT_DUR_HARD_WARN and not s.get("key_shot"):
            f.append(_fail("W-SHOT-LONG", "镜 %s 时长 %s 秒，超出 2-3 秒区间"
                           % (no, dur), warn=True))
        for k in ("framing", "move", "chars", "scene", "action", "emotion"):
            if not s.get(k):
                f.append(_fail("F-SHOT-FIELD", "镜 %s 缺字段 %s" % (no, k)))
        for c in (s.get("chars") or []):
            if c not in assets:
                f.append(_fail("F-SHOT-ASSET", "镜 %s 引用了不存在的角色 %s" % (no, c)))
        act = str(s.get("action") or "")
        if ("+" in act or "→" in act or "然后" in act) and not s.get("multi_ok"):
            f.append(_fail("F-SHOT-MULTI", "镜 %s 塞了多个动作：%s" % (no, act[:24])))
        if str(s.get("move")) in FAKE_MOTIONS and act.strip() in ("", "static", "静"):
            f.append(_fail("F-SHOT-FAKE-MOTION", "镜 %s 只有推拉位移，不是真动" % no))
    return f


def check_kf(ep):
    f = []
    for s in (ep.get("shots") or []):
        kf = s.get("kf") or {}
        no = s.get("no")
        if not kf:
            f.append(_fail("F-KF-MISSING", "镜 %s 没有关键帧记录" % no))
            continue
        if (kf.get("w"), kf.get("h")) != KF_SIZE:
            f.append(_fail("F-KF-SIZE", "镜 %s 关键帧 %sx%s，正档要求 %dx%d"
                           % (no, kf.get("w"), kf.get("h"), KF_SIZE[0], KF_SIZE[1])))
        for k, label in (("hand_ok", "手"), ("face_ok", "脸"),
                         ("edge_ok", "边缘"), ("no_pseudo_text", "伪文字")):
            if not kf.get(k):
                f.append(_fail("F-KF-FIX", "镜 %s 关键帧未修%s" % (no, label)))
    return f


def check_i2v(ep):
    f = []
    total = 0
    ok = 0
    for s in (ep.get("shots") or []):
        v = s.get("i2v") or {}
        no = s.get("no")
        if not v:
            f.append(_fail("F-I2V-MISSING", "镜 %s 没有出片记录" % no))
            continue
        total += 1
        if int(v.get("takes") or 0) > I2V_MAX_TAKES:
            f.append(_fail("F-I2V-TAKES", "镜 %s 抽了 %s 次，上限 %d"
                           % (no, v.get("takes"), I2V_MAX_TAKES)))
        for k, label in (("morph_ok", "变形"), ("no_pseudo_text", "伪文字"),
                         ("physics_ok", "物理"), ("no_drift", "匀速漂移"),
                         ("first_frame_ok", "首帧"), ("continuity_ok", "穿帮")):
            if not v.get(k):
                f.append(_fail("F-I2V-BREAK", "镜 %s 崩坏检查未过：%s" % (no, label)))
        if str(s.get("line") or "").strip() and not v.get("lip_sync_ok"):
            f.append(_fail("F-I2V-LIP", "镜 %s 有台词但口型未过" % no))
        if v.get("accepted"):
            ok += 1
    rate = (ok / total) if total else 0
    if total and rate < I2V_HIT_RATE_MIN:
        f.append(_fail("F-I2V-RATE", "成片率 %.0f%%，低于 %.0f%%——先修资产与提示词"
                       % (rate * 100, I2V_HIT_RATE_MIN * 100)))
    return f


def check_audio(ep):
    f = []
    for s in (ep.get("shots") or []):
        a = s.get("audio") or {}
        no = s.get("no")
        if not a:
            f.append(_fail("F-AUDIO-MISSING", "镜 %s 没有声音记录" % no))
            continue
        if str(s.get("line") or "").strip() and not a.get("voice"):
            f.append(_fail("F-AUDIO-VOICE", "镜 %s 有台词但没有配音" % no))
        if int(a.get("sfx") or 0) < 1:
            f.append(_fail("F-AUDIO-SFX", "镜 %s 没有动作音" % no))
        lv = a.get("level_lufs")
        if lv is None or not (LOUDNESS[0] <= float(lv) <= LOUDNESS[1]):
            f.append(_fail("F-AUDIO-LUFS", "镜 %s 响度 %s，应在 %.0f~%.0f"
                           % (no, lv, LOUDNESS[0], LOUDNESS[1])))
    return f


def check_assembly(ep):
    f = []
    a = ep.get("assembly") or {}
    if not a:
        return [_fail("F-ASM-NONE", "没有装配记录")]
    if int(a.get("fps") or 0) < FPS_MIN:
        f.append(_fail("F-ASM-FPS", "帧率 %s，要求 ≥%d" % (a.get("fps"), FPS_MIN)))
    if tuple(a.get("res") or ()) != KF_SIZE:
        f.append(_fail("F-ASM-RES", "分辨率 %s，要求 %s" % (a.get("res"), list(KF_SIZE))))
    if int(a.get("sample_rate") or 0) != SAMPLE_RATE:
        f.append(_fail("F-ASM-SR", "采样率 %s，要求 %d" % (a.get("sample_rate"), SAMPLE_RATE)))
    if int(a.get("subtitle_max_chars") or 0) > SUBTITLE_MAX_CHARS:
        f.append(_fail("F-ASM-SUB", "单行字幕 %s 字，上限 %d"
                       % (a.get("subtitle_max_chars"), SUBTITLE_MAX_CHARS)))
    if not a.get("speed_interpolated"):
        f.append(_fail("F-ASM-SPEED", "变速没有插值"))
    if float(a.get("first3s_diff") or 0) <= FIRST3S_DIFF_MIN:
        f.append(_fail("F-ASM-FIRST3S", "前 3 秒帧差 %s，要求 >%.2f"
                       % (a.get("first3s_diff"), FIRST3S_DIFF_MIN)))
    bad = [t for t in (a.get("transitions") or []) if t in BANNED_TRANSITIONS]
    if bad:
        f.append(_fail("F-ASM-TRANS", "用了短视频语法转场：%s" % ",".join(sorted(set(bad)))))
    return f


def check_qc(ep):
    f = []
    q = ep.get("qc") or {}
    seven = q.get("seven") or {}
    for k, label in (("resolution", "分辨率"), ("fps", "帧率"), ("audio_track", "音轨"),
                     ("loudness", "响度"), ("shot_len", "镜长"), ("first3s", "前3秒"),
                     ("subtitle", "字幕")):
        if not seven.get(k):
            f.append(_fail("F-QC-SEVEN", "七项硬指标未过：%s" % label))
    if float(q.get("blind_score") or 0) < BLIND_SCORE_MIN:
        f.append(_fail("F-QC-BLIND", "盲评 %s，要求 ≥%.0f" % (q.get("blind_score"), BLIND_SCORE_MIN)))
    if int(q.get("versions") or 0) > VERSIONS_MAX:
        f.append(_fail("F-QC-VERSIONS", "版本 %s 个，上限 %d——超线先修闸"
                       % (q.get("versions"), VERSIONS_MAX)))
    return f


def check_publish(ep):
    f = []
    p = ep.get("publish") or {}
    aigc = p.get("aigc") or {}
    for k, label in (("visual", "画面显式"), ("metadata", "元数据隐式"), ("per_episode", "每集提示")):
        if not aigc.get(k):
            f.append(_fail("F-PUB-AIGC", "AIGC 标识缺：%s" % label))
    if p.get("filing") != "done":
        f.append(_fail("F-PUB-FILING", "备案未完成"))
    return f


CHECKS = {
    "script": check_script, "assets": check_assets, "storyboard": check_storyboard,
    "kf": check_kf, "i2v": check_i2v, "audio": check_audio,
    "assembly": check_assembly, "qc": check_qc, "publish": check_publish,
}


def evaluate(ep):
    """全量评估：返回 verdict / 首个阻塞段 / 全部失败码。"""
    fails = []
    warns = []
    blocked_at = None
    per_stage = {}
    for st in STAGES:
        fs = CHECKS[st](ep)
        errs = [x for x in fs if not x.get("warn")]
        warns.extend([x for x in fs if x.get("warn")])
        per_stage[st] = fs
        if errs:
            fails.extend(errs)
            if blocked_at is None:
                blocked_at = st
    return {
        "verdict": "PASS" if not fails else "BLOCKED",
        "blocked_at": blocked_at,
        "warnings": warns,
        "failures": fails,
        "by_stage": {k: v for k, v in per_stage.items() if v},
        "next_gate": GATE_OF_STAGE.get(blocked_at) if blocked_at else "READY-TO-PUBLISH",
    }


def can_advance(current, target, ep):
    """状态机：只允许相邻推进，且目标段的门必须过。"""
    if current not in STAGES or target not in STAGES:
        return False, "F-SM-UNKNOWN", "未知状态 %s/%s" % (current, target)
    i, j = STAGES.index(current), STAGES.index(target)
    if j != i + 1:
        return False, "F-SM-SKIP", "禁止跳步：%s → %s" % (current, target)
    fs = CHECKS[target](ep)
    if fs:
        return False, "F-SM-GATE", "%s 门未过：%s" % (target, fs[0]["code"])
    return True, None, None


# ---- 自检：3 个样本 + 10 个反例 -------------------------------------------------
def _good():
    shot = lambda no, line, takes=2: {
        "no": no, "dur_s": 2.5, "framing": "MS", "move": "static",
        "chars": ["c1"], "scene": "s1", "action": "推门进来", "emotion": "警觉",
        "line": line, "kf": {"w": 1080, "h": 1920, "hand_ok": True, "face_ok": True,
                             "edge_ok": True, "no_pseudo_text": True},
        "i2v": {"takes": takes, "morph_ok": True, "no_pseudo_text": True, "physics_ok": True,
                "no_drift": True, "first_frame_ok": True, "continuity_ok": True,
                "lip_sync_ok": bool(line), "accepted": True},
        "audio": {"voice": bool(line), "sfx": 1, "level_lufs": -14},
    }
    return {
        "series": {"form": "2d-i2v", "kind": "manju", "platform": "hongguo", "style_anchor": "day"},
        "episode": {"no": 1, "duration_s": 75,
                    "arc": {"hook_3s": True, "conflicts": 3, "closed_loop": True,
                            "ending_hook_strength": 0.9, "max_conflict_strength": 0.6}},
        "assets": [{"id": "c1", "type": "character", "refs": 5,
                    "identity": {"face_ref": True, "identity_string": "C1-LOCK",
                                 "seed": 1234, "strength": 0.8},
                    "voice_ids": ["v-c1-1"]},
                   {"id": "s1", "type": "scene", "refs": 2}],
        "shots": [_good_shot(1, "谁在外面"), _good_shot(2, "")],
        "assembly": {"fps": 30, "res": [1080, 1920], "sample_rate": 48000,
                     "subtitle_max_chars": 15, "speed_interpolated": True,
                     "first3s_diff": 0.05, "transitions": ["cut", "match_action"]},
        "qc": {"seven": {"resolution": True, "fps": True, "audio_track": True,
                         "loudness": True, "shot_len": True, "first3s": True, "subtitle": True},
               "blind_score": 9.2, "versions": 2},
        "publish": {"aigc": {"visual": True, "metadata": True, "per_episode": True},
                    "filing": "done"},
    }


def _good_shot(no, line, takes=2):
    return {
        "no": no, "dur_s": 2.5, "framing": "MS", "move": "static",
        "chars": ["c1"], "scene": "s1", "action": "推门进来", "emotion": "警觉",
        "line": line,
        "kf": {"w": 1080, "h": 1920, "hand_ok": True, "face_ok": True,
               "edge_ok": True, "no_pseudo_text": True},
        "i2v": {"takes": takes, "morph_ok": True, "no_pseudo_text": True, "physics_ok": True,
                "no_drift": True, "first_frame_ok": True, "continuity_ok": True,
                "lip_sync_ok": bool(line), "accepted": True},
        "audio": {"voice": bool(line), "sfx": 1, "level_lufs": -14},
    }


def _mut(fn):
    ep = _good()
    fn(ep)
    return ep


def self_test():
    cases = []
    cases.append(("good", _good(), "PASS", None))
    cases.append(("no-assets", _mut(lambda e: e.update(assets=[])), "BLOCKED", "F-ASSET-NONE"))
    cases.append(("no-audio", _mut(lambda e: [s.pop("audio") for s in e["shots"]]),
                  "BLOCKED", "F-AUDIO-MISSING"))
    cases.append(("shot-4s-warn", _mut(lambda e: e["shots"][0].update(dur_s=4.2)),
                  "PASS", None))
    cases.append(("shot-6s", _mut(lambda e: e["shots"][0].update(dur_s=6.0)),
                  "BLOCKED", "F-SHOT-DUR"))
    cases.append(("static-open", _mut(lambda e: e["episode"]["arc"].update(hook_3s=False)),
                  "BLOCKED", "F-HOOK-3S"))
    cases.append(("480p", _mut(lambda e: e["shots"][0]["kf"].update(w=854, h=480)),
                  "BLOCKED", "F-KF-SIZE"))
    cases.append(("4-takes", _mut(lambda e: e["shots"][0]["i2v"].update(takes=4)),
                  "BLOCKED", "F-I2V-TAKES"))
    cases.append(("fake-motion", _mut(lambda e: e["shots"][0].update(move="push_in", action="static")),
                  "BLOCKED", "F-SHOT-FAKE-MOTION"))
    cases.append(("no-aigc", _mut(lambda e: e["publish"]["aigc"].update(metadata=False)),
                  "BLOCKED", "F-PUB-AIGC"))
    cases.append(("loud-8", _mut(lambda e: e["shots"][0]["audio"].update(level_lufs=-8)),
                  "BLOCKED", "F-AUDIO-LUFS"))
    cases.append(("speed-no-interp", _mut(lambda e: e["assembly"].update(speed_interpolated=False)),
                  "BLOCKED", "F-ASM-SPEED"))
    cases.append(("banned-trans", _mut(lambda e: e["assembly"].update(transitions=["cut", "white_flash"])),
                  "BLOCKED", "F-ASM-TRANS"))
    cases.append(("blind-8", _mut(lambda e: e["qc"].update(blind_score=8.4)),
                  "BLOCKED", "F-QC-BLIND"))
    fails = []
    for name, ep, want, code in cases:
        got = evaluate(ep)
        ok = got["verdict"] == want and (code is None or any(f["code"] == code for f in got["failures"]))
        if not ok:
            fails.append("%s: want %s/%s got %s/%s" % (
                name, want, code, got["verdict"],
                [f["code"] for f in got["failures"]][:3]))
    # 状态机：跳步必须被拒
    ep = _good()
    ok_adj, _, _ = can_advance("script", "assets", ep)
    ok_skip, code, _ = can_advance("script", "i2v", ep)
    if not ok_adj:
        fails.append("sm-adjacent: should pass")
    if ok_skip or code != "F-SM-SKIP":
        fails.append("sm-skip: should be rejected")
    if fails:
        print("SELFTEST FAIL (%d)：" % len(fails))
        for x in fails:
            print("  -", x)
        return 1
    print("SELFTEST OK: %d 样本（含 1 正例、%d 反例、状态机跳步）全部符合预期" % (len(cases), len(cases)-1))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--check", metavar="EPISODE_JSON")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.check:
        ep = json.load(open(a.check, encoding="utf-8"))
        print(json.dumps(evaluate(ep), ensure_ascii=False, indent=1))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
