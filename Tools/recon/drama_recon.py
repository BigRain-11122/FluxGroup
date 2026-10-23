#!/usr/bin/env python3
"""drama_recon.py — 短剧/漫剧结构与工艺量化拆解（离线、可复跑）

用法:
  python Tools/recon/drama_recon.py <video> [--out <dir>] [--scene 0.30] [--frames 12]

产出:
  <out>/<stem>.recon.json   全量量化件
  <out>/<stem>.recon.md     人读摘要
  <out>/frames/             等距抽帧 + 前 30 秒密集抽帧（用于字幕/景别人工判读）

依赖: ffmpeg/ffprobe（必需）; faster-whisper（可选，转写）; numpy/Pillow（可选，亮度分析）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import statistics
import sys
from pathlib import Path

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
FFPROBE = os.environ.get("FFPROBE", "ffprobe")


def run(cmd: list[str], binary: bool = False):
    p = subprocess.run(cmd, capture_output=True, text=not binary, errors="replace")
    if p.returncode != 0:
        raise RuntimeError(f"cmd failed ({p.returncode}): {' '.join(cmd[:6])}\n{p.stderr[-800:]}")
    # ffmpeg 的 showinfo/metadata 日志在 stderr，必须合并，否则解析恒为空
    return (p.stdout or "") + (p.stderr or "")


def probe(path: Path) -> dict:
    out = run([FFPROBE, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)])
    return json.loads(out)


def scene_scores(path: Path) -> list[tuple[float, float]]:
    """单次遍历取逐帧场景分，返回 [(pts_time, score)]。

    低码率竖屏短剧的硬切分数常低于 0.3，固定阈值会漏检；
    这里取全量分布，由调用方按阈值统计。
    """
    out = run([
        FFMPEG, "-hide_banner", "-i", str(path), "-vf",
        "select='gte(scene,0)',metadata=print:key=lavfi.scene_score",
        "-f", "null", "-",
    ], binary=False)
    pairs: list[tuple[float, float]] = []
    t = None
    for line in out.splitlines():
        m = re.search(r"pts_time:([0-9.]+)", line)
        if m:
            t = float(m.group(1))
            continue
        m = re.search(r"lavfi\.scene_score=([0-9.]+)", line)
        if m and t is not None:
            pairs.append((t, float(m.group(1))))
    return pairs


def cuts_by_threshold(pairs: list[tuple[float, float]], thresholds: list[float]) -> dict[str, list[float]]:
    return {f"{th:.2f}": [round(t, 3) for t, s in pairs if s >= th] for th in thresholds}


def loudness(path: Path) -> dict | None:
    try:
        out = run([FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0",
                   "-af", "loudnorm=print_format=json", "-f", "null", "-"])
    except RuntimeError:
        return None
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", out, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def extract_frames(path: Path, outdir: Path, duration: float, n: int) -> list[str]:
    outdir.mkdir(parents=True, exist_ok=True)
    made: list[str] = []
    # 等距关键帧
    for i in range(n):
        t = duration * (i + 0.5) / n
        f = outdir / f"even_{i:02d}_{t:07.1f}s.jpg"
        if not f.exists():
            run([FFMPEG, "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(path),
                 "-frames:v", "1", "-q:v", "3", str(f)])
        if f.exists():
            made.append(str(f))
    # 前 30 秒密集帧（钩子/字幕判读）
    for t in [x * 2.0 for x in range(1, 16)]:
        if t >= duration:
            break
        f = outdir / f"hook_{t:05.1f}s.jpg"
        if not f.exists():
            run([FFMPEG, "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(path),
                 "-frames:v", "1", "-q:v", "3", str(f)])
        if f.exists():
            made.append(str(f))
    return made


def transcribe(path: Path) -> dict | None:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception:
        return None
    model_size = os.environ.get("RECON_WHISPER_MODEL", "small")
    try:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(path), vad_filter=True, beam_size=1)
        segs = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segments]
    except Exception as exc:  # av/torch 版本漂移不应阻断量化主链
        return {"error": f"{type(exc).__name__}: {exc}", "segments": []}
    total_chars = sum(len(s["text"]) for s in segs)
    return {"language": info.language, "duration": round(info.duration, 1), "segments": segs,
            "chars": total_chars,
            "chars_per_min": round(total_chars / max(info.duration / 60, 0.01), 1)}


def pct(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    k = max(0, min(len(s) - 1, int(round((len(s) - 1) * p))))
    return round(s[k], 2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", default=None)
    ap.add_argument("--scene", type=float, default=0.30)
    ap.add_argument("--frames", type=int, default=12)
    ap.add_argument("--no-whisper", action="store_true")
    args = ap.parse_args()

    path = Path(args.video).resolve()
    if not path.exists():
        print(f"not found: {path}", file=sys.stderr)
        return 2
    outdir = Path(args.out) if args.out else path.parent / "recon"
    outdir.mkdir(parents=True, exist_ok=True)

    meta = probe(path)
    fmt = meta.get("format", {})
    v = next((s for s in meta.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in meta.get("streams", []) if s.get("codec_type") == "audio"), {})
    duration = float(fmt.get("duration") or v.get("duration") or 0)

    pairs = scene_scores(path)
    ths = [0.10, 0.15, 0.20, 0.25, 0.30]
    by_th = cuts_by_threshold(pairs, ths)
    cut_counts = {k: len(v) for k, v in by_th.items()}
    # 标定：选最接近 3s/镜 的阈值；若都偏离，取 0.15 兜底
    target = max(duration / 3.0, 1)
    pick = min(ths, key=lambda th: abs(len(by_th[f"{th:.2f}"]) - target))
    if not (duration / 120 <= len(by_th[f"{pick:.2f}"]) <= duration / 0.5):
        pick = 0.15
    cuts = by_th[f"{pick:.2f}"]
    bounds = [0.0] + [c for c in cuts if 0 < c < duration] + [duration]
    shots = [round(bounds[i + 1] - bounds[i], 2) for i in range(len(bounds) - 1)]
    shots = [s for s in shots if s > 0.04]

    frames = extract_frames(path, outdir / "frames", duration, args.frames)
    loud = loudness(path)
    tr = None if args.no_whisper else transcribe(path)

    result = {
        "source": str(path),
        "file_mb": round(path.stat().st_size / 1048576, 2),
        "format": {
            "duration_s": round(duration, 2),
            "duration_hms": f"{int(duration // 3600):02d}:{int(duration % 3600 // 60):02d}:{int(duration % 60):02d}",
            "bitrate_kbps": round(int(fmt.get("bit_rate", 0)) / 1000, 1),
            "size_mb": round(float(fmt.get("size", 0) or 0) / 1048576, 2),
        },
        "video": {
            "codec": v.get("codec_name"), "width": v.get("width"), "height": v.get("height"),
            "fps": v.get("r_frame_rate"), "pix_fmt": v.get("pix_fmt"),
            "bitrate_kbps": round(int(v.get("bit_rate", 0) or 0) / 1000, 1),
        },
        "audio": {
            "codec": a.get("codec_name"), "sample_rate": a.get("sample_rate"),
            "channels": a.get("channels"), "bitrate_kbps": round(int(a.get("bit_rate", 0) or 0) / 1000, 1),
            "loudness": loud,
        },
        "shots": {
            "threshold_used": pick,
            "cut_counts_by_threshold": cut_counts,
            "count": len(shots),
            "median_s": round(statistics.median(shots), 2) if shots else 0,
            "mean_s": round(statistics.fmean(shots), 2) if shots else 0,
            "p10_s": pct(shots, 0.10), "p90_s": pct(shots, 0.90),
            "under_1s_ratio": round(sum(1 for s in shots if s < 1.0) / len(shots), 3) if shots else 0,
            "cuts_per_min": round(len(shots) / max(duration / 60, 0.01), 2),
            "cut_points": cuts,
        },
        "transcript": tr,
        "frames": frames,
        "notes": {
            "静态镜头判定": "P90 < 2s 且 under_1s_ratio > 0.25 = 快切打法；中位 > 3s = 长镜叙事",
            "钩子判定": "首个强场景切点与首句台词时间差 ≤3s 视为开场即冲突",
        },
    }

    jpath = outdir / f"{path.stem}.recon.json"
    jpath.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# 拆解摘要：{path.name}",
        "",
        f"- 时长：{result['format']['duration_hms']}（{result['format']['duration_s']}s）｜文件 {result['file_mb']} MB｜码率 {result['format']['bitrate_kbps']} kbps",
        f"- 画面：{result['video']['width']}x{result['video']['height']} @ {result['video']['fps']}｜{result['video']['codec']}",
        f"- 音频：{result['audio']['codec']} {result['audio']['sample_rate']}Hz {result['audio']['channels']}ch {result['audio']['bitrate_kbps']}kbps",
        f"- 镜头：{result['shots']['count']} 个切点（阈值 {pick:.2f}）｜中位 {result['shots']['median_s']}s｜P90 {result['shots']['p90_s']}s｜<1s 占比 {result['shots']['under_1s_ratio']}｜切点/分 {result['shots']['cuts_per_min']}",
        f"- 分数分布：{json.dumps(cut_counts, ensure_ascii=False)}（用于校准阈值，低码率竖屏剧常见硬切分低于 0.3）",
    ]
    if loud:
        lines.append(f"- 响度：I={loud.get('input_i')} LUFS｜TP={loud.get('input_tp')} dBTP｜LRA={loud.get('input_lra')}")
    if tr and "language" in tr:
        lines.append(f"- 转写：{tr['language']}｜{tr['chars']} 字｜{tr['chars_per_min']} 字/分｜{len(tr['segments'])} 段")
        for s in tr["segments"][:8]:
            lines.append(f"  - [{s['start']:>7.2f}] {s['text']}")
    elif tr:
        lines.append(f"- 转写：失败（{tr.get('error')}）——量化主链不受影响")
    else:
        lines.append("- 转写：未启用（缺 faster-whisper 或 --no-whisper）")
    lines.append(f"- 抽帧：{len(frames)} 张 → {outdir / 'frames'}")
    mpath = outdir / f"{path.stem}.recon.md"
    mpath.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"ok": True, "json": str(jpath), "md": str(mpath),
                      "shots": len(shots), "median_shot_s": result["shots"]["median_s"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())