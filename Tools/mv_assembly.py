#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mv_assembly.py — 装配脚本的强制骨架（库，不是命令）。

为什么存在：2026-11-25 复盘证明，返工的最大来源不是"做错"，而是"新的装配脚本
不知道上一版修过什么"。所有已知的坑都在这里封死，新脚本 import 即可。

三条强制：
  1. 音轨必须过 `master_audio()`（两遍 loudnorm + alimiter + 精确截断），
     禁 `-c:a copy`（v7 修好的 −1.1 dBTP 就是被 copy 弄回 +2.1 的）。
  2. 出片必须过 `post_check()`（跑回归闸），FAIL 直接抛异常，不许交付。
  3. 有 EDL 必须过 `assert_edl_match()`（切点对账），防"假完成"。

用法：
    from mv_assembly import master_audio, post_check, assert_frames

    master_audio(src_with_audio, "audio.m4a", dur=30.0)
    # ... ffmpeg 装配时用 -i audio.m4a -c:a copy（这是合法的：音频已经母带过）
    assert_frames(out, expect=720, dur=30.0)
    post_check(out, edl="EDIT-PLAN.json", expect_frames=720)

注意：`master_audio` 之后再用 `-c:a copy` 是**正确**的；被禁的是"从原始源直接 copy"。
"""
import json
import os
import subprocess
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FF = "ffmpeg"
FP = "ffprobe"
HERE = os.path.dirname(os.path.abspath(__file__))


class AssemblyGateError(RuntimeError):
    """装配闸失败。捕获它没有意义——正确做法是修，不是跳过。"""


def _run(cmd, label=""):
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise AssemblyGateError("[%s] ffmpeg rc=%d\n%s" % (label, r.returncode,
                                                           (r.stderr or "")[-1200:]))
    return r


def master_audio(src, out, dur, lufs=-14.3, tp=-2.6, limiter=0.74, bitrate="256k"):
    """把源音轨做成母带：loudnorm 两遍 + aresample + alimiter + 精确截断 + AAC。

    经验值（2026-11-25 实测）：
      tp=-2.6 / limiter=0.74 → 实测输出 −2.0 dBTP（AAC 过冲 0.6 dB）
      若用 tp=-1.0 / limiter=0.891 → 实测 −0.3 dBTP，**不合格**
    """
    if not os.path.exists(src):
        raise AssemblyGateError("源不存在: " + src)

    # pass1：量测
    r = _run([FF, "-hide_banner", "-nostats", "-i", src,
              "-af", "loudnorm=I=%s:TP=%s:LRA=11:print_format=json" % (lufs, tp),
              "-f", "null", "-"], "loudnorm-pass1")
    measured = None
    txt = (r.stderr or "")
    start = txt.rfind("{")
    end = txt.rfind("}")
    if start >= 0 and end > start:
        try:
            measured = json.loads(txt[start:end + 1])
        except Exception:
            measured = None

    if measured:
        af = ("loudnorm=I=%s:TP=%s:LRA=11:measured_I=%s:measured_TP=%s:"
              "measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
              "aresample=48000,alimiter=limit=%s:level=false,atrim=0:%s"
              % (lufs, tp, measured["input_i"], measured["input_tp"],
                 measured["input_lra"], measured["input_thresh"],
                 measured.get("target_offset", "0.0"), limiter, dur))
    else:
        # 量测失败时退回单遍（会在回执里提示，不静默）
        print("[master_audio] WARN loudnorm pass1 解析失败，退回单遍动态模式", flush=True)
        af = ("loudnorm=I=%s:TP=%s:LRA=11,aresample=48000,"
              "alimiter=limit=%s:level=false,atrim=0:%s" % (lufs, tp, limiter, dur))

    _run([FF, "-y", "-v", "error", "-i", src, "-vn", "-af", af,
          "-c:a", "aac", "-b:a", bitrate, "-t", str(dur), out], "master_audio")
    return out


def verify_audio(path, max_dbtp=-1.0, lufs_target=-14.0, lufs_tol=1.5):
    """出片后核音轨。返回 dict；不达标抛异常。"""
    r = subprocess.run([FF, "-hide_banner", "-nostats", "-i", path,
                        "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    s = r.stderr or ""
    import re
    obs = {}
    m = re.findall(r"(?m)^\s*I:\s+(-?[\d.]+) LUFS", s)
    if m:
        obs["lufs"] = float(m[-1])
    m = re.findall(r"(?m)^\s*Peak:\s+(-?[\d.]+) dBFS", s)
    if m:
        obs["true_peak"] = float(m[-1])
    if obs.get("true_peak") is not None and obs["true_peak"] > max_dbtp:
        raise AssemblyGateError("真峰 %.1f dBTP > %.1f（削波）" % (obs["true_peak"], max_dbtp))
    if obs.get("lufs") is not None and abs(obs["lufs"] - lufs_target) > lufs_tol:
        raise AssemblyGateError("响度 %.1f 偏离 %.1f±%.1f" % (obs["lufs"], lufs_target, lufs_tol))
    return obs


def assert_frames(path, expect, dur, tol_frames=0, tol_dur=0.05):
    """帧数/时长断言。这是 setpts 系数写反（720→536）唯一能自动抓到的地方。"""
    r = subprocess.run([FP, "-v", "error", "-count_frames",
                        "-select_streams", "v:0",
                        "-show_entries", "stream=nb_read_frames",
                        "-show_entries", "format=duration",
                        "-of", "json", path],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    d = json.loads(r.stdout or "{}")
    st = (d.get("streams") or [{}])[0]
    n = int(st.get("nb_read_frames") or 0)
    got_dur = float(d.get("format", {}).get("duration") or 0)
    errs = []
    if abs(n - expect) > tol_frames:
        errs.append("帧数 %d ≠ %d" % (n, expect))
    if abs(got_dur - dur) > tol_dur:
        errs.append("时长 %.3f ≠ %.3f" % (got_dur, dur))
    if errs:
        raise AssemblyGateError("；".join(errs))
    return {"frames": n, "dur": round(got_dur, 3)}


def assert_edl_match(film, edl, tolerance=0.12, min_ratio=0.8):
    """切点对账：成片反测切点 vs 剪辑表。防「三个新版都是旧结构」。"""
    gate = os.path.join(HERE, "mv_regression_gate.py")
    r = subprocess.run([sys.executable, gate, "--film", film, "--edl", edl,
                        "--only", "R-07"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise AssemblyGateError("切点对账失败（成片与剪辑表不是同一版）\n" + (r.stdout or "")[-600:])
    return True


def post_check(film, edl="", expect_frames=0, json_out="", allow_fail=()):
    """跑回归闸。FAIL 抛异常；allow_fail 里列的 id 只警告不抛（慎用，须写进回执）。"""
    gate = os.path.join(HERE, "mv_regression_gate.py")
    cmd = [sys.executable, gate, "--film", film]
    if edl:
        cmd += ["--edl", edl]
    if expect_frames:
        cmd += ["--expect-frames", str(expect_frames)]
    if json_out:
        cmd += ["--json", json_out]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "")
    print(out, flush=True)
    if r.returncode == 0:
        return True
    if allow_fail:
        bad = [ln for ln in out.splitlines() if " FAIL " in ln
               and not any(a in ln for a in allow_fail)]
        if not bad:
            print("[post_check] 仅剩白名单项 FAIL（已记入回执）", flush=True)
            return True
    raise AssemblyGateError("回归闸 FAIL；详细见上方输出与 %s" % (json_out or "stdout"))


if __name__ == "__main__":
    print(__doc__)
