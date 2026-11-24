#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸执行器 v2：读契约，跑 G1/G2/G7/G8（静态），G3–G6 无证据记 NOT_RUN。

支持新工程：
    python Tools/agents/gate_runner.py \
      --contract cph4/fleet/game-v2/contracts/fold-001.yaml \
      --project-root cph4/fleet/game-v2/projects/fold-001 \
      --materials cph4/fleet/game-v2/projects/fold-001/delivery
不启动游戏、不改工程。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "cph4" / "fleet" / "game-v2"
DEFAULT_PROJECT = ROOT / "gaming" / "MiniGame" / "09_吸嘟嘟_GimmeAll_CAR" / "GimmeAll"
DEFAULT_SOFT = ROOT / "软著申请材料" / "G09_GimmeAll"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_lint import check_project, contract_hash, load_yaml  # noqa: E402


def age_days(ts: float) -> float:
    return (datetime.now().timestamp() - ts) / 86400


def read_text(p: Path, cap=600_000) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:cap]
    except OSError:
        return ""


def newest_source_ts(project: Path) -> float:
    exts = {".cs", ".prefab", ".asset", ".unity", ".mat", ".shader", ".shadergraph"}
    assets = project / "Assets"
    out = 0.0
    if not assets.exists():
        return out
    for p in assets.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            out = max(out, p.stat().st_mtime)
    return out


def g1_compile(project: Path):
    logs = sorted((project / "Logs").glob("compile_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not logs:
        return "NOT_RUN", [], "没有编译日志"
    log = logs[0]
    text = read_text(log)
    errors = len(re.findall(r"error CS\d+", text))
    ok_exit = "Exiting batchmode successfully" in text
    src_newer = newest_source_ts(project) > log.stat().st_mtime
    false_green = False
    tx = project / "Logs" / "test_meta_result.xml"
    tests = [p for p in (project / "Assets").rglob("*.cs") if "Tests" in p.parts] if (project / "Assets").exists() else []
    if tx.exists():
        m = re.search(r'testcasecount="(\d+)"', read_text(tx, 20000))
        false_green = bool(m and int(m.group(1)) == 0 and tests)
    fails = []
    if errors:
        fails.append(f"error CS={errors}")
    if not ok_exit:
        fails.append("batchmode 未成功退出")
    if src_newer:
        fails.append("源码新于编译日志")
    if false_green:
        fails.append("测试 0 用例却报 Passed")
    note = f"error CS={errors}；源码新于日志={src_newer}；假绿={false_green}"
    return ("PASS" if not fails else "FAIL"), [str(log.relative_to(ROOT))], note + ("；" + "；".join(fails) if fails else "")


def g2_build(project: Path):
    win = project / "Build" / "Win64"
    builds = []
    if win.exists():
        for sub in win.iterdir():
            if sub.is_dir():
                exes = [e for e in sub.glob("*.exe") if "CrashHandler" not in e.name]
                if exes:
                    builds.append(sub)
    apks = sorted((project / "Build").rglob("*.apk"), key=lambda p: p.stat().st_mtime, reverse=True) if (project / "Build").exists() else []
    webgl = project / "Build" / "MiniGameWeChat" / "webgl" / "index.html"
    if not builds and not apks and not webgl.exists():
        return "NOT_RUN", [], "没有可执行产物"
    tss = [b.stat().st_mtime for b in builds] + [a.stat().st_mtime for a in apks]
    if webgl.exists():
        tss.append(webgl.stat().st_mtime)
    newest_ts = max(tss)
    src_newer = newest_source_ts(project) > newest_ts
    age = age_days(newest_ts)
    fails = []
    if src_newer:
        fails.append("源码新于包")
    if age > 7:
        fails.append(f"包龄 {age:.1f} 天 > 7")
    ev = [str(b.relative_to(ROOT)) for b in builds[:2]] + [str(a.relative_to(ROOT)) for a in apks[:2]]
    return ("PASS" if not fails else "FAIL"), ev, f"最新包 {age:.1f} 天；源码新于包={src_newer}"


def g7_assets(project: Path):
    assets = project / "Assets"
    if not assets.exists():
        return "NOT_RUN", [], "没有 Assets 目录"
    files = [p for p in assets.rglob("*") if p.is_file()]
    missing = [p for p in files if p.suffix.lower() in {".cs", ".png", ".mat", ".prefab", ".asset"}
               and not Path(str(p) + ".meta").exists()]
    fails = [f"缺 meta {len(missing)}"] if missing else []
    return ("PASS" if not fails else "FAIL"), [str(assets.relative_to(ROOT))], \
        f"资产 {len(files)} 件；缺 meta {len(missing)}"


def g8_delivery(project: Path, materials: Path):
    icon = materials / "icon_512.png"
    privacy = materials / "privacy-policy.md"
    src = list(materials.glob("*源程序.txt")) if materials.exists() else []
    store_dirs = [project / "Store", project / "store", project / "marketing",
                  project / "Marketing", materials / "截图", materials / "screenshots"]
    shots, used_dir = [], None
    for d in store_dirs:
        if d.exists():
            imgs = [p for p in d.rglob("*") if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}]
            if imgs:
                shots, used_dir = imgs, d
                break
    fails = []
    if not icon.exists():
        fails.append("缺图标")
    if not privacy.exists():
        fails.append("缺隐私政策")
    if not src:
        fails.append("缺源程序")
    if len(shots) < 4:
        fails.append(f"商店截图 {len(shots)} < 4（需专用物料目录）")
    ev = [str(x.relative_to(ROOT)) for x in [icon, privacy] if x.exists()]
    if used_dir:
        ev.append(str(used_dir.relative_to(ROOT)))
    return ("PASS" if not fails else "FAIL"), ev, "；".join(fails) or "物料齐"


def g6_compliance(project: Path, contract):
    assets = project / "Assets"
    if not assets.exists():
        return "NOT_RUN", [], "没有 Assets 目录"
    ads = list((assets / "_Project" / "Ads").glob("*.cs")) if (assets / "_Project" / "Ads").exists() else []
    all_cs = [p for p in assets.rglob("*.cs")]
    level_failed = [p for p in all_cs if "LevelFailed" in read_text(p, 40000)]
    cls = contract.get("class")
    fails = []
    if cls in ("A", "C") and ads:
        fails.append(f"广告脚本 {len(ads)} 个")
    if level_failed:
        fails.append(f"疑似失败态路径 {len(level_failed)} 处")
    ev = [str(p.relative_to(project)) for p in (ads[:3] + level_failed[:3])]
    note = "；".join(fails) or "未发现广告/失败态"
    if level_failed:
        note += "（Family soft landing 是否完全屏蔽失败屏未证）"
    return ("PASS" if not fails else "FAIL"), ev, note


def g3_g5(project: Path, patterns, regex):
    hits = []
    for d in ("Logs", "production", "Design/evidence"):
        base = project / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".log", ".json", ".csv", ".txt"}:
                if any(k in p.name.lower() for k in patterns) and re.search(regex, read_text(p, 40000)):
                    hits.append(p)
    if not hits:
        return "NOT_RUN", [], "没有可用的测量文件"
    hits.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    age = age_days(hits[0].stat().st_mtime)
    return ("PASS" if age <= 30 else "FAIL"), [str(hits[0].relative_to(ROOT))], f"测量命中；{age:.1f} 天前"


def write_receipt(contract_path: Path, p: dict, gate: str, status: str, evidence, note):
    rec = {
        "receipt": f"gate/{gate}",
        "project_id": p.get("project_id"),
        "contract_file": str(contract_path.relative_to(ROOT)),
        "contract_hash": contract_hash(p),
        "constitution_version": p.get("constitution_version"),
        "class_version": p.get("class_version"),
        "status": status,
        "evidence": evidence,
        "note": note,
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    outdir = BASE / "receipts" / str(p.get("project_id"))
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{gate}.json"
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", required=True)
    ap.add_argument("--project-root", default=str(DEFAULT_PROJECT))
    ap.add_argument("--materials", default=None)
    args = ap.parse_args()

    cpath = ROOT / args.contract
    project = Path(args.project_root)
    if not project.is_absolute():
        project = ROOT / project
    if not project.exists():
        print(json.dumps({"error": "project not found", "path": str(project)}, ensure_ascii=False))
        return 2

    materials = Path(args.materials) if args.materials else (project / "delivery")
    if not materials.is_absolute():
        materials = ROOT / materials
    if not materials.exists() and project == DEFAULT_PROJECT:
        materials = DEFAULT_SOFT

    const = load_yaml(BASE / "constitution.yaml")
    classes = load_yaml(BASE / "classes.yaml")
    p = load_yaml(cpath)
    fails = check_project(p, const, classes)
    if fails:
        print(json.dumps({"error": "contract_invalid", "failures": fails}, ensure_ascii=False))
        return 2

    results = {
        "G1": g1_compile(project),
        "G2": g2_build(project),
        "G3": g3_g5(project, ["coldstart", "cold-start", "startup", "player.log"],
                    r"(startup|cold)[^\n]{0,40}(\d+(\.\d+)?)\s*(ms|s|秒)"),
        "G4": g3_g5(project, ["fps", "perf", "profile", "frame"], r"(\d{2,3}(\.\d+)?)\s*fps|fps[^\n]{0,10}(\d{2,3})"),
        "G5": g3_g5(project, ["session", "playtest", "playthrough", "tour"],
                    r"(duration|elapsed|session)[^\n]{0,30}(\d+(\.\d+)?)\s*(s|秒)"),
        "G6": g6_compliance(project, p),
        "G7": g7_assets(project),
        "G8": g8_delivery(project, materials),
    }
    summary = []
    for gate, (status, ev, note) in results.items():
        out = write_receipt(cpath, p, gate, status, ev, note)
        summary.append({"gate": gate, "status": status, "note": note, "receipt": str(out.relative_to(ROOT))})
    counts = {}
    for r in summary:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(json.dumps({"project": p.get("project_id"), "hash": contract_hash(p),
                      "project_root": str(project.relative_to(ROOT)),
                      "counts": counts, "gates": summary}, ensure_ascii=True, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
