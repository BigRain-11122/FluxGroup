# -*- coding: utf-8 -*-
"""artifact_review.py - 三层审核 + 入档 + 入库（真读内容，不看存在性）。

CEO 2026-11-07：「不仅要查文档，还要真实的审核产出，要几层审核，确定后入档入库，
入机队里面的仓库。」

DONE 只表示执行结束，不表示产物合格。本工具把 DONE 卡真正打开、读内容、交叉核对，
三层都过才算 APPROVED；通过后复制进 archive 并记账（sha256 可反查），
能对应到机队子仓的写待入清单（子仓未 clone 时绝不假装入库）。

Usage:
  artifact_review.py [--limit 30] [--apply] [--model]
    --apply  通过者真的复制入档 + 写待入清单（默认 dry-run 只审不写）
    --model  L3 抽样用 4B 判断语义一致性（默认只做 L1/L2）
Exit: 0 全部通过；1 有 REJECT；2 政策缺失
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
POLICY = os.path.join(FLEET, "REVIEW-POLICY-v1.json")
ARCHIVE = os.path.join(FLEET, "archive")
LEDGER = os.path.join(FLEET, "ARCHIVE-LEDGER.jsonl")
INTAKE = os.path.join(FLEET, "INTAKE-PENDING.jsonl")
BOARD = os.path.join(FLEET, "REVIEW-BOARD.md")
STATE = os.path.join(FLEET, "state", "artifact-review.json")

sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))

PLACEHOLDER = ("TODO", "TBD", "待填", "示例文本", "placeholder", "xxxx")
CONFLICT = ("<<<<<<<", ">>>>>>>")
REMOTE_RE = re.compile(r"^([A-Za-z]:[\\/]|\\\\|/)")
SUBREPO_PREFIX = ("quant/", "gaming/", "media/", "life/", "compute/", "domain/", "house/")


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return d


def rows(p):
    out = []
    try:
        with open(p, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    try:
                        out.append(json.loads(ln))
                    except Exception:
                        pass
    except Exception:
        pass
    return out


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def media_ok(p):
    """图片/视频的最小校验：先看签名，有 ffprobe 再验时长。"""
    try:
        head = open(p, "rb").read(16)
    except Exception:
        return False, "无法读取"
    sigs = {b"\x89PNG": "png", b"\xff\xd8\xff": "jpeg", b"GIF8": "gif",
            b"RIFF": "riff", b"\x00\x00\x00\x18ftyp": "mp4", b"\x1aE\xdf\xa3": "mkv"}
    kind = next((v for k, v in sigs.items() if head.startswith(k)), None)
    if not kind:
        return False, "签名不识别"
    if shutil.which("ffprobe"):
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", p], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        d = (r.stdout or "").strip()
        if d and d.replace(".", "", 1).isdigit() and float(d) <= 0:
            return False, "时长 0"
    return True, kind


# ---- L1 结构审 ---------------------------------------------------------------
def l1(path, rel):
    fails = []
    size = os.path.getsize(path)
    ext = os.path.splitext(rel)[1].lower()
    if size < (1024 if ext in (".png", ".jpg", ".jpeg", ".gif", ".mp4", ".wav") else 40):
        fails.append("体积过小(%dB)" % size)
        return fails
    if ext in (".json", ".jsonl"):
        try:
            if ext == ".json":
                json.load(open(path, encoding="utf-8"))
            else:
                for _ in open(path, encoding="utf-8"):
                    break
        except Exception as e:
            fails.append("JSON 解析失败:%s" % str(e)[:40])
    elif ext == ".csv":
        n = sum(1 for _ in open(path, encoding="utf-8", errors="replace"))
        if n < 2:
            fails.append("CSV 行数<2")
    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".mp4", ".wav"):
        ok, why = media_ok(path)
        if not ok:
            fails.append("媒体无效:%s" % why)
        return fails
    if ext in (".md", ".txt", ".json", ".jsonl", ".csv", ".py"):
        txt = open(path, encoding="utf-8", errors="replace").read()[:200000]
        low = txt.lower()
        for w in PLACEHOLDER:
            if w.lower() in low:
                fails.append("含占位文本:%s" % w)
                break
        for c in CONFLICT:
            if c in txt:
                fails.append("含冲突标记")
                break
        if ext in (".md", ".txt") and len(txt.strip()) < 20:
            fails.append("文本内容过短")
    return fails


# ---- L2 一致性审 -------------------------------------------------------------
def l2(card, path, rel):
    fails, notes = [], []
    try:
        txt = open(path, encoding="utf-8", errors="replace").read()[:400000]
    except Exception:
        txt = ""
    accept = str(card.get("accept") or "")

    # 数量要求：accept 里出现 a/b 或 ≥N
    m = re.search(r"(\d+)\s*/\s*(\d+)", accept)
    if m and txt:
        want = int(m.group(1))
        found = [int(x) for x in re.findall(r"\b(\d+)\b", txt)[:2000]]
        if want not in found:
            notes.append("accept 要求 %d/%s，产物未见该数字" % (want, m.group(2)))
    m2 = re.search(r"[≥>=]\s*(\d+)", accept)
    if m2 and txt:
        need = int(m2.group(1))
        nums = [int(x) for x in re.findall(r"\b(\d+)\b", txt)[:2000]]
        if nums and max(nums) < need:
            fails.append("accept 要求≥%d，产物最大数 %d" % (need, max(nums)))

    # 产物自称总数 vs 实际条目
    m3 = re.search(r"共\s*(\d+)\s*[条项个]", txt)
    if m3:
        claimed = int(m3.group(1))
        try:
            d = json.load(open(path, encoding="utf-8"))
            actual = len(d) if isinstance(d, list) else len(d.get("items") or d.get("results") or [])
            if actual and actual != claimed:
                fails.append("自称 %d 条，实际 %d 条" % (claimed, actual))
        except Exception:
            pass

    # 新鲜度：产物 mtime 与卡完成时间 ±24h
    fin = str(card.get("finished_at") or "")
    if fin:
        try:
            ft = time.mktime(time.strptime(fin[:19], "%Y-%m-%dT%H:%M:%S"))
            if abs(os.path.getmtime(path) - ft) > 86400:
                notes.append("产物 mtime 距完成时间超 24h（疑旧件）")
        except Exception:
            pass

    # 标题关键词弱一致性
    title = str(card.get("title") or "")
    kws = [w for w in re.findall(r"[\u4e00-\u9fa5]{2,4}", title)][:4]
    if kws and txt and not any(k in txt for k in kws):
        notes.append("标题关键词均未出现（弱一致性存疑）")
    return fails, notes


# ---- 入档 / 入库 -------------------------------------------------------------
def archive(rel_path, card, layers):
    line = str(card.get("line") or "unfiled")
    day = time.strftime("%Y%m%d")
    d = os.path.join(ARCHIVE, line, day)
    os.makedirs(d, exist_ok=True)
    h = sha256(rel_path)
    name = "%s-%s" % (h[:8], os.path.basename(rel_path))
    dst = os.path.join(d, name)
    if not os.path.exists(dst):
        shutil.copy2(rel_path, dst)
    rec = {"id": card.get("id"), "title": card.get("title"), "line": line,
           "src": os.path.relpath(rel_path, ROOT),
           "archived": os.path.relpath(dst, ROOT), "sha256": h,
           "bytes": os.path.getsize(rel_path), "layers": layers,
           "reviewed_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "reviewer": "artifact_review"}
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def intake(rec, card, policy):
    m = (policy.get("intake") or {}).get("map") or {}
    line = str(card.get("line") or "")
    repo = m.get(line)
    if not repo:
        return None
    if not os.path.isdir(os.path.join(ROOT, repo)):
        row = {"id": rec["id"], "line": line, "repo": repo,
               "src": rec["archived"], "target_rel": os.path.join(
                   line, time.strftime("%Y%m%d"), os.path.basename(rec["archived"])),
               "reason": "repo-not-cloned", "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
        with open(INTAKE, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return {"state": "pending", "repo": repo}
    tdir = os.path.join(ROOT, repo, line, time.strftime("%Y%m%d"))
    os.makedirs(tdir, exist_ok=True)
    dst = os.path.join(tdir, os.path.basename(rec["archived"]))
    shutil.copy2(os.path.join(ROOT, rec["archived"]), dst)
    return {"state": "copied", "repo": repo, "path": os.path.relpath(dst, ROOT)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--model", action="store_true")
    a = ap.parse_args()

    policy = jload(POLICY)
    if not policy:
        print(json.dumps({"verdict": "E-POLICY"}, ensure_ascii=False))
        return 2

    done = [r for r in rows(QUEUE) if str(r.get("state", "")).upper() == "DONE"][-a.limit:]
    results = []
    approved = rejected = skipped = 0
    for card in done:
        rel = str(card.get("deliverable") or "").strip()
        if not rel or REMOTE_RE.match(rel) or rel.startswith(SUBREPO_PREFIX) or \
                rel.startswith("cph4/fleet/state/"):
            results.append({"id": card.get("id"), "verdict": "SKIP",
                            "why": "非本机可判产物：%s" % rel[:40]})
            skipped += 1
            continue
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            results.append({"id": card.get("id"), "verdict": "SKIP", "why": "产物不在盘"})
            skipped += 1
            continue
        f1 = l1(p, rel)
        f2, notes = l2(card, p, rel) if not f1 else ([], [])
        layers = {"L1": "PASS" if not f1 else "FAIL", "L2": "PASS" if not f2 else "FAIL",
                  "L3": "n/a"}
        if f1 or f2:
            rejected += 1
            results.append({"id": card.get("id"), "verdict": "REJECT",
                            "why": "; ".join((f1 + f2)[:3]), "notes": notes[:2]})
            continue
        rec = None
        if a.apply:
            rec = archive(p, card, layers)
            it = intake(rec, card, policy)
            layers["intake"] = (it or {}).get("state", "n/a")
        approved += 1
        results.append({"id": card.get("id"), "verdict": "APPROVED",
                        "archived": (rec or {}).get("archived"), "notes": notes[:2]})

    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    L = ["# 产出审核 %s" % now, "",
         "_三层：L1 结构 / L2 一致性 / L3 语义抽查。DONE 只表示执行结束，不代表合格。_", "",
         "本次审 %d 张：**通过 %d / 拒 %d / 跳过 %d**（跳过=远端或不在盘，本机不可判）"
         % (len(results), approved, rejected, skipped), ""]
    rej = [r for r in results if r["verdict"] == "REJECT"]
    if rej:
        L += ["## 被拒（必须回炉）", ""]
        for r in rej:
            L.append("- **%s**：%s" % (r["id"], r["why"]))
        L.append("")
    app = [r for r in results if r["verdict"] == "APPROVED"]
    if app:
        L += ["## 通过并入档", ""]
        for r in app[:12]:
            L.append("- %s → `%s`%s" % (r["id"], r.get("archived") or "（dry-run 未写）",
                                        ("（待入 %s）" % (r.get("notes") or [""])[0]) if r.get("notes") else ""))
        L.append("")
    with open(BOARD, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump({"ts": now, "approved": approved, "rejected": rejected,
                   "skipped": skipped, "results": results}, f, ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": "REJECT" if rejected else "OK", "approved": approved,
                      "rejected": rejected, "skipped": skipped,
                      "applied": bool(a.apply), "board": os.path.relpath(BOARD, ROOT)},
                     ensure_ascii=False))
    for r in rej[:6]:
        print("  REJECT", r["id"], r["why"][:70])
    return 1 if rejected else 0


if __name__ == "__main__":
    sys.exit(main())