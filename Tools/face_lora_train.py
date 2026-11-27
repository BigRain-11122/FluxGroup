#!/usr/bin/env python3
"""单人面孔 LoRA 训练启动器（可复现·可续跑·带让路守卫）。

为什么需要它：2026-11-13 首轮训练是 PowerShell 里手敲的临时命令行，进程一死后
既无法续跑也还原不出参数（日志里只剩被裁断的 "python sd..."）。此后一律走本脚本。

用法：
  python Tools/face_lora_train.py check  --dataset media/faces/x/dataset --trigger ohwx
  python Tools/face_lora_train.py run    --dataset media/faces/x/dataset --trigger ohwx \
      --base D:/models/sd_xl_base_1.0.safetensors --steps 1400 --name her_x
  python Tools/face_lora_train.py status --log <训练日志>

设计要点：
  1. 全 argv 传参，不生成 toml——kohya 的 toml 把 store_true 项写成 `x = true` 时
     解析行为随版本漂移，命令行零歧义。
  2. repeats 恒为 1，总步数由 --steps 控制；epochs = steps / 图片数，跑前打印。
  3. 让路守卫：machine-state.flag 为 pause/pausedLite 时默认拒跑（CEO 用机优先）。
  4. 显存预检：空闲 < 阈值直接拒跑并说明原因，不做"跑到一半 OOM 静默消失"。
  5. 日志与权重都落在固定位置，status 可随时读取真实进度。
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from datetime import datetime

TRAIN_ROOT = r"C:\Users\sjs20\train-lora"
SD_SCRIPTS = os.path.join(TRAIN_ROOT, "sd-scripts")
PY = os.path.join(TRAIN_ROOT, ".venv", "Scripts", "python.exe")
FLAG = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\machine-state.flag"
IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

# 12G 显存下喂 SDXL 的现实值：再大就 OOM，再小则脸学不进去
MIN_FREE_MIB = 6500


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def count_images(dataset: str, trigger: str) -> tuple[str, int]:
    """返回 (实际训练目录, 图片数)。兼容 dataset/10_<trigger>/ 与直接传目录两种形态。"""
    sub = os.path.join(dataset, "10_" + trigger)
    d = sub if os.path.isdir(sub) else dataset
    n = 0
    for f in os.listdir(d):
        if os.path.splitext(f)[1].lower() in IMG_EXTS:
            n += 1
    return d, n


def pause_state() -> str | None:
    """读让路状态。返回 None 表示可跑。"""
    if not os.path.isfile(FLAG):
        return None
    try:
        with open(FLAG, encoding="utf-8", errors="ignore") as f:
            txt = f.read().strip()
    except OSError:
        return None
    low = txt.lower()
    if low.startswith("resume"):
        return None
    if low.startswith("pause"):
        return txt
    return None


def gpu_free_mib() -> int | None:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, encoding="utf-8", timeout=20,
        )
        if out.returncode != 0:
            return None
        return int(out.stdout.strip().splitlines()[0])
    except Exception:
        return None


def unload_local_models() -> None:
    """卸载 Ollama 常驻模型腾显存。

    实测（2026-11-15）：qwen3:4b-instruct 会被周期性加载，吃 7GB/12GB，
    正好把训练卡在显存检查这一步。训练是长任务、模型是可重载的短任务，
    让短任务让路。
    """
    try:
        import json as _json
        import urllib.request
        ps = _json.loads(urllib.request.urlopen("http://127.0.0.1:11434/api/ps",
                                                 timeout=8).read())
        for m in ps.get("models") or []:
            body = _json.dumps({"model": m.get("name"), "keep_alive": 0}).encode()
            req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body,
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=30).read()
            print(f"[info] 已卸载本地模型 {m.get('name')}（为训练让出显存）")
    except Exception as e:
        print(f"[warn] 卸载本地模型失败：{type(e).__name__}")


def cmd_check(a) -> int:
    d, n = count_images(a.dataset, a.trigger)
    free = gpu_free_mib()
    st = pause_state()
    print(f"训练目录 : {d}")
    print(f"图片数   : {n}")
    print(f"计划步数 : {a.steps}  → 约 {round(a.steps / max(n, 1), 1)} 个 epoch")
    print(f"显存空闲 : {free if free is not None else '未知'} MiB（下限 {MIN_FREE_MIB}）")
    print(f"让路状态 : {st or '未暂停'}")
    problems = []
    if n < 20:
        problems.append(f"素材 {n} 张 < 硬下限 20，先补素材（正身 LORA-FACE-LIB-PLAN-v1 §八）")
    if n > 60:
        problems.append(f"素材 {n} 张 > 上限 60，过拟合风险，建议筛到 40-60")
    if free is not None and free < MIN_FREE_MIB:
        problems.append(f"显存仅剩 {free} MiB，不足 {MIN_FREE_MIB}，会被 OOM 静默杀掉")
    if st:
        problems.append(f"机器处于让路态（{st}），白天不抢 GPU")
    for p in problems:
        print(f"[BLOCK] {p}")
    print("[OK] 可以训练" if not problems else f"[FAIL] {len(problems)} 项未过")
    return 0 if not problems else 1


def cmd_run(a) -> int:
    d, n = count_images(a.dataset, a.trigger)
    if n == 0:
        print(f"[FAIL] {d} 里没有图片")
        return 2
    out_dir = a.out_dir or os.path.join(os.path.dirname(os.path.abspath(d)), "out")
    weight = os.path.join(out_dir, a.name + ".safetensors")
    if a.skip_if_exists and os.path.isfile(weight):
        print(f"[SKIP] 权重已存在，不重复训练：{weight}")
        return 0
    if not a.force:
        st = pause_state()
        if st:
            print(f"[FAIL] 机器让路态：{st} —— 白天不抢 GPU。夜窗或 --force 再跑。")
            return 3
        free = gpu_free_mib()
        if free is not None and free < MIN_FREE_MIB:
            unload_local_models()
            time.sleep(6)
            free = gpu_free_mib()
        if free is not None and free < MIN_FREE_MIB:
            print(f"[FAIL] 显存仅剩 {free} MiB（下限 {MIN_FREE_MIB}），先释放再训练。")
            return 3
    if not os.path.isfile(a.base):
        print(f"[FAIL] 底模不存在：{a.base}")
        return 2

    out_dir = a.out_dir or os.path.join(os.path.dirname(os.path.abspath(d)), "out")
    os.makedirs(out_dir, exist_ok=True)
    log = a.log or os.path.join(TRAIN_ROOT, f"train_{a.name}.log")
    # 数据集配置单列成 toml：num_repeats / resolution / shuffle_caption 只在这里有效，
    # 命令行没有 --num_repeats（源码核对 2026-11-13），混进去会 unrecognized arguments。
    ds_cfg = os.path.join(out_dir, f"{a.name}_dataset.toml")
    with open(ds_cfg, "w", encoding="utf-8") as f:
        f.write(
            "[general]\n"
            f'shuffle_caption = {"true" if a.shuffle_caption else "false"}\n'
            'keep_tokens = 1\n'
            f'caption_extension = "{a.caption_ext}"\n\n'
            "[[datasets]]\n"
            "batch_size = 1\n"
            "enable_bucket = true\n"
            # 必须是整数：写成 "1024,1024" 会被 voluptuous schema 拒
            # （expected int for dictionary value @ data['datasets'][0]['resolution']）
            f"resolution = {a.resolution}\n"
            f"min_bucket_reso = {a.min_bucket}\n"
            f"max_bucket_reso = {a.max_bucket}\n\n"
            "  [[datasets.subsets]]\n"
            f'  image_dir = "{os.path.abspath(d).replace(chr(92), "/")}"\n'
            "  num_repeats = 1\n"
        )

    epochs = round(a.steps / n, 1)
    argv = [
        PY, "sdxl_train_network.py",
        "--pretrained_model_name_or_path", a.base,
        "--dataset_config", ds_cfg,
        "--network_module", "networks.lora",
        "--network_dim", str(a.rank),
        "--network_alpha", str(max(1, a.rank // 2)),
        "--network_train_unet_only",
        "--optimizer_type", "AdamW8bit",
        "--learning_rate", a.lr,
        "--max_train_steps", str(a.steps),
        "--save_every_n_steps", str(a.save_every),
        "--lr_scheduler", "cosine",
        "--lr_warmup_steps", "0",
        "--mixed_precision", "bf16",
        "--save_precision", "bf16",
        "--sdpa",
        # 12G 卡上把 latents 缓到内存会让显存顶到 97%，速度从 3s/it 掉到 18s/it
        # （2026-11-15 实测）。缓到磁盘换回速度。
        "--cache_latents_to_disk",
        "--gradient_checkpointing",
        "--max_data_loader_n_workers", "1",
        "--seed", "42",
        "--output_dir", out_dir,
        "--output_name", a.name,
        "--save_model_as", "safetensors",
    ]

    env = dict(os.environ)
    env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    env["PYTHONIOENCODING"] = "utf-8"

    print(f"[{_now()}] 训练启动：{n} 张 · {a.steps} 步 · {epochs} epochs · rank {a.rank}")
    print(f"  数据集 {d}")
    print(f"  日志   {log}")
    print(f"  输出   {out_dir}\\{a.name}.safetensors")
    if a.dry_run:
        print("\n--- dataset toml ---")
        with open(ds_cfg, encoding="utf-8") as f:
            print(f.read())
        print("--- argv ---")
        print(" ".join(argv))
        print("[DRY-RUN] 未启动训练")
        return 0
    with open(log, "w", encoding="utf-8", errors="replace") as lf:
        lf.write(f"# {_now()} {' '.join(argv)}\n")
        lf.flush()
        # 本机弹窗铁律：计划任务用 pythonw 承载（无控制台），子进程也必须 CREATE_NO_WINDOW，
        # 否则 python.exe 会自建控制台，CEO 桌面上闪黑窗。
        flags = 0x08000000 if os.name == "nt" else 0
        p = subprocess.Popen(argv, cwd=SD_SCRIPTS, stdout=lf, stderr=subprocess.STDOUT,
                             env=env, creationflags=flags)
        rc = p.wait()
    print(f"[{_now()}] 训练进程退出 rc={rc}")
    if rc != 0:
        print(f"[FAIL] 失败，看日志尾部：{log}")
        try:
            with open(log, encoding="utf-8", errors="replace") as lf:
                tail = lf.read().strip().splitlines()[-15:]
            print("\n".join(tail))
        except OSError:
            pass
    return rc


def find_datasets(faces_root: str) -> list[tuple[str, str, int]]:
    """扫描 <faces>/<key>-ds/10_<trigger>，返回 (key, 训练目录, 图片数)，按 key 排序。

    200 人备料后无人值守训练靠它：谁能训由"数据集是否达标"决定，不靠人工排单。
    """
    out = []
    if not os.path.isdir(faces_root):
        return out
    for nm in sorted(os.listdir(faces_root)):
        if not nm.endswith("-ds"):
            continue
        ds = os.path.join(faces_root, nm)
        sub = None
        for cand in os.listdir(ds):
            p = os.path.join(ds, cand)
            if os.path.isdir(p) and cand.startswith("10_"):
                sub = cand
                break
        d = os.path.join(ds, sub) if sub else ds
        n = 0
        if os.path.isdir(d):
            n = sum(1 for f in os.listdir(d) if os.path.splitext(f)[1].lower() in IMG_EXTS)
        out.append((nm[:-3], d, n))
    # 张数多的先训：素材越足越像，先把能出好结果的人做出来
    out.sort(key=lambda x: -x[2])
    return out


def cmd_batch(a) -> int:
    """无人值守批量训练：一次只跑一个（单卡防 OOM），已产出自动跳过。"""
    faces = a.faces_root
    rows = find_datasets(faces)
    ready = [(k, d, n) for k, d, n in rows if n >= a.min_images]
    lora_dir = a.lora_dir
    os.makedirs(lora_dir, exist_ok=True)
    pending = [(k, d, n) for k, d, n in ready
               if not os.path.isfile(os.path.join(lora_dir, k + ".safetensors"))]
    print(f"[{_now()}] 数据集 {len(rows)} 个 · 达标 {len(ready)} · 待训 {len(pending)}")
    if not pending:
        print("[done] 没有待训数据集")
        return 0
    if a.dry_run:
        for k, d, n in pending[:20]:
            print(f"  {k}: {n} 张  {d}")
        if len(pending) > 20:
            print(f"  ... 另 {len(pending) - 20} 个")
        return 0
    if not a.force:
        st = pause_state()
        if st:
            print(f"[FAIL] 机器让路态：{st} —— 白天不抢 GPU。")
            return 3
        free = gpu_free_mib()
        if free is not None and free < MIN_FREE_MIB:
            print(f"[FAIL] 显存仅剩 {free} MiB（下限 {MIN_FREE_MIB}），先释放再训练。")
            return 3
    k, d, n = pending[0]
    print(f"[{_now()}] 本轮训练 {k}（{n} 张）；队列还剩 {len(pending) - 1} 个")
    ns = argparse.Namespace(**vars(a))
    ns.dataset = os.path.dirname(d)
    ns.trigger = os.path.basename(d)[3:] if os.path.basename(d).startswith("10_") else "ohwx_woman"
    ns.name = k
    ns.out_dir = lora_dir
    ns.log = ""              # batch 子命令没定义 --log，交给 cmd_run 用默认路径
    ns.skip_if_exists = True
    return cmd_run(ns)


def cmd_status(a) -> int:
    if not os.path.isfile(a.log):
        print(f"[FAIL] 日志不存在：{a.log}")
        return 2
    with open(a.log, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    steps = [ln for ln in lines if re.search(r"\d+%\|", ln) or "steps:" in ln]
    print(f"日志 {a.log}")
    print(f"行数 {len(lines)} · 修改 {datetime.fromtimestamp(os.path.getmtime(a.log)):%m-%d %H:%M:%S}")
    for ln in (steps[-5:] if steps else lines[-8:]):
        print("  " + ln.strip()[:160])
    if any("Traceback" in ln or "Error" in ln for ln in lines[-40:]):
        print("[WARN] 尾部含错误字样")
    return 0


def main(argv=None) -> int:
    # pythonw.exe（计划任务无窗口承载）下 sys.stdout/stderr 为 None，print 会抛
    # AttributeError 导致任务一触发就静默死。先把标准流接管到日志文件。
    if sys.stdout is None or sys.stderr is None:
        try:
            os.makedirs(TRAIN_ROOT, exist_ok=True)
            _f = open(os.path.join(TRAIN_ROOT, "face_lora_train_stdout.log"), "a",
                      encoding="utf-8", buffering=1)
        except OSError:
            return 4
        if sys.stdout is None:
            sys.stdout = _f
        if sys.stderr is None:
            sys.stderr = _f

    ap = argparse.ArgumentParser(description="单人面孔 LoRA 训练启动器")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="训练前体检（素材数/显存/让路态）")
    c.add_argument("--dataset", required=True)
    c.add_argument("--trigger", required=True)
    c.add_argument("--steps", type=int, default=1400)

    r = sub.add_parser("run", help="启动训练")
    r.add_argument("--dataset", required=True)
    r.add_argument("--trigger", required=True)
    r.add_argument("--base", required=True, help="SDXL 底模路径")
    r.add_argument("--steps", type=int, default=1400)
    r.add_argument("--rank", type=int, default=32)
    r.add_argument("--lr", default="1e-4")
    r.add_argument("--resolution", default="1024", help="整数分辨率；写 1024,1024 会被 schema 拒")
    r.add_argument("--min-bucket", dest="min_bucket", type=int, default=512)
    r.add_argument("--max-bucket", dest="max_bucket", type=int, default=1280)
    r.add_argument("--save_every", type=int, default=200)
    r.add_argument("--name", required=True)
    r.add_argument("--out-dir", dest="out_dir", default="")
    r.add_argument("--log", default="")
    r.add_argument("--caption-ext", dest="caption_ext", default=".txt")
    r.add_argument("--no-shuffle-caption", dest="shuffle_caption", action="store_false")
    r.add_argument("--force", action="store_true", help="忽略让路态与显存预检")
    r.add_argument("--dry-run", dest="dry_run", action="store_true", help="只打印配置与命令行")
    r.add_argument("--skip-if-exists", dest="skip_if_exists", action="store_true",
                   help="权重已存在则跳过（供巡检式计划任务反复调用）")

    s = sub.add_parser("status", help="读训练日志进度")
    s.add_argument("--log", required=True)

    b = sub.add_parser("batch", help="无人值守批量训练（一次一个，跳过已完成）")
    b.add_argument("--faces-root", dest="faces_root",
                   default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                        "media", "faces"))
    b.add_argument("--lora-dir", dest="lora_dir", default="",
                   help="权重输出目录，缺省 <faces>/_loras")
    b.add_argument("--base", required=True)
    b.add_argument("--steps", type=int, default=1400)
    b.add_argument("--rank", type=int, default=32)
    b.add_argument("--lr", default="1e-4")
    b.add_argument("--resolution", default="1024")
    b.add_argument("--min-bucket", dest="min_bucket", type=int, default=512)
    b.add_argument("--max-bucket", dest="max_bucket", type=int, default=1280)
    b.add_argument("--save-every", dest="save_every", type=int, default=200)
    b.add_argument("--min-images", dest="min_images", type=int, default=20)
    b.add_argument("--caption-ext", dest="caption_ext", default=".txt")
    b.add_argument("--no-shuffle-caption", dest="shuffle_caption", action="store_false")
    b.add_argument("--force", action="store_true")
    b.add_argument("--dry-run", dest="dry_run", action="store_true")

    a = ap.parse_args(argv)
    if a.cmd == "batch" and not a.lora_dir:
        a.lora_dir = os.path.join(a.faces_root, "_loras")
    return {"check": cmd_check, "run": cmd_run, "status": cmd_status,
            "batch": cmd_batch}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
