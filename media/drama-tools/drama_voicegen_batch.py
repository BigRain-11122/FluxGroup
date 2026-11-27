# -*- coding: utf-8 -*-
"""Batch driver: run the proven r998 voicegen for an arbitrary episode range.

Reuses drama_voicegen_eps_r998.py by overriding its module globals (EPS /
OUT_BASE / LOG / DONE) so the inference path stays byte-identical to the
pilot that produced EP001-003 (single IndexTTS2 load, per-speaker zero-shot refs).

Usage: python drama_voicegen_batch.py EP004-EP060 [--out-name r1200_ep004_060]
"""
import importlib.util
import io
import os
import re
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "drama_voicegen_eps_r998.py")
TTS_OUT = r"C:\Fluxgroup\FluxGroup\media\drama-tts-out"
EX = r"C:\Fluxgroup\FluxGroup\media\drama-tools\repos\index-tts\examples"

CALM = [0, 0, 0, 0, 0, 0, 0, 0.5625]
HAPPY5 = [0.5, 0, 0, 0, 0, 0, 0, 0]
HAPPY6 = [0.6, 0, 0, 0, 0, 0, 0, 0]

# Exact-name table (longest / most specific first). Covers ids, Chinese names,
# role aliases and _DAD variants seen across all 60 episode JSONs (92 distinct).
EXACT = [
    ("MANCANG_DAD", "voice_05.wav", HAPPY6), ("满仓爹", "voice_05.wav", HAPPY6),
    ("满爹", "voice_05.wav", HAPPY6), ("MANCANG", "voice_05.wav", HAPPY6),
    ("王满仓", "voice_05.wav", HAPPY6), ("满仓", "voice_05.wav", HAPPY6),
    ("RED_DAD", "voice_04.wav", None), ("童年红利", "voice_04.wav", None),
    ("RED", "voice_04.wav", None), ("沈红利", "voice_04.wav", None), ("红利", "voice_04.wav", None),
    ("XIONGWEI", "voice_07.wav", None), ("熊伟", "voice_07.wav", None),
    ("XIONG", "voice_07.wav", None), ("熊天成", "voice_07.wav", None),
    ("熊", "voice_07.wav", None),
    ("FATHER", "voice_07.wav", None), ("父亲", "voice_07.wav", None), ("父", "voice_07.wav", None),
    ("GRANNY", "voice_04.wav", None), ("陆振海", "voice_07.wav", None),
    ("BOY", "voice_12.wav", None), ("少年长虹", "voice_12.wav", None), ("匠人", "voice_12.wav", None),
    ("CH", "voice_12.wav", None), ("陆长虹", "voice_12.wav", None),
    ("长虹", "voice_12.wav", None), ("长", "voice_12.wav", None),
    ("CROWD", "voice_05.wav", HAPPY5), ("散户群", "voice_05.wav", HAPPY5),
    ("散户甲", "voice_05.wav", HAPPY5), ("散户乙", "voice_05.wav", HAPPY5),
    ("散户丙", "voice_05.wav", HAPPY5), ("散户", "voice_05.wav", HAPPY5),
    ("NARRATOR", "voice_05.wav", CALM), ("旁白", "voice_05.wav", CALM),
    ("VO", "voice_05.wav", CALM), ("TV", "voice_05.wav", CALM), ("PA", "voice_05.wav", CALM),
    ("TAPE", "voice_05.wav", CALM), ("广播", "voice_05.wav", CALM), ("字幕", "voice_05.wav", CALM),
    ("侍者", "voice_05.wav", None), ("经纪", "voice_05.wav", None),
    ("门卫", "voice_12.wav", None), ("经理", "voice_05.wav", None),
]

PAREN = re.compile(r"[（(][^）)]*[）)]")
SPLIT = re.compile(r"[+/、／,，]|&")


def resolve2(spk):
    """speaker string -> (ref_path, emo_vec_or_None, cast_note).

    Normalises: drop parentheticals (画外/电视/回声), then take the FIRST of any
    composite speaker (script rule: combined lines resolve to the main character),
    then exact-match longest-first.
    """
    s = PAREN.sub("", str(spk or "")).strip()
    if SPLIT.search(s):
        s = SPLIT.split(s)[0].strip()
    if not s:
        return os.path.join(EX, "voice_05.wav"), CALM, "empty->narr"
    low = s.upper()
    for name, ref, emo in EXACT:
        if name.isascii():
            if low == name.upper() or (len(name) <= 3 and low.startswith(name.upper())):
                return os.path.join(EX, ref), emo, "%s->%s" % (s, ref)
        elif s == name or (len(name) >= 2 and name in s):
            return os.path.join(EX, ref), emo, "%s->%s" % (s, ref)
    return os.path.join(EX, "voice_05.wav"), CALM, "%s->fallback narr" % s


def parse_range(tok):
    if "-" in tok:
        a, b = tok.split("-", 1)
        n0, n1 = int(a.replace("EP", "")), int(b.replace("EP", ""))
        return ["EP%03d" % n for n in range(n0, n1 + 1)]
    return [tok]


def main(argv):
    eps = []
    out_name = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--out-name":
            i += 1
            out_name = argv[i]
        elif not a.startswith("--"):
            eps.extend(parse_range(a))
        i += 1
    if not eps:
        print("usage: drama_voicegen_batch.py EP004-EP060 [--out-name NAME]")
        return 2
    if not out_name:
        out_name = "r%d_%s_%s" % (int(time.time()) % 10000, eps[0].lower(), eps[-1].lower())

    spec = importlib.util.spec_from_file_location("vg", SRC)
    vg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vg)

    vg.resolve = resolve2
    vg.EPS = eps
    vg.OUT_BASE = os.path.join(TTS_OUT, out_name)
    vg.LOG = os.path.join(BASE, "voicegen_%s.log" % out_name)
    vg.DONE = os.path.join(BASE, "voicegen_%s.DONE.json" % out_name)
    os.makedirs(vg.OUT_BASE, exist_ok=True)
    print("BATCH eps=%d (%s..%s) out=%s" % (len(eps), eps[0], eps[-1], vg.OUT_BASE), flush=True)
    vg.main()
    print("BATCH-DONE %s" % vg.DONE, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))