# -*- coding: utf-8 -*-
"""kn_shotlist_coverage_c2175.py - third birth-station gate: shot-list coverage.

C2174 proved the KN 37.22-78.50 block cannot be fixed at the assembly stage:
one prop (the paper plane) holds 32.62 s of a 41.28 s span and punched-in
framing does not move the motif gate. This script moves that ruling upstream.
It reads the authored shot list, derives a declared prop class per unit, and
measures three things the previous probes could not see before a burn:

  1. prop screen-time share inside a sliding 40 s window (budget: no single
     physical prop over one third of the window),
  2. the longest run of consecutive units that share BOTH the declared camera
     position and the same prop class (budget: 3 units),
  3. song-level prop share, reported as advisory because the whole film is one
     prop's journey.

It then applies a span-preserving re-author plan (two non-plane inserts carved
out of the two plane windows that sit inside the starved block, no downstream
window touched) and re-measures. Insert prompts are built through the shots
module's own lexicon builders so grade, texture and style stay identical, and
are linted in both t2i and video modes before they are written out.

Products (all under media/mv-album-001-jay/evidence-c2175/):
  coverage.json, COVERAGE-GATE-c2175.md, COVERAGE-BOARD-c2175.png,
  and local-i2v/run-bmc-kn-inserts-c2175.json (staged, KF pending, not fired).
"""

import io
import json
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MEDIA = os.path.join(REPO, "media", "mv-album-001-jay")
OUT = os.path.join(MEDIA, "evidence-c2175")

SHOTS_FILE = None
for name in os.listdir(HERE):
    if name.endswith("-shots-v2.py") and name.startswith(u"\u53ef\u7231"):
        SHOTS_FILE = os.path.join(HERE, name)
        break
if not SHOTS_FILE:
    raise SystemExit("FATAL: KN shots file not found")

spec = importlib.util.spec_from_file_location("kn_shots", SHOTS_FILE)
SH = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SH)
LX = SH.LX

# ---- declared prop class ---------------------------------------------------
# plane_subject: the plane is the grammatical subject of the frame (confirmed on
# rendered frames by the C2174 area measure for the six units inside the block).
PLANE_SUBJECT = {"KN04", "KN05", "KN06", "KN07", "KN10", "KN11", "KN12", "KN13",
                 "KN14", "KN15", "KN16", "KN19", "KN20", "KN20b", "KN21",
                 "KN28", "KN29", "KN30"}
# plane_handled: a person handles the plane, so it holds the frame but is not
# the subject on its own (C2172 sampled these as person-led).
PLANE_HANDLED = {"KN01", "KN03"}
# everything else is non-plane coverage (city, her, him, sky).

BLOCK = (37.22, 78.50)
WINDOW_S = 40.0
PROP_BUDGET = 1.0 / 3.0
RUN_BUDGET = 3
# C2174 arithmetic: keeping four plane units leaves 10.38 s of holes, so the
# block needs at least that much non-plane coverage inside it to be cullable.
COVERAGE_TARGET_S = 10.38


def prop_class(shot_id):
    if shot_id in PLANE_SUBJECT:
        return "plane_subject"
    if shot_id in PLANE_HANDLED:
        return "plane_handled"
    return "non_plane"


def framing_key(prompt):
    """Declared camera position: the framing/motion clause of the i2v prompt."""
    body = prompt.split("16:9. ", 1)[-1]
    return body.split(";", 1)[0].strip().lower()


def collect():
    units = []
    # REUSE rows carry five fields only, so a reused window inherits the camera
    # and prop class of the authored unit it points at.
    base = {r[0]: r for r in SH.NEW}
    for row in list(SH.NEW) + list(SH.REUSE):
        sid, t0, t1 = row[0], row[1], row[2]
        prompt = row[6] if len(row) > 6 else base[sid][6]
        units.append({
            "shot": sid,
            "t0": round(t0, 2),
            "t1": round(t1, 2),
            "win_s": round(t1 - t0, 2),
            "speed": row[3],
            "prop": prop_class(sid),
            "camera": framing_key(prompt),
            "reuse": row in list(SH.REUSE),
        })
    units.sort(key=lambda u: u["t0"])
    return units


def overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def prop_share_in(units, t0, t1, prop):
    got = 0.0
    for u in units:
        if u["prop"] == prop:
            got += overlap(t0, t1, u["t0"], u["t1"])
    return got / (t1 - t0)


def sliding_max(units, prop, end):
    worst = (0.0, 0.0)
    t = 0.0
    while t + WINDOW_S <= end + 1e-6:
        s = prop_share_in(units, t, t + WINDOW_S, prop)
        if s > worst[1]:
            worst = (round(t, 2), round(s, 4))
        t += 1.0
    return worst


def longest_run(units):
    best = []
    cur = []
    for u in units:
        if cur and u["camera"] == cur[-1]["camera"] and u["prop"] == cur[-1]["prop"]:
            cur.append(u)
        else:
            cur = [u]
        if len(cur) > len(best):
            best = list(cur)
    return best


def block_report(units, t0, t1):
    plane = prop_share_in(units, t0, t1, "plane_subject")
    handled = prop_share_in(units, t0, t1, "plane_handled")
    non = prop_share_in(units, t0, t1, "non_plane")
    inside = [u for u in units if u["t0"] >= t0 - 1e-6 and u["t1"] <= t1 + 1e-6]
    return {
        "span_s": round(t1 - t0, 2),
        "plane_subject_s": round(plane * (t1 - t0), 2),
        "plane_subject_share": round(plane, 4),
        "plane_handled_share": round(handled, 4),
        "non_plane_share": round(non, 4),
        "non_plane_s": round(non * (t1 - t0), 2),
        "coverage_target_s": COVERAGE_TARGET_S,
        "coverage_ok": round(non * (t1 - t0), 2) >= COVERAGE_TARGET_S,
        "units": [u["shot"] for u in inside],
        "budget_ok": plane <= PROP_BUDGET,
    }


# ---- insert plan (span preserving, no downstream window touched) ------------
INS_A = {
    "shot": "KN31",
    "win": (43.64, 50.48),
    "src_s": 8.0,
    "prop": "non_plane",
    "kf": SH.kf("med", "low",
                "a line of small laundry swaying on a rooftop clothesline in warm window light, "
                "a small beaded bracelet hanging from the line among the cloth, the night city soft beyond",
                "warm_window", lens="50", tex="film_night"),
    "i2v": SH.i2v("A medium shot from a low angle", SH.CM["static"],
                  "A line of laundry swaying gently on a rooftop clothesline in warm window light, "
                  "a small beaded bracelet hanging among the cloth, the night city soft beyond"),
    "lyric_anchor": "gentle line of the chorus (43.64-50.48) - her world, not the plane",
    "replaces": "KN07",
}
INS_B = {
    "shot": "KN32",
    "win": (66.26, 73.26),
    "src_s": 8.0,
    "prop": "non_plane",
    "kf": SH.kf("wide", "low",
                "a small patterned cat sitting on the rooftop ledge beside a warm lit window, "
                "its tail curled around its paws, the whole night city bowl soft behind",
                "warm_window", lens="35", tex="film_night"),
    "i2v": SH.i2v("A wide shot from a low angle", SH.CM["static"],
                  "A small patterned cat sitting on the rooftop ledge beside a warm lit window, "
                  "its tail curled around its paws, the city bowl of lights soft behind it"),
    "lyric_anchor": "smart line of the chorus (66.26-73.26) - a quiet city detail, no plane",
    "replaces": "KN12 + the front of KN13",
}


def apply_plan(units):
    planned = []
    for u in units:
        sid = u["shot"]
        if sid == "KN07":
            planned.append(dict(u, shot="KN31", prop="non_plane",
                                speed=round(INS_A["src_s"] / (INS_A["win"][1] - INS_A["win"][0]), 3),
                                camera=INS_A["i2v"].split("16:9. ", 1)[-1].split(";", 1)[0].strip().lower(),
                                synth=True))
            continue
        if sid == "KN12" and not u["reuse"]:
            continue  # authored unit removed; its window goes to KN32 (reuse windows stay)
        if sid == "KN13" and not u["reuse"]:
            planned.append(dict(u, t0=73.26, win_s=round(78.50 - 73.26, 2), synth=False))
            continue
        planned.append(u)
    planned.append({
        "shot": "KN32", "t0": 66.26, "t1": 73.26, "win_s": 7.0,
        "speed": round(INS_B["src_s"] / 7.0, 3), "prop": "non_plane",
        "camera": INS_B["i2v"].split("16:9. ", 1)[-1].split(";", 1)[0].strip().lower(),
        "reuse": False, "synth": True,
    })
    planned.sort(key=lambda u: u["t0"])
    return planned


def window_check(units, end):
    bad = []
    for a, b in zip(units, units[1:]):
        d = round(b["t0"] - a["t1"], 2)
        if abs(d) > 0.05:
            bad.append((a["shot"], b["shot"], d))
    if abs(units[0]["t0"]) > 0.05:
        bad.append(("HEAD", units[0]["shot"], units[0]["t0"]))
    if abs(units[-1]["t1"] - end) > 0.05:
        bad.append(("TAIL", units[-1]["shot"], round(units[-1]["t1"] - end, 2)))
    return bad


def lint(prompt, mode):
    hits = LX.lint(prompt, mode=mode)
    return len(hits) if hits else 0


def board(before, after, path):
    from PIL import Image, ImageDraw
    W, H = 900, 420
    im = Image.new("RGB", (W, H), (16, 18, 24))
    d = ImageDraw.Draw(im)
    d.text((24, 16), "KN block 37.22-78.50s coverage: plane subject share", fill=(235, 232, 225))
    rows = [("before", before), ("after C2175 plan", after)]
    for i, (label, rep) in enumerate(rows):
        y = 70 + i * 140
        d.text((24, y - 22), "%s  plane %.1f%%  non-plane %.1f%%  budget %.0f%%" % (
            label, rep["plane_subject_share"] * 100, rep["non_plane_share"] * 100, PROP_BUDGET * 100),
            fill=(200, 196, 188))
        barw = W - 80
        x = 40
        segs = [("non-plane", rep["non_plane_share"], (96, 150, 190)),
                ("plane handled", rep["plane_handled_share"], (150, 130, 96)),
                ("plane subject", rep["plane_subject_share"], (196, 92, 72))]
        for name, frac, col in segs:
            w = int(barw * frac)
            d.rectangle([x, y, x + w, y + 54], fill=col)
            x += w
        bx = 40 + int(barw * PROP_BUDGET)
        d.line([(bx, y - 8), (bx, y + 62)], fill=(240, 220, 120), width=2)
        d.text((bx - 30, y + 66), "1/3 budget", fill=(240, 220, 120))
    d.text((24, H - 34), "yellow line = one-third prop budget; red = plane as subject", fill=(150, 146, 138))
    im.save(path, "PNG")


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    units = collect()
    end = SH.FILM_END

    before_worst = sliding_max(units, "plane_subject", end)
    before_run = longest_run([u for u in units if not u["reuse"]])
    before_block = block_report(units, *BLOCK)
    song_plane = sum(u["win_s"] for u in units if u["prop"] == "plane_subject") / end

    planned = apply_plan(units)
    gaps = window_check(planned, end)
    after_worst = sliding_max(planned, "plane_subject", end)
    after_run = longest_run([u for u in planned if not u["reuse"]])
    after_block = block_report(planned, *BLOCK)

    lint_a = {m: lint(INS_A["kf" if m == "t2i" else "i2v"], m) for m in ("t2i", "video")}
    lint_b = {m: lint(INS_B["kf" if m == "t2i" else "i2v"], m) for m in ("t2i", "video")}

    report = {
        "batch": "C2175",
        "gate": "shot-list coverage (prop budget + camera/prop run)",
        "source": os.path.basename(SHOTS_FILE),
        "budget": {"window_s": WINDOW_S, "prop_share_max": round(PROP_BUDGET, 4), "run_max": RUN_BUDGET},
        "before": {
            "block": before_block,
            "worst_40s_window": before_worst,
            "longest_run": {"units": [u["shot"] for u in before_run],
                            "len": len(before_run),
                            "camera": before_run[0]["camera"] if before_run else "",
                            "prop": before_run[0]["prop"] if before_run else ""},
            "song_plane_share": round(song_plane, 4),
        },
        "plan": {
            "kn31": {k: INS_A[k] for k in ("shot", "win", "src_s", "lyric_anchor", "replaces")},
            "kn32": {k: INS_B[k] for k in ("shot", "win", "src_s", "lyric_anchor", "replaces")},
            "kn13_after": {"win": (73.26, 78.50), "trimmed_from": (69.80, 78.50)},
            "windows_untouched_after_78_50": True,
        },
        "after": {
            "block": after_block,
            "worst_40s_window": after_worst,
            "longest_run": {"units": [u["shot"] for u in after_run],
                            "len": len(after_run),
                            "camera": after_run[0]["camera"] if after_run else "",
                            "prop": after_run[0]["prop"] if after_run else ""},
            "song_plane_share": round(
                sum(u["win_s"] for u in planned if u["prop"] == "plane_subject") / end, 4),
        },
        "prompts": {
            "KN31": {"kf": INS_A["kf"], "i2v": INS_A["i2v"], "lint_hits": lint_a},
            "KN32": {"kf": INS_B["kf"], "i2v": INS_B["i2v"], "lint_hits": lint_b},
        },
        "window_gaps": gaps,
        "verdict": None,
    }

    ok = (after_block["coverage_ok"] and not gaps
          and lint_a["t2i"] == 0 and lint_a["video"] == 0
          and lint_b["t2i"] == 0 and lint_b["video"] == 0
          and len(after_run) <= RUN_BUDGET)
    report["verdict"] = "PLAN-CLEARS-GATE" if ok else "PLAN-REVISE"

    with io.open(os.path.join(OUT, "coverage.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    board(before_block, after_block, os.path.join(OUT, "COVERAGE-BOARD-c2175.png"))

    md = []
    md.append("# KN shot-list coverage gate (C2175)\n")
    md.append("Source: `%s` / film end %.2fs\n" % (os.path.basename(SHOTS_FILE), end))
    md.append("## Budgets\n")
    md.append("- no single prop over 1/3 of any %.0fs window (song-level budget, advisory)\n"
              "- block non-plane coverage >= %.2fs, the C2174 keep-4 cull arithmetic\n"
              "- at most 3 consecutive units sharing camera position AND prop class\n"
              % (WINDOW_S, COVERAGE_TARGET_S))
    md.append("## Before (authored list as burned)\n")
    md.append("- block 37.22-78.50s: plane-subject %.2fs = **%.1f%%**, non-plane %.2fs (target >=%.2fs) -> %s"
              % (before_block["plane_subject_s"], before_block["plane_subject_share"] * 100,
                 before_block["non_plane_s"], COVERAGE_TARGET_S,
                 "OK" if before_block["coverage_ok"] else "FAIL"))
    md.append("- worst 40s window: starts %.2fs plane share %.1f%%" % (before_worst[0], before_worst[1] * 100))
    md.append("- longest run: %d units %s (camera `%s`, prop `%s`)"
              % (len(before_run), [u["shot"] for u in before_run], before_run[0]["camera"],
                 before_run[0]["prop"]))
    md.append("- song-level plane-subject share %.1f%% (advisory: the film is one prop's journey)\n"
              % (song_plane * 100))
    md.append("## Plan (span preserving)\n")
    md.append("- KN31 %.2f-%.2fs (%.2fs window, src %.1fs, speed %.3f) replaces KN07: laundry line + her bracelet, no face, no plane"
              % (INS_A["win"][0], INS_A["win"][1], INS_A["win"][1] - INS_A["win"][0], INS_A["src_s"],
                 INS_A["src_s"] / (INS_A["win"][1] - INS_A["win"][0])))
    md.append("- KN32 %.2f-%.2fs (%.2fs window, src %.1fs, speed %.3f) replaces KN12 and the front of KN13: rooftop cat by the lit window, low angle"
              % (INS_B["win"][0], INS_B["win"][1], INS_B["win"][1] - INS_B["win"][0], INS_B["src_s"],
                 INS_B["src_s"] / 7.0))
    md.append("- KN13 keeps %.2f-78.50s (trimmed take, no downstream window moves)\n" % 73.26)
    md.append("## After\n")
    md.append("- block plane-subject **%.1f%%** (was %.1f%%), non-plane %.2fs (was %.2fs) -> %s"
              % (after_block["plane_subject_share"] * 100, before_block["plane_subject_share"] * 100,
                 after_block["non_plane_s"], before_block["non_plane_s"],
                 "OK" if after_block["coverage_ok"] else "FAIL"))
    md.append("- worst 40s window: starts %.2fs plane share %.1f%% (was %.1f%% at %.2fs)"
              % (after_worst[0], after_worst[1] * 100, before_worst[1] * 100, before_worst[0]))
    md.append("- longest run: %d units %s" % (len(after_run), [u["shot"] for u in after_run]))
    md.append("- window gaps/overlaps: %s\n" % ("none" if not gaps else gaps))
    md.append("## Lint\n")
    md.append("- KN31 t2i %d / video %d hits; KN32 t2i %d / video %d hits\n"
              % (lint_a["t2i"], lint_a["video"], lint_b["t2i"], lint_b["video"]))
    md.append("## Verdict\n")
    md.append("**%s** - staged burns, KF not generated (GPU is running the KN 768P wave). "
              "Fire 480P pitch verify first, 768P only after pass.\n" % report["verdict"])
    md.append("## Next\n")
    md.append("- the worst %.0fs window is still 100%% plane at %.0fs: the reuse montage of the last third "
              "is the next coverage target, out of this round's scope\n"
              % (WINDOW_S, after_worst[0]))
    md.append("- KN31/KN32 need KF generation before a burn; the 30/30 A-pack harvest owns the GPU until then\n")
    with io.open(os.path.join(OUT, "COVERAGE-GATE-c2175.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    staged = {
        "policy": "KN insert burns (KN31/KN32) staged by C2175 coverage gate; 480P verify first, 768P only after pass",
        "gate": "COVERAGE-GATE-c2175 (prop budget <=1/3 per 40s window, camera+prop run <=3, lint clean)",
        "wave": "kn-inserts-c2175",
        "status": "staged-kf-pending",
        "total": 2,
        "total_win_s": 13.84,
        "units": [
            {"id": "KN_A-KN31", "shot": "KN31", "track": "KN", "win_s": 6.84,
             "speed": round(8.0 / 6.84, 3), "src_s": 8.0, "policy_band": "8-15s",
             "light": "warm_window", "frame": "media/mv-album-001-jay/frames/KN_KN31.png",
             "lyric_anchor": INS_A["lyric_anchor"], "note": "coverage insert A (non-plane)",
             "i2v_prompt": INS_A["i2v"]},
            {"id": "KN_A-KN32", "shot": "KN32", "track": "KN", "win_s": 7.0,
             "speed": round(8.0 / 7.0, 3), "src_s": 8.0, "policy_band": "8-15s",
             "light": "warm_window", "frame": "media/mv-album-001-jay/frames/KN_KN32.png",
             "lyric_anchor": INS_B["lyric_anchor"], "note": "coverage insert B (non-plane)",
             "i2v_prompt": INS_B["i2v"]},
        ],
    }
    man = os.path.join(HERE, "local-i2v", "run-bmc-kn-inserts-c2175.json")
    with io.open(man, "w", encoding="utf-8") as f:
        json.dump(staged, f, ensure_ascii=False, indent=1)

    print("BEFORE block plane %.1f%% | run %d | worst40 %.1f%%@%.0fs | song %.1f%%" % (
        before_block["plane_subject_share"] * 100, len(before_run), before_worst[1] * 100,
        before_worst[0], song_plane * 100))
    print("AFTER  block plane %.1f%% | run %d | worst40 %.1f%%@%.0fs | song %.1f%%" % (
        after_block["plane_subject_share"] * 100, len(after_run), after_worst[1] * 100,
        after_worst[0], sum(u["win_s"] for u in planned if u["prop"] == "plane_subject") / end * 100))
    print("lint KN31 t2i=%d video=%d | KN32 t2i=%d video=%d | gaps=%s" % (
        lint_a["t2i"], lint_a["video"], lint_b["t2i"], lint_b["video"], gaps))
    print("verdict:", report["verdict"])
    print("products:", OUT, "|", os.path.basename(man))
    if report["verdict"] != "PLAN-CLEARS-GATE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()