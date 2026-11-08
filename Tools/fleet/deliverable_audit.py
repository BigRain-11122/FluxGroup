# -*- coding: utf-8 -*-
"""审「DONE 卡的交产物到底在不在」——把「本机没有」和「真丢了」分开。

为什么需要它：lib_consolidate --check 报过「227 张 DONE 卡的交产物不在盘」，
但那个判据读的是本机 PRODUCTION-QUEUE.jsonl（分叉的陈旧副本），
而且只看 os.path.exists —— 交付物在 origin 里有、只是本机没拉，也会被判缺。
这正是 vault 台账同一类假警报（651 条「缺失」里 640 条其实可重建）。

判据三态：
  on_disk      本机磁盘上就有
  in_origin    origin/main 里有该文件（本机没拉，git checkout 即可）
  absent       两边都没有 —— 这才是真缺口

用法：
  python Tools/fleet/deliverable_audit.py
  python Tools/fleet/deliverable_audit.py --out cph4/fleet/queue-receipts/deliverables-20261108.json
Exit: 0 无真缺口；1 有真缺口（数量写进回执）
"""
import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RECEIPTS = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")


def origin_queue():
    r = subprocess.run(["git", "-C", ROOT, "show", "origin/main:cph4/fleet/PRODUCTION-QUEUE.jsonl"],
                       capture_output=True, timeout=60)
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", "replace")


def in_origin(paths):
    """批量判哪些路径在 origin/main 里（一次 git cat-file --batch-check）。"""
    have = set()
    if not paths:
        return have
    # 注意：batch-check 收的是「对象名」，不是树里的路径 —— 必须写成 origin/main:<path>，
    # 直接喂路径会全部回 missing（首版即此 bug）。
    inp = "".join("origin/main:%s\n" % p for p in paths).encode("utf-8")
    try:
        r = subprocess.run(["git", "-C", ROOT, "cat-file", "--batch-check"],
                           input=inp, capture_output=True, timeout=120)
        # batch-check 输出是「<path> <type> <size>」或「<path> missing」三段/两段；
        # 只按最后一段切会把类型当大小，导致一个都匹配不上（首版即此 bug，in_origin 恒 0）。
        for line in r.stdout.decode("utf-8", "replace").splitlines():
            if line.endswith(" missing"):
                continue
            parts = line.rsplit(" ", 2)
            if len(parts) == 3 and parts[0].startswith("origin/main:"):
                have.add(parts[0][len("origin/main:"):])
    except Exception:
        pass
    return have


def ignored(paths):
    """哪些路径被 .gitignore 覆盖——运行时产物本来就不进 git，不能算「缺交付」。"""
    out = set()
    if not paths:
        return out
    try:
        r = subprocess.run(["git", "-C", ROOT, "check-ignore", "--stdin", "--no-index"],
                           input="".join("%s\n" % p for p in paths).encode("utf-8"),
                           capture_output=True, timeout=60)
        for line in r.stdout.decode("utf-8", "replace").splitlines():
            if line.strip():
                out.add(line.strip())
    except Exception:
        pass
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(RECEIPTS, "deliverables-%s.json"
                                                 % time.strftime("%Y%m%d")))
    a = ap.parse_args(argv)

    blob = origin_queue()
    if blob is None:
        print("[deliv] 读不到 origin/main 的队列（先 git fetch）")
        return 2

    rows, seen = [], 0
    for line in blob.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if str(r.get("state") or "") != "DONE":
            continue
        dp = (r.get("deliverable") or "").strip()
        if not dp:
            continue
        seen += 1
        rel = dp.replace("\\", "/")
        if rel.startswith("/") or (len(rel) > 2 and rel[1] == ":"):
            full = dp            # 绝对路径：别的机器的盘，本机判不了
            rel = ""
        else:
            full = os.path.join(ROOT, dp.replace("/", os.sep))
        rows.append({"id": r.get("id"), "line": r.get("line"), "owner": r.get("owner"),
                     "deliverable": dp, "rel": rel, "full": full})

    need_origin = [x["rel"] for x in rows if x["rel"] and not os.path.exists(x["full"])]
    have = in_origin(need_origin)
    ign = ignored(need_origin)

    on_disk, in_org, absent, offnode, runtime = [], [], [], [], []
    for x in rows:
        if not x["rel"]:
            offnode.append(x)
        elif os.path.exists(x["full"]):
            on_disk.append(x)
        elif x["rel"] in have:
            in_org.append(x)
        elif x["rel"] in ign:
            runtime.append(x)
        else:
            absent.append(x)

    by_line_absent = Counter((x["line"] or "?") for x in absent)
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": "origin/main:cph4/fleet/PRODUCTION-QUEUE.jsonl",
        "done_with_deliverable": seen,
        "on_disk": len(on_disk),
        "in_origin_only": len(in_org),
        "offnode_absolute": len(offnode),
        "runtime_ignored": len(runtime),
        "absent": len(absent),
        "absent_by_line": dict(by_line_absent.most_common()),
        "absent_sample": [{"id": x["id"], "line": x["line"], "deliverable": x["deliverable"]}
                          for x in absent[:15]],
        "verdict": "PASS" if not absent else "FAIL",
        "note": ("runtime_ignored=路径被 .gitignore 覆盖（state/canary/media 之类运行时产物），"
                 "本来就不该进 git，不算缺交付；"
                 "in_origin_only=交付物在 origin 里、本机没拉，git checkout 即得，不算缺口；"
                 "offnode_absolute=交付物写的是别的机器的绝对盘符，本机判不了，也不算缺口。"
                 "只有 absent 才是真缺口。"),
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(rec, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("[deliv] DONE 有交付物 %d | 在盘 %d | 仅 origin %d | 运行时(ignore) %d | 他机绝对路径 %d | 真缺 %d"
          % (len(rows), len(on_disk), len(in_org), len(runtime), len(offnode), len(absent)))
    if absent:
        print("  真缺口按线：", dict(by_line_absent.most_common(5)))
        for x in absent[:5]:
            print("   ! ", x["line"], x["id"], "->", x["deliverable"][:70])
    print("  ->", os.path.relpath(a.out, ROOT))
    return 0 if not absent else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))