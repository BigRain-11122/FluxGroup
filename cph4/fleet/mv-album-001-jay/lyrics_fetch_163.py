# -*- coding: utf-8 -*-
# lyrics_fetch_163.py — 官方词面补给（163 歌词 API → lyrics/<曲>.lrc + lyrics/<曲>.txt）
#
# 为什么需要: lyric_calibration.py 要求 lyrics/<曲>.txt(官方词面) 或 .lrc(带时间戳);
#   POOL-0018/0019 首批 7 曲锚里 晴天 有 whisper words + madmom beats 但缺官方词面,
#   导致 calibrated/shotgrid 两腿产不出（matrix ready=6/7）。
#
# 用法: python lyrics_fetch_163.py <曲名> <163_song_id> [--first-line "<首句>"...]
#   头注格式与既有词面一致(# title= / # source=), 制片方来源与抓取时刻写进头注。
#   制作人员行(作词/作曲/编曲/… "XX : YY")被剔除——只留可唱歌词行。
# 自检: python lyrics_fetch_163.py --selftest   (离线夹具: 剔除/行数/头注三腿)
import io
import json
import os
import re
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
LYR = os.path.join(BASE, "lyrics")
API = "https://music.163.com/api/song/lyric?id=%s&lv=1&kv=1&tv=-1"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

# 制作人员行关键词（163 的 credit 行统一形如 "[00:00.000] 作词 : 周杰伦"）
CREDIT_KEYS = (
    "作词", "作曲", "编曲", "制作人", "和声编写", "和声", "吉他", "贝斯", "鼓",
    "录音工程", "混音", "录音助理", "母带", "监制", "发行", "出品", "统筹",
    "弦乐", "键盘", "合声", "program", "Program", "OP", "SP", "词", "曲",
)
TS = re.compile(r"^\[(\d+):(\d+)(?:[.:](\d{1,3}))?\]\s*(.*)$")
SEARCH = "https://music.163.com/api/search/get/web?s=%s&type=1&offset=0&limit=10"
ARTIST = "周杰伦"


def search_ids(song):
    """Resolve a 163 song id by name, refusing anything that is not clearly this track.

    Why this exists: the fetch leg only ever took an id, so the 27 unanchored album
    tracks could not get official lyrics without a human looking each id up - which is
    what actually held the anchor line at 14/41 (whisper alone is not enough: the text
    must be the official 正身). Matching is deliberately strict - exact normalized name
    AND artist must equal 周杰伦; near-matches are printed for a human, never written.
    """
    import urllib.parse
    q = urllib.parse.quote(song)
    req = urllib.request.Request(SEARCH % q,
                                 headers={"User-Agent": UA, "Referer": "https://music.163.com/"})
    try:
        data = json.load(urllib.request.urlopen(req, timeout=25))
    except Exception as e:  # noqa: BLE001 - a lookup failure must not kill the batch
        return None, [], "search-error: %s" % e
    songs = ((data.get("result") or {}).get("songs")) or []
    want = norm_song(song)
    exact = []
    for s in songs:
        artists = ",".join(a.get("name", "") for a in (s.get("artists") or []))
        if want in norm_song(s.get("name", "")) and ARTIST in artists:
            exact.append((s.get("id"), s.get("name"), artists))
    if not exact:
        return None, [(s.get("id"), s.get("name"),
                       ",".join(a.get("name", "") for a in (s.get("artists") or [])))
                      for s in songs[:5]], "no-exact-match"
    return exact[0][0], exact, ""


def norm_song(s):
    # Punctuation must not decide identity: QQ lists the same track as "爸，我回来了",
    # "爸,我回来了" and "爸 我回来了", and a full-width comma was enough to make the
    # matcher refuse a real original (measured 2026-11-06).
    return re.sub(r"[\s\u3000·\-—_（）()\[\]【】，,、。.．!！?？:：\"'“”‘’]", "", s or "")


# ---- second source: QQ Music -------------------------------------------------------
# Why: 网易云 search returns only covers for several album tracks (measured 2026-11-06:
# 三年二班 -> Madman/晚安/... , never 周杰伦), so the strict matcher kept refusing and
# the anchor line stayed at 14/41 for want of official 词面. QQ Music returns the real
# track, and its lyric body carries its own [ti:]/[ar:] tags - the strongest possible
# self-check, since the text declares which song it is.
QQ_SEARCH = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp?w=%s&format=json&n=30&new_json=1"
QQ_LYRIC = ("https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg"
            "?songmid=%s&format=json&nobase64=0&g_tk=5381")
QQ_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/120 Safari/537.36")


def qq_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": QQ_UA,
                                              "Referer": "https://y.qq.com/portal/player.html"})
    raw = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
    return json.loads(raw[raw.find("{"):])


def fetch_qq(song):
    """Return parsed rows via QQ Music, or raise RuntimeError with the reason."""
    import base64
    import urllib.parse
    d = qq_get(QQ_SEARCH % urllib.parse.quote("%s %s" % (song, ARTIST)))
    lst = (((d.get("data") or {}).get("song") or {}).get("list")) or []
    want = norm_song(song)
    mid = None
    for s in lst:
        singers = [a.get("name", "") for a in (s.get("singer") or [])]
        if singers == [ARTIST] and norm_song(s.get("name", "")) == want:
            mid = s.get("mid")
            break
    if not mid:
        raise RuntimeError("qq-no-exact-match")
    d = qq_get(QQ_LYRIC % mid)
    body = d.get("lyric") or ""
    if body and not body.lstrip().startswith("["):
        body = base64.b64decode(body).decode("utf-8", "replace")
    if "[ar:%s]" % ARTIST not in body.replace(" ", ""):
        raise RuntimeError("qq-artist-tag-mismatch")
    ti = re.search(r"\[ti:([^\]]*)\]", body)
    if ti:
        # Prefix, not equality: several album tracks legitimately carry an annotation in
        # their own title (「对不起 (统一茶饮料 广告曲)」 IS the 范特西 track - the song was
        # written as an ad jingle and then included on the album). Equality refused the
        # real lyric; a prefix still refuses a different song, and the [ar:] tag above
        # has already pinned the artist.
        if not norm_song(ti.group(1)).startswith(want):
            raise RuntimeError("qq-title-tag-mismatch: %s" % ti.group(1))
    rows, dropped = parse_lrc(body)
    if len(rows) < 20:
        raise RuntimeError("qq-too-few-lines: %d" % len(rows))
    return rows, dropped, "https://y.qq.com/n/ryqq/songDetail/" + mid


def is_credit(text):
    t = text.strip()
    if not t:
        return True
    m = re.match(r"^([^:：]{1,12})\s*[:：]\s*(.*)$", t)
    if m and m.group(1).strip() in CREDIT_KEYS:
        return True
    # 2026-11-06: QQ lyric bodies open with a "<song> - <artist> (romanized)" title line
    # that carries a timestamp, so it survived as a fake lyric and would have been fed
    # to the word alignment. Any line naming the artist in that shape is a title, not a
    # lyric line.
    if ARTIST in t and re.search(r"\s-\s", t) and len(t) <= 40:
        return True
    return False


def parse_lrc(raw):
    """→ ([(t, text)], dropped_credits)"""
    rows, dropped = [], 0
    for ln in raw.splitlines():
        m = TS.match(ln.strip())
        if not m:
            continue
        frac = m.group(3) or "0"
        t = int(m.group(1)) * 60 + int(m.group(2)) + int(frac) / (100 if len(frac) == 2 else 1000)
        text = m.group(4).strip()
        if is_credit(text):
            if text:
                dropped += 1
            continue
        rows.append((round(t, 2), text))
    return rows, dropped


def stamp(t):
    m, s = divmod(t, 60)
    return "[%02d:%05.2f]" % (int(m), s)


def main(argv):
    auto = "--auto" in sys.argv[1:]
    names = [a for a in argv if not a.startswith("--")]
    if auto:
        return main_auto(names)
    if not argv:
        print("usage: lyrics_fetch_163.py <song> <id>   |   --auto [song ...] [--limit N]")
        return 2
    song, sid = argv[0], argv[1]
    return fetch_and_write(song, sid)


def fetch_and_write(song, sid):
    url = API % sid
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://music.163.com/"})
    data = json.load(urllib.request.urlopen(req, timeout=25))
    raw = (data.get("lrc") or {}).get("lyric") or ""
    rows, dropped = parse_lrc(raw)
    if len(rows) < 20:
        print("REFUSE %s: only %d lyric lines parsed from %s (raw=%dB, dropped=%d)"
              % (ascii(song), len(rows), url, len(raw), dropped))
        return 3
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    return write_lyrics(song, rows, dropped, url, now)


def write_lyrics(song, rows, dropped, source, now):
    header = "# title=%s\n# source=%s\n# fetched=%s (official lyric library, credits dropped=%d)\n" % (
        song, source, now, dropped)
    os.makedirs(LYR, exist_ok=True)
    with io.open(os.path.join(LYR, song + ".txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(header)
        for _, text in rows:
            f.write(text + "\n")
    with io.open(os.path.join(LYR, song + ".lrc"), "w", encoding="utf-8", newline="\n") as f:
        f.write(header)
        for t, text in rows:
            f.write("%s%s\n" % (stamp(t), text))
    print("WROTE %s lines=%d dropped_credits=%d first=%r last=%r"
          % (ascii(song), len(rows), dropped, rows[0][1], rows[-1][1]))
    return 0


def main_auto(names):
    """Resolve ids by name and fetch, one album track at a time.

    Default scope = every song that has an audio file but no lyrics yet, so a bare
    --auto run drains the backlog instead of needing a hand-kept list. --limit caps
    a single run (network politeness + a bounded queue card).
    """
    limit = 0
    argv = sys.argv[1:]
    if "--limit" in argv:
        try:
            limit = int(argv[argv.index("--limit") + 1])
        except Exception:  # noqa: BLE001
            limit = 0
        names = [n for n in names if n != str(limit)]
    base = os.path.dirname(os.path.abspath(__file__))
    audio = os.path.join(base, "audio")
    if not names:
        songs = []
        for f in sorted(os.listdir(audio)):
            if not f.endswith(".mp3") or not f.startswith(ARTIST + " - "):
                continue
            s = f[len(ARTIST + " - "):-4]
            if os.path.exists(os.path.join(LYR, s + ".lrc")) or os.path.exists(os.path.join(LYR, s + ".txt")):
                continue
            songs.append(s)
        names = songs
    if limit:
        names = names[:limit]
    print("AUTO queue=%d" % len(names), flush=True)
    wrote = missed = 0
    for s in names:
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        sid, alts, err = search_ids(s)
        if sid:
            try:
                rc = fetch_and_write(s, sid)
            except Exception as e:  # noqa: BLE001
                print("ERR %s id=%s %s" % (ascii(s), sid, e), flush=True)
                rc = 9
            if rc == 0:
                wrote += 1
                time.sleep(0.6)
                continue
        # second source: QQ Music (owns the real album tracks; tags self-verify)
        try:
            rows, dropped, src = fetch_qq(s)
            rc = write_lyrics(s, rows, dropped, src, now)
            wrote += 1 if rc == 0 else 0
        except Exception as e:  # noqa: BLE001
            missed += 1
            print("MISS %s (163=%s) qq=%s candidates=%r" % (ascii(s), err, e, alts), flush=True)
        time.sleep(0.6)
    print("AUTO DONE wrote=%d missed=%d" % (wrote, missed), flush=True)
    return 0 if wrote else 2


def selftest():
    ok = 0
    fixture = ("[00:00.000] 作词 : 周杰伦\n[00:01.000] 作曲 : 周杰伦\n"
               "[00:28.950]故事的小黄花\n[00:32.380]从出生那年就飘着\n"
               "[00:35.870]\n[00:39.370]童年的荡秋千\n")
    rows, dropped = parse_lrc(fixture)
    # L1 credits dropped, blank lines dropped
    if [r[1] for r in rows] == ["故事的小黄花", "从出生那年就飘着", "童年的荡秋千"] and dropped == 2:
        ok += 1
        print("selftest L1 credit/blank filter PASS (dropped=%d)" % dropped)
    else:
        print("selftest L1 FAIL rows=%r dropped=%d" % (rows, dropped))
    # L2 timestamps preserved
    if rows[0][0] == 28.95 and stamp(rows[0][0]) == "[00:28.95]":
        ok += 1
        print("selftest L2 timestamp round-trip PASS")
    else:
        print("selftest L2 FAIL %r" % (rows[0],))
    # L3 a non-credit colon line survives (歌词里的冒号不是 credit)
    rows2, _ = parse_lrc("[00:10.000]我说：走吧\n")
    if rows2 and rows2[0][1] == "我说：走吧":
        ok += 1
        print("selftest L3 lyric-colon kept PASS")
    else:
        print("selftest L3 FAIL %r" % (rows2,))
    print("selftest: %d/3 PASS" % ok)
    return 0 if ok == 3 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    sys.exit(main([a for a in sys.argv[1:] if not a.startswith("--")]))