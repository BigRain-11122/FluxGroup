#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drama_av_manifest.py — D6/D7 的「配音+字幕 → 装配 manifest」桥。

为什么（2026-11-20）：`drama_assemble.py` 吃的是
  {clips, voice, voice_at, music, music_gain, subs[{text,from,to}], font}
但没有任何工序把「每镜的 sub 文本 + 每镜的配音 wav + 每镜的 mp4」拼成这份 manifest。
没有它，D7 永远只能手搓。

输入约定（按集目录，全部可缺）：
  <base>/kf_prompts.json      镜表（提供 sub / dur 顺序）
  <base>/i2v/EPxxx_NN.mp4      逐镜片段（缺则该镜只出字幕占位，不编入视频）
  <base>/vo/EPxxx_NN.wav       逐镜配音（piper 等产出；缺则该镜无旁白）
输出：
  <base>/assemble_manifest.json

用法：
  python Tools/fleet/drama_av_manifest.py --ep 1 [--music bgm.wav] [--voice-at 0.15]
Exit: 0 写出；3 一镜可用片段都没有
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def wav_dur(p):
    """最小 WAV 时长读取（不引 ffprobe，避免环境依赖）。"""
    import wave
    try:
        with wave.open(p, "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return 0.0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", type=int, required=True)
    ap.add_argument("--root", default=os.path.join(ROOT, "cph4", "fleet", "out", "drama"))
    ap.add_argument("--music", default="")
    ap.add_argument("--music-gain", type=float, default=0.28)
    ap.add_argument("--voice-at", type=float, default=0.15)
    ap.add_argument("--mix", action="store_true", help="把逐镜配音按时间线混成单轨 _mixed.wav")
    ap.add_argument("--font", default="")
    a = ap.parse_args(argv)

    base = os.path.join(a.root, "EP%03d" % a.ep)
    plan = os.path.join(base, "kf_prompts.json")
    if not os.path.isfile(plan):
        print("AV ABORT kf_prompts missing")
        return 3
    rows = json.load(open(plan, encoding="utf-8"))

    clips, subs, voices = [], [], []
    t = 0.0
    for r in rows:
        sid = r["id"]
        dur = float(r.get("dur") or 3.0)
        mp4 = os.path.join(base, "i2v", sid + ".mp4")
        wav = os.path.join(base, "vo", sid + ".wav")
        have_v = os.path.isfile(mp4)
        have_a = os.path.isfile(wav)
        if have_v:
            clips.append(os.path.relpath(mp4, ROOT).replace("\\", "/"))
        if have_a:
            voices.append({"file": os.path.relpath(wav, ROOT).replace("\\", "/"), "at": round(t + a.voice_at, 2)})
        sub = (r.get("sub") or "").strip()
        if sub:
            subs.append({"text": sub, "from": round(t + 0.1, 2), "to": round(t + dur - 0.1, 2)})
        t += dur if have_v else 0.0   # 无片段不计入时间线（避免字幕错位）

    if not clips:
        print("AV EP%03d no clips (i2v 未出)" % a.ep)
        return 3

    # 单轨混音（drama_assemble 只吃一条 voice 轨）：按时间线把每镜配音摆到位再拼
    mixed = ""
    if a.mix and voices:
        try:
            from pydub import AudioSegment
            total_ms = int(round(t * 1000)) + 200
            canvas = AudioSegment.silent(duration=total_ms, frame_rate=48000).set_channels(1)
            for v in voices:
                seg = AudioSegment.from_file(os.path.join(ROOT, v["file"]))
                seg = seg.set_frame_rate(48000).set_channels(1)
                canvas = canvas.overlay(seg, position=int(round(v["at"] * 1000)))
            mp = os.path.join(base, "vo", "_mixed.wav")
            os.makedirs(os.path.dirname(mp), exist_ok=True)
            canvas.export(mp, format="wav")
            mixed = os.path.relpath(mp, ROOT).replace("\\", "/")
            print("AV mixed voice -> %s (%.2fs)" % (mixed, len(canvas) / 1000.0))
        except Exception as e:
            print("AV mix failed (%s) -> 退回逐镜 voices" % type(e).__name__)

    man = {
        "clips": clips,
        "voice": mixed or (voices[0]["file"] if len(voices) == 1 else ""),
        "voice_at": 0.0 if mixed else a.voice_at,
        "voices": voices,
        "music": a.music,
        "music_gain": a.music_gain,
        "subs": subs,
        "font": a.font,
        "note": "由 drama_av_manifest.py 生成；voice=_mixed.wav 时 voice_at=0（已按时间线对齐）",
    }
    outp = os.path.join(base, "assemble_manifest.json")
    json.dump(man, open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("AV EP%03d clips=%d subs=%d voices=%d timeline=%.1fs -> %s" % (
        a.ep, len(clips), len(subs), len(voices), t, os.path.relpath(outp, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
