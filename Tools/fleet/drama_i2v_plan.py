#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drama_i2v_plan.py — D4 的「KF 图 → i2v manifest」桥（产线第二个真断点）。

为什么（2026-11-20 实测）：D3 出图之后没有任何工序能把 KF 变成 i2v 的输入。
`local-i2v/h3_i2v_album.py` 吃的是 MV 专辑的 manifest 格式，但生成那份 manifest 的
工序只服务 MV；drama 侧全空 → D4 永远 BLOCKED。

本文件只做确定性转换（不做创作判断）：
  kf_prompts.json + kf/*.png  →  <ep>/i2v_manifest.json
输出 unit = {id, shot, track, win_s, src_s, speed, width, height, light,
             frame, note, i2v_prompt, frame_bytes, prompt_words}
i2v_prompt = 运动描述（镜头机位 + 主体微动作），由 detail_en 与轨位推导：
  铁律（承 2026-11-14 H3 判例）：只描述"要发生变化的部位+环境"，起始态非目标的部位
  绝不给目标态指令（例如 KF 唇微张就不要写 lips closed）。

用法：
  python Tools/fleet/drama_i2v_plan.py --ep 1
  python Tools/fleet/drama_i2v_plan.py --ep 1 --width 768 --height 1344 --max-s 6
Exit: 0 写出；3 无可用帧
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

CAM = {
    'static': 'locked-off camera, no camera movement',
    'pushin': 'the camera pushes in slowly with small amplitude',
    'pullout': 'the camera pulls back slowly with small amplitude',
    'pan': 'the camera pans laterally with small amplitude',
    'tilt': 'the camera tilts slightly with small amplitude',
    'track': 'the camera tracks sideways with small amplitude',
    'handheld': 'a faint handheld drift keeps the frame alive',
}


def motion_of(detail):
    t = (detail or '').lower()
    if any(k in t for k in ('descending', 'diving', 'push', 'dolly in', 'zoom in')):
        return 'pushin'
    if any(k in t for k in ('pull', 'zoom out', 'recede')):
        return 'pullout'
    if 'pan' in t:
        return 'pan'
    if 'tilt' in t:
        return 'tilt'
    if any(k in t for k in ('track', 'follow', 'lateral')):
        return 'track'
    if any(k in t for k in ('handheld', 'shaky')):
        return 'handheld'
    return 'static'


def build_prompt(detail, cam, has_person):
    """运动提示词：环境先动，人只做一件事（禁双表情/禁口型指令）。"""
    env = 'the rain streaks and the ambient light shift slightly'
    low = (detail or '').lower()
    if any(k in low for k in ('rain', 'storm')):
        env = 'the rain streaks fall and the backlight flickers slightly'
    elif any(k in low for k in ('city', 'skyline', 'neon')):
        env = 'distant neon flickers and city haze drifts slowly'
    elif any(k in low for k in ('candle', 'fire', 'torch')):
        env = 'the flame breathes and the light on the surfaces shifts'
    elif any(k in low for k in ('crowd', 'trading hall', 'traders')):
        env = 'the crowd sways and the background noise of bodies shifts'
    elif any(k in low for k in ('notebook', 'paper', 'pages')):
        env = 'the paper edges lift and settle in the air'
    body = ('the figure holds still, only a slow breath in the shoulders'
            if has_person else 'no person enters the frame')
    return ('Single continuous take at 24fps, vertical 9:16. %s; %s; %s. '
            'Restrained cinematic motion, camera and subject motion only, no text, no logos.'
            % (CAM[cam], body, env))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", type=int, required=True)
    ap.add_argument("--root", default=os.path.join(ROOT, "cph4", "fleet", "out", "drama"))
    ap.add_argument("--width", type=int, default=768)
    ap.add_argument("--height", type=int, default=1344)
    ap.add_argument("--max-s", type=float, default=6.0, help="单镜上限（H3 本机实测 >10s 不可单烧）")
    ap.add_argument("--speed", type=float, default=1.0)
    a = ap.parse_args(argv)

    base = os.path.join(a.root, "EP%03d" % a.ep)
    plan = os.path.join(base, "kf_prompts.json")
    if not os.path.isfile(plan):
        print("I2V-PLAN ABORT kf_prompts missing: %s（先跑 drama_kf_plan.py）" % plan)
        return 3
    rows = json.load(open(plan, encoding="utf-8"))
    units, missing = [], []
    for r in rows:
        fp = os.path.join(base, "kf", r["id"] + ".png")
        if not os.path.isfile(fp):
            missing.append(r["id"])
            continue
        dur = float(r.get("dur") or 3.0)
        win = min(dur, a.max_s)
        cam = motion_of(r.get("prompt", ""))
        units.append({
            "id": "EP%03d_%s" % (a.ep, r["id"].split("_")[-1]),
            "shot": r["id"],
            "track": "EP%03d" % a.ep,
            "win_s": round(win, 2),
            "src_s": round(win, 2),
            "speed": a.speed,
            "width": a.width,
            "height": a.height,
            "light": r.get("light", "day"),
            "frame": os.path.relpath(fp, ROOT).replace("\\", "/"),
            "note": (r.get("sub") or "")[:60],
            "i2v_prompt": build_prompt(r.get("prompt", ""), cam, bool(r.get("ids"))),
            "frame_bytes": os.path.getsize(fp),
            "prompt_words": len(build_prompt(r.get("prompt", ""), cam, bool(r.get("ids"))).split()),
        })
    if not units:
        print("I2V-PLAN no frames for EP%03d (missing=%d)" % (a.ep, len(missing)))
        return 3
    man = {
        "policy": "漫剧 EP%03d D4 i2v（%d 镜·%dx%d·锁定机位·禁口型指令）" % (
            a.ep, len(units), a.width, a.height),
        "gate": "D3 帧已出（drama_kf_batch 回执）",
        "wave": "drama-ep%03d" % a.ep,
        "total": len(units),
        "total_win_s": round(sum(u["win_s"] for u in units), 2),
        "units": units,
    }
    outp = os.path.join(base, "i2v_manifest.json")
    json.dump(man, open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("I2V-PLAN EP%03d units=%d win=%.1fs missing_frames=%d -> %s" % (
        a.ep, len(units), man["total_win_s"], len(missing), os.path.relpath(outp, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
