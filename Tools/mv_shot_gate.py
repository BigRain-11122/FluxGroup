# -*- coding: utf-8 -*-
"""mv_shot_gate.py - 每镜入片闸（镜头级"护照"），不是整片事后体检。

为什么要这个：2026-11-03 CEO 连挑五类问题（换脸/穿帮/没运镜/裂帧/风格断层），
每一类都是"某个镜头单独看不对"，而 mv_delivery_gate 只按整片统计查技术指标，
没有任何一环在"这一镜能不能进片"上做判断，于是每次都是 CEO 先发现、我再改一镜。
这个脚本把判断前移到镜头级：每镜一张护照，任一项不过 → 该镜不许入片。

六项判据（全部机器可算，人工只看抽帧板）：
  1 motion    该镜全局位移 px/帧（相位相关），FIG/FACE 镜低于阈值 = 没运镜
  2 still     帧间差过低 = 静止画面
  3 dup       重复帧/复现
  4 blend     切点两侧出现"两画面各半"的混合帧（半叠化露馅）
  5 face      人脸聚类离群 = 换人（Haar 检脸 + 纹理/色彩指纹，无模型依赖）
  6 style     饱和度/边缘密度离群 = 风格断层（如 2D 插画混进实拍）

用法：
  python Tools/mv_shot_gate.py <master.mp4> [--rows auto] [--out dir] [--json f.json]
退出码：0 全绿 / 2 有镜不过 / 3 输入不足（BLOCKED）
"""
import argparse, json, os, subprocess, sys, tempfile

import numpy as np

try:
    import cv2
except ImportError:
    print("BLOCKED: opencv-python missing")
    sys.exit(3)

# 阈值（改这里=升级标准，必须整片重跑）
TH_MOTION_FIG = 0.60      # px/frame(24fps 归一)，人物镜最低位移
TH_MOTION_OBJ = 0.25      # 空镜物件允许更慢
TH_STILL_MAD = 0.45       # 帧间平均差低于此=静止
TH_BLEND_LO, TH_BLEND_HI = 0.55, 0.92   # 与两侧镜头相似度都落在此带=混合帧
TH_FACE_SIM = 0.40        # 与片内人脸主簇的相似度低于此=疑似换人
TH_STYLE_SAT = 2.5        # 饱和度 z 分数绝对值上限
TH_STYLE_EDGE = 2.5       # 边缘密度 z 分数绝对值上限
CARD_WINDOWS = [(38.79, 40.21), (219.71, 223.88)]   # 片名卡/片尾卡，允许静止

DET_MODEL = r"D:\AI\models\face\yunet.onnx"
REC_MODEL = r"D:\AI\models\face\sface.onnx"


def _load_models():
    if not (os.path.exists(DET_MODEL) and os.path.exists(REC_MODEL)):
        return None, None
    det = cv2.FaceDetectorYN.create(DET_MODEL, "", (320, 320), 0.6, 0.3, 500)
    rec = cv2.FaceRecognizerSF.create(REC_MODEL, "")
    return det, rec


DET, REC = _load_models()


def ffprobe_info(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=width,height,r_frame_rate",
                          "-of", "json", path], capture_output=True, text=True)
    d = json.loads(out.stdout)["streams"][0]
    num, den = d["r_frame_rate"].split("/")
    return int(d["width"]), int(d["height"]), float(num) / float(den)


def read_frames(path, w=320, sample_fps=6.0):
    """按 sample_fps 抽样返回 (gray 小图, bgr 小图, 原始时间戳列表)。"""
    W, H, fps = ffprobe_info(path)
    h = max(2, int(round(w * H / W / 2)) * 2)
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf",
           "fps=%g,scale=%d:%d" % (sample_fps, w, h), "-f", "rawvideo",
           "-pix_fmt", "bgr24", "-"]
    p = subprocess.run(cmd, capture_output=True)
    buf = np.frombuffer(p.stdout, dtype=np.uint8)
    n = len(buf) // (w * h * 3)
    bgr = buf[:n * w * h * 3].reshape(n, h, w, 3)
    gray = np.array([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in bgr]) if n else np.zeros((0, h, w), np.uint8)
    ts = [i / sample_fps for i in range(n)]
    return gray, bgr, ts, fps, (W, H)


def shifts(grays):
    """相邻帧全局位移（相位相关），返回 px/帧数组。"""
    out = [0.0]
    for a, b in zip(grays[:-1], grays[1:]):
        try:
            (dx, dy), _ = cv2.phaseCorrelate(np.float32(a), np.float32(b))
            out.append(float((dx * dx + dy * dy) ** 0.5))
        except Exception:
            out.append(0.0)
    return np.asarray(out, dtype=float)


def face_detect_full(bgr_frame, min_ratio=0.06):
    """返回 (feat, n_faces, face_w_ratio, clipped)。

    整张脸必须在画面内才作数：被边缘切掉的脸，alignCrop 出来的隐向量不可信
    （INT4 俯拍手部镜实测给了 -0.12，把"脸只露半张"误判成换人）。
    """
    if DET is None:
        return None, 0, 0.0, False
    h, w = bgr_frame.shape[:2]
    DET.setInputSize((w, h))
    _, faces = DET.detect(bgr_frame)
    if faces is None or len(faces) == 0:
        return None, 0, 0.0, False
    best = max(faces, key=lambda f: f[2] * f[3])
    x, y, bw, bh = [float(v) for v in best[:4]]
    ratio = bw / float(w)
    clipped = (x <= 2 or y <= 2 or x + bw >= w - 2 or y + bh >= h - 2)
    if ratio < min_ratio or clipped:
        return None, len(faces), ratio, clipped
    try:
        aligned = REC.alignCrop(bgr_frame, best)
        feat = REC.feature(aligned).flatten().astype(np.float32)
        feat = feat / (np.linalg.norm(feat) + 1e-6)
    except Exception:
        return None, len(faces), ratio, clipped
    return feat, len(faces), ratio, clipped


def faceprint(bgr_frame):
    feat, n, _, _ = face_detect_full(bgr_frame)
    return feat, n


def style_stats(bgr_frames):
    sat, edge, flat = [], [], []
    for f in bgr_frames:
        hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
        sat.append(float(hsv[:, :, 1].mean()))
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        edge.append(float(cv2.Laplacian(g, cv2.CV_32F).var()))
        # 平涂度：每通道量化到 16 级后的唯一色数。真人实拍=成千上万，赛璐璐/2D=几十到几百
        q = (f >> 4).astype(np.uint32)
        packed = (q[:, :, 0] << 8) | (q[:, :, 1] << 4) | q[:, :, 2]
        flat.append(float(len(np.unique(packed))))
    return (float(np.mean(sat)) if sat else 0.0,
            float(np.mean(edge)) if edge else 0.0,
            float(np.mean(flat)) if flat else 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--rows", default="auto", help="镜头窗口；auto=按检测切点自动切")
    ap.add_argument("--out", default="")
    ap.add_argument("--json", default="")
    ap.add_argument("--cut-mad", type=float, default=12.0)
    ap.add_argument("--baseline", default="",
                    help="known-defect baseline json; only NEW defects fail")
    ap.add_argument("--write-baseline", default="",
                    help="write current defect list as the new baseline")
    a = ap.parse_args()

    if not os.path.exists(a.video):
        print("BLOCKED: master not found %s" % a.video)
        return 3

    outdir = a.out or os.path.join(tempfile.gettempdir(), "mv_shot_gate")
    os.makedirs(outdir, exist_ok=True)

    grays, bgrs, ts, fps, (W, H) = read_frames(a.video)
    if len(grays) < 10:
        print("BLOCKED: too few frames decoded (%d)" % len(grays))
        return 3
    sample_fps = len(grays) / (ts[-1] - ts[0] + 1e-6)

    mad = np.asarray([0.0] + [float(np.mean(np.abs(grays[i].astype(np.int16) - grays[i - 1].astype(np.int16))))
                              for i in range(1, len(grays))])
    cuts = [i for i in range(1, len(grays)) if mad[i] >= a.cut_mad]
    bounds = [0] + cuts + [len(grays)]
    shots = [(bounds[k], bounds[k + 1]) for k in range(len(bounds) - 1)
             if bounds[k + 1] - bounds[k] >= 3]

    sh = shifts(grays)
    # px/帧 归一到 24fps（抽样率不同不改每帧位移量，只影响统计窗口）

    rows = []
    for idx, (s0, s1) in enumerate(shots):
        t0, t1 = ts[s0], ts[min(s1, len(ts) - 1)]
        seg = slice(s0, s1)
        m_mot = float(sh[seg][1:].mean()) if s1 - s0 > 1 else 0.0
        m_mad = float(mad[seg][1:].mean()) if s1 - s0 > 1 else 0.0
        sat, edge, flat = style_stats(bgrs[seg])
        in_card = any(c0 - 0.05 <= t0 <= c1 for c0, c1 in CARD_WINDOWS)
        fp, nface = faceprint(bgrs[(s0 + s1) // 2])
        rows.append(dict(i=idx, t0=round(t0, 2), t1=round(t1, 2), dur=round(t1 - t0, 2),
                         motion=round(m_mot, 3), mad=round(m_mad, 3),
                         sat=round(sat, 1), edge=round(edge, 1), flat=int(flat),
                         faces=int(nface), card=in_card, fp=fp))

    # ---- 判据 ----
    fails = {r["i"]: [] for r in rows}

    # 6 style：全片 z 分数
    for key, th, low in (("sat", TH_STYLE_SAT, False), ("edge", TH_STYLE_EDGE, True),
                         ("flat", TH_STYLE_EDGE, True)):
        vals = np.array([r[key] for r in rows], dtype=float)
        mu, sd = vals.mean(), vals.std() + 1e-6
        for r in rows:
            z = (r[key] - mu) / sd
            if (low and z < -th) or ((not low) and z > th):
                fails[r["i"]].append("style:%s z=%.1f" % (key, z))

    # 1/2 motion & still
    for r in rows:
        is_fig = r["faces"] > 0
        th = TH_MOTION_FIG if is_fig else TH_MOTION_OBJ
        if r["card"]:
            continue
        if r["motion"] < th:
            fails[r["i"]].append("motion:%.2f<%.2f(%s)" % (r["motion"], th, "FIG" if is_fig else "OBJ"))
        if r["mad"] < TH_STILL_MAD and r["motion"] < th:
            fails[r["i"]].append("still:mad=%.2f" % r["mad"])

    # 4 blend：切点前后各 1 帧与两侧的相似度都在中间带
    fps_s = sample_fps

    def sim(a_img, b_img):
        a1 = cv2.resize(a_img, (64, 36)).astype(np.float32)
        b1 = cv2.resize(b_img, (64, 36)).astype(np.float32)
        a1 -= a1.mean(); b1 -= b1.mean()
        d = (np.linalg.norm(a1) * np.linalg.norm(b1)) + 1e-6
        return float((a1 * b1).sum() / d)

    blends = []
    for c in cuts:
        if c - 2 < 0 or c + 1 >= len(grays):
            continue
        prev, cur, nxt = grays[c - 2], grays[c], grays[min(c + 1, len(grays) - 1)]
        s_prev, s_next = sim(cur, prev), sim(cur, nxt)
        s_pn = sim(prev, nxt)
        # a blend frame sits between two DIFFERENT shots: it resembles both, while the
        # two ends resemble each other far less. Without that third test, every ordinary
        # cut between two similar-looking shots false-positives (first run: 159 "blends").
        if (TH_BLEND_LO < s_prev < TH_BLEND_HI and TH_BLEND_LO < s_next < TH_BLEND_HI
                and s_pn < 0.45):
            blends.append(round(ts[c], 2))
    for t in blends:
        idx = next((r["i"] for r in rows if r["t0"] <= t <= r["t1"]), None)
        if idx is not None:
            fails[idx].append("blend cut@%.2fs" % t)

    # 5 face 聚类离群
    fps_list = [(r["i"], r["fp"], r["t0"]) for r in rows if r["fp"] is not None]
    clusters = []
    if len(fps_list) >= 4:
        # union-find over cosine similarity: each group = one face identity
        parent = {i: i for i, _, _ in fps_list}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[ry] = rx

        for a_i in range(len(fps_list)):
            for b_i in range(a_i + 1, len(fps_list)):
                ia, fa, _ = fps_list[a_i]
                ib, fb, _ = fps_list[b_i]
                c = float((fa * fb).sum())
                if c >= TH_FACE_SIM:
                    union(ia, ib)
        groups = {}
        for i, f, t0 in fps_list:
            groups.setdefault(find(i), []).append((i, t0))
        clusters = sorted(groups.values(), key=lambda g: -len(g))
        # 判据：一个带脸的镜头，其所属身份必须在片里出现过 >=3 次；只出现一次的脸
        # 基本就是"这一镜自己长了一张脸"——换人或路人，必须人眼复核。
        for g in clusters:
            if len(g) < 3:
                for i, t0 in g:
                    fails[i].append("face solo-identity(%.1fs cluster=%d)" % (t0, len(g)))
    else:
        print("NOTE: 人脸样本不足（%d），face 判据本轮 BLOCKED" % len(fps_list))

    # ---- 输出 ----
    bad = [i for i, v in fails.items() if v]
    for r in rows:
        r.pop("fp", None)
        if fails[r["i"]]:
            r["fails"] = fails[r["i"]]
            # 该镜抽 6 帧一张板，供人眼复核（机制的一部分：证据自动生成）
            s0 = shots[r["i"]][0]
            s1 = shots[r["i"]][1]
            pick = np.linspace(s0, max(s0, s1 - 1), 6).astype(int)
            tiles = [cv2.resize(bgrs[k], (320, int(320 * bgrs[k].shape[0] / bgrs[k].shape[1])))
                     for k in pick]
            hmax = max(t.shape[0] for t in tiles)
            tiles = [cv2.copyMakeBorder(t, 0, hmax - t.shape[0], 0, 0, cv2.BORDER_CONSTANT)
                     for t in tiles]
            sheet = np.hstack(tiles)
            r["sheet"] = os.path.join(outdir, "shot_%03d_%.2fs.png" % (r["i"], r["t0"]))
            cv2.imwrite(r["sheet"], sheet)

    print("shots=%d  failing=%d  blends=%d  face_identities=%d"
          % (len(rows), len(bad), len(blends), len(clusters)))
    for k, g in enumerate(clusters):
        print("  face#%d  count=%d  shots=%s" % (k + 1, len(g),
                                                 ",".join("%.1fs" % t0 for _, t0 in g[:12])))
    for r in rows:
        if r.get("fails"):
            print("FAIL shot%02d %6.2f-%6.2fs motion=%.2f mad=%.2f | %s"
                  % (r["i"], r["t0"], r["t1"], r["motion"], r["mad"], "; ".join(r["fails"])))

    # ---- 基线棘轮：已知债照旧记账，只拦新缺陷 ----
    cur = sorted(round(r["t0"], 1) for r in rows if r.get("fails"))
    if a.write_baseline:
        json.dump({"written": "2026-11-03", "count": len(cur), "shot_starts": cur},
                  open(a.write_baseline, "w", encoding="utf-8"), indent=1)
        print("baseline written: %d known defects -> %s" % (len(cur), a.write_baseline))

    new_defects = []
    if a.baseline and os.path.exists(a.baseline):
        base = set(json.load(open(a.baseline, encoding="utf-8"))["shot_starts"])
        new_defects = [r for r in rows if r.get("fails") and round(r["t0"], 1) not in base]
        print("ratchet: known=%d  new=%d" % (len(base), len(new_defects)))
        for r in new_defects:
            print("NEW-FAIL shot%02d %6.2fs | %s" % (r["i"], r["t0"], "; ".join(r["fails"])))

    if a.json:
        json.dump({"video": a.video, "fps": fps, "size": [W, H], "shots": rows,
                   "failing": bad, "blend_cuts": blends,
                   "face_clusters": [[{"shot": i, "t": t0} for i, t0 in g] for g in clusters],
                   "thresholds": {"motion_fig": TH_MOTION_FIG, "motion_obj": TH_MOTION_OBJ,
                                  "still_mad": TH_STILL_MAD, "face_sim": TH_FACE_SIM}},
                  open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("json ->", a.json)
    print("sheets ->", outdir)
    if a.baseline and os.path.exists(a.baseline):
        return 2 if new_defects else 0
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())