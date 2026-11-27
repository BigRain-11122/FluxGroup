# -*- coding: utf-8 -*-
"""face_video_collect.py — 从视频源抽帧补素材（YouTube/剧集/写真花絮），网络+CPU，不碰 GPU。

为什么需要它（2026-11-18）：
  图片搜索引擎（360）对冷门人物/日韩老艺人命中极差，raw 常年停在 20-40 张。
  但视频源里同一个人会连续出现几十秒到几分钟，抽帧一次能拿几十张多角度素材——
  这是图片搜索给不了的密度。实测 yt-dlp 在本机：B站搜索被 412 挡（需 cookie），
  YouTube 直连可用，且老 MV/早期采访/剧集片段都有。

管线：搜索 → 只下 480p 短片 → ffmpeg 按 fps 抽帧 → 逐帧过 face_lora_prep 的闸 → 合格件入 raw。

用法：
  py Tools/face_video_collect.py --person 徐若瑄 --alias "Vivian Hsu" --max-videos 4
  py Tools/face_video_collect.py --person 中谷美纪 --min-year 1995 --fps 0.4
"""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

# YouTube 标题常带 emoji/日文假名，Windows 控制台默认 GBK，print 会抛 UnicodeEncodeError
# 把整个进程打死（实测首跑即崩在"下载失败"的日志行上）。统一按 UTF-8 输出。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup"
TOOLS = os.path.join(ROOT, "Tools")
FACES = os.path.join(ROOT, "media", "faces")
sys.path.insert(0, TOOLS)
import face_lora_prep as GATE  # noqa: E402

YTDLP = r"C:\Users\sjs20\AppData\Local\Programs\Python\Python314\Scripts\yt-dlp.exe"
FFMPEG = r"C:\Users\sjs20\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
IMG = (".jpg", ".jpeg", ".png", ".webp")

# 视频类型词：MV/采访/写真花絮/剧集，这几类才会给"同一个人长时间占画面"
TYPE_WORDS = {
    "mv": "{n} MV",
    "mv_cn": "{n} 音乐录影带",
    "interview": "{n} interview",
    "interview_cn": "{n} 采访",
    "photoshoot": "{a} photoshoot",
    "drama": "{n} 片段",
    "drama_en": "{a} movie scene",
}


def run(cmd, timeout=1800, quiet=True):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout,
                       creationflags=0x08000000 if os.name == "nt" else 0)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out


def search(query, n=6):
    """返回 [(url, title, duration)]；只保留 30s~25min 的条目（太短没料，太长费时）。"""
    rc, out = run([YTDLP, "--no-warnings", "--flat-playlist", "--no-playlist",
                   "--print", "%(webpage_url)s\t%(title)s\t%(duration)s",
                   "ytsearch%d:%s" % (n, query)], timeout=180)
    rows = []
    for ln in out.splitlines():
        parts = ln.split("\t")
        if len(parts) < 3 or not parts[0].startswith("http"):
            continue
        try:
            dur = float(parts[2])
        except ValueError:
            continue
        if 30 <= dur <= 1500:
            rows.append((parts[0], parts[1][:80], dur))
    return rows


def grab(url, dst_dir, max_sec=600):
    """下 480p 视频流（不要音频——抽帧用不上，省一半带宽和时间）。

    2026-11-18 实锚：YouTube 该视频所有格式都是 "video only"（bv/m3u8），
    用 `best[height<=480]` 会报 "Requested format is not available"——
    best 指的是音视频合一格式，这里根本不存在。必须用 bv*（bestvideo）。
    """
    tpl = os.path.join(dst_dir, "%(id)s.%(ext)s")
    cmd = [YTDLP, "--no-warnings", "--no-playlist",
           # 480p 实测：MV 里的中景人脸只有 100-150px，全被 face_px>=200 的闸拒掉（59 帧入 0 张）。
           # 720p 是能让人脸过尺寸门的最低档。
           "-f", "bv*[height<=720]/bv*[height<=1080]/b[height<=720]/bv*/b",
           "--download-sections", "*0-%d" % max_sec,
           "--force-keyframes-at-cuts",
           "-o", tpl, url]
    rc, out = run(cmd, timeout=900)
    files = [os.path.join(dst_dir, f) for f in os.listdir(dst_dir)
             if f.lower().endswith((".mp4", ".webm", ".mkv", ".flv"))]
    return files[0] if files else None


def extract(video, out_dir, fps=0.5):
    os.makedirs(out_dir, exist_ok=True)
    rc, out = run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
                   "-i", video, "-vf", "fps=%.2f" % fps,
                   "-q:v", "2", os.path.join(out_dir, "f_%05d.jpg")], timeout=900)
    return rc == 0


def admit(frame, raw_dir, hashes):
    """逐帧过闸：合格且与已有不重复才入 raw，命名用内容哈希（跨轮次天然去重）。"""
    with open(frame, "rb") as f:
        data = f.read()
    h = hashlib.sha1(data).hexdigest()
    if h in hashes:
        return None
    dst = os.path.join(raw_dir, "%s.jpg" % h[:12])
    if os.path.exists(dst):
        return None
    rep = GATE.evaluate(frame)
    # os.replace 跨卷会抛 WinError 17（temp 目录与工作目录不在同一卷），必须用 shutil.move
    shutil.move(frame, dst)
    if rep["verdict"] == "REJECT":
        os.remove(dst)
        return None
    hashes.add(h)
    return rep["face_px"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--person", required=True)
    ap.add_argument("--alias", default="", help="英文名/原名，逗号分隔")
    ap.add_argument("--types", default="mv,interview,photoshoot,drama")
    ap.add_argument("--per-type", type=int, default=3, help="每类取几个视频")
    ap.add_argument("--fps", type=float, default=0.5, help="抽帧频率（0.5=每2秒一帧）")
    ap.add_argument("--max-sec", type=int, default=420, help="每个视频只取前 N 秒")
    ap.add_argument("--max-videos", type=int, default=6)
    ap.add_argument("--out", default="", help="默认 media/faces/<key>，需与批次同名")
    a = ap.parse_args()

    key = a.out or infer_key(a.person)
    raw_dir = os.path.join(FACES, key, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    names = [a.person] + [x.strip() for x in a.alias.split(",") if x.strip()]
    queries = []
    for t in [x.strip() for x in a.types.split(",") if x.strip()]:
        tpl = TYPE_WORDS.get(t)
        if not tpl:
            continue
        for i, nm in enumerate(names):
            queries.append(tpl.format(n=nm, a=nm if i else (names[1] if len(names) > 1 else nm)))

    seen_q, uniq = set(), []
    for q in queries:
        if q not in seen_q:
            seen_q.add(q)
            uniq.append(q)

    cands = []
    for q in uniq:
        got = search(q, a.per_type * 2)
        print("[search] %s → %d 条" % (q, len(got)), flush=True)
        cands.extend(got)
        if len(cands) >= a.max_videos * 3:
            break

    seen_u, videos = set(), []
    for u, t, d in cands:
        if u not in seen_u:
            seen_u.add(u)
            videos.append((u, t, d))
    videos = videos[:a.max_videos]
    print("候选视频 %d 个，开始下载抽帧" % len(videos), flush=True)

    hashes = set()
    admitted = 0
    for i, (u, title, dur) in enumerate(videos, 1):
        t0 = time.time()
        with tempfile.TemporaryDirectory() as td:
            vid = grab(u, td, a.max_sec)
            if not vid:
                print("  [%d/%d] 下载失败 %s" % (i, len(videos), title), flush=True)
                continue
            fr = os.path.join(td, "frames")
            if not extract(vid, fr, a.fps):
                print("  [%d/%d] 抽帧失败 %s" % (i, len(videos), title), flush=True)
                continue
            frames = sorted(os.listdir(fr))
            got = 0
            for fn in frames:
                px = admit(os.path.join(fr, fn), raw_dir, hashes)
                if px:
                    got += 1
            admitted += got
            print("  [%d/%d] %-42s 抽 %d 帧 → 入 %d 张 · %.0fs"
                  % (i, len(videos), title[:42], len(frames), got, time.time() - t0), flush=True)

    total = sum(1 for f in os.listdir(raw_dir) if f.lower().endswith(IMG))
    print("\n合计本次新增 %d 张，%s 现有 raw %d 张" % (admitted, key, total), flush=True)
    return 0 if admitted else 1


def infer_key(person):
    """把人名映射回批次 key（ql01/tm03…）；找不到就原样用人名当目录。"""
    pool = os.path.join(ROOT, "cph4", "fleet", "mv-album-001-jay", "casting-pool-v1.json")
    try:
        import json
        d = json.load(open(pool, encoding="utf-8"))
        for fam in d["families"]:
            for i, nm in enumerate(fam.get("internal_index_only") or [], 1):
                if nm == person or nm.lower() == person.lower():
                    return "%s%02d" % (fam["id"], i)
    except Exception:
        pass
    return re.sub(r"[^\w]", "_", person)


if __name__ == "__main__":
    sys.exit(main())
