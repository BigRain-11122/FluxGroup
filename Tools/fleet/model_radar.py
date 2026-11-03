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


# ---- fleet: per-node policy / idle gate / receipt ---------------------------------
# CEO 2026-11-03：机队每台机空闲时都要做同样的事——搜最新模型、适配、实测，
# 测不过就不换。判定阈值只留 policy 一处（accept_upgrade），各机只差"能装多大"。
def detect_node():
    n = (os.environ.get("FLUX_NODE") or "").strip()
    if n:
        return n
    import socket
    try:
        h = socket.gethostname().lower()
    except Exception:
        return ""
    for k in ("bm-a", "bm-b", "bm-c", "bm-d", "bm-m"):
        if k in h:
            return k
    return h


def node_cfg(pol, node):
    """把 nodes[<node>] 叠加到策略上；未声明的机沿用全局段。

    不猜机器上装了什么：未声明的机由 local_models() 实测，缺基线就报 NEED-BASELINE。
    """
    nodes = pol.get("nodes") or {}
    nd = nodes.get(node) or {}
    out = dict(pol)
    for k in ("duties", "tracked_families", "auto_pull", "accept_upgrade", "thresholds",
              "golden_set", "idle"):
        if k in nd:
            out[k] = nd[k]
    out["node"] = node
    out["discover"] = bool(nd.get("discover", pol.get("discover", True)))
    out["auto_baseline"] = bool(nd.get("auto_baseline", pol.get("auto_baseline", False)))
    return out


def _win_avail_gb():
    """Windows 可用物理内存（mem_gate 只有 vm_stat，跨机不能直接用）。"""
    import ctypes

    class MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

    m = MS()
    m.dwLength = ctypes.sizeof(MS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return round(m.ullAvailPhys / 1e9, 1)


def avail_gb():
    if sys.platform == "win32":
        try:
            return _win_avail_gb()
        except Exception:
            return None
    try:
        sys.path.insert(0, HERE)
        import mem_gate
        return mem_gate.available_gb()
    except Exception:
        return None


def queue_busy(root, node):
    """本机是否有在执行的生产卡（发卡不抢占生产，这是唯一权威的忙闲信号）。"""
    p = os.path.join(root, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("state") != "RUNNING" or node not in (r.get("nodes") or []):
                    continue
                # 自己在跑时不能把自己判成"本机忙"（否则每张雷达卡都 SKIPPED-IDLE）
                if "model_radar" in str(r.get("cmd") or ""):
                    continue
                return r.get("id")
    except Exception:
        pass
    return None


def busy_why(cfg):
    """返回阻塞原因或 None。闲 = 没有在跑的本机卡 + 不在 CEO 用机时段 + 内存够。"""
    idle = cfg.get("idle") or {}
    q = queue_busy(ROOT, cfg.get("node") or "")
    if q and idle.get("queue_blocks", True):
        return "queue-running:%s" % q
    win = idle.get("skip_weekday_hours")
    if win:
        import datetime as _dt
        now = _dt.datetime.now()
        if now.weekday() < 5 and int(win[0]) <= now.hour < int(win[1]):
            return "workday-window:%02d-%02d" % (int(win[0]), int(win[1]))
    floor = float(idle.get("min_free_gb") or 0)
    av = avail_gb()
    if floor and av is not None and av < floor:
        return "free-mem:%.1fGB<%.1fGB" % (av, floor)
    return None


def receipt_path(node, out_path=""):
    if out_path:
        return out_path if os.path.isabs(out_path) else os.path.join(ROOT, out_path)
    if not node:
        return ""
    return os.path.join(ROOT, "cph4", "fleet", "queue-receipts",
                        "model-radar-%s-%s.json" % (node, time.strftime("%Y%m%d")))


def apply_swap(node, model, why):
    """把建议落成现行档：只改 policy 里该机的 resident，并留回滚记录。

    建议不自动生效曾是纪律；CEO 2026-11-03 改为「测得好就换，测不好不换」——
    所以自动落档，但必须同时写入旧档与回滚命令，任何一次换档都可一步退回。
    """
    pol = load_policy()
    nodes = pol.setdefault("nodes", {})
    nd = nodes.setdefault(node, {})
    duties = nd.setdefault("duties", json.loads(json.dumps(pol.get("duties") or {})))
    old = (duties.get("resident") or {}).get("model")
    if not old or old == model:
        return {"applied": False, "why": "no-change"}
    duties.setdefault("resident", {})["model"] = model
    duties["resident"]["changed_at"] = now_iso()
    duties["resident"]["changed_why"] = why
    duties["resident"]["previous"] = old
    with open(POLICY, "w", encoding="utf-8") as f:
        json.dump(pol, f, ensure_ascii=False, indent=1)
    return {"applied": True, "from": old, "to": model,
            "rollback": "set nodes.%s.duties.resident.model=%s" % (node, old)}


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


def discover_families(limit=8):
    """搜上游最新模型家族（CEO：闲时去搜最新的大模型）。

    只作候选提示，不据此换档：页面结构变了就返回空，宁可不报也不造假候选。
    """
    for url in ("https://ollama.com/library?sort=newest", "https://ollama.com/library"):
        try:
            html = http_text(url)
        except Exception:
            continue
        fams = []
        i = 0
        while len(fams) < limit:
            i = html.find('href="/library/', i)
            if i < 0:
                break
            j = i + len('href="/library/')
            k = j
            while k < len(html) and (html[k].isalnum() or html[k] in ".-_"):
                k += 1
            name = html[j:k]
            if name and "/" not in name and name not in fams:
                fams.append(name)
            i = k
        if fams:
            return fams
    return []


def scan(pol=None):
    pol = pol or load_policy()
    loc = local_models()
    ap = pol.get("auto_pull") or {}
    size_cap = float(ap.get("max_size_gb") or 6.0)
    # 下限同样必要：0.6B/0.8B 这类档永远不可能顶替 4B 的职责，全报出来只会把
    # 真正的候选淹没（实测首跑 attention 8 条里 4 条是小档噪声）。
    size_floor = float(ap.get("min_size_gb") or 1.5)
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
        seen_dg = set(loc[n]["digest"] for n in loc)
        new = []
        for tag in remote_tags(family):
            if tag in have:
                continue
            rdig, rsize = remote_manifest(family, tag)
            if rsize is None or rsize > size_cap or rsize < size_floor:
                continue
            # 同内容改名（latest→8b、v1.5→latest 这类别名）不算新档（含本次已列出的候选）
            dg = rdig.split(":")[-1][:16] if rdig else None
            if dg and dg in seen_dg:
                continue
            if dg:
                seen_dg.add(dg)
            new.append({"model": "%s:%s" % (family, tag), "family": family, "tag": tag,
                        "local_digest": None,
                        "remote_digest": (rdig.split(":")[-1][:16] if rdig else None),
                        "size_gb": rsize, "state": "NEW-TAG"})
        rows.extend(new[:4])                       # 每家族最多 4 个候选，按页面顺序
    # 上游最新家族：只报到，不自动拉（可能是完全不同的任务面，混装会占盘占内存）
    discovered = []
    if pol.get("discover"):
        known = set(f.split(":")[0] for f in loc) | set(pol.get("tracked_families") or [])
        for fam in discover_families():
            if fam in known:
                continue
            for tag in remote_tags(fam)[:2]:
                rdig, rsize = remote_manifest(fam, tag)
                if rsize is None or rsize > size_cap or rsize < size_floor:
                    continue
                dg = (rdig.split(":")[-1][:16] if rdig else None)
                # latest 与具体 tag 常常同 digest，去重否则一个家族占两条
                if any(x.get("remote_digest") == dg for x in discovered):
                    continue
                discovered.append({"model": "%s:%s" % (fam, tag), "family": fam,
                                   "size_gb": rsize, "state": "NEW-FAMILY",
                                   "remote_digest": dg})
            if len(discovered) >= 6:
                break
    out = {"ts": now_iso(), "node": pol.get("node") or "", "installed": len(loc),
           "engine": ("up" if loc else "ollama-unreachable"), "rows": rows,
           "discovered": discovered,
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
    """容量判据只留一处：Mac 复用 mem_gate.decide；Windows 用可用物理内存 - 2GB 余量。"""
    if sys.platform == "win32":
        av = avail_gb()
        if av is None:
            return False, {"verdict": "UNKNOWN", "why": "avail_gb unavailable"}
        return (av - 2.0) >= float(need_gb or 0), {"avail_gb": av, "need_gb": need_gb,
                                                   "verdict": "OK" if (av - 2.0) >= float(need_gb or 0) else "DOWNGRADE"}
    try:
        sys.path.insert(0, HERE)
        import mem_gate
        d = mem_gate.decide(need_gb)
        return d.get("verdict") == "OK", d
    except Exception as e:
        return False, {"error": str(e)[:80]}


def bench(models, runs=3, skip_quality=False, pol=None):
    pol = pol or load_policy()
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
def decide(pol=None):
    pol = pol or load_policy()
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
def run(node="", idle_only=False, out_path="", apply=False, force=False):
    node = node or detect_node()
    pol = node_cfg(load_policy(), node)
    st = _read_state()
    today = time.strftime("%Y-%m-%d")
    if force is False and ("--force" in sys.argv):
        force = True
    if (st.get("last_run_day") == today) and not force:
        _write_receipt(node, out_path, {"ts": now_iso(), "node": node, "verdict": "SKIPPED",
                                        "why": "already ran today", "day": today})
        print(json.dumps({"skipped": "already ran today", "day": today}, ensure_ascii=False))
        return 0
    if idle_only:
        why = busy_why(pol)
        if why:
            # 不是失败：机器在生产，雷达让路；留回执说明"为什么今天没跑"
            _write_receipt(node, out_path, {"ts": now_iso(), "node": node, "verdict": "SKIPPED-IDLE",
                                            "why": why})
            print(json.dumps({"skipped_idle": why, "node": node}, ensure_ascii=False))
            return 0
    lock = OUT + ".lock"
    if os.path.exists(lock) and (now_ts() - os.path.getmtime(lock)) < 3600:
        print(json.dumps({"skipped": "another run in progress"}, ensure_ascii=False))
        return 0                      # 一次跑可能几分钟（含拉档），不许慢批重入叠跑
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(lock, "w", encoding="utf-8") as f:
        f.write(now_iso())
    try:
        return _run_body(pol, today, node, out_path, apply)
    finally:
        try:
            os.remove(lock)
        except OSError:
            pass


def _run_body(pol, today, node="", out_path="", apply=False):
    sc = scan(pol)
    log = {"ts": now_iso(), "node": node, "engine": sc.get("engine"),
           "attention": sc["attention"], "discovered": sc.get("discovered"),
           "bench": None, "decide": None, "applied": None, "skipped": [],
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
        # 只测会答话的档；embedding 档没有黄金集，单列不测。
        # 还要只测本机真装了的档——跨机策略里别的机的档在这里没权重，测了只会刷屏假红。
        installed = set(local_models())
        emb = (pol["duties"].get("embedding") or {}).get("model")
        # 未声明基线的工作机：以本机实际装着的最大对话模型为基线（不猜外部型号）。
        res = pol["duties"].get("resident") or {}
        if (res.get("model") not in installed) and pol.get("auto_baseline"):
            loc = local_models()
            cands = [n for n in loc if n != emb and "embed" not in n]
            if cands:
                res["model"] = max(cands, key=lambda n: loc[n].get("size_gb") or 0)
                pol["duties"]["resident"] = res
                log["baseline_resolved"] = res["model"]
        models = []
        for d in pol["duties"].values():
            m = d.get("model")
            if not m or m == emb:
                continue
            if m in installed:
                models.append(m)
            else:
                log["skipped"].append("not-installed:%s" % m)
        if models:
            log["bench"] = bench(models, pol=pol)
            log["decide"] = decide(pol)
        else:
            log["decide"] = {"verdicts": [{"action": "NEED-BASELINE",
                                           "why": "本机没有任何策略声明的模型，先把基线装上或声明 nodes.<node>.duties"}]}
    # 换档：只认 SUGGEST-SWAP，且必须是本机已装、实测过的那一档。测不过一律不动。
    if apply and (log.get("decide") or {}).get("verdicts"):
        for v in log["decide"]["verdicts"]:
            if v.get("action") == "SUGGEST-SWAP" and v.get("model") in set(local_models()):
                log["applied"] = apply_swap(node, v["model"], v.get("why") or "")
                break
        if not log.get("applied"):
            log["applied"] = {"applied": False, "why": "no candidate passed the two-path rule"}
    ledger({"ts": log["ts"], "node": node, "attention": log["attention"],
            "benched": bool(log["bench"]), "pulled": log["pulled"],
            "applied": log.get("applied"),
            "suggest": [v for v in ((log["decide"] or {}).get("verdicts") or [])
                        if v.get("action") == "SUGGEST-SWAP"]})
    st2 = _read_state()
    st2["last_run_day"] = today
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(st2, f, ensure_ascii=False, indent=1)
    _write_receipt(node, out_path, {
        "ts": log["ts"], "node": node, "verdict": "OK",
        "engine": sc.get("engine"), "installed": sc.get("installed"),
        "attention": log["attention"], "discovered": log.get("discovered"),
        "skipped": log["skipped"], "pulled": log["pulled"],
        "baseline": (log.get("decide") or {}).get("baseline"),
        "verdicts": (log.get("decide") or {}).get("verdicts"),
        "applied": log.get("applied"),
        "rule": "质量更高且速度>=现役90%，或质量持平且速度>=105%；质量更低一律不换",
    })
    print(json.dumps(log, ensure_ascii=False)[:600])
    return 2 if sc["attention"] else 0


def _write_receipt(node, out_path, body):
    """回执必须落 git 受控目录，远端才可验证（state/ 是 gitignore）。"""
    p = receipt_path(node, out_path)
    if not p:
        return
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(body, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("scan", "bench", "decide", "run", "status"))
    ap.add_argument("--models", default="")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--skip-quality", action="store_true")
    ap.add_argument("--node", default="", help="机名；缺省按 FLUX_NODE/主机名判")
    ap.add_argument("--idle-only", action="store_true", help="本机有生产卡/用机时段/内存不足则让路")
    ap.add_argument("--out", default="", help="回执路径；缺省 queue-receipts/model-radar-<node>-<day>.json")
    ap.add_argument("--apply", action="store_true", help="实测通过两条判据才自动换档（留回滚）")
    a = ap.parse_args(argv)
    node = a.node or detect_node()
    pol = node_cfg(load_policy(), node)

    if a.cmd == "scan":
        print(json.dumps(scan(pol), ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "bench":
        ms = [m.strip() for m in a.models.split(",") if m.strip()]
        print(json.dumps(bench(ms, a.n, a.skip_quality, pol=pol), ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "decide":
        print(json.dumps(decide(pol), ensure_ascii=False, indent=1))
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
    return run(node=node, idle_only=a.idle_only, out_path=a.out,
               apply=a.apply, force=("--force" in argv))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))