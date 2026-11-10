#!/usr/bin/env python3
"""本地大模型链路健康检查（DSH → Ollama）。

逐段验证：服务存活 → 模型在场 → 凭据引用 → 关思考可用 → 工具调用 → DSH 配置 → 压缩预算。

用法：
    python3 Tools/fleet/check_local_llm.py          # 快速检查
    python3 Tools/fleet/check_local_llm.py --full   # 额外做 ~13k token 上下文实测
"""
import json
import os
import sys
import urllib.error
import urllib.request

DSH_PATCH = os.path.expanduser("~/.dsh/profiles/desktop/cordis.patch.yml")
CREDS = os.path.expanduser("~/.dsh/.credentials.yaml")
MODEL = "qwen3.5:4b-mlx"
ROUTE = "ollama-local"

ok = fail = 0


def check(name, fn):
    global ok, fail
    try:
        detail = fn()
        ok += 1
        print(f"  \033[32mPASS\033[0m {name}" + (f" — {detail}" if detail else ""))
    except Exception as e:
        fail += 1
        print(f"  \033[31mFAIL\033[0m {name} — {type(e).__name__}: {str(e)[:180]}")


def load_yaml(path):
    import yaml
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def dsh_provider():
    for entry in load_yaml(DSH_PATCH):
        if entry.get("id") == "llm-pi-ai":
            return entry["config"]["providers"][ROUTE]
    raise KeyError("配置里没有 ollama-local 路由")


def dsh_compaction():
    for entry in load_yaml(DSH_PATCH):
        if entry.get("id") == "compaction-basic":
            return entry["config"]
    return {}


def endpoint():
    return dsh_provider()["baseURL"].rstrip("/")


def post(path, body, timeout=300):
    url = endpoint().replace("/v1", "") + path
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def t_service():
    url = endpoint().replace("/v1", "") + "/api/version"
    with urllib.request.urlopen(url, timeout=10) as r:
        d = json.load(r)
    return f"Ollama {d['version']} @ {endpoint()}"


def t_model():
    d = post("/api/show", {"model": MODEL}, timeout=30)
    caps = ",".join(d.get("capabilities") or [])
    return f"{MODEL} 能力={caps}"


def t_credential():
    ref = dsh_provider().get("apiKeyEnv")
    if not ref:
        return "路由未设 apiKeyEnv（走 pi-ai 环境发现）"
    refs = (load_yaml(CREDS) or {}).get("refs") or {}
    if ref not in refs:
        raise KeyError(f"{ref} 不在 {CREDS} 的 refs 里")
    return f"{ref} 已入凭据库"


def t_chat_no_think():
    d = post(
        "/v1/chat/completions",
        {
            "model": MODEL,
            "messages": [{"role": "user", "content": "只回复两个字：可用"}],
            "max_tokens": 32,
            "stream": False,
            "reasoning_effort": "none",
        },
    )
    msg = d["choices"][0]["message"]
    if not (msg.get("content") or "").strip():
        raise ValueError("content 为空（思考未关闭或被截断）")
    return f"回复={msg['content'].strip()[:10]!r} 用量={d['usage']['total_tokens']}"


def t_tools():
    d = post(
        "/v1/chat/completions",
        {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "你是编码助手，必须通过工具完成任务。"},
                {"role": "user", "content": "执行 ls -la 看看当前目录"},
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "bash",
                        "description": "执行 bash 命令",
                        "parameters": {
                            "type": "object",
                            "properties": {"command": {"type": "string"}},
                            "required": ["command"],
                        },
                    },
                }
            ],
            "max_tokens": 256,
            "stream": False,
            "reasoning_effort": "none",
        },
    )
    calls = d["choices"][0]["message"].get("tool_calls") or []
    if not calls:
        raise ValueError("模型没有返回 tool_calls")
    return f"tool_calls={[c['function']['name'] for c in calls]}"


def t_config():
    p = dsh_provider()
    wins = {m["id"]: m.get("contextWindow") for m in p["models"]}
    if MODEL not in wins:
        raise KeyError(f"{MODEL} 不在 providers.{ROUTE}.models 里")
    return f"baseURL={p['baseURL']} 模型={list(wins)} 窗口={wins[MODEL]}"


def t_budget():
    c = dsh_compaction()
    W = next(m["contextWindow"] for m in dsh_provider()["models"] if m["id"] == MODEL)
    pol = next(
        (m for m in (c.get("modelPolicies") or []) if m.get("model") == MODEL), {}
    )
    O = pol.get("maxTokens") or c.get("maxTokens") or W
    B = pol.get("headroomTokens") or c.get("headroomTokens") or 65536
    budget = W - O - B
    if budget <= 0:
        raise ValueError(f"W-O-B={budget} ≤ 0，切模型会失败")
    return f"W={W} O={O} B={B} → 压力预算 {budget}"


def t_context():
    filler = "这是一段用于测试上下文长度的填充文本。" * 1400
    d = post(
        "/v1/chat/completions",
        {
            "model": MODEL,
            "messages": [{"role": "user", "content": filler + "\n\n只回复两个字：可用"}],
            "max_tokens": 8,
            "stream": False,
            "reasoning_effort": "none",
        },
        timeout=900,
    )
    n = d["usage"]["prompt_tokens"]
    if n < 12000:
        raise ValueError(f"只吃下 {n} token，上下文疑似被截断")
    return f"摄入 {n} token 未截断"


def main():
    print(f"本地大模型链路检查（DSH 路由 {ROUTE}）")
    check("服务存活", t_service)
    check("模型在场", t_model)
    check("DSH 路由配置", t_config)
    check("凭据引用", t_credential)
    check("压缩预算", t_budget)
    check("关思考出正文", t_chat_no_think)
    check("工具调用", t_tools)
    if "--full" in sys.argv:
        print("  … 上下文实测较慢，请稍候")
        check("长上下文", t_context)
    print(f"\n结果：{ok} 通过，{fail} 失败")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
