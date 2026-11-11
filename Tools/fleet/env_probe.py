#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""env_probe.py - 在每台机上自采 AI 运行环境，写成事实文件供主控对齐。

为什么要它：CEO 2026-11-11「对他们的软件环境什么的也要了解，随时更新」。
主控没法远程执行（FleetLink 只传信号），所以环境事实必须由每台机自己产出：
    各机每日跑 → cph4/fleet/env/<station>.json → 随 git 同步 → 主控只读快照

只采可比项（不采密钥/不采账号）：
  python 版本与解释器、平台、核数
  pip 关键包版本（torch/numpy/pillow/requests/onnxruntime/transformers）
  ollama 版本 + 模型名/digest/量化
  ffmpeg 版本
  GPU 型号与驱动（nvidia-smi；mac 用 system_profiler）
  白名单环境变量（OLLAMA_*、CUDA_*、HF_HOME、TORCH_HOME）
跨平台：只用标准库，不用 fcntl/sysctl 之外的本机专属命令，且每项都容错。

用法：
  python3 Tools/fleet/env_probe.py            # 只打印（人看一眼）
  python3 Tools/fleet/env_probe.py --write     # 写 cph4/fleet/env/<station>.json
  python3 Tools/fleet/env_probe.py --self-test
Exit: 0 采完；2 连不上本机模型服务（其余项照采）
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
ENVDIR = os.path.join(FLEET, "env")
OLLAMA = os.environ.get("OLLAMA_URL") or "http://127.0.0.1:11434"
PKGS = ("torch", "torchvision", "numpy", "pillow", "requests", "onnxruntime", "transformers")
ENV_KEYS = ("OLLAMA_MODELS", "OLLAMA_KEEP_ALIVE", "OLLAMA_NUM_PARALLEL",
            "OLLAMA_MAX_LOADED_MODELS", "OLLAMA_HOST", "CUDA_HOME", "CUDA_PATH",
            "HF_HOME", "TORCH_HOME", "FLUX_VAULT")


def station():
    try:
        sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
        import local_model as lm
        return lm.local_station() or "unknown"
    except Exception:
        return "unknown"


def _run(cmd, timeout=8):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (p.stdout or p.stderr or "").strip()
    except Exception:
        return ""


def python_info():
    return {"version": platform.python_version(), "implementation": platform.python_implementation(),
            "executable": sys.executable}


def pip_info():
    import importlib.metadata as md
    out = {}
    for p in PKGS:
        try:
            out[p] = md.version(p)
        except Exception:
            pass
    return out


def ollama_info():
    import urllib.request
    info = {"url": OLLAMA, "version": None, "models": [], "err": None}
    try:
        with urllib.request.urlopen(OLLAMA + "/api/version", timeout=3) as r:
            info["version"] = (json.loads(r.read()) or {}).get("version")
        with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=5) as r:
            for m in (json.loads(r.read()) or {}).get("models") or []:
                info["models"].append({
                    "name": m.get("name"), "size_gb": round((m.get("size") or 0) / 1e9, 2),
                    "digest": (m.get("digest") or "")[:16],
                    "quant": (m.get("details") or {}).get("quantization_level"),
                })
    except Exception as e:
        info["err"] = str(e)[:120]
    return info


def ffmpeg_info():
    txt = _run(["ffmpeg", "-version"], 8)
    ver = None
    if txt.startswith("ffmpeg version"):
        ver = txt.split()[2]
    return {"version": ver, "present": bool(txt)}


def gpu_info():
    smi = shutil.which("nvidia-smi")
    if smi:
        txt = _run([smi, "--query-gpu=name,driver_version,memory.total",
                    "--format=csv,noheader"], 10)
        return {"backend": "nvidia-smi", "cards": [x.strip() for x in txt.splitlines() if x.strip()]}
    if platform.system() == "Darwin":
        txt = _run(["system_profiler", "SPDisplaysDataType"], 15)
        chips = [ln.split(":", 1)[1].strip() for ln in txt.splitlines()
                 if "Chipset Model" in ln]
        return {"backend": "system_profiler", "cards": chips}
    return {"backend": None, "cards": []}


def env_info():
    return {k: os.environ.get(k) for k in ENV_KEYS if os.environ.get(k) is not None}


def probe():
    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "station": station(),
        "hostname": platform.node(),
        "os": platform.system().lower(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python": python_info(),
        "packages": pip_info(),
        "ollama": ollama_info(),
        "ffmpeg": ffmpeg_info(),
        "gpu": gpu_info(),
        "env": env_info(),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)

    if a.self_test:
        return self_test()

    p = probe()
    print("站点 %s｜%s %s｜python %s｜ollama %s｜ffmpeg %s"
          % (p["station"], p["os"], p["machine"], p["python"]["version"],
             p["ollama"]["version"] or "不可达", p["ffmpeg"]["version"] or "未装"))
    print("模型 %d 个：%s" % (len(p["ollama"]["models"]),
                          "、".join(m["name"] for m in p["ollama"]["models"][:6])))
    if p["gpu"]["cards"]:
        print("GPU：%s" % "；".join(p["gpu"]["cards"][:4]))
    if p["env"]:
        print("环境变量：%s" % p["env"])
    if a.write:
        os.makedirs(ENVDIR, exist_ok=True)
        path = os.path.join(ENVDIR, "%s.json" % p["station"])
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(p, f, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
        print("→ %s" % os.path.relpath(path, ROOT))
    return 0 if not p["ollama"]["err"] else 2


def self_test():
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    p = probe()
    chk("采到平台与核数", p["os"] and p["machine"] and p["cpu_count"])
    chk("python 版本形如 x.y.z", p["python"]["version"].count(".") >= 1, p["python"])
    chk("ollama 段有结构（无论通不通）", "models" in p["ollama"] and "version" in p["ollama"])
    chk("ffmpeg 段有 present 字段", "present" in p["ffmpeg"], p["ffmpeg"])
    chk("env 只采白名单键", set(p["env"]).issubset(set(ENV_KEYS)), list(p["env"]))
    chk("不含敏感字段（token/key/secret）",
        not any(k for k in json.dumps(p, ensure_ascii=False).lower().split('"')
                if k.endswith("token") or k.endswith("secret")))
    print("[env_probe] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


if __name__ == "__main__":
    sys.exit(main())
