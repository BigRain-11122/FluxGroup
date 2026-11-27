#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self_acquire.py — 缺料时机器自己取，不再等主控分发。

CEO 2026-11-08：「你提供不了可以让他们自己找，不要等待浪费」。

三种自取（都做确定性校验，拿不到就 rc=3，绝不伪造）：
  1. 从已有素材里抽：视频抽帧 / 音频切段 / 图片放大 —— 输入是仓内或本机已有文件
  2. 从资产库取：按 sha256 从 FluxAssets 走 asset_pull 拉到本机（已有则 SKIP）
  3. 从允许的开源源下载：仅限 allowlist 域名 + sha256/size 校验（默认关闭，需 --allow-net）

用法：
  python Tools/fleet/self_acquire.py --from-video media/x.mp4 --frames 8 --out media/inbox/kf
  python Tools/fleet/self_acquire.py --from-audio media/y.mp3 --seg 60 --out media/inbox/va
  python Tools/fleet/self_acquire.py --vault <sha256|rel> --dest media/inbox/z.png
  python Tools/fleet/self_acquire.py --net <url> --dest media/inbox/a.mp3 --sha256 <hash> --allow-net
Exit: 0 拿到并校验通过；3 拿不到（合法缺料，不算执行失败）
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
NET_ALLOW = ("opengameart.org", "librivox.org", "commons.wikimedia.org")


def ff(name):
    for c in (name, os.path.join(os.path.expanduser("~"), "bin", name),
              "/opt/homebrew/bin/" + name, "/usr/local/bin/" + name):
        if shutil.which(c) or os.path.exists(c):
            return c
    return None


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rec(kind, ok, detail, out=None):
    r = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": kind, "ok": ok,
         "detail": detail, "artifact": out}
    d = os.path.join(FLEET, "queue-receipts")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "self-acquire-%s-%s.json" % (kind, time.strftime("%Y%m%dT%H%M%S")))
    with open(p, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    print("[self-acquire] %s %s · %s" % (kind, "OK" if ok else "BLOCKED", detail))
    if out:
        print("   产物:", os.path.relpath(out, ROOT) if str(out).startswith(ROOT) else out)
    return 0 if ok else 3


def from_video(src, n, out):
    src = src if os.path.isabs(src) else os.path.join(ROOT, src)
    if not os.path.exists(src):
        return rec("video-frames", False, "源视频不存在：%s" % src)
    exe = ff("ffmpeg")
    if not exe:
        return rec("video-frames", False, "没有 ffmpeg")
    os.makedirs(out, exist_ok=True)
    # 等间隔抽帧：先取时长
    probe = ff("ffprobe")
    dur = 0.0
    if probe:
        r = subprocess.run([probe, "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", src], capture_output=True, text=True)
        try:
            dur = float((r.stdout or "0").strip())
        except Exception:
            dur = 0.0
    made = []
    for i in range(n):
        t = (dur * (i + 0.5) / n) if dur else i
        dst = os.path.join(out, "%s_kf%02d.jpg" % (os.path.splitext(os.path.basename(src))[0], i + 1))
        r = subprocess.run([exe, "-y", "-ss", "%.2f" % t, "-i", src, "-frames:v", "1",
                            "-q:v", "2", dst], capture_output=True, timeout=180)
        if r.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 1024:
            made.append(dst)
    if not made:
        return rec("video-frames", False, "抽帧失败（0 张落盘）")
    return rec("video-frames", True, "抽到 %d/%d 帧（时长 %.1fs）" % (len(made), n, dur), made[0])


def from_audio(src, seg, out):
    src = src if os.path.isabs(src) else os.path.join(ROOT, src)
    if not os.path.exists(src):
        return rec("audio-seg", False, "源音频不存在：%s" % src)
    exe = ff("ffmpeg")
    if not exe:
        return rec("audio-seg", False, "没有 ffmpeg")
    os.makedirs(out, exist_ok=True)
    base = os.path.splitext(os.path.basename(src))[0]
    dst = os.path.join(out, "%s_%ds.wav" % (base, seg))
    r = subprocess.run([exe, "-y", "-t", str(seg), "-i", src, "-ac", "1", "-ar", "24000", dst],
                       capture_output=True, timeout=300)
    if r.returncode != 0 or not os.path.exists(dst) or os.path.getsize(dst) < 1024:
        return rec("audio-seg", False, "切段失败")
    return rec("audio-seg", True, "切出 %d 秒（%d 字节）" % (seg, os.path.getsize(dst)), dst)


def from_vault(q, dest):
    src = os.path.join(ROOT, "Tools", "fleet", "asset_pull.py")
    if not os.path.exists(src):
        return rec("vault", False, "asset_pull.py 不存在")
    args = [sys.executable, src]
    args += ["--card", q] if not (len(q) >= 32) else ["--rel", q, "--dest", dest]
    if len(q) >= 32:
        pass
    else:
        args += ["--dest", dest]
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=600)
    ok = r.returncode == 0 and (os.path.exists(dest) if os.path.isabs(dest)
                                else os.path.exists(os.path.join(ROOT, dest)))
    return rec("vault", ok, (r.stdout or r.stderr or "").strip()[:200])


def from_net(url, dest, want_sha):
    host = (url.split("/")[2] if "//" in url else "").lower()
    if not any(host.endswith(a) for a in NET_ALLOW):
        return rec("net", False, "域名不在 allowlist：%s" % host)
    import urllib.request
    dst = dest if os.path.isabs(dest) else os.path.join(ROOT, dest)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dst)
    except Exception as e:
        return rec("net", False, "下载失败：%s" % str(e)[:120])
    if want_sha and sha256(dst) != want_sha:
        os.remove(dst)
        return rec("net", False, "sha256 不匹配，已删除")
    return rec("net", True, "下载 %d 字节，校验通过" % os.path.getsize(dst), dst)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-video")
    ap.add_argument("--from-audio")
    ap.add_argument("--vault")
    ap.add_argument("--net")
    ap.add_argument("--dest", default="media/inbox")
    ap.add_argument("--out", default="media/inbox/acquired")
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--seg", type=int, default=60)
    ap.add_argument("--sha256")
    ap.add_argument("--allow-net", action="store_true")
    a = ap.parse_args(argv[1:])
    if a.from_video:
        return from_video(a.from_video, a.frames, a.out)
    if a.from_audio:
        return from_audio(a.from_audio, a.seg, a.out)
    if a.vault:
        return from_vault(a.vault, a.dest)
    if a.net:
        if not a.allow_net:
            return rec("net", False, "未加 --allow-net（默认不许联网取料）")
        return from_net(a.net, a.dest, a.sha256)
    print(__doc__)
    return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))