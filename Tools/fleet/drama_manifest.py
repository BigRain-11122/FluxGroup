#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drama_manifest.py - 把"盘上的素材"变成装配器能吃的 manifest（工序链缺的那一环）。

为什么（2026-11-03 实测）：漫剧/短剧链断在这里——src-scan 只报"哪几个目录有片段"，
assemble 却要一份 manifest-<date>.json；没人写它，于是装配段每天报 BLOCKED，
线看起来在跑、其实永远出不了片。这不是素材缺口，是自动化缺口。

本工具只做确定性的事：找片段、按镜号排序、认人声/配乐、可选读 srt 字幕，写 manifest。
不做创作判断（分镜顺序、字幕文案由分镜/剧本段给）。

用法：
  python3 drama_manifest.py --dir media/drama-sample-v2 --out media/drama-tools/manifest-2026-11-03.json
  python3 drama_manifest.py --dir media/x --out m.json --voice v.mp3 --music bgm.wav --subs s.srt
Exit: 0 片段已找到并写出 manifest；3 没找到片段（manifest 仍写出，clips 为空，供下游判 BLOCKED）。
"""
import argparse
import json
import os
import re
import sys

VIDEO_EXT = (".mp4", ".mov", ".m4v", ".webm")
AUDIO_EXT = (".mp3", ".wav", ".m4a", ".aac", ".flac")
# 装配产物与中间件不算素材：asm-* 是上一次装配结果，重跑会把旧成片再拼一遍。
EXCLUDE_PREFIX = ("asm-", "out-", "final-")
VOICE_HINT = ("voice", "tts", "narration", "vo_")
MUSIC_HINT = ("music", "bgm", "score", "soundtrack")


def natkey(name):
    """c2 < c10：按数字段做自然排序，否则镜序会被字典序打乱。"""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def scan(dirpath):
    clips, audios, srts = [], [], []
    for n in sorted(os.listdir(dirpath), key=natkey):
        p = os.path.join(dirpath, n)
        if not os.path.isfile(p):
            continue
        low = n.lower()
        if low.startswith(EXCLUDE_PREFIX):
            continue
        if low.endswith(VIDEO_EXT):
            clips.append(p)
        elif low.endswith(AUDIO_EXT):
            audios.append(p)
        elif low.endswith((".srt", ".ass")):
            srts.append(p)
    return clips, audios, srts


def pick(audios, hints):
    for p in audios:
        base = os.path.basename(p).lower()
        if any(h in base for h in hints):
            return p
    return None


def read_srt(path):
    """读 srt 成 [{text,from,to}]；解析不了就返回空（宁缺不编）。"""
    try:
        raw = open(path, encoding="utf-8-sig", errors="replace").read()
    except OSError:
        return []

    def ts(t):
        h, m, rest = t.replace(",", ".").split(":")
        return int(h) * 3600 + int(m) * 60 + float(rest)

    subs = []
    for block in re.split(r"\n\s*\n", raw.replace("\r\n", "\n")):
        lines = [x.strip() for x in block.splitlines() if x.strip()]
        if not lines:
            continue
        idx = 0 if re.match(r"^\d+$", lines[0]) else -1
        if len(lines) <= idx + 1 or "-->" not in lines[idx + 1]:
            continue
        a, b = lines[idx + 1].split("-->")
        text = " ".join(lines[idx + 2:])
        if text:
            subs.append({"text": text, "from": ts(a.strip()), "to": ts(b.strip())})
    return subs


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice", default="")
    ap.add_argument("--music", default="")
    ap.add_argument("--subs", default="")
    a = ap.parse_args(argv)

    if not os.path.isdir(a.dir):
        print("[man] 目录不存在：%s（rc=3）" % a.dir)
        write(a.out, {"clips": [], "blocked": "目录不存在：%s" % a.dir})
        return 3

    clips, audios, srts = scan(a.dir)
    man = {
        "clips": clips,
        "voice_at": 0.6,
        "music_gain": 0.3,
        "source_dir": a.dir,
    }
    voice = a.voice or pick(audios, VOICE_HINT)
    music = a.music or pick(audios, MUSIC_HINT)
    if voice:
        man["voice"] = voice
    if music:
        man["music"] = music
    subs = read_srt(a.subs) if a.subs else (read_srt(srts[0]) if srts else [])
    if subs:
        man["subs"] = subs

    if not clips:
        man["blocked"] = "目录里没有 i2v 片段（%s 下无 %s）" % (a.dir, "/".join(VIDEO_EXT))
        write(a.out, man)
        print("[man] 没有片段：%s（manifest 已写，clips 为空，rc=3）" % a.dir)
        return 3

    write(a.out, man)
    print("[man] manifest -> %s（片段 %d / 人声 %s / 配乐 %s / 字幕 %d）"
          % (a.out, len(clips), "有" if voice else "无", "有" if music else "无", len(subs)))
    return 0


def write(path, man):
    # 回执必须带 verdict（2026-11-03）：没有判据字段的产物在质量门里只能记 UNKNOWN，
    # 上游明明跑成功了也会被判成缺件。
    man["verdict"] = "PASS" if man.get("clips") else "BLOCKED"
    man["status"] = man["verdict"]
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))