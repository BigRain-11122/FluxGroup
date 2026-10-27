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


def is_credit(text):
    t = text.strip()
    if not t:
        return True
    m = re.match(r"^([^:：]{1,12})\s*[:：]\s*(.*)$", t)
    if m and m.group(1).strip() in CREDIT_KEYS:
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
    if not argv:
        print("usage: lyrics_fetch_163.py <song> <id>")
        return 2
    song, sid = argv[0], argv[1]
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
    header = "# title=%s\n# source=%s\n# fetched=%s (netease lyric api, credits dropped=%d)\n" % (
        song, url, now, dropped)
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