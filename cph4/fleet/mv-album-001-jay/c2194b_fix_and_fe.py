"""C2194b: correct the burn queue-order note (the KN18 job runs first, not behind)
and file one fleet-experience entry.
"""

import io
import json
import os
import sys
import time

MG = r"K:\Fluxgroup\MiniGame"
HQ = r"K:\Fluxgroup\FluxGroup"
STATE = os.path.join(MG, "state-c.json")
FE = os.path.join(MG, "Design", "configs", "GLOBAL", "\u6863\u6848",
                  "\u673a\u961f\u7ecf\u9a8c\u6c47\u62a5\u961f\u5217.md")
FLAGS = [
    os.path.join(MG, ".codely-cli", "engine-tick", "wave-harvest-pending.json"),
    os.path.join(HQ, ".codely-cli", "engine-tick", "wave-harvest-pending.json"),
]
PROMPT_ID = "d0fcc4ca-fb80-4f68-97fa-f829b950585c"

FE_ENTRY = u"""### FE-20261024-bm-c-c2194 — \u5f15\u64ce\u6b7b\u4e0d\u7b49\u4e8e\u71c3\u6bd9\u6b7b\uff1a\u9a71\u52a8\u8fdb\u7a0b\u6b7b\u4e86\u6e32\u67d3\u4ecd\u5728\u670d\u52a1\u5668\u4fa7\u8dd1\u5b8c\uff0c\u6536\u83b7\u4e00\u5f8b\u8ba4\u76d8
- \u6765\u6e90: bm-c C2194\uff08KN18 768P \u71c3\u6bd9\u6536\u83b7\uff09
- \u7c7b\u578b: \u57fa\u7840\u8bbe\u65bd / \u5de5\u5177\u5931\u6548\u65cf
- \u4f18\u5148\u7ea7: P1
- \u5185\u5bb9: \u4e0a\u4e00\u8f6e\u7528 pythonw \u628a i2v \u94fe\u8def\u6d3e\u79bb\u4f1a\u8bdd\u70b9\u706b\uff0c\u4f46\u8be5\u8fdb\u7a0b\u4ecd\u662f CLI \u4f1a\u8bdd\u7684\u5b50\u8fdb\u7a0b\uff0c\u4f1a\u8bdd\u7ed3\u675f\u65f6\u8fde\u5e26\u88ab\u6740\uff08Job Object\uff09\u2014\u2014\u65e5\u5fd7\u56e0\u6b64\u5728 1260s \u5904\u65ad\u5c3e\u3001\u76ee\u6807\u76ee\u5f55\u65e0\u6587\u4ef6\uff0c\u770b\u4e0a\u53bb\u50cf\u201c\u71c3\u6bd9\u5931\u8d25\u201d\uff1b\u5b9e\u60c5\u662f ComfyUI \u670d\u52a1\u5668\uff08\u72ec\u7acb PID\uff09\u628a\u8fd9\u4e2a job \u8dd1\u5b8c\u4e86\uff0c\u6210\u54c1\u843d\u5728 D:\\ComfyUI\\ComfyUI\\output\\ \u4e0e /history/<prompt_id>\u3002\u5224\u636e\u56e0\u6b64\u8981\u4e09\u9762\uff1a\u76ee\u6807\u76ee\u5f55\u3001ComfyUI output\u3001/history\u3002\u6536\u83b7\u6539\u4e3a adopt-by-disk\uff08c2194_kn18_watch_harvest.py\uff09\u540e\u4e0d\u518d\u4f9d\u8d56\u9a71\u52a8\u8fdb\u7a0b\u5b58\u6d3b\u3002\u540c\u65f6\u4fee\u4e00\u4e2a\u771f\u5b9e\u9677\u9631\uff1a\u5931\u8d25\u4ef6\u88ab\u9a71\u52a8\u5668\u5df2\u63d0\u4ea4\u5230\u751f\u4ea7\u76ee\u5f55\u540e\uff0c\u4e0b\u4e00\u6b21\u71c3\u4f1a\u56e0 SKIP \u5224\u636e\uff08\u6587\u4ef6\u5b58\u5728\u4e14 >100KB\uff09\u76f4\u63a5\u8df3\u8fc7\u2014\u2014\u91cd\u71c3\u524d\u5fc5\u5148\u5c06\u7ea2\u5757\u79fb\u5165 clips-red/ \u5b58\u8bc1\u3002
- \u8bc1\u636e: cph4/fleet/mv-album-001-jay/c2194_kn18_watch_harvest.py + media/mv-album-001-jay/logs/kn18-prod-c2194.json\uff08p99 26/79/69 vs \u9608\u503c 47\uff09+ clips-red/KN_G6-KN18-c2192-768p-red.mp4 + kn_film_gate.py\uff08\u5e74\u5e95\u95e8\uff1a5737 \u5e27 0 \u590d\u8bfb\u5bf9\uff0cfilm v2 PASS\uff09
- \u7528\u9014: \u4efb\u4f55 GPU \u957f\u6279\u6536\u83b7\u524d\u5148\u770b\u4e09\u9762\uff1b\u4efb\u4f55\u91cd\u71c3\u5148\u6e05\u76ee\u6807\u76ee\u5f55\u3002
- \u72b6\u6001: \u5f85 A \u673a\u5f52\u5e76
"""


def main():
    # 1) correct the queue-order note in both flags
    for f in FLAGS:
        with io.open(f, "r", encoding="ascii") as fh:
            d = json.load(fh)
        d["what"] = ("KN18 768P re-burn with prompt v5.0-C2194-sparse-closeup, submitted as ComfyUI prompt "
                     + PROMPT_ID + " at 17:53:30 (seed 102675 carried over, so the wording is the only variable). "
                     "It is rendering now; one queued 480P animatic sits behind it. Expect the render ~18:15-18:20.")
        with io.open(f, "w", encoding="ascii") as fh:
            json.dump(d, fh, indent=1, ensure_ascii=True)
    print("flags corrected:", len(FLAGS))

    # 2) state next_round ETA wording
    with io.open(STATE, "r", encoding="utf-8") as fh:
        st = json.load(fh)
    st["next_round"] = st["next_round"].replace(
        "submitted 17:53, behind one queued 480P animatic, so expect it ~18:30",
        "submitted 17:53:30 and rendering now with one 480P animatic queued behind it, so expect the render ~18:15-18:20")
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("state ETA corrected")

    # 3) fleet experience entry
    with io.open(FE, "r", encoding="utf-8", newline="") as fh:
        raw = fh.read()
    if "FE-20261024-bm-c-c2194" in raw:
        print("FE entry already present - skipped")
        return 0
    if raw and not raw.endswith("\n"):
        raw += "\r\n" if "\r\n" in raw else "\n"
    eol = "\r\n" if "\r\n" in raw else "\n"
    block = FE_ENTRY.replace("\n", eol)
    with io.open(FE, "w", encoding="utf-8", newline="") as fh:
        fh.write(raw + block)
    print("FE entry appended")
    return 0


if __name__ == "__main__":
    sys.exit(main())