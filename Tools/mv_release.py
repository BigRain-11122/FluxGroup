#!/usr/bin/env python3
"""mv_release.py - 一条命令出发布件（出厂席的"每片必跑"固化）

把 2026-11-08 手工跑的流程串成一条：
  1) 规格核验（帧数/帧率/时长/音轨）
  2) 黑帧 + 定格检测（ffmpeg 双路）
  3) 剪辑索引（PySceneDetect → CSV + OTIO）
  4) 响度与真峰值；超线则出 _pub 版（视频流 copy，只处理音频）
  5) 交付闸（带重演白名单与设计静止窗）
  6) 汇总成 <stem>-qa.json，PASS 才给发布路径

用法:
  python Tools/mv_release.py <video> [--whitelist f.json] [--card a:b ...]
                              [--gate-json out.json] [--skip-gate] [--poster t]
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "Tools")
LUFS_TARGET, TP_LIMIT = -14.0, -1.0


def run(args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_entries",
             "stream=codec_type,width,height,r_frame_rate,nb_frames",
             "-show_entries", "format=duration", "-of", "json", path])
    try:
        d = json.loads(r.stdout)
    except Exception:
        return {}
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    num, _, den = (v.get("r_frame_rate") or "0/1").partition("/")
    fps = (float(num) / float(den)) if float(den or 0) else 0.0
    return {"w": v.get("width"), "h": v.get("height"), "fps": round(fps, 3),
            "frames": int(v.get("nb_frames") or 0),
            "duration": round(float(d.get("format", {}).get("duration", 0)), 3),
            "has_audio": a is not None}


def freeze_black(path, logdir):
    log = os.path.join(logdir, "freeze_black.log")
    with open(log, "w", encoding="utf-8") as fh:
        subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-an", "-vf",
                        "blackdetect=d=0.1:pic_th=0.98:pix_th=0.10,"
                        "freezedetect=n=0.003:d=0.4", "-f", "null", "-"],
                       cwd=ROOT, stdout=subprocess.DEVNULL, stderr=fh)
    txt = open(log, encoding="utf-8", errors="replace").read()
    blacks = [float(m) for m in re.findall(r"black_start: ([\d.]+)", txt)]
    freezes = []
    cur = None
    for line in txt.splitlines():
        m = re.search(r"freeze_start: ([\d.]+)", line)
        if m:
            cur = float(m.group(1))
        m = re.search(r"freeze_duration: ([\d.]+)", line)
        if m and cur is not None:
            freezes.append((cur, float(m.group(1))))
            cur = None
    return blacks, freezes


def loudness(path, logdir):
    log = os.path.join(logdir, "loud.log")
    with open(log, "w", encoding="utf-8") as fh:
        subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn",
                        "-af", "ebur128=peak=true", "-f", "null", "-"],
                       cwd=ROOT, stdout=subprocess.DEVNULL, stderr=fh)
    txt = open(log, encoding="utf-8", errors="replace").read()
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", txt)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", txt)
    return (float(i[-1]) if i else None), (float(tp[-1]) if tp else None)


def normalize_audio(src, dst):
    r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src,
             "-c:v", "copy", "-af",
             f"loudnorm=I={LUFS_TARGET}:TP=-2:LRA=9,alimiter=limit=0.84:level=false",
             "-c:a", "aac", "-b:a", "320k", dst])
    return r.returncode == 0


def cutindex(path, outdir, stem):
    csv_p = os.path.join(outdir, f"{stem}-cutindex.csv")
    r = run([sys.executable, os.path.join(TOOLS, "mv_cutindex.py")
             if os.path.exists(os.path.join(TOOLS, "mv_cutindex.py")) else "", path, csv_p])
    if not os.path.exists(csv_p):
        # 退化：用内联 scenedetect
        try:
            from scenedetect import open_video, SceneManager, ContentDetector
            import csv as _csv
            v = open_video(path)
            sm = SceneManager()
            sm.add_detector(ContentDetector(threshold=27.0))
            sm.detect_scenes(v)
            scenes = sm.get_scene_list()
            with open(csv_p, "w", newline="", encoding="utf-8") as fh:
                w = _csv.writer(fh)
                w.writerow(["shot", "start_s", "end_s", "dur_s"])
                for i, (s, e) in enumerate(scenes, 1):
                    w.writerow([i, round(s.seconds, 3), round(e.seconds, 3),
                                round(e.seconds - s.seconds, 3)])
            return csv_p, len(scenes)
        except Exception as ex:
            print("cutindex skipped:", ex)
            return None, 0
    return csv_p, sum(1 for _ in open(csv_p, encoding="utf-8")) - 1


def gate(path, whitelist, cards, gate_json):
    cmd = [sys.executable, os.path.join(TOOLS, "mv_delivery_gate.py"), path,
           "--json", gate_json]
    if whitelist and os.path.exists(whitelist):
        cmd += ["--whitelist", whitelist]
    for c in cards:
        cmd += ["--card", c]
    r = run(cmd)
    if r.returncode != 0 and not (r.stdout or "").strip():
        print("gate    : 子进程异常 rc=%s" % r.returncode)
        print((r.stderr or "")[-500:])
    try:
        return json.load(open(gate_json, encoding="utf-8")), r.stdout
    except Exception:
        # 闸未落 json 时，退化为解析 stdout 的 VERDICT，避免把"没写文件"当成崩溃
        m = re.search(r"VERDICT:\s*(\w+)", r.stdout or "")
        verdict = m.group(1) if m else "ERROR"
        fails = [l.strip()[5:].strip() for l in (r.stdout or "").splitlines()
                 if l.strip().startswith("FAIL ")]
        return {"verdict": verdict, "fails": fails, "_from_stdout": True}, r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--whitelist", default="")
    ap.add_argument("--card", action="append", default=[])
    ap.add_argument("--gate-json", default="")
    ap.add_argument("--skip-gate", action="store_true")
    ap.add_argument("--poster", type=float, default=0.0)
    a = ap.parse_args()

    path = os.path.abspath(a.video)
    if not os.path.exists(path):
        sys.exit("no such file: " + path)
    stem = os.path.splitext(os.path.basename(path))[0]
    outdir = os.path.dirname(path)
    work = tempfile.mkdtemp(prefix="mvrelease_")

    print("=" * 60)
    info = probe(path)
    print("spec    :", info)

    blacks, freezes = freeze_black(path, work)
    print(f"black   : {len(blacks)} 段 {blacks[:5]}")
    print(f"freeze  : {len(freezes)} 处 {freezes[:5]}")

    csv_p, shots = cutindex(path, outdir, stem)
    print(f"cutindex: {shots} 镜 -> {csv_p}")

    lufs, tp = loudness(path, work)
    print(f"loud    : I={lufs} LUFS  TP={tp} dBFS")
    publish = path
    if lufs is not None and tp is not None and (tp > TP_LIMIT or abs(lufs - LUFS_TARGET) > 1.5):
        pub = os.path.join(outdir, stem + "_pub.mp4")
        print("audio   : 超线 -> 生成", pub)
        if normalize_audio(path, pub):
            publish = pub
            lufs, tp = loudness(pub, work)
            print(f"loud(*) : I={lufs} LUFS  TP={tp} dBFS")
        else:
            print("audio   : 归一失败，保留原音轨")

    if a.poster > 0:
        pj = os.path.join(outdir, f"{stem}-poster-{a.poster:g}s.jpg")
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(a.poster),
             "-i", path, "-frames:v", "1", "-q:v", "2", pj])
        print("poster  :", pj)

    verdict, gate_out = ("SKIPPED", "")
    gate_json = a.gate_json or os.path.join(
        ROOT, "cph4", "fleet", "queue-receipts", f"{stem}-gate.json")
    if not a.skip_gate:
        g, gate_out = gate(path, a.whitelist, a.card, gate_json)
        verdict = g.get("verdict", "ERROR")
        print("gate    :", verdict)
        for f in g.get("fails", []):
            print("   fail :", f)

    qa = {"file": path, "spec": info, "black_segments": blacks,
          "freezes": freezes, "shots": shots, "cutindex": csv_p,
          "loudness": {"I": lufs, "TP": tp}, "publish_file": publish,
          "gate": verdict, "gate_json": gate_json}
    qa_p = os.path.join(outdir, f"{stem}-qa.json")
    json.dump(qa, open(qa_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    shutil.rmtree(work, ignore_errors=True)

    print("=" * 60)
    print("QA      :", qa_p)
    print("PUBLISH :", publish if verdict in ("PASS", "SKIPPED") else "(gate not PASS)")
    return 0 if verdict in ("PASS", "SKIPPED") else 1


if __name__ == "__main__":
    sys.exit(main())