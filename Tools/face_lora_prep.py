# -*- coding: utf-8 -*-
"""face_lora_prep.py — 单人面孔 LoRA 的素材闸与数据集生成（私有实验用）。

做四件事：检测人脸 → 过闸 → 去重 → 切图 + 出 caption + 出 kohya 配置。
不做：下载素材、训练、验收（训练走 kohya sd-scripts，验收走 mv_lora_eval.py）。

判据来源 = cph4/fleet/mv-album-001-jay/LORA-FACE-LIB-PLAN-v1.md §二/§四

用法：
  python Tools/face_lora_prep.py scan   <raw_dir> [--json out.json]
  python Tools/face_lora_prep.py build  <raw_dir> --out <dataset_dir> --trigger ohwx_woman
  python Tools/face_lora_prep.py config --dataset <dataset_dir> --trigger ohwx_woman --base flux --out train.toml
  python Tools/face_lora_prep.py selftest

退出码：0 达标 / 1 素材不足或不达标 / 2 输入错误 / 3 依赖缺失
"""
import argparse
import json
import os
import re
import shutil
import sys

try:
    import cv2
    import numpy as np
except ImportError:
    print("[BLOCKED] 需要 opencv-python 与 numpy", file=sys.stderr)
    raise SystemExit(3)

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# 闸线（首轮默认值，须用正负控标定后按机种改写——见 plan §四）
LAP_MIN = 60.0         # 原生尺度人脸区 Laplacian 方差下限（放大后再量会把糊图算清）
FACE_MIN_PX = 200      # 人脸短边像素下限（老照片现实值；512 以上才算理想）
FACE_GOOD_PX = 320
CLIP_MAX = 0.06        # 高光裁剪像素占比上限
PHASH_DIST = 8         # pHash 汉明距离 <= 此值判重复

# caption 里出现这些词=把身份写进描述，触发词就学不到人
IDENTITY_WORDS = [
    "big eyes", "large eyes", "high nose", "sharp nose", "v-shaped", "oval face",
    "thin lips", "full lips", "dimple", "double eyelid", "大眼", "高鼻", "瓜子脸",
]

CAPTION_BASE = "{trigger}, a photo of a woman, natural skin texture with visible pores, " \
               "unretouched, film grain, soft even light"

MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models",
                     "face_detection_yunet_2023mar.onnx")
MODEL_SFACE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models",
                           "face_recognition_sface_2021dec.onnx")
_DET = None
_REC = None


def list_images(root):
    out = []
    for base, _, files in os.walk(root):
        for fn in sorted(files):
            if os.path.splitext(fn)[1].lower() in EXTS:
                out.append(os.path.join(base, fn))
    return out


def detect_faces(img):
    """返回 [(x,y,w,h)]，按面积降序。OpenCV 5 用 YuNet，老版本回退 Haar。"""
    global _DET
    h, w = img.shape[:2]
    if hasattr(cv2, "FaceDetectorYN") and os.path.isfile(MODEL):
        if _DET is None:
            _DET = cv2.FaceDetectorYN.create(MODEL, "", (320, 320), 0.6, 0.3, 5000)
        _DET.setInputSize((w, h))
        _, faces = _DET.detect(img)
        if faces is None:
            return []
        # 只留高置信框：远景路人/虚化剪影常被误检成小脸，会把主脸挤掉
        out = [tuple(int(v) for v in f[:4]) for f in faces if float(f[14]) >= 0.75]
        return sorted(out, key=lambda r: r[2] * r[3], reverse=True)
    if hasattr(cv2, "CascadeClassifier"):
        cas = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades,
                                                 "haarcascade_frontalface_default.xml"))
        eq = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        faces = cas.detectMultiScale(eq, scaleFactor=1.08, minNeighbors=6, minSize=(60, 60))
        return sorted([tuple(int(v) for v in f) for f in faces],
                      key=lambda r: r[2] * r[3], reverse=True)
    raise SystemExit("[BLOCKED] 无人脸检测器：需 cv2.FaceDetectorYN + " + MODEL)


def laplacian_var(gray_face):
    return float(cv2.Laplacian(gray_face, cv2.CV_64F).var())


def _eval_scale(crop, cap=512):
    """清晰度只在原生或降采样尺度上量：放大插值会凭空造高频，把糊图量成清晰。"""
    h, w = crop.shape[:2]
    m = max(h, w)
    if m <= cap:
        return crop
    s = cap / float(m)
    return cv2.resize(crop, (max(1, int(w * s)), max(1, int(h * s))),
                      interpolation=cv2.INTER_AREA)


def clip_ratio(gray_face):
    """只量高光溢出：暗部死黑在夜戏里是正常造型，不该判负。"""
    n = max(int(gray_face.size), 1)
    hi = int((gray_face >= 250).sum())
    return hi / float(n)


def phash(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    d = cv2.dct(g)[:8, :8]
    med = np.median(d[1:])
    return "".join("1" if v > med else "0" for v in d.flatten())


def hamming(a, b):
    return sum(1 for x, y in zip(a, b) if x != y)


def text_line_score(img):
    """估"图里有多少成行文字"。返回 (行数, 最宽行占比, 文字行面积占比)。

    为什么要它（2026-11-17 标定）：360 搜「沈银河」会带出「讲沈银河新闻的李英爱截图」，
    这类短视频截屏满屏标题+字幕，脸是别人、还压着字。但**边缘水印不能一起删**——
    实测正常写真底部有一条台标/微博水印时 cover≈0.02，满屏字幕截图 cover≈0.09。
    所以判据用面积占比分开，不用"有没有文字"一刀切。
    """
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = g.shape[:2]
    if h > 480:
        g = cv2.resize(g, (int(w * 480.0 / h), 480), interpolation=cv2.INTER_AREA)
    gx = cv2.convertScaleAbs(cv2.Sobel(g, cv2.CV_16S, 1, 0, ksize=3))
    _, bw = cv2.threshold(gx, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    kw = max(9, int(bw.shape[1] * 0.03))
    rows = cv2.morphologyEx(bw, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (kw, 3)))
    n, _, stats, _ = cv2.connectedComponentsWithStats(rows, 8)
    lines, widest, cover = 0, 0.0, 0.0
    for i in range(1, n):
        _x, _y, ww, hh, area = stats[i]
        if hh > bw.shape[0] * 0.10 or ww < bw.shape[1] * 0.12:
            continue
        if ww / max(hh, 1) < 2.5:
            continue
        lines += 1
        widest = max(widest, ww / float(bw.shape[1]))
        cover += area
    return lines, widest, cover / float(bw.size or 1)


def evaluate(path, min_face_px=FACE_MIN_PX, lap_min=LAP_MIN):
    img = cv2.imread(path)
    if img is None:
        return {"path": path, "verdict": "REJECT", "reasons": ["unreadable"]}
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = detect_faces(img)
    if not faces:
        return {"path": path, "verdict": "REJECT", "reasons": ["no_face"], "size": [w, h]}

    x, y, fw, fh = faces[0]
    reasons, warns = [], []
    if len(faces) > 1:
        big = fw * fh
        # 阈值必须与 curate 的单脸判据一致（2026-11-17 统一为 0.60）。
        # 旧值 0.3 在下载端就把"旁边站个人"的写真全判死、进不了 keep/，
        # 下游 curate 再松也没用——实测 ql05 raw 100 张而 keep 只剩一小撮，
        # 就是这一处在最上游截流。
        others = [f for f in faces[1:] if f[2] * f[3] > 0.60 * big]
        if others:
            reasons.append("multi_face")

    face_px = min(fw, fh)
    if face_px < min_face_px:
        reasons.append("face_too_small")
    elif face_px < FACE_GOOD_PX:
        warns.append("face_small_warn")

    pad = int(1.45 * max(fw, fh) / 2)
    cx, cy = x + fw // 2, y + fh // 2
    x0, y0 = max(0, cx - pad), max(0, cy - pad)
    x1, y1 = min(w, cx + pad), min(h, cy + pad)
    crop = gray[y0:y1, x0:x1]
    if crop.size == 0:
        return {"path": path, "verdict": "REJECT", "reasons": ["bad_crop"]}
    crop512 = _eval_scale(crop)

    lap = laplacian_var(crop512)
    tight = gray[y:y + fh, x:x + fw]          # 过曝只在脸框内量，别把白背景算成死白
    clip = clip_ratio(tight) if tight.size else 1.0
    if lap < lap_min:
        reasons.append("blurry")
    if clip > CLIP_MAX:
        reasons.append("blown_out")
    if min(w, h) < 400:
        warns.append("small_source")
    # 满屏标题/字幕的短视频截图剔除；只有边缘水印的保留（cover 阈值见 text_line_score 注释）
    _tl, _tw, _tc = text_line_score(img)
    if _tc >= 0.04 or (_tl >= 4 and _tc >= 0.02):
        reasons.append("text_overlay")

    return {
        "path": path,
        "verdict": "REJECT" if reasons else ("WARN" if warns else "PASS"),
        "reasons": reasons,
        "warns": warns,
        "size": [w, h],
        "face_px": face_px,
        "face_ratio": round((fw * fh) / float(w * h), 4),
        "laplacian": round(lap, 1),
        "clip_ratio": round(clip, 4),
        "phash": phash(img),
        "text_cover": round(_tc, 4),
    }


def scan_dir(raw, min_face_px=FACE_MIN_PX, lap_min=LAP_MIN):
    rows = [evaluate(p, min_face_px, lap_min) for p in list_images(raw)]
    kept, seen = [], []
    for r in rows:
        if r["verdict"] == "REJECT":
            continue
        ph = r.get("phash")
        if ph and any(hamming(ph, s) <= PHASH_DIST for s in seen):
            r["verdict"] = "REJECT"
            r["reasons"].append("duplicate")
            continue
        if ph:
            seen.append(ph)
        kept.append(r)
    counts = {"total": len(rows), "pass": sum(1 for r in rows if r["verdict"] == "PASS"),
              "warn": sum(1 for r in rows if r["verdict"] == "WARN"),
              "reject": sum(1 for r in rows if r["verdict"] == "REJECT"),
              "usable": len(kept)}
    return {"rows": rows, "counts": counts}


def crop_and_save(path, out_path, size):
    img = cv2.imread(path)
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = detect_faces(img)
    if not faces:
        return False
    x, y, fw, fh = faces[0]
    pad = int(1.45 * max(fw, fh) / 2)
    cx, cy = x + fw // 2, y + fh // 2
    x0, y0 = max(0, cx - pad), max(0, cy - pad)
    x1, y1 = min(w, cx + pad), min(h, cy + pad)
    crop = img[y0:y1, x0:x1]
    if crop.size == 0:
        return False
    interp = cv2.INTER_AREA if crop.shape[0] > size else cv2.INTER_CUBIC
    cv2.imwrite(out_path, cv2.resize(crop, (size, size), interpolation=interp))
    return True


def detect_face_detail(img):
    """返回 (box, landmarks)。landmarks 为 YuNet 的 5 点：右眼、左眼、鼻尖、右嘴角、左嘴角。

    打 caption 需要关键点：只靠文件名猜角度（guess_tags）在爬来的 p0000.jpg 上永不命中，
    会让整份数据集的 caption 变成同一句，模型只能把「这张脸+这套光」当固定搭配。
    """
    global _DET
    h, w = img.shape[:2]
    if hasattr(cv2, "FaceDetectorYN") and os.path.isfile(MODEL):
        if _DET is None:
            _DET = cv2.FaceDetectorYN.create(MODEL, "", (320, 320), 0.6, 0.3, 5000)
        _DET.setInputSize((w, h))
        _, faces = _DET.detect(img)
        if faces is None:
            return None, None
        cand = [f for f in faces if float(f[14]) >= 0.75]
        if not cand:
            return None, None
        best = max(cand, key=lambda f: f[2] * f[3])
        box = tuple(int(v) for v in best[:4])
        pts = [(float(best[4 + i * 2]), float(best[5 + i * 2])) for i in range(5)]
        return box, pts
    fs = detect_faces(img)
    return (fs[0], None) if fs else (None, None)


def pose_label(pts):
    """头朝向：鼻尖相对两眼中点的水平偏移 / 眼距。>0.30 判侧脸（不训练，仅作测试）。"""
    if not pts:
        return ""
    (ax, ay), (bx, by), (nx, _ny) = pts[0], pts[1], pts[2]
    eye_dist = max(abs(bx - ax), 1.0)
    off = (nx - (ax + bx) / 2.0) / eye_dist
    if abs(off) > 0.30:
        base = "side profile"
    elif abs(off) > 0.13:
        base = "head turned " + ("left" if off > 0 else "right")
    else:
        base = "front view"
    roll = np.degrees(np.arctan2(by - ay, bx - ax))
    if abs(roll) > 14:
        base += ", head tilted"
    return base


def smile_label(pts):
    """表情只做粗判（单张无中性基线），宁可漏标也不误标——表情被学成身份是大忌。

    阈值实测标定（2026-11-13·60 张徐若瑄素材）：drop 连续分布无双峰，
    p10=0.349 / p50=0.444；0.175~0.19 三张明显在笑。取 0.34 抓约 10%，
    不按 plan 的 30% 硬凑——把中性标成 smiling 会让模型把"笑"当默认表情。
    """
    if not pts:
        return ""
    (ax, _ay), (bx, _by), (_nx, ny) = pts[0], pts[1], pts[2]
    (_mrx, mry), (_mlx, mly) = pts[3], pts[4]
    eye_dist = max(abs(bx - ax), 1.0)
    drop = ((mry + mly) / 2.0 - ny) / eye_dist   # 嘴角比鼻尖低多少（越小=嘴越上提）
    if drop < 0.22:
        return "laughing"
    if drop < 0.34:
        return "smiling"
    return ""


def light_label(img, box):
    """光位：用高光比例、脸部与背景亮度比、色温判四类老照片常见光。"""
    h, w = img.shape[:2]
    x, y, fw, fh = box
    x0, y0, x1, y1 = max(0, x), max(0, y), min(w, x + fw), min(h, y + fh)
    face = img[y0:y1, x0:x1]
    if face.size == 0:
        return ""
    g = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    L = float(g.mean())
    hi = float((g >= 245).mean())
    b, _gr, r = (float(face[:, :, i].mean()) for i in range(3))
    warm = r - b
    gray_all = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mask = np.ones((h, w), np.uint8)
    mask[y0:y1, x0:x1] = 0
    bgL = float(gray_all[mask == 1].mean()) if mask.sum() else L
    if hi > 0.04 and bgL < L * 0.75:
        return "direct flash photography"
    if L < 78:
        return "low light night scene"
    if bgL > L * 1.15:
        return "daylight"
    if warm > 22:
        return "warm indoor light"
    return "soft even light"


def detect_face_row(img):
    """返回 YuNet 原始 15 维检测行（SFace 对齐与特征提取需要完整向量）。"""
    global _DET
    h, w = img.shape[:2]
    if not (hasattr(cv2, "FaceDetectorYN") and os.path.isfile(MODEL)):
        return None
    if _DET is None:
        _DET = cv2.FaceDetectorYN.create(MODEL, "", (320, 320), 0.6, 0.3, 5000)
    _DET.setInputSize((w, h))
    _, faces = _DET.detect(img)
    if faces is None:
        return None
    cand = [f for f in faces if float(f[14]) >= 0.75]
    if not cand:
        return None
    return max(cand, key=lambda f: f[2] * f[3])


def get_recognizer():
    global _REC
    if _REC is None:
        if not (hasattr(cv2, "FaceRecognizerSF") and os.path.isfile(MODEL_SFACE)):
            raise SystemExit("[BLOCKED] 需要 cv2.FaceRecognizerSF + " + MODEL_SFACE)
        _REC = cv2.FaceRecognizerSF.create(MODEL_SFACE, "")
    return _REC


def face_embedding(img, row):
    rec = get_recognizer()
    # alignCrop 要求 1x15 的 float32；传裸 15 维会抛 cv2.error
    box = np.asarray(row, dtype=np.float32).reshape(1, 15)
    return rec.feature(rec.alignCrop(img, box)).flatten().astype(np.float32)


def _cos(a, b):
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def make_contact_board(paths, out_path, cols=6, cell=200):
    """抽检板：让人一眼看出这批是不是同一个人（机器判据之外的最后一道人眼关）。"""
    if not paths:
        return False
    # cv2.imwrite 不建父目录，缺了会静默失败
    parent = os.path.dirname(os.path.abspath(out_path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    rows = (len(paths) + cols - 1) // cols
    board = np.full((rows * cell, cols * cell, 3), 32, np.uint8)
    for i, p in enumerate(paths):
        img = cv2.imread(p)
        if img is None:
            continue
        h, w = img.shape[:2]
        s = cell / float(max(h, w))
        img = cv2.resize(img, (max(1, int(w * s)), max(1, int(h * s))))
        r, c = divmod(i, cols)
        board[r * cell:r * cell + img.shape[0], c * cell:c * cell + img.shape[1]] = img
    cv2.imwrite(out_path, board)
    return True


def _knn_scores(sims: "np.ndarray", k: int = 8) -> "np.ndarray":
    """每张图与最近的 k 张的平均相似度 = 一致性分。

    实测依据（2026-11-13·张柏芝 44 张）：kNN 分 p0=0.403/p50=0.630/max=0.709；
    抽检板确认最低 6 张里 5 张是别人（戴帽网红、蓝吊带、短发女等）。
    混入者与目标人互相不像，所以"最近邻平均"天然把他们压到底部，
    比"到质心距离"稳——同族名人质心相似度也会 >0.6，单阈值剔不干净。
    """
    n = sims.shape[0]
    k = max(1, min(k, n - 1))
    s = sims.copy()
    np.fill_diagonal(s, -1.0)
    return np.sort(s, axis=1)[:, -k:].mean(axis=1)


def curate(src, out, keep=45, min_sim=0.20, board=None, link_thr=0.58):
    """人物一致性挑选：剔除混进来的他人脸与合影，再按质量排序取最优。

    三道判据，缺一都会训废：
      1. 合影不进：检测到第二张脸且面积接近主脸 → 主脸可能不是目标人
      2. kNN 一致性分低于阈值 → 与这批主体不像，判混入
      3. 质量排序：清晰度 + 脸尺寸，取最优 keep 张
    """
    paths = list_images(src)
    rows = []
    errs = []
    skipped_multi = 0
    skipped_text = 0
    for p in paths:
        img = cv2.imread(p)
        if img is None:
            continue
        h0, w0 = img.shape[:2]
        global _DET
        if _DET is None and os.path.isfile(MODEL):
            _DET = cv2.FaceDetectorYN.create(MODEL, "", (320, 320), 0.6, 0.3, 5000)
        faces = None
        if _DET is not None:
            _DET.setInputSize((w0, h0))
            _, faces = _DET.detect(img)
        if faces is None:
            continue
        cand = [f for f in faces if float(f[14]) >= 0.75]
        if not cand:
            continue
        cand.sort(key=lambda f: f[2] * f[3], reverse=True)
        if len(cand) > 1 and float(cand[1][2] * cand[1][3]) > 0.60 * float(cand[0][2] * cand[0][3]):
            skipped_multi += 1
            continue
        _tl, _tw, _tc = text_line_score(img)
        if _tc >= 0.04 or (_tl >= 4 and _tc >= 0.02):
            skipped_text += 1
            continue
        row = cand[0]
        try:
            emb = face_embedding(img, row)
        except Exception as e:
            if len(errs) < 3:
                errs.append(f"{os.path.basename(p)}: {type(e).__name__} {e}")
            continue
        x, y, w, h = (int(v) for v in row[:4])
        g = cv2.cvtColor(img[max(0, y):y + h, max(0, x):x + w], cv2.COLOR_BGR2GRAY)
        if g.size == 0:
            continue
        rows.append({"path": p, "emb": emb, "face_px": min(w, h), "lap": laplacian_var(_eval_scale(g))})

    if len(rows) < 5:
        return {"picked": 0, "reason": "too_few_faces", "total": len(paths),
                "errs": errs, "skipped_multi": skipped_multi}

    E = np.stack([r["emb"] for r in rows])
    En = E / np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-6)
    sims = En @ En.T
    np.fill_diagonal(sims, 1.0)
    knn = _knn_scores(sims, 8)
    for i, r in enumerate(rows):
        r["knn"] = float(knn[i])

    idx = [i for i in range(len(rows)) if knn[i] >= link_thr]
    # 兜底不能无下限：小池子混杂时（实测陈都灵 20 张池 kNN 中位仅 0.465）
    # 「取前 20」会把明显不是本人的人凑进数据集，比素材少更糟。
    # 2026-11-17 改：门槛随池子自身分布走（自适应档），目的是"剔离群"而不是"按固定分卡死"。
    # 实测旧口径把 60 张过闸素材砍到 14 张，逼出"素材不足 → 再采一轮 → 又砍到 14"的死循环。
    # 绝对底线 0.42 保住"不混入他人"，混入风险由 --board 抽检板人眼兜住。
    if len(idx) < 20:
        med = float(np.median(knn))
        floor = max(0.42, min(link_thr - 0.06, med - 0.04))
        alt = [int(i) for i in np.argsort(-knn) if knn[i] >= floor]
        if len(alt) < 12:
            return {"picked": 0, "reason": "low_consistency", "total": len(paths),
                    "candidates": len(rows), "knn_median": round(float(np.median(knn)), 3),
                    "floor": round(floor, 3), "errs": errs, "skipped_multi": skipped_multi}
        idx = alt

    picked = [rows[i] for i in idx]
    # 近重复剔除（2026-11-17）：同一张原图的不同裁切/不同尺寸会同时进池，scan_dir 的 pHash 去重管不到这里。
    # 抽检板实测 ql05 的 45 张里约 10 对是近重复，等于数据集真实多样性只有 35 张。
    # 只留清晰度最高的一张——重复件占配额不给信息，却让 kNN 一致性虚高。
    # 2026-11-18 补第二道：同一张图换裁切后整图 pHash 距离会 >8（抓不住），但人脸 embedding
    # 余弦仍会 >0.95（实测汤唯 31 张板图里 5-6 对是这种：同款西装不同裁切、同张回眸不同尺寸）。
    _seen_ph, _seen_emb, _uniq = [], [], []
    for r in sorted(picked, key=lambda x: -x["lap"]):
        _img = cv2.imread(r["path"])
        ph = phash(_img) if _img is not None else ""
        if ph and any(hamming(ph, s) <= PHASH_DIST for s in _seen_ph):
            continue
        # rows 里的 emb 是未归一化的人脸特征，直接点积会得到几百的量级、把全部图判成重复
        # （2026-11-18 实锚：汤唯重挑后 build 只剩 1 张）。必须先归一化再算余弦。
        e = None
        if r.get("emb") is not None:
            e = r["emb"] / (np.linalg.norm(r["emb"]) + 1e-9)
            if any(float(np.dot(e, v)) >= 0.95 for v in _seen_emb):
                continue
        if ph:
            _seen_ph.append(ph)
        if e is not None:
            _seen_emb.append(e)
        _uniq.append(r)
    picked = _uniq
    laps = np.array([r["lap"] for r in rows], dtype=np.float32)
    pxs = np.array([r["face_px"] for r in rows], dtype=np.float32)
    ln = (laps - laps.min()) / max(float(np.ptp(laps)), 1e-6)
    pn = np.clip((pxs - FACE_MIN_PX) / max(FACE_GOOD_PX - FACE_MIN_PX, 1), 0, 1)
    score = {r["path"]: 0.6 * float(a) + 0.4 * float(b) for r, a, b in zip(rows, ln, pn)}

    # 年代优先：标题确认「年轻」的排最前，未标注次之，明确近年的排最后。
    # 不猜脸龄——脸龄没有标定过的阈值，猜错会把好素材挡在外面；标题年份可追溯可复核。
    titles = _load_titles(src)
    era_rank = {"young": 0, "unknown": 1, "recent": 2}
    for r in rows:
        r["era"] = era_tag(titles.get(os.path.basename(r["path"]), ""))
    picked.sort(key=lambda r: (era_rank[r["era"]], -score[r["path"]]))
    sel = picked[:keep]
    era_hist: dict[str, int] = {}
    for r in sel:
        era_hist[r["era"]] = era_hist.get(r["era"], 0) + 1

    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        fp = os.path.join(out, f)
        if os.path.isfile(fp):
            os.remove(fp)
    for i, r in enumerate(sel):
        shutil.copy2(r["path"], os.path.join(out, f"{i:03d}_{os.path.basename(r['path'])}"))
    if board:
        make_contact_board([r["path"] for r in sel], board)
    return {"picked": len(sel), "candidates": len(rows), "skipped_multi": skipped_multi,
            "dropped_inconsistent": len(rows) - len(idx),
            "link_threshold": link_thr,
            "knn_median": round(float(np.median(knn)), 3),
            "era": era_hist,
            "out": out}


ERA_HIT = ("早期", "旧照", "年轻时", "少女时期", "学生时期", "出道前", "出道时",
           "写真集", "90年代", "九十年代", "2000年", "2001", "2002", "2003",
           "1999", "1998", "1997", "1996")
ERA_MISS = ("2026", "2025", "2024", "2023", "2022", "2021", "2020",
            "近照", "现状", "最新", "今日", "昨天", "官宣", "产后", "二胎",
            "中年", "成熟风", "红毯", "活动现场", "节目现场", "电影首映")
# 「像她」「某版她」「她的对手」——图里多半是别人，这是最常见的误采来源
ERA_LOOKALIKE = ("版{0}", "像{0}", "神似{0}", "撞脸{0}", "{0}的最", "翻版{0}", "小{0}")


def era_tag(title: str, person: str = "") -> str:
    """young / recent / drop_other / unknown。

    CEO 要「都要年轻时候的」。判据优先级（都是可追溯的文本证据，不猜脸龄）：
      1. 标题里的「N 岁」：>=27 判近年，16-26 判年轻
      2. 近年年份与「近照/现状/红毯」等词 → 近年
      3. 「版某某/像某某/某某的对手」→ 不是本人（这个坑比年龄更致命）
      4. 早期/旧照/少女时期/写真集等 → 年轻
    未命中任何一条 = unknown（保留，交给质量排序与抽检板）。
    """
    t = (title or "").strip()
    if not t:
        return "unknown"
    for m in re.finditer(r"(\d{1,2})\s*岁", t):
        age = int(m.group(1))
        if age >= 27:
            return "recent"
        if 16 <= age <= 26:
            return "young"
    low = t.lower()
    if any(m in low for m in ERA_MISS):
        return "recent"
    if person and any(p.format(person) in t for p in ERA_LOOKALIKE):
        return "drop_other"
    if any(h in t for h in ERA_HIT):
        return "young"
    return "unknown"


def _load_titles(src: str) -> dict:
    """标题存于 <person>/raw/_titles.json，keep 目录里按原文件名匹配。"""
    base = os.path.dirname(os.path.abspath(src))
    for cand in (os.path.join(base, "raw", "_titles.json"),
                 os.path.join(src, "_titles.json")):
        if os.path.isfile(cand):
            try:
                with open(cand, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
    return {}


def guess_tags(name):
    low = name.lower()
    tags = []
    for k, v in (("front", "front view"), ("left", "head turned left"),
                 ("right", "head turned right"), ("profile", "side profile"),
                 ("smile", "smiling"), ("grin", "laughing"),
                 ("day", "daylight"), ("night", "night scene"),
                 ("flash", "direct flash")):
        if k in low:
            tags.append(v)
    return ", ".join(tags)


def build(raw, out, trigger, size=1024):
    rep = scan_dir(raw)
    os.makedirs(out, exist_ok=True)
    os.makedirs(os.path.join(out, "10_" + trigger), exist_ok=True)
    dstdir = os.path.join(out, "10_" + trigger)
    # 先清空：多轮 build 会累积旧图（实锚：ql01 训练集涨到 107 张，而 curated 只有 45），
    # 每轮必须从本次挑选结果重建，否则早先未挑选的图会一直留在训练集里。
    for f in os.listdir(dstdir):
        fp = os.path.join(dstdir, f)
        if os.path.isfile(fp) and os.path.splitext(f)[1].lower() in (EXTS | {".txt"}):
            os.remove(fp)
    ok = 0
    tags_hist = {}
    for r in rep["rows"]:
        if r["verdict"] == "REJECT":
            continue
        img = cv2.imread(r["path"])
        if img is None:
            continue
        box, pts = detect_face_detail(img)
        pose = pose_label(pts)
        if "side profile" in pose:
            # 侧脸超 45° 不进训练集（plan §二），留作验收测试图
            r["reasons"].append("profile_excluded")
            continue
        light = light_label(img, box) if box else ""
        smile = smile_label(pts)
        base = os.path.splitext(os.path.basename(r["path"]))[0]
        dst = os.path.join(dstdir, f"{base}_{ok:03d}.png")
        if not crop_and_save(r["path"], dst, size):
            continue
        # caption 只写"不随人变"的东西：光位/角度/表情/画质。身份全部压进触发词。
        parts = [trigger, "a photo of a woman", "natural skin texture with visible pores",
                 "unretouched", "film grain"]
        for t in (pose, light, smile):
            if t:
                parts.append(t)
        cap = ", ".join(parts)
        with open(os.path.splitext(dst)[0] + ".txt", "w", encoding="utf-8") as f:
            f.write(cap)
        key = " | ".join(x for x in (pose, light, smile) if x)
        tags_hist[key] = tags_hist.get(key, 0) + 1
        ok += 1
    rep["counts"]["built"] = ok
    rep["counts"]["distinct_captions"] = len(tags_hist)
    rep["tag_hist"] = dict(sorted(tags_hist.items(), key=lambda kv: -kv[1]))
    with open(os.path.join(out, "prep-report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    return rep, ok


FLUX_TOML = """[general]
pretrained_model_name_or_path = "{base}"
shuffle_caption = true
caption_extension = ".txt"
keep_tokens = 1
seed = 42

[[datasets]]
batch_size = 1
enable_bucket = true
resolution = "1024,1024"

  [[datasets.subsets]]
  image_dir = "{ds}"
  num_repeats = {repeats}

[network]
network_module = "networks.lora_flux"
network_dim = 32
network_alpha = 32

[optimizer]
optimizer_type = "AdamW8bit"
learning_rate = 1e-4
max_train_steps = {steps}
lr_scheduler = "cosine"
lr_warmup_steps = 0

[saving]
save_every_n_steps = 200
output_dir = "{out}"
output_name = "{name}"
save_model_as = "safetensors"

[other]
gradient_checkpointing = true
mixed_precision = "bf16"
save_precision = "bf16"
max_data_loader_n_workers = 2
"""

SDXL_TOML = """[general]
pretrained_model_name_or_path = "{base}"
shuffle_caption = true
caption_extension = ".txt"
keep_tokens = 1
seed = 42
network_train_unet_only = true
sdpa = true
cache_latents = true
gradient_checkpointing = true
mixed_precision = "fp16"
save_precision = "fp16"
max_data_loader_n_workers = 2

[[datasets]]
batch_size = 1
enable_bucket = true
resolution = "1024,1024"

  [[datasets.subsets]]
  image_dir = "{ds}"
  num_repeats = {repeats}

[network]
network_module = "networks.lora"
network_dim = 32
network_alpha = 16

[optimizer]
optimizer_type = "AdamW8bit"
learning_rate = 1e-4
text_encoder_lr = 5e-5
max_train_steps = {steps}
lr_scheduler = "cosine"
lr_warmup_steps = 0

[saving]
save_every_n_steps = 200
output_dir = "{out}"
output_name = "{name}"
save_model_as = "safetensors"
"""


def emit_config(ds, trigger, base, out_path, steps, name, model_path=""):
    ds_abs = os.path.abspath(ds)
    subdir = os.path.join(ds_abs, "10_" + trigger)
    if not os.path.isdir(subdir):
        subdir = ds_abs
    n = len([f for f in os.listdir(subdir) if os.path.splitext(f)[1].lower() in EXTS])
    # repeats 固定 1：总步数由 max_train_steps 控制，epochs = steps / n。
    # 旧算法 repeats=1200/n 会让 40 张图跑满 1200 步才过一个 epoch，
    # 实际只训练 1.x 轮，LoRA 学不到身份。
    repeats = 1
    epochs = round(steps / max(n, 1), 1)
    tpl = FLUX_TOML if base == "flux" else SDXL_TOML
    text = tpl.format(ds=subdir.replace("\\", "/"), repeats=repeats, steps=steps,
                      out=os.path.dirname(os.path.abspath(out_path)).replace("\\", "/"),
                      name=name, base=(model_path or "").replace("\\", "/"))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    return {"images": n, "repeats": repeats, "steps": steps, "epochs": epochs, "toml": out_path}


def check_caption(path):
    """caption 自检：禁身份词。"""
    hits = []
    with open(path, encoding="utf-8") as f:
        t = f.read().lower()
    for w in IDENTITY_WORDS:
        if w.lower() in t:
            hits.append(w)
    return hits


def selftest():
    """闸必须自带正例与反例——反例不过=闸是假闸。"""
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".codely-cli", "tmp")
    os.makedirs(tmp, exist_ok=True)
    a = os.path.join(tmp, "lt_sharp.png")
    b = os.path.join(tmp, "lt_blur.png")
    c = os.path.join(tmp, "lt_blown.png")
    base = np.zeros((512, 512, 3), np.uint8)
    for i in range(0, 512, 8):
        base[i:i + 4, :, :] = 255
        base[:, i:i + 4, 0] = 128
    cv2.imwrite(a, base)
    cv2.imwrite(b, cv2.GaussianBlur(base, (41, 41), 0))
    blown = np.full((512, 512, 3), 255, np.uint8)
    cv2.imwrite(c, blown)

    ga = cv2.cvtColor(cv2.imread(a), cv2.COLOR_BGR2GRAY)
    gb = cv2.cvtColor(cv2.imread(b), cv2.COLOR_BGR2GRAY)
    gc = cv2.cvtColor(cv2.imread(c), cv2.COLOR_BGR2GRAY)

    fails = []
    if not (laplacian_var(ga) > LAP_MIN):
        fails.append("正例（锐利）未过清晰度闸")
    if laplacian_var(gb) >= LAP_MIN:
        fails.append("反例（虚焦）竟过清晰度闸——闸失效")
    if not (clip_ratio(gc) > CLIP_MAX):
        fails.append("反例（全白过曝）未触发过曝闸")
    pa = phash(base)
    if hamming(pa, phash(base.copy())) != 0:
        fails.append("pHash 不自洽（同图距离非 0）")
    if hamming(pa, phash(cv2.GaussianBlur(base, (41, 41), 0))) <= PHASH_DIST:
        pass  # 模糊版同 pHash 属预期，去重按 pHash 不按清晰度

    for f in fails:
        print(f"[FAIL] {f}")
    if fails:
        return 1
    print(f"[PASS] 正例 lap={laplacian_var(ga):.0f} 反例 lap={laplacian_var(gb):.0f} "
          f"过曝裁剪={clip_ratio(gc):.2f} pHash 自洽")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="单人 LoRA 素材闸与数据集生成")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan"); s.add_argument("raw"); s.add_argument("--json")
    s.add_argument("--min-face-px", type=int, default=FACE_MIN_PX)
    s.add_argument("--lap", type=float, default=LAP_MIN)

    s = sub.add_parser("build"); s.add_argument("raw"); s.add_argument("--out", required=True)
    s.add_argument("--trigger", required=True); s.add_argument("--size", type=int, default=1024)

    s = sub.add_parser("config"); s.add_argument("--dataset", required=True)
    s.add_argument("--trigger", required=True); s.add_argument("--base", default="flux",
                                                               choices=["flux", "sdxl"])
    s.add_argument("--out", required=True); s.add_argument("--steps", type=int, default=1400)
    s.add_argument("--name", default="face_lora"); s.add_argument("--model", default="")

    s = sub.add_parser("curate", help="人物一致性挑选（剔除混入他人脸 + 质量排序）")
    s.add_argument("src"); s.add_argument("--out", required=True)
    s.add_argument("--keep", type=int, default=45)
    s.add_argument("--min-sim", dest="min_sim", type=float, default=0.20)
    s.add_argument("--link-thr", dest="link_thr", type=float, default=0.58,
                   help="kNN 一致性分下限：低于判混入他人（实测 0.58）")
    s.add_argument("--board", default="", help="抽检板输出路径（拼图，人眼确认同一人）")

    sub.add_parser("selftest")
    a = ap.parse_args(argv)

    if a.cmd == "selftest":
        return selftest()
    if a.cmd == "scan":
        rep = scan_dir(a.raw, a.min_face_px, a.lap)
        c = rep["counts"]
        print(f"扫描 {c['total']} · PASS {c['pass']} · WARN {c['warn']} · REJECT {c['reject']} "
              f"· 去重后可用 {c['usable']}")
        need = 20
        if c["usable"] < need:
            print(f"[FAIL] 可用 {c['usable']} 张 < 硬下限 {need} 张——先补素材，别急着训")
        elif c["usable"] < 40:
            print(f"[WARN] 可用 {c['usable']} 张 < 建议 {40} 张——可训但容易不像")
        else:
            print(f"[PASS] 可用 {c['usable']} 张，够训")
        for r in rep["rows"]:
            if r["verdict"] != "PASS":
                print(f"  {r['verdict']}: {os.path.basename(r['path'])} "
                      f"{r.get('reasons') or r.get('warns')}")
        if a.json:
            with open(a.json, "w", encoding="utf-8") as f:
                json.dump(rep, f, ensure_ascii=False, indent=1)
            print(f"报告 → {a.json}")
        return 0 if c["usable"] >= need else 1
    if a.cmd == "build":
        rep, ok = build(a.raw, a.out, a.trigger, a.size)
        print(f"生成 {ok} 张训练图 → {os.path.join(a.out, '10_' + a.trigger)}")
        bad = 0
        for base, _, files in os.walk(a.out):
            for fn in files:
                if fn.endswith(".txt"):
                    h = check_caption(os.path.join(base, fn))
                    if h:
                        print(f"  [caption] {fn} 含身份词 {h}")
                        bad += 1
        return 0 if ok >= 20 else 1
    if a.cmd == "curate":
        info = curate(a.src, a.out, a.keep, a.min_sim, a.board or None, a.link_thr)
        if info.get("reason"):
            print(f"[FAIL] {info['reason']}：{info.get('total')} 张 · 可用脸 {info.get('candidates')}")
            for e in info.get("errs") or []:
                print(f"  {e}")
            return 1
        print(f"候选 {info['candidates']} 张 · 合影跳过 {info['skipped_multi']} 张 "
              f"· 判混入剔除 {info['dropped_inconsistent']} 张 · 留存 {info['picked']} 张"
              f"（kNN 阈值 {info['link_threshold']}，全批中位 {info['knn_median']}）")
        era = info.get("era") or {}
        if era:
            print("  年代构成：" + " · ".join(
                f"{k} {v}" for k, v in sorted(era.items(), key=lambda kv: -kv[1])))
        print(f"→ {info['out']}")
        if a.board:
            print(f"抽检板 → {a.board}")
        return 0 if info["picked"] >= 20 else 1
    if a.cmd == "config":
        info = emit_config(a.dataset, a.trigger, a.base, a.out, a.steps, a.name, a.model)
        print(f"配置 → {info['toml']}（{info['images']} 张 · repeats {info['repeats']} "
              f"· {info['steps']} 步）")
        print("下一步：在 sd-scripts 目录下 accelerate launch ... "
              + ("flux_train_network.py" if a.base == "flux" else "sdxl_train_network.py")
              + " --config_file <toml>")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
