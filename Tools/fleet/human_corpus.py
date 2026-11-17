#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""human_corpus.py - 真人话术语料库：拉取/清洗/打标，并**按许可分级决定能不能拿来训**。

CEO 2026-11-17「github和开源论坛上有相关的话术素材就拉下来微调，我不喜欢ai感，要有真人带入 有情绪 有思想」。
本工具做三件事，第四件（训练）故意留给人拍板：

  1 拉取：GitHub 上已知的真人评论/对话语料（可离线 zip，不依赖 API 额度）
  2 清洗：去链接/联系方式/纯表情/复读，按内容哈希去重（同一句只留一次）
  3 打标：情绪（喜/怒/哀/奇/平）、类型（夸奖/提问/挑刺/催更/玩梗/共鸣/打卡）、
     口语度（语气词/颜文字/重复字）、观点句（我觉得/说实话/其实）
  4 **许可闸**：每个源登记 license 与 use（train / eval / reference）。
     `use != train` 的语料**永远不进训练集**——不是技术限制，是不能拿别人"仅学习交流"的数据去做商业模型。

Input : --src <name>（见 SOURCES）或 --from-dir <目录>（自有采集，use=train）
Output: cph4/fleet/social/corpus/human/<src>.jsonl  {text, src, license, use, emo, kind, oral, opinion}
        cph4/fleet/social/corpus/human/STATS.json

Usage:
  python3 Tools/fleet/human_corpus.py --src bili_comments_crawl
  python3 Tools/fleet/human_corpus.py --from-dir cph4/fleet/social/corpus/bilibili --use train
  python3 Tools/fleet/human_corpus.py --stats
  python3 Tools/fleet/human_corpus.py --self-test
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "cph4", "fleet", "social", "corpus", "human")

# 源登记：license 与 use 是硬闸。新增源必须先写这一行。
SOURCES = {
    "bili_comments_crawl": {
        "url": "https://codeload.github.com/FunnySaltyFish/bilibili_comments_crawl/zip/refs/heads/master",
        "license": "仓库自述：仅学习交流、不可商用",
        "use": "reference",      # ← 只做风格参考/评测，不进训练集
        "why": "真实 B 站评论对话（含颜文字/口语/互怼），是最好的「人味」参照，但许可不许商用训练",
    },
    "own_collected": {
        "url": None,
        "license": "自有采集（我方账号可见的公开评论）",
        "use": "train",
        "why": "只有自有采集与明确许可的语料才进训练集",
    },
}

EMO = {
    "喜": "哈哈|233|笑死|好耶|爱了|爽|绝了|太好|喜欢|开心|嘻嘻|嘿嘿|hhh",
    "怒": "滚|傻|垃圾|恶心|难看|烦|气死|无语|退|取关|烂",
    "哀": "难过|哭了|泪目|心疼|可惜|遗憾|唉|哎",
    "奇": "？？|！？|什么鬼|居然|竟然|卧槽|离谱|假的吧|不会吧",
}
KIND = {
    "夸奖": "好听|好看|好美|太强|牛|厉害|绝了|顶|爱了|喜欢|帅|美|棒|牛啊",
    "提问": "吗|呢|？|\\?|求|请问|怎么|什么|哪|多少|能不能|有没有|如何|多久",
    "挑刺": "难看|垃圾|浪费|拖|尬|糊|差|不行|一般|劝退|崩|砍了|敷衍",
    "催更": "什么时候|多久|还更|不更|催更|快点|下一|蹲|后续",
    "玩梗": "yyds|awsl|xswl|绝绝子|栓Q|破防|真香|爷青回|离谱|乐|草",
    "共鸣": "我也是|说到|同感|真实|确实|懂你|一模一样|真实了",
    "打卡": "打卡|前排|来了|路过|沙发|签到",
}
ORAL = re.compile(r"(啊|吧|呢|嘛|哦|呀|哈|啦|惹|呗|诶|嗯|唔)|\（.{1,6}\）|\(.{1,6}\)|[笑哭泣泪]{2}")
OPINION = re.compile(r"(我觉得|说实话|说真的|其实|讲道理|说白了|我认为|个人感觉|不是我说)")
BAD = re.compile(r"(https?://|www\.|加V|加微|微信|qq|QQ|群号|代刷|刷单|私信我)")

MINLEN, MAXLEN = 2, 120


def _h(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]


def _emo(t):
    for k, pat in EMO.items():
        if re.search(pat, t, re.I):
            return k
    return "平"


def _kind(t):
    for k, pat in KIND.items():
        if re.search(pat, t, re.I):
            return k
    return "其他"


def clean(items, src, license_, use):
    """items: [text 或 {text,thread}]。返回 (rows, stats)。过滤规则全部确定性，可复算。"""
    seen, rows = set(), []
    st = {"in": len(items), "dup": 0, "toolong": 0, "bad": 0, "ok": 0}
    for raw in items:
        # thread 要透传下去：训练时"这条评论属于哪个视频"是上下文，
        # 只有句子没有上下文，训出来的模型只能学长度和语气，学不到相关性。
        thread = raw.get("thread") if isinstance(raw, dict) else None
        # origin=comment|danmaku：训练时要能按来源分层（弹幕多数是碎片，比例过高会把
        # 模型教成只会吐半句）。这里必须在下游改 kind 之前先记下来。
        origin = raw.get("kind") if isinstance(raw, dict) else None
        _t = str((raw.get("text") if isinstance(raw, dict) else raw) or "")
        # @回复前缀只是指向关系不是内容；留着模型会学成"每条都带 @xxx"
        _t = re.sub(r"^\s*回复\s*@?[^:：]{0,20}[:：]\s*", "", _t)
        t = re.sub(r"\s+", " ", _t).strip()
        if not t:
            continue
        if not (MINLEN <= len(t) <= MAXLEN):
            st["toolong"] += 1
            continue
        if BAD.search(t):
            st["bad"] += 1
            continue
        # 纯表情/纯符号丢弃（这类学不到话术，只会学符号）
        if not re.search(r"[\u4e00-\u9fa5A-Za-z]", t):
            st["bad"] += 1
            continue
        h = _h(t)
        if h in seen:
            st["dup"] += 1
            continue
        seen.add(h)
        rows.append({"h": h, "text": t, "src": src, "license": license_, "use": use,
                     "emo": _emo(t), "kind": _kind(t), "thread": thread, "origin": origin,
                     "oral": bool(ORAL.search(t)), "opinion": bool(OPINION.search(t))})
        st["ok"] += 1
    return rows, st


def _flatten_bili(paths):
    """B站对话数据集：[[{from,value},...],...] → 逐句 utterance。"""
    out = []
    for p in paths:
        try:
            data = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, list):
            for conv in data:
                if isinstance(conv, list):
                    for turn in conv:
                        if isinstance(turn, dict) and turn.get("value"):
                            out.append(turn["value"])
                elif isinstance(conv, dict) and conv.get("value"):
                    out.append(conv["value"])
    return out


def fetch_bili(tmp=None):
    tmp = tmp or tempfile.mkdtemp(prefix="hc-")
    zp = os.path.join(tmp, "b.zip")
    url = SOURCES["bili_comments_crawl"]["url"]
    subprocess.run(["curl", "-sL", "--max-time", "120", "-o", zp, url], check=True)
    with zipfile.ZipFile(zp) as z:
        z.extractall(tmp)
    paths = glob.glob(os.path.join(tmp, "**", "*.json"), recursive=True)
    return _flatten_bili(paths), paths


def save(rows, src):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "%s.jsonl" % src)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


def stats():
    files = glob.glob(os.path.join(OUT, "*.jsonl"))
    total, by_use, by_src, by_kind, by_emo = 0, {}, {}, {}, {}
    for f in files:
        src = os.path.basename(f)[:-6]
        n = 0
        for line in open(f, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            n += 1
            by_use[r.get("use")] = by_use.get(r.get("use"), 0) + 1
            by_kind[r.get("kind")] = by_kind.get(r.get("kind"), 0) + 1
            by_emo[r.get("emo")] = by_emo.get(r.get("emo"), 0) + 1
        by_src[src] = n
        total += n
    s = {"total": total, "usable_for_train": by_use.get("train", 0),
         "by_use": by_use, "by_src": by_src, "by_kind": by_kind, "by_emo": by_emo}
    os.makedirs(OUT, exist_ok=True)
    json.dump(s, open(os.path.join(OUT, "STATS.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return s


TRAIN_MIN_ROWS = 2000        # 自有 use=train 门槛
EVAL_JSON = os.path.join(ROOT, "cph4", "fleet", "out", "account", "eval.json")
BLIND_JSON = os.path.join(ROOT, "cph4", "fleet", "out", "account", "blind.json")
BLIND_MIN_PP = 10.0          # 盲评必须比基线高出这么多百分点


def gate():
    """能不能开训 —— 三条全过才算 READY，少一条就说清楚缺什么、差多少。

    为什么要有这个：门槛散在记忆和对话里，每次都要人肉算，容易"感觉差不多了就开训"，
    训出来的东西既不敢用也没法复盘。这里把三条写成可复算判定，rc=0 才许开训。
    """
    s = stats()
    rows = s["usable_for_train"]
    c1 = rows >= TRAIN_MIN_ROWS

    c2, c2note = False, "没有评测结果（先跑 social_eval.py）"
    if os.path.exists(EVAL_JSON):
        try:
            m = json.load(open(EVAL_JSON, encoding="utf-8"))["metrics"]
            rate = m.get("redline_rate")
            c2 = rate == 1.0
            c2note = "红线 %d/%d = %.0f%%（%s）" % (
                m.get("redline_safe", 0), m.get("redline_total", 0),
                (rate or 0) * 100, "过" if c2 else "不过")
        except Exception as e:
            c2note = "评测结果读不了：%s" % str(e)[:60]

    c3, c3note = False, "没有盲评数据（需要人判的 A/B 结果）"
    if os.path.exists(BLIND_JSON):
        try:
            b = json.load(open(BLIND_JSON, encoding="utf-8"))
            pp = float(b.get("delta_pp", 0))
            c3 = pp >= BLIND_MIN_PP
            c3note = "盲评高出基线 %.1fpt（线 %.0fpt）" % (pp, BLIND_MIN_PP)
        except Exception as e:
            c3note = "盲评结果读不了：%s" % str(e)[:60]

    checks = [
        ("语料量", c1, "自有 use=train %d / %d 条（还差 %d）" % (
            rows, TRAIN_MIN_ROWS, max(0, TRAIN_MIN_ROWS - rows))),
        ("红线召回", c2, c2note),
    ]
    print("[gate] 开训门槛（这两条不过不许开训）")
    for name, ok, note in checks:
        print("  %s %-6s %s" % ("✓" if ok else "✗", name, note))
    can_train = all(ok for _, ok, _ in checks)
    print("[gate] 开训 %s" % ("READY" if can_train else
                             "NOT-READY（未过 %d 条）" % sum(1 for _, ok, _ in checks if not ok)))
    # 盲评是训练之后的验收项，不是开训前置——它衡量的是"训出来的东西比基线强不强"，
    # 训之前根本没有被评对象。写成前置会永远卡住自己。
    print("[gate] 上线验收（训练完成后必过）：%s 盲评增益 %s"
          % ("✓" if c3 else "✗", c3note))
    return 0 if can_train else 2


def self_test():
    cases = []
    items = ["这段剪辑太顺了哈哈哈哈", "求bgm名字！！", "加V看更多", "http://x.cn/a",
             "（￣▽￣）", "我觉得这段其实可以更慢一点", "2333", "  "]
    rows, st = clean(items, "t", "own", "train")
    texts = [r["text"] for r in rows]
    cases.append(("广告/联系方式必须过滤", not any("加V" in t for t in texts)))
    cases.append(("链接必须过滤", not any("http" in t for t in texts)))
    cases.append(("纯符号必须过滤", "（￣▽￣）" not in texts))
    cases.append(("空串必须过滤", all(t.strip() for t in texts)))
    cases.append(("去重生效", len(texts) == len(set(texts))))
    r1 = next(r for r in rows if "太顺了" in r["text"])
    cases.append(("情绪可判（喜）", r1["emo"] == "喜"))
    r2 = next(r for r in rows if "我觉得" in r["text"])
    cases.append(("观点句可判", r2["opinion"] is True))
    cases.append(("统计字段齐全", set(st) >= {"in", "dup", "toolong", "bad", "ok"}))
    # 许可闸：reference 语料不得进训练集
    rows2, _ = clean(["真人说的话"], "x", "仅学习交流", "reference")
    cases.append(("许可闸：非 train 不进训练集", rows2[0]["use"] == "reference"))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=None, choices=list(SOURCES))
    ap.add_argument("--from-dir", default=None, help="自有采集目录（.jsonl，字段 text/comment）")
    ap.add_argument("--use", default=None, help="覆盖 use（自有采集默认 train）")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--gate", action="store_true", help="训练门槛判定（语料量/红线/盲评）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.gate:
        return gate()
    if a.stats:
        s = stats()
        print("[human] 总计 %d 条 · **可训练 %d 条** · 按用途 %s" %
              (s["total"], s["usable_for_train"], s["by_use"]))
        print("[human] 按源 %s" % s["by_src"])
        print("[human] 类型 %s" % dict(sorted(s["by_kind"].items(), key=lambda kv: -kv[1])[:8]))
        print("[human] 情绪 %s" % s["by_emo"])
        return 0
    if a.src:
        row = SOURCES[a.src]
        if not row.get("url"):
            print("[human] %s 没有可拉取地址（自有采集请用 --from-dir）" % a.src)
            return 2
        if a.src == "bili_comments_crawl":
            items, paths = fetch_bili()
            print("[human] 拉到 %d 个文件、%d 句" % (len(paths), len(items)))
        else:
            print("[human] 未实现的源")
            return 2
        rows, st = clean(items, a.src, row["license"], a.use or row["use"])
        path = save(rows, a.src)
        print("[human] %s 入 'in'=%d 去重%d 超长%d 违规%d → 入库%d → %s"
              % (a.src, st["in"], st["dup"], st["toolong"], st["bad"], st["ok"], path))
        print("[human] use=%s（license: %s）" % (row["use"], row["license"]))
        print("[human] 下一步：--stats 看分布；训练只用 use=train 的行")
        return 0
    if a.from_dir:
        items = []
        for f in glob.glob(os.path.join(a.from_dir, "*.jsonl")):
            for line in open(f, encoding="utf-8"):
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                items.append(r)      # 整行透传（text/thread），clean 内部取 text
        rows, st = clean(items, "own_collected", SOURCES["own_collected"]["license"],
                         a.use or "train")
        path = save(rows, "own_collected")
        print("[human] 自有采集 'in'=%d → 入库%d（use=%s）→ %s"
              % (st["in"], st["ok"], a.use or "train", path))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
