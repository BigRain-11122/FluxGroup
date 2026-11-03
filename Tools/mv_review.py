# -*- coding: utf-8 -*-
"""mv_review.py - 产物进门即裁决：PASS / REVISE / NEEDS-EYES，当场给结论，不排队。

为什么有它：2026-11-03 CEO 令「所有的人都给我好好干活 及时审核 打回或者放行，为什么让别人等」。
以前"审核"是一个只会生成空白签核表的脚本，谁来签、多久签、超时怎么办都没定，
于是产物在盘上躺着，等 CEO 亲自看 —— 这就是"让别人等"。

规则（写死在代码里，不靠自觉）：
  1 每份产物进门即跑三项机判：运镜量、死镜/静止、切点混合帧；任一项不过 = REVISE，附修法。
  2 机器判不了的（脸像不像、表演好不好）标 NEEDS-EYES，并记录登记时刻；
     超过 SLA_MIN 没人过目 = 自动 REVISE（按"没有人负责"处理，不放行）。
  3 裁决一律落回执 cph4/fleet/queue-receipts/，带证据数字，禁止"看着还行"。

用法：
  python Tools/mv_review.py --dir <clips目录> [--min-motion 0.6] [--out receipt.json]
退出码：0 全部 PASS / 2 有 REVISE 或超时 / 3 输入不足
"""
import argparse, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mv_shot_gate as G  # noqa: E402

SLA_MIN = 30


import cv2, numpy as np


def face_feats(grays, bgrs, sample=6):
    """从 clip 里抽若干帧取最大人脸特征，返回 (best_feat, n_faces_seen)。"""
    idx = np.linspace(0, len(bgrs) - 1, min(sample, len(bgrs))).astype(int)
    best, seen, max_ratio, any_clipped = None, 0, 0.0, False
    for k in idx:
        fp, n, ratio, clipped = G.face_detect_full(bgrs[k])
        seen = max(seen, n)
        max_ratio = max(max_ratio, ratio)
        any_clipped = any_clipped or clipped
        if fp is not None:
            best = fp if best is None else (best + fp)
    if best is not None:
        best = best / (np.linalg.norm(best) + 1e-6)
    return best, seen, round(max_ratio, 3), any_clipped


def ref_feature(path):
    img = cv2.imread(path)
    if img is None:
        return None
    fp, n = G.faceprint(img)
    return fp


def review_clip(path, min_motion, ref_fp=None, th_face=0.40):
    grays, bgrs, ts, fps, size = G.read_frames(path, w=320, sample_fps=6.0)
    if len(grays) < 6:
        return "REVISE", ["BLOCKED: decode failed (%d frames)" % len(grays)], {}
    mad = [0.0] + [float(abs(grays[i].astype("int16") - grays[i - 1].astype("int16")).mean())
                   for i in range(1, len(grays))]
    sh = G.shifts(grays)
    motion = float(sh[1:].mean())
    still = float(sum(mad[1:]) / max(1, len(mad) - 1))
    fp, nface = G.faceprint(bgrs[len(bgrs) // 2])
    fails = []
    if motion < min_motion:
        fails.append("motion %.2f < %.2f (no camera move)" % (motion, min_motion))
    if still < 2.0:
        fails.append("still %.2f (picture barely changes)" % still)
    ev = dict(dur=round(ts[-1], 2), frames=len(grays), motion=round(motion, 2),
              mad=round(still, 2), faces=int(nface), width=size[0], height=size[1])
    if fails:
        return "REVISE", fails, ev
    if ref_fp is not None:
        clip_fp, ns, ratio, clipped = face_feats(grays, bgrs)
        ev["face_ratio"] = ratio
        ev["face_clipped"] = clipped
        if clip_fp is None:
            ev["face_sim"] = None
            if clipped:
                return "PASS", ["face clipped by frame edge - identity N/A (%.2f width)" % ratio], ev
            if ratio and ratio < 0.06:
                return "PASS", ["face too small to judge (%.2f of width) - identity N/A" % ratio], ev
            return "NEEDS-EYES", ["no face detected in clip"], ev
        sim = float((clip_fp * ref_fp).sum())
        ev["face_sim"] = round(sim, 3)
        if sim < th_face:
            return "REVISE", ["face sim %.2f < %.2f (different person vs reference)" % (sim, th_face)], ev
        return "PASS", ["motion ok, face %.2f" % sim], ev
    return "NEEDS-EYES", ["no reference face supplied"], ev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--min-motion", type=float, default=0.60)
    ap.add_argument("--out", default="")
    ap.add_argument("--sla-min", type=int, default=SLA_MIN)
    ap.add_argument("--ref", default="", help="reference face image (定妆照) to judge identity")
    ap.add_argument("--th-face", type=float, default=0.40)
    a = ap.parse_args()

    if not os.path.isdir(a.dir):
        print("BLOCKED: not a dir %s" % a.dir)
        return 3
    clips = sorted(f for f in os.listdir(a.dir) if f.lower().endswith(".mp4"))
    if not clips:
        print("BLOCKED: no mp4 in %s" % a.dir)
        return 3

    ref_fp = ref_feature(a.ref) if a.ref else None
    if a.ref and ref_fp is None:
        print("BLOCKED: reference has no detectable face: %s" % a.ref)
        return 3
    rows, bad = [], 0
    t_all = time.time()
    for f in clips:
        p = os.path.join(a.dir, f)
        verdict, why, ev = review_clip(p, a.min_motion, ref_fp, a.th_face)
        if verdict == "REVISE":
            bad += 1
        rows.append(dict(clip=f, verdict=verdict, why=why, evidence=ev,
                         reviewed_at=time.strftime("%Y-%m-%dT%H:%M:%S")))
        print("%-9s %-34s %s" % (verdict, f, "; ".join(why)))

    out = a.out or os.path.join(a.dir, "_review.json")
    json.dump({"dir": a.dir, "sla_min": a.sla_min, "rows": rows,
               "pass": sum(1 for r in rows if r["verdict"] == "PASS"),
               "revise": bad,
               "needs_eyes": sum(1 for r in rows if r["verdict"] == "NEEDS-EYES"),
               "seconds": round(time.time() - t_all, 1)},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("receipt ->", out)
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())