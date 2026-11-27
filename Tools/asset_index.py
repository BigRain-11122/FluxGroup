# -*- coding: utf-8 -*-
"""asset_index.py —— 素材单一索引（SOP §七 BOM）

用法:
  python asset_index.py seed           # 写入当前已定片
  python asset_index.py add --shot X --window "a-b" --file F --take T --verdict V --evidence E
  python asset_index.py list
装配只认这张表：表里没有的素材不许出现在成片里。
"""
import argparse, json, os, sys, datetime

IDX = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv-album-001-jay\ASSET-INDEX.jsonl"

SEED = [
    dict(shot="R1_E01a_carver", window="187.26-190.00", src=r"D:\FleetWorker\review\r1\takes\R1_t3_s9303.mp4",
         take="t3_s9303", verdict="PASS_480P", evidence="10帧零漂移/咬字2.5次", note="768P 待出"),
    dict(shot="R2_SING3b", window="197.00-199.00", src=r"D:\FleetWorker\review\r234\takes\R2_sing3.mp4",
         take="R2_sing3 前2.0s", verdict="PASS_480P", evidence="咬字3-4次/脸稳", note="避开中段麦穗碗；768P 待出"),
    dict(shot="R3_E01c_first_line", window="191.60-193.12", src=r"D:\FleetWorker\review\finals\R3c_768_s9412.mp4",
         take="R3c_768_s9412", verdict="PASS_768P", evidence="干净首帧/无景别跳变/刻痕稳定", note="入选"),
    dict(shot="R4_E02a_dig", window="193.12-197.00", src=r"D:\FleetWorker\review\finals\R4a_768.mp4",
         take="R4a_768", verdict="PASS_768P", evidence="五指清晰/刻痕稳定", note="动作=按压+剔挖"),
    dict(shot="R5_S8S9", window="40.22-44.00", src="crop=814:458:530:155 (from v5.13)",
         take="reframe", verdict="PASS", evidence="41/42.5/43.5 无倒影", note="换构图，不重烧"),
]


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def load():
    if not os.path.exists(IDX):
        return []
    with open(IDX, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def save(rows):
    with open(IDX, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("seed")
    p = sub.add_parser("add")
    for k in ("shot", "window", "file", "take", "verdict", "evidence"):
        p.add_argument("--" + k, required=True)
    sub.add_parser("list")
    a = ap.parse_args()

    rows = load()
    if a.cmd == "seed":
        have = {r["shot"] for r in rows}
        n = 0
        for s in SEED:
            if s["shot"] not in have:
                rows.append({**s, "ts": now()}); n += 1
        save(rows)
        print("SEEDED", n, "rows; total", len(rows))
    elif a.cmd == "add":
        rows.append(dict(shot=a.shot, window=a.window, src=a.file, take=a.take,
                         verdict=a.verdict, evidence=a.evidence, ts=now()))
        save(rows)
        print("ADDED", a.shot)
    else:
        for r in rows:
            print("%-22s %-14s %-10s %s" % (r["shot"], r["window"], r["verdict"], os.path.basename(str(r["src"]))))


if __name__ == "__main__":
    main()