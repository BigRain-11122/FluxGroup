#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mv_beats_anchor.py - beats/downbeat anchors for the MV album line, CPU-only.

Why: the first-batch 7 songs have beats anchors (madmom RNNDownBeat), the other
~34 album tracks do not, and madmom cannot be installed on bm-a. librosa is
already in the interpreter, so beats can be produced here instead of waiting for
the bm-b whisperX lane (which only the words leg needs).

Schema is intentionally identical to <song>-beats.json produced by bm-b:
  song, source, model, n_beats, n_downbeats, duration_sec, beats[[t, pos]], downbeats[t]
The model string states the real engine - this is NOT madmom RNNDownBeat and must
not be presented as such.

Usage:
  python Tools/mv_beats_anchor.py --limit 1 --report D:\\FleetWorker\\review\\beats_probe.json
  python Tools/mv_beats_anchor.py --missing-only
"""
import argparse
import json
import os
import sys
import time

ANCHORS = os.path.join("cph4", "fleet", "mv-album-001-jay", "anchors")
AUDIO = os.path.join("cph4", "fleet", "mv-album-001-jay", "audio")
MODEL = "librosa-1.0.0-beat_track+flux-phase(assumed 4/4)"


def load_audio(path, sr=22050):
    import librosa
    y, _ = librosa.load(path, sr=sr, mono=True)
    return y, sr


def track(y, sr):
    import librosa
    import numpy as np
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, trim=False)
    # librosa >=1.0 returns tempo as a 1-element array, older versions a float
    tempo = float(np.atleast_1d(tempo).ravel()[0])
    if len(beat_frames) < 8:
        return None
    onset = librosa.onset.onset_strength(y=y, sr=sr)
    onset = onset / (onset.max() + 1e-9)
    # bar phase: pick the phase whose positions carry the most onset energy
    best_phase, best_score = 1, -1.0
    for phase in range(4):
        idx = beat_frames[phase::4]
        idx = idx[idx < len(onset)]
        if len(idx) == 0:
            continue
        score = float(onset[idx].sum()) / len(idx)
        if score > best_score:
            best_score, best_phase = score, phase + 1
    times = librosa.frames_to_time(beat_frames, sr=sr)
    beats = []
    downbeats = []
    for i, t in enumerate(times):
        pos = ((i - (best_phase - 1)) % 4) + 1
        beats.append([round(float(t), 3), pos])
        if pos == 1:
            downbeats.append(round(float(t), 3))
    return {
        "model": MODEL,
        "tempo_bpm": round(float(tempo), 2),
        "n_beats": len(beats),
        "n_downbeats": len(downbeats),
        "beats": beats,
        "downbeats": downbeats,
    }


def discover(anchors_dir, audio_dir, missing_only=True):
    words, beats, base = set(), set(), set()
    for f in os.listdir(anchors_dir):
        if f.endswith("-words.json"):
            words.add(f[: -len("-words.json")])
        elif f.endswith("-beats.json"):
            beats.add(f[: -len("-beats.json")])
    out = []
    for f in os.listdir(audio_dir):
        if not f.lower().endswith(".mp3"):
            continue
        # audio file names carry a "歌手 - 歌名.mp3" shape; skip single-track
        # source copies such as mv001_source_320k.mp3 that carry no artist prefix
        stem = os.path.splitext(f)[0]
        if " - " not in stem:
            continue
        song = stem.split(" - ", 1)[-1]
        if missing_only and song in beats:
            continue
        out.append({"song": song, "mp3": f, "has_words": song in words, "has_beats": song in beats})
    # songs that already have word anchors are worth more (full shotgrid becomes possible)
    out.sort(key=lambda r: (not r["has_words"], r["song"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchors-dir", default=ANCHORS)
    ap.add_argument("--audio-dir", default=AUDIO)
    ap.add_argument("--all", action="store_true", help="include songs that already have beats")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--report", default="")
    ap.add_argument("--song", default="", help="only this song")
    args = ap.parse_args()

    todo = discover(args.anchors_dir, args.audio_dir, missing_only=not args.all)
    if args.song:
        todo = [r for r in todo if r["song"] == args.song]
    if args.limit:
        todo = todo[: args.limit]
    if not todo:
        print("NOTHING-TO-DO")
        return 0

    rows = []
    ok = fail = 0
    for r in todo:
        mp3 = os.path.join(args.audio_dir, r["mp3"])
        dst = os.path.join(args.anchors_dir, r["song"] + "-beats.json")
        t0 = time.time()
        try:
            y, sr = load_audio(mp3)
            res = track(y, sr)
            if res is None:
                raise RuntimeError("too few beats detected")
            doc = {
                "song": r["song"],
                "source": r["mp3"],
                "model": res["model"],
                "tempo_bpm": res["tempo_bpm"],
                "n_beats": res["n_beats"],
                "n_downbeats": res["n_downbeats"],
                "duration_sec": round(len(y) / float(sr), 2),
                "beats": res["beats"],
                "downbeats": res["downbeats"],
            }
            with open(dst, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(doc, fh, ensure_ascii=False, indent=1)
            ok += 1
            rows.append({
                "song": r["song"], "status": "OK", "out": dst,
                "tempo_bpm": res["tempo_bpm"], "n_beats": res["n_beats"],
                "n_downbeats": res["n_downbeats"], "duration_sec": doc["duration_sec"],
                "secs": round(time.time() - t0, 2),
            })
            print("OK   %-16s bpm=%-6s beats=%-4d down=%-4d %.1fs" % (
                r["song"], res["tempo_bpm"], res["n_beats"], res["n_downbeats"], time.time() - t0))
        except Exception as exc:
            fail += 1
            rows.append({"song": r["song"], "status": "FAIL", "error": str(exc)})
            print("FAIL %-16s %s" % (r["song"], exc))

    summary = {"model": MODEL, "ok": ok, "fail": fail, "total": len(todo), "rows": rows}
    if args.report:
        os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
        with open(args.report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=1)
        print("report -> %s" % args.report)
    print("SUMMARY ok=%d fail=%d total=%d" % (ok, fail, len(todo)))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())