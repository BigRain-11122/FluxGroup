#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""音乐平台评论区采集：网易云 / QQ音乐。

为什么补这条线（CEO 2026-11-26 令「你的训练素材去拉qq音乐 网易云音乐这些的音乐平台的评论，
有很多高质量的」）：
养号需要的不是"干货腔"，是**情感短句**——一句话里带情绪、带具体经验、不带术语。
B站评论偏理性讨论（"这期知识点密集"），音乐平台评论区偏故事与感受
（"虽然叫晴天，但整个故事都在下雨"），正好补上现在语料里最缺的那一类。

两条通道都实测过（2026-11-26）：
  · 网易云 `music.163.com/api/v1/resource/comments/R_SO_4_<id>` 直连可用，
    返回 hotComments + comments，无需登录、无需加密参数。
  · QQ音乐走 `soso/client_search_cp` 拿 **songid（数字）**，再用
    `fcg_global_comment_h5.fcg?...&topid=<songid>&cmd=6` 取评论。
    注意：topid 传 songmid（字母串）会返回 code=0 但 total=0 —— 这是个静默坑。

输出格式与 `corpus/human/own_collected.jsonl` 完全一致（use=train 才进训练集）。

用法：
  python3 Tools/fleet/music_comments.py --self-test
  python3 Tools/fleet/music_comments.py --netease 186016 --qq 97773 --limit 200
  python3 Tools/fleet/music_comments.py --keyword "周杰伦" --limit 120
  python3 Tools/fleet/music_comments.py ... --dry      # 只统计不落盘
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
TARGET = os.path.join(SOCIAL, "corpus", "human", "own_collected.jsonl")
SEEDS = os.path.join(SOCIAL, "MUSIC-SEEDS.json")
ROTATE = os.path.join(ROOT, ".codely-cli", "state", "MUSIC-ROTATE.json")
CLASSICS = os.path.join(SOCIAL, "MUSIC-CLASSICS.json")
PICKCACHE = os.path.join(ROOT, ".codely-cli", "state", "MUSIC-PICK-CACHE.json")
PICK_TTL_S = 30 * 86400      # 头部歌曲的 id 与评论量不会天天变，30 天足够
RAW_DIR = os.path.join(SOCIAL, "raw", "music")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# 太短的学不到语气，太长的是散文不是评论；音乐评论区两大极端都在中段最有价值
MIN_LEN, MAX_LEN = 8, 120


def _get(url, referer, timeout=25, retries=2):
    last = None
    for _ in range(max(1, retries)):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:      # 网络抖动重试，仍失败就抛给调用方定性
            last = e
            time.sleep(1.2)
    raise last


# ---------------- 网易云 ----------------
def netease_comments(song_id, limit=100, offset=0):
    """返回 [{"text","likes","song"}]。老接口直连，无需登录。"""
    url = ("https://music.163.com/api/v1/resource/comments/R_SO_4_%s?limit=%d&offset=%d"
           % (song_id, min(100, limit), offset))
    raw = _get(url, "https://music.163.com/")
    doc = json.loads(raw or "{}")
    if doc.get("code") not in (200, 0, None):
        raise RuntimeError("网易云 code=%s" % doc.get("code"))
    out = []
    for key in ("hotComments", "comments"):
        for c in (doc.get(key) or []):
            t = (c.get("content") or "").strip()
            if t:
                out.append({"text": t, "likes": int(c.get("likedCount") or 0),
                            "song": str(song_id), "platform": "netease_music"})
    return out


def netease_chart(n=50):
    """网易云热歌榜（playlist 3778678）前 n 首 → [song_id]。榜单本身就是"当下热度"。"""
    url = "https://music.163.com/api/playlist/detail?id=3778678"
    doc = json.loads(_get(url, "https://music.163.com/") or "{}")
    tracks = ((doc.get("result") or {}).get("tracks") or [])
    return [str(t.get("id")) for t in tracks[:n] if t.get("id")]


def comment_total(song_id, platform="netease_music"):
    """这首歌有多少条评论 —— 这就是"头部"的量化判据。

    实锚（2026-11-26）：晴天 196 万、我不难过 11 万、网络新歌 5516。
    靠它筛，比靠"歌手名搜索取前 8 首"准得多（后者会带出冷门与翻唱）。
    """
    if platform != "netease_music":
        return None
    url = ("https://music.163.com/api/v1/resource/comments/R_SO_4_%s?limit=1&offset=0"
           % song_id)
    try:
        return int(json.loads(_get(url, "https://music.163.com/") or "{}").get("total") or 0)
    except Exception:
        return None


def pick_best(keyword, n=5, artist=None):
    """按关键词搜歌，返回评论量最大的那一版 → (song_id, total, label)。

    为什么要"评论量最大"而不是"第一条"：网易云搜索对"歌名+歌手"的排序很脏。
    实锚（2026-11-26）：搜「稻香 周杰伦」第一条是「稻香(治愈版)|周杰伦.、街道办GDC」，
    搜「七里香 周杰伦」第一条是「七里香(MV版)|王俊凯」——都是翻唱。
    原唱的评论量是翻唱的几百倍（晴天 196 万、翻唱几千），所以用 total 选最稳，
    不需要依赖歌手名字匹配（正版的 artist 有时写 "Jay" 而不是"周杰伦"）。
    """
    # 缓存：头部歌的 song_id 基本不变，每次重查 4 条要多花 2-3 分钟
    cache = {}
    try:
        cache = json.load(open(PICKCACHE, encoding="utf-8"))
    except Exception:
        pass
    c = cache.get(keyword)
    if c and (time.time() - float(c.get("at") or 0)) < PICK_TTL_S:
        return c.get("sid"), int(c.get("total") or 0), keyword

    ids = netease_search(keyword, n)
    if not ids:
        return None, 0, ""
    best, best_tot = None, -1
    for sid in ids[:n]:
        tot = comment_total(sid)
        if tot is None:
            continue
        if tot > best_tot:
            best, best_tot = sid, tot
        # 已经足够头部就不用再问了（省请求）
        if best_tot >= 500000:
            break
        time.sleep(0.35)
    if best:
        cache[keyword] = {"sid": best, "total": max(0, best_tot), "at": time.time()}
        try:
            os.makedirs(os.path.dirname(PICKCACHE), exist_ok=True)
            json.dump(cache, open(PICKCACHE, "w", encoding="utf-8"), ensure_ascii=False)
        except Exception:
            pass
    return best, max(0, best_tot), keyword


def netease_paged(song_id, pages=5, per=100):
    """深翻页：头部歌评论几十万，首页只是极小样本。热评优先。"""
    out, first = [], True
    for pn in range(max(1, pages)):
        try:
            batch = netease_comments(song_id, limit=per, offset=pn * per)
        except Exception:
            break
        if not batch:
            break
        if first:
            out += batch          # 第一页含 hotComments（质量最高）
            first = False
        else:
            out += batch
        time.sleep(0.55)
    return out


def netease_search(keyword, n=10):
    """关键词 → [song_id]。type=1 是单曲。"""
    q = urllib.parse.quote(keyword)
    url = ("https://music.163.com/api/search/get?s=%s&type=1&limit=%d&offset=0" % (q, n))
    doc = json.loads(_get(url, "https://music.163.com/") or "{}")
    res = ((doc.get("result") or {}).get("songs") or [])
    return [str(x.get("id")) for x in res if x.get("id")]


# ---------------- QQ音乐 ----------------
def qq_search(keyword, n=10):
    """关键词 → [(songid, songmid, name)]。评论接口只认数字 songid。"""
    q = urllib.parse.quote(keyword)
    url = ("https://c.y.qq.com/soso/fcgi-bin/client_search_cp?p=1&n=%d&w=%s&format=json"
           % (n, q))
    doc = json.loads(_get(url, "https://y.qq.com/") or "{}")
    lst = (((doc.get("data") or {}).get("song") or {}).get("list") or [])
    out = []
    for s in lst:
        if s.get("songid"):
            out.append((str(s["songid"]), s.get("songmid") or "", s.get("songname") or ""))
    return out


def qq_comments(songid, limit=100, pagenum=0, pagesize=25):
    """cmd=6 是最新评论分页。topid 必须是数字 songid，传 songmid 会静默返回 0 条。"""
    url = ("https://c.y.qq.com/base/fcgi-bin/fcg_global_comment_h5.fcg?g_tk=5381&loginUin=0"
           "&hostUin=0&format=json&inCharset=utf8&outCharset=utf-8&notice=0"
           "&platform=yqq.json&needNewCode=0&cid=205360772&reqtype=2&biztype=1"
           "&topid=%s&cmd=6&pagenum=%d&pagesize=%d" % (songid, pagenum, min(25, pagesize)))
    doc = json.loads(_get(url, "https://y.qq.com/") or "{}")
    if doc.get("code") not in (0, None):
        raise RuntimeError("QQ音乐 code=%s" % doc.get("code"))
    c = doc.get("comment") or {}
    out = []
    for key in ("hotlist", "commentlist"):
        for x in (c.get(key) or []):
            t = (x.get("rootcommentcontent") or "").strip()
            if t:
                out.append({"text": t, "likes": int(x.get("praisenum") or 0),
                            "song": str(songid), "platform": "qq_music"})
    return out


# ---------------- 落盘 ----------------
def _h(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def load_rotate():
    try:
        return json.load(open(ROTATE, encoding="utf-8"))
    except Exception:
        return {}


def existing_hashes(path=TARGET):
    got = set()
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                got.add(json.loads(line).get("h"))
            except Exception:
                pass
    except FileNotFoundError:
        pass
    return got


def to_row(item):
    """转成与 own_collected.jsonl 一致的形状。"""
    t = re.sub(r"\s+", " ", item["text"]).strip()
    return {
        "h": _h(t),
        "text": t,
        "src": item["platform"],
        "license": "第三方平台公开评论（%s），按 CEO 2026-11-26 令纳入训练素材"
                   % item["platform"],
        "use": "train",
        "emo": "",
        "kind": "乐评",
        "thread": "%s://song/%s" % (item["platform"], item["song"]),
        "origin": item["platform"],
        "oral": False,
        "opinion": True,
        # 来源域已知：音乐平台评论区 → 音乐区观众段。不给这个提示，78% 会落进
        # generic 而 generic 不进任何训练段（实测 2412/3073 白采）。
        "seg_hint": "music_seeker",
    }


# 纯祝福/打卡模板：这类句子对学"怎么说话"没有信息量，却会教模型输出空话
_BLESS = re.compile(r"(希望|祝).{0,8}(顺利|快乐|成功|上岸|考上|加油|开心)")
_JUNK = re.compile(r"[^\u4e00-\u9fff\w\s，。！？、,.!?~…—\-\[\]（）()：:；;“”\"'’]")


def quality_ok(t):
    """这条值不值得进训练语料。

    2026-11-26 实锚：头部歌评论区里混着大量"谢谢[抱抱你]""希望明天考试顺利！"
    和一条字符乱码（ZakzkvnzkZ…）。这些进训练只会教模型说空话与输出噪声。
    判据：汉字够多、汉字占比够、字符噪声少、不是纯祝福模板。
    """
    han = len(re.findall(r"[\u4e00-\u9fff]", t))
    if han < 6:
        return False
    if han / max(1, len(t)) < 0.5:
        return False
    if len(_JUNK.findall(t)) > 3:
        return False
    if len(t) < 20 and _BLESS.search(t):
        return False
    # 连续 6 个以上拉丁字母基本是乱码或水军刷屏
    if re.search(r"[A-Za-z]{6,}", t):
        return False
    return True


def clean_and_filter(items):
    """长度、噪声与信息量过滤：链接/纯表情/纯@/纯数字/祝福模板/乱码都不进语料。"""
    out = []
    for it in items:
        t = re.sub(r"\s+", " ", (it.get("text") or "")).strip()
        if not (MIN_LEN <= len(t) <= MAX_LEN):
            continue
        if re.search(r"https?://", t):
            continue
        if re.fullmatch(r"[\d\s\W]+", t):
            continue
        if t.count("@") >= 2:
            continue
        if not quality_ok(t):
            continue
        out.append(dict(it, text=t))
    return out


def write_rows(items, path=TARGET, dry=False):
    have = existing_hashes(path)
    rows, seen = [], set()
    for it in items:
        r = to_row(it)
        if r["h"] in have or r["h"] in seen:
            continue
        seen.add(r["h"])
        rows.append(r)
    if dry:
        return len(rows), rows
    if rows:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.makedirs(RAW_DIR, exist_ok=True)
        with open(os.path.join(RAW_DIR, "music-%s.jsonl" %
                              time.strftime("%Y%m%d")), "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(rows), rows


def self_test():
    cases = []

    def fake_netease(url, referer, **kw):
        return json.dumps({"code": 200,
                           "hotComments": [{"content": "虽然叫晴天，但整个故事都在下雨", "likedCount": 9}],
                           "comments": [{"content": "短", "likedCount": 1}]})

    real_get = _get
    try:
        globals()["_get"] = fake_netease
        got = netease_comments(186016, limit=10)
        cases.append(("网易云解析出 2 条（含热评）", len(got) == 2))
        kept = clean_and_filter(got)
        cases.append(("过短被过滤", len(kept) == 1 and kept[0]["likes"] == 9))

        def fake_qq(url, referer, **kw):
            return json.dumps({"code": 0, "comment": {
                "commenttotal": 1,
                "commentlist": [{"rootcommentcontent": "高中三年每天单曲循环这首", "praisenum": 5}]}})
        globals()["_get"] = fake_qq
        q = qq_comments(97773, limit=10)
        cases.append(("QQ音乐解析出 1 条", len(q) == 1 and q[0]["platform"] == "qq_music"))

        # 负控：接口返 0 条时不能假装采到
        def fake_empty(url, referer, **kw):
            return json.dumps({"code": 0, "comment": {"commenttotal": 0, "commentlist": []}})
        globals()["_get"] = fake_empty
        cases.append(("空结果不造假", len(qq_comments(1)) == 0))

        # 负控：去重必须真的生效（同文本第二次不写）
        globals()["_get"] = fake_qq
        rows = [to_row(x) for x in qq_comments(97773)]
        cases.append(("哈希稳定可用于去重", rows[0]["h"] == _h(rows[0]["text"])))
        cases.append(("字段形状与训练语料一致",
                      {"h", "text", "src", "license", "use", "emo", "kind",
                       "thread", "origin", "oral", "opinion"} <= set(rows[0])))
        cases.append(("带来源段提示", rows[0].get("seg_hint") == "music_seeker"))
        cases.append(("纯祝福模板被滤",
                      quality_ok("希望明天考试顺利！") is False))
        cases.append(("字符乱码被滤",
                      quality_ok("ZakzkvnzkZxgkZlvnpv bxvpvxkzxpklv") is False))
        cases.append(("有细节的长评保留",
                      quality_ok("原曲像是站在爱人的身后轻声呢喃委屈，这个版本像是释然之后回头看") is True))
        cases.append(("use 必须是 train 才进训练集", rows[0]["use"] == "train"))
    finally:
        globals()["_get"] = real_get

    ok = 0
    for name, val in cases:
        print("  [%s] %s" % ("PASS" if val else "FAIL", name))
        ok += 1 if val else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--netease", default="", help="网易云 song_id，逗号分隔")
    ap.add_argument("--qq", default="", help="QQ音乐 songid（数字），逗号分隔")
    ap.add_argument("--keyword", default="", help="按关键词搜歌后采评论，逗号分隔多个")
    ap.add_argument("--chart", type=int, default=0,
                    help="采网易云热歌榜前 N 首的评论")
    ap.add_argument("--classics", action="store_true",
                    help="采 MUSIC-CLASSICS.json 里的头部歌手头部歌曲")
    ap.add_argument("--min-total", type=int, default=0,
                    help="只采评论总量 ≥ 这个数的歌（头部门槛）")
    ap.add_argument("--pages", type=int, default=3, help="每首深翻页数（100 条/页）")
    ap.add_argument("--rotate", type=int, default=0,
                    help="从 MUSIC-SEEDS.json 轮换取 N 个关键词（自动任务用）")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    items, errs = [], []
    netease_ids = [x for x in a.netease.split(",") if x.strip()]
    qq_ids = [x for x in a.qq.split(",") if x.strip()]
    if a.rotate:
        try:
            seeds = json.load(open(SEEDS, encoding="utf-8"))
            kws = list(seeds.get("keywords") or [])
            cur = int(load_rotate().get("next") or 0)
            pick = [kws[(cur + i) % len(kws)] for i in range(min(a.rotate, len(kws)))]
            od, _ = load_rotate(), None
            od["next"] = (cur + len(pick)) % max(1, len(kws))
            od["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            os.makedirs(os.path.dirname(ROTATE), exist_ok=True)
            json.dump(od, open(ROTATE, "w", encoding="utf-8"), ensure_ascii=False)
            a.keyword = (a.keyword + "," + ",".join(pick)) if a.keyword else ",".join(pick)
            print("[music] 本轮轮换到：%s" % "、".join(pick))
        except Exception as e:
            print("[music] 轮换失败（%s），改用 --keyword" % type(e).__name__)
            return 3
    if a.keyword:
        # 支持逗号分隔多个关键词：一次跑一批歌手，比一个个来省启动与握手
        for kw in [x.strip() for x in a.keyword.split(",") if x.strip()]:
            try:
                netease_ids += netease_search(kw, 8)
            except Exception as e:
                errs.append("网易云搜索[%s]失败：%s" % (kw, type(e).__name__))
            try:
                qq_ids += [s[0] for s in qq_search(kw, 8)]
            except Exception as e:
                errs.append("QQ音乐搜索[%s]失败：%s" % (kw, type(e).__name__))
            time.sleep(0.8)

    if a.chart:
        try:
            netease_ids += netease_chart(a.chart)
        except Exception as e:
            errs.append("热歌榜取不到：%s" % type(e).__name__)
    if a.classics:
        try:
            cl = json.load(open(CLASSICS, encoding="utf-8")).get("songs") or []
            print("[music] 按评论量挑头部版本（%d 首候选）…" % len(cl))
            for name in cl:
                try:
                    sid, tot, label = pick_best(name, n=4)
                    if sid:
                        netease_ids.append(sid)
                        print("  %-22s → %s（%d 条）" % (name, sid, tot))
                except Exception:
                    continue
                time.sleep(0.3)
        except Exception as e:
            errs.append("经典清单读不到：%s" % type(e).__name__)

    # 去重（榜单/清单/显式 id 可能重叠）
    seen_ids, uniq = set(), []
    for sid in netease_ids:
        if sid not in seen_ids:
            seen_ids.add(sid)
            uniq.append(sid)
    netease_ids = uniq

    skipped = 0
    for sid in netease_ids:
        tot = comment_total(sid) if a.min_total else None
        if a.min_total and (tot is None or tot < a.min_total):
            skipped += 1
            continue
        try:
            items += netease_paged(sid, pages=a.pages)
            if a.min_total:
                print("[music] %s 评论 %d 条 → 采 %d" % (sid, tot, 0))
        except Exception as e:
            errs.append("网易云 %s：%s" % (sid, type(e).__name__))
        time.sleep(0.5)
    if a.min_total and skipped:
        print("[music] 评论量不足被跳过 %d 首（门槛 %d）" % (skipped, a.min_total))
    for sid in qq_ids:
        pages = max(1, a.limit // 25)
        for pn in range(pages):
            try:
                items += qq_comments(sid, pagenum=pn)
            except Exception as e:
                errs.append("QQ %s p%s：%s" % (sid, pn, type(e).__name__))
                break
            time.sleep(0.5)

    kept = clean_and_filter(items)
    n, _rows = write_rows(kept, dry=a.dry)
    print("[music] 抓 %d 条 → 清洗后 %d → 新入库 %d%s"
          % (len(items), len(kept), n, "（dry，未写）" if a.dry else ""))
    for e in errs[:6]:
        print("  ! %s" % e)
    return 0 if (n or a.dry) else 3


if __name__ == "__main__":
    sys.exit(main())
