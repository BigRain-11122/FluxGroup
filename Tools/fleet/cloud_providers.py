#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cloud_providers.py - 云端多通道统一入口（本地优先，云端只做升级件）。

2026-11-10 CEO：本机豆包/千问会员在手，可调用其云端能力；主控统一调度。

重要事实（必须说清）：
  桌面版会员 ≠ API 额度。程序调用要各自平台的 API Key：
    豆包  -> 火山方舟 Ark（ARK_API_KEY，OpenAI 兼容 /api/v3）
    千问  -> 阿里云百炼 DashScope（DASHSCOPE_API_KEY，compatible-mode/v1）
  消费级会员通常不含 API 计费；API 一般有免费额度、超出按量计费。

密钥只放本机：~/.config/fluxgroup/cloud-keys.env（chmod 600），不进 git：
  ARK_API_KEY=...
  ARK_MODEL=doubao-pro-32k        # 或你在方舟创建的推理接入点 ID
  DASHSCOPE_API_KEY=...
  DASHSCOPE_MODEL=qwen-plus

用途边界：
  - 公司业务 -> 只走团结 Codely（公司座席，合规闸）；
  - 个人/非公司 -> 可用豆包/千问（个人账号，费用自理）；
  - 本地能判的，一律不上云。

用法：
  python3 Tools/fleet/cloud_providers.py status
  python3 Tools/fleet/cloud_providers.py ask --provider qwen --prompt "用一句话解释RAG"
"""
import argparse
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
KEYFILE = os.path.expanduser("~/.config/fluxgroup/cloud-keys.env")

ORDER = ["deepseek", "codely"]  # 2026-11-10 CEO：本地优先；免费时段走 DeepSeek；Codely 非必要不走

PROVIDERS = {
    "deepseek": {"label": "DeepSeek（免费时段优先）", "key": "DEEPSEEK_API_KEY",
                 "base": "https://api.deepseek.com/v1",
                 "model_env": "DEEPSEEK_MODEL", "model": "deepseek-chat"},
    "doubao": {"label": "豆包（火山方舟）", "key": "ARK_API_KEY",
               "base": "https://ark.cn-beijing.volces.com/api/v3",
               "model_env": "ARK_MODEL", "model": "doubao-pro-32k"},
    "qwen": {"label": "千问（百炼 DashScope）", "key": "DASHSCOPE_API_KEY",
             "base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
             "model_env": "DASHSCOPE_MODEL", "model": "qwen-plus"},
}


def load_keys():
    env = {}
    try:
        for line in open(KEYFILE, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    for p in PROVIDERS.values():
        if os.environ.get(p["key"]):
            env.setdefault(p["key"], os.environ[p["key"]])
    return env


def status():
    env = load_keys()
    out = {}
    for name, p in PROVIDERS.items():
        has = bool(env.get(p["key"]))
        out[name] = {"label": p["label"], "key_present": has,
                     "model": env.get(p["model_env"]) or p["model"],
                     "base": p["base"]}
    # 团结 Codely：官方 CLI 存在即视为通道可用（座席合规另由 bridge 管）
    cli = os.path.expanduser("~/Library/Application Support/Tuanjie Cowork/bin/codely")
    out["codely"] = {"label": "团结 Codely（公司座席）", "key_present": os.path.isfile(cli),
                     "model": "codely-core", "base": "official-cli"}
    return out


def offpeak(now=None):
    """DeepSeek 优惠时段 = UTC 16:30-00:30 = 北京时间 00:30-08:30。"""
    import datetime
    bj = (now or datetime.datetime.utcnow()) + datetime.timedelta(hours=8)
    m = bj.hour * 60 + bj.minute
    return 30 <= m < 510


def available():
    st = status()
    return [n for n in ORDER if (st.get(n) or {}).get("key_present")]


def ask_chain(prompt, allow_company=False, timeout=120, max_tokens=1024, urgent=False):
    """按 ORDER 依次试；DeepSeek 只在免费时段（或 urgent）用；Codely 需 allow_company。"""
    errs = []
    for name in ORDER:
        if name == "deepseek" and not offpeak() and not urgent:
            errs.append("deepseek:offpeak-only")
            continue
        if name == "codely":
            if not allow_company:
                continue
            return ("codely", None)
        try:
            return (name, ask(name, prompt, timeout=timeout, max_tokens=max_tokens))
        except SystemExit as e:
            errs.append("%s:%s" % (name, str(e)[:60]))
        except Exception as e:
            errs.append("%s:%s" % (name, str(e)[:80]))
    return ("", "all cloud providers unavailable: " + "; ".join(errs))


def ask(provider, prompt, timeout=120, max_tokens=1024):
    env = load_keys()
    p = PROVIDERS.get(provider)
    if not p:
        raise SystemExit("unknown provider: %s" % provider)
    key = env.get(p["key"])
    if not key:
        raise SystemExit("missing %s (put it in %s)" % (p["key"], KEYFILE))
    try:
        import token_guard as tg
        prompt, _saved = tg.guard(prompt, int(os.environ.get("TOKEN_BUDGET") or 16000))
    except Exception:
        pass
    model = env.get(p["model_env"]) or p["model"]
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": max_tokens, "temperature": 0.2}).encode()
    req = urllib.request.Request(p["base"].rstrip("/") + "/chat/completions", data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    return ((d.get("choices") or [{}])[0].get("message") or {}).get("content") or ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "ask"])
    ap.add_argument("--provider", default="qwen")
    ap.add_argument("--prompt", default="")
    a = ap.parse_args()
    if a.cmd == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=1))
        return 0
    print(ask(a.provider, a.prompt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
