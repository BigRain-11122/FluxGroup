# -*- coding: utf-8 -*-
"""lora_scout.py — 开源社区现成角色/面孔 LoRA 的选品与下载（反烂大街）。

为什么不是直接按 "Most Downloaded" 排序：热门榜=所有人都在用同一批脸，
出来的片子必然撞脸，也必然是一眼 AI 网红脸。本工具按「中段热度 + 质量佐证 +
具体性 + 新鲜度」打分，并把通用美女类模型直接拉黑。

用法：
  python Tools/lora_scout.py search --query portrait --base "Flux.1 D" --limit 100 --out cand.json
  python Tools/lora_scout.py search --queries "film portrait,1990s,vintage portrait" --out cand.json
  python Tools/lora_scout.py fetch --version-id 123456 --out D:\\lora [--token xxx]
  python Tools/lora_scout.py selftest

判据来源 = cph4/fleet/mv-album-001-jay/READYMADE-LORA-LIB-v1.md
退出码：0 成功 / 1 无候选或下载失败 / 2 参数错
"""
import argparse
import hashlib
import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request

API = "https://civitai.com/api/v1/models"
VER = "https://civitai.com/api/v1/model-versions"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# 烂大街 / 通用脸黑名单（命中即剔除，不做加权）
GENERIC = [
    "asian beauty", "korean beauty", "beautiful woman", "perfect face", "beauty portrait",
    "realistic girl", "real girl", "kpop", "idol face", "all in one", "face helper",
    "generic", "asian girl", "chinese beauty", "girl next door", "pretty face",
    "美女", "网红脸", "通用脸",
]
# 具体性加分词（年代/媒介/编辑风格=有个性的脸）
SPECIFIC = [
    "1980", "1990", "2000", "retro", "vintage", "film", "analog", "kodak", "portra",
    "polaroid", "editorial", "documentary", "noir", "period", "grunge", "cinema",
    "35mm", "medium format", "kodachrome", "photobook",
]
# 名像人名（两三个词、首字母大写、无空格关键词）的正则
NAME_LIKE = re.compile(r"^[A-Z][a-z]{2,}(\s[A-Z][a-z]{2,}){1,2}$")

DL_LO, DL_HI = 200, 20000      # 热度中段：太低没验证，太高烂大街


def _get(url, token=None, raw=False):
    h = dict(UA)
    if token:
        h["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read() if raw else json.load(r)


def search_one(query, base, limit, tag=None):
    q = {"limit": limit, "types": "LORA", "sort": "Newest"}
    if query:
        q["query"] = query
    if tag:
        q["tag"] = tag
    if base:
        q["baseModels"] = base
    url = API + "?" + urllib.parse.urlencode(q)
    try:
        return _get(url).get("items", [])
    except Exception as e:  # 网络/限流不致命，继续下一组
        print(f"[warn] 查询失败 {query!r}: {e}", file=sys.stderr)
        return []


def version_of(model):
    vs = model.get("modelVersions") or []
    return vs[0] if vs else {}


def pick_file(ver):
    for f in ver.get("files") or []:
        n = (f.get("name") or "").lower()
        if n.endswith(".safetensors"):
            return f
    return None


def is_generic(name, tags):
    blob = (name + " " + " ".join(tags or [])).lower()
    return any(g in blob for g in GENERIC)


def score(model):
    """反烂大街评分 0-100，返回 (score, reasons)。"""
    st = model.get("stats") or {}
    dl = int(st.get("downloadCount") or 0)
    up = int(st.get("thumbsUpCount") or 0)
    tags = [t.lower() for t in (model.get("tags") or [])]
    name = model.get("name") or ""
    reasons, s = [], 0.0

    # 1) 热度中段（30 分）：log 距离区间中心
    if dl <= 0:
        return 0.0, ["无下载数据"]
    lo, hi = math.log10(DL_LO), math.log10(DL_HI)
    x = math.log10(dl)
    if lo <= x <= hi:
        center = (lo + hi) / 2
        s += 30 * max(0.0, 1 - abs(x - center) / ((hi - lo) / 2))
        reasons.append(f"热度中段({dl})")
    elif x > hi:
        s += max(0.0, 12 - (x - hi) * 15)
        reasons.append(f"过热(-{dl})")
    else:
        s += 6
        reasons.append(f"冷门待验({dl})")

    # 2) 质量佐证（25 分）：点赞/下载比 与 绝对赞数
    ratio = up / dl if dl else 0
    s += min(15.0, ratio * 1000)              # 1.5% 拿满
    s += min(10.0, up / 20.0)                  # 200 赞拿满
    reasons.append(f"赞/下={ratio:.2%} 赞={up}")

    # 3) 具体性（25 分）
    blob = (name + " " + " ".join(tags)).lower()
    hit = [w for w in SPECIFIC if w in blob]
    if hit:
        s += min(15.0, 5.0 * len(hit))
        reasons.append("具体性+" + ",".join(sorted(set(hit))[:3]))
    if NAME_LIKE.match(name.strip()):
        s += 10
        reasons.append("人设名")

    # 4) 新鲜度（10 分）
    pub = (version_of(model).get("publishedAt") or "")[:10]
    if pub >= "2025-01-01":
        s += 10
        reasons.append("新")
    elif pub >= "2024-06-01":
        s += 5

    # 5) 惩罚
    if "celebrity" in " ".join(tags):
        s -= 8
        reasons.append("明星标签(-8)")
    if any(w in (name.lower()) for w in ("anime", "cartoon", "3d", "chibi")):
        s -= 25
        reasons.append("非实拍(-25)")

    return round(max(0.0, min(100.0, s)), 1), reasons


def collect(queries, base, limit, tag=None):
    seen, models = set(), []
    for q in queries:
        for m in search_one(q.strip(), base, limit, tag):
            if m.get("id") in seen:
                continue
            seen.add(m.get("id"))
            models.append(m)
    return models


def norm(m):
    ver = version_of(m)
    f = pick_file(ver)
    tags = m.get("tags") or []
    sc, why = score(m)
    return {
        "id": m.get("id"),
        "name": m.get("name"),
        "creator": (m.get("creator") or {}).get("username"),
        "type": m.get("type"),
        "baseModels": m.get("baseModels"),
        "tags": tags,
        "stats": {k: (m.get("stats") or {}).get(k) for k in ("downloadCount", "thumbsUpCount", "commentCount")},
        "allowCommercialUse": m.get("allowCommercialUse"),
        "allowNoCredit": m.get("allowNoCredit"),
        "generic": is_generic(m.get("name") or "", tags),
        "score": sc,
        "why": why,
        "versionId": ver.get("id"),
        "versionName": ver.get("name"),
        "baseModel": ver.get("baseModel"),
        "trainedWords": ver.get("trainedWords"),
        "publishedAt": (ver.get("publishedAt") or "")[:10],
        "file": (f or {}).get("name"),
        "sizeMB": round(((f or {}).get("sizeKB") or 0) / 1024.0, 1),
        "downloadUrl": ver.get("downloadUrl"),
        "page": f"https://civitai.com/models/{m.get('id')}",
    }


def cmd_search(a):
    queries = a.queries.split(",") if a.queries else [a.query or "portrait"]
    models = collect(queries, a.base, a.limit, a.tag)
    if not models:
        print("[FAIL] 无候选（检查网络或换关键词）")
        return 1
    rows = [r for r in (norm(m) for m in models) if not r["generic"] and r["file"]]
    rows.sort(key=lambda r: r["score"], reverse=True)
    keep = [r for r in rows if r["score"] >= a.min_score][:a.top]
    print(f"抓到 {len(models)} · 剔通用 {len(models) - len(rows)} · 过线 {len(keep)}\n")
    print(f"{'分数':<6}{'名称':<38}{'下载':>8}{'赞':>6}  {'基准':<12}{'大小MB':>8}  理由")
    for r in keep:
        print(f"{r['score']:<6}{r['name'][:36]:<38}{r['stats']['downloadCount']:>8}"
              f"{r['stats']['thumbsUpCount']:>6}  {str(r['baseModel'])[:11]:<12}{r['sizeMB']:>8}  "
              f"{' | '.join(r['why'][:2])}")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump({"queries": queries, "base": a.base, "items": keep}, f, ensure_ascii=False, indent=1)
        print(f"\n候选清单 → {a.out}")
    return 0


def _is_safetensors(data):
    """safetensors = 8 字节小端头长度 + JSON 头（以 { 开头）。挡住登录页/错误 JSON。"""
    if len(data) < 1024:
        return False
    if data[8:9] != b"{":
        return False
    return True


def cmd_fetch(a):
    token = a.token or os.environ.get("CIVITAI_TOKEN")
    info = _get(f"{VER}/{a.version_id}", token=token)
    url = info.get("downloadUrl")
    name = None
    for f in info.get("files") or []:
        if (f.get("name") or "").lower().endswith(".safetensors"):
            name = f["name"]
            break
    if not url or not name:
        print("[FAIL] 该版本无公开直链（可能需登录/付费）")
        return 1
    os.makedirs(a.out, exist_ok=True)
    dst = os.path.join(a.out, name)
    data = _get(url, token=token, raw=True)
    if not _is_safetensors(data):
        head = data[:160].decode("utf-8", "replace").replace("\n", " ")
        print(f"[FAIL] 拿到的不是权重文件（{len(data)} 字节）——多为需登录/受限。"
              f"\n       前 160 字节: {head[:160]}"
              f"\n       解决: 设环境变量 CIVITAI_TOKEN 或用 --token")
        return 1
    with open(dst, "wb") as f:
        f.write(data)
    h = hashlib.sha256(data).hexdigest()[:16]
    print(f"已下载 → {dst}（{len(data)/1048576:.1f} MB, sha256:{h}）")
    return 0


def selftest():
    """评分必须能把「中段+具体」排在「超热+通用」前面。"""
    def mk(name, dl, up, tags, pub="2025-06-01"):
        return {"name": name, "tags": tags, "stats": {"downloadCount": dl, "thumbsUpCount": up},
                "modelVersions": [{"publishedAt": pub + "T00:00:00Z", "id": 1}]}
    hot = mk("Asian Beauty Realistic Girl", 900000, 20000, ["asian", "realistic"])
    mid = mk("1990s Film Portrait", 3000, 120, ["film", "portrait", "vintage", "90s"])
    cold = mk("Some Face", 20, 1, [])
    sh, _ = score(hot)
    sm, _ = score(mid)
    sc, _ = score(cold)
    fails = []
    if not sm > sh:
        fails.append(f"中段具体款 {sm} 未超过超热通用款 {sh}")
    if not sm > sc:
        fails.append(f"中段具体款 {sm} 未超过无验证冷款 {sc}")
    if not is_generic("Asian Beauty Realistic Girl", []):
        fails.append("通用名未被打黑")
    for f in fails:
        print("[FAIL]", f)
    if fails:
        return 1
    print(f"[PASS] 通用热门={sh} 中段具体={sm} 冷门={sc}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="开源社区 LoRA 选品与下载（反烂大街）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search"); s.add_argument("--query"); s.add_argument("--queries")
    s.add_argument("--base", default="Flux.1 D"); s.add_argument("--limit", type=int, default=100)
    s.add_argument("--tag"); s.add_argument("--top", type=int, default=25)
    s.add_argument("--min-score", type=float, default=45)
    s.add_argument("--out")

    s = sub.add_parser("fetch"); s.add_argument("--version-id", required=True)
    s.add_argument("--out", required=True); s.add_argument("--token")

    sub.add_parser("selftest")
    a = ap.parse_args(argv)
    if a.cmd == "selftest":
        return selftest()
    if a.cmd == "search":
        return cmd_search(a)
    return cmd_fetch(a)


if __name__ == "__main__":
    sys.exit(main())
