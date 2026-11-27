#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""quality_agents.py - 分线质量席：量得出来、拦得住、能自证。

CEO 2026-11-07「给各个业务和研发提升质量的智能体，要先进可靠」。可靠的定义写在这里：
  1. **判据可机算**：每条都落到一个数（时长/分辨率/黑场比/字段齐全/引用数…），不靠感觉。
  2. **反例自证（negative control）**：每条判据都配一个"应当被判 FAIL"的合成样本，
     --selftest 时若反例竟然通过，说明这条闸是假的，直接 rc=2 报警。
     （历史教训：假绿比没有闸更糟——报过一次假绿，之后真绿也没人信。）
  3. **漂移监测**：每次评分进 state/quality/<line>.jsonl，与历史中位数比，
     跌破 drift_drop_pct 就点名"质量在退步"，而不是只看"这次过没过"。
  4. **双层判分**：规则判分是硬闸；模型只做补充描述（可关），规则永不让位。

用法：
  python3 Tools/fleet/quality_agents.py --selftest                 # 反例自证（CI 必跑）
  python3 Tools/fleet/quality_agents.py --line content-mv --artifact <file>
  python3 Tools/fleet/quality_agents.py --report                   # 一屏 QUALITY-BOARD.md
  rc: 0 通过 | 1 未达阈值 | 2 反例失效/配置坏 | 3 输入缺失
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
REG = os.path.join(F, "QUALITY-AGENTS-v1.json")
STATE = os.path.join(F, "state", "quality")
def _tool(name):
    """找一个真能跑的可执行文件（launchd 的 PATH 不含 ~/bin，实测把 ffmpeg 判成缺失）。"""
    import shutil
    cand = os.environ.get(name.upper()) or ""
    if cand and os.path.exists(cand):
        return cand
    hit = shutil.which(name)
    if hit:
        return hit
    for d in (os.path.expanduser("~/bin"), "/opt/homebrew/bin", "/usr/local/bin",
              r"C:\ffmpeg\bin", r"C:\Program Files\ffmpeg\bin"):
        p2 = os.path.join(d, name + (".exe" if os.name == "nt" else ""))
        if os.path.exists(p2):
            return p2
    return name


FFPROBE = _tool("ffprobe")
FFMPEG = _tool("ffmpeg")


def now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def registry():
    with open(REG, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- metrics
def _run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or ""), (r.stderr or "")
    except Exception:
        return 127, "", ""


def _probe(path):
    rc, out, _ = _run([FFPROBE, "-v", "error", "-print_format", "json",
                       "-show_format", "-show_streams", path])
    if rc != 0:
        return None
    try:
        return json.loads(out)
    except Exception:
        return None


def metrics_video(path):
    d = _probe(path)
    m = {}
    if not d:
        return m
    fmt = d.get("format") or {}
    v = next((s for s in d.get("streams") or [] if s.get("codec_type") == "video"), {})
    a = next((s for s in d.get("streams") or [] if s.get("codec_type") == "audio"), None)
    try:
        m["duration_s"] = float(fmt.get("duration") or 0)
    except Exception:
        m["duration_s"] = 0.0
    m["height_px"] = int(v.get("height") or 0)
    m["width_px"] = int(v.get("width") or 0)
    try:
        m["bitrate_kbps"] = int(fmt.get("bit_rate") or 0) // 1000
    except Exception:
        m["bitrate_kbps"] = 0
    m["has_audio"] = bool(a)
    # 黑场占比：blackdetect 给出黑场总时长 / 总时长
    rc, out, err = _run([FFMPEG, "-v", "info", "-i", path, "-vf",
                         "blackdetect=d=0.1:pix_th=0.10", "-an", "-f", "null", "-"], timeout=300)
    blob = (err or "") + (out or "")
    blacks = 0.0
    for mm in re.finditer(r"black_duration:([0-9.]+)", blob):
        try:
            blacks += float(mm.group(1))
        except Exception:
            pass
    total = m.get("duration_s") or 0
    m["black_ratio"] = round(blacks / total, 4) if total > 0 else 1.0
    return m


def metrics_image(path):
    d = _probe(path)
    m = {}
    if not d:
        return m
    v = next((s for s in d.get("streams") or [] if s.get("codec_type") == "video"), {})
    w, h = int(v.get("width") or 0), int(v.get("height") or 0)
    m["width_px"], m["height_px"] = w, h
    m["min_side_px"] = min(w, h) if w and h else 0
    try:
        m["file_kb"] = round(os.path.getsize(path) / 1024.0, 2)
    except Exception:
        m["file_kb"] = 0
    # 颜色多样性：抽样像素的唯一颜色比例（用 ffmpeg 缩到 32x32 后统计）
    tmp = os.path.join(tempfile.gettempdir(), "qa_colors.raw")
    rc, _, _ = _run([FFMPEG, "-v", "error", "-y", "-i", path, "-vf", "scale=32:32",
                     "-f", "rawvideo", "-pix_fmt", "rgb24", tmp], timeout=60)
    ratio = 0.0
    if rc == 0 and os.path.exists(tmp):
        try:
            data = open(tmp, "rb").read()
            px = [data[i:i + 3] for i in range(0, len(data), 3)]
            ratio = round(len(set(px)) / float(max(1, len(px))), 4)
        except Exception:
            ratio = 0.0
        finally:
            try:
                os.remove(tmp)
            except Exception:
                pass
    m["unique_color_ratio"] = ratio
    m["aspect"] = round(w / float(h), 4) if h else 0.0
    # 关键帧只认 16:9 / 9:16（其余会被 i2v 或竖屏裁切）；给 3% 容差
    m["aspect_in_set"] = any(abs(m["aspect"] - t) / t <= 0.03 for t in (16 / 9.0, 9 / 16.0))
    return m


def metrics_build(path):
    """构建类：path 是构建目录。看入口清单、体积、引用完整性。"""
    m = {"entry_exists": False, "total_mb": 0.0, "broken_refs": 0}
    if not os.path.isdir(path):
        return m
    total = 0
    for dirpath, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(dirpath, f))
            except Exception:
                pass
    m["total_mb"] = round(total / (1024.0 * 1024.0), 2)
    entry = None
    for cand in ("index.html", "manifest.json", "game.json", "project.json", "Build.json"):
        p = os.path.join(path, cand)
        if os.path.exists(p):
            entry = p
            break
    m["entry_exists"] = bool(entry)
    if entry and entry.endswith(".json"):
        try:
            doc = json.load(open(entry, encoding="utf-8-sig"))
            refs = []
            for k in ("files", "assets", "entry", "main"):
                v = doc.get(k)
                if isinstance(v, list):
                    refs += [x for x in v if isinstance(x, str)]
                elif isinstance(v, str):
                    refs.append(v)
            m["broken_refs"] = sum(1 for r in refs
                                   if not os.path.exists(os.path.join(path, r)))
        except Exception:
            m["broken_refs"] = 0
    return m


def metrics_report(path):
    """报告类：只吃 json（回测报告）。"""
    m = {"has_fields": False, "has_benchmark": False,
         "trades": 0, "period_days": 0}
    try:
        doc = json.load(open(path, encoding="utf-8-sig"))
    except Exception:
        return m
    need = ("sharpe", "max_drawdown", "trades", "benchmark", "period")
    m["has_fields"] = all(k in doc for k in need)
    m["has_benchmark"] = bool(doc.get("benchmark"))
    try:
        m["trades"] = int(doc.get("trades") or 0)
    except Exception:
        m["trades"] = 0
    period = doc.get("period")
    days = 0
    if isinstance(period, str) and "-" in period:
        try:
            a, b = period.split("-")[:2]
            from datetime import date
            d1 = date.fromisoformat(a if len(a) > 4 else a + "-01-01")
            d2 = date.fromisoformat(b if len(b) > 4 else b + "-01-01")
            days = (d2 - d1).days
        except Exception:
            days = 0
    elif isinstance(period, (int, float)):
        days = int(period)
    m["period_days"] = days
    return m


def metrics_doc(path):
    m = {"sections": 0, "placeholder_hits": 0, "chars": 0, "evidence_links": 0}
    try:
        s = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return m
    m["chars"] = len(s)
    m["sections"] = len(re.findall(r"(?m)^#{2,3}\s+\S", s))
    m["placeholder_hits"] = len(re.findall(r"(?i)\bTODO\b|\bTBD\b|待补|占位|待定", s))
    m["evidence_links"] = len(re.findall(r"https?://", s))
    # 正身件引仓内文件路径（反引号包住的 cph4/… 、Tools/…）同样是证据。
    # 只认 http 链接会把"路径即证据"的文档全判死（CROSS-MACHINE-EXEC-v1.md 实锚）。
    for cand in re.findall(r"`([\w./\-]+\.(?:md|json|jsonl|py|ps1|mp4|png|jpg|csv))`", s):
        if os.path.exists(os.path.join(ROOT, cand)):
            m["evidence_links"] += 1
    return m


METRICS = {"video": metrics_video, "image": metrics_image,
           "build": metrics_build, "report": metrics_report, "doc": metrics_doc}


def measure(kind, path):
    fn = METRICS.get(kind)
    return fn(path) if fn else {}


# ---------------------------------------------------------------- scoring
def check(item, m):
    metric = item["metric"]
    if metric not in m:
        return None            # 量不出来 = 不判（不许把"没量到"当通过）
    got = m[metric]
    want = item["value"]
    op = item["op"]
    try:
        if op == ">=":
            return got >= want
        if op == "<=":
            return got <= want
        if op == "==":
            return got == want
        if op == ">":
            return got > want
        if op == "<":
            return got < want
    except Exception:
        return None
    return None


def score_line(key, path, reg=None):
    reg = reg or registry()
    spec = (reg.get("lines") or {}).get(key)
    if not spec:
        return None
    m = measure(spec.get("artifact"), path)
    rows, judged, passed, blocked = [], 0, 0, []
    m_judged = m_passed = 0
    for item in spec.get("items") or []:
        ok = check(item, m)
        mandatory = item.get("mandatory", True)     # 默认强制：单条硬伤不能被加权分放过去
        rows.append({"id": item["id"], "metric": item["metric"], "op": item["op"],
                     "want": item["value"], "got": m.get(item["metric"]),
                     "ok": ok, "why": item.get("why"), "mandatory": mandatory})
        if ok is not None:
            judged += 1
            passed += 1 if ok else 0
            if mandatory:
                m_judged += 1
                m_passed += 1 if ok else 0
            if ok is False and mandatory:
                blocked.append(item["id"])
    # 建议项（mandatory:false）只作提示，不进分数线：否则一张合规的方图道具
    # 会因为"关键帧才要求 16:9"这条建议被判 FAIL —— 2026-11-08 实测 0.75<0.8。
    ratio = round((m_passed if m_judged else passed) / float(m_judged or judged), 3) \
        if (m_judged or judged) else None
    return {"line": key, "path": path, "measured": m, "items": rows,
            "judged": judged, "passed": passed, "mandatory_judged": m_judged,
            "mandatory_passed": m_passed, "score": ratio,
            "blocked": blocked, "verdict_ok": (not blocked)}


# ---------------------------------------------------------------- negative controls
def _ff(tmpd, name, args):
    p = os.path.join(tmpd, name)
    _run([FFMPEG, "-v", "error", "-y"] + args + [p], timeout=120)
    return p


def _bad_for(item, kind, reg):
    """为单条判据造一个**只违反它**的样本；造不出来就返回 None（宁可不判也不假绿）。"""
    metric = item.get("metric")
    tmpd = tempfile.mkdtemp(prefix="qa_bad_")
    v = item.get("value")

    if kind == "video":
        if metric == "duration_s":
            return _ff(tmpd, "b.mp4", ["-f", "lavfi", "-i", "color=c=gray:s=1280x720:d=2",
                                       "-f", "lavfi", "-i", "sine=f=440:d=2",
                                       "-shortest", "-r", "10"])
        if metric == "height_px":
            return _ff(tmpd, "b.mp4", ["-f", "lavfi", "-i", "color=c=gray:s=320x240:d=40",
                                       "-f", "lavfi", "-i", "sine=f=440:d=40",
                                       "-shortest", "-r", "10"])
        if metric == "has_audio":
            return _ff(tmpd, "b.mp4", ["-f", "lavfi", "-i", "color=c=gray:s=1280x720:d=40",
                                       "-an", "-r", "10"])
        if metric == "black_ratio":
            return _ff(tmpd, "b.mp4", ["-f", "lavfi", "-i", "color=c=black:s=1280x720:d=40",
                                       "-f", "lavfi", "-i", "sine=f=440:d=40",
                                       "-shortest", "-r", "10"])
        if metric == "bitrate_kbps":
            return _ff(tmpd, "b.mp4", ["-f", "lavfi", "-i", "color=c=gray:s=1280x720:d=40",
                                       "-f", "lavfi", "-i", "sine=f=440:d=40",
                                       "-shortest", "-r", "2", "-b:v", "60k"])
        return None

    if kind == "image":
        if metric == "min_side_px":
            return _ff(tmpd, "b.png", ["-f", "lavfi", "-i", "color=c=red:s=64x64:d=1",
                                       "-frames:v", "1"])
        if metric == "aspect_in_set":
            return _ff(tmpd, "b.png", ["-f", "lavfi", "-i", "testsrc=s=512x512:d=1",
                                       "-frames:v", "1"])
        if metric == "file_kb":
            return _ff(tmpd, "b.png", ["-f", "lavfi", "-i", "color=c=gray:s=8x8:d=1",
                                       "-frames:v", "1"])
        if metric == "unique_color_ratio":
            return _ff(tmpd, "b.png", ["-f", "lavfi", "-i", "color=c=red:s=512x512:d=1",
                                       "-frames:v", "1"])
        return None

    if kind == "build":
        d = os.path.join(tmpd, "build")
        os.makedirs(d, exist_ok=True)
        if metric == "entry_exists":
            return d                      # 空目录 = 无入口
        if metric == "total_mb" and item.get("op") == "<=":
            big = os.path.join(d, "payload.bin")
            with open(big, "wb") as f:     # 稀疏文件：不占真实磁盘
                f.truncate(int((float(v) + 20) * 1024 * 1024))
            return d
        if metric == "total_mb":
            return d                      # 空目录 = 0MB
        if metric == "broken_refs":
            mf = os.path.join(d, "manifest.json")
            json.dump({"files": ["missing_1.bin", "missing_2.bin"]},
                      open(mf, "w", encoding="utf-8"))
            return d
        return None

    if kind == "report":
        p = os.path.join(tmpd, "b.json")
        if metric == "has_fields":
            json.dump({"note": "empty"}, open(p, "w", encoding="utf-8"))
            return p
        if metric == "trades":
            json.dump({"sharpe": 1.0, "max_drawdown": 0.2, "trades": 3,
                       "benchmark": "CSI300", "period": "2020-01-01-2025-01-01"},
                      open(p, "w", encoding="utf-8"))
            return p
        if metric == "period_days":
            json.dump({"sharpe": 1.0, "max_drawdown": 0.2, "trades": 100,
                       "benchmark": "CSI300", "period": "2026-01-01-2026-02-01"},
                      open(p, "w", encoding="utf-8"))
            return p
        if metric == "has_benchmark":
            json.dump({"sharpe": 1.0, "max_drawdown": 0.2, "trades": 100,
                       "period": "2020-01-01-2025-01-01"},
                      open(p, "w", encoding="utf-8"))
            return p
        return None

    if kind == "doc":
        p = os.path.join(tmpd, "b.md")
        if metric == "sections":
            open(p, "w", encoding="utf-8").write("# only title\n\ntext\n")
        elif metric == "placeholder_hits":
            open(p, "w", encoding="utf-8").write("# t\n\n## a\n\nTODO 待补\n\n## b\n\n## c\n")
        elif metric == "chars":
            open(p, "w", encoding="utf-8").write("# t\n\n## a\n\nshort\n")
        elif metric == "evidence_links":
            open(p, "w", encoding="utf-8").write(
                "# t\n\n## a\n\n" + "x" * 900 + "\n\n## b\n\n## c\n")
        else:
            return None
        return p
    return None


def have_tools():
    """工具缺失 ≠ 判据失效：先分清是哪一种，否则会把"本机没 ffmpeg"报成 21 条假闸。"""
    miss = []
    for name, path in (("ffmpeg", FFMPEG), ("ffprobe", FFPROBE)):
        try:
            rc, _, _ = _run([path, "-version"], timeout=15)
        except Exception:
            rc = 127
        if rc != 0:
            miss.append(name)
    return miss


def selftest(verbose=True):
    """逐条判据：为它造专属反例，必须判 FAIL。拦不住的判据 = 假闸。"""
    miss = have_tools()
    if miss:
        msg = ("本机缺 %s（PATH 与常见安装目录都没找到），无法造反例自证 → "
               "换到有 ffmpeg 的机器跑，不要判成判据失效" % "、".join(miss))
        if verbose:
            print("[quality-selftest] BLOCKED: " + msg)
        return 3, {"items": 0, "problems": ["E-NO-FFMPEG: " + msg], "missing_tools": miss}
    reg = registry()
    bad, checked = [], 0
    for key, spec in (reg.get("lines") or {}).items():
        kind = spec.get("artifact")
        for item in spec.get("items") or []:
            p = _bad_for(item, kind, reg)
            if not p:
                bad.append("%s/%s: 造不出专属反例（判据无法自证）" % (key, item["id"]))
                continue
            m = measure(kind, p)
            ok = check(item, m)
            checked += 1
            if ok is True:
                bad.append("%s/%s: 反例通过（假闸）metric=%s want=%s%s got=%s" %
                           (key, item["id"], item["metric"], item["op"], item["value"],
                            m.get(item["metric"])))
            elif ok is None:
                bad.append("%s/%s: 反例上量不出 %s" % (key, item["id"], item["metric"]))
    if any(sys.platform.startswith("win") for _ in [0]):
        pass
    verdict = "PASS" if not bad else "FAIL"
    if verbose:
        print("[quality-selftest] items=%d verdict=%s" % (checked, verdict))
        for b in bad[:12]:
            print("   - %s" % b)
    return 0 if not bad else 2, {"items": checked, "problems": bad}


# ---------------------------------------------------------------- history / drift
def record(res):
    if not res:
        return
    os.makedirs(STATE, exist_ok=True)
    p = os.path.join(STATE, "%s.jsonl" % res["line"])
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now(), "score": res["score"],
                            "passed": res["passed"], "judged": res["judged"],
                            "blocked": res.get("blocked") or [], "path": res["path"]},
                           ensure_ascii=False) + "\n")


def drift(res, reg):
    p = os.path.join(STATE, "%s.jsonl" % res["line"])
    if not os.path.exists(p):
        return None
    vals = []
    for line in open(p, encoding="utf-8"):
        try:
            d = json.loads(line)
            if d.get("score") is not None:
                vals.append(float(d["score"]))
        except Exception:
            pass
    if len(vals) < 5 or res["score"] is None:
        return None
    vals_sorted = sorted(vals)
    median = vals_sorted[len(vals_sorted) // 2]
    drop_pct = reg.get("thresholds", {}).get("drift_drop_pct", 15)
    if median > 0 and (median - res["score"]) / median * 100.0 > drop_pct:
        return {"median": median, "now": res["score"], "drop_pct": drop_pct}
    return None


def board(reg=None):
    reg = reg or registry()
    out = ["# 质量席一屏 %s" % now(), "",
           "判据来源：`cph4/fleet/QUALITY-AGENTS-v1.json`（每条判据都自带反例）", ""]
    out.append("| 线 | 最近评分 | 判定 | 历史中位 | 漂移 | 硬伤 |")
    out.append("|---|---|---|---|---|---|")
    for key, spec in (reg.get("lines") or {}).items():
        p = os.path.join(STATE, "%s.jsonl" % key)
        rows = []
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
        rows = [r for r in rows]
        if not rows or rows[-1].get("score") is None:
            out.append("| %s | - | 未评分（本机无产物） | - | - | - |" % spec.get("name", key))
            continue
        rows = [r for r in rows if r.get("score") is not None]
        last = rows[-1]
        hist = sorted(float(r["score"]) for r in rows)
        med = hist[len(hist) // 2]
        thr = reg.get("thresholds", {}).get("pass_score", 0.8)
        verdict = "PASS" if float(last["score"]) >= thr and not last.get("blocked") else "FAIL"
        drop = reg.get("thresholds", {}).get("drift_drop_pct", 15)
        dflag = "-"
        if med > 0 and (med - float(last["score"])) / med * 100.0 > drop:
            dflag = "退步 %.0f%%" % ((med - float(last["score"])) / med * 100.0)
        out.append("| %s | %.2f | %s | %.2f | %s |" %
                   (spec.get("name", key), float(last["score"]), verdict, med, dflag))
    out += ["", "## 反例自证（闸是否真的会拦）", ""]
    rc, info = selftest(verbose=False)
    out.append("- 判据数：%d" % info["items"])
    out.append("- 结论：%s" % ("全部能拦住反例（闸有效）" if rc == 0 else
                              "有 %d 条闸失效：%s" % (len(info["problems"]), info["problems"][:3])))
    path = os.path.join(F, "QUALITY-BOARD.md")
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    return path


def _newest(paths):
    best = None
    for p in paths:
        try:
            mt = os.path.getmtime(p)
        except Exception:
            continue
        if best is None or mt > best[0]:
            best = (mt, p)
    return best[1] if best else None


def scan(reg=None, only=None):
    """按注册表里的 globs 找每条线最新的产物并打分；找不到就如实说没有。"""
    import glob as _g
    reg = reg or registry()
    out = []
    for key, spec in (reg.get("lines") or {}).items():
        if only and key != only:
            continue
        cands = []
        for pat in spec.get("globs") or []:
            cands += [p for p in _g.glob(os.path.join(ROOT, pat), recursive=True)
                      if os.path.isfile(p) or os.path.isdir(p)]
        # exclude：样机/冒烟/演示件不是交付物。以前把 lp_smoke_*.mp4 当成成片判 VD-01
        # （时长<30s、无音轨）→ 影片线常年 FAIL，而真正该看的是 full_mv_*。
        ex = spec.get("exclude") or []
        if ex:
            def _excluded(p):
                rel = os.path.relpath(p, ROOT).replace(os.sep, "/").lower()
                return any(_g.fnmatch.fnmatch(rel, e.lower()) for e in ex)
            cands = [p for p in cands if not _excluded(p)]
        p = _newest(cands)
        if not p:
            # 本机没产物也要留一行：否则屏上永远显示上一次的旧分（收窄取样后仍挂着
            # 早已不该判的 FAIL，谁也没法修）。
            try:
                os.makedirs(STATE, exist_ok=True)
                with open(os.path.join(STATE, "%s.jsonl" % key), "a",
                          encoding="utf-8") as f:
                    f.write(json.dumps({"ts": now(), "score": None,
                                        "state": "NO-ARTIFACT"}, ensure_ascii=False) + "\n")
            except Exception:
                pass
            out.append({"line": key, "state": "NO-ARTIFACT"})
            continue
        res = score_line(key, p, reg)
        if res:
            record(res)
            out.append({"line": key, "state": "SCORED", "artifact": p,
                        "score": res["score"], "blocked": res.get("blocked") or []})
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--line")
    ap.add_argument("--artifact")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        rc, info = selftest()
        if a.json:
            print(json.dumps(info, ensure_ascii=False))
        return rc
    if a.scan:
        rows = scan(only=a.line)
        for r in rows:
            if r["state"] == "NO-ARTIFACT":
                print("[quality] %-13s NO-ARTIFACT（本机没有该线产物，不评分）" % r["line"])
            else:
                print("[quality] %-13s %.2f %s %s" %
                      (r["line"], r["score"] or 0,
                       "HARD-FAIL:" + ",".join(r["blocked"]) if r["blocked"] else "ok",
                       os.path.relpath(r["artifact"], ROOT)))
        p = board()
        print("[quality] board -> %s" % p)
        return 0
    if a.report:
        p = board()
        print("[quality] board -> %s" % p)
        return 0
    if not a.line or not a.artifact:
        print(__doc__)
        return 3
    if not os.path.exists(a.artifact):
        print("[quality] E-NOARTIFACT %s" % a.artifact)
        return 3
    reg = registry()
    res = score_line(a.line, a.artifact, reg)
    if res is None:
        print("[quality] E-NOLINE %s" % a.line)
        return 3
    d = drift(res, reg)
    record(res)
    thr = reg.get("thresholds", {}).get("pass_score", 0.8)
    ok = (res["score"] is not None and res["score"] >= thr
          and not res.get("blocked"))
    print("[quality] %-13s score=%.2f (%d/%d) %s%s" %
          (a.line, res["score"] or 0, res["passed"], res["judged"],
           "PASS" if ok else "FAIL",
           "" if not res.get("blocked") else "  HARD-FAIL:" + ",".join(res["blocked"])))
    for row in res["items"]:
        mark = {True: "ok", False: "FAIL", None: "n/a"}[row["ok"]]
        print("   %-6s %-18s got=%-10s want %s %s  -> %s" %
              (row["id"], row["metric"], row["got"], row["op"], row["want"], mark))
    if d:
        print("   DRIFT 低于历史中位 %.0f%%（中位 %.2f → 本次 %.2f）" %
              ((d["median"] - d["now"]) / d["median"] * 100.0, d["median"], d["now"]))
    if a.json:
        print(json.dumps(res, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))