#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""train_lora.py — 在自有语料上做 LoRA，并把这一次训练写成可复盘的运行卡。

纪律（写死在代码里，不靠记性）：
  - **开训前必过门槛**：语料量 + 红线召回（human_corpus.py --gate 的 rc=0）。
    没过要显式 --force-plumbing 才跑，且运行卡会被标成 plumbing（不是正式模型）。
  - **数据指纹必记**：train.jsonl 的 sha256 进运行卡；语料变了但卡没变 = 不可复盘。
  - **只写副本**：LoRA 权重落在 train/RUNS/<ts>/adapter，不动基座权重。
  - **显存/内存先腾**：训练前 `ollama stop` 已加载模型（4B 4bit 常驻 5.4GB，
    和 LoRA 抢同一池 32GB 统一内存；实测会直接换页把速度拖成渣）。

用法：
  python3 Tools/fleet/train_lora.py                      # 默认 300 iter
  python3 Tools/fleet/train_lora.py --iters 60 --plumbing # 只验证管路通不通
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(ROOT, "cph4", "fleet", "social", "train")
RUNS = os.path.join(DATA, "RUNS")
MODEL_DEFAULT = os.path.join(os.path.expanduser("~"), ".fluxgroup", "models", "qwen3.5-4b-4bit")
PY = sys.executable


def sha_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def free_models():
    """把 ollama 常驻模型卸掉：32GB 统一内存里模型和训练是同一个池子。"""
    try:
        out = subprocess.run(["ollama", "ps"], capture_output=True, text=True).stdout
    except Exception:
        return []
    names = [l.split()[0] for l in out.splitlines()[1:] if l.strip()]
    for n in names:
        subprocess.run(["ollama", "stop", n], capture_output=True)
    return names


def gate_ok():
    try:
        r = subprocess.run([PY, os.path.join(HERE, "human_corpus.py"), "--gate"],
                           capture_output=True, text=True)
        return r.returncode == 0, (r.stdout or "").strip()
    except Exception as e:
        return False, "门槛跑不起来：%s" % str(e)[:80]


def parse_loss_lines(path):
    """从 train.log 抽 train/val 曲线。剥 ANSI 是关键——不剥就抓不到，卡里静默 None。"""
    ansi = re.compile(r"\x1b\[[0-9;]*m")
    tl, vl = [], []
    for raw in open(path, encoding="utf-8", errors="replace"):
        line = ansi.sub("", raw)
        m = re.search(r"Train loss ([\d.]+)", line) or re.search(r"\d+\s+([\d.]+)\s*[▲▼]", line)
        if m:
            tl.append(float(m.group(1)))
        m = re.search(r"Val loss ([\d.]+)", line) or re.search(r"\bval\s+([\d.]+)", line)
        if m:
            vl.append(float(m.group(1)))
    return tl, vl


def self_test():
    cases = []
    import tempfile
    # 1 新版动画式输出（带 ANSI 色码）必须能解析
    log = ("\x1b[1miter\x1b[0m train_loss\n"
           "   10    \x1b[1m5.072 ▼\x1b[0m    \x1b[1m   20\x1b[0m      0.2k\n"
           "    1    \x1b[1mval\x1b[0m \x1b[1m5.423\x1b[0m    5.79s\n")
    f = tempfile.NamedTemporaryFile("w", suffix=".log", delete=False, encoding="utf-8")
    f.write(log); f.close()
    tl, vl = parse_loss_lines(f.name)
    os.unlink(f.name)
    cases.append(("ANSI 下能抓 train loss", tl == [5.072]))
    cases.append(("ANSI 下能抓 val loss", vl == [5.423]))
    # 2 老格式 "Train loss 1.23" 也要认
    cases.append(("老格式兼容", re.search(r"Train loss ([\d.]+)", "Train loss 1.23") is not None))
    # 3 解析不出时返回空而不是崩
    f2 = tempfile.NamedTemporaryFile("w", suffix=".log", delete=False, encoding="utf-8")
    f2.write("nothing here\n"); f2.close()
    cases.append(("坏日志返回空", parse_loss_lines(f2.name) == ([], [])))
    os.unlink(f2.name)
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def other_train_pids():
    """在跑的 mlx 训练进程（不含自己）。

    2026-11-19 实锚：train_run.sh 被两个调用方先后触发，两份训练同时跑，
    swap 顶到 6.3GB/7.2GB 而 mlx 一句错都不报——只看"进程活着"会以为一切正常。
    包装脚本已有 mkdir 锁；这里再挡一层，防的是绕过包装、直接调本脚本的路。
    """
    me = os.getpid()
    try:
        out = subprocess.run(["ps", "-axo", "pid=,command="],
                             capture_output=True, text=True).stdout
    except Exception:
        return []
    pids = []
    for line in (out or "").splitlines():
        m = re.match(r"^\s*(\d+)\s+(.*)$", line)
        if not m:
            continue
        pid, cmd = int(m.group(1)), m.group(2)
        if pid == me or "lora" not in cmd or "--train" not in cmd:
            continue
        if "mlx_lm" in cmd:
            pids.append(pid)
    return pids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--data", default=DATA)
    ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--num-layers", type=int, default=8)
    ap.add_argument("--learning-rate", type=float, default=1e-5)
    ap.add_argument("--max-seq-length", type=int, default=512)
    ap.add_argument("--steps-per-eval", type=int, default=50)
    ap.add_argument("--plumbing", action="store_true", help="只验管路（会标成 plumbing）")
    ap.add_argument("--keep-models", action="store_true", help="不卸载 ollama 模型")
    ap.add_argument("--resume", default=None, help="从某个 *_adapters.safetensors 续训")
    ap.add_argument("--grad-checkpoint", action="store_true",
                    help="梯度检查点：用时间换内存，防触发 swap")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    busy = other_train_pids()
    if busy:
        print("[train] SKIP-ALREADY-TRAINING pid=%s 已有训练在跑，本次放弃"
              "（两份训练同时跑只会双输）" % ",".join(str(p) for p in busy))
        return 3

    train_f = os.path.join(a.data, "train.jsonl")
    if not os.path.exists(train_f) or not os.path.exists(os.path.join(a.data, "valid.jsonl")):
        print("[train] 缺 train.jsonl / valid.jsonl（先跑 train_build.py）")
        return 2
    if not os.path.isdir(a.model):
        print("[train] 基座不存在：%s\n        下载：HF_ENDPOINT=https://hf-mirror.com python3 -c "
              "\"from huggingface_hub import snapshot_download as d;d('mlx-community/Qwen3.5-4B-4bit',"
              "local_dir='%s')\"" % (a.model, a.model))
        return 2

    ok, detail = gate_ok()
    print(detail)
    if not ok and not a.plumbing:
        print("[train] 开训门槛未过。要么补语料/修红线，要么显式 --plumbing 只验管路。")
        return 2

    n_train = sum(1 for _ in open(train_f, encoding="utf-8"))
    ts = time.strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join(RUNS, ts)
    os.makedirs(run_dir, exist_ok=True)
    adapter = os.path.join(run_dir, "adapter")

    stopped = [] if a.keep_models else free_models()
    if stopped:
        print("[train] 已卸载常驻模型：%s" % ", ".join(stopped))
        time.sleep(3)

    argv = [PY, "-m", "mlx_lm", "lora", "--train",
            "--model", a.model, "--data", a.data,
            "--batch-size", str(a.batch_size), "--iters", str(a.iters),
            "--num-layers", str(a.num_layers), "--learning-rate", str(a.learning_rate),
            "--max-seq-length", str(a.max_seq_length),
            "--steps-per-eval", str(a.steps_per_eval),
            "--adapter-path", adapter, "--seed", "20261117", "--mask-prompt"]
    if a.resume:
        argv += ["--resume-adapter-file", a.resume]
    if a.grad_checkpoint:
        argv.append("--grad-checkpoint")
    print("[train] %d 条训练样本 · %d iter · num-layers=%d · bs=%d"
          % (n_train, a.iters, a.num_layers, a.batch_size))
    print("[train] %s" % " ".join(argv[2:]))

    t0 = time.time()
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log_path = os.path.join(run_dir, "train.log")
    train_losses, val_losses = [], []
    # mlx_lm 的进度条带 ANSI 颜色码（"\x1b[1m5.072 ▼\x1b[0m"），不先剥掉正则就抓不到，
    # 运行卡里会静默留 None——看着像"训练没产出损失"，其实只是没剥色。
    ansi = re.compile(r"\x1b\[[0-9;]*m")
    with open(log_path, "w", encoding="utf-8") as logf:
        for raw_line in proc.stdout:
            logf.write(raw_line)
            logf.flush()
            sys.stdout.write(raw_line)
            sys.stdout.flush()
            line = ansi.sub("", raw_line)
            m = re.search(r"Train loss ([\d.]+)", line)
            if not m:
                m = re.search(r"\d+\s+([\d.]+)\s*[▲▼]", line)
            if m:
                train_losses.append(float(m.group(1)))
            m = re.search(r"Val loss ([\d.]+)", line) or re.search(r"\bval\s+([\d.]+)", line)
            if m:
                val_losses.append(float(m.group(1)))
    rc = proc.wait()
    wall = round(time.time() - t0, 1)

    card = {
        "ts": ts, "run_dir": os.path.relpath(run_dir, ROOT), "rc": rc,
        "plumbing_only": bool(a.plumbing) or not ok,
        "base_model": a.model, "argv": argv[2:],
        "train_rows": n_train,
        "data_sha": {f: sha_of(os.path.join(a.data, f))
                     for f in ("train.jsonl", "valid.jsonl")},
        "iters": a.iters, "train_loss_last": train_losses[-1] if train_losses else None,
        "val_loss_last": val_losses[-1] if val_losses else None,
        "train_loss_head": train_losses[:3], "val_loss_all": val_losses,
        "wall_sec": wall, "models_unloaded": stopped,
        "adapter": os.path.relpath(adapter, ROOT) if os.path.isdir(adapter) else None,
    }
    json.dump(card, open(os.path.join(run_dir, "RUN.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("[train] rc=%d 用时 %.0fs train_loss=%s val_loss=%s"
          % (rc, wall, card["train_loss_last"], card["val_loss_last"]))
    print("[train] 运行卡 %s" % os.path.join(card["run_dir"], "RUN.json"))
    if rc != 0:
        print("[train] 失败：看 %s" % log_path)
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
