# -*- coding: utf-8 -*-
"""ledger_append.py - append text to a repo ledger using the file's own newline/encoding.

Why: these ledgers are read by both humans and grep-based gates; mixing LF into a CRLF
file produces phantom diffs and broke blob comparisons before (2026-10-17 judgement).

Usage: python Tools/ledger_append.py <file> <text-file-utf8>
"""
import io
import os
import sys


def main(argv):
    target, src = argv
    with io.open(src, encoding="utf-8") as f:
        text = f.read()
    raw = open(target, "rb").read()
    nl = b"\r\n" if b"\r\n" in raw else b"\n"
    body = text.replace("\r\n", "\n").replace("\n", nl.decode())
    if not text.endswith("\n"):
        body += nl.decode()
    with open(target, "ab") as f:
        f.write(body.encode("utf-8"))
    print("APPENDED %s (+%d bytes)" % (os.path.basename(target), len(body.encode("utf-8"))))


if __name__ == "__main__":
    main(sys.argv[1:])