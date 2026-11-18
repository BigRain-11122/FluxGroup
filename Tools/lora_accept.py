# -*- coding: utf-8 -*-
"""lora_accept.py - 女主/角色 LoRA 的首次实测验收（不训练，只出图 + 打分 + 拼板）。

判据来源：.codely-cli 记忆 2026-11-16 两条
  ① 人脸一致性只能用 SFace 余弦，多模态模型不算数；
  ② 阈值必须按自家管线基线定，不许套真人 0.55-0.85。

做法：同一段中性提示词（只换场景），让 LoRA 自己担脸，不给任何参考图。
  - 跨镜相似度：同一条 LoRA 的两张不同场景图互比（这正是"跨镜还是同一个人"）
  - 素材相似度：出图 vs 该条训练素材里脸最大的一张（看它学没学到脸）
  - 板图：每条一行，人工一眼看

Usage:
  py Tools/lora_accept.py --names T02,T03 --scenes 2 --strength 1.0
  py Tools/lora_accept.py --names T05 --scenes 3 --out <dir>
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import uuid

import cv2
import numpy as np

SERVER = "http://127.0.0.1:8188"
HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN_HOME = r"D:\FluxGroup-Offload\15-training"
MODEL = os.path.join(HERE, "models", "face_detection_yunet_2023mar.onnx")
MODEL_SFACE = os.path.join(HERE, "models", "face_recognition_sface_2021dec.onnx")

W, H = 896, 512

# 中性身份句：不描述长相，长相必须由 LoRA 提供（否则测的是提示词不是权重）
IDENTITY = ("A 20-year-old Taiwanese woman in the year 2001, plain ordinary looks, "
            "NOT a Korean idol, no K-pop styling, no makeup, no glossy retouch, "
            "natural unretouched skin with visible pores and fine film grain, matte complexion, "
            "relaxed unfitted early-2000s Taipei clothes. ")

TAIL = (" Shot on 35mm film, cinematic film still from a 2001 Taiwanese music video, "
        "soft neutral grade with gentle contrast, visible grain. "
        "No readable text, no typography, no logos, no watermark.")

SCENES = {
    "A_classroom": ("A medium close-up at eye level, chest up, standing beside a classroom window "
                    "in the late afternoon; flat overcast daylight from the left, a wooden desk edge "
                    "and a chalkboard out of focus behind her, quiet, nobody else in frame."),
    "B_rainstreet": ("A close-up at night under a street lamp on a wet Taipei street, light rain, "
                     "she holds a plain umbrella; warm sodium lamp key light from above right, "
                     "wet pavement reflections behind her, the rest of the street in deep shadow."),
    "C_stairwell": ("A medium shot in a concrete school stairwell, she leans on the railing looking "
                    "away from camera; cool daylight from a high window, faint fluorescent tube behind, "
                    "dust in the air, muted palette."),
}

# 每条 LoRA：权重名 -> (触发词, 训练素材目录)
JOBS = {
    "her_mv0001": ("h01", os.path.join(TRAIN_HOME, "dataset", "her_mv0001")),
    "T02": ("h02", os.path.join(TRAIN_HOME, "dataset", "T02")),
    "T03": ("h03", os.path.join(TRAIN_HOME, "dataset", "T03")),
    "T04": ("h04", os.path.join(TRAIN_HOME, "dataset", "T04")),
    "T05": ("h05", os.path.join(TRAIN_HOME, "dataset", "T05")),
    "T06": ("h06", os.path.join(TRAIN_HOME, "dataset", "T06")),
    "T07": ("h07", os.path.join(TRAIN_HOME, "dataset", "T07")),
    "T08": ("h08", os.path.join(TRAIN_HOME, "dataset", "T08")),
}


def graph(prompt_text, seed, lora, strength, w, h, prefix):
    """与 Tools/kf_male_lora.py 同一张图（已实测可出图）：krea2 turbo int8 + 8 步 euler simple。"""
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_int8_convrot.safetensors", "weight_dtype": "default"}},
        "15": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["10", 0], "lora_name": lora, "strength_model": strength}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "52": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {"clip": ["11", 0], "vae": ["12", 0], "prompt": prompt_text}},
        "53": {"class_type": "FluxKontextMultiReferenceLatentMethod", "inputs": {"conditioning": ["52", 0], "reference_latents_method": "index_timestep_zero"}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["53", 0]}},
        "64": {"class_type": "ModelSamplingFlux", "inputs": {"model": ["15", 0], "max_shift": 1.15, "base_shift": 0.5, "width": w, "height": h}},
        "57": {"class_type": "CFGGuider", "inputs": {"model": ["64", 0], "positive": ["53", 0], "negative": ["13", 0], "cfg": 1.0}},
        "63": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "59": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "60": {"class_type": "BasicScheduler", "inputs": {"model": ["64", 0], "scheduler": "simple", "steps": 8, "denoise": 1.0}},
        "61": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "58": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["63", 0], "guider": ["57", 0], "sampler": ["59", 0], "sigmas": ["60", 0], "latent_image": ["61", 0]}},
        "62": {"class_type": "VAEDecode", "inputs": {"samples": ["58", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["62", 0], "filename_prefix": prefix}},
    }


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())


def gen(prompt, seed, lora, strength, dst, prefix, budget=420):
    try:
        pid = post(SERVER + "/prompt", {"prompt": graph(prompt, seed, lora, strength, W, H, prefix),
                                       "client_id": str(uuid.uuid4())})["prompt_id"]
    except Exception as e:
        print("    submit failed: %s" % e, flush=True)
        return False
    t0 = time.time()
    while time.time() - t0 < budget:
        try:
            h = json.loads(urllib.request.urlopen(SERVER + "/history/" + pid, timeout=30).read())
            if pid in h:
                for _n, o in h[pid]["outputs"].items():
                    for img in o.get("images", []):
                        url = ("%s/view?filename=%s&subfolder=%s&type=%s"
                               % (SERVER, urllib.parse.quote(img["filename"]),
                                  urllib.parse.quote(img["subfolder"]), img["type"]))
                        open(dst, "wb").write(urllib.request.urlopen(url, timeout=120).read())
                        return True
        except Exception:
            pass
        time.sleep(2.0)
    return False


_DET = None
_REC = None


def _init():
    global _DET, _REC
    if _DET is None:
        _DET = cv2.FaceDetectorYN.create(MODEL, "", (320, 320), 0.6, 0.3, 5000)
        _REC = cv2.FaceRecognizerSF.create(MODEL_SFACE, "")


def face_vec(path):
    """返回 (特征向量, 脸宽占图宽比例)。检不到脸返回 (None, 0)。"""
    _init()
    img = cv2.imread(path)
    if img is None:
        return None, 0.0
    det = cv2.FaceDetectorYN.create(MODEL, "", (img.shape[1], img.shape[0]), 0.6, 0.3, 5000)
    _, faces = det.detect(img)
    if faces is None or not len(faces):
        return None, 0.0
    f = max(faces, key=lambda r: r[2] * r[3])
    ratio = float(f[2]) / img.shape[1]
    v = _REC.feature(_REC.alignCrop(img, f.reshape(1, -1))).flatten().astype(np.float32)
    return v / (np.linalg.norm(v) + 1e-9), ratio


def ref_vec(ds_dir, n=4):
    """从训练素材里挑脸最大的 n 张，取平均作为"这条 LoRA 该长的样子"。"""
    if not os.path.isdir(ds_dir):
        return None, 0
    cand = []
    for name in sorted(os.listdir(ds_dir)):
        if not name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue
        v, r = face_vec(os.path.join(ds_dir, name))
        if v is not None and r >= 0.03:
            cand.append((r, v))
    if not cand:
        return None, 0
    cand.sort(key=lambda t: -t[0])
    top = [v for _, v in cand[:n]]
    m = np.mean(top, axis=0)
    return m / (np.linalg.norm(m) + 1e-9), len(cand)


def board(rows, path):
    """每行一条 LoRA：场景图并排 + 左侧标签。"""
    _init()
    th = 300
    tiles = []
    for label, imgs, note in rows:
        row = []
        for p in imgs:
            im = cv2.imread(p)
            if im is None:
                im = np.zeros((H, W, 3), np.uint8)
            h, w = im.shape[:2]
            im = cv2.resize(im, (int(w * th / h), th))
            im = cv2.copyMakeBorder(im, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=(60, 60, 60))
            row.append(im)
        if row:
            tiles.append((label, note, row))
    if not tiles:
        return None
    lw = 210
    width = lw + sum(min(t[2][0].shape[1], 560) for t in tiles[:1]) if tiles else 0
    # 统一按最宽的一行排版
    maxw = lw + sum(im.shape[1] for im in tiles[0][2])
    canvas = np.full((th * len(tiles) + 4 * len(tiles), maxw, 3), 18, np.uint8)
    for i, (label, note, row) in enumerate(tiles):
        y = i * (th + 4)
        x = lw
        for im in row:
            if x + im.shape[1] > canvas.shape[1]:
                break
            canvas[y:y + im.shape[0], x:x + im.shape[1]] = im
            x += im.shape[1]
        cv2.putText(canvas, label, (8, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (235, 235, 235), 1, cv2.LINE_AA)
        for j, line in enumerate(note.split("|")):
            cv2.putText(canvas, line, (8, y + 62 + j * 26), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (150, 215, 255), 1, cv2.LINE_AA)
    cv2.imwrite(path, canvas)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", default=",".join(JOBS))
    ap.add_argument("--scenes", type=int, default=2, help="用前 n 个场景")
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=9300)
    ap.add_argument("--out", default=os.path.join(TRAIN_HOME, "accept"))
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    keys = [k.strip() for k in a.names.split(",") if k.strip()]
    scene_keys = list(SCENES)[:a.scenes]
    report = {"at": time.strftime("%Y-%m-%d %H:%M:%S"), "strength": a.strength,
              "scenes": scene_keys, "width": W, "height": H, "rows": []}
    rows_for_board = []

    for name in keys:
        if name not in JOBS:
            print("skip unknown %s" % name, flush=True)
            continue
        trig, ds = JOBS[name]
        t0 = time.time()
        imgs = []
        for sk in scene_keys:
            prompt = IDENTITY + trig + ", " + SCENES[sk] + TAIL
            dst = os.path.join(a.out, "%s_%s.png" % (name, sk));
            dst = dst.replace("__", "_")
            dst = os.path.join(a.out, "%s_%s.png" % (name, sk))
            if os.path.exists(dst):
                print("  [%s/%s] cached" % (name, sk), flush=True)
            elif not gen(prompt, a.seed, name + "_rank32.safetensors", a.strength, dst, "lora_accept"):
                print("  [%s/%s] TIMEOUT" % (name, sk), flush=True)
                continue
            else:
                print("  [%s/%s] done %.0fs" % (name, sk, time.time() - t0), flush=True)
            imgs.append((sk, dst))

        vecs = [(sk, d, face_vec(d)) for sk, d in imgs]
        usable = [(sk, d, v, r) for sk, d, (v, r) in vecs if v is not None]
        cross = []
        for i in range(len(usable)):
            for j in range(i + 1, len(usable)):
                cross.append(float(np.dot(usable[i][2], usable[j][2])))
        rv, nref = ref_vec(ds)
        sims_ref = [float(np.dot(v, rv)) for _, _, v, _ in usable] if rv is not None else []
        row = {
            "name": name, "trigger": trig, "images": len(imgs),
            "faces_found": len(usable),
            "face_ratio": [round(r, 3) for _, _, _, r in usable],
            "cross_scene_median": round(float(np.median(cross)), 3) if cross else None,
            "cross_scene_min": round(min(cross), 3) if cross else None,
            "vs_dataset_median": round(float(np.median(sims_ref)), 3) if sims_ref else None,
            "vs_dataset_min": round(min(sims_ref), 3) if sims_ref else None,
            "ref_images": nref,
            "secs": round(time.time() - t0, 1),
        }
        report["rows"].append(row)
        note = "cross=%s|vs_ds=%s" % (
            ("%.2f/%.2f" % (row["cross_scene_median"], row["cross_scene_min"])) if cross else "n/a",
            ("%.2f/%.2f" % (row["vs_dataset_median"], row["vs_dataset_min"])) if sims_ref else "n/a")
        rows_for_board.append((name, [d for _, d in imgs], note))
        print("  => %s cross=%s vs_dataset=%s faces=%d/%d"
              % (name, row["cross_scene_median"], row["vs_dataset_median"], len(usable), len(imgs)), flush=True)

    rp = os.path.join(a.out, "lora-accept-report.json")
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    bp = os.path.join(a.out, "lora-accept-board.jpg")
    board(rows_for_board, bp)
    print("\nreport -> %s\nboard  -> %s" % (rp, bp), flush=True)

    print("\n%-11s %-14s %-14s %s" % ("NAME", "cross-scene", "vs-dataset", "faces"))
    for r in report["rows"]:
        print("%-11s %-14s %-14s %d/%d"
              % (r["name"], "%s/%s" % (r["cross_scene_median"], r["cross_scene_min"]),
                 "%s/%s" % (r["vs_dataset_median"], r["vs_dataset_min"]),
                 r["faces_found"], r["images"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
