#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_prompts.py - 用本机常驻模型批量产出「资产生产规格」（P0 目标 → 可执行提示词）。

为什么（2026-11-03 CEO「Mac 的 CPU/GPU 利用率很低」）：
  低利用率的真因不是机器弱，是没有"本机吃得下、又真有用"的活。
  资产库 P0 有 128 件目标，其中每件都需要一份生产规格（主体/构图/风格词/负向词/尺寸/是否透明底），
  这是纯文本生成，正好是本机 GPU 能吃、且产出能直接喂给生产链的活。

判据：
  - 幂等：已在 JSON 里的 key 跳过（可断点续跑）
  - 结构化：必须能解析出 subject/composition/style/negative/size/alpha/use 七字段，缺就记 MISS
  - 只写 cph4（索引进 git），不产出图（图由生成服务出）

用法：
  python3 asset_prompts.py --tier p0 --limit 20 [--model qwen3:8b] [--out cph4/fleet/asset-lib-v1/ASSET-PROMPTS-v1.json]
Exit: 0 完成；3 模型服务不可达（BLOCKED）
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
if not OLLAMA.startswith("http"):
    OLLAMA = "http://" + OLLAMA
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGETS = os.path.join(ROOT, "cph4", "fleet", "asset-lib-v1", "LIBRARY-TARGETS.json")
FIELDS = ["subject", "composition", "style", "negative", "size", "alpha", "use"]

SYS = ("你在为竖屏短剧/漫剧的资产库写生产规格。只输出一行 JSON，不要解释。"
       "字段：subject（主体，一句话，具体物件或场景）、composition（构图/机位）、"
       "style（风格词，英文短语，赛璐璐动漫+现代都市写实）、negative（负向词，英文）、"
       "size（如 2048x2048 或 1080x1920）、alpha（true/false，透明底必须 true）、"
       "use（在剧里怎么用，一句话）。")


def post(path, payload, timeout=180):
    req = urllib.request.Request(OLLAMA + path,
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def ask(model, prompt, timeout=180):
    """think=false 必须显式关：qwen3 系否则把答案全写在 thinking 里，response 为空。"""
    payload = {"model": model, "prompt": prompt, "system": SYS, "stream": False,
               "think": False,
               "options": {"temperature": 0.7, "num_predict": 300}}
    t0 = time.time()
    r = post("/api/generate", payload, timeout)
    txt = (r.get("response") or "").strip()
    n = int(r.get("eval_count") or 0)
    sec = float(r.get("eval_duration") or 0) / 1e9 or (time.time() - t0)
    return txt, n, sec


def parse(txt):
    s = txt.strip()
    if "{" in s and "}" in s:
        s = s[s.index("{"): s.rindex("}") + 1]
    try:
        d = json.loads(s)
    except Exception:
        return None
    return d if all(k in d for k in FIELDS) else None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="p0")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--model", default="qwen3.5:4b-mlx")
    ap.add_argument("--out", default="cph4/fleet/asset-lib-v1/ASSET-PROMPTS-v1.json")
    a = ap.parse_args(argv)
    try:
        urllib.request.urlopen(OLLAMA + "/api/tags", timeout=10).read()  # GET，不是 POST
    except Exception as e:
        print("[prompts] BLOCKED 本机模型服务不可达：%s（rc=3）" % e)
        return 3
    tg = json.load(open(TARGETS, encoding="utf-8"))
    classes = tg.get("classes") or {}
    out_path = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc = {"ts": "", "model": a.model, "tier": a.tier, "items": {}}
    if os.path.exists(out_path):
        try:
            doc = json.load(open(out_path, encoding="utf-8"))
            doc["model"] = a.model
        except Exception:
            pass
    items = doc.setdefault("items", {})
    todo = []
    for cls, spec in classes.items():
        need = int(spec.get(a.tier) or 0)  # 每类要这么多件
        for i in range(1, need + 1):
            key = "%s-%02d" % (cls, i)
            if key not in items:
                todo.append((key, cls, spec.get("name") or cls, spec.get("spec") or {}))
    todo = todo[: max(0, a.limit)]
    if not todo:
        print("[prompts] 没缺口，跳过")
        return 0
    ok = miss = 0
    t_start = time.time()
    for key, cls, cname, spec in todo:
        need_txt = json.dumps(spec, ensure_ascii=False)
        prompt = ("资产类别：%s（%s）。硬性规格：%s。请为第 %s 件写生产规格。"
                  % (cname, cls, need_txt, key.split("-")[-1]))
        try:
            txt, n, sec = ask(a.model, prompt)
        except Exception as e:
            print("[prompts] %s 调用失败：%s" % (key, e))
            miss += 1
            continue
        d = parse(txt)
        if not d:
            miss += 1
            items[key] = {"cls": cls, "raw": txt[:400], "status": "MISS"}
            continue
        d.update({"cls": cls, "status": "OK", "model": a.model,
                  "tps": round(n / sec, 1) if sec else None})
        items[key] = d
        ok += 1
        print("[prompts] %s ok（%s tok/s）" % (key, d.get("tps")))
    doc["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    doc["stats"] = {"asked": len(todo), "ok": ok, "miss": miss,
                    "seconds": round(time.time() - t_start, 1)}
    json.dump(doc, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[prompts] 本轮 %d 件：成 %d / 缺 %d，用时 %.1fs → %s"
          % (len(todo), ok, miss, time.time() - t_start, os.path.relpath(out_path, ROOT)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))