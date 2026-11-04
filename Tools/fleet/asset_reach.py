#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_reach.py - 资产可达性账：把"账面 651 条"和"现在真能拿到几条"分开报。

为什么（2026-11-04 主控职责面 mc-asset）：
  vault 台账 651 条全部指向 /Volumes/移动硬盘/FluxAssets，而该卷当前未挂载。任何
  "资产已归集/已备份"的说法都必须先过这一关：**账面数量不等于可达数量**。
  把两者混在一句话里，就等于用不可达的账目冒充已完成的资产。

判据（可核验）：
  * 每条按路径前缀取卷（/Volumes/<name>/…），卷不在 = UNMOUNTED；
  * 卷在但文件不在 = MISSING；
  * 卷在且文件在 = REACHABLE（再抽样核 sha256 前 8 位，抽样失败记 SHA-MISMATCH）。
产出：state/asset-reachability.json + ASSET-REACH.md
Exit: 0 有可达且无缺失；2 台账 >0 而可达 0（账面活着盘是死的）
"""
import argparse
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
IDX = os.path.join(FLEET, "vault", "index.jsonl")
OUT = os.path.join(FLEET, "state", "asset-reachability.json")
MD = os.path.join(FLEET, "ASSET-REACH.md")
SAMPLE = 8


def sha8(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:8]


def volume_of(path):
    parts = str(path).replace("\\", "/").split("/")
    if len(parts) > 2 and parts[1] == "Volumes":
        return "/Volumes/" + parts[2]
    return ""


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    rows = []
    if os.path.exists(IDX):
        for ln in open(IDX, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            try:
                rows.append(json.loads(ln))
            except Exception:
                pass

    vols = {}
    reach, missing, unmounted = [], [], {}
    for r in rows:
        p = r.get("path") or ""
        v = volume_of(p)
        if v:
            if v not in vols:
                vols[v] = os.path.isdir(v) and (os.path.ismount(v) or os.path.isdir(v))
            if not vols[v]:
                unmounted.setdefault(v, 0)
                unmounted[v] += 1
                continue
        if os.path.exists(p):
            reach.append(r)
        else:
            missing.append(r.get("path"))

    sha_bad = []
    for r in random.sample(reach, min(SAMPLE, len(reach))) if reach else []:
        try:
            if sha8(r["path"]) != (r.get("sha256") or "")[:8]:
                sha_bad.append(r["path"])
        except Exception:
            sha_bad.append(r["path"])

    state = {"ts": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
             "ledger_total": len(rows), "reachable": len(reach),
             "missing": len(missing), "missing_sample": missing[:10],
             "unmounted_volumes": unmounted, "sha_checked": min(SAMPLE, len(reach)),
             "sha_mismatch": sha_bad,
             "verdict": ("UNREACHABLE" if rows and not reach else
                         ("PARTIAL" if missing or unmounted else "OK"))}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(state, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    lines = ["# 资产可达性（%s）" % state["ts"][:16], "",
             "台账 %d 条 · **可达 %d 条** · 缺失 %d 条 · 判定 %s"
             % (len(rows), len(reach), len(missing), state["verdict"]), ""]
    for v, n in unmounted.items():
        lines.append("- 卷未挂载：%s（%d 条账面在此）" % (v, n))
    if sha_bad:
        lines.append("- sha 抽样不符 %d 件：%s" % (len(sha_bad), "、".join(sha_bad[:3])))
    if state["verdict"] == "UNREACHABLE":
        lines.append("- 结论：**任何「资产已归集/已备份」的报告都不成立**——盘不在，账不作数。"
                     "挂盘后重跑本工具即恢复。")
    open(MD, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    if a.json:
        print(json.dumps(state, ensure_ascii=False))
    else:
        print("[asset-reach] 台账 %d 可达 %d 缺失 %d 判定 %s%s"
              % (len(rows), len(reach), len(missing), state["verdict"],
                 (" 未挂载:" + ",".join(unmounted)) if unmounted else ""))
    return 2 if (rows and not reach) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))