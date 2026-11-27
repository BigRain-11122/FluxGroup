# -*- coding: ascii -*-
# c2133_notes_and_kanban.py - claim note (number collision), ledger note, kanban C row.

import io
import os

BASE = "K:\\Fluxgroup\\MiniGame\\"
CLAIMS = BASE + ".codely-cli\\batch-claims.log"
LEDGER = BASE + ".codely-cli\\engine-tick\\tick-ledger.txt"
KANBAN = BASE + "Design\\configs\\GLOBAL\\\u6863\u6848\\" + u"\u673a\u961f\u534f\u4f5c\u770b\u677f.md"

ROW = (u"| C | 2026-10-20 | **C2133-conform A \u6279\u6574\u6bb5\u88c5\u914d\u6837\u7247\u51fa\u7247 + \u88c5\u914d\u7d22\u5f15\u987a\u5e8f\u7f3a\u9677\u6839\u6cbb**"
       u"\uff0807:31-08:2x\uff09| \u5b9e\u7269=\u2460`media/mv-album-001-jay/assembly-packA/XQ-PACKA-CONFORM-v1-c2133.mp4`"
       u"\uff081344\u00d7768/24fps/196.25s/44.6MB\uff0c33 \u5355\u5143\u6309\u7f16\u5199\u7a97\u53e3\u786c\u5207+\u539f\u66f2 0s \u914d\u5165\uff09\uff1b"
       u"\u2461\u5ba1\u770b\u5305 `assembly-packA/review/`\uff1a960px \u4ee3\u7406\u7247 15.25MB + 33 \u683c\u5207\u70b9\u6761\u677f 204KB\uff1b"
       u"\u2462\u7d22\u5f15 v2 `xq-PACKA-ASSEMBLY-INDEX-v2-c2133.json/.md`\uff1b\u2463\u56db\u4efd\u5b9e\u6d4b\u6536\u636e\uff08conform/cutpoints/reviewpack/index-verify\uff09 | "
       u"\u5224\u5b9a=\u7d22\u5f15\u7f3a\u9677=C2132 \u6309\u6587\u4ef6\u5e8f\u5efa\u8868\uff0c\u628a\u7ec8\u7ae0\u5757 F5-33a/b/c\u3001F5-34 \u6392\u5230\u7247\u5934\uff08\u7167\u526a=\u7ec8\u7ae0\u5f00\u573a\uff09\u2192v2 \u6539\u4ece\u7f16\u5199\u76ee\u5f55\u5b9a\u5e8f\uff0c\u5c3e\u56db\u5b9e\u6d4b=F5-33a/b/c/F5-34\uff1b"
       u"\u5b9a\u65f6\u786c\u95f8 CUTPOINTS-END ok=1 exact=33/33 max_mad=2.83\uff08\u9010\u5355\u5143\u4e2d\u70b9\u5e27 vs \u6e90\u7247\u540c\u70b9\u5e27 MAD\u00b14 \u5e27\u641c\u7d22\uff09\uff1b"
       u"\u9996\u7248 scene \u95f8 12/33 \u5224\u4e3a\u68c0\u6d4b\u5668\u5c40\u9650\u975e\u526a\u8f91\u7f3a\u9677\uff08\u5df2\u5982\u5b9e\u5165\u6536\u636e\uff09\uff1b"
       u"\u773c\u95f8 10 \u5e27\u63a5\u89e6\u677f\u591a\u6a21\u6001\u8bfb=\u5341\u5e27\u5404\u4e0d\u540c/\u66dd\u5149\u6b63\u5e38/\u767d\u5929\u2192\u591c\u53d9\u4e8b\u5f27/\u8272\u8c03\u8fde\u8d2f/\u96f6\u9ed1\u5e27\u96f6\u51bb\u7ed3\uff1b"
       u"\u94f6\u884c `packA-assembly-index-verify-v1` \u2192 done\uff08INDEX-VERIFY-END ok=1 mismatches=0\uff1b07:25 \u8ba4\u9886\u540e\u672a\u8dd1=C2132 \u9a8c\u8bc1\u5668\u5220\u81ea\u5df1\u88ab\u76d1\u5b88\u5360\u7528\u7684\u65e5\u5fd7 WinError 32\uff09 | "
       u"\u4e0b\u4e00\u6b65=\u5bfc\u6f14\u5e2d\u62ff\u5ba1\u770b\u5305\u5bf9\u88c5\u914d\u5b9a\u7a3f+S5-27 \u53cc\u7b7e\uff1b\u94f6\u884c\u9884\u6302 packA-conform-origin-verify-v1\uff08\u4e0b\u8f6e\u6536\u5272\u63a8\u540e\u6838 origin\uff09 |"
       )


def append(path, text, utf8=True):
    raw = open(path, "rb").read()
    crlf = b"\r\n" in raw[-4000:]
    eol = u"\r\n" if crlf else u"\n"
    add = text
    if not raw.endswith(b"\n"):
        add = eol + add
    with open(path, "ab") as f:
        f.write(add.encode("utf-8" if utf8 else "gbk"))
    return crlf


def main():
    claim = (u"C2133-conform @2026-10-20 08:24:00 \u6574\u6bb5\u88c5\u914d\u6837\u7247\u8f6e\u2014\u2014"
             u"\u53f7\u4ee3\u8ba9\u8def\u6ce8\u8bb0\uff1aC2133 \u5df2\u5728 07:34:57 \u88ab M5 \u8f66\u9053\u5360\uff0c"
             u"\u672c\u8f6e\u4ea7\u7269\u4ee5 C2133-conform \u4e3a\u552f\u4e00\u6807\u7b7e\uff0c\u6587\u4ef6\u540d\u4e0d\u56de\u6539")
    append(CLAIMS, claim)

    note = (u"2026-10-20 08:24 | \u7f16\u53f7\u52d8\u8bef | C2133 \u4e0e M5 \u8f66\u9053 07:34:57 \u5360\u53f7\u649e\u53f7"
            u"\uff08\u5bf9\u65b9= m5 audit c2132 increment\uff09\uff1b\u672c\u8f6e\u4ea7\u7269\u7edf\u4e00\u6807\u8bb0\u4e3a **C2133-conform**"
            u"\uff08\u6587\u4ef6\u540d\u5df2\u843d\u76d8\u4e0d\u56de\u6539\uff09\uff0c\u540e\u7eed\u672c\u673a\u8f6e\u6b21\u4ece C2135 \u53d6\u53f7")
    append(LEDGER, note)

    append(KANBAN, ROW)
    print("CLAIM/LEDGER/KANBAN appended")


if __name__ == "__main__":
    main()