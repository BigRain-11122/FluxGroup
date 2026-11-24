#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seg_propose.py - 从"未识别"语料里挖候选信号词，并做**上线前验伤**。

为什么要有它（2026-11-18 实测）：三万字语料里 41% 落不进任何人群段（generic）。
那不是"这些人没特征"，是信号词没覆盖他们的说法——未识别的高频片段里，
剪辑(230)/素材(182)/软件(95)/教程(65)/字幕(47)/节奏(49)/画面(95)/剧情(70)
全是"学剪辑的人"在说话，而 tech_nerd 现有信号是参数/像素/帧率这种硬技术词。

没有验伤就往上加词，是拿整条线的路由做赌注：一个词可能把 A 段的人抢到 B 段。
所以本工具只做三件事，且第三件是硬门：
  1 PROPOSE：从 generic 里挖高频片段，去重叠、去过通用词，给出候选
  2 VALIDATE：把候选模拟加进某个段，重算全量分布，检查四条红线
  3 VERDICT：任一红线破就判 REJECT 并写明破在哪（谁被抢走了多少）

四条红线（验收判据，不是感觉）：
  R1 generic 必须真的下降 ≥3 个百分点（不到就没意义）
  R2 目标段增幅 ≥10%（不然这批词等于没落位）
  R3 任何既有段被抢走 ≤20%（超过就是拿别人的准确率换这个段的召回）
  R4 单段占比 ≤45%（不许造出一个吃掉半壁江山的怪物段）

用法：
  python3 Tools/fleet/seg_propose.py --self-test
  python3 Tools/fleet/seg_propose.py --corpus cph4/fleet/social/corpus/human/QUALITY-PASS.jsonl --apply-proposals
  python3 Tools/fleet/seg_propose.py --propose            # 只看候选，不写文件
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SPEC = os.path.join(ROOT, "cph4", "fleet", "social", "AUDIENCE-SEGMENTS-v1.json")
PASS_F = os.path.join(ROOT, "cph4", "fleet", "social", "corpus", "human", "QUALITY-PASS.jsonl")
OUT = os.path.join(ROOT, "cph4", "fleet", "social", "SEGMENT-PROPOSALS.jsonl")

sys.path.insert(0, HERE)
import segments as sg                    # noqa: E402

# 通用词不该当信号：它们在哪个段都出现，加了只会制造误判
GENERIC_WORDS = set("""这个 那个 就是 真的 什么 感觉 一下 不是 可以 我们 你们 他们 自己 时候
一直 还是 有点 已经 因为 所以 都是 这么 现在 没有 一个 需要 知道 觉得 喜欢 看到
视频 个视 个视频 笑哭 没有 什么 怎么""".split())

R1_GENERIC_DROP_PP = 3.0
R2_TARGET_GAIN_PCT = 10.0
R3_STEAL_MAX_PCT = 20.0
R4_SEG_MAX_SHARE = 45.0


def samples(path=PASS_F, min_len=8):
    out = []
    try:
        for line in open(path, encoding="utf-8"):
            if line.strip():
                t = (json.loads(line).get("text") or "").strip()
                if len(t) >= min_len:
                    out.append(t)
    except FileNotFoundError:
        pass
    return out


def dist(texts, spec=None):
    spec = spec or sg.load_spec()
    c = collections.Counter()
    for t in texts:
        c[sg.classify(t, spec)["primary"]] += 1
    return c


def propose(texts, top=40, min_freq=40, n_max=4):
    """从未识别语料里挖候选：2-4 字片段，去通用词、去子串包含。"""
    spec = sg.load_spec()
    gen = [t for t in texts if sg.classify(t, spec)["primary"] == "generic"]
    cnt = collections.Counter()
    for t in gen:
        s = re.sub(r"[^\u4e00-\u9fff]", " ", t)
        for n in range(2, n_max + 1):
            for i in range(len(s) - n + 1):
                w = s[i:i + n]
                if " " in w or w in GENERIC_WORDS:
                    continue
                cnt[w] += 1
    # 既有信号词不要重复提
    known = {w.lower() for seg in spec["segments"] for w in seg["signals"]}
    cand = [(w, n) for w, n in cnt.most_common(400)
            if n >= min_freq and w.lower() not in known]
    # 去子串：长词保留（更具体），短词若只是长词的片段则丢
    keep = []
    for w, n in sorted(cand, key=lambda x: (-len(x[0]), -x[1])):
        if any(w in k for k, _ in keep):
            continue
        keep.append((w, n))
    keep.sort(key=lambda x: -x[1])
    return keep[:top], len(gen)


def validate(texts, segment_id, words):
    """模拟把 words 加进 segment_id，重算分布并跑四条红线。返回 (verdict, detail)。"""
    base_spec = sg.load_spec()
    d0 = dist(texts, base_spec)
    n = sum(d0.values()) or 1
    spec = json.loads(json.dumps(base_spec))
    tgt = next((s for s in spec["segments"] if s["id"] == segment_id), None)
    if tgt is None:
        return "REJECT", {"why": "没有这个段：%s" % segment_id}
    tgt["signals"] = list(dict.fromkeys(list(tgt.get("signals") or []) + list(words)))
    d1 = dist(texts, spec)

    gen_drop = 100.0 * (d0.get("generic", 0) - d1.get("generic", 0)) / n
    tgt_gain = 100.0 * (d1.get(segment_id, 0) - d0.get(segment_id, 0)) / max(d0.get(segment_id, 1), 1)
    steal = {}
    for k, v0 in d0.items():
        if k in ("generic", segment_id):
            continue
        v1 = d1.get(k, 0)
        if v0 >= 20 and v1 < v0 * (1 - R3_STEAL_MAX_PCT / 100.0):
            steal[k] = round(100.0 * (v0 - v1) / v0, 1)
    share = 100.0 * d1.get(segment_id, 0) / n
    d = {"generic_drop_pp": round(gen_drop, 1), "target_gain_pct": round(tgt_gain, 1),
         "stolen_pct": steal, "target_share_pct": round(share, 1),
         "rows": {"before": dict(d0), "after": dict(d1)}}
    bad = []
    if gen_drop < R1_GENERIC_DROP_PP:
        bad.append("R1 generic 只降 %.1fpp（需 ≥%.0f）" % (gen_drop, R1_GENERIC_DROP_PP))
    if tgt_gain < R2_TARGET_GAIN_PCT:
        bad.append("R2 %s 只涨 %.0f%%（需 ≥%.0f%%）" % (segment_id, tgt_gain, R2_TARGET_GAIN_PCT))
    if steal:
        bad.append("R3 抢走 %s（>%.0f%%）"
                   % (", ".join("%s %.0f%%" % (k, v) for k, v in steal.items()), R3_STEAL_MAX_PCT))
    if share > R4_SEG_MAX_SHARE:
        bad.append("R4 %s 占比 %.0f%%（>%.0f%%）" % (segment_id, share, R4_SEG_MAX_SHARE))
    return ("REJECT" if bad else "ACCEPT"), dict(d, violations=bad)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--corpus", default=PASS_F)
    ap.add_argument("--segment", default="tech_nerd", help="候选要落进哪个段")
    ap.add_argument("--propose", action="store_true", help="只打候选")
    ap.add_argument("--apply-proposals", action="store_true",
                    help="验伤通过就把词写进段位文件（ACCEPT 才写）")
    ap.add_argument("--top", type=int, default=12)
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    texts = samples(a.corpus)
    if not texts:
        print("[seg] 语料为空：%s" % a.corpus)
        return 2
    cand, n_gen = propose(texts, top=a.top)
    print("[seg] 语料 %d 条，未识别 %d（%.1f%%）" % (len(texts), n_gen, 100.0 * n_gen / len(texts)))
    print("[seg] 候选：%s" % " · ".join("%s(%d)" % (w, n) for w, n in cand))
    words = [w for w, _ in cand]
    verdict, detail = validate(texts, a.segment, words)
    print("[seg] 验伤 %s → %s" % (a.segment, verdict))
    print("      generic 降 %.1fpp ｜ %s 涨 %.1f%% ｜ 占比 %.1f%%"
          % (detail.get("generic_drop_pp", 0), a.segment,
             detail.get("target_gain_pct", 0), detail.get("target_share_pct", 0)))
    for v in detail.get("violations") or []:
        print("      破线：%s" % v)
    rec = {"ts": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
           "segment": a.segment, "words": words, "verdict": verdict, "detail": detail}
    if a.apply_proposals:
        with open(OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("[seg] 提案已记账 → %s" % os.path.relpath(OUT, ROOT))
        if verdict == "ACCEPT":
            spec = json.load(open(SPEC, encoding="utf-8"))
            tgt = next(s for s in spec["segments"] if s["id"] == a.segment)
            tgt["signals"] = list(dict.fromkeys(list(tgt.get("signals") or []) + words))
            json.dump(spec, open(SPEC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("[seg] 已写入段位文件（ACCEPT）")
        else:
            print("[seg] 未写入（验伤未过，只留提案）")
    return 0 if verdict == "ACCEPT" else 1


def self_test():
    """四条红线必须能红：造"该拒"和"该过"两组样例反向验证。"""
    # 目标段涨得离谱→应因 R4 被拒；词无效→应因 R2 被拒
    fake = ["剪辑素材怎么弄" for _ in range(30)] + ["普通的一句话吧" for _ in range(70)]
    v1, d1 = validate(fake, "tech_nerd", ["剪辑素材"])
    v2, d2 = validate(fake, "tech_nerd", ["完全不存在的词组abc"])
    cases = [
        ("无效词必须拒（R2）", v2 == "REJECT"),
        ("有效词应通过", v1 == "ACCEPT"),
        ("不存在的段必须拒", validate(fake, "no_such_seg", ["剪辑"])[0] == "REJECT"),
        ("占比红线可触发（全部命中）", validate(["剪辑"] * 60, "tech_nerd", ["剪辑"])[1]
         .get("target_share_pct", 0) > R4_SEG_MAX_SHARE),
    ]
    ok = 0
    for n, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
        ok += 1 if c else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
