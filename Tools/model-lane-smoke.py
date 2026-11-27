# -*- coding: utf-8 -*-
"""model-lane-smoke.py - 模型车道常备冒烟（O-20261015-1505 优化点⑥·换装回归标准件）

Why: 10-15 换装现场手搓验证脚本的收编——任何模型换装/迁移/bm-d 切换后跑一遍，
五分钟出四车道绿红，不再现搭脚手架。车道与默认值按 bm-a v3 架构；全部可用
环境变量改指（bm-d 切换时=改 env 零改码，优化点⑤同源）。

车道：
  A brain     : BRAIN_URL (默认 http://127.0.0.1:8090/v1/chat/completions) 年轮短生成+思考泄漏检查
  B storyboard: 同 BRAIN_URL·JSON 结构化输出检查
  C flash     : FLASH_URL (默认 http://127.0.0.1:11434/v1/chat/completions) + FLASH_MODEL(qwen3:4b-instruct)
  D qa-gateway: QA_URL (默认 http://127.0.0.1:8792/health) 存活检查（不发真召见·荣誉席/轮值门禁不扰）
Exit: 0=全绿  1=有红  2=机制故障
"""
import json
import os
import sys
import time
import urllib.request

BRAIN = os.environ.get("BRAIN_URL", "http://127.0.0.1:8090/v1/chat/completions")
FLASH = os.environ.get("FLASH_URL", "http://127.0.0.1:11434/v1/chat/completions")
FLASH_MODEL = os.environ.get("FLASH_MODEL", "qwen3:4b-instruct")
QA = os.environ.get("QA_URL", "http://127.0.0.1:8792/health")
BRAIN_MODEL = os.environ.get("BRAIN_MODEL", "qwen3.6-35b")


def post(url, body, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8")), time.time() - t0


def verdicts():
    v = []
    try:
        a, wa = post(BRAIN, {"model": BRAIN_MODEL,
            "messages": [{"role": "user", "content":
                "你是硅基城市居民。写一句今天的年轮日记（中文·不超过30字·口语化）。"}],
            "max_tokens": 80, "temperature": 0.8,
            "chat_template_kwargs": {"enable_thinking": False}})
        ca = a["choices"][0]["message"]["content"]
        ok = ("<think" not in ca) and len(ca.strip()) >= 10
        v.append(("A brain 年轮", ok, "wall=%.1fs leak=%s" % (wa, "<think" in ca), ca[:60]))
    except Exception as e:
        v.append(("A brain 年轮", False, str(e)[:80], ""))
    try:
        b, wb = post(BRAIN, {"model": BRAIN_MODEL,
            "messages": [{"role": "user", "content":
                "只输出 JSON 数组 2 项，每项 {\"shot\": \"T1\", \"desc\": \"中文画面(≤30字)\"}。不要其他文字。"}],
            "max_tokens": 300, "temperature": 0.65,
            "chat_template_kwargs": {"enable_thinking": False}})
        cb = b["choices"][0]["message"]["content"]
        arr = json.loads(cb[cb.find("["):cb.rfind("]") + 1])
        ok = len(arr) == 2 and arr[0].get("desc")
        v.append(("B storyboard JSON", ok, "wall=%.1fs" % wb, cb[:60]))
    except Exception as e:
        v.append(("B storyboard JSON", False, str(e)[:80], ""))
    try:
        c, wc = post(FLASH, {"model": FLASH_MODEL,
            "messages": [{"role": "user", "content": "用一句大白话回答：本地模型是什么？"}],
            "max_tokens": 80, "temperature": 0.3})
        cc = c["choices"][0]["message"]["content"]
        ok = ("<think" not in cc) and len(cc.strip()) >= 8
        v.append(("C flash %s" % FLASH_MODEL, ok, "wall=%.1fs" % wc, cc[:60]))
    except Exception as e:
        v.append(("C flash", False, str(e)[:80], ""))
    try:
        with urllib.request.urlopen(QA, timeout=10) as r:
            j = json.loads(r.read().decode("utf-8"))
        ok = j.get("status") == "ok"
        v.append(("D qa-gateway", ok, json.dumps(j, ensure_ascii=False)[:80], ""))
    except Exception as e:
        v.append(("D qa-gateway", False, str(e)[:80], ""))
    return v


def main():
    print("== model-lane-smoke (O-20261015-1505) brain=%s flash=%s qa=%s" % (BRAIN, FLASH, QA))
    rc = 0
    for name, ok, info, sample in verdicts():
        print("[%-18s] %s | %s | %s" % (name, "PASS" if ok else "FAIL", info, sample))
        if not ok:
            rc = 1
    print("SMOKE %s" % ("GREEN" if rc == 0 else "RED"))
    return rc


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
