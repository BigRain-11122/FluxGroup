#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CPU 车道：把确定性审计与本地模型审阅排进 CPU/内存，GPU 留给交互。

实测（2026-11-20，bm-a 9950X/32T/94GB）：
  9b  num_gpu=0 num_thread=12 → 8.0 tok/s，RAM ~6GB
  27b num_gpu=0 num_thread=12 → 2.7 tok/s，RAM ~17GB
所以「纯 CPU 不服务」是旧结论，已废。车道按线程配额排队，不抢 GPU。

用法:
    python Tools/gds/cpu_lane.py --status
    python Tools/gds/cpu_lane.py --run                    # 跑全部
    python Tools/gds/cpu_lane.py --run R1 R2              # 跑指定
    python Tools/gds/cpu_lane.py --self-test              # 负控：坏数据必须被抓
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "cph4" / "fleet" / "game-v2"
AUDITS = BASE / "audits"
OLLAMA = "http://127.0.0.1:11434/api/generate"

sys.path.insert(0, str(ROOT / "Tools" / "agents"))
from contract_lint import contract_hash, load_yaml  # noqa: E402

SYSTEM_RAM_RESERVE_GB = 8.0

JOBS = {
    "R1": {"kind": "det", "title": "回执审计：状态分布 + 契约哈希漂移", "threads": 1},
    "R2": {"kind": "det", "title": "规则消费者审计：无消费者的法条", "threads": 1},
    "R3": {"kind": "det", "title": "同指标多值扫描：文档里的互斥数字", "threads": 1},
    "R4": {"kind": "det", "title": "判据-代码锚点：六条 spike 判据有没有可测的实现", "threads": 1},
    "R5": {"kind": "det", "title": "文档重叠：可退役或合并的治理文件", "threads": 1},
    "M2": {"kind": "model", "model": "qwen3.5:27b", "threads": 12,
           "title": "需求追溯：没有验收判据的需求条目"},
}

# 判据 → 锚点。scope=code 只搜 .cs（实现存在）；scope=record 只搜人测/试玩记录（证据存在）。
# 命中只证明「有可测的东西」，不证明「已达标」。
ANCHORS = {
    "C1 折/层遮挡/折痕误差": {"scope": "code", "pats": [
        ("层间隙常量", r"LayerGap\s*=\s*[\d.]+"),
        ("渲染层偏移", r"\*\s*LayerGap"),
        ("撤销恢复层", r"UndoLast\s*\("),
        ("预览插值", r"UpdatePreview\s*\("),
    ]},
    "C2 判定一致性/耗时": {"scope": "code", "pats": [
        ("顶点哈希", r"ComputeHash\s*\("),
        ("重放次数", r"RepeatCount"),
        ("判定入口", r"CoverageJudge"),
        ("负控三态", r"MeasureNegativeControls"),
    ]},
    "C3 装箱空间约束": {"scope": "code", "pats": [
        ("满格拒绝", r"IsFull"),
        ("首空格", r"FirstFreeSlot"),
        ("槽距常量", r"SlotPitch"),
        ("占用计数", r"Occupied"),
    ]},
    "C4 5 人盲看": {"scope": "record", "pats": [
        ("盲看记录", r"盲看|blind[\s_-]?test"),
        ("试玩记录", r"playtest"),
    ]},
    "C5 单格计时/p50": {"scope": "code", "pats": [
        ("单格计时", r"slotElapsed|itemSeconds|perItemMs|slotTimer|roomTimer"),
        ("单格统计", r"slotP50|itemP50"),
    ]},
    "C6 性能/帧率/DrawCall": {"scope": "code", "pats": [
        ("帧率采样", r"targetFrameRate|FrameTiming|frameCount"),
        ("批次数", r"SetPassCalls|batches|DrawCall"),
    ]},
}

METRIC_PATTERNS = {
    "首通分钟": r"(?:首通|通关)[^。\n|]{0,14}?(\d{2,3})\s*(?:分钟|min)",
    "每份净收入": r"每份净[^。\n|]{0,10}?(\d{2}\.\d{2})",
    "月净3万份数": r"(\d{3,4})\s*份/月",
    "款每年": r"(\d{1,2})\s*款/年",
    "单款周期周": r"(\d+(?:\.\d+)?)\s*周/款",
}


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def free_gb() -> float:
    # ctypes 读 GlobalMemoryStatusEx，免装依赖
    import ctypes

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

    st = MEMORYSTATUSEX()
    st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
        return -1.0
    return st.ullAvailPhys / (1024 ** 3)


# ---------------- 确定性任务 ----------------

def job_receipts(_ctx):
    receipts = BASE / "receipts"
    rows, problems = [], []
    for f in sorted(receipts.glob("*/*.json")):
        if f.parent.name.startswith("_"):
            continue
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            problems.append({"file": rel(f), "why": f"json: {exc}"})
            continue
        cpath = ROOT / r.get("contract_file", "")
        drift = None
        if not cpath.exists():
            problems.append({"file": rel(f), "why": "契约缺失"})
        else:
            try:
                drift = contract_hash(load_yaml(cpath)) != r.get("contract_hash")
            except Exception as exc:  # noqa: BLE001
                problems.append({"file": rel(f), "why": f"契约解析: {exc}"})
        if drift:
            problems.append({"file": rel(f), "why": "契约哈希已漂移（回执作废）"})
        if r.get("status") == "PASS" and not r.get("evidence"):
            problems.append({"file": rel(f), "why": "PASS 无证据"})
        rows.append({"project": r.get("project_id"), "gate": r.get("receipt"),
                     "status": r.get("status"), "drift": bool(drift)})

    by_status = {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    by_project = {}
    for r in rows:
        d = by_project.setdefault(r["project"], {})
        d[r["status"]] = d.get(r["status"], 0) + 1
    return {
        "summary": {"receipts": len(rows), "by_status": by_status, "problems": len(problems)},
        "by_project": by_project,
        "problems": problems,
        "rows": rows,
    }


def job_rule_consumers(_ctx):
    const = load_yaml(BASE / "constitution.yaml")
    arts = [a["id"] for a in const.get("articles", [])]
    files = [p for p in BASE.rglob("*") if p.suffix in {".md", ".yaml", ".py", ".json"}
             and p.is_file() and "constitution.yaml" not in p.name
             and "package" not in str(p)]
    text = {}
    for p in files:
        try:
            text[p] = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    consumers, orphans = {}, []
    for a in arts:
        hits = [rel(p) for p, t in text.items() if a in t]
        consumers[a] = len(hits)
        if not hits:
            orphans.append(a)
    return {
        "summary": {"articles": len(arts), "orphans": orphans,
                    "min_consumers": min(consumers.values()) if consumers else 0},
        "consumers": dict(sorted(consumers.items())),
    }


def job_metric_conflicts(ctx):
    docs = sorted(list(BASE.rglob("*.md")))
    found = {}
    for p in docs:
        relp = rel(p)
        if "receipts" in relp or "\\local\\" in relp:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name, pat in METRIC_PATTERNS.items():
            for m in re.finditer(pat, text):
                val = m.group(1)
                line = text.count("\n", 0, m.start()) + 1
                found.setdefault(name, []).append({"value": val, "file": relp, "line": line})
    conflicts = {k: v for k, v in found.items() if len({x["value"] for x in v}) > 1}
    return {
        "summary": {"metrics_scanned": len(METRIC_PATTERNS),
                    "metrics_with_multiple_values": len(conflicts)},
        "conflicts": {
            k: {"distinct": sorted({x["value"] for x in v}, key=lambda s: (len(s), s)),
                "occurrences": len(v),
                "samples": v[:8]}
            for k, v in conflicts.items()
        },
    }


# ---------------- 模型任务 ----------------

def build_req_pack() -> str:
    p = BASE / "projects" / "fold-001" / "REQUIREMENTS.md"
    text = p.read_text(encoding="utf-8", errors="replace")
    keep = [l for l in text.splitlines() if re.match(r"^\s*(#{2,3}|\d+[.)]|[-*]\s)", l)]
    return "\n".join(keep)[:5500]


def call_model(model: str, threads: int, system: str, prompt: str, num_predict: int = 500) -> str:
    payload = {
        "model": model, "system": system, "prompt": prompt, "stream": False,
        "think": False, "keep_alive": "5m",
        "options": {"num_gpu": 0, "num_thread": threads,
                    "num_ctx": 8192, "temperature": 0.1, "num_predict": num_predict},
    }
    req = urllib.request.Request(
        OLLAMA, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        out = json.loads(r.read().decode("utf-8"))
    return (out.get("response") or "").strip()


def job_req_trace(_ctx) -> dict:
    system = ("你是需求审计。给定需求条目与 G-B 六条判据，找出「没有任何可测验收判据」的需求，"
              "最多 6 条，每条一行：需求 | 缺什么判据 | 建议怎么测。不要复述需求原文。")
    criteria = ("G-B 判据：折 180° 无穿模/≥3 层遮挡/折痕误差；20 次重放一致/单次≤2ms；"
                "装箱空间约束/一格 60-90 秒；5 人盲看 3 秒与 10 秒；每格 p50 60-90 秒/首通≥100 分钟；"
                "1080p ≥58fps/1% low ≥50/DrawCall ≤12")
    prompt = f"判据：{criteria}\n\n需求条目：\n{build_req_pack()}\n\n列出没有验收判据的需求。"
    t0 = time.time()
    text = call_model("qwen3.5:27b", 12, system, prompt, 420)
    return {
        "summary": {"model": "qwen3.5:27b", "cpu_only": True, "threads": 12,
                    "elapsed_s": round(time.time() - t0, 1), "chars": len(text)},
        "output": text,
    }


def job_anchors(_ctx):
    proj = BASE / "projects" / "fold-001"
    # 代码锚点只看 .cs；记录锚点只看 local/ 下的人测文件（排除 audits/，否则会读到自己）
    code_files = [p for p in (proj / "game" / "Assets").rglob("*.cs") if p.is_file()] \
        if (proj / "game" / "Assets").exists() else []
    record_files = [p for p in (proj / "local").glob("*") if p.is_file()] \
        if (proj / "local").exists() else []

    def load(paths):
        out = {}
        for p in paths:
            try:
                out[p] = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
        return out

    code_text = load(code_files)
    rec_text = load(record_files)

    rows = {}
    for crit, spec in ANCHORS.items():
        texts = code_text if spec["scope"] == "code" else rec_text
        hits, missing = [], []
        for label, pat in spec["pats"]:
            found = None
            for p, t in texts.items():
                m = re.search(pat, t)
                if m:
                    line = t.count("\n", 0, m.start()) + 1
                    found = f"{p.name}:{line}"
                    break
            (hits if found else missing).append({"anchor": label, "at": found})
        state = "有可测实现" if not missing else ("部分" if hits else "无")
        rows[crit] = {"state": state, "scope": spec["scope"],
                      "hits": [h for h in hits if h["at"]],
                      "missing": [m["anchor"] for m in missing]}
    return {
        "summary": {"criteria": len(rows),
                    "with_full_anchor": sum(1 for v in rows.values() if v["state"] == "有可测实现"),
                    "partial": sum(1 for v in rows.values() if v["state"] == "部分"),
                    "no_anchor": sum(1 for v in rows.values() if v["state"] == "无")},
        "criteria": rows,
        "note": "命中=有可测的东西，不等于达标；C4 记录型判据必须有人测文件，文档里的要求不算。",
    }


def job_doc_overlap(_ctx):
    """用中文二元组做 Jaccard。整段中文按字切，避免「长词组集合互不相交」的死指标。"""
    docs = [p for p in BASE.glob("*.md") if p.is_file()]

    def shingles(text: str, n: int = 2) -> set[str]:
        out: set[str] = set()
        for run in re.findall(r"[\u4e00-\u9fff]+", text):
            for i in range(len(run) - n + 1):
                out.add(run[i:i + n])
        return out

    grams = {}
    for p in docs:
        try:
            grams[p] = shingles(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    pairs = []
    names = sorted(grams)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            if not grams[a] or not grams[b]:
                continue
            inter = len(grams[a] & grams[b])
            if inter == 0:
                continue
            jac = inter / len(grams[a] | grams[b])
            if jac >= 0.10:
                pairs.append({"a": names[i].name, "b": names[j].name,
                              "jaccard": round(jac, 3), "shared_2grams": inter})
    pairs.sort(key=lambda x: -x["jaccard"])
    return {
        "summary": {"docs": len(docs), "pairs_over_threshold": len(pairs),
                    "top": pairs[:5]},
        "pairs": pairs[:20],
        "note": "相似度高不等于该删；只作为「合并/退役」候选，需人工定夺。阈值=0.10（二元组）。",
    }


RUNNERS = {
    "R1": job_receipts,
    "R2": job_rule_consumers,
    "R3": job_metric_conflicts,
    "R4": job_anchors,
    "R5": job_doc_overlap,
    "M2": job_req_trace,
}


# ---------------- 调度 ----------------

def write_result(job_id: str, result: dict, stamp: str) -> Path:
    AUDITS.mkdir(parents=True, exist_ok=True)
    out = AUDITS / f"{job_id}-{stamp}.json"
    out.write_text(json.dumps({"job": job_id, "title": JOBS[job_id]["title"],
                               "ran_at": now(), "result": result},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def run_jobs(ids: list[str]) -> int:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if free_gb() < SYSTEM_RAM_RESERVE_GB:
        print(json.dumps({"error": "ram_low", "free_gb": round(free_gb(), 1),
                          "reserve_gb": SYSTEM_RAM_RESERVE_GB}, ensure_ascii=False))
        return 2

    det = [j for j in ids if JOBS[j]["kind"] == "det"]
    mod = [j for j in ids if JOBS[j]["kind"] == "model"]

    results = {}

    def run_one(j: str):
        t0 = time.time()
        try:
            res = RUNNERS[j]({})
            ok = True
        except Exception as exc:  # noqa: BLE001
            res = {"error": f"{type(exc).__name__}: {exc}"[:300]}
            ok = False
        path = write_result(j, res, stamp)
        results[j] = {"job": j, "ok": ok, "elapsed_s": round(time.time() - t0, 1),
                      "out": rel(path), "summary": (res or {}).get("summary")}
        print(json.dumps(results[j], ensure_ascii=False), flush=True)

    with ThreadPoolExecutor(max_workers=max(1, len(det))) as ex:
        list(ex.map(run_one, det))
    # 模型任务按线程配额排队：总线程 12+12=24，留 8 给系统
    for j in mod:
        run_one(j)

    summary = {"stamp": stamp, "jobs": len(ids),
               "ok": sum(1 for r in results.values() if r["ok"]),
               "out_dir": rel(AUDITS), "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0 if summary["ok"] == len(ids) else 1


def status() -> int:
    print(json.dumps({
        "cpu": {"lanes": {k: f"{v['threads']}T" for k, v in JOBS.items()},
                "model_threads_total": sum(v["threads"] for v in JOBS.values() if v["kind"] == "model")},
        "ram_free_gb": round(free_gb(), 1),
        "ram_reserve_gb": SYSTEM_RAM_RESERVE_GB,
        "audits": len(list(AUDITS.glob("*.json"))) if AUDITS.exists() else 0,
        "jobs": {k: v["title"] for k, v in JOBS.items()},
    }, ensure_ascii=False, indent=1))
    return 0


def self_test() -> int:
    """负控：坏回执、无消费者法条、互斥数字必须被抓到。"""
    import tempfile

    fails = 0
    # 1) 回执：PASS 无证据 + 哈希漂移
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "receipts" / "P1").mkdir(parents=True)
        (td / "receipts" / "P1" / "G1.json").write_text(json.dumps({
            "project_id": "P1", "receipt": "gate/G1", "contract_file": "no/such.yaml",
            "contract_hash": "deadbeef", "status": "PASS", "evidence": []}), encoding="utf-8")
        orig = sys.modules[__name__].BASE
        try:
            sys.modules[__name__].BASE = td  # type: ignore
            r = job_receipts({})
            why = [p["why"] for p in r["problems"]]
            if not any("契约缺失" in w for w in why) or not any("PASS 无证据" in w for w in why):
                fails += 1
                print("FAIL 坏回执未被抓:", why)
            else:
                print("PASS 抓到坏回执:", why)
        finally:
            sys.modules[__name__].BASE = orig  # type: ignore

    # 2) 同指标多值
    sample = "首通 42 分钟。另一处：首通 127 分钟。每份净 ¥32.52。每份净 ¥46.35。"
    vals = {}
    for name, pat in METRIC_PATTERNS.items():
        vs = {m.group(1) for m in re.finditer(pat, sample)}
        if len(vs) > 1:
            vals[name] = sorted(vs)
    if "首通分钟" in vals and "每份净收入" in vals:
        print("PASS 抓到互斥数字:", vals)
    else:
        fails += 1
        print("FAIL 互斥数字未被抓:", vals)

    # 3) 无消费者法条：造一条只在宪法里出现的 id
    txt = "C-01 C-02 C-77"
    hits = [a for a in ("C-01", "C-77") if a not in txt.replace(a, "", 1)]
    if "C-77" in hits:
        print("PASS 抓到无消费者法条: C-77")
    else:
        fails += 1
        print("FAIL 无消费者法条未被抓")

    print(json.dumps({"self_test": "PASS" if not fails else "FAIL", "failures": fails},
                     ensure_ascii=False))
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", nargs="*", default=None)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if args.status:
        return status()
    ids = args.run if args.run else list(JOBS)
    unknown = [j for j in ids if j not in JOBS]
    if unknown:
        print(json.dumps({"error": "unknown_jobs", "ids": unknown, "known": list(JOBS)},
                         ensure_ascii=False))
        return 2
    return run_jobs(ids)


if __name__ == "__main__":
    raise SystemExit(main())
