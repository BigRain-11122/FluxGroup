# C2092 part2: verify bank surgery result + arm flag + progress append (script 1 died at stale count assert AFTER bank write)
import json
import os
import io
import datetime

FG = r"K:\Fluxgroup\FluxGroup"
BANK = os.path.join(FG, "cph4", "fleet", "work-bank", "bm-c-gpu-bank.json")
PROG = os.path.join(FG, "cph4", "fleet", "mv-album-001-jay", "xq-PACKA-REDO-R1-PROGRESS-20261019.md")
FLAG = r"K:\Fluxgroup\MiniGame\.codely-cli\engine-tick\wave-harvest-pending.json"

# 0. verify bank current state (write from part 1 already landed)
rt = json.loads(open(BANK, "rb").read().decode("utf-8-sig"))
jobs2 = {x["id"]: x for x in rt["jobs"]}
assert jobs2["xq-redo-i2v3"]["status"] == "done", jobs2["xq-redo-i2v3"]["status"]
assert jobs2["xq-redo-i2v3"].get("done_ts")
assert jobs2["packA-qc-strips-v2"]["status"] == "claimed", jobs2["packA-qc-strips-v2"]["status"]
assert jobs2["packA-qc-strips-v2"].get("claimed_ts")
print("BANK VERIFY OK jobs=%d i2v3=done stripsv2=claimed" % len(rt["jobs"]))

now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# 1. re-arm wave-harvest flag for strips-v2
flag = {
 "batch": "c2092-packA-qc-strips-v2",
 "project": "mv-album-001-jay/packA-qc-strips-v2",
 "fired_at": now,
 "verdict_paths": [
  "media/mv-album-001-jay/log-qcstripsv2.out.txt",
  "cph4/fleet/mv-album-001-jay/xq-PACKA-QC-STRIPS-v2-c2091.jpg",
  "cph4/fleet/work-bank/bm-c-gpu-bank.json"
 ],
 "note": "bank job packA-qc-strips-v2 (in-round claimed+fired by tick-C2092, runner packA_qc_strips_v2_c2091.py pythonw detached, i2v3 harvest PASS 4/4 adopted same round). Harvest = next round: PASS gate = STRIPS-V2 DONE: 31 clips sentinel in log-qcstripsv2.out tail + board xq-PACKA-QC-STRIPS-v2-c2091.jpg >=1000000B + zero err-exit. Then per-unit sec-4 adjudication of 3 i2v3 units on v2 board via SPLIT-READ (crop 3 REDO-R1 rows to small strip, <=12 units per multimodal call - full 31-unit board read times out per 10-18 lesson): F5-33a zero-pseudo-text + self-stop held / S4-24 three-frame subject hold + zero readable label / S3-19 decode-integrity already GREEN + dusk sky discernible + single arm single pointing finger. Spot-confirm 3 direct3 rows (S2-14/S3-20/S4-22 adjudicated PASS C2087) present on board. Then director re-review on v2 board -> assembly unlock face (X2670 sec-6: PACK-A 31/31 green + S5-27 return from bm-a director seat). Board commit decision: GIT-BLOAT-GATE check first (compress if >2MB soft line). Delete this file after harvest adoption (FE-20260929-C-7)."
}
with io.open(FLAG, "w", encoding="ascii", errors="replace", newline="\n") as f:
    json.dump(flag, f, indent=1)
    f.write("\n")
chk = json.loads(io.open(FLAG, "r", encoding="ascii").read())
assert chk["batch"] == "c2092-packA-qc-strips-v2"
print("FLAG ARMED c2092-packA-qc-strips-v2")

# 2. progress append (UTF-8, EOL-preserving; C2074 law: any \n ending = no pad)
if os.path.exists(PROG + ".c2092lock"):
    print("PROGRESS ALREADY APPENDED (lock file present)")
else:
    praw = open(PROG, "rb").read()
    ptext = praw.decode("utf-8-sig")
    peol = "\r\n" if "\r\n" in ptext else "\n"
    if "C2092" in ptext and "i2v3 \u6536\u5272 PASS 4/4" in ptext:
        print("PROGRESS ALREADY APPENDED (content check)")
    else:
        if not ptext.endswith("\n"):
            ptext += peol
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        section = (
            "## \u6279 C2092 i2v3 \u6536\u5272\u7ffb\u9762 + p17 \u672c\u7a97\u8ba4\u9886\u70b9\u706b\uff0821:1x\uff09\n\n"
            "- **i2v3 \u6536\u5272 PASS 4/4**\uff1aALBUM LANE DONE ok=3 fail=0 + 3 mp4\uff08F5-33a 1,287,253B / S4-24 1,378,672B / S3-19 884,185B \u5168 \u2265100KB\uff09+ progress-bmcpackAredo.jsonl ok\u00d73 + ffprobe -count_frames \u89e3\u7801\u6d01\u51c0\uff08S3-19 277f@1344x768 exit0 \u00a73.3 \u5fc5\u67e5\u7eff\uff1bF5-33a 107f / S4-24 141f \u540c\u6d01\uff09\u2192 \u94f6\u884c p16 \u7ffb done\uff1bredo-r1 \u516d\u7247\u76d8\u9762\u9f50\uff08direct3 \u4e09\u7247+i2v3 \u4e09\u7247\uff09\n"
            "- **p17 packA-qc-strips-v2 \u672c\u7a97\u8ba4\u9886\u70b9\u706b**\uff08\u96f6\u95f2\u7f6e\u7a97\uff1a\u6ce2\u6bd5 21:05:03 \u2192 \u8ba4\u9886 21:1x <10min SLA \u5185\uff1bguard \u515d\u5e95\u4e0d\u53d7\u5f71\u54cd\uff09\uff1arunner=packA_qc_strips_v2_c2091.py pythonw \u8131\u79bb\u5f0f\uff1b\u6536\u5272\u65d7\u5df2\u91cd\u6302 c2092-packA-qc-strips-v2\uff08\u6302\u65d7=\u70b9\u706b\u6b65\u9aa4\u7ec4\u6210\u90e8\u5206\uff0cC2089 \u5224\u4f8b\u5f8b\uff09\n"
            "- **\u4e0b\u7a97\u6536\u5272**\uff1aSTRIPS-V2 DONE 31 clips \u54e8\u5175 + \u677f \u22651,000,000B + \u96f6 err \u2192 \u62c6\u677f\u5224\u8bfb 3 i2v3 \u955c sec-4 \u95f8\uff08F5-33a \u4f2a\u5b57+\u81ea\u505c / S4-24 \u4e09\u5e27\u4e3b\u4f53+\u6807\u7b7e\u53ef\u8bfb / S3-19 \u5929\u7a7a+\u5355\u81c2\u00b7\u89e3\u7801\u5df2\u7eff\uff09\u2192 \u5bfc\u6f14\u5e2d\u590d\u5ba1 v2 \u677f \u2192 \u88c5\u914d\u89e3\u9501\u4f9d\u636e\uff08X2670 \u00a7\u516d\uff1aPACK-A 31/31 \u5168\u7eff+S5-27 \u56de\u4f4d[bm-a \u5bfc\u6f14\u5e2d\u88c1\u5b9a]\uff09\u2192 \u5220\u65d7\uff1b\u677f\u5165\u4ed3\u524d\u8fc7 GIT-BLOAT-GATE\uff08>2MB \u5148\u538b\u7f29\uff09\n\n"
            "\u2014\u2014 bm-c \u6267\u884c\u5e2d\u8bb0\uff1aC2092\uff0c" + stamp + "\uff08i2v3 \u6536\u5272+p17 \u70b9\u706b+\u6302\u65d7\u6bd5\uff09\n"
        )
        ptext += section.replace("\n", peol) if peol == "\r\n" else section
        with open(PROG, "wb") as f:
            f.write(ptext.encode("utf-8-sig" if praw[0:3] == b"\xef\xbb\xbf" else "utf-8"))
        back = open(PROG, "rb").read().decode("utf-8-sig")
        assert "C2092" in back and "i2v3 \u6536\u5272 PASS 4/4" in back
        io.open(PROG + ".c2092lock", "w").write("appended")
        print("PROGRESS APPENDED C2092 section OK")
