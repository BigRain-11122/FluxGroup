#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_dataset_audit.py - 训练数据集准入闸（人脸/语音），只卡"明显不合格"。

为什么（2026-11-03 CEO：「我很讨厌和别的 ai 一样的 ai 脸和声音，去烧各种有自己特色的」）：
  讨厌的东西不是靠"提示词写得花"解决的，先决条件是**数据集本身不像 AI 默认审美**。
  这批数据集一旦是网红脸/磨皮图，或者播音腔朗读，后面训出来的 LoRA 与音色必然平庸，
  再调参也救不回来。所以在训练之前先过闸：不合格的数据集不许进训练，省掉几小时 GPU。

判据（只用 ffmpeg + 纯 Python，不依赖 numpy/PIL，机队任何机器都能跑）：

  face 模式（角色 LoRA 数据集）
    1. 张数 ≥ 12（少于 12 张训不出稳定角色）
    2. 短边 ≥ 768（低于此训练出来糊）
    3. 近似重复率 ≤ 30%（同一张图换背景/换尺寸=假多样性，靠 dHash 判）
    4. 细节能量中位数 ≥ 阈值（磨皮/美颜会把高频细节抹平，拉普拉斯方差会掉）

  rights 判据（两种模式都必须过，2026-11-03 CEO 令「克隆对象要非常广泛」后加的硬门）

    数据集目录里必须有 RIGHTS.json（或 --rights 指定），声明三件事：
      source      来源（自有录制 / 公有领域 / CC 授权库 / 已购买商用授权 / 平台授权）
      license     own | public-domain | cc0 | cc-by | licensed | unknown
      real_person 是否含真实人物（true/false）+ consent 是否有其本人书面授权

    判 FAIL 的三种情况：license 缺失或 unknown；real_person=true 且 consent!=true；
    对真人做声音/肖像克隆而无授权，属民法典 §1019/§1023 与深度合成规定的直接违规，
    不是"风险偏好"问题。机器先把这条挡住，人才不会因为"别人都这么干"而踩进去。

  voice 模式（音色数据集）
    1. 总时长 ≥ 60 秒且条数 ≥ 8（GPT-SoVITS 少样本下限）
    2. 单条时长 2–12 秒占比 ≥ 80%（太长爆显存，太短学不到韵律）
    3. 停顿密度 ≥ 6 次/分钟（播音腔特征之一是"一口气念完、停顿规律稀薄"）
    4. 响度动态 LRA ≥ 5 LU（播音腔被压得很平；生活化录音起伏更大）

这些只是**排除明显不合格**，不能证明"有特色"——有没有特色最终只能人看/人听。
所以本闸的 PASS 语义是"允许进入训练"，不是"这数据集很好"。

用法：
  python3 asset_dataset_audit.py --mode face  --dir <图片目录> [--out receipts/x.json]
  python3 asset_dataset_audit.py --mode voice --dir <音频目录> [--out receipts/x.json]
Exit: 0 PASS；1 FAIL（列缺口）；2 目录不存在/不可读。
"""
import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time

IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
AUD_EXT = (".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg")

FACE_MIN_COUNT = 12
FACE_MIN_SIDE = 768
FACE_MAX_DUP_RATIO = 0.30
FACE_MIN_TEXTURE_P90 = 250.0     # 拉普拉斯能量 p90 地板：只为拦"极端糊脸"
# Why 从"中位数<12 硬门"改成"p90 地板"（2026-11-11 实测标定）：
#   中位数被平坦背景吃掉——本人像组（灰底棚拍，正是角色参考的规格）p50=4~16 全部触底，
#   而把同一张图 gblur σ2.5（等于磨皮）p50 仍是 9.0，即"好图判负、糊图判过"两面都失准。
#   p90 只取最有细节的那 10% 像素，同一组图 900~1521，σ8 极端糊图 169 → 地板 250 可拦糊脸。
#   σ2.5 中等磨皮 p90=729 仍会过，所以此指标只作"极端"地板，皮肤毛孔真伪由人眼抽检（禁当质量背书）。

VOICE_MIN_TOTAL_S = 60.0
VOICE_MIN_COUNT = 8
VOICE_OK_LEN = (2.0, 12.0)
VOICE_MIN_OK_RATIO = 0.80
VOICE_MIN_PAUSE_PER_MIN = 6.0
VOICE_MIN_LRA = 5.0


def ff(name):
    # 无人值守时 PATH 不含 ~/bin（实测本机 ffmpeg 就在那里），只查 PATH
    # 会把"有工具"误判成"没有 ffmpeg"，卡片永远 BLOCKED。
    for c in (os.environ.get(name.upper()) or "", name):
        if not c:
            continue
        if os.path.isabs(c) and os.path.exists(c):
            return c
        if shutil.which(c):
            # 返回解析后的绝对路径：返回裸名字会让"能不能找到"看起来一样（RG-24 实锚）
            return shutil.which(c)
    exe = name + (".exe" if os.name == "nt" else "")
    for d in (os.path.expanduser("~/bin"), "/opt/homebrew/bin", "/usr/local/bin",
              r"C:\ffmpeg\bin", r"C:\Program Files\ffmpeg\bin"):
        p = os.path.join(d, exe)
        if os.path.exists(p):
            return p
    return None


FFMPEG = ff("ffmpeg")
FFPROBE = ff("ffprobe")


def run(cmd, timeout=300, binary=False):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        out = r.stdout if binary else (r.stdout or b"").decode("utf-8", "replace")
        err = (r.stderr or b"").decode("utf-8", "replace")
        return r.returncode, out, err
    except Exception as e:
        return 1, (b"" if binary else ""), str(e)


def probe(path):
    """返回 (w,h,duration)。ffprobe 优先，缺失时解析 ffmpeg -i。"""
    if FFPROBE:
        rc, out, _ = run([FFPROBE, "-v", "error", "-show_streams", "-show_format",
                          "-of", "json", path], 60)
        if rc == 0:
            try:
                d = json.loads(out)
                v = next((s for s in d.get("streams") or [] if s.get("codec_type") == "video"), {})
                dur = float((d.get("format") or {}).get("duration") or 0)
                return (int(v.get("width") or 0), int(v.get("height") or 0), dur)
            except Exception:
                pass
    rc, out, err = run([FFMPEG, "-hide_banner", "-i", path], 60)
    text = (out or "") + (err or "")
    d = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", text)
    dur = int(d.group(1)) * 3600 + int(d.group(2)) * 60 + float(d.group(3)) if d else 0.0
    m = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", text)
    return (int(m.group(1)) if m else 0, int(m.group(2)) if m else 0, dur)


def dhash(path):
    """按 8x8 差分哈希判近似重复；解码交给 ffmpeg，本机无需 PIL。"""
    rc, out, _ = run([FFMPEG, "-v", "error", "-i", path, "-vf", "scale=9:8,format=gray",
                      "-f", "rawvideo", "-"], 60, binary=True)
    if rc != 0 or len(out) < 72:
        return None
    px = struct.unpack("72B", out[:72])
    bits = 0
    i = 0
    for row in range(8):
        for col in range(8):
            left = px[row * 9 + col]
            right = px[row * 9 + col + 1]
            bits |= (1 if left > right else 0) << i
            i += 1
    return bits


def texture_profile(path):
    """(p50, p90) 拉普拉斯能量：p50 报给人看（背景敏感），p90 才是判据。"""
    rc, out, _ = run([FFMPEG, "-v", "error", "-i", path, "-vf",
                      "scale=256:256:force_original_aspect_ratio=increase,crop=256:256,format=gray",
                      "-f", "rawvideo", "-"], 60, binary=True)
    if rc != 0 or len(out) < 256 * 256:
        return None
    W = 256
    px = out[:W * W]
    vals = []
    for y in range(1, W - 1):
        base = y * W
        for x in range(1, W - 1):
            c = px[base + x]
            lap = 4 * c - px[base + x - 1] - px[base + x + 1] - px[base - W + x] - px[base + W + x]
            vals.append(lap * lap)
    if not vals:
        return None
    vals.sort()
    return float(vals[len(vals) // 2]), float(vals[int(len(vals) * 0.90)])


ALLOWED_LICENSES = ("own", "public-domain", "cc0", "cc-by", "licensed")


def audit_rights(d, override=""):
    """来源合规门：没有授权声明就不许进训练。

    数据集常按主体分目录（faces/CH01/…、voices/<id>/…），授权声明天然落在子目录；
    因此顶层缺失时继承子目录声明，但要求各子目录口径一致，不一致一律判缺。
    """
    path = override or ""
    inherited = []
    if not path:
        for cand in ("RIGHTS.json", "rights.json"):
            p = os.path.join(d, cand)
            if os.path.exists(p):
                path = p
                break
    if not path and os.path.isdir(d):
        for n in sorted(os.listdir(d)):
            sub = os.path.join(d, n)
            if os.path.isdir(sub):
                for cand in ("RIGHTS.json", "rights.json"):
                    p = os.path.join(sub, cand)
                    if os.path.exists(p):
                        inherited.append(p)
                        break
        uniq = set()
        for p in inherited:
            try:
                r = json.load(open(p, encoding="utf-8-sig"))
            except Exception:
                uniq.add(("<unreadable>", p))
                continue
            uniq.add((str(r.get("source") or ""), str(r.get("license") or "").lower(),
                      bool(r.get("real_person")), r.get("consent")))
        if len(uniq) == 1:
            path = inherited[0]
        elif len(uniq) > 1:
            return ({"declared": False, "conflict": len(uniq)},
                    ["子目录授权声明不一致（%d 种口径）：%s" % (
                        len(uniq), ", ".join(sorted(os.path.relpath(p, d) for p in inherited[:6])))])
    if not path or not os.path.exists(path):
        return {"declared": False}, ["缺授权声明：数据集目录里要有 RIGHTS.json（source/license/real_person/consent），"
                                     "或训练时传 --rights；没有授权声明的数据集一律不许进训练"]
    try:
        r = json.load(open(path, encoding="utf-8-sig"))
    except Exception as e:
        return {"declared": False, "error": str(e)[:80]}, ["RIGHTS.json 读不了：%s" % e]
    gaps = []
    lic = str(r.get("license") or "").strip().lower()
    if lic not in ALLOWED_LICENSES:
        gaps.append("license=%r 不在允许清单 %s（unknown 等于没授权）" % (lic, list(ALLOWED_LICENSES)))
    if not str(r.get("source") or "").strip():
        gaps.append("RIGHTS.json 没写 source（来源必须可追溯）")
    rp = r.get("real_person")
    if rp is True and r.get("consent") is not True:
        gaps.append("real_person=true 但没有本人同意（consent!=true）：真人声音/肖像克隆必须有书面授权")
    return {"declared": True, "path": os.path.relpath(path, os.getcwd()) if not os.path.isabs(path) else path,
            "license": lic, "source": r.get("source"), "real_person": rp,
            "consent": r.get("consent")}, gaps


def audit_face(d):
    gaps, files = [], []
    # 人脸数据集是按角色分目录的（faces/CH01/front.png…），只扫顶层会把整库读成 0 张。
    for root, _dirs, names in os.walk(d):
        for n in sorted(names):
            if n.lower().endswith(IMG_EXT):
                files.append(os.path.join(root, n))
    files.sort()
    if len(files) < FACE_MIN_COUNT:
        gaps.append("张数 %d < %d（训不出稳定角色）" % (len(files), FACE_MIN_COUNT))
    sizes, tex, tex50, hashes = [], [], [], []
    for p in files:
        w, h, _ = probe(p)
        if w and h:
            sizes.append(min(w, h))
        tp = texture_profile(p)
        if tp is not None:
            tex50.append(tp[0])
            tex.append(tp[1])
        hs = dhash(p)
        if hs is not None:
            hashes.append(hs)
    small = [s for s in sizes if s < FACE_MIN_SIDE]
    if small:
        gaps.append("%d/%d 张短边 < %d" % (len(small), len(sizes) or 1, FACE_MIN_SIDE))
    dup = 0
    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            if bin(hashes[i] ^ hashes[j]).count("1") <= 4:
                dup += 1
    dup_ratio = (dup / max(1, len(hashes) * (len(hashes) - 1) / 2.0))
    if dup_ratio > FACE_MAX_DUP_RATIO:
        gaps.append("近似重复率 %.0f%% > %.0f%%（同一张图换背景=假多样性）"
                    % (dup_ratio * 100, FACE_MAX_DUP_RATIO * 100))
    tex_p90 = sorted(tex)[len(tex) // 2] if tex else None
    tex_p50 = sorted(tex50)[len(tex50) // 2] if tex50 else None
    if tex_p90 is not None and tex_p90 < FACE_MIN_TEXTURE_P90:
        gaps.append("细节能量 p90 %.0f < %.0f（极端糊脸/强磨皮，训出来就是 AI 脸）"
                    % (tex_p90, FACE_MIN_TEXTURE_P90))
    detail = {"mode": "face", "count": len(files), "min_side": min(sizes) if sizes else None,
              "dup_ratio": round(dup_ratio, 3), "texture_p90": tex_p90,
              "texture_p50_advisory": tex_p50,
              "texture_note": "p50 受平坦背景影响不作判据；p90<250=极端糊脸才拦，"
                              "中等磨皮测不出（σ2.5 实测 p90=729），毛孔真伪由人眼抽检"}
    return detail, gaps


def audit_voice(d):
    gaps, files = [], []
    for root, _dirs, names in os.walk(d):
        for n in sorted(names):
            if n.lower().endswith(AUD_EXT):
                files.append(os.path.join(root, n))
    files.sort()
    if len(files) < VOICE_MIN_COUNT:
        gaps.append("条数 %d < %d" % (len(files), VOICE_MIN_COUNT))
    total, ok_len, pauses, lras = 0.0, 0, 0, []
    for p in files:
        _, _, dur = probe(p)
        total += dur
        if VOICE_OK_LEN[0] <= dur <= VOICE_OK_LEN[1]:
            ok_len += 1
        rc, out, err = run([FFMPEG, "-hide_banner", "-i", p, "-af",
                            "silencedetect=n=-35dB:d=0.35", "-f", "null", "-"], 180)
        pauses += len(re.findall(r"silence_start", (out or "") + (err or "")))
        rc, out, err = run([FFMPEG, "-hide_banner", "-i", p, "-af",
                            "loudnorm=print_format=json", "-f", "null", "-"], 180)
        m = re.search(r'"input_lra"\s*:\s*"?(-?[\d.]+)"?', (out or "") + (err or ""))
        if m:
            lras.append(float(m.group(1)))
    if total < VOICE_MIN_TOTAL_S:
        gaps.append("总时长 %.0fs < %.0fs" % (total, VOICE_MIN_TOTAL_S))
    ok_ratio = ok_len / max(1, len(files))
    if ok_ratio < VOICE_MIN_OK_RATIO:
        gaps.append("2–12 秒条目占比 %.0f%% < %.0f%%（太长爆显存/太短学不到韵律）"
                    % (ok_ratio * 100, VOICE_MIN_OK_RATIO * 100))
    per_min = pauses / max(1e-6, total / 60.0) if total else 0
    if per_min < VOICE_MIN_PAUSE_PER_MIN:
        gaps.append("停顿密度 %.1f 次/分 < %.0f（一口气念完=播音腔特征）"
                    % (per_min, VOICE_MIN_PAUSE_PER_MIN))
    lra_med = sorted(lras)[len(lras) // 2] if lras else None
    if lra_med is not None and lra_med < VOICE_MIN_LRA:
        gaps.append("响度动态 LRA %.1f LU < %.0f（被压得太平=播音腔）" % (lra_med, VOICE_MIN_LRA))
    return {"mode": "voice", "count": len(files), "total_s": round(total, 1),
            "ok_len_ratio": round(ok_ratio, 3), "pauses_per_min": round(per_min, 1),
            "lra_median": lra_med}, gaps


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["face", "voice"])
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--rights", default="", help="RIGHTS.json 路径（默认在数据集目录里找）")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.dir):
        out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "mode": a.mode, "dir": a.dir,
               "verdict": "BLOCKED", "status": "BLOCKED",
               "gaps": ["目录不存在：%s" % a.dir]}
        emit(out, a.out)
        print("目录不存在：%s" % a.dir)
        return 2
    if not FFMPEG:
        out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "mode": a.mode, "dir": a.dir,
               "verdict": "BLOCKED", "status": "BLOCKED", "gaps": ["没有 ffmpeg"]}
        emit(out, a.out)
        print("没有 ffmpeg，无法审计")
        return 2
    rights, rgaps = audit_rights(a.dir, a.rights)
    measured, gaps = audit_face(a.dir) if a.mode == "face" else audit_voice(a.dir)
    measured["rights"] = rights
    gaps = rgaps + gaps
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "dir": a.dir,
           "spec": "ASSET-DATASET-GATE-v1", "measured": measured,
           "verdict": "PASS" if not gaps else "FAIL", "gaps": gaps,
           "note": "PASS=允许进训练，不代表这数据集有特色；特色只能人看/人听"}
    out["status"] = out["verdict"]
    emit(out, a.out)
    print("%s %s  %s" % ("DATASET", out["verdict"], a.dir))
    print("  " + json.dumps(measured, ensure_ascii=False))
    for g in gaps:
        print("  ! " + g)
    return 0 if not gaps else 1


def emit(out, path):
    if not path:
        return
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))