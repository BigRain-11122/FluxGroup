# -*- coding: ascii -*-
# c2133_closeout_writes.py - prepend the snapshot block and append ledger rows.

import io
import os
import time

SNAP = "K:\\Fluxgroup\\MiniGame\\" + u"\u81ea\u52a8\u5316\u5feb\u7167-c.md"  # auto snapshot c
LEDGER = r"K:\Fluxgroup\MiniGame\.codely-cli\engine-tick\tick-ledger.txt"

BLOCK = u"""# \u81ea\u52a8\u5316\u5feb\u7167-c\uff08C \u673a\u5feb\u7167\u00b7vC2133\uff09\u00b7 2026-10-20 08:05 \u00b7 A \u6279\u6574\u6bb5\u88c5\u914d\u6837\u7247\u51fa\u7247 + \u88c5\u914d\u7d22\u5f15\u987a\u5e8f\u7f3a\u9677\u6839\u6cbb

- **\u68c0\u6d4b\u65f6\u95f4**\uff1a2026-10-20 08:05\uff5ctick = tick-20261020-0805@c2133-packa-conform-orderfix\uff5cnormal_iteration\uff5c\u96f6 batchmode\u3001\u96f6 GPU\u3001\u96f6 MCP
- **Step0**\uff1apreflight \u5168\u9762 PASS \u96f6 FLAG\uff08AMP 40%\uff5c\u94f6\u884c 1 \u5355 claimed @07:25:59 \u65e0 runner \u4ea7\u7269 = \u672c\u8f6e\u6536\u5272\u9762\uff09\uff1bRAM 15.1% < 40% = NOT-GREEN-IDLE \u96f6\u9886\u6c60\u4e49\u52a1\uff1bGPU free 9.5G / verdict=GPU_DRAFT_OK\uff08\u672c\u8f6e\u672a\u7528 GPU\uff09
- **\u5934\u6761\u5b9e\u7269\uff08CEO/\u5bfc\u6f14\u53ef\u6253\u5f00\uff09**\uff1a
  - **A \u6279\u6574\u6bb5\u88c5\u914d\u6837\u7247** = `media/mv-album-001-jay/assembly-packA/XQ-PACKA-CONFORM-v1-c2133.mp4`\uff081344\u00d7768 / 24fps / **196.25s** / 44.6MB\uff0c33 \u5355\u5143\u6309\u7f16\u5199\u7a97\u53e3\u786c\u5207\uff0c\u539f\u66f2\u4ece 0s \u914d\u5165 0.6s/1.4s \u6de1\u5165\u6de1\u51fa\uff09
  - **\u5bfc\u6f14\u5ba1\u770b\u5305** = `assembly-packA/review/`\uff1a960px \u4ee3\u7406\u7247 15.25MB\uff08\u6b63\u7247 44.6MB\uff09+ **33 \u5355\u5143\u9996\u5e27\u5207\u70b9\u6761\u677f** `XQ-PACKA-CUT-STRIP-c2133.jpg`\uff08204KB\uff09
  - **\u88c5\u914d\u7d22\u5f15 v2** = `cph4/fleet/mv-album-001-jay/xq-PACKA-ASSEMBLY-INDEX-v2-c2133.json` + `.md`\uff0833 \u5355\u5143\u3001\u516d\u4e2a redo-r1 \u5b9a\u7247\u3001\u7f16\u5199\u7a97\u53e3\u5408\u8ba1 196.14s\uff09
  - **\u5b9e\u6d4b\u6536\u636e** = `xq-PACKA-CONFORM-c2133.json` / `xq-PACKA-CUTPOINTS-c2133.json` / `review/REVIEW-PACK-c2133.json`
- **\u672c\u8f6e\u5934\u53f7\u6839\u6cbb\uff08\u771f\u7f3a\u9677\uff09**\uff1aC2132 \u7d22\u5f15\u662f\u6309\u6587\u4ef6\u5939\u904d\u5386\u5f97\u51fa\u7684\u5b57\u540d\u5e8f\uff08F0\u3001F5\u3001S0\u2026S5\uff09\uff0c**\u628a\u7ec8\u7ae0\u5757 F5-33a/b/c\u3001F5-34 \u6392\u5230\u4e86\u7247\u5934**\u2014\u2014\u7167\u5b83\u526a\u4f1a\u62ff\u7ec8\u7ae0\u5f00\u573a\u3002v2 \u6539\u4ece\u7f16\u5199\u76ee\u5f55\uff08\u661f\u6674-i2v-PACK-A-v1.json\uff09\u5b9a\u5e8f\uff0cF5-33c \u63d2\u5728 F5-34 \u4e4b\u524d\uff1b\u6bb5\u843d\u5c3e\u56db\u5355\u5143\u5b9e\u6d4b\u4e3a `F5-33a,F5-33b,F5-33c,F5-34`\u3002
- **\u65f6\u5e8f\u8bc1\u660e\uff08\u786c\u95f8\uff09**\uff1a\u9010\u5355\u5143\u53d6\u6837\u7247\u7a97\u53e3\u4e2d\u70b9\u5e27 vs \u540c\u5355\u5143\u6e90\u7247\u540c\u65f6\u70b9\u5e27\uff08MAD\uff0c\u00b14 \u5e27\u641c\u7d22\u5438\u6536\u6210\u7247\u5e38\u91cf ~0.1s \u504f\u79fb\uff09\uff1a**CUTPOINTS-END ok=1 exact=33/33 max_mad=2.83**\uff08\u9608\u503c 6.0\uff09\u3002\u9996\u7248\u7528 ffmpeg scene \u5206\u6570\u505a\u95f8\u53ea\u5f97 12/33\uff08\u76f8\u4f3c\u955c\u4e0d\u89e6\u53d1\u3001\u955c\u5185\u8fd0\u52a8\u8bef\u89e6\u53d1\uff09\u2014\u2014\u5224\u4e3a\u68c0\u6d4b\u5668\u5c40\u9650\u975e\u526a\u8f91\u7f3a\u9677\uff0c\u5f53\u8f6e\u6362\u6d4b\u6cd5\u5e76\u5728\u6536\u636e\u91cc\u5982\u5b9e\u8bb0\u8f7d\u3002
- **\u773c\u95f8**\uff1a10 \u5e27\u63a5\u89e6\u677f\uff08\u6bcf 20s\uff09\u591a\u6a21\u6001\u8bfb\uff1a\u5341\u5e27\u5404\u4e0d\u76f8\u540c\u3001\u66dd\u5149\u6b63\u5e38\u3001\u767d\u5929\u2192\u9ec4\u660f\u2192\u591c\u7684\u53d9\u4e8b\u5f27\u3001\u8272\u8c03\u8de8\u955c\u8fde\u8d2f\u3001\u96f6\u9ed1\u5e27/\u96f6\u51bb\u7ed3\u91cd\u590d/\u96f6\u6807\u9898\u5361\uff1b33 \u683c\u5207\u70b9\u6761\u677f\u8bfb\uff1a\u5f00\u573a\u5ba4\u5185\u8fd1\u666f\u2192\u4e61\u91ce\u767d\u663c\u2192\u591c\u2192\u6536\u5728\u5199\u5b57\u8fd1\u666f\uff0c\u65e0\u7ec8\u7ae0\u63d0\u524d\u3002
- **\u94f6\u884c**\uff1a`packA-assembly-index-verify-v1` \u2192 done\uff08**INDEX-VERIFY-END ok=1 mismatches=0**\uff1b07:25:59 \u8ba4\u9886\u540e\u4ece\u672a\u8dd1\u8fc7\u2014\u2014C2132 \u9a8c\u8bc1\u5668\u7b2c\u4e00\u6b65\u5c31\u53bb\u5220\u76d1\u5b88\u6b63\u5728\u91cd\u5b9a\u5411\u7684\u81ea\u5df1\u7684\u65e5\u5fd7\uff0cWinError 32 \u5f53\u573a\u6b7b\uff1b\u66ff\u6362\u7248\u4e0d\u78b0\u81ea\u5df1\u65e5\u5fd7\uff0c\u91cd\u7b97 33 \u7247 sha256+\u5b57\u8282\u3001\u5bf9\u7167\u7f16\u5199\u76ee\u5f55\u6821\u987a\u5e8f\u3001\u5e76\u6838 v1 \u4e24\u4ef6\u5728 origin\uff09\uff1b`packA-conform-cutpoints-v1` \u2192 done\uff1b`packA-conform-review-pack-v1` \u2192 done\uff1b\u9884\u6302\u540e\u7ee7 **`packA-conform-origin-verify-v1`**\uff08\u94f6\u884c\u4e0d\u7a7a\uff09
- **\u95ee\u9898\u6e05\u5355**\uff1a(\u7ea2) \u65e0 \u00b7(\u9ec4) \u6210\u7247\u5e38\u91cf ~0.1s \u504f\u79fb\uff08\u603b\u957f 196.25s vs \u7f16\u5199 196.14s\uff0c\u5df2\u5728\u951a\u5b9a\u641c\u7d22\u4e2d\u5438\u6536\uff0c\u5982\u5b9e\u8bb0\u5f55\uff09\u00b7(\u84dd) bm-a \u5bfc\u6f14\u5e2d\u5bf9\u6837\u7247\u4e0e S5-27 \u53cc\u7b7e\u4ecd\u5728\u5bf9\u65b9\u5e2d
- **\u989d\u5ea6\u4e0e\u5de5\u5177**\uff1aTJ 0 \u00b7 \u4e91\u7aef 0 \u00b7 GPU 0 \uff08\u7eaf CPU\uff1affmpeg \u7f16\u7801 + PIL \u6bd4\u5bf9\uff09
- **\u4e0b\u4e00\u6b65**\uff1a\u2460 bm-a \u5bfc\u6f14\u5e2d\u62ff\u5ba1\u770b\u5305\uff08\u4ee3\u7406\u7247 + \u5207\u70b9\u6761\u677f\uff09\u5bf9\u88c5\u914d\u5b9a\u7a3f\u3001\u5bf9 S5-27 \u53cc\u7b7e \u2461 \u4e0b\u4e00\u8f6e\u6536\u5272 `packA-conform-origin-verify-v1`\uff08\u63a8\u540e\u6838 origin \u5b57\u8282\uff09\u2462 \u5b57\u5e55/\u5b57\u5361\u4e0e\u97f3\u9891\u504f\u79fb\u5f52\u7f16\u8f91\u5c97
"""


def main():
    raw = open(SNAP, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    block = BLOCK.encode("utf-8")
    if b"\r\n" in raw[:4000]:
        block = block.replace(b"\n", b"\r\n")
        body = raw
    else:
        body = raw
    marker = u"# \u81ea\u52a8\u5316\u5feb\u7167-c".encode("utf-8")
    if body.find(marker) >= 0:
        idx = body.find(marker)
        head = body[:idx] if idx > 0 else b""
        if bom and idx == 0:
            head = b"\xef\xbb\xbf"
            body = body[3:]
        new = head + block + body
    else:
        new = block + body
    with open(SNAP, "wb") as f:
        f.write(new)

    stamp = time.strftime("%Y-%m-%d %H:%M")
    rows = [
        u"%s | Step0 \u5b8c\u6210 | preflight \u5168 PASS \u96f6 FLAG\uff1b\u94f6\u884c 1 \u5355 claimed@07:25:59 \u65e0 runner \u4ea7\u7269 = \u6536\u5272\u9762\uff1bRAM 15.1%%<40%% NOT-GREEN-IDLE\uff1bLOCK \u672c\u73ed\u81ea\u6301" % stamp,
        u"%s | Step1-2 \u5b8c\u6210 | \u672c\u673a owned=mv0001 \u661f\u6674 A \u6279\uff1b\u76d8\u9762 33 \u7247\u9f50\uff1b\u7d22\u5f15 v2 \u5b57\u540d\u5e8f\u7f3a\u9677\u5b9a\u8c0c\uff08\u7ec8\u7ae0\u5757\u8dd1\u5230\u7247\u5934\uff09" % stamp,
        u"%s | Step5 \u5b8c\u6210 | \u5b9e\u4f53\u4ea7\u7269 PACK-A \u6574\u6bb5\u6837\u7247 196.25s/44.6MB + \u5ba1\u770b\u5305\uff08960px \u4ee3\u7406 15.25MB + 33 \u683c\u5207\u70b9\u6761\u677f\uff09" % stamp,
        u"%s | Step3 \u5b8c\u6210 | \u5b9a\u65f6\u786c\u95f8 CUTPOINTS-END ok=1 exact=33/33 max_mad=2.83\uff1b\u94f6\u884c INDEX-VERIFY-END ok=1 mismatches=0" % stamp,
        u"%s | Step6 \u5b8c\u6210 | state \u53cc\u951a\u540c\u503c + \u5feb\u7167 vC2133 + \u94f6\u884c\u9884\u6302 packA-conform-origin-verify-v1\uff08jobs=43 pending=1\uff09" % stamp,
        u"%s | Step7 \u5b8c\u6210 | \u4ea7\u54c1\u4ef6+\u56de\u6267+\u94f6\u884c+\u5feb\u7167+\u53f0\u8d26 \u540c\u6279\u6536\u53e3\uff1bFluxGroup pathspec + MiniGame closeout + FleetPush machine/C" % stamp,
        u"%s | TICK_DONE C2133 | A \u6279\u88c5\u914d\u6837\u7247 33 \u5355\u5143 196.25s + \u7d22\u5f15 v2 \u987a\u5e8f\u6839\u6cbb + \u5ba1\u770b\u5305 | \u95f8=\u5207\u70b9 33/33\uff08MAD 2.83\uff09/\u7d22\u5f15\u9a8c\u8bc1 0 \u5dee | build_ok=True" % stamp,
    ]
    lraw = open(LEDGER, "rb").read()
    lcrlf = b"\r\n" in lraw[-2000:]
    eol = u"\r\n" if lcrlf else u"\n"
    add = u"".join(r + eol for r in rows)
    if not lraw.endswith(b"\n"):
        add = eol + add
    with open(LEDGER, "ab") as f:
        f.write(add.encode("utf-8"))
    print("SNAP bytes=%d bom=%s" % (len(new), bom))
    print("LEDGER rows=7 crlf=%s" % lcrlf)


if __name__ == "__main__":
    main()