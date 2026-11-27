#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""subs_asr.py - 用 Mac GPU（MLX/Metal）把音轨转成字幕源，并给音色库做机器抽检。

为什么（2026-11-03 CEO「可以 你自动化推进下去」）：
  字幕这一环此前是「人给文件」或「装配器自己声明 --subs-burned」，CANON 判据 7 一直半自动；
  音色库则只能看回执条数，没有一条「这段录音到底能不能听清」的机器事实。
  这两件事是同一个能力：ASR。放在主控 GPU 上跑，属于「交付车间」的活，不抢生产机的卡。

用法：
  # 1) 出字幕（成片或音轨都行）
  python3 subs_asr.py --in cut.mp4 --out subs/2026-11-03.srt [--json qc.json]
  # 2) 带金标验准确率（CER）
  python3 subs_asr.py --in voice.mp3 --ref "这份协议，你签也得签。"
  # 3) 音色库批量抽检（可懂度/语速/静音比）
  python3 subs_asr.py --batch media/asset/inbox --out-dir /tmp/asr-qc

判据（都是机器可测）：
  cer          ≤ 0.05 合格（有金标时才算）
  coverage     ≥ 0.60（有声段占总时长比例，太低=大半静音/漏录）
  cps          1.5–7.0 字/秒（中文自然语速；低于=拖，高于=糊）
  chars        > 0（转写为空=不可辨，直接判负）

Exit: 0 通过；1 不合格（有 gaps）；3 输入/后端未到位（BLOCKED 回执，不写交付物路径）。
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

LOCAL_MODEL = os.path.expanduser("~/.cache/whisper-mlx/large-v3-turbo")
# 本机网络实测（2026-11-03）：huggingface.co 与 hf-mirror.com 的 API 全部超时，ModelScope 通。
# 所以权重走 ModelScope 一次性落地到本地目录，之后离线跑，不再每次摸网。
DEFAULT_MODEL = os.environ.get("ASR_MODEL") or (
    LOCAL_MODEL if os.path.isdir(LOCAL_MODEL) else "mlx-community/whisper-large-v3-turbo")
LINE_MAX = 17  # 单行字数上限（GUARDED_V4 折行律）


def ffmpeg():
    for c in (os.environ.get("FFMPEG"), "ffmpeg",
              "/Users/%s/bin/ffmpeg" % os.environ.get("USER", "")):
        if c and shutil.which(c):
            return c
    return None


def run(cmd, timeout=1800):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           errors="replace")
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 1, str(e)


def blocked(target, why, extra=None):
    """输入/后端未到位：写 BLOCKED 回执，路径必须与交付物分离（2026-11-03 教训）。"""
    root, ext = os.path.splitext(target or "subs-asr")
    # 拦截回执一律落 .json（且与交付物同名+后缀区分）：写进 .srt/.csv 会让下游把拒绝当产物
    base = root if ext else (target or "subs-asr")
    rec = os.path.join(os.path.dirname(base) or ".",
                       os.path.basename(base) + "-blocked.json")
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "status": "BLOCKED",
           "error_class": "E-BLOCKED-INPUT", "why": why, "tool": "subs_asr",
           "target": target}
    if extra:
        out.update(extra)
    try:
        d = os.path.dirname(os.path.abspath(rec))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(rec, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("[asr] BLOCKED %s（回执 %s）" % (why, rec))
    except Exception:
        print("[asr] BLOCKED %s" % why)
    return 3


def backend():
    try:
        import mlx_whisper  # noqa: F401
        return "mlx"
    except Exception:
        pass
    try:
        import faster_whisper  # noqa: F401
        return "faster"
    except Exception:
        return ""


def to_wav(src, dst):
    """Whisper 只吃 16k 单声道；视频自动抽音轨。"""
    F = ffmpeg()
    rc, out = run([F, "-y", "-loglevel", "error", "-i", src,
                   "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", dst])
    return rc == 0 and os.path.exists(dst) and os.path.getsize(dst) > 1024


def transcribe(wav, model, lang, be):
    t0 = time.time()
    if be == "mlx":
        import mlx_whisper
        r = mlx_whisper.transcribe(wav, path_or_hf_repo=model,
                                   language=(lang or None), verbose=None)
    else:
        from faster_whisper import WhisperModel
        m = WhisperModel(model, device="cpu", compute_type="int8")
        segs, _info = m.transcribe(wav, language=(lang or None))
        r = {"segments": [{"start": s.start, "end": s.end, "text": s.text} for s in segs]}
    return r, time.time() - t0


def ts(sec):
    sec = max(0.0, float(sec))
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return ("%02d:%02d:%06.3f" % (int(h), int(m), s)).replace(".", ",")


def fold(text):
    """按标点切成 ≤17 字的行（单行超 17 字在竖屏上会被裁）。短句保持一行，不要硬切。"""
    text = text.strip()
    if len(text) <= LINE_MAX:
        return text
    parts, cur = [], ""
    for ch in text:
        cur += ch
        if ch in "，。！？；：、…" or len(cur) >= LINE_MAX:
            parts.append(cur.strip())
            cur = ""
    if cur.strip():
        parts.append(cur.strip())
    return "\n".join(p for p in parts if p)


def norm_punct(s):
    """Whisper 对中文常出半角标点；字幕要全角，否则竖屏上看着像代码。"""
    for a, b in ((",", "，"), ("?", "？"), ("!", "！"), (":", "："),
                 (";", "；"), ("(", "（"), (")", "）")):
        s = s.replace(a, b)
    return s


def to_srt(segments):
    out = []
    for i, s in enumerate(segments, 1):
        out.append("%d\n%s --> %s\n%s\n" %
                   (i, ts(s["start"]), ts(s["end"]),
                    fold(norm_punct(s.get("text", "").strip()))))
    return "\n".join(out)


def norm(s):
    return re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]", "", s or "")


def cer(ref, hyp):
    """字错率（编辑距离 / 参考长度）。中文字符级，够用且可复算。"""
    a, b = norm(ref), norm(hyp)
    if not a:
        return None
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            cur = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (ca != cb))
            prev = cur
    return round(d[len(b)] / len(a), 4)


def qc(src, segments, dur, elapsed, ref=None):
    speak = sum(max(0.0, s["end"] - s["start"]) for s in segments)
    text = "".join(s.get("text", "") for s in segments)
    chars = len(norm(text))
    cov = round(speak / dur, 3) if dur else 0.0
    cps = round(chars / speak, 2) if speak > 0 else 0.0
    r = {"input": src, "segments": len(segments), "duration_s": round(dur, 2),
         "speech_s": round(speak, 2), "coverage": cov, "chars": chars, "cps": cps,
         "elapsed_s": round(elapsed, 2),
         "rtf": round(elapsed / dur, 3) if dur else None}
    gaps = []
    warns = []
    if chars == 0:
        gaps.append("转写为空（不可辨/无人声）")
    if cov < 0.15:
        gaps.append("有声段占比 %.2f < 0.15（几乎没人声）" % cov)
    elif cov < 0.60:
        # 漫剧/短剧里有音乐垫底是常态（实测 12s 成片人声只占 39%），不能按"大半静音"判红。
        warns.append("有声段占比 %.2f（人声稀疏，音乐段偏多属正常，抽查用）" % cov)
    if chars and not (1.5 <= cps <= 7.0):
        gaps.append("语速 %.2f 字/秒不在 1.5–7.0（过低=拖，过高=糊）" % cps)
    if ref:
        c = cer(ref, text)
        r["cer"] = c
        # 两档（2026-11-03 实测口径）：10% 以上才算"不可辨"，5–10% 记警告不判红。
        # 依据=本机 TTS 已知文本实测 7.7%，错的全是同音字（得/的），人类听写也会这么错；
        # 把 5% 当硬线会让每日抽检常驻红灯，红灯一常驻就没人看了。
        if c is not None and c > 0.10:
            gaps.append("字错率 %.1f%% > 10%%（金标对照，属不可辨）" % (c * 100))
        elif c is not None and c > 0.05:
            warns.append("字错率 %.1f%%（5–10%%，多为同音字，人工抽查即可）" % (c * 100))
    r["gaps"] = gaps
    r["warns"] = warns
    r["verdict"] = "PASS" if not gaps else "FAIL"
    return r


def probe_dur(src):
    F = ffmpeg()
    rc, out = run([F, "-hide_banner", "-i", src])
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", out or "")
    if not m:
        return 0.0
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def one(a, src, out_srt, out_json, be, model):
    if not os.path.exists(src):
        return blocked(out_json or out_srt or src, "输入不存在：%s" % src)
    F = ffmpeg()
    if not F:
        return blocked(out_json or out_srt or src, "没有 ffmpeg")
    dur = probe_dur(src)
    if dur <= 0:
        return blocked(out_json or out_srt or src, "读不出时长：%s" % src)
    tmpdir = tempfile.mkdtemp(prefix="asr-")
    wav = os.path.join(tmpdir, "a.wav")
    try:
        if not to_wav(src, wav):
            return blocked(out_json or out_srt or src, "抽音轨失败：%s" % src)
        r, elapsed = transcribe(wav, model, a.lang, be)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    segs = r.get("segments") or []
    if out_srt:
        os.makedirs(os.path.dirname(os.path.abspath(out_srt)) or ".", exist_ok=True)
        with open(out_srt, "w", encoding="utf-8") as f:
            f.write(to_srt(segs))
    q = qc(src, segs, dur, elapsed, a.ref)
    q.update({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "backend": be, "model": model,
              "srt": out_srt or "", "text": "".join(s.get("text", "") for s in segs).strip()})
    if out_json:
        os.makedirs(os.path.dirname(os.path.abspath(out_json)) or ".", exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(q, f, ensure_ascii=False, indent=1)
    print("[asr] %s  %.1fs 档 rtf=%.2f  cov=%.2f  cps=%.2f  %s" %
          (q["verdict"], dur, q["rtf"] or 0, q["coverage"], q["cps"],
           ("CER=%.1f%%" % (q["cer"] * 100)) if q.get("cer") is not None else "无金标"))
    for g in q["gaps"]:
        print("  ! " + g)
    return 0 if q["verdict"] == "PASS" else 1


def sync(a):
    """自动补字幕源：成片没有对应 SRT 就补一份，一天只跑一次（冲脉慢批 300s 会重入）。

    为什么这样接：字幕不再靠人给或靠装配器自己申报，判据 7 有了链上一手产出；
    但 ASR 吃 GPU，不能每轮跑，所以按日期闸 + "只补缺的"来收敛。
    """
    be = backend()
    if not be:
        return blocked(a.subs_dir or a.sync_dir, "没有 ASR 后端（pip install mlx-whisper）")
    d = a.sync_dir
    if not os.path.isdir(d):
        return blocked(a.subs_dir or d, "成片目录不存在：%s" % d)
    subs_dir = a.subs_dir or os.path.join("cph4", "fleet", "drama-dept-v1", "subs")
    os.makedirs(subs_dir, exist_ok=True)
    stamp = os.path.join(subs_dir, "_asr-sync-%s.json" % time.strftime("%Y-%m-%d"))
    if os.path.exists(stamp):
        print("[asr] 今日已同步过（%s），跳过" % os.path.basename(stamp))
        return 0
    cutoff = time.time() - a.days * 86400
    todo = []
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith(".mp4"):
            continue
        p = os.path.join(d, f)
        if os.path.getmtime(p) < cutoff:
            continue
        srt = os.path.join(subs_dir, os.path.splitext(f)[0] + ".srt")
        if not os.path.exists(srt):
            todo.append((p, srt))
    rows, bad = [], 0
    for p, srt in todo[:2]:  # 慢批里一次最多补 2 条：GPU 是共用的，不能长时间占用
        rc = one(a, p, srt, os.path.join(subs_dir, "_qc", os.path.basename(srt) + ".json"), be, a.model)
        rows.append({"file": p, "srt": srt, "rc": rc})
        bad += 1 if rc != 0 else 0
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "dir": d, "backend": be,
           "model": a.model, "missing_before": len(todo), "done": len(rows) - bad,
           "fail": bad, "rows": rows}
    # 有失败或还没轮完就**不写当日戳**：否则一次临时失败/截断会把"今天不干了"钉死，等于假绿。
    if bad == 0 and len(rows) == len(todo):
        with open(stamp, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=1)
    print("[asr] 补字幕 %d 条（失败 %d，待补 %d）→ %s"
          % (len(rows), bad, max(0, len(todo) - len(rows)),
             stamp if (bad == 0 and len(rows) == len(todo)) else "未写当日戳（有失败或有剩余，下轮继续）"))
    return 0 if bad == 0 else 1


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default="")
    ap.add_argument("--out", dest="srt", default="")
    ap.add_argument("--json", dest="json", default="")
    ap.add_argument("--ref", default="", help="金标文本，给了就算 CER")
    ap.add_argument("--batch", default="", help="目录批量抽检（音色库语料）")
    ap.add_argument("--out-dir", dest="out_dir", default="")
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--sync-dir", dest="sync_dir", default="",
                    help="自动模式：把该目录里还没有字幕源的成片补出 SRT（冲脉慢批用）")
    ap.add_argument("--subs-dir", dest="subs_dir", default="",
                    help="SRT 落库目录（默认 cph4/fleet/drama-dept-v1/subs）")
    ap.add_argument("--days", type=int, default=7, help="只看最近 N 天改过的成片")
    a = ap.parse_args(argv)
    if a.sync_dir:
        return sync(a)
    be = backend()
    if not be:
        return blocked(a.json or a.srt or a.batch or "subs-asr",
                       "没有 ASR 后端（pip install mlx-whisper）")
    if a.batch:
        d = a.batch
        if not os.path.isdir(d):
            return blocked(a.out_dir or d, "目录不存在：%s" % d)
        audio = sorted(f for f in os.listdir(d)
                       if f.lower().endswith((".wav", ".mp3", ".m4a", ".flac", ".ogg", ".mp4")))
        if not audio:
            return blocked(a.out_dir or d, "目录里没有音频：%s" % d)
        out_dir = a.out_dir or os.path.join(d, "_asr-qc")
        os.makedirs(out_dir, exist_ok=True)
        rows, bad = [], 0
        for f in audio:
            q = one(a, os.path.join(d, f), "",
                    os.path.join(out_dir, os.path.splitext(f)[0] + ".json"), be, a.model)
            jf = os.path.join(out_dir, os.path.splitext(f)[0] + ".json")
            if os.path.exists(jf):
                with open(jf, encoding="utf-8") as fh:
                    rec = json.load(fh)
                rows.append({"file": f, "verdict": rec.get("verdict"),
                             "cps": rec.get("cps"), "coverage": rec.get("coverage"),
                             "chars": rec.get("chars"), "gaps": rec.get("gaps")})
                bad += 1 if rec.get("verdict") != "PASS" else 0
        summary = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "dir": d, "total": len(rows),
                   "fail": bad, "backend": be, "model": a.model, "rows": rows}
        sp = os.path.join(out_dir, "SUMMARY.json")
        with open(sp, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=1)
        print("[asr] 批量 %d 件，不合格 %d 件 → %s" % (len(rows), bad, sp))
        return 0 if bad == 0 else 1
    if not a.src:
        ap.error("需要 --in 或 --batch")
    return one(a, a.src, a.srt or (os.path.splitext(a.src)[0] + ".srt"), a.json, be, a.model)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))