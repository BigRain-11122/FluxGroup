# -*- coding: utf-8 -*-
"""lora_queue.py - 年代女主 LoRA 训练单驱动器（无人值守，按 order 顺序跑）。

为什么要有它：CEO 要求「排满训练单」，且同一型要同时供 MV(16:9) 与漫剧/短剧(9:16)。
每条 job 的流程固定：起 ComfyUI → 出竖+横两批定妆图 → AI 味闸剔除 → build → 关 ComfyUI → train → 记账。
用法：python Tools/lora_queue.py [--only T02] [--dry]

三条状态纪律（2026-11-03 加，避免会话死了以后链子自欺）：
- 记账只改自己那条 job：整份 q 回写会把他窗的新状态冲掉。
- status=running 必须先验真：训练进程在就算在跑；进程没了但末轮检查点在盘 = trained；
  两者都不成立才算 interrupted 并重跑，不把「断了」记成「在跑」。
- 权重名与 job id 可以不同（T01 的历史权重叫 her_mv0001），一律走 train_name 取，不再靠猜。
"""
import argparse, json, os, shutil, subprocess, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(ROOT, "cph4", "fleet", "mv-lora", "LORA-TRAIN-QUEUE-v1.json")
RECEIPTS = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
TRAIN_HOME = os.environ.get("LORA_HOME", r"D:\FluxGroup-Offload\15-training")
COMFY_PY = r"D:\AI\comfyui-krea\ComfyUI_windows_portable\python_embeded\python.exe"
COMFY_MAIN = r"D:\AI\comfyui-krea\ComfyUI_windows_portable\ComfyUI\main.py"


def say(m):
    print("[queue] " + m, flush=True)


def tn(job):
    """训练用的权重名：老的 T01 权重叫 her_mv0001，不能靠 job id 猜。"""
    return job.get("train_name") or job["id"]


def outdir(job):
    return os.path.join(TRAIN_HOME, "outputs", tn(job))


def final_ckpt(job, epochs):
    """末轮检查点在盘 = 这条真的训完了（不是靠状态字段自证）。"""
    p = os.path.join(outdir(job), "%s_rank32-%06d.safetensors" % (tn(job), int(epochs)))
    return p if os.path.exists(p) else None


def proc_alive(match):
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
        "Where-Object { $_.CommandLine -match '%s' } | Measure-Object | "
        "Select-Object -ExpandProperty Count" % match],
        capture_output=True, text=True)
    try:
        return int((out.stdout or "0").strip() or 0) > 0
    except Exception:
        return False


def save_job(job):
    """只回写自己那条，锁外读、临时件写、原子替换。"""
    cur = json.load(open(Q, encoding="utf-8"))
    for i, j in enumerate(cur.get("jobs", [])):
        if j.get("id") == job.get("id"):
            cur["jobs"][i] = job
            break
    tmp = Q + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cur, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, Q)


def receipt(job, status, extra=None):
    os.makedirs(RECEIPTS, exist_ok=True)
    body = {
        "card": "LORA-%s-%s" % (job["id"], time.strftime("%Y%m%d")),
        "queue_id": job["id"], "type": job.get("name"), "trigger": job.get("trigger"),
        "train_name": tn(job), "status": status,
        "dataset": os.path.join(TRAIN_HOME, "dataset", job["id"]),
        "weights_dir": outdir(job), "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if extra:
        body.update(extra)
    p = os.path.join(RECEIPTS, "lora-%s-%s.json" % (job["id"], time.strftime("%Y%m%d")))
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(body, fh, ensure_ascii=False, indent=1)
    return p


def comfy_up(timeout=240):
    try:
        urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=5).read()
        return True
    except Exception:
        pass
    subprocess.Popen([COMFY_PY, COMFY_MAIN, "--listen", "0.0.0.0", "--port", "8188",
                      "--disable-auto-launch"], creationflags=0x08000000)
    for _ in range(timeout // 5):
        time.sleep(5)
        try:
            urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=5).read()
            return True
        except Exception:
            continue
    return False


def comfy_down():
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                    "Where-Object { $_.CommandLine -match 'ComfyUI' } | "
                    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"],
                   capture_output=True)
    time.sleep(8)


def run(cmd, log):
    with open(log, "a", encoding="utf-8", errors="replace") as fh:
        fh.write("$ " + " ".join(cmd) + "\n")
        fh.flush()
        rc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT).returncode
    return rc


def portraits(job, n, w, h, log):
    return run([sys.executable, os.path.join(ROOT, "Tools", "lora_portraits.py"),
                "--name", job["id"], "--trigger", job["trigger"], "--base", job["base"],
                "--count", str(n), "--width", str(w), "--height", str(h)], log)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    q = json.load(open(Q, encoding="utf-8"))
    d = q["defaults"]
    logdir = os.path.join(TRAIN_HOME, "logs")
    os.makedirs(logdir, exist_ok=True)

    for job in sorted(q["jobs"], key=lambda x: x["order"]):
        if a.only and job["id"] != a.only:
            continue
        st = job.get("status")
        if st in ("done", "trained"):
            continue
        if st == "running":
            # 验真：进程在 = 真在跑；进程没了但末轮在盘 = 已完成；都不是才算断了
            if proc_alive("lora_pipeline.+train.+--name %s" % tn(job)):
                say("%s 正在训练（%s），跳过" % (job["id"], tn(job)))
                continue
            ck = final_ckpt(job, d["epochs"])
            if ck:
                job["status"] = "trained"
                job["weights"] = os.path.basename(ck)
                save_job(job)
                receipt(job, "trained", {"weights": os.path.basename(ck),
                                         "note": "进程已退，末轮检查点在盘，判为训完"})
                say("%s 判为训完（%s）" % (job["id"], os.path.basename(ck)))
                continue
            say("%s 状态写着 running 但进程已死且无末轮检查点 → interrupted，重跑"
                % job["id"])
            job["status"] = "interrupted"
            save_job(job)

        log = os.path.join(logdir, "queue-%s-%s.log" % (job["id"], time.strftime("%Y%m%d")))
        say("%s %s 开工" % (job["id"], job["name"]))
        if a.dry:
            say("  dry: 出图 %d 张(横竖各半) → 闸 → build → train" % d["count"])
            continue

        # 有训练在跑时不能开 ComfyUI（显存冲突），等着
        while proc_alive("lora_pipeline.+train"):
            say("  等待在训任务结束…")
            time.sleep(120)

        if not comfy_up():
            say("  BLOCKED ComfyUI 起不来，跳过")
            job["status"] = "blocked-comfy"
            save_job(job)
            receipt(job, "blocked-comfy", {"error": "ComfyUI 240s 内未就绪"})
            continue
        half = max(8, d["count"] // 2)
        portraits(job, half, 1344, 768, log)          # MV 16:9
        portraits(job, d["count"] - half, 768, 1344, log)  # 漫剧/短剧 9:16
        comfy_down()

        ds = os.path.join(TRAIN_HOME, "dataset", job["id"])
        pngs = [f for f in os.listdir(ds) if f.endswith(".png")] if os.path.isdir(ds) else []
        say("  出图 %d 张" % len(pngs))
        if len(pngs) < d["min_keep"]:
            say("  BLOCKED 素材不足 %d < %d" % (len(pngs), d["min_keep"]))
            job["status"] = "blocked-material"
            save_job(job)
            receipt(job, "blocked-material", {"images": len(pngs), "min_keep": d["min_keep"]})
            continue

        g = os.path.join(TRAIN_HOME, "logs", "smell-%s.json" % job["id"])
        run([sys.executable, os.path.join(ROOT, "Tools", "ai_smell_gate.py"),
             "--src", ds, "--json", g], log)
        try:
            rep = json.load(open(g, encoding="utf-8"))
            bad = [os.path.basename(r["frame"]) for r in rep["rows"] if "skinvar" in r["strong"]]
        except Exception:
            bad = []
        if bad and len(bad) <= len(pngs) * d["max_reject_ratio"]:
            rej = os.path.join(ds, "_rejected")
            os.makedirs(rej, exist_ok=True)
            for f in bad:
                for p in (os.path.join(ds, f), os.path.splitext(os.path.join(ds, f))[0] + ".txt"):
                    if os.path.exists(p):
                        shutil.move(p, os.path.join(rej, os.path.basename(p)))
            say("  剔除 %d 张（肤色过匀）" % len(bad))
            pngs = [f for f in os.listdir(ds) if f.endswith(".png")]

        if len(pngs) < d["min_keep"]:
            say("  BLOCKED 剔除后不足 %d" % len(pngs))
            job["status"] = "blocked-material"
            save_job(job)
            receipt(job, "blocked-material", {"images": len(pngs), "after_gate": True})
            continue

        job["status"] = "running"
        job["images"] = len(pngs)
        save_job(job)

        rc = run([sys.executable, os.path.join(ROOT, "Tools", "lora_pipeline.py"),
                  "build", "--name", tn(job), "--dir", ds, "--epochs", str(d["epochs"])], log)
        if rc == 0:
            rc = run([sys.executable, os.path.join(ROOT, "Tools", "lora_pipeline.py"),
                      "train", "--name", tn(job)], log)

        ck = final_ckpt(job, d["epochs"])
        job["status"] = "trained" if (rc == 0 and ck) else "failed-%d" % rc
        if ck:
            job["weights"] = os.path.basename(ck)
        save_job(job)
        receipt(job, job["status"], {"rc": rc, "images": len(pngs),
                                     "weights": job.get("weights")})
        say("  %s rc=%d status=%s" % (job["id"], rc, job["status"]))

    say("队列结束")


if __name__ == "__main__":
    main()