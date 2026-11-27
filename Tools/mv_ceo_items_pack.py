# -*- coding: utf-8 -*-
"""mv_ceo_items_pack.py - build the evidence packs for the three remaining mv0001 CEO items.

Why: after Q-MV-0001-001..011 the machine side is done; what still blocks sign-off is human
judgment (11 static->jump points, era blind test, shot double-sign). Those judgments are slow
and error-prone when the evidence is scattered across D:\\FleetWorker\\review. This script
turns existing measurements into three ready-to-judge packs. It reuses the artifacts already
produced (aesthetic/trans/flags json) and does not re-measure anything.

Items:
  signoff   - one row per shot (95) with era/metrics/duplicate flag + empty signature columns
  erablind  - blind shuffled stills (era label removed) + separate answer key
  staticjump- 3x3 frame strip per STATIC_JUMP point + metrics row

Usage:
  py mv_ceo_items_pack.py --out D:\\FleetWorker\\review\\ceo_items_v717 [--mode all|signoff|erablind|staticjump]
"""
import argparse
import json
import os
import random

import cv2

REVIEW = r"D:\FleetWorker\review"
VIDEO = (r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover"
         r"\outbound\krea2\30s-reel-v1\full_mv_v717.mp4")
AESTHETIC = os.path.join(REVIEW, "aesthetic_v717.json")
TRANS = os.path.join(REVIEW, "trans_v717.json")
RECONCILE = os.path.join(REVIEW, "reconcile_v717.json")
SEED = 20261028
PER_ERA = 12


def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _frames(cap, idxs, tile=(336, 189)):
    out = []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    for i in idxs:
        i = max(0, min(total - 1, int(i)))
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, fr = cap.read()
        if not ok:
            fr = None
        else:
            fr = cv2.resize(fr, tile, interpolation=cv2.INTER_AREA)
        out.append((i, fr))
    return out


def _label(img, text):
    cv2.rectangle(img, (0, 0), (img.shape[1], 18), (0, 0, 0), -1)
    cv2.putText(img, text, (4, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.38,
                (255, 255, 255), 1, cv2.LINE_AA)
    return img


def _blank(img, tile):
    import numpy as np
    return np.zeros((tile[1], tile[0], 3), dtype="uint8")


def build_signoff(out):
    aes = _load(AESTHETIC)
    rec = _load(RECONCILE) if os.path.exists(RECONCILE) else {}
    table = aes["table"]
    dup_t = set()
    for row in aes.get("duplicates") or []:
        if isinstance(row, list) and len(row) >= 2:
            dup_t.update([round(float(row[0]), 3), round(float(row[1]), 3)])
    amb = {round(float(t), 3) for t, _ in (aes.get("ambiguous_era") or [])}

    d = os.path.join(out, "signoff")
    os.makedirs(d, exist_ok=True)
    rows = []
    for r in table:
        t0 = round(float(r["t0"]), 3)
        rows.append({
            "shot": r["i"] + 1, "t0": t0, "t1": round(float(r["t1"]), 3),
            "dur": round(float(r["dur"]), 2), "luma": r["luma"], "sat": r["sat"],
            "warm": r["warm"], "motion": r["motion"], "era": r.get("era_group"),
            "era_score": round(float(r.get("era_score") or 0), 2),
            "era_ambiguous": t0 in amb, "reprise_dup": t0 in dup_t,
            "verdict_D": "", "verdict_S": "", "note": "",
        })
    payload = {
        "version": "v717",
        "counts": {"audit_shots": aes.get("shots"), "trans_points": (rec.get("counts") or {}).get("trans"),
                   "union_cuts": rec.get("union_cut_count"),
                   "trans_shot_boundaries": rec.get("trans_shot_boundaries")},
        "why": "One row per audit shot. Signatures are the human act; this sheet only pre-fills measurements.",
        "rows": rows,
    }
    with open(os.path.join(d, "SIGN-OFF-SHEET-v717.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    c = payload["counts"]
    lines = [
        "# mv0001 v717 逐镜双签表（95 镜）", "",
        "口径声明：本表以**逐镜审计 95 镜**为行单位（audit_shots=%s）；转场审计 %s 个切点、"
        "两口径联合真切点 %s；三口径差异见 `mv_shot_reconcile.py` 输出。"
        "签名前先确认本表口径即签字对象。" % (c["audit_shots"], c["trans_points"], c["union_cuts"]), "",
        "| # | t0 | t1 | 时长 | 亮度 | 饱和 | 暖度 | 运动 | 时代 | 时代分 | 歧义 | 重演重复 | 导演签 | 制监签 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append("| %d | %.3f | %.3f | %.2f | %s | %s | %s | %s | %s | %.2f | %s | %s |  |  |" % (
            r["shot"], r["t0"], r["t1"], r["dur"], r["luma"], r["sat"], r["warm"], r["motion"],
            r["era"], r["era_score"], "是" if r["era_ambiguous"] else "",
            "是" if r["reprise_dup"] else ""))
    lines += ["", "## 签名规则", "",
              "1. 每行必须写 PASS / REVISE + 一句自己的判断（复述机器数字不算独立审核）。",
              "2. REVISE 行必须给出生站（哪一站本该拦住）与修法，否则不收。",
              "3. 时代列标「歧义」的行（era_score 距阈值 7.0 不足 0.5）不参与时代盲测统计。", ""]
    with open(os.path.join(d, "SIGN-OFF-SHEET-v717.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return len(rows), os.path.join(d, "SIGN-OFF-SHEET-v717.md")


def build_erablind(out):
    aes = _load(AESTHETIC)
    thr = float(aes.get("epoch_thr") or 7.0)
    table = aes["table"]
    picks = []
    for grp in ("A", "B"):
        cand = [r for r in table if r.get("era_group") == grp
                and abs(float(r.get("era_score") or 0) - thr) >= 0.5]
        cand.sort(key=lambda r: -abs(float(r.get("era_score") or 0) - thr))
        for r in cand[:PER_ERA]:
            picks.append({"shot": r["i"] + 1, "t": round((r["t0"] + r["t1"]) / 2.0, 3),
                          "era": grp, "era_score": round(float(r.get("era_score") or 0), 2)})
    random.Random(SEED).shuffle(picks)

    d = os.path.join(out, "erablind")
    os.makedirs(d, exist_ok=True)
    cap = cv2.VideoCapture(VIDEO)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    key, missing = [], 0
    for n, p in enumerate(picks, 1):
        name = "blind_%02d.jpg" % n
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(p["t"] * fps)))
        ok, fr = cap.read()
        if not ok:
            missing += 1
            continue
        h, w = fr.shape[:2]
        if w > 768:
            fr = cv2.resize(fr, (768, int(h * 768.0 / w)), interpolation=cv2.INTER_AREA)
        cv2.imwrite(os.path.join(d, name), fr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        key.append({"file": name, "shot": p["shot"], "t": p["t"], "era": p["era"],
                    "era_score": p["era_score"]})
    cap.release()
    with open(os.path.join(d, "KEY.json"), "w", encoding="utf-8") as f:
        json.dump({"seed": SEED, "rule": "era_score distance >=0.5 from epoch_thr %.1f" % thr,
                   "answers": key}, f, ensure_ascii=False, indent=1)
    lines = ["# 时代盲测（v717）", "",
             "共 %d 张，顺序已用 seed=%d 打乱，纪元标签只在 KEY.json 里。" % (len(key), SEED), "",
             "作答表（填 A=远古 / B=现代 / 不确定）：", "",
             "| 文件 | 你的判断 | 确信度 1-5 | 依据（画面里哪一处） |", "|---|---|---|---|"]
    for k in key:
        lines.append("| %s |  |  |  |" % k["file"])
    lines += ["", "判据：跑完 ≥15 张再对 KEY。低于 4/5 命中率=时代区分不成立，回炉调色而不是调答案。", ""]
    with open(os.path.join(d, "ANSWERS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return len(key), missing, os.path.join(d, "ANSWERS.md")


def build_staticjump(out):
    trans = _load(TRANS)
    sj = [x for x in trans if str(x.get("verdict", "")).upper() == "STATIC_JUMP"]
    d = os.path.join(out, "staticjump")
    os.makedirs(d, exist_ok=True)
    cap = cv2.VideoCapture(VIDEO)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    tile = (336, 189)
    rows = []
    for n, e in enumerate(sj, 1):
        c = int(round(float(e["t"]) * fps))
        idxs = [c + (k - 4) * 2 for k in range(9)]
        sheet = None
        for k, (fi, fr) in enumerate(_frames(cap, idxs, tile)):
            img = fr if fr is not None else _blank(None, tile)
            img = _label(img.copy(), "f%d t=%.2f" % (fi, fi / fps))
            if sheet is None:
                import numpy as np
                sheet = np.zeros((tile[1] * 3, tile[0] * 3, 3), dtype="uint8")
            sheet[(k // 3) * tile[1]:(k // 3 + 1) * tile[1],
                  (k % 3) * tile[0]:(k % 3 + 1) * tile[0]] = img
        name = "sj%02d_t%07.3f.png" % (n, float(e["t"]))
        cv2.imwrite(os.path.join(d, name), sheet)
        rows.append({"n": n, "t": float(e["t"]), "frame": e.get("frame"), "file": name,
                     "luma_gap": e.get("luma_gap"), "mag_tail": e.get("mag_tail"),
                     "mag_head": e.get("mag_head"), "dir_cos": e.get("dir_cos"),
                     "g_tail": e.get("g_tail"), "g_head": e.get("g_head")})
    cap.release()
    with open(os.path.join(d, "staticjump-11.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    lines = ["# v717 静止接高速 11 处逐条判定", "",
             "每处一张 3x3 联系条（事件帧前后各 4 帧，步长 2 帧），帧号与时刻已烧在图左上角。", "",
             "判定只有两种合法结论：**真切点**（镜头边界，进双签表）或**镜内断裂**（本镜缺陷，返修）。"
             "第三种「看着像但我没把握」必须写明不确定点，不许留空。", "",
             "| # | t | 帧 | 亮度差 | 尾运动 | 头运动 | 方向余弦 | 判定 | 依据 |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %d | %.3f | %s | %s | %s | %s | %s |  |  |" % (
            r["n"], r["t"], r["frame"], r["luma_gap"], r["mag_tail"], r["mag_head"], r["dir_cos"]))
    lines += ["", "机器提示（不作结论）：mag_tail 与 mag_head 都 <0.2 且 luma_gap >15 = 静止间光度突变，"
              "优先怀疑真切点；任一运动 >0.5 而同帧画面同构 = 优先怀疑镜内断裂。", ""]
    with open(os.path.join(d, "STATIC-JUMP-11.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return len(rows), os.path.join(d, "STATIC-JUMP-11.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", default="all", choices=["all", "signoff", "erablind", "staticjump"])
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if not os.path.exists(VIDEO):
        raise SystemExit("video missing: %s" % VIDEO)
    if a.mode in ("all", "signoff"):
        n, p = build_signoff(a.out)
        print("SIGNOFF rows=%d -> %s" % (n, p))
    if a.mode in ("all", "erablind"):
        n, miss, p = build_erablind(a.out)
        print("ERABLIND images=%d missing=%d -> %s" % (n, miss, p))
    if a.mode in ("all", "staticjump"):
        n, p = build_staticjump(a.out)
        print("STATICJUMP points=%d -> %s" % (n, p))


if __name__ == "__main__":
    main()