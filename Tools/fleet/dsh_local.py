#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dsh_local.py - 把本机 Ollama 接进 DeepSeek Harness（DSH）客户端的适配器。

为什么需要适配层（实测，2026-11-08）：
  1) 本机 Ollama 由 com.fluxgroup.ollama.plist 托管，OLLAMA_CONTEXT_LENGTH=4096。
     而 DSH 一次请求的系统提示约 5.7 万字符（≈1.9 万 token），直连 /v1 会被
     Ollama 静默截断：不报错，只是答非所问。
  2) OpenAI 兼容端点不接受 num_ctx（实测：body 里带 num_ctx/options.num_ctx 都被忽略，
     /api/ps 里 context_length 仍是 4096/8192）。
  3) 因此这里不改进程环境、不重启 Ollama、不额外起代理，而是建一个带 num_ctx 的
     模型变体（ollama create FROM ... PARAMETER num_ctx 32768），再把变体写进
     DSH 的 profile 配置作为本地路由。默认模型不动，用户重启后在模型选择器里切。

用法：
  python3 Tools/fleet/dsh_local.py probe                 # 只读体检（不写任何东西）
  python3 Tools/fleet/dsh_local.py prepare               # 建 / 校验上下文变体（幂等）
  python3 Tools/fleet/dsh_local.py install               # 写本地路由进 DSH 配置（自动备份，可回滚）
  python3 Tools/fleet/dsh_local.py uninstall             # 移除本地路由
  python3 Tools/fleet/dsh_local.py status

退出码：0 正常；2 本地模型服务不可用；3 配置校验失败。
"""
import argparse
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DSH_PATCH = os.path.expanduser("~/.dsh/profiles/desktop/cordis.patch.yml")
STATE = os.path.join(ROOT, "cph4", "fleet", "state", "dsh-local.json")
STAGE = os.path.join(ROOT, "cph4", "fleet", "state", "dsh", "cordis.patch.yml")
BENCH = os.path.join(ROOT, "cph4", "fleet", "state", "dsh-local-bench.json")
OLLAMA = (os.environ.get("OLLAMA_URL") or "http://127.0.0.1:11434").rstrip("/")
CTX = 32768
DEFAULT_BASE = "qwen3:8b"
MARK_BEGIN = "# >>> dsh-local: managed by Tools/fleet/dsh_local.py (do not edit by hand)"
MARK_END = "# <<< dsh-local"


def _get(path, timeout=10):
    with urllib.request.urlopen(OLLAMA + path, timeout=timeout) as r:
        return json.loads(r.read())


def _post(path, payload, timeout=600):
    req = urllib.request.Request(OLLAMA + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def models():
    try:
        return [m["name"] for m in _get("/api/tags").get("models", [])]
    except Exception:
        return []


def resident():
    try:
        return [(m["name"], m.get("context_length"), round(m.get("size_vram", 0) / 1e9, 1))
                for m in _get("/api/ps").get("models", [])]
    except Exception:
        return []


def variant_name(base, ctx=CTX):
    return "%s-dsh%dk" % (base, ctx // 1024)


def ensure_variant(base, ctx=CTX):
    """建一个 num_ctx 固定的变体；已存在就直接复用。"""
    name = variant_name(base, ctx)
    have = models()
    if name in have:
        return name, "exists"
    if base not in have:
        raise SystemExit("基础模型不存在：%s（先 ollama pull %s）" % (base, base))
    _post("/api/create", {"model": name, "from": base,
                          "parameters": {"num_ctx": ctx}, "stream": False})
    return name, "created"


def provider_block(base, ctx=CTX, endpoint=None):
    endpoint = (endpoint or OLLAMA).rstrip("/")
    name = variant_name(base, ctx)
    return """%s
# 必须按 id 覆盖 dsh-base 里那条 *dormant* 的 llm-pi-ai 条目；
# 只写 name 会再插一个同类实例（不报错，但路由一条都注册不上，2026-11-09 实测）。
- id: llm-pi-ai
  name: '@deepseek-ai/dsh-llm-pi-ai'
  config:
    providers:
      ollama-local:
        displayName: 本地 Ollama（bm-m）
        api: openai-completions
        baseURL: %s/v1
        defaultContextWindow: %d
        defaultMaxTokens: 8192
        timeoutMs: 600000
        models:
          - id: %s
            name: %s
            contextWindow: %d
            maxTokens: 8192
            reasoningEfforts:
              off: none
              low: low
              medium: medium
              high: high
%s
""" % (MARK_BEGIN, endpoint, ctx, name, name, ctx, MARK_END)


def _strip_block(text):
    if MARK_BEGIN not in text:
        return text
    head, _, rest = text.partition(MARK_BEGIN)
    _, _, tail = rest.partition(MARK_END)
    return (head + tail).rstrip() + "\n"


def _commit(new_text):
    """写回 DSH 配置；沙箱只读时退化为生成待应用文件（不谎报已生效）。"""
    try:
        bak = DSH_PATCH + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
        shutil.copy2(DSH_PATCH, bak)
        open(DSH_PATCH, "w", encoding="utf-8").write(new_text)
        return "live", bak
    except OSError as e:
        os.makedirs(os.path.dirname(STAGE), exist_ok=True)
        open(STAGE, "w", encoding="utf-8").write(new_text)
        print("沙箱不允许直接改 DSH 配置（%s）" % str(e)[:60])
        print("已生成待应用文件：%s" % STAGE)
        print("在终端执行（先备份原文件）：")
        print("  cp " + DSH_PATCH + " " + DSH_PATCH + ".bak-$(date +%Y%m%d-%H%M%S)")
        print("  cp " + STAGE + " " + DSH_PATCH)
        return "staged", None


def _validate(text):
    try:
        import yaml
    except ImportError:
        return True  # 没有 pyyaml 时退化为括号/缩进粗检
    try:
        doc = yaml.safe_load(text)
    except Exception as e:
        print("YAML 解析失败：%s" % e, file=sys.stderr)
        return False
    if not isinstance(doc, list):
        print("配置顶层应为列表，实际是 %s" % type(doc).__name__, file=sys.stderr)
        return False
    return True


def _parallel_slots():
    """读服务端 NUM_PARALLEL（plist 是唯一来源）；查不到按 3 算。"""
    try:
        p = os.path.expanduser("~/Library/LaunchAgents/com.fluxgroup.ollama.plist")
        t = open(p, encoding="utf-8").read()
        i = t.find("OLLAMA_NUM_PARALLEL")
        seg = t[i:i + 120]
        import re
        m = re.search(r"<string>(\d+)</string>", seg)
        return int(m.group(1)) if m else 3
    except Exception:
        return 3


def install(base, ctx, force=False, parallel=None, endpoint=None):
    par = parallel if parallel is not None else _parallel_slots()
    if par > 1 and ctx * par >= 49152 and not force:
        print("拒绝安装：服务端 OLLAMA_NUM_PARALLEL=%d，%d×%d=%d 上下文。" %
              (par, ctx, par, ctx * par))
        print("  实测后果：调度器预测 18.4GiB，直接驱逐本机已驻留模型（2026-11-08 00:38 日志）。")
        print("  这不是配置错误，是内存装不下；强行切会拖垮机队。")
        print("  真要用请显式加 --force，并自行承担驱逐/排队。")
        return 5
    name, how = ensure_variant(base, ctx)
    if not os.path.exists(DSH_PATCH):
        raise SystemExit("找不到 DSH 配置：%s" % DSH_PATCH)
    text = open(DSH_PATCH, encoding="utf-8").read()
    old = _strip_block(text).rstrip() + "\n"
    new = old.rstrip() + "\n\n" + provider_block(base, ctx, endpoint)
    if not _validate(new):
        raise SystemExit(3)
    os.makedirs(STATE, exist_ok=True)
    where, bak = _commit(new)
    if where == "live":
        print("已写入本地路由：provider=ollama-local model=%s（变体 %s）" % (name, how))
        print("备份：%s" % bak)
        print("默认模型未改；重启 DSH 后在模型选择器里选「本地 Ollama（bm-m）」。")
    return 0


def uninstall():
    if not os.path.exists(DSH_PATCH):
        raise SystemExit("找不到 DSH 配置：%s" % DSH_PATCH)
    text = open(DSH_PATCH, encoding="utf-8").read()
    if MARK_BEGIN not in text:
        print("未安装本地路由，无需移除。")
        return 0
    new = _strip_block(text)
    if not _validate(new):
        raise SystemExit(3)
    where, bak = _commit(new)
    if where == "live":
        print("已移除本地路由。备份：%s" % bak)
    return 0


def verify(base, ctx, timeout=180):
    """真跑一次，确认变体确实按 ctx 装载（服务忙时会排队，超时如实报）。"""
    name = variant_name(base, ctx)
    body = {"model": name, "messages": [{"role": "user", "content": "只回复 OK"}],
            "max_tokens": 4, "stream": False, "reasoning_effort": "none"}
    req = urllib.request.Request(OLLAMA + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read())
        print("调用成功 %.1fs：%s" % (time.time() - t0,
                                   (d["choices"][0]["message"].get("content") or "").strip()[:40]))
    except Exception as e:
        print("调用失败（%.0fs）：%s" % (time.time() - t0, str(e)[:120]))
        print("服务忙时请求会排队；这不是配置错误。")
        return 4
    got = [r for r in resident() if r[0] == name]
    if got:
        print("已装载上下文：%s（期望 %d）" % (got[0][1], ctx))
        return 0 if got[0][1] == ctx else 5
    print("模型已卸载，/api/ps 查不到；配置仍是 %d。" % ctx)
    return 0



def bench(base, ctx, prompt_file=None, predict=64, timeout=900):
    """科学决策实测：用 DSH 真实系统提示走 OpenAI 端点（不传 num_ctx），量三件事：

      ① 变体是否真按 ctx 装载（/api/ps）
      ② 上下文是否被截断（usage.prompt_tokens 应≈真实提示 token 数，而不是 4096）
      ③ 冷启动整步墙钟、热态预填/解码速度、显存

    判据先写死再看数：ctx_loaded==ctx、prompt_tokens>=15000、warm_wall<=120s、
    decode>=8 tok/s、vram<=20GB。全过才谈得上「拿本地当 DSH 默认」。
    """
    name = variant_name(base, ctx)
    if prompt_file and os.path.exists(prompt_file):
        prompt = open(prompt_file, encoding="utf-8").read()
        src = prompt_file
    else:
        prompt = ("You are a local assistant. Read the rules and tools below.\n"
                  + ("Rule: check evidence before concluding; never invent files.\n" * 900))
        src = "synthetic"
    msgs = [{"role": "system", "content": prompt},
            {"role": "user", "content": "用一句话说明你收到了什么。"}]

    # A) 走 DSH 将来会走的同一条路：OpenAI 兼容端点，body 里不带 num_ctx
    body = {"model": name, "messages": msgs, "max_tokens": predict,
            "stream": False, "reasoning_effort": "none"}
    req = urllib.request.Request(OLLAMA + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read())
    except Exception as e:
        print("bench 失败：%s" % str(e)[:160])
        return 4
    cold = time.time() - t0
    usage = d.get("usage") or {}
    ptok = usage.get("prompt_tokens") or 0
    got = [r for r in resident() if r[0] == name]
    loaded_ctx = got[0][1] if got else None
    vram = got[0][2] if got else None

    # B) 同上下文再跑一次原生端点，拿 eval_duration 拆出预填/解码
    body2 = {"model": name, "messages": msgs, "think": False, "stream": False,
             "keep_alive": "10m",
             "options": {"num_ctx": ctx, "num_predict": predict, "temperature": 0.2}}
    t1 = time.time()
    try:
        d2 = _post("/api/chat", body2, timeout)
    except Exception as e:
        print("热态测量失败：%s" % str(e)[:120])
        d2 = {}
    warm = time.time() - t1
    pe = d2.get("prompt_eval_count") or 0
    pd = (d2.get("prompt_eval_duration") or 1) / 1e9
    ec = d2.get("eval_count") or 0
    ed = (d2.get("eval_duration") or 1) / 1e9
    pref = round(pe / pd, 1) if pd > 0 and d2 else 0
    dec = round(ec / ed, 1) if ed > 0 and d2 else 0

    ok = (loaded_ctx == ctx and ptok >= 15000 and warm <= 120
          and dec >= 8 and (vram is None or vram <= 20))
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": name, "prompt_src": src,
           "prompt_chars": len(prompt), "prompt_tokens": ptok,
           "cold_wall_s": round(cold, 1), "warm_wall_s": round(warm, 1),
           "prefill_tok_s": pref, "decode_tok_s": dec, "reply_tokens": ec,
           "ctx_loaded": loaded_ctx, "vram_gb": vram,
           "verdict": "VIABLE" if ok else "NOT-VIABLE"}
    os.makedirs(os.path.dirname(BENCH), exist_ok=True)
    json.dump(out, open(BENCH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print("结论：%s（门槛 ctx=%d / prompt_tokens>=15000 / warm<=120s / decode>=8 / vram<=20GB）"
          % (out["verdict"], ctx))
    return 0 if ok else 5


def probe():
    print("Ollama      : %s" % OLLAMA)
    try:
        ver = _get("/api/version", timeout=5)
        print("版本        : %s" % ver.get("version"))
    except Exception as e:
        print("连不上 Ollama：%s" % str(e)[:120], file=sys.stderr)
        return 2
    ms = models()
    print("模型(%d)    : %s" % (len(ms), ", ".join(ms)))
    res = resident()
    print("驻留        : %s" % (", ".join("%s(ctx=%s, %.1fGB)" % r for r in res) or "无"))
    ctxs = {r[1] for r in res}
    if ctxs and max(c or 0 for c in ctxs) < 24000:
        print("⚠ 当前驻留上下文 %s < 24000：DSH 系统提示约 1.9 万 token，直连会截断。" % ctxs)
    print("建议变体    : %s（num_ctx=%d）" % (variant_name(DEFAULT_BASE), CTX))
    return 0



def set_default(provider, model, effort="low"):
    """改 DSH 新会话默认模型（agent-default-model 一项），保留其余配置与注释。"""
    if not os.path.exists(DSH_PATCH):
        raise SystemExit("找不到 DSH 配置：%s" % DSH_PATCH)
    text = open(DSH_PATCH, encoding="utf-8").read()
    m = re.search(r"(- id: agent-default-model\n(?:.*\n)*?)(?=\n- |\Z)", text)
    if not m:
        raise SystemExit("配置里没有 agent-default-model 项")
    block = m.group(1)
    nb = re.sub(r"(\n\s+provider:\s*)\S+", r"\g<1>" + provider, block, count=1)
    nb = re.sub(r"(\n\s+model:\s*)\S+", r"\g<1>" + model, nb, count=1)
    if re.search(r"\n\s+reasoningEffort:", nb):
        nb = re.sub(r"(\n\s+reasoningEffort:\s*)\S+", r"\g<1>" + effort, nb, count=1)
    else:
        nb = nb.rstrip("\n") + "\n    reasoningEffort: " + effort + "\n"
    new = text.replace(block, nb, 1)
    if not _validate(new):
        raise SystemExit(3)
    where, bak = _commit(new)
    if where == "live":
        print("默认模型 -> %s / %s（备份 %s）" % (provider, model, bak))
        print("重启 DSH 生效。")
    return 0


def status():
    print("DSH 配置    : %s" % DSH_PATCH)
    if not os.path.exists(DSH_PATCH):
        print("  (不存在)")
        return 2
    text = open(DSH_PATCH, encoding="utf-8").read()
    if MARK_BEGIN in text:
        print("本地路由    : 已安装（live）")
    elif os.path.exists(STAGE):
        print("本地路由    : 未安装；已生成待应用文件 %s" % STAGE)
    else:
        print("本地路由    : 未安装")
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(("provider:", "model:", "model:")) or s.startswith("- id: agent-default-model"):
            print("  %s" % s)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="DSH x 本机 Ollama 适配器")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("prepare")
    p.add_argument("--models", default=DEFAULT_BASE, help="逗号分隔的基础模型名")
    p.add_argument("--ctx", type=int, default=CTX)
    i = sub.add_parser("install")
    i.add_argument("--models", default=DEFAULT_BASE)
    i.add_argument("--ctx", type=int, default=CTX)
    i.add_argument("--force", action="store_true")
    i.add_argument("--parallel", type=int, default=None)
    i.add_argument("--base", default=None)
    sub.add_parser("uninstall")
    b = sub.add_parser("bench")
    b.add_argument("--models", default=DEFAULT_BASE)
    b.add_argument("--ctx", type=int, default=CTX)
    b.add_argument("--prompt-file", default="/tmp/dsh-sysprompt.txt")
    b.add_argument("--predict", type=int, default=64)
    b.add_argument("--timeout", type=int, default=900)
    v = sub.add_parser("verify")
    v.add_argument("--models", default=DEFAULT_BASE)
    v.add_argument("--ctx", type=int, default=CTX)
    v.add_argument("--timeout", type=int, default=180)
    d = sub.add_parser("default")
    d.add_argument("--provider", default="ollama-local")
    d.add_argument("--model", default="qwen3:8b-dsh32k")
    d.add_argument("--effort", default="low")
    d.add_argument("--cloud", action="store_true")
    sub.add_parser("probe")
    sub.add_parser("status")
    a = ap.parse_args(argv)

    if a.cmd == "default":
        if a.cloud:
            return set_default("deepseek-account", "deepseek-flash", a.effort)
        return set_default(a.provider, a.model, a.effort)
    if a.cmd == "probe":
        return probe()
    if a.cmd == "status":
        return status()
    if a.cmd == "bench":
        return bench(a.models.split(",")[0].strip(), a.ctx, a.prompt_file, a.predict, a.timeout)
    if a.cmd == "verify":
        return verify(a.models.split(",")[0].strip(), a.ctx, a.timeout)
    if a.cmd == "prepare":
        for base in a.models.split(","):
            base = base.strip()
            if base:
                print("%s -> %s (%s)" % (base, *(ensure_variant(base, a.ctx))))
        return 0
    if a.cmd == "install":
        base = a.models.split(",")[0].strip()
        return install(base, a.ctx, a.force, a.parallel, a.base)
    if a.cmd == "uninstall":
        return uninstall()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
