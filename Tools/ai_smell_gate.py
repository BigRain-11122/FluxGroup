# -*- coding: utf-8 -*-
"""ai_smell_gate.py - AI 脸 / AI 味 / AI 穿帮 闸（CEO：讨厌 AI 感，AI 是工具，成品要是艺术）。

十项机判（每项都能落到具体像素原因），外加人眼清单：
  skin 皮肤高频<42 · sym 镜像差<6.5 · catch 眼神光∉[1,3] · noise 噪声σ<1.2
  sat 高饱和平坦>22% · clone 同帧脸相似≥0.80
  hue 色相熵<2.4 · lc 局部对比度σ<9 · skinvar 肤色abσ<6 · eyebig 眼过大
用法：
  python Tools/ai_smell_gate.py --src <视频|目录> [--fps 1] [--json out.json]
  python Tools/ai_smell_gate.py --calibrate <应通过目录> <应拒绝目录>
退出码 0 PASS / 2 有问题 / 3 输入不足
"""
import argparse, json, os, subprocess, sys
import numpy as np
try:
    import cv2
except ImportError:
    print("BLOCKED: opencv-python missing"); sys.exit(3)

DET_MODEL = r"D:\AI\models\face\yunet.onnx"
REC_MODEL = r"D:\AI\models\face\sface.onnx"
TH = dict(skin=1.5, sym=8.0, noise=1.2, sat=0.75, clone=0.80,
          hue=1.2, lc=0.06, skinvar=8.0, eye=0.72)
FACE_MIN = 0.08   # face width <8% -> skin/sym/catch untrusted
CHECKS = ["skin", "sym", "catch", "noise", "sat", "clone", "hue", "lc", "skinvar", "eyebig"]


def _models():
    if not (os.path.exists(DET_MODEL) and os.path.exists(REC_MODEL)):
        return None, None
    return (cv2.FaceDetectorYN.create(DET_MODEL, "", (320, 320), 0.6, 0.3, 500),
            cv2.FaceRecognizerSF.create(REC_MODEL, ""))


DET, REC = _models()


def faces(img):
    if DET is None:
        return []
    h, w = img.shape[:2]; DET.setInputSize((w, h))
    _, f = DET.detect(img)
    return [] if f is None else list(f)


def feat(img, box):
    try:
        v = REC.feature(REC.alignCrop(img, box)).flatten().astype(np.float32)
        return v / (np.linalg.norm(v) + 1e-6)
    except Exception:
        return None


def metrics(img):
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    fs = faces(img); m = {}
    big = max(fs, key=lambda x: x[2] * x[3]) if fs else None

    if big is not None:
        x, y, bw, bh = [int(v) for v in big[:4]]; bw, bh = max(2, bw), max(2, bh)
        # skin
        cx, cy = x + bw // 2, y + int(bh * 0.62); r = max(4, int(min(bw, bh) * 0.18))
        patch = gray[max(0, cy - r):cy + r, max(0, cx - r):cx + r]
        m["skin"] = float(cv2.Laplacian(patch, cv2.CV_64F).var()) if patch.size else 999.0
        # sym
        crop = gray[y:y + bh, x:x + bw]
        m["sym"] = (float(np.mean(cv2.absdiff(crop, cv2.resize(cv2.flip(crop, 1), (crop.shape[1], crop.shape[0])))))
                    if crop.size else 99.0)
        # catch
        eye = gray[max(0, y + int(bh * .28)):y + int(bh * .50), max(0, x + int(bw * .12)):x + int(bw * .88)]
        if eye.size:
            _, th = cv2.threshold(eye, min(250, int(np.percentile(eye, 99.6))), 255, cv2.THRESH_BINARY)
            m["catch"] = max(0, cv2.connectedComponents(th)[0] - 1)
        else:
            m["catch"] = 2
        # clone
        if len(fs) >= 2:
            vs = [v for v in (feat(img, b) for b in fs) if v is not None]
            m["clone"] = max([float(vs[i].dot(vs[j])) for i in range(len(vs)) for j in range(i + 1, len(vs))] or [0.0])
        else:
            m["clone"] = 0.0
        # skinvar
        c = img[y:y + bh // 2, x:x + bw]
        m["skinvar"] = float(cv2.cvtColor(c, cv2.COLOR_BGR2LAB)[:, :, 1:].std()) if c.size else 99.0
        # eyebig (脸宽高比>0.85 且眼区占比高 -> 网红脸倾向)
        m["face_ratio"] = bw / float(w)
        m["eyebig"] = (bw / float(bh)) * (eye.shape[1] / float(bw) if eye.size else 0.0)
    else:
        m.update(skin=999.0, sym=99.0, catch=2, clone=0.0, skinvar=99.0, eyebig=0.0, face_ratio=0.0)

    c = gray[int(h * .3):int(h * .7), int(w * .3):int(w * .7)]
    m["noise"] = float(cv2.Laplacian(c, cv2.CV_64F).std()) if c.size else 99.0
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    flat = cv2.blur(np.abs(cv2.Laplacian(gray, cv2.CV_64F)).astype(np.float32), (9, 9)) < 3.0
    m["sat"] = float(((hsv[:, :, 1] > 190) & flat).mean())
    hue = hsv[:, :, 0][hsv[:, :, 1] > 40]
    if hue.size > 1000:
        p = np.bincount((hue // 8).astype(np.int32), minlength=23).astype(np.float64); p /= p.sum()
        m["hue"] = float(-(p[p > 0] * np.log2(p[p > 0])).sum())
    else:
        m["hue"] = 9.0
    lc = cv2.blur(cv2.Laplacian(gray, cv2.CV_64F).astype(np.float32), (31, 31))
    m["lc"] = float(lc.std())
    return m


def flags(m):
    """返回可疑项 key 列表。注意方向：有的值越低越可疑。"""
    out = []
    if m.get("face_ratio",1.0)>=FACE_MIN and m["skin"] < TH["skin"]: out.append("skin")
    if m.get("face_ratio",1.0)>=FACE_MIN and m["sym"] < TH["sym"]: out.append("sym")
    if m.get("face_ratio",1.0)>=FACE_MIN and (m["catch"] < 1 or m["catch"] > 3): out.append("catch")
    if m["noise"] < TH["noise"]: out.append("noise")
    if m["sat"] > TH["sat"]: out.append("sat")
    if m["clone"] >= TH["clone"]: out.append("clone")
    if m["hue"] < TH["hue"]: out.append("hue")
    if m["lc"] < TH["lc"]: out.append("lc")
    if m.get("face_ratio",1.0)>=FACE_MIN and m["skinvar"] < TH["skinvar"]: out.append("skinvar")
    if m["eyebig"] > TH["eye"]: out.append("eyebig")
    return out


def frames_of(src, fps):
    if os.path.isdir(src):
        for n in sorted(os.listdir(src)):
            if n.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                p = os.path.join(src, n); img = cv2.imread(p)
                if img is not None:
                    yield p, img
        return
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", "fps=%g" % fps,
                        "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    buf, off, i = p.stdout, 0, 0
    while off < len(buf):
        j = buf.find(b"IEND", off)
        if j < 0: break
        arr = cv2.imdecode(np.frombuffer(buf[off:j + 8], np.uint8), cv2.IMREAD_COLOR)
        if arr is not None:
            yield "t=%06.2fs" % (i / float(fps)), arr
        i += 1; off = j + 8


def calibrate(pass_dir, reject_dir):
    """按「应通过 / 应拒绝」两组算分离度，给出建议阈值（不自动改代码）。"""
    def collect(d):
        return [metrics(img) for _, img in frames_of(d, 1.0)]
    P, R = collect(pass_dir), collect(reject_dir)
    if not P or not R:
        print("BLOCKED: 两组样本都要有图"); return 3
    rep = {"n_pass": len(P), "n_reject": len(R), "metrics": {}}
    for k in ["skin", "sym", "noise", "hue", "lc", "skinvar"]:
        pv = np.array([m[k] for m in P]); rv = np.array([m[k] for m in R])
        # 假设"低=可疑"：阈值取两组之间（越小越可疑）
        thr = (np.percentile(pv, 20) + np.percentile(rv, 80)) / 2
        sep = (np.percentile(pv, 20) - np.percentile(rv, 80)) / (pv.std() + 1e-6)
        rep["metrics"][k] = {"pass_p20": round(float(np.percentile(pv, 20)), 2),
                             "reject_p80": round(float(np.percentile(rv, 80)), 2),
                             "suggest": round(float(thr), 2), "separation_sigma": round(float(sep), 2),
                             "usable": bool(sep > 0.5)}
    for k in ["sat", "clone", "eyebig"]:
        pv = np.array([m[k] for m in P]); rv = np.array([m[k] for m in R])
        thr = (np.percentile(pv, 80) + np.percentile(rv, 20)) / 2
        sep = (np.percentile(rv, 20) - np.percentile(pv, 80)) / (pv.std() + 1e-6)
        rep["metrics"][k] = {"pass_p80": round(float(np.percentile(pv, 80)), 3),
                             "reject_p20": round(float(np.percentile(rv, 20)), 3),
                             "suggest": round(float(thr), 3), "separation_sigma": round(float(sep), 2),
                             "usable": bool(sep > 0.5)}
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src"); ap.add_argument("--fps", type=float, default=1.0)
    ap.add_argument("--json"); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--calibrate", nargs=2, metavar=("PASS_DIR", "REJECT_DIR"))
    a = ap.parse_args()
    if a.calibrate:
        return calibrate(a.calibrate[0], a.calibrate[1])
    if not a.src:
        ap.error("--src required")
    rows, n, adv = [], 0, 0
    # 强证据（可直接判可疑）与弱证据（只做提示）分开：弱项在暗光/小脸镜上天然误报，
    # 混进 verdict 会让闸变成噪音，最后没人看（旧闸就是这么死的）。
    STRONG = ("skin", "sym", "clone", "skinvar")
    for name, img in frames_of(a.src, a.fps):
        m = metrics(img); fl = flags(m); n += 1
        st = [x for x in fl if x in STRONG]
        wk = [x for x in fl if x not in STRONG]
        if st or wk:
            if wk and not st:
                adv += 1
            rows.append({"frame": name, "strong": st, "advisory": wk,
                         "detail": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()}})
            if a.limit and len([r for r in rows if r["strong"]]) >= a.limit: break
    hard = [r for r in rows if r["strong"]]
    verdict = "PASS" if not hard else ("REVISE" if len(hard) >= 3 else "NEEDS-EYES")
    receipt = {"gate": "ai-smell", "src": a.src, "frames": n, "flagged": len(rows),
               "thresholds": TH, "verdict": verdict, "rows": rows,
               "needs_eyes": ["发丝成块", "牙齿连片", "多指多肢", "物体穿插/悬空", "镜面倒影不符", "画面内文字乱码", "头身比失真"],
               "note": "阈值未标定前只作参考，不得作放行依据"}
    out = a.json or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                                 "cph4", "fleet", "queue-receipts", "ai-smell-latest.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"frames": n, "flagged": len(rows), "verdict": verdict, "out": out}, ensure_ascii=False))
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())