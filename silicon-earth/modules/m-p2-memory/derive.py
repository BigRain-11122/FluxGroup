# -*- coding: utf-8 -*-
"""
m-p2-memory · 记忆派生 v0.3

v0.3 修质量席指出的"位置编号"问题：
记忆 ID 不再按列表位置从头数，而是从种子里的最大编号往后接。
这样新增种子（拿到更大的显式 ID）不会让已有派生记忆全体重编号。

其余不变：memory.json = seed.json + events 的纯函数，可删可重建。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(DATA, "memory.json")
SEED = os.path.join(DATA, "seed.json")
EVENTS = os.path.join(ROOT, "modules", "m-w2-clock", "data", "events.jsonl")


def read_json(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write_json(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def mid_num(mid):
    try:
        return int(str(mid)[1:])
    except Exception:
        return 0


def ensure_seed():
    if os.path.exists(SEED):
        return read_json(SEED).get("memories", [])
    seeded = []
    if os.path.exists(OUT):
        seeded = [m for m in read_json(OUT).get("memories", []) if not m.get("event_id")]
    write_json(SEED, {"note": "种子记忆，不属于任何事件；派生记忆不得写入本文件", "memories": seeded})
    return seeded


def derive():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    seeded = ensure_seed()
    memories = [dict(m) for m in seeded]
    n = max([mid_num(m.get("id")) for m in seeded] or [0])
    bad = 0

    if os.path.exists(EVENTS):
        with open(EVENTS, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except Exception:
                    bad += 1
                    continue
                if not isinstance(ev, dict) or "type" not in ev:
                    bad += 1
                    continue
                etype = ev["type"]
                actors = ev.get("actors", [])
                if not actors:
                    continue

                if etype in ("build", "repair"):
                    rows = [(actors[0], "kept", "我做过这件事。", None)]
                elif etype == "help" and len(actors) >= 2:
                    rows = [(actors[1], "kept", "有人帮过我。", None)]
                elif etype == "teach" and len(actors) >= 2:
                    rows = [(actors[1], "given", "有人教过我一件事。", None)]
                elif etype == "blackout" and len(actors) >= 2:
                    rows = [(actors[0], "lost", "那一段被断电截断了。", actors[1])]
                else:
                    rows = []

                for person_id, kind, text, unrecognized in rows:
                    n += 1
                    memories.append({
                        "id": "M%04d" % n,
                        "person_id": person_id,
                        "day": ev["day"],
                        "kind": kind,
                        "text": text,
                        "event_id": ev["id"],
                        "unrecognized": unrecognized,
                    })

                for wid in ev.get("witnesses", []):
                    n += 1
                    memories.append({
                        "id": "M%04d" % n, "person_id": wid, "day": ev["day"],
                        "kind": "kept", "text": "那天我在场。",
                        "event_id": ev["id"], "unrecognized": None,
                    })

    write_json(OUT, {"version": "1.3", "memories": memories})
    lost = sum(1 for m in memories if m["kind"] == "lost")
    extra = f" · 跳过坏行 {bad}" if bad else ""
    print(f"记忆派生完成：{len(memories)} 条（种子 {len(seeded)} · 派生 {len(memories)-len(seeded)} · lost {lost}）{extra}")


if __name__ == "__main__":
    sys.exit(derive() or 0)
