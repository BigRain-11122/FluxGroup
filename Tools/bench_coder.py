# -*- coding: utf-8 -*-
# bench_coder.py - resident 35B coder acceptance bench (CEO order 2026-10-14)
# Gates: tok/s >= 30 (V100 spec P0 line), coding sanity answers, CJK sanity.
# Self file-log only (no stdout dependency), safe-zone log.
import json, os, time, urllib.request, sys

# L1 endpoint is swappable (D-20261028-11): resident 35B on :8090, or the
# degraded ollama slot on :11434. Set L1_ENDPOINT to override the base URL.
URL = (os.environ.get("L1_ENDPOINT") or "http://127.0.0.1:8090").rstrip("/") + "/v1/chat/completions"
LOG = r"C:\Users\sjs20\Desktop\FluxGroup\media\logs\coder-bench.log"

def log(m):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + m + "\n")

def chat(messages, max_tokens=512, temperature=0.3):
    body = json.dumps({"messages": messages, "max_tokens": max_tokens,
                       "temperature": temperature, "stream": False,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(URL, data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as r:
        out = json.loads(r.read().decode())
    dt = time.time() - t0
    usage = out.get("usage", {})
    ct = usage.get("completion_tokens", 0)
    return out["choices"][0]["message"]["content"], ct, dt

log("BENCH-START")
# 1) speed probe (short gen)
try:
    txt, ct, dt = chat([{"role": "user", "content": "Write a Python one-liner to reverse a string s."}], max_tokens=64)
    tps = ct / dt if dt else 0
    log("speed: %d tok in %.1fs = %.1f tok/s | ans=%s" % (ct, dt, tps, txt.strip().replace("\n", " ")[:120]))
except Exception as e:
    log("speed FAIL %r" % e); sys.exit(1)

# 2) coding sanity: bug-fix question with verifiable answer
try:
    q = ("Unity: a coroutine `IEnumerator Start()` never runs its body after `yield return null`. "
         "Name the exact requirement for the method returning the IEnumerator in Unity 2022 and give the fix in one line.")
    txt, ct, dt = chat([{"role": "user", "content": q}], max_tokens=384)
    ok = ("mono" in txt.lower() or "monobehaviour" in txt.lower() or "monobehavior" in txt.lower() or "返回类型" in txt or "void" in txt)
    log("coding-fix: verdict=%s | ans=%s" % (ok, txt.strip().replace("\n", " ")[:300]))
except Exception as e:
    log("coding FAIL %r" % e); ok = False

# 3) longer coding gen (stable tok/s check)
try:
    q = "Write a complete C# static helper: int SafeDivide(int a, int b) returning 0 on divide-by-zero, with 3 unit-test asserts."
    txt, ct, dt = chat([{"role": "user", "content": q}], max_tokens=512)
    tps2 = ct / dt if dt else 0
    has_try = "try" in txt and "catch" in txt
    log("long-gen: %.1f tok/s (%d tok / %.1fs) struct_ok=%s" % (tps2, ct, dt, has_try))
    log("long-gen-ans=%s" % txt.strip().replace("\n", " ")[:400])
except Exception as e:
    log("long FAIL %r" % e); tps2 = 0

# 4) CJK sanity
try:
    txt, ct, dt = chat([{"role": "user", "content": "用一句话说明什么是幂等性。"}], max_tokens=128)
    log("cjk: %s" % txt.strip().replace("\n", " ")[:200])
except Exception as e:
    log("cjk FAIL %r" % e)

verdict = "PASS" if (tps >= 30 and ok and tps2 >= 25) else "REVIEW"
log("VERDICT %s speed=%.1f long=%.1f" % (verdict, tps, tps2))
print("VERDICT %s speed=%.1f long=%.1f" % (verdict, tps, tps2))
