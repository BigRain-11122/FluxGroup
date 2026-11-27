# -*- coding: utf-8 -*-
"""Build a casting reel: one representative line per main character.

Output: media/drama-eps-audio/CASTING-REEL-r1202.mp3 + a .md index (who says what).
Purpose: let a human judge each voice in ~40 seconds instead of scrubbing 60 episodes.
"""
import io
import json
import os
import subprocess
import sys
import wave

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
MF = r"C:\Fluxgroup\FluxGroup\media\drama-tts-out\r1202_preview\MANIFEST-r998.json"
OUTDIR = r"C:\Fluxgroup\FluxGroup\media\drama-eps-audio"
FF = r"C:\Fluxgroup\MiniGame\Tools\ffmpeg\bin\ffmpeg.exe"
TMP = os.path.join(OUTDIR, "_reel")

WANT = [
    ("CH", "主角 长虹", ("CH", "长虹", "长")),
    ("NARRATOR", "旁白", ("NARRATOR", "旁白", "VO", "字幕")),
    ("MANCANG", "满仓（喜剧）", ("MANCANG", "满仓")),
    ("RED", "红利（女记者）", ("RED", "红利")),
    ("XIONG", "熊天成（反派）", ("XIONG", "熊天成")),
    ("XIONGWEI", "熊伟（反派之子）", ("XIONGWEI", "熊伟")),
    ("CROWD", "散户群", ("CROWD", "散户", "群众")),
]


def dur(p):
    with wave.open(p) as w:
        return w.getnframes() / float(w.getframerate())


def main():
    d = json.load(open(MF, encoding="utf-8"))
    lines = [l for l in d["lines"] if l.get("ok") and os.path.exists(l.get("file", ""))]
    os.makedirs(TMP, exist_ok=True)
    picked, used = [], set()
    for key, label, aliases in WANT:
        best = None
        for l in lines:
            spk = (l.get("speaker") or "")
            if not any(a in spk for a in aliases):
                continue
            a = l.get("audio_s") or 0
            if 1.2 <= a <= 9.5 and (best is None or a > (best.get("audio_s") or 0)):
                best = l
        if best:
            picked.append((label, best))
            used.add(best["name"])

    if not picked:
        print("no lines picked")
        return 2

    silence = os.path.join(TMP, "sil.wav")
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                    "-i", "anullsrc=r=22050:cl=mono", "-t", "0.45", silence], check=False)

    parts = []
    idx = []
    for i, (label, l) in enumerate(picked):
        parts.append(l["file"])
        idx.append((i + 1, label, l.get("speaker"), l.get("text"), round(dur(l["file"]), 2)))
        if i < len(picked) - 1:
            parts.append(silence)

    listf = os.path.join(TMP, "list.txt")
    with open(listf, "w", encoding="utf-8") as f:
        for p in parts:
            f.write("file '%s'\n" % p.replace("\\", "/"))

    out = os.path.join(OUTDIR, "CASTING-REEL-r1202.mp3")
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", listf, "-c:a", "libmp3lame", "-b:a", "160k", "-af",
                    "loudnorm=I=-16:TP=-1.5", out], check=False)

    md = os.path.join(OUTDIR, "CASTING-REEL-r1202.md")
    with open(md, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 配音选角试听表（r1202·清洗后文本）\n\n")
        f.write("| # | 角色 | 原始说话人写法 | 时长 | 台词 |\n|---|---|---|---|---|\n")
        for n, label, spk, text, ad in idx:
            f.write("| %d | %s | %s | %.2fs | %s |\n" % (n, label, spk, ad, (text or "")[:44]))
        f.write("\n> 各角色用不同 zero-shot 参考音：主角/少年=voice_12、满仓/旁白/散户=voice_05、红利=voice_04（女）、"
                "熊系=voice_07（低音）。如某角色听着不对，直接点名换参考音即可整批复用。\n")
    print("REEL %s (%d chars) + %s" % (out, len(picked), md))
    return 0


if __name__ == "__main__":
    sys.exit(main())