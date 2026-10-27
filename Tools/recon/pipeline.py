#!/usr/bin/env python3
"""pipeline.py — 竞品破解流水线（编排现成工具，不自造解析器）

把"拿到一个包"到"可用的归一化数值"串成一条可重复执行的命令：

  1. 定位解包目录（<slug>_x）与 APK
  2. 引擎识别（Cocos / Unity-il2cpp / 未知）
  3. 配置抽取：
       Cocos  -> cocos_cfg.py（明文 cc.JsonAsset）
       Unity  -> 指向 il2cpp_out 的 dump.cs / dump_schema 产出，不在此重解析
  4. 归一化：把抽出的表整理成统一 schema（recon-levels/v1）
  5. 校验：只搬运原值，不自造；字段覆盖不足则只列候选，不产出 levels.json
  6. 出 MANIFEST.json + REPORT.md

用法:
  python Tools/recon/pipeline.py --slug xwdsh
  python Tools/recon/pipeline.py --slug xxl --normalize-only
  python Tools/recon/pipeline.py --list
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APK_ROOT = Path(r"D:\FluxGroup\recon\apk")
DATA_ROOT = ROOT / "media" / "recon" / "data"
CARD_DIR = ROOT / "cph4" / "fleet" / "recon-dept-v1" / "cards"
COCOS_CFG = ROOT / "Tools" / "recon" / "cocos_cfg.py"

# 波次字段别名：全部来自已确认的 LevelWaveConfig 字段名（逻辑面复刻），不改名不补值。
WAVE_ALIASES = {
    "triggerTime": ("triggerTime", "trigger", "startTime", "waveStartTime"),
    "firstRefreshNum": ("firstRefreshNum", "firstNum", "initNum", "firstRefresh"),
    "singleRefreshNum": ("singleRefreshNum", "singleNum", "perRefresh", "batchNum"),
    "interval": ("interval", "refreshInterval", "spawnInterval"),
    "eliteRefreshTime": ("eliteRefreshTime", "eliteTime", "eliteRefresh"),
    "bossRefreshTime": ("bossRefreshTime", "bossTime", "bossRefresh"),
    "atkRatio": ("atkRatio", "attackRatio", "atkScale"),
    "hpRatio": ("hpRatio", "healthRatio", "hpScale"),
    "passValue": ("passValue", "goalValue", "targetValue"),
    "valueMax": ("valueMax", "goalMax", "targetMax"),
    "currencyNum": ("currencyNum", "rewardNum", "coinNum"),
}


def log(msg: str) -> None:
    print(f"[recon] {msg}", flush=True)


def detect_engine(extracted: Path) -> str:
    if (extracted / "assets" / "assets" / "resources").is_dir():
        return "cocos"
    if (extracted / "lib").is_dir() and list(extracted.glob("lib/**/libil2cpp.so")):
        return "unity-il2cpp"
    if (extracted / "assets" / "bin" / "Data").is_dir():
        return "unity-mono"
    return "unknown"


def find_extracted(slug: str) -> Path | None:
    for cand in (APK_ROOT / f"{slug}_x", APK_ROOT / slug):
        if cand.is_dir():
            return cand
    return None


def run_cocos_cfg(extracted: Path, slug: str) -> tuple[int, str]:
    if not COCOS_CFG.exists():
        return 1, f"missing {COCOS_CFG}"
    p = subprocess.run(
        [sys.executable, str(COCOS_CFG), str(extracted), slug],
        capture_output=True, text=True, errors="replace",
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def load_tables(slug: str) -> list[dict]:
    """读取 cocos_cfg 产出的表；每项 = {table, path, data}。"""
    d = DATA_ROOT / slug
    if not d.is_dir():
        return []
    tables = []
    for p in sorted(d.glob("*.json")):
        if p.name.startswith("_"):
            continue
        try:
            raw = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        tables.append({"table": p.stem, "path": str(p), "data": raw})
    return tables


def pick(obj: dict, alias: tuple[str, ...]):
    lowered = {k.lower(): v for k, v in obj.items()}
    for a in alias:
        if a.lower() in lowered:
            return lowered[a.lower()]
    return None


def rows_of(data) -> list[dict]:
    """表的行：数组 / {rows:[...]} / 按 id 键的字典（Cocos 常见）。"""
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        for k in ("rows", "data", "list", "items", "configs"):
            v = data.get(k)
            if isinstance(v, list):
                return [r for r in v if isinstance(r, dict)]
        # 字典按 id 键：{"1": {...}, "2": {...}}
        dict_rows = [(k, v) for k, v in data.items() if isinstance(v, dict)]
        if len(dict_rows) >= 3:
            out = []
            for k, v in dict_rows:
                row = dict(v)
                row.setdefault("_key", k)
                out.append(row)
            return out
        # 单行对象视作一行
        if data and all(not isinstance(v, (list, dict)) for v in data.values()):
            return [data]
    return []


def score_table(rows: list[dict]) -> int:
    if not rows:
        return 0
    hit = 0
    for key, aliases in WAVE_ALIASES.items():
        if any(pick(rows[0], aliases) is not None for _ in (0,)):
            hit += 1
    return hit


def normalize(slug: str, engine: str) -> dict:
    tables = load_tables(slug)
    candidates = []
    best = None
    best_score = 0
    for t in tables:
        rows = rows_of(t["data"])
        score = score_table(rows)
        if score:
            candidates.append({
                "table": t["table"], "rows": len(rows),
                "wave_fields_hit": score, "path": t["path"],
            })
        if score > best_score and score >= 3:
            best_score, best = score, (t, rows)

    manifest = {
        "schema": "recon-manifest/v1",
        "slug": slug,
        "engine": engine,
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "table_count": len(tables),
        "tables": [{"table": t["table"], "rows": len(rows_of(t["data"])), "path": t["path"]} for t in tables],
        "level_candidates": sorted(candidates, key=lambda c: -c["wave_fields_hit"]),
        "levels_emitted": False,
        "note": "字段覆盖不足则不产出 levels.json；本流水线只搬运原值，不补默认值。",
    }

    if best:
        t, rows = best
        out_levels = []
        for i, row in enumerate(rows):
            wave = {}
            for key, aliases in WAVE_ALIASES.items():
                v = pick(row, aliases)
                if v is not None:
                    wave[key] = v
            lvl_id = pick(row, ("id", "levelId", "level", "stageId"))
            out_levels.append({"id": lvl_id if lvl_id is not None else i + 1, "waves": [wave]})
        levels = {
            "schema": "recon-levels/v1",
            "slug": slug,
            "engine": engine,
            "source_table": t["table"],
            "source_path": t["path"],
            "field_coverage": f"{best_score}/{len(WAVE_ALIASES)}",
            "levels": out_levels,
        }
        dst = DATA_ROOT / slug / "levels.json"
        dst.write_text(json.dumps(levels, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest["levels_emitted"] = True
        manifest["levels_path"] = str(dst)
        manifest["levels_count"] = len(out_levels)
        manifest["levels_source_table"] = t["table"]
        log(f"levels.json <- {t['table']} ({len(out_levels)} 行, 字段覆盖 {best_score}/{len(WAVE_ALIASES)})")

    # 规范化落盘：每张有效表写成 jsonl（原值直搬），并统计列名与行数
    norm_dir = DATA_ROOT / slug / "norm"
    norm_dir.mkdir(parents=True, exist_ok=True)
    normalized = []
    for t in tables:
        rows = rows_of(t["data"])
        if len(rows) < 5:
            continue
        cols = sorted({k for r in rows[:50] for k in r.keys()})
        out = norm_dir / f"{t['table']}.jsonl"
        with out.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        normalized.append({"table": t["table"], "rows": len(rows),
                           "columns": cols[:40], "jsonl": str(out)})
    manifest["normalized_tables"] = normalized
    manifest["normalized_count"] = len(normalized)

    # 曲线导出：形如 level→数字 的成长/难度表，直接给策划用（原值直搬，不做拟合）
    curve_dir = DATA_ROOT / slug / "curves"
    curve_dir.mkdir(parents=True, exist_ok=True)
    curves = []
    for n in normalized:
        rows = []
        with open(n["jsonl"], "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
        if not rows:
            continue
        idx_col = next((c for c in rows[0].keys()
                        if re.fullmatch(r"(?i)_?key|id|level|stage|chapter", c)), None)
        num_cols = []
        for c in rows[0].keys():
            if c == idx_col:
                continue
            vals = [r.get(c) for r in rows if isinstance(r.get(c), (int, float))]
            if len(vals) >= max(5, int(len(rows) * 0.8)):
                num_cols.append(c)
        if not idx_col or not num_cols or len(rows) < 8:
            continue
        for c in num_cols[:3]:
            out = curve_dir / f"{n['table']}.{c}.csv"
            with out.open("w", encoding="utf-8") as f:
                f.write(f"{idx_col},{c}\n")
                for r in rows:
                    if isinstance(r.get(c), (int, float)):
                        f.write(f"{r.get(idx_col)},{r[c]}\n")
            curves.append({"table": n["table"], "index": idx_col, "value": c,
                           "rows": len(rows), "csv": str(out)})
    manifest["curves"] = curves[:80]
    manifest["curve_count"] = len(curves)

    # Unity/IL2CPP：没有明文表，但有 dump.cs —— 建「配置类→字段」索引供设计面查
    if engine == "unity-il2cpp":
        cands = [APK_ROOT / "il2cpp_out" / "dump.cs"]
        cands += sorted(APK_ROOT.glob(f"{slug}*/**/dump.cs"))
        cands += sorted(APK_ROOT.glob("il2cpp_*/dump.cs"))
        for c in cands:
            if c.exists():
                manifest["il2cpp"] = il2cpp_index(c)
                log(f"il2cpp index <- {c} (classes={manifest['il2cpp']['class_count']}, "
                    f"config={manifest['il2cpp']['config_class_count']})")
                break

    (DATA_ROOT / slug).mkdir(parents=True, exist_ok=True)
    (DATA_ROOT / slug / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def parse_dump_cs(path: Path) -> dict:
    """从 Il2CppDumper 的 dump.cs 抽 类→字段 索引（机械解析，不推断数值）。"""
    classes: dict[str, list[str]] = {}
    current = None
    pending = None
    depth = 0
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                s = line.strip()
                m = re.match(r"(?:public|internal|private|protected)?\s*(?:sealed\s+|abstract\s+|static\s+|partial\s+)*class\s+([A-Za-z0-9_`<>]+)", s)
                if m:
                    pending = m.group(1)
                    if "{" in s:
                        current, depth = pending, s.count("{") - s.count("}")
                        classes.setdefault(current, [])
                        pending = None
                    continue
                if pending is not None:
                    if s.startswith("{"):
                        current, depth = pending, 1
                        classes.setdefault(current, [])
                        pending = None
                    elif s and not s.startswith("//"):
                        pending = None
                    continue
                if current is None:
                    continue
                depth += s.count("{") - s.count("}")
                if depth <= 0:
                    current = None
                    continue
                fm = re.match(r"(?:public|private|protected|internal|readonly|static|\s)+([A-Za-z0-9_<>,\.\[\]]+)\s+([A-Za-z0-9_]+)\s*(?:[;=])", s)
                if fm and not s.startswith("//"):
                    name = fm.group(2)
                    if name not in classes[current]:
                        classes[current].append(name)
    except Exception:
        return {}
    return classes


def il2cpp_index(dump_cs: Path) -> dict:
    classes = parse_dump_cs(dump_cs)
    keys = re.compile(r"(?i)(level|wave|config|stage|reward|drop|shop|iap|price|enemy|spawn|buff|skill)")
    relevant = {k: v for k, v in classes.items() if keys.search(k)}
    return {
        "dump_cs": str(dump_cs),
        "class_count": len(classes),
        "config_class_count": len(relevant),
        "config_classes": [{"class": k, "fields": v[:40]} for k, v in
                           sorted(relevant.items(), key=lambda kv: -len(kv[1]))[:120]],
    }


def write_report(slug: str, manifest: dict, engine: str, extract_log: str) -> Path:
    CARD_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    p = CARD_DIR / f"PIPELINE-{slug}-{ts}.md"
    lines = [
        f"# 破解流水线回执 · {slug}",
        "",
        f"- 生成：{manifest['generated']}",
        f"- 引擎：{engine}",
        f"- 抽表数：{manifest['table_count']}",
        f"- 归一化产物：{'已产出 ' + manifest.get('levels_path','') if manifest['levels_emitted'] else '未产出（字段覆盖不足，只列候选）'}",
        "",
        "## 关卡候选表",
        "",
        "| 表 | 行数 | 波次字段命中 |",
        "|---|---|---|",
    ]
    for c in manifest["level_candidates"][:10]:
        lines.append(f"| {c['table']} | {c['rows']} | {c['wave_fields_hit']}/{len(WAVE_ALIASES)} |")
    lines += ["", "## 抽取日志（尾部 20 行）", "", "```", *extract_log.strip().splitlines()[-20:], "```", ""]
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--normalize-only", action="store_true")
    args = ap.parse_args()

    if args.list:
        for d in sorted(APK_ROOT.iterdir()) if APK_ROOT.exists() else []:
            if d.is_dir() and d.name.endswith("_x"):
                print(d.name[:-2])
        return 0

    if not args.slug:
        ap.error("--slug required")

    slug = args.slug
    extracted = find_extracted(slug)
    if not extracted:
        print(f"[recon] 未找到解包目录：{APK_ROOT}\\{slug}_x", file=sys.stderr)
        return 2

    engine = detect_engine(extracted)
    log(f"slug={slug} engine={engine} dir={extracted}")

    extract_log = ""
    if not args.normalize_only:
        if engine == "cocos":
            rc, out = run_cocos_cfg(extracted, slug)
            extract_log = out
            log(f"cocos_cfg rc={rc}")
            if rc != 0:
                print(out, file=sys.stderr)
                return rc
        elif engine == "unity-il2cpp":
            extract_log = ("Unity/IL2CPP：配置在 Assembly-CSharp 内，走 Il2CppDumper/Cpp2IL 链；\n"
                           "本流水线只做归一化，不重复反编译。已有 dump 见 D:\\FluxGroup\\recon\\apk\\il2cpp_out")
            log("unity-il2cpp：跳过抽表，直接归一化已有 dump")
        else:
            extract_log = "引擎未识别：先跑 apk_recon.py 确认包结构"
            log(extract_log)

    manifest = normalize(slug, engine)
    report = write_report(slug, manifest, engine, extract_log)
    print(json.dumps({
        "slug": slug, "engine": engine,
        "tables": manifest["table_count"],
        "levels_emitted": manifest["levels_emitted"],
        "levels_count": manifest.get("levels_count", 0),
        "manifest": str(DATA_ROOT / slug / "MANIFEST.json"),
        "report": str(report),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())