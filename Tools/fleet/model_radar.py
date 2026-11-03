#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model_radar.py - 本地模型每日扫描+实测：有新版本就测，测不过就不换。

为什么（CEO 2026-11-03「不断打磨本地的模型使用策略，保证质量和速度，还有及时更新，
每天都要扫描和测试是否有更新的，创建一个机制」）：
  换模型最容易犯两个错——凭版本号或榜单换（不可比）、凭一次未预热的墙钟比速度（假结论，
  我自己就犯过：把 0.93s 模型加载算进墙钟，得出"新版慢 2.8 倍"的反向结论）。
  所以本工具只做四件事，且全部可复算：
    1 扫：本机已装 digest vs 上游 manifest digest，同 tag 变 digest=上游重发，页面上新 tag=新档
    2 测：先预热，再用 API 的 eval_duration/eval_count 只算解码段，多次取中位
    3 判：黄金集命中数不许降、解码速度不许掉超 10%、必须 mem_gate 放行——三条全过才建议换
    4 报：写 state/model-radar.json + 台账，建议不自动生效（换档由主控脉/CEO 决定）

用法：
  python3 Tools/fleet/model_radar.py scan             # 只扫版本（不占 GPU）
  python3 Tools/fleet/model_radar.py bench --models qwen3:4b-instruct,qwen3.5:4b --n 3
  python3 Tools/fleet/model_radar.py decide           # 用最新 bench 判是否建议换档
  python3 Tools/fleet/model_radar.py run              # 每日任务：扫+（需要时）测+判+报
Exit: 0 正常；2 有可用更新待裁定（不是故障，是提醒）
"""
import argparse
import json
import os
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
POLICY = os.path.join(FLEET, "LOCAL-MODEL-POLICY.json")
LEDGER = os.path.join(FLEET, "model-radar", "LEDGER.jsonl")
OUT = os.path.join(STATE, "model-radar.json")

OLLAMA = "http://127.0.0.1:11434"
REGISTRY = "https://registry.ollama.ai/v2/library/%s/manifests/%s"
TAGS_PAGE = "https://ollama.com/library/%s/tags"
MANIFEST_ACCEPT = "application/vnd.docker.distribution.manifest.v2+json"


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def now_ts():
    return time.time()


def load_policy():
    with open(POLICY, encoding="utf-8") as f:
        return json.load(f)


def http_json(url, timeout=15, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def http_text(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "fluxgroup-model-radar/1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


# ---- 1 scan ---------------------------------------------------------------------
def local_models():
    """本机已装：name -> {digest,size,params}。"""
    out = {}
    try:
        d = http_json(OLLAMA + "/api/tags", timeout=8)
    except Exception:
        return out
    for m in d.get("models") or []:
        full = m.get("digest") or ""
        out[m.get("name")] = {"digest": full[:16], "digest_full": full,
                              "size_gb": round((m.get("size") or 0) / 1e9, 2)}
    return out


def remote_manifest(family, tag):
    """上游 manifest：返回 (manifest_digest, size_gb)。

    必须用 manifest 自身的 digest 跟本地比：`/api/tags` 的 digest 就是 manifest digest。
    早先拿 config.digest 比过，两者永远不相等——于是每个模型都被报成"有更新"，
    这类假信号比不扫更糟（会让"更新"这个词失效）。
    """
    import hashlib
    req = urllib.request.Request(REGISTRY % (family, tag), headers={"Accept": MANIFEST_ACCEPT})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            raw = r.read()
            hdr = r.headers.get("Docker-Content-Digest") or ""
    except urllib.error.HTTPError as e:
        return ("http-%d" % e.code, None)
    except Exception:
        return (None, None)
    digest = hdr.strip() or ("sha256:" + hashlib.sha256(raw).hexdigest())
    size = 0
    try:
        d = json.loads(raw.decode("utf-8", "replace"))
        size = sum((l.get("size") or 0) for l in (d.get("layers") or []))
    except Exception:
        pass
    return (digest, round(size / 1e9, 2) if size else None)


def remote_tags(family):
    """上游标签列表（页面解析，拿不到就返回空——不拿它当判据，只作"有新档"提示）。"""
    try:
        html = http_text(TAGS_PAGE % family)
    except Exception:
        return []
    tags = set()
    key = family + ":"
    i = 0
    while True:
        i = html.find(key, i)
        if i < 0:
            break
        j = i + len(key)
        k = j
        while k < len(html) and (html[k].isalnum() or html[k] in ".-"):
            k += 1
        tok = html[j:k]
        # 只留纯量化档位（跳过 -fp16/-q4 变体），避免几十个重复档位噪声
        if tok and "-" not in tok:
            tags.add(tok)
        i = k
    return sorted(tags)


def split_model(name):
    if ":" in name:
        fam, tag = name.split(":", 1)
        return fam, tag
    return name, "latest"


def scan():
    pol = load_policy()
    loc = local_models()
    ap = pol.get("auto_pull") or {}
    size_cap = float(ap.get("max_size_gb") or 6.0)
    rows = []
    for family in pol.get("tracked_families", []):
        installed = [n for n in loc if n.split(":")[0] == family]
        for name in installed:
            fam, tag = split_model(name)
            rdig, _rsize = remote_manifest(fam, tag)
            same = bool(rdig) and rdig.split(":")[-1][:16] == loc[name]["digest"]
            rows.append({"model": name, "family": fam, "tag": tag,
                         "local_digest": loc[name]["digest"],
                         "remote_digest": (rdig.split(":")[-1][:16] if rdig else None),
                         "size_gb": loc[name]["size_gb"],
                         "state": ("MISSING-REMOTE" if (rdig or "").startswith("http-") else
                                   ("SAME" if same else "UPDATED"))})
        # 家族里本机没有的档：只有"够小、能自动拉"的才列成候选，避免几十条噪声
        have = set(split_model(n)[1] for n in installed)
        new = []
        for tag in remote_tags(family):
            if tag in have:
                continue
            rdig, rsize = remote_manifest(family, tag)
            if rsize is None or rsize > size_cap:
                continue
            # 同内容改名（latest→8b、v1.5→latest 这类别名）不算新档
            if rdig and any(rdig.split(":")[-1][:16] == loc[n]["digest"] for n in loc):
                continue
            new.append({"model": "%s:%s" % (family, tag), "family": family, "tag": tag,
                        "local_digest": None,
                        "remote_digest": (rdig.split(":")[-1][:16] if rdig else None),
                        "size_gb": rsize, "state": "NEW-TAG"})
        rows.extend(new[:4])                       # 每家族最多 4 个候选，按页面顺序
    out = {"ts": now_iso(), "installed": len(loc), "rows": rows,
           "attention": [r["model"] for r in rows if r["state"] in ("UPDATED", "NEW-TAG")]}
    os.makedirs(STATE, exist_ok=True)
    _merge_state("scan", out)
    return out


# ---- 2 bench --------------------------------------------------------------------
def ask(model, prompt, num_predict=96, timeout=240):
    """一次生成，返回解码段速度与原始指标。预热由调用方负责。

    think=false 是必须的：qwen3 系的思考模型会把内容全放进 thinking，response 为空——
    评测端看到的就是"0 命中"，那是测量问题不是模型问题（2026-11-03 实测踩到）。
    """
    body = json.dumps({"model": model, "prompt": prompt, "stream": False, "think": False,
                       "options": {"temperature": 0, "num_predict": num_predict,
                                   "num_ctx": 8192}}).encode()
    req = urllib.request.Request(OLLAMA + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode("utf-8", "replace"))
    wall = time.time() - t0
    ec = d.get("eval_count") or 0
    ed = d.get("eval_duration") or 0
    pc = d.get("prompt_eval_count") or 0
    pd = d.get("prompt_eval_duration") or 0
    ld = d.get("load_duration") or 0
    return {"text": (d.get("response") or ""), "thinking": (d.get("thinking") or ""),
            "wall_s": round(wall, 2),
            "gen_tokens": ec, "load_s": round(ld / 1e9, 2),
            # 只算解码段：把加载与预填算进去比速度，是我 2026-11-03 犯过的错
            "decode_tok_s": round(ec / (ed / 1e9), 1) if ed else None,
            "prefill_tok_s": round(pc / (pd / 1e9), 1) if pd else None,
            "done": bool(d.get("done"))}


def score_quality(model, golden, timeout=240):
    hits, detail = 0, []
    for item in golden:
        try:
            r = ask(model, item["prompt"], num_predict=160, timeout=timeout)
            text = r["text"] or r["thinking"]      # 思考模型的答案可能在 thinking 里
        except Exception as e:
            detail.append({"id": item["id"], "ok": False, "why": "error:%s" % str(e)[:50]})
            continue
        ok = any(str(k) in text for k in item["must"])
        if ok and item.get("max_chars"):
            ok = len(text.strip()) <= int(item["max_chars"])
        hits += 1 if ok else 0
        detail.append({"id": item["id"], "ok": ok,
                       "head": text.strip().replace("\n", " ")[:60]})
    return {"hits": hits, "total": len(golden), "detail": detail}


def served_by(model):
    """这个模型由哪个引擎在跑（mlx / llamacpp）。取不到就返回 None，不猜。"""
    try:
        out = subprocess.run(["ollama", "ps"], capture_output=True, text=True,
                             timeout=10).stdout
    except Exception:
        return None
    for line in out.splitlines()[1:]:
        parts = line.split()
        if parts and parts[0] == model:
            for tok in parts:
                if tok in ("mlx", "llamacpp"):
                    return tok
    return None


def mem_ok(need_gb):
    """容量判据只留一处：复用 mem_gate.decide。"""
    try:
        sys.path.insert(0, HERE)
        import mem_gate
        d = mem_gate.decide(need_gb)
        return d.get("verdict") == "OK", d
    except Exception as e:
        return False, {"error": str(e)[:80]}


def bench(models, runs=3, skip_quality=False):
    pol = load_policy()
    golden = pol.get("golden_set") or []
    res = []
    for m in models:
        installed = local_models()
        size = (installed.get(m) or {}).get("size_gb")
        ok_mem, mem = mem_ok(size or 0)
        if not ok_mem:
            res.append({"model": m, "skipped": "mem_gate:%s" % mem.get("verdict"), "mem": mem})
            continue
        try:
            ask(m, "预热：只回 ok。", num_predict=8)          # 预热（不计入样本）
            samples = [ask(m, "用一句话说明：机队主控脉负责什么？", num_predict=96)
                       for _ in range(max(1, runs))]
        except Exception as e:
            res.append({"model": m, "skipped": "error:%s" % str(e)[:80]})
            continue
        sp = [s["decode_tok_s"] for s in samples if s["decode_tok_s"]]
        row = {"model": m, "size_gb": size,
               "decode_tok_s": round(statistics.median(sp), 1) if sp else None,
               # 引擎必须记下来：同一台机上 MLX 与 llamacpp 是两条不同实现，不记引擎的
               # "提速"结论过几天没人复现得了（2026-11-03 实测：qwen3.5 系走 mlx，
               # qwen3:4b-instruct 走 llamacpp，且上游没有它的 -mlx 版）。
               "engine": served_by(m),
               "runs": samples, "mem": mem}
        if not skip_quality:
            row["quality"] = score_quality(m, golden)
        res.append(row)
    out = {"ts": now_iso(), "runs": runs, "results": res}
    _merge_state("bench", out)
    return out


# ---- 3 decide -------------------------------------------------------------------
def decide():
    pol = load_policy()
    st = _read_state()
    bench_rows = {r["model"]: r for r in (st.get("bench") or {}).get("results", [])
                  if not r.get("skipped")}
    cur_name = pol["duties"]["resident"]["model"]
    cur = bench_rows.get(cur_name)
    acc = pol.get("accept_upgrade", {})
    verdicts = []
    # 所有参与实测的模型都错的题 = 题本身或用法有问题，不能记成模型缺陷
    miss_by_id = {}
    for m, r in bench_rows.items():
        for d in ((r.get("quality") or {}).get("detail") or []):
            if not d.get("ok"):
                miss_by_id.setdefault(d["id"], []).append(m)
    set_defects = sorted([i for i, ms in miss_by_id.items() if len(ms) >= max(2, len(bench_rows))])
    if not cur:
        verdicts.append({"model": cur_name, "action": "NEED-BENCH",
                         "why": "现役档没有实测数据，先跑 bench"})
        for m in bench_rows:
            if m != cur_name:
                verdicts.append({"model": m, "action": "CANDIDATE-NO-BASELINE",
                                 "why": "现役档无基线，无法判断是否更好"})
        return {"ts": now_iso(), "resident": cur_name, "verdicts": verdicts,
                "set_defects": set_defects}
    q0 = (cur.get("quality") or {}).get("hits", 0)
    s0 = cur.get("decode_tok_s") or 0
    for m, r in bench_rows.items():
        if m == cur_name:
            continue
        q = (r.get("quality") or {}).get("hits", 0)
        s = r.get("decode_tok_s") or 0
        if pol["duties"].get("sealed", {}).get("model") == m:
            verdicts.append({"model": m, "action": "SEALED", "why": "封存档不参与换档"})
            continue
        q_ok = q > q0
        s_ok = (s0 and s >= s0 * (1 - float(acc.get("speed_drop_max", 0.10))))
        gain = float(acc.get("speed_gain_min", 1.05))
        if q_ok and s_ok:
            verdicts.append({"model": m, "action": "SUGGEST-SWAP",
                             "why": "质量更高 %d>%d 且速度可接受 %.1f vs %.1f tok/s"
                                    % (q, q0, s, s0)})
        elif q == q0 and s >= s0 * gain:
            verdicts.append({"model": m, "action": "SUGGEST-SWAP",
                             "why": "同质量 %d/%d，速度 %.1f vs %.1f tok/s（快 %.0f%%）"
                                    % (q, (r.get("quality") or {}).get("total", 0), s, s0,
                                       (s / s0 - 1) * 100 if s0 else 0)})
        elif q < q0:
            verdicts.append({"model": m, "action": "KEEP",
                             "why": "质量更低：%d vs 现役 %d" % (q, q0)})
        elif q == q0 and s >= s0:
            verdicts.append({"model": m, "action": "KEEP",
                             "why": "同质量但不够快：%.1f vs %.1f tok/s（要求至少快 %.0f%%）"
                                    % (s, s0, (gain - 1) * 100)})
        else:
            verdicts.append({"model": m, "action": "KEEP",
                             "why": "更慢：%.1f vs 现役 %.1f tok/s（上限允许掉 %d%%）"
                                    % (s, s0, int(float(acc.get("speed_drop_max", 0.10)) * 100))})
    if not verdicts:
        verdicts.append({"model": cur_name, "action": "KEEP", "why": "无其它候选参与比较"})
    out = {"ts": now_iso(), "resident": cur_name,
           "baseline": {"quality": q0, "decode_tok_s": s0},
           "verdicts": verdicts, "set_defects": set_defects}
    _merge_state("decide", out)
    return out


# ---- state / ledger -------------------------------------------------------------
def _read_state():
    try:
        with open(OUT, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _merge_state(key, val):
    st = _read_state()
    st[key] = val
    st["updated"] = now_iso()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


def ledger(line):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def stale_days():
    st = _read_state()
    ts = (st.get("bench") or {}).get("ts")
    if not ts:
        return 999
    try:
        t = time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%S"))
    except Exception:
        return 999
    return (now_ts() - t) / 86400.0


# ---- 4 run ----------------------------------------------------------------------
def run():
    pol = load_policy()
    st = _read_state()
    today = time.strftime("%Y-%m-%d")
    if (st.get("last_run_day") == today) and "--force" not in sys.argv:
        print(json.dumps({"skipped": "already ran today", "day": today}, ensure_ascii=False))
        return 0
    lock = OUT + ".lock"
    if os.path.exists(lock) and (now_ts() - os.path.getmtime(lock)) < 3600:
        print(json.dumps({"skipped": "another run in progress"}, ensure_ascii=False))
        return 0                      # 一次跑可能几分钟（含拉档），不许慢批重入叠跑
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(lock, "w", encoding="utf-8") as f:
        f.write(now_iso())
    try:
        return _run_body(pol, today)
    finally:
        try:
            os.remove(lock)
        except OSError:
            pass


def _run_body(pol, today):
    sc = scan()
    log = {"ts": now_iso(), "attention": sc["attention"], "bench": None, "decide": None,
           "pulled": [], "stale_days": round(stale_days(), 1)}
    ap = pol.get("auto_pull") or {}
    # 先更新再实测：否则测的是旧版本，结论对不上上游。只拉同家族、够小的（默认 <=6GB）。
    if ap.get("enabled"):
        pulled_n = 0
        for row in sc["rows"]:
            if pulled_n >= int(ap.get("max_per_day") or 2):
                break
            # 只拉新增档：同 tag 上游重发只报告——拉到新版等于把旧版基线冲掉，A/B 就没了
            if row["state"] not in (ap.get("only_states") or ["NEW-TAG"]):
                continue
            if row["family"] not in (ap.get("only_same_family_as") or []):
                continue
            if (row.get("size_gb") or 0) > float(ap.get("max_size_gb") or 6.0):
                continue
            try:
                subprocess.run(["ollama", "pull", row["model"]], timeout=1800,
                               capture_output=True)
                log["pulled"].append(row["model"])
                pulled_n += 1
            except Exception:
                pass
    need_bench = bool(sc["attention"]) or bool(log["pulled"]) or \
        stale_days() > pol["thresholds"]["bench_stale_days"]
    if need_bench:
        # 只测会答话的档；embedding 档没有黄金集，单列不测
        emb = (pol["duties"].get("embedding") or {}).get("model")
        models = [d.get("model") for d in pol["duties"].values()
                  if d.get("model") and d.get("model") != emb]
        log["bench"] = bench(models)
        log["decide"] = decide()
    ledger({"ts": log["ts"], "attention": log["attention"],
            "benched": bool(log["bench"]), "pulled": log["pulled"],
            "suggest": [v for v in ((log["decide"] or {}).get("verdicts") or [])
                        if v.get("action") == "SUGGEST-SWAP"]})
    st2 = _read_state()
    st2["last_run_day"] = today
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(st2, f, ensure_ascii=False, indent=1)
    print(json.dumps(log, ensure_ascii=False)[:600])
    return 2 if sc["attention"] else 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("scan", "bench", "decide", "run", "status"))
    ap.add_argument("--models", default="")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--skip-quality", action="store_true")
    a = ap.parse_args(argv)

    if a.cmd == "scan":
        print(json.dumps(scan(), ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "bench":
        ms = [m.strip() for m in a.models.split(",") if m.strip()]
        print(json.dumps(bench(ms, a.n, a.skip_quality), ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "decide":
        print(json.dumps(decide(), ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "status":
        st = _read_state()
        print(json.dumps({"updated": st.get("updated"),
                          "attention": (st.get("scan") or {}).get("attention"),
                          "bench_ts": (st.get("bench") or {}).get("ts"),
                          "stale_days": round(stale_days(), 1),
                          "verdicts": (st.get("decide") or {}).get("verdicts")},
                         ensure_ascii=False, indent=1))
        return 0
    return run()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))