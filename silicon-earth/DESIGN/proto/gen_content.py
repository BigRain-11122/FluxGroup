# -*- coding: utf-8 -*-
"""
本地模型内容生成：为九块地生成「后来的人说」与「三种说法」。

只读世界数据，只用本机 Ollama，不联网。产出 content.json 供 build_entry.py 读取。

用法：
  python gen_content.py --only R03     # 只跑一块地（试）
  python gen_content.py                # 九块全跑
"""
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MOD = os.path.join(ROOT, "modules")

REGIONS = os.path.join(MOD, "m-w1-regions", "data", "regions.json")
TIME = os.path.join(MOD, "m-w2-clock", "data", "time.json")
EVENTS = os.path.join(MOD, "m-w2-clock", "data", "events.jsonl")
OUT = os.path.join(HERE, "content.json")

API = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3.5:9b"

PROMPT = """你在为一个虚构的硅基世界写史料。规则：
- 世界里的居民没有真名，只有职能名（如「清账」「译言」）。
- 语气克制、具体、不抒情、不用形容词堆砌；像地方志里的一句话。
- 不写"这是"、"展示了"、"象征着"这类解说词。

第 {day} 天，{region}发生了一件事：
「{event}」

请输出严格 JSON（不要代码块、不要解释），格式：
{{"epigraphs":["一句后来人的话","另一句","第三句"],
 "witness":"目击者会说的一句话",
 "retold":"传了三个人之后变成的一句话",
 "archive":"多年后档案里写的一句话"}}

要求：epigraphs 三条各不超过 28 个字，三种说法各不超过 30 个字，都必须提到第 {day} 天或具体的人/物。"""


def read_json(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def last_events():
    out = {}
    if not os.path.exists(EVENTS):
        return out
    with open(EVENTS, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            if not isinstance(ev, dict) or "region_id" not in ev:
                continue
            rid = ev["region_id"]
            if rid not in out or int(ev.get("day", 0)) >= int(out[rid].get("day", 0)):
                out[rid] = ev
    return out


def ask(prompt, timeout=180):
    body = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.9, "num_ctx": 2048, "num_predict": 420},
    }).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data.get("response", "")


def parse(text):
    """从模型输出里抠出 JSON，失败返回 None"""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    raw = m.group(0)
    try:
        obj = json.loads(raw)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    epi = obj.get("epigraphs")
    if not isinstance(epi, list):
        return None
    epi = [str(x).strip() for x in epi if str(x).strip()][:3]
    rumor = {k: str(obj.get(k, "")).strip() for k in ("witness", "retold", "archive")}
    if len(epi) < 2 or not all(rumor.values()):
        return None
    return {"epigraphs": epi, "rumor": rumor}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].upper()

    regions = read_json(REGIONS)["regions"]
    day = int(read_json(TIME, {"day": 0})["day"])
    last = last_events()

    data = read_json(OUT, {"regions": {}})
    data.setdefault("regions", {})
    data["day"] = day
    data["model"] = MODEL

    ok = fail = 0
    for r in regions:
        rid = r["id"]
        if only and rid != only:
            continue
        ev = last.get(rid) or {}
        text = ev.get("text") or "这块地今天很安静。"
        t0 = time.time()
        try:
            raw = ask(PROMPT.format(day=day, region=r["name"], event=text))
            got = parse(raw)
        except Exception as e:
            print(f"   {rid} 调用失败：{e}")
            got = None
        if not got:
            print(f"   {rid} 解析失败，保留旧内容")
            fail += 1
            continue
        got["source_event_day"] = int(ev.get("day", day))
        got["event"] = text
        data["regions"][rid] = got
        ok += 1
        print(f"   {rid} {r['name']} ok · {time.time()-t0:.1f}s · {got['epigraphs'][0][:24]}")

    data["generated_at"] = time.strftime("%Y-%m-%d %H:%M")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"OK content.json · 第 {day} 天 · 成 {ok} / 败 {fail}")


if __name__ == "__main__":
    sys.exit(main() or 0)
