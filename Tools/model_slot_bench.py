# -*- coding: utf-8 -*-
"""bm-b 模型槽位实测（确定性，本地 Ollama，零云端）。

对每个候选模型：加载 -> 固定 prompt -> 记 tok/s 与首字延迟 -> 采样 VRAM -> 卸载。
输出 JSON 供 MACHINE-PROFILE 与槽位策略引用。必须绕过系统代理（Clash 会截 127.0.0.1）。
"""
import io
import json
import subprocess
import sys
import time
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

API = "http://127.0.0.1:11434/api/generate"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
PROMPT = "用一句话说明汽修店的轮毂动平衡是什么，不超过30字。"
MODELS = sys.argv[1:] or ["qwen3.8:4b", "qwen2.5:7b-instruct", "bili-reply-v38:latest", "bili-reply-14b:latest"]


def vram():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, timeout=10).stdout.decode().strip().splitlines()[0]
        used, util = [float(x) for x in out.split(",")]
        return used, util
    except Exception:
        return None, None


def call(model, keep_alive=None, timeout=600):
    payload = {
        "model": model,
        "prompt": PROMPT,
        "stream": False,
        "think": False,
        "options": {"num_ctx": 2048, "temperature": 0.2, "num_predict": 64},
    }
    if keep_alive is not None:
        payload["keep_alive"] = keep_alive
    req = urllib.request.Request(API, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with OPENER.open(req, timeout=timeout) as r:
        body = json.loads(r.read().decode("utf-8"))
    wall = time.time() - t0
    ev = body.get("eval_count") or 0
    evd = body.get("eval_duration") or 0  # ns
    tps = (ev / (evd / 1e9)) if evd else None
    load = body.get("load_duration") or 0
    return {
        "model": model,
        "wall_s": round(wall, 2),
        "load_s": round(load / 1e9, 2) if load else None,
        "gen_tokens": ev,
        "tok_per_s": round(tps, 1) if tps else None,
        "sample": (body.get("response") or "").strip()[:60],
    }


def main():
    if "--weekly" in sys.argv[1:] and time.localtime().tm_wday != 0:
        print("SKIP weekly gate: today is not Monday (wday=%d)" % time.localtime().tm_wday)
        return 0
    # busy guard: never yank models while a loop round is mid-flight
    lock = r"C:\Fluxgroup\FluxGroup\quant\bigmoney\Logs\iteration-loop\round.lock"
    try:
        import os as _os
        if _os.path.exists(lock) and time.time() - _os.path.getmtime(lock) < 900:
            print("SKIP busy guard: iteration round lock is fresh (<15min)")
            return 0
    except Exception:
        pass
    rows = []
    for m in MODELS:
        print("== %s" % m, flush=True)
        try:
            r = call(m)
            used, util = vram()
            r["vram_used_mb"] = used
            r["gpu_util_pct"] = util
            rows.append(r)
            print("   wall=%.2fs load=%ss tok/s=%s vram=%sMB util=%s%%"
                  % (r["wall_s"], r["load_s"], r["tok_per_s"], used, util), flush=True)
        except Exception as e:
            rows.append({"model": m, "error": str(e)[:200]})
            print("   ERROR %s" % str(e)[:200], flush=True)
        try:
            call(m, keep_alive=0)  # unload
        except Exception:
            pass
    out = r"C:\Fluxgroup\FluxGroup\cph4\fleet\model-slots\bench-bm-b.json"
    import os
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"), "prompt": PROMPT, "rows": rows}, f,
                  ensure_ascii=False, indent=1)
    print("WROTE " + out)


if __name__ == "__main__":
    main()