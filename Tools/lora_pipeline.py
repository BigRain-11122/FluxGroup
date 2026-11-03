# -*- coding: utf-8 -*-
"""lora_pipeline.py - 角色 LoRA 训练流水线（选中素材 → 建库 → 训 → 验收）。

为什么要有这个：CEO 令「以后 MV 开始前，先把男女主和路人的 LoRA 烧出来，周杰伦的可
以一直更新到最稳」。此前 jman 是一个手写 bat + 手写 toml，换角色就得重抄一遍，且没有
验收口径——于是"烧出来了"只能靠眼看，没法判哪一版更好。

四个子命令，一条链：
  extract  从成片/素材里抽候选脸（YuNet 检脸 + 尺寸筛 + dHash 去重 + 拼板）
  build    校验数据集 → 生成 dataset_<name>.toml + train_<name>.bat（12GB 配方）
  train    跑缓存与训练，日志落 logs/<name>/
  gate     用 SFace 对产物逐图打分（阈值复用 mv_shot_gate.TH_FACE_SIM，只留一处定义）
  status   打印台账 cph4/fleet/mv-lora/LORA-REGISTRY.json

路径（可用环境变量覆盖）：LORA_HOME=D:\\FluxGroup-Offload\\15-training、
MUSUBI_HOME=C:\\Users\\sjs20\\musubi-tuner。
"""
import argparse, json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "Tools"))
TRAIN_HOME = os.environ.get("LORA_HOME", r"D:\FluxGroup-Offload\15-training")
MUSUBI = os.environ.get("MUSUBI_HOME", r"C:\Users\sjs20\musubi-tuner")
COMFY = r"D:\AI\comfyui-krea\ComfyUI_windows_portable\ComfyUI"
RAW_DIT = os.path.join(TRAIN_HOME, r"models\krea2\raw\krea2_raw_bf16.safetensors")
TEXT_ENCODER = os.path.join(TRAIN_HOME, r"models\krea2\text_encoder\qwen3vl_4b_bf16.safetensors")
VAE = os.path.join(COMFY, r"models\vae\qwen_image_vae.safetensors")
REGISTRY = os.path.join(ROOT, "cph4", "fleet", "mv-lora", "LORA-REGISTRY.json")
PY = os.path.join(MUSUBI, r".venv\Scripts\python.exe")
ACC = os.path.join(MUSUBI, r".venv\Scripts\accelerate.exe")

MIN_IMAGES = 15          # 少于这个数不训（LoRA 会只学会背景）
MIN_FACE_RATIO = 0.10    # 脸宽占画面低于此值＝看不清五官，不做素材


def log(*a):
    print("[lora]", *a, flush=True)


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)
    return p


def load_registry():
    if os.path.exists(REGISTRY):
        with open(REGISTRY, encoding="utf-8") as f:
            return json.load(f)
    return {"schema": 1, "note": "角色 LoRA 台账：谁在役、数据集指纹、验收分", "roles": {}}


def save_registry(reg):
    ensure_dir(os.path.dirname(REGISTRY))
    reg["updated"] = time.strftime("%Y-%m-%d %H:%M")
    with open(REGISTRY, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=1)


def run(cmd, log_path=None, check=True):
    log("$", " ".join(cmd) if isinstance(cmd, list) else cmd)
    if log_path:
        ensure_dir(os.path.dirname(log_path))
        fh = open(log_path, "a", encoding="utf-8", errors="replace")
        p = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT)
        fh.close()
    else:
        p = subprocess.run(cmd)
    if check and p.returncode != 0:
        raise SystemExit("命令失败 rc=%d: %s" % (p.returncode, cmd))
    return p.returncode


# ---------------------------------------------------------------- extract
def _dhash(img, size=8):
    import cv2, numpy as np
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, (size + 1, size), interpolation=cv2.INTER_AREA)
    d = g[:, 1:] > g[:, :-1]
    return int("".join("1" if v else "0" for v in d.flatten()), 2)


def _hamming(a, b):
    return bin(a ^ b).count("1")


def _grab_frames(src, windows, fps, out_dir):
    """按时间窗抽帧；src 可以是视频，也可以是目录（直接取图）。"""
    import cv2
    paths = []
    if os.path.isdir(src):
        for n in sorted(os.listdir(src)):
            if n.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                paths.append(os.path.join(src, n))
        return paths
    for i, (t0, t1) in enumerate(windows):
        p = os.path.join(out_dir, "w%02d_%06.2f.png" % (i, t0))
        cmd = ["ffmpeg", "-v", "error", "-ss", "%.2f" % t0, "-to", "%.2f" % t1,
               "-i", src, "-vf", "fps=%g" % fps, "-y", p.replace(".png", "_%03d.png")]
        subprocess.run(cmd, capture_output=True)
        paths.extend(sorted(
            os.path.join(out_dir, n) for n in os.listdir(out_dir)
            if n.startswith("w%02d_" % i) and n not in paths))
    return paths


def cmd_extract(a):
    import cv2
    from mv_shot_gate import face_detect_full
    tmp = ensure_dir(os.path.join(TRAIN_HOME, "tmp", "extract-" + a.name))
    for n in os.listdir(tmp):
        os.remove(os.path.join(tmp, n))
    windows = []
    for w in a.windows.split(","):
        if w.strip():
            t0, t1 = w.split(":")
            windows.append((float(t0), float(t1)))
    frames = _grab_frames(a.src, windows or [(0, 1e9)], a.fps, tmp)
    log("抽帧 %d 张" % len(frames))

    ref = None
    if a.ref:
        import cv2, numpy as np
        rimg = cv2.imread(a.ref)
        rf, _, _, _ = face_detect_full(rimg, min_ratio=0.0)
        if rf is None:
            raise SystemExit("BLOCKED: --ref 里检不到可用人脸")
        ref = rf

    kept, hashes, rows = [], [], []
    for p in frames:
        img = cv2.imread(p)
        if img is None:
            continue
        feat, n, ratio, clipped = face_detect_full(img, min_ratio=0.0)
        ok = (feat is not None) and (ratio >= a.min_face)
        if ok and ref is not None:
            from mv_shot_gate import TH_FACE_SIM
            ok = float(feat.dot(ref)) >= TH_FACE_SIM
        dup = False
        if ok:
            h = _dhash(img)
            dup = any(_hamming(h, x) <= a.dhash_dist for x in hashes)
        if ok and not dup:
            hashes.append(_dhash(img))
            kept.append((p, ratio))
            rows.append(p)
    log("过筛 %d 张（脸宽>=%.0f%% 且去重）" % (len(kept), a.min_face * 100))

    # 质量排序：脸够大优先，最多取 max
    kept.sort(key=lambda x: -x[1])
    kept = kept[:a.max]
    dst = ensure_dir(os.path.join(TRAIN_HOME, "dataset", a.name))
    for i, (p, _) in enumerate(kept, 1):
        shutil.copy(p, os.path.join(dst, "%s_%03d.png" % (a.name, i)))
        cap = "%s, %s" % (a.trigger, a.caption)
        with open(os.path.join(dst, "%s_%03d.txt" % (a.name, i)), "w", encoding="utf-8") as f:
            f.write(cap.strip() + "\n")

    # 拼板：给导演眼看
    if kept:
        import numpy as np
        TH = 256
        tiles = []
        for p, _ in kept[:24]:
            im = cv2.imread(p)
            h, w = im.shape[:2]
            tiles.append(cv2.resize(im, (TH, max(2, int(TH * h / w)))))
        hh = max(t.shape[0] for t in tiles)
        tiles = [cv2.copyMakeBorder(t, 0, hh - t.shape[0], 0, 0, cv2.BORDER_CONSTANT) for t in tiles]
        cols = 6
        while len(tiles) % cols:
            tiles.append(np.zeros_like(tiles[0]))
        sheet = np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)])
        out = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
        ensure_dir(out)
        sheet_path = os.path.join(out, "lora-sheet-%s.jpg" % a.name)
        cv2.imwrite(sheet_path, sheet, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
        log("拼板", sheet_path)

    print(json.dumps({"name": a.name, "dataset": dst, "kept": len(kept),
                      "sources": [os.path.basename(p) for p, _ in kept]},
                     ensure_ascii=False, indent=1))
    return 0 if len(kept) >= MIN_IMAGES else 3


# ---------------------------------------------------------------- build
TOML_TMPL = """[general]
resolution = [512, 512]
caption_extension = ".txt"
batch_size = 1
enable_bucket = true
bucket_no_upscale = false

[[datasets]]
image_directory = "{images}"
cache_directory = "{cache}"
num_repeats = {rep}
"""

BAT_TMPL = """@echo off
rem {name} LoRA / RAW base / rank32 / {epochs} epochs  (generated by Tools/lora_pipeline.py)
echo TRAIN START %date% %time%
cd /d {musubi}
{acc} launch --num_cpu_threads_per_process 1 --mixed_precision bf16 src\\musubi_tuner\\krea2_train_network.py ^
 --dit "{dit}" --vae "{vae}" --dataset_config {toml} ^
 --sdpa --mixed_precision bf16 --timestep_sampling krea2_shift --weighting_scheme none ^
 --optimizer_type adamw8bit --learning_rate {lr} --gradient_checkpointing --gradient_checkpointing_cpu_offload ^
 --max_data_loader_n_workers 2 --persistent_data_loader_workers ^
 --network_module networks.lora_krea2 --network_dim {dim} --network_alpha {dim} ^
 --fp8_base --fp8_scaled --blocks_to_swap 26 --block_swap_h2d_only --block_swap_ring_size 1 --split_attn ^
 --max_train_epochs {epochs} --save_every_n_epochs {save_every} --seed {seed} ^
 --output_dir "{outdir}" --output_name {output}
echo TRAIN EXITCODE %errorlevel% %time%
"""


def cmd_build(a):
    images = a.dir or os.path.join(TRAIN_HOME, "dataset", a.name)
    if not os.path.isdir(images):
        raise SystemExit("BLOCKED: 数据集目录不存在 " + images)
    imgs = [n for n in os.listdir(images) if n.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
    missing = [n for n in imgs
               if not os.path.exists(os.path.join(images, os.path.splitext(n)[0] + ".txt"))]
    if missing:
        log("WARN 缺标注 %d 张，示例：%s" % (len(missing), missing[:3]))
    if len(imgs) < MIN_IMAGES:
        raise SystemExit("BLOCKED: 素材 %d 张 < %d 张，先补素材（宁缺毋滥，不硬训）"
                         % (len(imgs), MIN_IMAGES))

    toml = os.path.join(MUSUBI, "dataset_%s.toml" % a.name)
    with open(toml, "w", encoding="utf-8", newline="\n") as f:
        f.write(TOML_TMPL.format(images=images.replace("\\", "/"),
                                 cache=os.path.join(TRAIN_HOME, "work", "cache", a.name).replace("\\", "/"),
                                 rep=a.repeats))
    bat = os.path.join(MUSUBI, "train_%s.bat" % a.name)
    with open(bat, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(BAT_TMPL.format(name=a.name, epochs=a.epochs, musubi=MUSUBI, acc=ACC,
                               dit=RAW_DIT, vae=VAE, toml=os.path.basename(toml),
                               lr=a.lr, dim=a.dim, save_every=max(1, a.epochs // 8),
                               seed=a.seed, outdir=os.path.join(TRAIN_HOME, "outputs", a.name),
                               output=a.name + "_rank32"))
    log("已生成", toml)
    log("已生成", bat)
    log("下一步：python Tools/lora_pipeline.py train --name %s" % a.name)
    return 0


# ---------------------------------------------------------------- train
def cmd_train(a):
    toml = os.path.join(MUSUBI, "dataset_%s.toml" % a.name)
    if not os.path.exists(toml):
        raise SystemExit("BLOCKED: 先跑 build")
    for p, label in ((RAW_DIT, "RAW 底模"), (VAE, "VAE")):
        if not os.path.exists(p):
            raise SystemExit("BLOCKED: 缺%s %s（RAW 24.5GB 需从 HF 重下）" % (label, p))
    logs = ensure_dir(os.path.join(TRAIN_HOME, "logs", a.name))
    env_cache = os.path.join(MUSUBI, "src", "musubi_tuner")
    if not a.skip_cache:
        run([PY, os.path.join(env_cache, "krea2_cache_latents.py"),
             "--dataset_config", toml, "--vae", VAE, "--skip_existing"],
            os.path.join(logs, "cache-latents.log"))
        if os.path.exists(TEXT_ENCODER):
            run([PY, os.path.join(env_cache, "krea2_cache_text_encoder_outputs.py"),
                 "--dataset_config", toml, "--text_encoder", TEXT_ENCODER, "--skip_existing"],
                os.path.join(logs, "cache-te.log"))
        else:
            log("WARN 无文本编码器缓存，训练可继续（只是不能出样图）")
    rc = run([os.path.join(MUSUBI, "train_%s.bat" % a.name)], os.path.join(logs, "train.log"),
             check=False)
    log("训练结束 rc=%d 日志=%s" % (rc, os.path.join(logs, "train.log")))
    return rc


# ---------------------------------------------------------------- gate
def cmd_gate(a):
    """验收：产物图 vs 定妆照，SFace 余弦相似度。阈值复用 mv_shot_gate（只留一处）。"""
    import cv2, numpy as np
    from mv_shot_gate import face_detect_full, TH_FACE_SIM

    def feats(paths):
        out = []
        for p in paths:
            img = cv2.imread(p)
            if img is None:
                continue
            f, n, _, _ = face_detect_full(img, min_ratio=0.0)
            if f is not None:
                out.append((p, f))
        return out

    def listdir(p):
        return [os.path.join(p, n) for n in sorted(os.listdir(p))
                if n.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]

    refs = feats(listdir(a.ref))
    if len(refs) < 1:
        raise SystemExit("BLOCKED: 参考图里检不到可用人脸（脸宽<6%% 或贴边）")
    ref = np.mean([f for _, f in refs], axis=0)
    ref /= (np.linalg.norm(ref) + 1e-6)
    cand = feats(listdir(a.dir))
    if not cand:
        raise SystemExit("BLOCKED: 产物目录无可用人脸")

    sims = sorted(((float(np.dot(ref, f)), p) for p, f in cand), reverse=True)
    vals = [s for s, _ in sims]
    hit = sum(1 for v in vals if v >= TH_FACE_SIM)
    rate = hit / float(len(vals))
    verdict = "PASS" if rate >= a.pass_rate else "REVISE"
    receipt = {
        "gate": "lora-identity", "name": a.name, "ref_dir": a.ref, "cand_dir": a.dir,
        "threshold": TH_FACE_SIM, "pass_rate_required": a.pass_rate,
        "candidates": len(vals), "pass": hit, "rate": round(rate, 3),
        "median": round(float(np.median(vals)), 3), "min": round(min(vals), 3),
        "worst": [os.path.basename(p) for _, p in sims[-3:]],
        "verdict": verdict, "at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    out = a.out or os.path.join(ROOT, "cph4", "fleet", "queue-receipts",
                                "lora-gate-%s-%s.json" % (a.name, time.strftime("%Y%m%d")))
    ensure_dir(os.path.dirname(out))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=1)
    log("verdict=%s rate=%.2f median=%.3f → %s" % (verdict, rate, receipt["median"], out))
    return 0 if verdict == "PASS" else 2


def cmd_status(a):
    reg = load_registry()
    print(json.dumps(reg, ensure_ascii=False, indent=1))
    return 0


# ---------------------------------------------------------------- probe
def cmd_probe(a):
    """扫全片，按人脸身份聚类，报每个身份出现在哪些时间点、哪一帧脸最大（用来挑定妆帧）。"""
    import cv2
    from mv_shot_gate import face_detect_full, TH_FACE_SIM
    tmp = ensure_dir(os.path.join(TRAIN_HOME, "tmp", "probe"))
    for n in os.listdir(tmp):
        os.remove(os.path.join(tmp, n))
    frames = _grab_frames(a.src, [(0, 1e9)], a.fps, tmp)
    cents, groups = [], []
    for p in frames:
        img = cv2.imread(p)
        if img is None:
            continue
        feat, n, ratio, clipped = face_detect_full(img, min_ratio=0.0)
        if feat is None:
            continue
        best, sim = -1, -1.0
        for i, c in enumerate(cents):
            s = float(feat.dot(c))
            if s > sim:
                best, sim = i, s
        if best >= 0 and sim >= TH_FACE_SIM:
            groups[best].append((p, ratio, face_detect_full(img, 0.0)[0]))
            cents[best] = cents[best] * 0.9 + feat * 0.1
            cents[best] /= (float((cents[best] ** 2).sum()) ** 0.5 + 1e-6)
        else:
            cents.append(feat.copy())
            groups.append([(p, ratio, feat)])
    out = []
    for i, g in enumerate(groups):
        if len(g) < a.min_frames:
            continue
        g.sort(key=lambda x: -x[1])
        out.append({"id": i, "frames": len(g),
                    "best_frame": os.path.basename(g[0][0]),
                    "best_face_ratio": round(g[0][1], 3),
                    "sample_path": g[0][0]})
    out.sort(key=lambda x: -x["frames"])
    print(json.dumps({"scanned": len(frames), "identities": out}, ensure_ascii=False, indent=1))
    return 0


def main():
    ap = argparse.ArgumentParser(description="角色 LoRA 训练流水线")
    sub = ap.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("extract", help="从成片/目录抽候选脸")
    e.add_argument("--src", required=True, help="视频文件或图片目录")
    e.add_argument("--name", required=True)
    e.add_argument("--windows", default="", help="时间窗 t0:t1,t0:t1（视频时用）")
    e.add_argument("--fps", type=float, default=2.0)
    e.add_argument("--min-face", type=float, default=MIN_FACE_RATIO)
    e.add_argument("--dhash-dist", type=int, default=6)
    e.add_argument("--max", type=int, default=40)
    e.add_argument("--trigger", default="")
    e.add_argument("--caption", default="person, natural light, film grain")
    e.add_argument("--ref", default=None, help="定妆照：只保留与它同一张脸的帧")
    e.set_defaults(func=cmd_extract)

    b = sub.add_parser("build", help="生成 toml + bat")
    b.add_argument("--name", required=True)
    b.add_argument("--dir", default=None)
    b.add_argument("--repeats", type=int, default=8)
    b.add_argument("--epochs", type=int, default=12)
    b.add_argument("--dim", type=int, default=32)
    b.add_argument("--lr", default="1e-4")
    b.add_argument("--seed", type=int, default=42)
    b.set_defaults(func=cmd_build)

    t = sub.add_parser("train", help="缓存 + 训练")
    t.add_argument("--name", required=True)
    t.add_argument("--skip-cache", action="store_true")
    t.set_defaults(func=cmd_train)

    g = sub.add_parser("gate", help="身份一致性验收")
    g.add_argument("--name", required=True)
    g.add_argument("--ref", required=True, help="定妆照目录")
    g.add_argument("--dir", required=True, help="产物目录（网格/试烧图）")
    g.add_argument("--pass-rate", type=float, default=0.80)
    g.add_argument("--out", default=None)
    g.set_defaults(func=cmd_gate)

    s = sub.add_parser("status", help="打印台账")
    s.set_defaults(func=cmd_status)

    p = sub.add_parser("probe", help="扫片找人脸身份（挑定妆帧用）")
    p.add_argument("--src", required=True)
    p.add_argument("--fps", type=float, default=1.0)
    p.add_argument("--min-frames", type=int, default=5)
    p.set_defaults(func=cmd_probe)

    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()