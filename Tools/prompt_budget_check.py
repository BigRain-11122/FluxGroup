# -*- coding: utf-8 -*-
"""Prompt budget checker (deterministic, no network, no model).

Why: SD1.5 CLIP silently truncates at 77 tokens and the tail (usually the STYLE
layer) is what gets dropped - measured cause of style drift on 992/1236 shots
(prompt-experience-ledger P-01). This tool makes the budget visible before a
burn, so the truncation is fixed at assembly time instead of diagnosed later.

Tokenizer note: this is a *heuristic* estimate (words -> ceil(len/4), punctuation
-> 1, CJK char -> 1), calibrated to be within ~10% of CLIP BPE for English
prompts. It is a guardrail, not a replacement for the real tokenizer.

Usage:
  py prompt_budget_check.py --text "a prompt string"
  py prompt_budget_check.py --file prompts.txt          # one prompt per line, '#' skipped
  py prompt_budget_check.py --json EP001.json --keys detail_en,style
  py prompt_budget_check.py --selftest
Exit code: 0 all within budget, 2 any over budget, 1 usage error.
"""
import io
import json
import math
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CJK = re.compile(r"[\u4e00-\u9fff]")
TOKEN_PART = re.compile(r"[A-Za-z0-9']+|[^\sA-Za-z0-9']")


def estimate(text, limit=77):
    words = re.findall(r"[A-Za-z0-9']+", text)
    punct = re.findall(r"[^\sA-Za-z0-9']", text)
    # punctuation that lives inside words (hyphen/apostrophe) is counted with words
    tok = sum(max(1, int(math.ceil(len(w) / 4.0))) for w in words)
    tok += sum(1 for p in punct if p not in "-'")
    cjk = len(CJK.findall(text))
    tok += cjk
    return tok, cjk


def check_one(text, limit):
    tok, cjk = estimate(text)
    verdict = "OK" if tok <= limit else "OVER"
    note = ""
    if cjk:
        note = " [CJK %d chars: Latin-trained CLIP tokenizes poorly]" % cjk
    return tok, verdict, note


def report(rows, limit):
    over = 0
    for i, text in enumerate(rows, 1):
        tok, verdict, note = check_one(text, limit)
        over += verdict != "OK"
        head = text.strip().replace("\n", " ")
        print("%3d  tok=%3d/%d  %-4s  %s%s" % (i, tok, limit, verdict, head[:90], note))
    print("SUMMARY lines=%d over=%d limit=%d" % (len(rows), over, limit))
    return 2 if over else 0


def main(argv):
    limit = 77
    text = None
    path = None
    jpath = None
    keys = ("detail_en",)
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--text":
            i += 1
            text = argv[i]
        elif a == "--file":
            i += 1
            path = argv[i]
        elif a == "--json":
            i += 1
            jpath = argv[i]
        elif a == "--keys":
            i += 1
            keys = tuple(k.strip() for k in argv[i].split(",") if k.strip())
        elif a == "--limit":
            i += 1
            limit = int(argv[i])
        elif a == "--selftest":
            rows = [
                "in extreme close-up of the broken pocket watch chain snapping, shallow depth of field",
                " ".join(["word"] * 60),
                " ".join(["word"] * 90),
                "young man in white shirt, Chang Hong, three people in one frame, hands close over the paper",
                "盛夏的交易大厅，红马甲，翻牌大屏",
            ]
            return report(rows, limit)
        i += 1

    if text is not None:
        return report([text], limit)
    if path:
        rows = []
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.rstrip("\n")
                if line.strip() and not line.lstrip().startswith("#"):
                    rows.append(line)
        return report(rows, limit)
    if jpath:
        data = json.load(open(jpath, encoding="utf-8-sig"))
        shots = data.get("shots", data if isinstance(data, list) else [])
        rows = []
        for s in shots:
            parts = [str(s.get(k) or "") for k in keys]
            joined = ", ".join(p for p in parts if p)
            if joined:
                rows.append(joined)
        return report(rows, limit)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))