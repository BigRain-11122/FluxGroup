#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_v2_segments_r1057.py - V2《法务部》段件构建器（bm-c r1057·CPU 道）
依据: cph4/fleet/meme-daily-v1/PREPRO-V2.md (v0.2 CERTIFIED) + 实测材料参数
产出 (media/v2-falvbu/build/): c1.mp4 c3.mp4 c4.mp4 c5.mp4 c6.mp4 card.mp4
       + seg1_t..seg5_t.wav + bgm_falvbu.wav
       + 覆写 topics/v2-shots.json (旧发布会草案判负归档·git 史可溯)
装配: python tools/assemble_meme.py --topic v2 --media <build> --out <final>
实测适配 (PREPRO 弹性条款·入 DIRECTOR-REVIEW 备审):
  seg5 语音实长 3.88s (silencedetect -35dB) > C5 拍长 3.21s -> C6 扩 1.4->2.15s
  (12.5-14.65: 前 0.85s 承 seg5 尾韵+空 feed, 后 1.35s 纯静+幸存句加冕),
  C7 [14.65,15.55], 总长 15.55 = V1 同长 (J-M8 甜区上沿合法)。
"""
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..", "..", "..")   # tools -> meme-daily-v1 -> fleet -> cph4 -> FluxGroup root
MEDIA = os.path.join(REPO, "media", "meme-daily-v1")
V1 = os.path.join(MEDIA, "v1-zunjie-brake")
V2 = os.path.join(MEDIA, "v2-falvbu")
KFL_SRC = os.path.join(REPO, "media", "mv-album-001-jay", "clips-local-768", "V2_KFL.mp4")
BUILD = os.path.join(V2, "build")
WORK = os.path.join(BUILD, "_work")
FF = shutil.which("ffmpeg")

FPS = 30
W, H = 720, 1280


def run(cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, cwd=cwd)
    if r.returncode != 0:
        sys.exit("FFMPEG FAIL: " + " ".join(cmd) + "\n" + r.stderr.decode("utf-8", "replace")[-1500:])


def font(size, bold=True):
    name = "msyhbd.ttc" if bold else "msyh.ttc"
    p = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", name)
    if not os.path.exists(p):
        p = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "msyh.ttc")
    return ImageFont.truetype(p, size)


def encode_frames(frames_dir, n, out, fps=FPS):
    run([FF, "-y", "-loglevel", "error", "-framerate", str(fps),
         "-i", os.path.join(frames_dir, "f%04d.png"),
         "-frames:v", str(n), "-pix_fmt", "yuv420p", "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", out])


def v_text(draw, x, y, text, fnt, fill, step=None):
    step = step or int(fnt.size * 1.18)
    cy = y
    for ch in text:
        draw.text((x, cy), ch, font=fnt, fill=fill)
        cy += step
    return cy


# ---------------------------------------------------------------- C1 巨幕合成
def build_c1():
    """V1 KF-P i2v [0,2.0] 48 帧 @24fps + 逐帧巨幕替换 + 侧条。"""
    out = os.path.join(BUILD, "c1.mp4")
    fd = os.path.join(WORK, "c1")
    os.makedirs(fd, exist_ok=True)
    src = os.path.join(V1, "clips", "clip_KF_P.mp4")
    run([FF, "-y", "-loglevel", "error", "-ss", "0", "-t", "2.0", "-i", src, "-an",
         os.path.join(fd, "f%04d.png")])
    s3 = Image.open(os.path.join(V1, "frames", "S3.png")).convert("RGB")
    N = len([f for f in os.listdir(fd) if f.startswith("f")])
    for i in range(1, N + 1):
        p = os.path.join(fd, ("f%04d.png" % i))
        img = Image.open(p).convert("RGB")
        SW, SH = img.size          # KF-P i2v 原生 768x1344：巨幕框按材料原生尺寸（PREPRO f0 [0,312,768,888]）
        t = (i - 1) / float(max(1, N - 1))
        top = int(312 - 4 * t)     # f0 312 -> f59 308（PREPRO 巨幕内插账·符号定谳）
        bot = int(888 - 118 * t)   # f0 888 -> f59 770
        sh = bot - top
        # 巨幕内容
        crop = s3.crop((0, 0, s3.width, int(s3.width * sh / float(SW))))
        crop = crop.resize((SW, sh))
        if t < 0.39:            # 0-0.78s: 断裂微距回调 (0.2s 承诺可见)
            content = ImageEnhance.Brightness(crop).enhance(0.95)
        elif t < 0.70:          # 0.78-1.67s: 变灰+叉+已处理 (3 帧淡入)
            g = ImageEnhance.Color(crop).enhance(0.0)
            g = ImageEnhance.Brightness(g).enhance(0.55)
            k = min(1.0, (t - 0.39) / 0.07)
            content = Image.blend(crop, g, k)
            d = ImageDraw.Draw(content)
            cx, cy = SW // 2, sh // 2
            r = int(min(SW, sh) * 0.22)
            wd = max(6, int(r * 0.16))
            for a, b in ((-1, -1), (-1, 1)):
                d.line([cx + a * r, cy + b * r, cx - a * r, cy - b * r],
                       fill=(228, 228, 236), width=wd)
            tag = "已处理"
            tf = font(30)
            tw = d.textlength(tag, font=tf)
            bx = SW - int(tw) - 60
            by = sh - 78          # content 画布内坐标（原 bot-78 画在画布外=标签静默消失）
            d.rectangle([bx - 14, by - 8, bx + tw + 14, by + 40], fill=(24, 24, 30))
            d.text((bx, by), tag, font=tf, fill=(206, 206, 214))
        else:                    # 1.67-2.0s: 清空暗屏 (2 帧过渡)
            dark = Image.new("RGB", (SW, sh), (14, 14, 19))
            k = min(1.0, (t - 0.70) / 0.06)
            base = ImageEnhance.Color(crop).enhance(0.0)
            base = ImageEnhance.Brightness(base).enhance(0.55)
            content = Image.blend(base, dark, k)
        # 羽化边粘贴 (3px)
        mask = Image.new("L", (SW, sh), 255)
        md = ImageDraw.Draw(mask)
        for e in range(3):
            md.rectangle([e, e, SW - 1 - e, sh - 1 - e], outline=255 - (e + 1) * 50)
        img.paste(content, (0, top), mask)
        # 侧条「速成汽车·法务部」
        d = ImageDraw.Draw(img, "RGBA")
        band = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
        bd = ImageDraw.Draw(band)
        bd.rectangle([702, 336, 766, 830], fill=(12, 12, 16, 165))
        bd.text((712, 352), "", font=font(30), fill=(0, 0, 0, 0))
        bd2 = ImageDraw.Draw(band)
        v_text(bd2, 724, 350, "速成汽车·法务部", font(30), (236, 236, 242))
        img = Image.alpha_composite(img.convert("RGBA"), band).convert("RGB")
        img.save(p)
    encode_frames(fd, N, out, fps=24)
    print("  c1 ok (%d frames)" % N)


# ---------------------------------------------------------------- C3 feed 瀑布
def build_c3():
    out = os.path.join(BUILD, "c3.mp4")
    fd = os.path.join(WORK, "c3")
    os.makedirs(fd, exist_ok=True)
    N = 84            # 2.8s @30
    BG = (16, 16, 20)
    CARD = (54, 54, 62)
    comments = ["视频没了", "谁存了？", "刚想看，没了"]
    rows = []
    y = 96
    for i in range(7):
        kind = "comment" if i in (2, 4, 6) else "card"
        rows.append({"kind": kind, "y": y, "grayed": False})
        y += 158 if kind == "card" else 118
    # 变灰节拍 (local s): 对齐 seg3 字头序列
    beats = [0.10, 0.38, 0.72, 1.02, 1.32, 2.32, 2.62]
    for idx, r in enumerate(rows):
        r["beat"] = beats[idx]
    for i in range(N):
        t = i / float(FPS)
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        for idx, r in enumerate(rows):
            gray = t >= r["beat"]
            # 复冒行: 「谁存了？」(idx4) 灰后在 2.5s 复亮·末 2 帧再退灰
            repop = (idx == 4 and 2.50 <= t < N / float(FPS) - 2 / float(FPS))
            hi = (t >= r["beat"] + 0.12) and gray
            if r["kind"] == "card":
                base = 46 if not gray else 20
                col = (base + 8, base + 8, base + 14)
                d.rounded_rectangle([36, r["y"], 696, r["y"] + 146], radius=12, fill=col)
                tb = 150 if not gray else 60
                d.rounded_rectangle([52, r["y"] + 16, 244, r["y"] + 124], radius=8,
                                    fill=(tb, tb, tb + 6))
                d.rounded_rectangle([262, r["y"] + 22, 660, r["y"] + 54], radius=7,
                                    fill=(tb - 20, tb - 20, tb - 14))
                d.rounded_rectangle([262, r["y"] + 70, 560, r["y"] + 98], radius=7,
                                    fill=(tb - 40, tb - 40, tb - 36))
            else:
                txt = comments[[2, 4, 6].index(idx)]
                av = (168, 162, 118) if not gray else (60, 60, 66)
                ty = r["y"] + 16
                d.ellipse([64, ty, 104, ty + 40], fill=(90, 90, 100) if not gray else (44, 44, 50))
                cf = font(34, bold=(idx == 4))
                col = (238, 238, 244) if (repop or not gray) else (96, 96, 104)
                d.text((124, ty + 2), txt, font=cf, fill=col)
                if repop:
                    # 复冒视觉加权: 浅金单点 + 行高↑ (加下划短杠)
                    d.ellipse([596, ty + 12, 616, ty + 32], fill=(212, 180, 106))
                    d.rounded_rectangle([124, ty + 54, 124 + int(d.textlength(txt, font=cf)) + 18,
                                         ty + 62], radius=4, fill=(212, 180, 106))
        img.save(os.path.join(fd, ("f%04d.png" % (i + 1))))
    encode_frames(fd, N, out)
    print("  c3 ok (84 frames)")


# ---------------------------------------------------------------- C4 声明卡
def build_c4():
    out = os.path.join(BUILD, "c4.mp4")
    fd = os.path.join(WORK, "c4")
    os.makedirs(fd, exist_ok=True)
    N = 69            # 2.3s @30
    for i in range(N):
        t = i / float(FPS)
        img = Image.new("RGB", (W, H), (13, 13, 17))
        d = ImageDraw.Draw(img)
        glow = 1.0 + 0.02 * np.sin(2 * np.pi * 0.5 * t)
        cx0, cy0, cw, chh = 50, 150, 620, 830
        base = int(34 * glow)
        d.rounded_rectangle([cx0 - 6, cy0 - 6, cx0 + cw + 6, cy0 + chh + 6], radius=20,
                           fill=(base + 8, base + 8, base + 14))
        d.rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + chh], radius=16, fill=(24, 24, 30))
        # 卡头 (首读级字号·与下架同屏秒读)
        hf = font(40)
        d.text((cx0 + 36, cy0 + 30), "速成汽车", font=hf, fill=(232, 232, 238))
        d.text((cx0 + 36, cy0 + 86), "关于近期不实信息的情况说明", font=font(30, False),
               fill=(176, 176, 184))
        d.line([cx0 + 36, cy0 + 140, cx0 + cw - 36, cy0 + 140], fill=(58, 58, 66), width=2)
        # 正文灰条 (generic 声明文本·不可读伪文字用灰条代)
        for k in range(7):
            wfrac = [0.92, 0.86, 0.9, 0.6, 0.88, 0.82, 0.45][k]
            yy = cy0 + 168 + k * 44
            d.rounded_rectangle([cx0 + 36, yy, cx0 + 36 + int((cw - 72) * wfrac), yy + 18],
                                radius=6, fill=(64, 64, 72))
        # 灰罩 + 叉 + 下架 (卡中下部)
        vy = cy0 + 520
        d.rectangle([cx0, vy, cx0 + cw, cy0 + chh], fill=(18, 18, 24, ))
        xx, yy2 = W // 2, vy + 130
        d.ellipse([xx - 62, yy2 - 62, xx + 62, yy2 + 62], fill=(140, 140, 148))
        d.line([xx - 28, yy2 - 28, xx + 28, yy2 + 28], fill=(58, 58, 64), width=10)
        d.line([xx - 28, yy2 + 28, xx + 28, yy2 - 28], fill=(58, 58, 64), width=10)
        nf = font(36)
        nt = "该内容已因权利方投诉下架"
        d.text(((W - d.textlength(nt, font=nf)) // 2, yy2 + 92), nt, font=nf, fill=(210, 210, 218))
        # 时码走动 (03:11:57.8 -> 03:12:00.1·11 分基与 C6「今天 03:12」同宿主连续)
        tc = 11 * 60 + 57.8 + t * 1.0
        mm = int(tc // 60)
        ss = tc % 60
        ts = "今天 03:%02d:%04.1f" % (mm, ss)
        d.text((cx0 + cw - 6 - d.textlength(ts, font=font(22, False)) - 20,
                cy0 + chh - 40), ts, font=font(22, False), fill=(150, 150, 158))
        # 淡入 (前 6 帧)
        if i < 6:
            k = i / 6.0
            img = ImageEnhance.Brightness(img).enhance(0.35 + 0.65 * k)
        img.save(os.path.join(fd, ("f%04d.png" % (i + 1))))
    encode_frames(fd, N, out)
    print("  c4 ok (69 frames)")


# ---------------------------------------------------------------- C5 慢放回收
def build_c5():
    out = os.path.join(BUILD, "c5.mp4")
    run([FF, "-y", "-loglevel", "error", "-stats", "-ss", "2.4", "-t", "2.6",
         "-i", KFL_SRC, "-vf",
         "setpts=1.2346*PTS,minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
         "-pix_fmt", "yuv420p", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         out])
    print("  c5 ok (0.81x minterpolate)")


# ---------------------------------------------------------------- C6 空 feed 幸存
def build_c6():
    out = os.path.join(BUILD, "c6.mp4")
    fd = os.path.join(WORK, "c6")
    os.makedirs(fd, exist_ok=True)
    N = 65            # 2.15s @30
    reveal = 0.85     # local: seg5 尾韵后·纯静加冕
    for i in range(N):
        t = i / float(FPS)
        img = Image.new("RGB", (W, H), (14, 14, 18))
        d = ImageDraw.Draw(img)
        # 「该用户正在输入…」闪动 (周期 0.45s·全程)
        if int(t / 0.45) % 2 == 0:
            tf = font(24, False)
            ts = "该用户正在输入…"
            d.text(((W - d.textlength(ts, font=tf)) // 2, 1080), ts, font=tf, fill=(132, 132, 140))
        if t >= reveal:
            k = min(1.0, (t - reveal) / 0.15)
            a = int(255 * k)
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(ov)
            ty = 470
            od.ellipse([222, ty, 278, ty + 56], fill=(90, 90, 100, a))
            od.rounded_rectangle([298, ty + 8, 470, ty + 22], radius=7, fill=(90, 90, 100, a))
            cf = font(44)           # 9 字形 x44px + 起点298 = 694 <= 720（原 font50 右缘溢出截断）
            ct = "慢慢踩，法务部也是"
            od.text((298, ty + 44), ct, font=cf, fill=(255, 255, 255, a))
            sf = font(26, False)
            od.text((300, ty + 118), "今天 03:12", font=sf, fill=(148, 148, 156, a))
            img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        img.save(os.path.join(fd, ("f%04d.png" % (i + 1))))
    encode_frames(fd, N, out)
    print("  c6 ok (65 frames·2.15s)")


# ---------------------------------------------------------------- C7 签名卡
def build_card():
    out = os.path.join(BUILD, "card.mp4")
    fd = os.path.join(WORK, "card")
    os.makedirs(fd, exist_ok=True)
    N = 27            # 0.9s @30
    for i in range(N):
        img = Image.new("RGB", (W, H), (8, 8, 10))
        d = ImageDraw.Draw(img)
        if i < 12:      # 签名卡 0.4s
            wf = font(64)
            wt = "速成汽车"
            d.text(((W - d.textlength(wt, font=wf)) // 2, 560), wt, font=wf, fill=(240, 240, 246))
        else:           # 标识卡 0.5s
            lf = font(34)
            lt = "AI 生成｜纯属演绎"
            d.text(((W - d.textlength(lt, font=lf)) // 2, 560), lt, font=lf, fill=(220, 220, 228))
            lf2 = font(24, False)
            lt2 = "事件为虚构演绎设定"
            d.text(((W - d.textlength(lt2, font=lf2)) // 2, 636), lt2, font=lf2, fill=(150, 150, 158))
        img.save(os.path.join(fd, ("f%04d.png" % (i + 1))))
    encode_frames(fd, N, out)
    print("  card ok (27 frames)")


# ---------------------------------------------------------------- 旁白剪垫 + BGM 包络
def build_audio():
    trims = {"seg1": 2.06, "seg2": 2.05, "seg3": 3.10, "seg4": 1.09, "seg5": 3.93}
    for k, dur in trims.items():
        run([FF, "-y", "-loglevel", "error", "-i",
             os.path.join(V2, "narration", "%s.wav" % k), "-t", "%.2f" % dur,
             os.path.join(BUILD, "%s_t.wav" % k)])
    # BGM: V1 同源前移 0.6s + 终止式收束/声桥/极轻回归/C6 全静 包络预烤
    env = ("if(lt(t,7.0),1.0,if(lt(t,7.35),1.0-0.98*(t-7.0)/0.35,"
           "if(lt(t,8.6),0.02,if(lt(t,9.2),0.02+0.28*(t-8.6)/0.6,"
           "if(lt(t,12.4),0.30,if(lt(t,12.9),0.30*(1-(t-12.4)/0.5),0))))))")
    run([FF, "-y", "-loglevel", "error", "-ss", "0.6",
         "-i", os.path.join(V1, "audio", "bgm.wav"),
         "-af", ("afade=t=in:d=0.4,volume=eval=frame:volume='%s'" % env),
         "-af", "aresample=48000", "-t", "15.55",
         os.path.join(BUILD, "bgm_falvbu.wav")])
    print("  audio ok (5 segs trimmed + bgm envelope)")


# ---------------------------------------------------------------- spec 覆写
def write_spec():
    spec = {
        "topic": "v2", "slug": "falvbu",
        "title": "速成汽车宇宙·第2集：法务部，我们永不休息（PREPRO-V2 v0.2 CERTIFIED 装配版）",
        "duration_target": 15.55,
        "resolution": [720, 1280], "fps": 30,
        "subtitle_style_big": {"fontsize": 56, "marginv": 300},
        "revision_note": ("bm-c r1057 装配版：旧发布会草案判负归档（git 史可溯）。"
                          "seg5 语音实测 3.88s (silencedetect -35dB) > C5 拍长 3.21s -> "
                          "C6 弹性扩 2.15s (PREPRO §二 拍6 弹性带条款)：前 0.85s 承 seg5 "
                          "尾韵+空 feed，后 1.35s 纯静+幸存句加冕；C7 [14.65,15.55]；"
                          "总长 15.55=V1 同长。C1-C5 分拍表原封未动。"),
        "shots": [
            {"id": "C1", "file": "c1.mp4", "trim": [0.0, 2.0],
             "note": "拍1 守护宣言：KF-P 回收+巨幕 PIL（S3 微距 0-0.78s→灰+叉+已处理 0.78-1.67s→清空暗屏 1.67-2.0s）+侧条"},
            {"id": "C2", "file": "KFL.mp4", "trim": [0.0, 2.2],
             "note": "拍2 深夜法务部：KF-L i2v [0,2.2]"},
            {"id": "C3", "file": "c3.mp4", "trim": [0.0, 2.8],
             "note": "拍3 全网清理：generic feed 灰条瀑布 7 行·三小字各异·谁存了？删而复冒·段末帧退灰"},
            {"id": "C4", "file": "c4.mp4", "trim": [0.0, 2.3],
             "note": "拍4 误删自己：声明卡灰罩+叉+已因权利方投诉下架·屏光微动+时码 03:11:5x→03:12:0x"},
            {"id": "C5", "file": "c5.mp4", "trim": [0.0, 3.21],
             "note": "拍5 双部门签名语：KFL [2.4,5.0] 0.81x minterpolate 慢放回收（禁末帧冻结）"},
            {"id": "C6", "file": "c6.mp4", "trim": [0.0, 2.15],
             "note": "拍6 唯一幸存：空 feed·正在输入闪动全程·幸存句 13.35s 高对比首读（纯静加冕 1.35s）+今天 03:12"},
            {"id": "C7", "file": "card.mp4", "trim": [0.0, 0.9],
             "note": "拍7 签名卡 0.4s→标识卡 0.5s"}
        ],
        "narration_segments": [
            {"file": "seg1_t.wav", "t": 0.05, "note": "有一种守护，看不见。（末字≈2.06 落 C1/C2 切点）"},
            {"file": "seg2_t.wav", "t": 2.35, "note": "那件事，现在没人聊了。"},
            {"file": "seg3_t.wav", "t": 4.35, "note": "那一晚，全网相关内容，全部消失。（尾入 C4 头 0.4s）"},
            {"file": "seg4_t.wav", "t": 7.50, "note": "删得很干净。（hold 8.59-9.3=0.71s ≤0.9 ✓）"},
            {"file": "seg5_t.wav", "t": 9.35, "note": "生产部，一年三款。法务部，永不休息。（尾韵承 C6 前 0.85s）"}
        ],
        "bgm_file": "bgm_falvbu.wav", "bgm_gain_db": 0,
        "subtitles": [
            {"t": [0.05, 2.10], "text": "有一种守护，{Y}看不见{W}。", "style": "Big"},
            {"t": [2.35, 4.40], "text": "那件事，现在没人聊了。", "style": "Big"},
            {"t": [4.35, 7.40], "text": "那一晚，全网相关内容，{Y}全部消失{W}。", "style": "Big"},
            {"t": [7.50, 8.55], "text": "删得很干净。", "style": "Big"},
            {"t": [9.35, 13.30], "text": "生产部，一年三款。\\N法务部，{Y}永不休息{W}。", "style": "Big",
             "note": "双行字幕随 seg5"},
            {"t": [9.35, 12.50], "text": "{\\an2\\pos(360,1130)\\fs42}速成汽车", "style": "Small",
             "note": "wordmark 与「生产部」首字同帧淡入（锁同步锚）"},
            {"t": [11.90, 12.50], "text": "{\\an2\\pos(360,1190)\\fs26}投诉通道：请慢慢填", "style": "Small",
             "note": "拍尾 0.6s 错峰单独浮现"},
        ],
        "watermark": "AI 生成｜纯属演绎",
        "publish_caption": ("速成汽车法务部：相关问题，已全部处理完毕。评论区聊聊：你猜，还剩什么。"
                            "（改编自近期车圈名场面，懂的都懂。速成汽车=虚构品牌·情节为演绎设定）"
                            "#车圈 #法务部 #下架 #AI动画"),
        "pinned_comment": ("慢慢踩。转给还在找视频的人。下集：速成汽车加班图鉴，我们永不休息。"
                           "（虚构品牌·纯属演绎）"),
        "media_layout": ("装配 --media 指向本 build 夹（c1/KFL/c3/c4/c5/c6/card.mp4 + "
                         "seg1_t..seg5_t.wav + bgm_falvbu.wav；KFL.mp4=V2_KFL.mp4 拷贝）")
    }
    with open(os.path.join(REPO, "cph4", "fleet", "meme-daily-v1", "topics", "v2-shots.json"),
              "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)
    print("  spec ok (topics/v2-shots.json)")


def main():
    if not FF:
        sys.exit("ffmpeg not found")
    os.makedirs(WORK, exist_ok=True)
    print("BUILD v2 segments (bm-c r1057):")
    shutil.copyfile(KFL_SRC, os.path.join(BUILD, "KFL.mp4"))
    build_c1()
    build_c3()
    build_c4()
    build_c5()
    build_c6()
    build_card()
    build_audio()
    write_spec()
    print("ALL-SEGMENTS-DONE -> %s" % BUILD)


if __name__ == "__main__":
    main()
