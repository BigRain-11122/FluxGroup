#!/usr/bin/env python3
"""跨号撞车闸：同一篇稿子不许在短时间内出现在两个号上。

为什么要有这个闸：平台判搬运**不看你是不是同一个人**。
五个号发同一篇＝五个号一起降权。而且它比风控隐蔽——
风控会给你提示，搬运判定不会，只体现在后续每条内容的推荐量上。
`MULTI-ACCOUNT.md` 早就写了「7 天内 6-gram 重合 ≥60% 判重」，
但代码里只有评论用的 8 字重合原语（social_comment_gen.shared_run），
**没有任何东西检查「这篇是不是已经用别的号发过」**。

判据（k=6 连续字，沿用 MULTI-ACCOUNT.md 口径）：
  候选稿的 6-gram 有 ≥60% 出现在
    · 别的号近 14 天的发布里 → FAIL（搬运）
    · 同一个号近 30 天的发布里 → FAIL（自我重复，同样伤推荐）

刻意不做的事：
  · 判不了「换个说法重发」的语义搬运——那要模型。现在先守住字面这条。
  · 太短的文本（<8 个 6-gram）直接 SKIP，交给评论闸（SD/AC05 那条线）。

用法：
  cross_account_dup.py --check --account gzh-1 --in 稿子.md
  cross_account_dup.py --record --account gzh-1 --in 稿子.md --title "..." --url "..."
  cross_account_dup.py --list
  cross_account_dup.py --self-test
退出码：0 不撞车 / 1 撞车（或 record 被拒） / 4 自检失败
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REGISTRY = os.path.join(ROOT, "cph4", "fleet", "social", "ACCOUNTS-REGISTRY-v1.json")
LEDGER = os.path.join(ROOT, "cph4", "fleet", "social", "state", "PUBLISHED.jsonl")

K = 6
THRESH = 0.60
CROSS_DAYS = 14
SELF_DAYS = 30
MIN_GRAMS = 8      # 少于这么多个 6-gram 就判不了，直接 SKIP


def norm(text):
    """归一化：去代码块/链接/markdown 符号/空白。只留可比较的字。"""
    t = re.sub(r"```[\s\S]*?```", "", text or "")
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"[#>*`\-\[\]()（）「」『』" "''…·,，。、；;:：!！?？]", "", t)
    return re.sub(r"\s+", "", t)


def grams(text, k=K):
    t = norm(text)
    return {t[i:i + k] for i in range(len(t) - k + 1)} if len(t) >= k else set()


def containment(cand_grams, prior_grams):
    if not cand_grams:
        return 0.0
    return len(cand_grams & prior_grams) / len(cand_grams)


def longest_shared(cand, prior, ks=(40, 30, 20, 12, 9, 6)):
    """给作者看的最长重合片段（从长到短试，够用即停）。"""
    a, b = norm(cand), norm(prior)
    for k in ks:
        ga = {a[i:i + k] for i in range(len(a) - k + 1)} if len(a) >= k else set()
        gb = {b[i:i + k] for i in range(len(b) - k + 1)} if len(b) >= k else set()
        hit = ga & gb
        if hit:
            return k, sorted(hit, key=len, reverse=True)[0]
    return None, None


def load_registry():
    doc = json.load(open(REGISTRY, encoding="utf-8"))
    return {a["id"]: a for a in doc.get("accounts") or []}


def load_ledger():
    if not os.path.exists(LEDGER):
        return []
    rows = []
    for line in open(LEDGER, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:  # noqa: BLE001
            continue
    return rows


def check(account, text, ledger=None, now=None):
    """返回 (level, hits, stats)。level ∈ PASS/SKIP/FAIL。"""
    ledger = load_ledger() if ledger is None else ledger
    now = now or datetime.now()
    cg = grams(text)
    stats = {"account": account, "grams": len(cg), "compared": 0,
             "max_cross": 0.0, "max_self": 0.0}
    if len(cg) < MIN_GRAMS:
        stats["why"] = f"只有 {len(cg)} 个 6-gram，太短判不了（交给评论闸）"
        return "SKIP", [], stats

    hits = []
    for r in ledger:
        if r.get("account") == account and r.get("kind") == "shadow":
            continue
        try:
            ts = datetime.fromisoformat(r["ts"])
        except Exception:  # noqa: BLE001
            continue
        age_days = (now - ts).total_seconds() / 86400
        same = r.get("account") == account
        window = SELF_DAYS if same else CROSS_DAYS
        if age_days > window:
            continue
        stats["compared"] += 1
        c = containment(cg, grams(r.get("text", "")))
        if same:
            stats["max_self"] = max(stats["max_self"], c)
        else:
            stats["max_cross"] = max(stats["max_cross"], c)
        if c >= THRESH:
            k, frag = longest_shared(text, r.get("text", ""))
            hits.append({
                "account": r.get("account"), "platform": r.get("platform"),
                "ts": r.get("ts"), "age_days": round(age_days, 1),
                "containment": round(c, 3), "same_account": same,
                "title": (r.get("title") or "")[:40],
                "longest": f"{k} 字连续重合：{frag[:30]}" if k else "",
            })

    if hits:
        hits.sort(key=lambda x: -x["containment"])
        return "FAIL", hits, stats
    if stats["compared"] == 0:
        # 台账为空时的 PASS 是"没东西可比"，不是"不撞车"。必须显式标出来，
        # 否则就是"机制绿灯空转"的经典形态：闸天天绿，因为它根本没读数据。
        stats["empty"] = True
        return "PASS-EMPTY", [], stats
    return "PASS", [], stats


def record(account, text, title="", url="", kind="published", now=None, force=False,
           ledger=None):
    """写发布台账。撞车时不写（除非 force），避免台账本身被污染。"""
    ledger = load_ledger() if ledger is None else ledger
    lvl, hits, stats = check(account, text, ledger=ledger, now=now)
    if lvl == "FAIL" and not force:
        return False, {"level": "FAIL", "hits": hits, "stats": stats,
                       "why": "撞车，拒绝入账（确属有意重发再加 --force）"}
    row = {
        "ts": (now or datetime.now()).isoformat(timespec="seconds"),
        "account": account, "platform": None, "kind": kind,
        "title": title, "url": url,
        "sha": hashlib.sha1(norm(text).encode("utf-8")).hexdigest()[:16],
        "chars": len(norm(text)), "text": text[:20000],
    }
    try:
        row["platform"] = load_registry().get(account, {}).get("platform")
    except Exception:  # noqa: BLE001
        pass
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return True, {"level": lvl, "hits": hits, "stats": stats, "row": row}


# ---------------- 自检 ----------------
PRIOR_A = ("秦PLUS 和海豹06 差两万，我把两页配置表叠在一起看。" * 3
           + "根据两车官方配置表，多出来的第一项是后悬架，秦PLUS 用扭力梁，海豹06 用多连杆。"
           + "第二项是电池容量，海豹06 是 60.5 度，秦PLUS 是 48 度，按官网报价每度 600 元算差 7500 元。"
           + "剩下的四项加起来不到 6000 元，占差价的三成。" * 2)

PRIOR_B = ("享界 V8 的发布会上，L3 自动驾驶的表述又成了主角。" * 2
           + "判断一套座舱好不好，不看它堆了多少功能，看关掉一个功能要几步。"
           + "同样的关闭车道保持，有的车两步，有的车五步，指尖在屏幕上找了三圈。" * 2)


def _ledger_with(now):
    return [
        {"ts": (now - timedelta(days=3)).isoformat(timespec="seconds"),
         "account": "bili-1", "platform": "bilibili", "kind": "published",
         "title": "配置表叠着看", "text": PRIOR_A},
        {"ts": (now - timedelta(days=5)).isoformat(timespec="seconds"),
         "account": "gzh-1", "platform": "gzh", "kind": "published",
         "title": "关掉一个功能要几步", "text": PRIOR_B},
    ]


def self_test():
    fails = []
    now = datetime.now()
    L = _ledger_with(now)

    # 1 正控：全新主题必须 PASS
    new_doc = ("小鹏 G7 的中控屏把空调温度放在最上层，风量藏进二级菜单。" * 2
               + "从界面看能力，这种做法暴露的是产品对常用动作的排序判断。" * 2)
    lvl, hits, st = check("gzh-1", new_doc, ledger=L, now=now)
    if lvl != "PASS":
        fails.append(f"正控[全新主题] 被判 {lvl}: {hits[:1]}")

    # 2 负控：同一篇发到另一个号 → FAIL（跨号）
    lvl2, hits2, _ = check("gzh-1", PRIOR_A, ledger=L, now=now)
    if lvl2 != "FAIL":
        fails.append("负控[跨号搬运] 未判 FAIL")
    elif not any(not h["same_account"] for h in hits2):
        fails.append("负控[跨号搬运] 命中却归成同号")

    # 3 负控：换掉三成措辞仍要判红（60% 门槛的边界）
    parts = re.split(r"(?<=。)", PRIOR_A)
    rewritten = "".join(p if i % 3 else "这一句我完全重写了，换了个说法讲另外一件事。" 
                        for i, p in enumerate(parts))
    lvl3, hits3, st3 = check("bili-2", rewritten, ledger=L, now=now)
    if lvl3 != "FAIL":
        fails.append(f"负控[换三成措辞] 未判红（重合 {st3['max_cross']:.2f}）")

    # 4 正控：同选题但另起一稿必须 PASS
    same_topic = ("同一块屏，为什么有人点两下有人点五下。" * 2
                  + "我把这两条路径画在白板上，一共十一步，差的是层级不是功能。" * 2
                  + "真正的成本不在屏幕，在用户每次都要重新找一遍。" * 2)
    lvl4, hits4, st4 = check("gzh-1", same_topic, ledger=L, now=now)
    if lvl4 != "PASS":
        fails.append(f"正控[同题材另起一稿] 被误判（重合 {st4['max_cross']:.2f}）")

    # 5 负控：同号 30 天内自我重复 → FAIL
    lvl5, hits5, _ = check("gzh-1", PRIOR_B, ledger=L, now=now)
    if lvl5 != "FAIL" or not any(h["same_account"] for h in hits5):
        fails.append("负控[同号自我重复] 未判红或未归成同号")

    # 6 边界：太短必须 SKIP 而不是 PASS（假绿的经典形态）
    lvl6, _, _ = check("gzh-1", "这条屏真难用。", ledger=L, now=now)
    if lvl6 != "SKIP":
        fails.append(f"负控[太短] 应为 SKIP，实际 {lvl6}")

    # 7 过期不判：40 天前的稿子不该再拦（否则等于永久封稿）
    old = [{"ts": (now - timedelta(days=40)).isoformat(timespec="seconds"),
            "account": "bili-1", "platform": "bilibili", "kind": "published",
            "text": PRIOR_A}]
    lvl7, _, st7 = check("gzh-1", PRIOR_A, ledger=old, now=now)
    if lvl7 == "FAIL":
        fails.append("负控[超窗口] 40 天前的稿子仍在拦")
    elif not st7.get("empty"):
        fails.append("负控[超窗口] 超窗口后应落回「无可比对象」，实际仍在比对")

    # 8 record 撞车必须拒绝入账（台账不许被污染）
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        global LEDGER
        keep = LEDGER
        LEDGER = os.path.join(td, "PUBLISHED.jsonl")
        ok, info = record("gzh-1", PRIOR_A, ledger=L, now=now)
        if ok:
            fails.append("负控[record] 撞车稿被写入台账")
        ok2, _ = record("gzh-1", new_doc, ledger=L, now=now)
        if not ok2:
            fails.append("正控[record] 正常稿被拒绝")
        LEDGER = keep

    # 9 负控：空台账不许伪装成 PASS（"机制绿灯空转"的经典形态）
    lvl9, _, st9 = check("gzh-1", PRIOR_A, ledger=[], now=now)
    if lvl9 != "PASS-EMPTY" or not st9.get("empty"):
        fails.append(f"负控[空台账] 应返回 PASS-EMPTY，实际 {lvl9}")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print("SELF-TEST OK 9/9  (3 正控 + 5 负控含空台账 + record 拒绝污染)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--account")
    ap.add_argument("--in", dest="inp")
    ap.add_argument("--title", default="")
    ap.add_argument("--url", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    if a.list:
        rows = load_ledger()
        print(f"发布台账 {len(rows)} 条 · {LEDGER}")
        for r in rows[-15:]:
            print(f"  {r.get('ts')}  {r.get('account'):10} {r.get('platform') or '-':10} "
                  f"{(r.get('title') or '')[:38]}")
        return 0

    if not a.account:
        ap.print_help()
        return 1

    reg = load_registry()
    if a.account not in reg:
        print(f"未知账号 {a.account}；注册表里有：{', '.join(sorted(reg))}", file=sys.stderr)
        return 1

    if not a.inp:
        ap.print_help()
        return 1
    text = open(a.inp, encoding="utf-8").read()

    if a.record:
        ok, info = record(a.account, text, title=a.title, url=a.url, force=a.force)
        st = info["stats"]
        print(f"{'已入账' if ok else '拒绝入账'}  {a.account}  "
              f"6-gram {st['grams']} 个 / 比对 {st['compared']} 条")
        for h in info["hits"]:
            print(f"  FAIL 撞 {h['account']}({h['platform']}) {h['age_days']} 天前 "
                  f"重合 {h['containment']:.0%} · {h['longest']}")
        if not ok:
            print(info.get("why", ""), file=sys.stderr)
            return 1
        return 0

    lvl, hits, st = check(a.account, text)
    print(f"{lvl}  {a.account}  6-gram {st['grams']} 个 / 比对 {st['compared']} 条 "
          f"/ 跨号最高重合 {st['max_cross']:.0%} / 同号最高重合 {st['max_self']:.0%}")
    if st.get("why"):
        print(f"  {st['why']}")
    if st.get("empty"):
        print(f"  ⚠ 台账为空（{LEDGER}），这条 PASS 只是「没东西可比」，不代表不撞车。\n"
              f"    先跑 --record 把已发内容记进去，闸才开始有判断力。")
    for h in hits:
        print(f"  FAIL 撞 {h['account']}({h['platform']}) {h['age_days']} 天前 "
              f"重合 {h['containment']:.0%} · {h['longest']}")
        if h["title"]:
            print(f"       已发标题：{h['title']}")
    if lvl == "FAIL":
        print("\n结论：这篇不能发。要么换角度重写，要么换号首发。", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
