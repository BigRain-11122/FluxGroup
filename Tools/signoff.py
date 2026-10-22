# -*- coding: utf-8 -*-
"""signoff.py —— 专家签核台账写入器（GATE-SPEC-v1 §三）

用法：
    python Tools/signoff.py --version v5.19 --station S5 --seat E --verdict PASS \
        --criteria '{"offplan":3,"islands":0,"cuts_checked":72}' \
        --evidence release_gate.txt

规则：缺字段/verdict 非法/证据文件不存在 → 拒绝写入。
"""
import argparse, json, os, sys, datetime

LEDGER = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv-album-001-jay\QA-SIGNOFF-LEDGER.jsonl"
STATIONS = {"N0", "N1", "N2", "N3", "N4", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "P1", "P2", "P3"}
SEATS = {"D", "S", "C", "E", "G", "A", "T", "L", "P", "R"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--station", required=True)
    ap.add_argument("--seat", required=True)
    ap.add_argument("--verdict", required=True, choices=["PASS", "FAIL", "CONDITIONAL"])
    ap.add_argument("--criteria", required=True, help="JSON 对象，写实测数字")
    ap.add_argument("--evidence", nargs="+", required=True, help="证据文件/目录路径")
    ap.add_argument("--note", required=True, help="必须写自己看到的数字")
    a = ap.parse_args()

    if a.station not in STATIONS:
        sys.exit("station 非法: %s（合法: %s）" % (a.station, sorted(STATIONS)))
    if a.seat not in SEATS:
        sys.exit("seat 非法: %s（合法: %s）" % (a.seat, sorted(SEATS)))
    try:
        crit = json.loads(a.criteria)
        assert isinstance(crit, dict) and crit, "criteria 必须是非空 JSON 对象"
    except Exception as e:
        sys.exit("criteria 解析失败: %s" % e)

    missing = [p for p in a.evidence if not os.path.exists(p)]
    if missing:
        sys.exit("证据不存在，拒绝签核: %s" % missing)

    if a.verdict == "CONDITIONAL" and "条件" not in a.note:
        sys.exit("CONDITIONAL 必须在 note 写明『条件』")
    if any(x not in a.note for x in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
        sys.exit("note 必须写出自己实测到的数字（复述他人数字不算独立审核）")

    rec = {
        "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "version": a.version, "station": a.station, "seat": a.seat,
        "verdict": a.verdict, "criteria": crit,
        "evidence": a.evidence, "note": a.note,
    }
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("SIGNED:", json.dumps(rec, ensure_ascii=False)[:200])


if __name__ == "__main__":
    main()