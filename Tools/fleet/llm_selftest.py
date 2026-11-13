#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""llm_selftest.py - 判断「这台机器到底能不能用主控的本地大模型」。

为什么需要它：网关 8792 开着、代码在 origin/main 上，都不等于**这台机器**能用——
  · 本机没写 ~/.fluxgroup-llm-token → 401，机器静默失败或干脆不调；
  · tailnet 不通 / 网关没起 → 连接被拒，被当成「模型不可用」；
  · 节点还写着封存的老模型名 → 403，看起来像网关坏了。
这三种在回执里长得一样（都是"没结果"），所以必须有一个工具把原因分清楚。

返回码（三态，缺料不算失败）：
  0 = 可用（生成 200，且白名单负控生效）
  3 = 缺前置（没令牌文件 / 没设端点）→ 该做的事是准备，不是修网关
  1 = 真故障（连不上 / 令牌不对 / 白名单失效）

用法：
  python3 Tools/fleet/llm_selftest.py                     # 人读
  python3 Tools/fleet/llm_selftest.py --json out.json     # 卡回执用
  python3 Tools/fleet/llm_selftest.py --model qwen3:1.7b  # 指定档位
环境：
  FLUX_LLM_BASE   默认 http://100.75.133.10:8792（主控 tailnet 地址）
  FLUX_LLM_TOKEN_FILE 默认 ~/.fluxgroup-llm-token
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE = "http://100.75.133.10:8792"
DEFAULT_TOKEN = os.path.expanduser("~/.fluxgroup-llm-token")
PROBE = "只回答两个字：收到"
# 用于负控：策略里封存/对照的档位，网关必须拒绝
DENY_CANDIDATES = ("qwen3:4b-instruct", "qwen3.5:4b", "qwen3:35b")


def call(base, path, token, body=None, timeout=60):
    url = base.rstrip("/") + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data,
                                headers={"Content-Type": "application/json",
                                         "X-Flux-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {"error": "%s: %s" % (type(e).__name__, str(e)[:120])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("FLUX_LLM_BASE", DEFAULT_BASE))
    ap.add_argument("--token-file",
                    default=os.environ.get("FLUX_LLM_TOKEN_FILE", DEFAULT_TOKEN))
    ap.add_argument("--model", default="qwen3.5:4b-mlx")
    ap.add_argument("--json", default="")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--skip-deny-test", action="store_true",
                    help="跳过白名单负控（只在网关不在本机时用，会少判一项）")
    a = ap.parse_args()

    rep = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "base": a.base,
           "model": a.model, "checks": {}, "verdict": "", "why": ""}

    def done(rc, verdict, why):
        rep["verdict"] = verdict
        rep["why"] = why
        if a.json:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(a.json)) or ".", exist_ok=True)
                with open(a.json, "w", encoding="utf-8") as f:
                    json.dump(rep, f, ensure_ascii=False, indent=1)
            except Exception as e:
                print("[llm-selftest] 写 json 失败:", e)
        print("[llm-selftest] %s %s" % (verdict, why))
        for k, v in rep["checks"].items():
            print("  %-12s %s" % (k, v))
        return rc

    # 1) 令牌：缺文件就是缺料（rc=3），不是网关故障
    try:
        token = open(a.token_file).read().strip()
    except Exception:
        token = ""
    if not token:
        rep["checks"]["token"] = "MISSING %s" % a.token_file
        return done(3, "E-NO-TOKEN",
                    "本机没有 %s（权限 600、串与主控一致、不入 git）" % a.token_file)
    rep["checks"]["token"] = "present len=%d" % len(token)

    # 2) 连通 + 认证：/api/tags 最便宜
    code, body = call(a.base, "/api/tags", token, timeout=min(a.timeout, 20))
    rep["checks"]["tags"] = "http=%d" % code
    if code == 0:
        return done(1, "E-UNREACHABLE", "%s 连不上：%s" % (a.base, body.get("error", "")[:80]))
    if code == 401:
        return done(1, "E-BAD-TOKEN", "网关拒绝令牌（本机串与主控不一致或被轮换）")
    if code != 200:
        return done(1, "E-BAD-GATEWAY", "GET /api/tags http=%d %s" % (code, body.get("error", "")[:80]))

    # 2b) 令牌到底有没有被校验：拿一个故意错的串再打一次 /api/tags。
    # 2026-11-10 CEO 选 B（tailnet/回环免令牌）之后，本机自呼永远 200——那时
    # "令牌通过"这句是假的，必须如实标成"未校验"，否则出问题会去查错的地方。
    c, _ = call(a.base, "/api/tags", token + "-deliberately-wrong", timeout=min(a.timeout, 20))
    enforced = (c == 401)
    rep["checks"]["token_enforced"] = "yes（错令牌被拒）" if enforced else \
        "no（可信网段免令牌 / 网关未启令牌；本机可用但不代表令牌这条路是通的）"

    # 3) 真生成：光能列模型不算可用，必须真出一段话
    t0 = time.time()
    code, body = call(a.base, "/api/generate", token,
                      {"model": a.model, "prompt": PROBE, "stream": False,
                       "think": False, "options": {"num_predict": 16}},
                      timeout=a.timeout)
    dt = time.time() - t0
    text = (body.get("response") or "").strip()
    rep["checks"]["generate"] = "http=%d %.2fs response=%r" % (code, dt, text[:40])
    if code == 403:
        return done(1, "E-MODEL-DENIED",
                    "网关不认这个档位 %s：先把 LOCAL-MODEL-POLICY.json 的座位对齐" % a.model)
    if code != 200 or not text:
        return done(1, "E-GEN-FAILED", "生成失败 http=%d %s" % (code, body.get("error", "")[:100]))
    rep["checks"]["latency_s"] = round(dt, 3)

    # 4) 白名单负控：能拒绝封存档位才算门是活的（拦不住的闸等于没闸）
    if a.skip_deny_test:
        rep["checks"]["deny"] = "SKIPPED"
    else:
        hit = None
        for m in DENY_CANDIDATES:
            c, _ = call(a.base, "/api/generate", token,
                        {"model": m, "prompt": "hi", "stream": False,
                         "options": {"num_predict": 1}}, timeout=min(a.timeout, 20))
            if c == 200:
                hit = m
                break
        rep["checks"]["deny"] = "OK (封存档位被拒)" if not hit else "FAIL 放行了 %s" % hit
        if hit:
            return done(1, "E-WHITELIST-LEAK",
                        "网关放行了本应封存的 %s（远端能拉起来顶掉常驻主力）" % hit)

    return done(0, "OK", "%s 可用，延迟 %.2fs，白名单负控通过%s"
                % (a.model, dt, "" if enforced else "（令牌未被校验：可信网段免令牌）"))


if __name__ == "__main__":
    sys.exit(main())