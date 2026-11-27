#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""line_gate.py - 短剧/游戏/策略三条线各自的闸（2026-11-02 补）。

为什么：此前只有 MV 有闸，"不过线不许扩"落不到别的线。这里给三条线各一个
便宜、可复跑的机检，判据写死在代码里，输出符合 VERDICT 契约（可复现、带指纹）。

用法：
  python3 line_gate.py drama  <成片.mp4>  [--json out.json]
  python3 line_gate.py game   <包.html|apk|zip> [--json out.json]
  python3 line_gate.py strategy <结论.json> [--json out.json]
退出码：0 通过 / 1 不通过 / 2 用法错误
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

VERSION = "line-gate-1.0-20261102"
FFPROBE = shutil.which("ffprobe") or "/Users/junsheng.sun/bin/ffprobe"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def probe(path):
    r = subprocess.run([FFPROBE, "-v", "error", "-print_format", "json",
                        "-show_format", "-show_streams", path],
                       capture_output=True, text=True, timeout=120)
    return json.loads(r.stdout or "{}")


def gate_drama(path):
    p = probe(path)
    streams = p.get("streams") or []
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    has_video = any(s.get("codec_type") == "video" for s in streams)
    dur = float((p.get("format") or {}).get("duration") or 0)
    checks = [
        {"name": "有画面", "value": has_video, "pass": has_video},
        {"name": "有音轨", "value": has_audio, "pass": has_audio},
        {"name": "时长 30-600 秒", "value": round(dur, 1), "pass": 30 <= dur <= 600},
    ]
    # 响度：-14 LUFS 附近（平台标准），过响或过轻都不发
    if has_audio:
        try:
            r = subprocess.run([shutil.which("ffmpeg") or "/Users/junsheng.sun/bin/ffmpeg",
                                "-hide_banner", "-i", path, "-af", "loudnorm=print_format=json",
                                "-f", "null", "-"], capture_output=True, text=True, timeout=600)
            blob = r.stderr[r.stderr.rfind("{"):]
            lufs = float(json.loads(blob).get("input_i"))
            checks.append({"name": "响度 -18~-10 LUFS", "value": lufs,
                           "pass": -18 <= lufs <= -10})
        except Exception:
            checks.append({"name": "响度可测", "value": None, "pass": False})
    return checks


def gate_game(path):
    size_mb = round(os.path.getsize(path) / 1048576.0, 2)
    checks = [{"name": "包存在且非空", "value": size_mb, "pass": size_mb > 0.2},
              {"name": "包体 <80MB", "value": size_mb, "pass": size_mb < 80}]
    if path.endswith(".html"):
        txt = open(path, encoding="utf-8", errors="ignore").read()
        checks += [{"name": "有 canvas 或脚本", "value": ("<canvas" in txt or "<script" in txt),
                    "pass": "<canvas" in txt or "<script" in txt},
                   {"name": "无外链依赖", "value": ("http://" not in txt and "https://" not in txt),
                    "pass": "http://" not in txt and "https://" not in txt}]
    return checks


STRATEGY_KEYS = ["annual_return", "max_drawdown", "sharpe", "sample_period", "trades"]


def gate_strategy(path):
    try:
        d = json.load(open(path, encoding="utf-8-sig"))
    except Exception:
        return [{"name": "结论可解析", "value": False, "pass": False}]
    flat = json.dumps(d, ensure_ascii=False)
    checks = [{"name": "五个数齐全", "value": flat[:60],
               "pass": all(k in flat for k in STRATEGY_KEYS)}]
    try:
        dd = abs(float(d.get("max_drawdown") or d.get("max_dd") or 0))
        checks.append({"name": "回撤在合理区间(<60%)", "value": dd, "pass": dd < 60})
    except (TypeError, ValueError):
        checks.append({"name": "回撤可读", "value": None, "pass": False})
    return checks


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    kind, path = argv[0], argv[1]
    if not os.path.exists(path):
        print("找不到文件：%s" % path)
        return 2
    fn = {"drama": gate_drama, "game": gate_game, "strategy": gate_strategy}.get(kind)
    if not fn:
        print("未知线：%s（drama/game/strategy）" % kind)
        return 2
    checks = fn(path)
    ok = all(c["pass"] for c in checks)
    v = {"gate": "%s-gate" % kind, "input": path, "input_sha": sha(path),
         "checks": checks, "pass": ok, "tool_version": VERSION,
         "ts": __import__("datetime").datetime.now().isoformat(timespec="seconds")}
    out = ""
    for i, a in enumerate(argv):
        if a == "--json" and i + 1 < len(argv):
            out = argv[i + 1]
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        json.dump(v, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%s %s" % (v["gate"], "PASS" if ok else "FAIL"))
    for c in checks:
        print("  %s %-22s %s" % ("✓" if c["pass"] else "✗", c["name"], c["value"]))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))