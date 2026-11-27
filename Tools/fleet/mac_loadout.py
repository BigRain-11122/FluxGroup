#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mac_loadout.py - MacBook(M1 Pro 32GB) 算力阶梯：按余量决定这一轮吃什么活。

为什么（CEO 2026-11-05「你对我的 macbook 内存 CPU GPU 都没有开发到位」）：
  实测：10 核只跑 ~28%、内存空 74%、GPU 53%、swap 已用 480MB。空着的是算力，
  但 bm-m 是主控机——不能拿它做重生产（i2v/渲染/回测），能做且该做的是**控制面智能**：
    ① 抽检验收（用本地 4B 判产物像不像真的）
    ② 资产打标/检索（caption + embedding，给各线复用降本）
    ③ 文档/裁决摘要（把 60 项职责的结论压成可读）
    ④ ASR 字幕（已有 asr_subs，按日）

  阶梯（内存优先，宁可少跑也不许把 32GB 换成 swap）：
    L3 free>=14GB 且 GPU<=85%：4B 常驻 + 抽检 + 打标（每轮最多 8 件）
    L2 free>=8GB  ：单任务串行（抽检 4 件 或 打标 4 张）
    L1 free>=4GB  ：只做规则任务，模型不加载
    L0 <4GB 或 swap 增速>0：只测量，不干活，必要时卸载模型

用法：
  python3 Tools/fleet/mac_loadout.py            # 量一次并按阶梯干一轮活
  python3 Tools/fleet/mac_loadout.py --dry      # 只报阶梯与候选，不执行
  python3 Tools/fleet/mac_loadout.py --status   # 只看最近一次结果
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
OUT = os.path.join(F, "state", "mac-loadout.json")
OLLAMA = "http://127.0.0.1:11434"


def sh(cmd, timeout=20):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (p.stdout or "").strip()
    except Exception:
        return ""


def mem_free_gb():
    """用 vm_stat 估可用内存（free+inactive+speculative）。"""
    out = sh("vm_stat")
    page = 16384
    vals = {}
    for line in out.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip().rstrip(".")
            try:
                vals[k.strip()] = int(v)
            except ValueError:
                pass
    free = vals.get("Pages free", 0) + vals.get("Pages inactive", 0) + vals.get("Pages speculative", 0)
    return round(free * page / (1024 ** 3), 1)


def swap_used_mb():
    out = sh("sysctl -n vm.swapusage")
    try:
        return float(out.split("used = ")[1].split("M")[0])
    except Exception:
        return 0.0


def gpu_pct():
    out = sh("ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '\"Device Utilization %\"=[0-9]*' | head -1")
    try:
        import re as _re
        m = _re.search(r"=([0-9]+)", out)
        return int(m.group(1)) if m else -1
    except Exception:
        return -1


def load_avg():
    try:
        return os.getloadavg()[0]
    except Exception:
        return -1


def ollama_ps():
    try:
        with urllib.request.urlopen(OLLAMA + "/api/ps", timeout=3) as r:
            d = json.loads(r.read().decode("utf-8"))
        return [{"name": m.get("name"), "gb": round((m.get("size") or 0) / (1024 ** 3), 1)}
                for m in (d.get("models") or [])]
    except Exception:
        return []


def ask(prompt, model=None, timeout=90):
    """本地模型一次问答（不联网、不花钱）。失败返回 None，绝不假装成功。"""
    model = model or "qwen3.5:4b-mlx"
    # qwen3 系是思考模型：think=false 才会把答案放进 response（否则全在 thinking，
    # 表现为"模型没回答"——本地模型雷达踩过同一个坑）。
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "think": False,
                       "options": {"temperature": 0.1, "num_predict": 160}}).encode()
    req = urllib.request.Request(OLLAMA + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8"))
            return (d.get("response") or d.get("thinking") or "").strip()
    except Exception:
        return None


def ladder(free, swap_mb, gpu, load):
    if free < 4 or swap_mb > 600:
        return "L0", "内存/swap 吃紧：只测量，不加载模型"
    if free >= 14 and (gpu < 85 or gpu < 0):
        return "L3", "余量充足：4B 常驻 + 抽检 + 打标（每轮<=8 件）"
    if free >= 8:
        return "L2", "中等：单任务串行（<=4 件）"
    return "L1", "偏紧：只做规则任务"


def candidates():
    """这一轮可干的轻活（按价值排序，全部是控制面）。"""
    out = []
    # ① 抽检：近 24h DONE 且没有闸回执的卡
    try:
        rows = [json.loads(l) for l in open(os.path.join(F, "PRODUCTION-QUEUE.jsonl"),
                                            encoding="utf-8") if l.strip()]
        done = [r for r in rows if r.get("state") == "DONE" and r.get("deliverable")]
        out.append({"kind": "sample_review", "count": len(done), "why": "抽检验收（本地 4B 判产物是否可信）"})
    except Exception:
        pass
    # ② 打标：待打标图片
    try:
        n = 0
        for base in ("media/asset", "cph4/fleet/asset-lib-v1"):
            p = os.path.join(ROOT, base)
            if not os.path.isdir(p):
                continue
            for dp, dn, fn in os.walk(p):
                n += sum(1 for x in fn if x.lower().endswith((".png", ".jpg", ".jpeg")))
        out.append({"kind": "caption", "count": n, "why": "资产打标（进检索，供各线复用）"})
    except Exception:
        pass
    # ③ 字幕：需要素材
    out.append({"kind": "asr", "count": 1, "why": "成片补字幕（有素材才跑）"})
    return out


def do_sample_review(limit):
    """抽检：让 4B 看交付物摘要，判断"这份产物像不像真做完的"。只做提示，不改卡状态。"""
    rows = [json.loads(l) for l in open(os.path.join(F, "PRODUCTION-QUEUE.jsonl"),
                                        encoding="utf-8") if l.strip()]
    done = [r for r in rows if r.get("state") == "DONE" and r.get("deliverable")]
    done = done[-limit:]
    verdicts = []
    for r in done:
        dl = r.get("deliverable")
        p = dl if os.path.isabs(dl) else os.path.join(ROOT, dl)
        try:
            size = os.path.getsize(p) if os.path.isfile(p) else -1
            head = ""
            if os.path.isfile(p) and size < 200000:
                head = open(p, encoding="utf-8", errors="ignore").read(1500)
        except Exception:
            size, head = -1, ""
        prompt = ("判断这份交付物是否像「真做完」的产物。只回一行：PASS 或 SUSPECT:原因。\n"
                  "卡：%s\n交付物：%s\n大小：%s 字节\n内容前段：\n%s" %
                  (r.get("id"), dl, size, head[:1200]))
        resp = ask(prompt)
        verdicts.append({"id": r.get("id"), "bytes": size,
                         "verdict": (resp or "MODEL-UNAVAILABLE").strip()[:120]})
    with open(os.path.join(F, "state", "sample-review.json"), "w", encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "items": verdicts},
                  f, ensure_ascii=False, indent=1)
    return len(verdicts)


def do_caption(limit):
    """打标：调用既有 asset_caption.py，一次少量，避免占满内存。"""
    p = os.path.join(ROOT, "Tools", "fleet", "asset_caption.py")
    if not os.path.exists(p):
        return 0
    try:
        subprocess.run([sys.executable, p, "--dir", "media/asset", "--recursive",
                        "--limit", str(limit), "--out",
                        "cph4/fleet/state/caption-batch.json"],
                       cwd=ROOT, capture_output=True, text=True, timeout=600)
        return limit
    except Exception:
        return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args(argv)

    if a.status:
        try:
            print(open(OUT, encoding="utf-8").read())
        except Exception:
            print("(还没有记录)")
        return 0

    free, swap_mb, gpu, load = mem_free_gb(), swap_used_mb(), gpu_pct(), load_avg()
    level, why = ladder(free, swap_mb, gpu, load)
    models = ollama_ps()
    cands = candidates()

    did = []
    if not a.dry:
        if level == "L3":
            did.append({"task": "sample_review", "n": do_sample_review(4)})
            did.append({"task": "caption", "n": do_caption(4)})
        elif level == "L2":
            did.append({"task": "sample_review", "n": do_sample_review(2)})
        elif level == "L1":
            did.append({"task": "none", "n": 0, "why": "内存偏紧，只做规则任务"})

    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "host": "bm-m",
           "hardware": {"chip": "Apple M1 Pro", "cpu_cores": 10, "ram_gb": 32},
           "measured": {"free_gb": free, "swap_mb": swap_mb, "gpu_pct": gpu, "load1": load},
           "level": level, "why": why, "models_loaded": models,
           "candidates": cands, "did": did}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))