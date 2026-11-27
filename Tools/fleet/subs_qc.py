#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""subs_qc.py — 漫剧线字幕逐集质检（SRT / ASS）。

为什么：QUALITY-SPEC-v2 §7 只写了"单行 ≤ 17 字"，其余（停留时长、CPS、标点、越界、
错别字）以前靠人眼看。人眼看不出 4.06s 和 4.00s 的差，也看不出"这次协议/这份协议"。
本工具把这些全部变成可测量的数字，每条判据给出命中行号，便于直接改。

判据（硬，命中即 FAIL）：
  R1 单行字数 > 17（含标点，去空白；QUALITY-SPEC-v2 §7 GUARDED_V4 折行律）
  R2 单条停留 < 0.60s 或 > 4.00s
  R3 CPS（字数/停留秒） > 9.0
  R4 出现半角标点或英文引号（, . ! ? ; : " ' ( ) 等）
  R5 时间码非法：倒序 / 重叠 / 起点<0 / 尾部超出容器时长 +0.10s
  R6 单条超过 2 行（折行律上限）
  R7 错别字黑名单命中
  R7b 同源组多数派不一致（同时间栅格的字幕里，文本与多数派不同 → 判为误识）
  R8 空文本 / 纯标点

软（WARN，不影响结论）：
  W1 相邻两条间隙 < 0.04s（烧制时字幕跳变，无呼吸感）
  W2 文件末尾缺换行 / BOM / CRLF 混用
  W3 单行 15–17 字（贴线，建议折行）
  W4 无 ASR sidecar（无出处，无法回溯是哪一版人声转出来的）

用法：
  python3 Tools/fleet/subs_qc.py cph4/fleet/drama-dept-v1/subs/*.srt \\
      --media-dir media/drama-out --json /tmp/subs_qc.json
  python3 Tools/fleet/subs_qc.py --self-test        # 正负控自检
Exit: 0 = 全 PASS；1 = 有 FAIL；2 = 读不了 / 自检不达标。
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# ---- 判据常量（改这里 = 改闸）----------------------------------------------
MAX_CHARS_PER_LINE = 17      # QUALITY-SPEC-v2 §7
MIN_CUE_S = 0.60
MAX_CUE_S = 4.00
MAX_CPS = 9.0
MAX_CUE_LINES = 2
TAIL_TOLERANCE_S = 0.10
GAP_WARN_S = 0.04
NEAR_LIMIT_CHARS = 15        # W3 贴线

# 半角标点 / 英文引号（出现即违反"中文标点"口径）
HALF_WIDTH = set(',.!?;:"\'()[]{}<>/\\|~`@#$%^&*_+=')
# 允许出现的符号（中文省略号、破折号、间隔号等）——不在 HALF_WIDTH 里即放行

# 错别字黑名单：常见字幕/ASR 误写（左=错，右=对）
TYPO_BLACKLIST = [
    ("签属", "签署"),
    ("做为", "作为"),
    ("在次", "再次"),
    ("即然", "既然"),
    ("因该", "应该"),
    ("以经", "已经"),
    ("由其是", "尤其是"),
]

CN_PUNCT = set("，。！？；：、“”‘’（）《》【】…—·「」『』～")


# ---- 解析 ---------------------------------------------------------------
def _clean_text(t):
    """去 ASS 覆盖标签，保留 \\N 断行。"""
    t = re.sub(r"\{[^}]*\}", "", t)
    return t.replace("\\N", "\n").replace("\\n", "\n")


def parse_ts(srt_like):
    srt_like = srt_like.strip()
    m = re.match(r"(?:(\d+):)?(\d{1,2}):(\d{1,2})[.,](\d{1,3})", srt_like)
    if not m:
        return None
    h = int(m.group(1) or 0)
    frac = m.group(4)
    ms = int(frac) if len(frac) == 3 else int(frac.ljust(3, "0"))
    return h * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + ms / 1000.0


def parse_srt(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    cues = []
    for block in re.split(r"\n\s*\n", text.strip("\n")):
        lines = [l for l in block.split("\n")]
        if not lines:
            continue
        tm = None
        body_at = 0
        for i, l in enumerate(lines):
            if "-->" in l:
                tm = l
                body_at = i + 1
                break
        if tm is None:
            continue
        a, b = [x.strip() for x in tm.split("-->")]
        start, end = parse_ts(a), parse_ts(b)
        if start is None or end is None:
            continue
        body = "\n".join(lines[body_at:]).strip("\n")
        if body.strip() == "" and body_at == 0:
            continue
        cues.append({"start": start, "end": end, "text": body})
    return cues


def parse_ass(text):
    text = text.replace("\r\n", "\n")
    fmt = None
    cues = []
    for line in text.split("\n"):
        s = line.strip()
        if s.lower().startswith("format:") and fmt is None:
            fmt = [x.strip().lower() for x in s.split(":", 1)[1].split(",")]
            continue
        if not s.lower().startswith("dialogue:"):
            continue
        if fmt is None:
            fmt = ["layer", "start", "end", "style", "name", "marginl",
                   "marginr", "marginv", "effect", "text"]
        parts = s.split(":", 1)[1].split(",", len(fmt) - 1)
        row = dict(zip(fmt, parts))
        start = parse_ts(row.get("start", ""))
        end = parse_ts(row.get("end", ""))
        if start is None or end is None:
            continue
        cues.append({"start": start, "end": end,
                     "text": _clean_text(row.get("text", "")).strip()})
    return cues


def load_subs(path):
    with open(path, "rb") as f:
        raw = f.read()
    enc = "utf-8-sig"
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("gb18030", "replace")
        enc = "gb18030"
    low = path.lower()
    cues = parse_ass(text) if low.endswith(".ass") else parse_srt(text)
    return cues, text, raw, enc


# ---- 单条度量 -----------------------------------------------------------
def disp_len(s):
    """显示字数：去空白后的字符数（含标点，含中英文）。"""
    return len(re.sub(r"\s+", "", s))


def net_len(s):
    """净字数：只数 CJK/字母/数字，不含标点。"""
    return len(re.findall(r"[0-9A-Za-z\u4e00-\u9fff]", s))


def bad_punct(s):
    return sorted({c for c in s if c in HALF_WIDTH})


def typo_hits(s):
    return [(w, r) for w, r in TYPO_BLACKLIST if w in s]


# ---- 容器时长（只读元数据，不渲染、不解码）-------------------------------
def probe_duration(path):
    if not path or not os.path.exists(path):
        return None
    if shutil.which("ffprobe"):
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nw=1:nk=1", path],
                capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                return float(r.stdout.strip())
        except Exception:
            pass
    return None


def sidecar_path(srt_path):
    """ASR sidecar 可能落在同目录，也可能落在 _qc/ 子目录（本线现状）。"""
    cands = [srt_path + ".json",
             os.path.join(os.path.dirname(srt_path), "_qc",
                          os.path.basename(srt_path) + ".json")]
    for c in cands:
        if os.path.exists(c):
            return c
    return None


def sidecar_duration(srt_path):
    sc = sidecar_path(srt_path)
    if sc:
        try:
            d = json.load(open(sc, encoding="utf-8"))
            if d.get("duration_s"):
                return float(d["duration_s"]), sc
        except Exception:
            pass
    return None, None


# ---- 单文件审计 ---------------------------------------------------------
def audit(path, duration=None, peer=None, dur_src=""):
    cues, text, raw, enc = load_subs(path)
    v = []   # 硬违规
    w = []   # 软告警

    def V(rule, detail):
        v.append({"rule": rule, "detail": detail})

    def W(rule, detail):
        w.append({"rule": rule, "detail": detail})

    if not cues:
        V("R8", "未解析到任何字幕条（空文件 / 时间码不可解析）")

    max_line = 0
    over_len = []
    cps_bad = []
    dur_bad = []
    punct_bad = []
    typo_list = []
    line_overflow = []

    for i, c in enumerate(cues, 1):
        dur = round(c["end"] - c["start"], 3)
        lines = [l for l in c["text"].split("\n")]
        ntext = re.sub(r"\s+", "", c["text"])

        if ntext == "" or all(ch in CN_PUNCT or ch in HALF_WIDTH for ch in ntext):
            V("R8", "第%d条为空或纯标点" % i)

        for l in lines:
            n = disp_len(l)
            max_line = max(max_line, n)
            if n > MAX_CHARS_PER_LINE:
                over_len.append({"cue": i, "chars": n, "text": l})
                V("R1", "第%d条单行%d字> %d：%s" % (i, n, MAX_CHARS_PER_LINE, l))
            elif n >= NEAR_LIMIT_CHARS:
                W("W3", "第%d条单行%d字贴线（≤%d 但建议折行）" % (i, n, MAX_CHARS_PER_LINE))
        if len(lines) > MAX_CUE_LINES:
            line_overflow.append(i)
            V("R6", "第%d条%d行> %d 行上限" % (i, len(lines), MAX_CUE_LINES))

        if dur < MIN_CUE_S or dur > MAX_CUE_S:
            dur_bad.append({"cue": i, "dur": dur})
            V("R2", "第%d条停留%.3fs 越界[%.2f,%.2f]：%s"
              % (i, dur, MIN_CUE_S, MAX_CUE_S, ntext))
        if dur > 0:
            cps = len(ntext) / dur
            if cps > MAX_CPS:
                cps_bad.append({"cue": i, "cps": round(cps, 2)})
                V("R3", "第%d条CPS%.2f> %.1f（%d字/%.2fs）"
                  % (i, cps, MAX_CPS, len(ntext), dur))

        bp = bad_punct(c["text"])
        if bp:
            punct_bad.append({"cue": i, "chars": bp})
            V("R4", "第%d条含半角/英文标点 %s：%s"
              % (i, "".join(bp), ntext))

        th = typo_hits(c["text"])
        for wrong, right in th:
            typo_list.append({"cue": i, "wrong": wrong, "right": right})
            V("R7", "第%d条错别字「%s」应为「%s」" % (i, wrong, right))

        if c["start"] < 0 or c["end"] <= c["start"]:
            V("R5", "第%d条时间码非法 %.3f→%.3f" % (i, c["start"], c["end"]))

    # 时间码序列：倒序 / 重叠 / 间隙
    prev = None
    for i, c in enumerate(cues, 1):
        if prev is not None:
            if c["start"] < prev["start"]:
                V("R5", "第%d条起点%.3f早于上一条(%.3f)：时间码倒序"
                  % (i, c["start"], prev["start"]))
            gap = round(c["start"] - prev["end"], 3)
            if gap < 0:
                V("R5", "第%d条与上一条重叠 %.3fs" % (i, -gap))
            elif gap < GAP_WARN_S:
                W("W1", "第%d条与上一条间隙%.3fs< %.2fs（烧制跳变）"
                  % (i, gap, GAP_WARN_S))
        prev = c

    tail = round(cues[-1]["end"], 3) if cues else 0.0
    if duration and tail > duration + TAIL_TOLERANCE_S:
        V("R5", "尾部越界：末条 %.3fs > 容器 %.3fs（+%.3fs，来源=%s）"
          % (tail, duration, tail - duration, dur_src or "probe"))

    # 同源组多数派（R7b）
    if peer:
        for i, c in enumerate(cues, 1):
            key = (round(c["start"], 3), round(c["end"], 3))
            maj = peer.get(key)
            mine = re.sub(r"[^\u4e00-\u9fffa-zA-Z0-9]", "", c["text"])
            if maj and maj["votes"] >= 2 and mine and mine != maj["text"]:
                V("R7b", "第%d条文本「%s」与同源组多数派「%s」（%d/%d 文件）不一致"
                  % (i, c["text"].replace("\n", "/"), maj["text"],
                     maj["votes"], maj["total"]))

    # 格式
    if not text.endswith("\n"):
        W("W2", "文件末尾缺换行（部分播放器吞最后一条）")
    if raw[:3] == b"\xef\xbb\xbf":
        W("W2", "带 UTF-8 BOM")
    if b"\r\n" in raw and raw.count(b"\r\n") != raw.count(b"\n"):
        W("W2", "CRLF/LF 混用")
    sc_dur, sc_path = sidecar_duration(path)
    if not sc_path:
        W("W4", "无 ASR sidecar（.json），出处不可回溯")

    return {
        "file": path,
        "encoding": enc,
        "cues": len(cues),
        "duration_ref": duration,
        "duration_src": dur_src,
        "tail_end": tail,
        "chars_total": sum(disp_len(c["text"]) for c in cues),
        "max_line_chars": max_line,
        "over_len": over_len,
        "cps_bad": cps_bad,
        "dur_bad": dur_bad,
        "punct_bad": punct_bad,
        "typos": typo_list,
        "line_overflow": line_overflow,
        "cues_detail": [{"i": i, "start": round(c["start"], 3),
                         "end": round(c["end"], 3),
                         "dur": round(c["end"] - c["start"], 3),
                         "chars": disp_len(c["text"]),
                         "cps": round(disp_len(c["text"]) / (c["end"] - c["start"]), 2)
                         if c["end"] > c["start"] else None,
                         "text": c["text"]} for i, c in enumerate(cues, 1)],
        "violations": v,
        "warns": w,
        "verdict": "FAIL" if v else "PASS",
    }


def build_peer_index(results):
    """按时间栅格分组（≥3 个文件同栅格才算同源组），算每格多数派文本。"""
    groups = {}
    for r in results:
        key = tuple((c["start"], c["end"]) for c in r["cues_detail"])
        if not key:
            continue
        groups.setdefault(key, []).append(r["file"])
    peers = {}
    for key, files in groups.items():
        if len(files) < 3:
            continue
        votes = {}
        for f in files:
            r = next(x for x in results if x["file"] == f)
            for idx, (s, e) in enumerate(key):
                t = re.sub(r"[^\u4e00-\u9fffa-zA-Z0-9]",
                           "", r["cues_detail"][idx]["text"])
                d = votes.setdefault((s, e), {})
                d.setdefault(t, 0)
                d[t] += 1
        for k, d in votes.items():
            best = max(d.items(), key=lambda kv: kv[1])
            if best[1] >= 2 and len(d) > 1:
                peers[k] = {"text": best[0], "votes": best[1],
                            "total": len(files)}
    return peers, {k: v for k, v in groups.items() if len(v) >= 3}


# ---- 自检（正负控）------------------------------------------------------
SELFTEST_POS = """1
00:00:00,600 --> 00:00:04,200
这份协议，你签也得签。

2
00:00:04,400 --> 00:00:08,400
三年，你连一句真话都没有。

3
00:00:08,800 --> 00:00:11,960
……我签。
"""

SELFTEST_CASES = [
    ("pos-clean", SELFTEST_POS, None, "PASS", "合格字幕必须 PASS"),
    ("neg-long-line", """1
00:00:00,600 --> 00:00:03,000
我跟你说过多少次了这三年你连一句真话都没有
""", None, "FAIL", "单行 21 字 > 17"),
    ("neg-cps", """1
00:00:00,600 --> 00:00:01,600
你连一句真话都没有你连一句真话都没有
""", None, "FAIL", "17字/1.0s = CPS 17 > 9"),
    ("neg-duration", """1
00:00:00,600 --> 00:00:05,600
我签。
""", None, "FAIL", "停留 5.0s > 4.0"),
    ("neg-halfwidth", """1
00:00:00,600 --> 00:00:03,000
这份协议,你签也得签.
""", None, "FAIL", "半角逗号/句号"),
    ("neg-tail", """1
00:00:00,600 --> 00:00:05,900
我签。
""", 5.0, "FAIL", "末条 5.9s > 容器 5.0s+0.1"),
    ("neg-typo", """1
00:00:00,600 --> 00:00:03,000
这份协议你签属了。
""", None, "FAIL", "错别字 签属→签署"),
    ("neg-empty", """1
00:00:00,600 --> 00:00:03,000
，
""", None, "FAIL", "纯标点"),
]


def self_test():
    tmp = tempfile.mkdtemp(prefix="subs_qc_selftest_")
    score = 0
    total = 0
    rows = []

    def run(text, duration=None):
        p = os.path.join(tmp, "case.srt")
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return audit(p, duration=duration, dur_src="selftest")

    for name, text, dur, expect, why in SELFTEST_CASES:
        total += 1
        r = run(text, dur)
        ok = r["verdict"] == expect
        score += 1 if ok else 0
        rows.append((name, expect, r["verdict"], "OK" if ok else "MISMATCH", why))

    # 同源组多数派：2 票 vs 1 票，少数派必须 FAIL
    group = {}
    for nm, txt in (("g1", "这份协议"), ("g2", "这份协议"), ("g3", "这次协议")):
        p = os.path.join(tmp, nm + ".srt")
        with open(p, "w", encoding="utf-8") as f:
            f.write("1\n00:00:00,000 --> 00:00:01,560\n%s\n" % txt)
        group[nm] = p
    res = [audit(p) for p in group.values()]
    peers, gs = build_peer_index(res)
    res = [audit(p, peer=peers) for p in group.values()]
    by = {os.path.basename(r["file"]): r for r in res}
    for nm, expect in (("g1.srt", "PASS"), ("g2.srt", "PASS"), ("g3.srt", "FAIL")):
        total += 1
        ok = by[nm]["verdict"] == expect
        score += 1 if ok else 0
        rows.append(("peer-" + nm, expect, by[nm]["verdict"],
                     "OK" if ok else "MISMATCH", "多数派 2:1 判少数派"))

    print("== subs_qc 自检（正负控）==")
    for name, expect, got, st, why in rows:
        print("  [%s] %-16s expect=%-4s got=%-4s  %s" % (st, name, expect, got, why))
    print("  自检分数：%d/%d" % (score, total))
    shutil.rmtree(tmp, ignore_errors=True)
    return score, total


# ---- 主流程 -------------------------------------------------------------
def find_container(srt_path, media_dir):
    stem = os.path.splitext(os.path.basename(srt_path))[0]
    if not media_dir:
        return None, ""
    for ext in (".mp4", ".mov", ".mkv", ".webm"):
        p = os.path.join(media_dir, stem + ext)
        if os.path.exists(p):
            d = probe_duration(p)
            if d:
                return d, p
    return None, ""


def main():
    ap = argparse.ArgumentParser(description="漫剧字幕逐集质检")
    ap.add_argument("paths", nargs="*", help="字幕文件（.srt/.ass）")
    ap.add_argument("--media-dir", default="", help="同源容器目录（只读时长元数据）")
    ap.add_argument("--assume-duration", type=float, default=None,
                    help="统一指定容器时长（容器找不到时用）")
    ap.add_argument("--json", default="", help="结果落 JSON")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        s, t = self_test()
        sys.exit(0 if s == t else 2)
    if not args.paths:
        ap.print_help()
        sys.exit(2)

    results = []
    for p in args.paths:
        if not os.path.exists(p):
            print("!! 缺失：%s" % p, file=sys.stderr)
            results.append({"file": p, "verdict": "FAIL", "cues": 0,
                            "violations": [{"rule": "R0", "detail": "文件不存在"}],
                            "warns": [], "cues_detail": []})
            continue
        dur, src = find_container(p, args.media_dir)
        if dur is None:
            dur, sc = sidecar_duration(p)
            src = (src or "") + (sc or "")
        if dur is None and args.assume_duration:
            dur, src = args.assume_duration, "assume"
        results.append(audit(p, duration=dur, dur_src=os.path.basename(src or "")))

    peers, groups = build_peer_index(results)
    if peers:
        out = []
        for r in results:
            p = r["file"]
            dur, src = r["duration_ref"], r["duration_src"]
            out.append(audit(p, duration=dur, peer=peers, dur_src=src))
        results = out

    print("| 集 | 行数 | 超长行 | CPS超标行 | 时长越界 | 结论 | 修法 |")
    print("|---|---|---|---|---|---|---|")
    for r in results:
        name = os.path.basename(r["file"])
        tail_bad = [v for v in r["violations"] if "尾部越界" in v["detail"]]
        fixes = []
        if r["over_len"]:
            fixes.append("拆行至≤%d字" % MAX_CHARS_PER_LINE)
        if r["cps_bad"]:
            fixes.append("补停留/CPS≤%.0f" % MAX_CPS)
        if r["dur_bad"]:
            fixes.append("停留归位[%.2f,%.2f]" % (MIN_CUE_S, MAX_CUE_S))
        if r["punct_bad"]:
            fixes.append("半角→全角")
        if r["typos"]:
            fixes.append("错字→" + "/".join(sorted({t["right"] for t in r["typos"]})))
        if tail_bad:
            fixes.append("末条收到容器内")
        if r["line_overflow"]:
            fixes.append("折行≤%d行" % MAX_CUE_LINES)
        if any(v["rule"] == "R7b" for v in r["violations"]):
            fixes.append("按同源组多数派校正")
        print("| %s | %d | %d | %d | %d | %s | %s |" % (
            name, r["cues"], len(r["over_len"]), len(r["cps_bad"]),
            len(r["dur_bad"]) + len(tail_bad),
            r["verdict"], "；".join(fixes) if fixes else "—"))

    npass = sum(1 for r in results if r["verdict"] == "PASS")
    print("\n合计 %d 份：PASS %d / FAIL %d"
          % (len(results), npass, len(results) - npass))
    if groups:
        print("同源组（时间栅格一致，≥3 份）：%d 组" % len(groups))
    for r in results:
        if r["verdict"] == "FAIL":
            print("\n--- %s 硬违规 ---" % os.path.basename(r["file"]))
            for v in r["violations"]:
                print("  %s %s" % (v["rule"], v["detail"]))

    if args.json:
        os.makedirs(os.path.dirname(args.json) or ".", exist_ok=True)
        json.dump({"ts": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
                   "spec": "QUALITY-SPEC-v2 §7 + subs_qc v1",
                   "thresholds": {"max_chars_per_line": MAX_CHARS_PER_LINE,
                                  "min_cue_s": MIN_CUE_S, "max_cue_s": MAX_CUE_S,
                                  "max_cps": MAX_CPS,
                                  "tail_tolerance_s": TAIL_TOLERANCE_S},
                   "results": results},
                  open(args.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("\nJSON → %s" % args.json)

    sys.exit(0 if npass == len(results) else 1)


if __name__ == "__main__":
    main()
