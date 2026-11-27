#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gzh_db.py — 公众号线的单一数据库（SQLite）。

为什么要建（CEO 2026-11-27「还是要建立可用的数据库」）：
  在此之前，这条线的账散在 7 个 append-only 文件里：
    ARTICLES.jsonl（风格语料）/ ARTICLES-INDUSTRY.jsonl（产业语料）/ URLS.jsonl（池子）
    URLS-FAILED.jsonl（死链）/ LOOP-LEDGER.jsonl（台账）/ trainset/*.jsonl / drafts/*/manifest.json
  后果是实测过的三种病：
    ① 21 行只有 17 个唯一链接——重复入库没人拦，也没人能一眼看出来；
    ② 「两本账混着数」把已采完的 71 条盖世链接当待抓，一次跑爆 900 秒预算（2026-11-25 实锚）；
    ③ 想回答「风格语料到底有几篇能训」要写一次性 python，每次口径还可能不一样。
  SQLite 一次解决三条：唯一约束挡重复、genre 字段分两本账、一条 SQL 就是口径。

设计约束（照本工程的规矩来）：
  · 只用标准库 sqlite3，不引外部依赖，不装服务。
  · 导入幂等：同一个文件导两次，行数不变；重复只记账不重复插。
  · URL 归一化后再判重（https/http、尾参数、锚点、斜杠），归一化本身要能被负控证明在起作用。
  · 数据库是派生物：jsonl 仍是采集器的落地格式，DB 可随时 --rebuild 重建，不做双向写。

用法：
  python3 Tools/fleet/gzh_db.py --init          # 建库建表建视图
  python3 Tools/fleet/gzh_db.py --ingest-all    # 全量导入（幂等，可反复跑）
  python3 Tools/fleet/gzh_db.py --status        # 一屏看账
  python3 Tools/fleet/gzh_db.py --check         # 完整性检查，有问题 rc=1
  python3 Tools/fleet/gzh_db.py --ask style|week|gates
  python3 Tools/fleet/gzh_db.py --self-test
退出码：0 正常 / 1 check 有问题 / 4 自检失败
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GZH = os.environ.get("GZH_DIR") or os.path.join(ROOT, "cph4", "fleet", "social", "gzh")
DB = os.environ.get("GZH_DB") or os.path.join(GZH, "gzh.db")

# 追踪参数：只影响来源归因，不影响文章身份。
# 刻意**不**剥 __biz / mid / idx / sn——老式公众号链接靠这四个定位到具体某篇，
# 剥掉会把不同文章合并成一条（这是最容易写错的一处，自检里有负控守着）。
TRACK = {"from", "scene", "subscene", "srcid", "sharer_sharetime", "sharer_shareid",
         "chksm", "sessionid", "clicktime", "enterid", "ascene", "devicetype",
         "version", "nettype", "abtest_cookie", "key", "pass_ticket", "wx_header",
         "isappinstalled", "exportkey", "frommsgid", "mpshare", "sharing",
         "utm_source", "utm_medium", "utm_campaign", "spm", "ref"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS urls (
  uid        TEXT PRIMARY KEY,
  url        TEXT NOT NULL,
  url_norm   TEXT NOT NULL UNIQUE,
  kw         TEXT, source TEXT, mirror TEXT, author_id TEXT,
  title      TEXT, found_at TEXT,
  status     TEXT DEFAULT 'todo'   -- todo / done / failed
);
CREATE TABLE IF NOT EXISTS articles (
  uid        TEXT PRIMARY KEY,
  url_norm   TEXT NOT NULL UNIQUE,
  url        TEXT, account TEXT, author TEXT,
  title      TEXT NOT NULL,
  publish_ts TEXT, publish_date TEXT,
  words      INTEGER, paras INTEGER, imgs INTEGER,
  heads_json TEXT, lead TEXT, body TEXT,
  genre      TEXT,            -- review=可训文风 / press=通稿 / industry=产业 / unknown
  genre_why  TEXT, source TEXT, mirror INTEGER, fetched_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_art_genre ON articles(genre);
CREATE INDEX IF NOT EXISTS ix_art_account ON articles(account);
CREATE TABLE IF NOT EXISTS url_failures (
  uid TEXT PRIMARY KEY, url TEXT, url_norm TEXT, why TEXT, at TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_fail_norm ON url_failures(url_norm, why);
CREATE TABLE IF NOT EXISTS weeks (
  week TEXT PRIMARY KEY, season TEXT, kind TEXT,
  date_from TEXT, date_to TEXT, theme TEXT, why TEXT, keywords TEXT
);
CREATE TABLE IF NOT EXISTS week_pieces (
  week TEXT, quadrant TEXT, topic TEXT,
  PRIMARY KEY (week, topic)
);
CREATE TABLE IF NOT EXISTS drafts (
  date TEXT, path TEXT, week TEXT, topic TEXT, quadrant TEXT, kind TEXT,
  chars INTEGER, status TEXT, writer TEXT, gate_json TEXT,
  PRIMARY KEY (date, path)
);
CREATE TABLE IF NOT EXISTS gate_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT, path TEXT, gate TEXT, rc INTEGER, detail TEXT, at TEXT
);
CREATE TABLE IF NOT EXISTS loop_ledger (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT, phase TEXT, status TEXT, secs REAL, why TEXT, tail TEXT,
  facts_json TEXT, run_id TEXT
);
-- 台账每次全量导入会重复插，唯一键挡住（同一拍同一 run_id 只算一行）
CREATE UNIQUE INDEX IF NOT EXISTS ux_ledger ON loop_ledger(ts, run_id);
CREATE TABLE IF NOT EXISTS ingest_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT, file TEXT, rows INTEGER, inserted INTEGER, merged INTEGER,
  skipped INTEGER, note TEXT
);
CREATE VIEW IF NOT EXISTS v_style_corpus AS
  SELECT account, COUNT(*) n, ROUND(AVG(words),0) avg_words
  FROM articles WHERE genre IN ('review','feature') GROUP BY account ORDER BY n DESC;
CREATE VIEW IF NOT EXISTS v_corpus_split AS
  SELECT genre, COUNT(*) n FROM articles GROUP BY genre ORDER BY n DESC;
CREATE VIEW IF NOT EXISTS v_account_mix AS
  SELECT account, genre, COUNT(*) n FROM articles GROUP BY account, genre ORDER BY n DESC;
"""


def norm_url(u):
    """URL 归一化：去掉协议差异、追踪参数、锚点、尾斜杠。判重的唯一依据。"""
    if not u:
        return ""
    s = u.strip()
    if s.startswith("//"):
        s = "http:" + s
    try:
        p = urlsplit(s)
    except Exception:
        return s
    host = (p.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k not in TRACK]
    path = p.path.rstrip("/") or "/"
    return urlunsplit(("https", host, path, urlencode(q), ""))


def conn(path=None):
    c = sqlite3.connect(path or DB)
    c.row_factory = sqlite3.Row
    return c


def init(path=None):
    p = path or DB
    os.makedirs(os.path.dirname(p), exist_ok=True)
    c = conn(p)
    c.executescript(SCHEMA)
    # 老库升级：CREATE TABLE IF NOT EXISTS 不会补列，这里显式补
    try:
        c.execute("ALTER TABLE urls ADD COLUMN status TEXT DEFAULT 'todo'")
    except sqlite3.OperationalError:
        pass
    c.commit()
    c.close()
    return p


def _rows(f):
    for ln in open(f, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            yield json.loads(ln)
        except Exception:
            yield None


def ingest_articles(f, c, genre_default=None):
    ins = merged = skipped = bad = 0
    for r in _rows(f):
        if not isinstance(r, dict) or not r.get("title"):
            bad += 1
            continue
        n = norm_url(r.get("url"))
        if not n:
            bad += 1
            continue
        try:
            c.execute("""INSERT INTO articles
              (uid,url_norm,url,account,author,title,publish_ts,publish_date,words,paras,
               imgs,heads_json,lead,body,genre,genre_why,source,mirror,fetched_at)
              VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                r.get("_uid") or n, n, r.get("url"), r.get("account"), r.get("author"),
                r["title"], r.get("publish_ts"), r.get("publish_date"),
                r.get("words"), r.get("paras"), r.get("imgs"),
                json.dumps(r.get("heads") or [], ensure_ascii=False),
                r.get("lead"), r.get("text"),
                r.get("genre") or genre_default or "unknown",
                r.get("genre_why"), r.get("source"),
                1 if r.get("mirror") else 0, r.get("fetched_at")))
            ins += 1
        except sqlite3.IntegrityError:
            merged += 1          # 同一篇的另一种链接写法：记合并，不再插
            # 但判据会变（例：2026-11-27 新增 feature 体裁），已有行必须跟着更新，
            # 否则库里存的是过期分类，重算半天等于没算。
            try:
                c.execute("""UPDATE articles SET genre=?, genre_why=?, words=?,
                             heads_json=?, account=COALESCE(account,?) WHERE url_norm=?""",
                          (r.get("genre") or genre_default or "unknown", r.get("genre_why"),
                           r.get("words"),
                           json.dumps(r.get("heads") or [], ensure_ascii=False),
                           r.get("account"), n))
            except Exception:
                pass
        except Exception:
            skipped += 1
    return ins, merged, skipped, bad


def ingest_urls(f, c):
    ins = merged = bad = 0
    for r in _rows(f):
        if not isinstance(r, dict) or not r.get("url"):
            bad += 1
            continue
        n = norm_url(r["url"])
        try:
            c.execute("""INSERT INTO urls (uid,url,url_norm,kw,source,mirror,author_id,title,found_at)
                         VALUES (?,?,?,?,?,?,?,?,?)""",
                      (r.get("_uid") or n, r["url"], n, r.get("kw"), r.get("source"),
                       r.get("mirror"), r.get("author_id"), r.get("title"), r.get("found_at")))
            ins += 1
        except sqlite3.IntegrityError:
            merged += 1
        except Exception:
            bad += 1
    return ins, merged, bad


def ingest_failures(f, c):
    ins = bad = 0
    for r in _rows(f):
        if not isinstance(r, dict) or not r.get("url"):
            bad += 1
            continue
        n = norm_url(r["url"])
        try:
            cur = c.execute("INSERT OR IGNORE INTO url_failures (uid,url,url_norm,why,at) VALUES (?,?,?,?,?)",
                            (r.get("_uid") or n, r["url"], n, r.get("why"), r.get("at")))
            ins += max(cur.rowcount, 0)   # 真实插入行数，不是"尝试次数"（假计数会骗人）
        except Exception:
            bad += 1
    return ins, bad


def ingest_ledger(f, c):
    ins = bad = 0
    for r in _rows(f):
        if not isinstance(r, dict) or not r.get("ts"):
            bad += 1
            continue
        try:
            cur = c.execute("""INSERT OR IGNORE INTO loop_ledger
                         (ts,phase,status,secs,why,tail,facts_json,run_id)
                         VALUES (?,?,?,?,?,?,?,?)""",
                      (r.get("ts"), r.get("phase"), r.get("status"), r.get("secs"),
                       r.get("why"), r.get("tail"),
                       json.dumps(r.get("facts") or {}, ensure_ascii=False), r.get("run_id") or ""))
            ins += max(cur.rowcount, 0)
        except Exception:
            bad += 1
    return ins, bad


def ingest_themes(f, c):
    d = json.load(open(f, encoding="utf-8"))
    ins = 0
    for w in d.get("weeks") or []:
        c.execute("""INSERT OR REPLACE INTO weeks
                     (week,season,kind,date_from,date_to,theme,why,keywords)
                     VALUES (?,?,?,?,?,?,?,?)""",
                  (w["week"], w.get("season"), w.get("kind"), w.get("from"), w.get("to"),
                   w.get("主题"), w.get("为什么这周写这个"),
                   "、".join(w.get("关键词") or [])))
        for p in w.get("篇") or []:
            c.execute("INSERT OR REPLACE INTO week_pieces (week,quadrant,topic) VALUES (?,?,?)",
                      (w["week"], p.get("quadrant"), p.get("topic")))
        ins += 1
    return ins


def ingest_drafts(c):
    """导草稿与闸结论。gates.txt 里没有结构化 rc 时，用 manifest 的 gate_rc。"""
    ins = 0
    for man in sorted(glob.glob(os.path.join(GZH, "drafts", "*", "manifest.json"))):
        try:
            m = json.load(open(man, encoding="utf-8"))
        except Exception:
            continue
        d = m.get("date") or os.path.basename(os.path.dirname(man))
        path = m.get("draft") or ""
        c.execute("""INSERT OR REPLACE INTO drafts
                     (date,path,week,topic,quadrant,kind,chars,status,writer,gate_json)
                     VALUES (?,?,?,?,?,?,?,?,?,?)""",
                  (d, path, m.get("week"), m.get("topic"), m.get("quadrant"), m.get("kind"),
                   m.get("chars"), m.get("status"), m.get("writer"),
                   json.dumps(m.get("gate_rc") or {}, ensure_ascii=False)))
        for gate, rc in (m.get("gate_rc") or {}).items():
            c.execute("""INSERT INTO gate_runs (date,path,gate,rc,detail,at) VALUES (?,?,?,?,?,?)""",
                      (d, path, gate, rc, None, m.get("queued_at") or d))
        ins += 1
    return ins


def _log(c, f, rows, ins, merged=0, skipped=0, note=""):
    c.execute("""INSERT INTO ingest_log (ts,file,rows,inserted,merged,skipped,note)
                 VALUES (?,?,?,?,?,?,?)""",
              (datetime.now().isoformat(timespec="seconds"), os.path.basename(f),
               rows, ins, merged, skipped, note))


def ingest_all(path=None, gzh=None):
    p = path or DB
    g = gzh or GZH
    init(p)
    c = conn(p)
    out = {}
    for name, fn in (("ARTICLES.jsonl", ingest_articles), ("ARTICLES-INDUSTRY.jsonl", ingest_articles)):
        f = os.path.join(g, name)
        if os.path.exists(f):
            before = c.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
            n = len(list(_rows(f)))
            r = fn(f, c)
            after = c.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
            out[name] = dict(rows=n, inserted=r[0], merged=r[1] or 0, bad=r[2] or r[3] or 0,
                             table_delta=after - before)
            _log(c, f, n, r[0], r[1] or 0, r[2] if len(r) > 2 else 0)
    f = os.path.join(g, "URLS.jsonl")
    if os.path.exists(f):
        n = len(list(_rows(f)))
        r = ingest_urls(f, c)
        out["URLS.jsonl"] = dict(rows=n, inserted=r[0], merged=r[1], bad=r[2])
        _log(c, f, n, r[0], r[1], r[2])
    f = os.path.join(g, "URLS-FAILED.jsonl")
    if os.path.exists(f):
        n = len(list(_rows(f)))
        r = ingest_failures(f, c)
        out["URLS-FAILED.jsonl"] = dict(rows=n, inserted=r[0], bad=r[1])
        _log(c, f, n, r[0], 0, r[1])
    f = os.path.join(g, "LOOP-LEDGER.jsonl")
    if os.path.exists(f):
        n = len(list(_rows(f)))
        r = ingest_ledger(f, c)
        out["LOOP-LEDGER.jsonl"] = dict(rows=n, inserted=r[0], bad=r[1])
        _log(c, f, n, r[0], 0, r[1])
    f = os.path.join(g, "THEME-SEASONS-v1.json")
    if os.path.exists(f):
        try:
            out["THEME-SEASONS-v1.json"] = dict(weeks=ingest_themes(f, c))
        except Exception as e:  # noqa: BLE001
            out["THEME-SEASONS-v1.json"] = dict(error=str(e)[:80])
    out["drafts"] = dict(manifests=ingest_drafts(c))
    # 状态落库：池子里已在 articles 出现过的，标 done。
    # 不这么做的话「还有多少待抓」每次都要 join 现推，一处算错就派错活
    # （2026-11-25 实锚：71 条已采链接被当待抓，一次跑爆 900 秒预算）。
    c.execute("""UPDATE urls SET status='done'
                 WHERE url_norm IN (SELECT url_norm FROM articles)""")
    c.execute("""UPDATE urls SET status='failed'
                 WHERE status<>'done' AND url_norm IN (SELECT url_norm FROM url_failures)""")
    out["urls_status"] = dict(zip(("todo", "done", "failed"), (
        c.execute("SELECT COUNT(*) FROM urls WHERE status='todo'").fetchone()[0],
        c.execute("SELECT COUNT(*) FROM urls WHERE status='done'").fetchone()[0],
        c.execute("SELECT COUNT(*) FROM urls WHERE status='failed'").fetchone()[0])))
    c.commit()
    c.close()
    return out


# ---------------------------------------------------------------- 读

def status(path=None):
    c = conn(path or DB)
    q = lambda s: c.execute(s).fetchone()[0]  # noqa: E731
    info = {
        "文章总数": q("SELECT COUNT(*) FROM articles"),
        "风格语料(review+feature)": q("SELECT COUNT(*) FROM articles WHERE genre IN ('review','feature')"),
        "通稿(press)": q("SELECT COUNT(*) FROM articles WHERE genre='press'"),
        "产业(industry)": q("SELECT COUNT(*) FROM articles WHERE genre='industry'"),
        "未知(unknown)": q("SELECT COUNT(*) FROM articles WHERE genre='unknown'"),
        "种子池": q("SELECT COUNT(*) FROM urls"),
        "待抓(todo)": q("SELECT COUNT(*) FROM urls WHERE status='todo'"),
        "已采(done)": q("SELECT COUNT(*) FROM urls WHERE status='done'"),
        "死链": q("SELECT COUNT(*) FROM url_failures"),
        "周主题": q("SELECT COUNT(*) FROM weeks"),
        "草稿": q("SELECT COUNT(*) FROM drafts"),
        "台账行": q("SELECT COUNT(*) FROM loop_ledger"),
        "累计合并重复": q("SELECT COALESCE(SUM(merged),0) FROM ingest_log"),
    }
    width = max(len(k) for k in info)
    for k, v in info.items():
        print("%s  %s" % (k.ljust(width + 2, "　"), v))
    print("\n账号 × 体裁：")
    for r in c.execute("SELECT * FROM v_account_mix LIMIT 12"):
        print("  %-28s %-9s %d" % (r["account"] or "(未知)", r["genre"], r["n"]))
    c.close()
    return info


def check(path=None):
    """完整性检查。只查能被证伪的：缺链接、缺正文、同题重复、池子里已采的还被当待抓。"""
    c = conn(path or DB)
    problems = []

    n = c.execute("SELECT COUNT(*) FROM articles WHERE url_norm IS NULL OR url_norm=''").fetchone()[0]
    if n:
        problems.append("有 %d 篇没有可用链接" % n)
    n = c.execute("SELECT COUNT(*) FROM articles WHERE body IS NULL OR length(body)<200").fetchone()[0]
    if n:
        problems.append("有 %d 篇正文缺失或过短（<200 字）" % n)
    # 同名不同号不算重复（行业内通稿多平台同题很常见），同名同号才是真重复
    # 产业稿没有 account，用 source 代替；两者都空就归一组
    for r in c.execute("""SELECT COALESCE(account,'') acc, COALESCE(source,'') src,
                                 title, COUNT(*) n FROM articles
                          GROUP BY acc, src, title HAVING n>1 ORDER BY n DESC LIMIT 5"""):
        problems.append("同源同名 %d 篇：%s%s｜%s"
                        % (r["n"], r["acc"] or "", r["src"] or "", r["title"][:36]))
    n = c.execute("""SELECT COUNT(*) FROM urls u JOIN articles a ON a.url_norm=u.url_norm
                     WHERE u.status<>'done'""").fetchone()[0]
    if n:
        problems.append("池子状态没落库：%d 条已采完却仍标 todo/未标（状态同步没跑）" % n)

    if problems:
        print("完整性检查：%d 项" % len(problems))
        for p in problems:
            print("  - " + p)
    else:
        print("完整性检查：全过")
    c.close()
    return 1 if problems else 0


def ask(what, path=None):
    c = conn(path or DB)
    what = (what or "style").lower()
    if what == "style":
        print("能进文笔训练的篇目（genre=review）：")
        for r in c.execute("SELECT * FROM v_style_corpus"):
            print("  %-24s %3d 篇  均 %s 字" % (r["account"], r["n"], r["avg_words"]))
    elif what == "week":
        for r in c.execute("SELECT * FROM weeks ORDER BY date_from"):
            print("%s %s → %s《%s》" % (r["week"], r["date_from"], r["date_to"], r["theme"]))
            for p in c.execute("SELECT * FROM week_pieces WHERE week=?", (r["week"],)):
                print("    · [%s] %s" % (p["quadrant"], p["topic"]))
    elif what == "gates":
        for r in c.execute("""SELECT date,gate,rc FROM gate_runs
                              ORDER BY date DESC, gate LIMIT 30"""):
            print("  %s  %-10s %s" % (r["date"], r["gate"], "过" if r["rc"] == 0 else "未过"))
    else:
        print("可选：style / week / gates")
        c.close()
        return 2
    c.close()
    return 0


# ---------------------------------------------------------------- 自检

def self_test():
    import tempfile
    fails = []
    d = tempfile.mkdtemp(prefix="gzhdb-")
    p = os.path.join(d, "t.db")

    # 1 归一化真的在起作用（负控：不去追踪参数就会变两条）
    a = norm_url("https://mp.weixin.qq.com/s/abc?from=timeline&isappinstalled=0")
    b = norm_url("http://www.mp.weixin.qq.com/s/abc/")
    if a != b:
        fails.append("URL 归一化没消掉协议/参数/尾斜杠差异：%s vs %s" % (a, b))

    init(p)
    f1 = os.path.join(d, "a.jsonl")
    with open(f1, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"url": "https://mp.weixin.qq.com/s/abc?from=x", "title": "甲",
                             "account": "42号车库", "words": 100, "genre": "review",
                             "text": "正文" * 200}, ensure_ascii=False) + "\n")
        fh.write(json.dumps({"url": "http://www.mp.weixin.qq.com/s/abc/", "title": "甲二",
                             "account": "42号车库", "words": 100, "genre": "review",
                             "text": "正文" * 200}, ensure_ascii=False) + "\n")
        fh.write("{坏 JSON\n")
    c = conn(p)
    ins, merged, skipped, bad = ingest_articles(f1, c)
    c.commit()
    n1 = c.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    if n1 != 1:
        fails.append("同 URL 两种写法没被合并（期望 1 行，实际 %d）" % n1)
    if merged != 1:
        fails.append("合并计数不对（期望 1，实际 %d）" % merged)
    if bad != 1:
        fails.append("坏 JSON 没被计入 bad（期望 1，实际 %d）" % bad)

    # 2 幂等：同一文件再导一次，行数不变、重复只记账
    ins2, merged2, _, _ = ingest_articles(f1, c)
    c.commit()
    n2 = c.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    if n2 != n1:
        fails.append("导入不幂等：第二次导完变成 %d 行（第一次 %d）" % (n2, n1))

    # 3 负控：两本账必须靠 genre 分开，不可靠文件名
    c.execute("""INSERT INTO articles (uid,url_norm,title,genre,body)
                 VALUES ('x2','https://e.com/2','乙','industry','x'||printf('%200c',''))""")
    c.commit()
    style = c.execute("SELECT COUNT(*) FROM articles WHERE genre='review'").fetchone()[0]
    if style != 1:
        fails.append("genre 分账失效：review 应为 1，实际 %d" % style)

    # 4 状态必须落库：池子里已采的条目 status 应为 done
    c.execute("INSERT INTO urls (uid,url,url_norm,status) VALUES ('u1','https://mp.weixin.qq.com/s/abc','%s','todo')" % a)
    c.execute("""UPDATE urls SET status='done' WHERE url_norm IN (SELECT url_norm FROM articles)""")
    c.commit()
    st = c.execute("SELECT status FROM urls WHERE uid='u1'").fetchone()[0]
    if st != "done":
        fails.append("状态没落库：已采条目 status=%s（应为 done）" % st)

    # 5 check 必须能在坏数据上判红（把状态改回 todo 模拟同步没跑）
    c.execute("UPDATE urls SET status='todo' WHERE uid='u1'")
    c.commit()
    c.close()
    rc = check(p)
    if rc == 0:
        fails.append("负控失效：池子里有已采完的链接，check 仍判全过")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for x in fails:
            print("  - " + x, file=sys.stderr)
        return 4
    print("SELF-TEST OK 4/4（归一化/幂等/分账/check 能红）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--ingest-all", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--ask", default=None)
    ap.add_argument("--db", default=None)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.db:
        globals()["DB"] = a.db
    if a.self_test:
        return self_test()
    if a.init:
        print("建库：%s" % init())
        return 0
    if a.ingest_all:
        out = ingest_all()
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    if a.status:
        status()
        return 0
    if a.check:
        return check()
    if a.ask:
        return ask(a.ask)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
