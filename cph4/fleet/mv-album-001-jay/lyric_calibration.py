# -*- coding: utf-8 -*-
# lyric_calibration.py — 词面校准批 (MV 产线律 2026-10-13: whisper 词面误听 → 官方词面正身)
# 输入: lyrics/<曲>.txt(官方词面, # 开头为头注) / lyrics/<曲>.lrc(带行时间戳的官方对齐, 优先直读)
#       anchors/<锚>.json(whisper 词级时序: dict{words,lines} 或 list[{start,end,text}])
# 输出: anchors/<曲>-calibrated.txt/.json — 官方词面行 + 行级时间窗 (词面=官方正身, 时序=whisper/LRC)
# 算法: whisper 行段 × 官方行 全局单调 DP 对齐 (Needleman-Wunsch) — 对重复副歌逐实例配对、
#       容忍误听词/合并行/拆分行/乐器段; 未覆盖行用前后邻行时间窗插值并标 [approx]。
import difflib, json, os, re, sys
import zhconv
sys.stdout.reconfigure(errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
LYR = os.path.join(BASE, "lyrics")
ANC = os.path.join(BASE, "anchors")
SONGS = {"星晴": "星晴", "可爱女人": "可爱女人", "龙卷风": "龙卷风",
         "简单爱": "jiandanan", "开不了口": "kaibuliaokou", "安静": "安静-words",
         "斗牛": "斗牛", "黑色幽默": "黑色幽默", "晴天": "晴天-words",
         # POOL-0023 第二批 7 首（2026-10-29 事件班登记）：5 首现有官方 .lrc 直读
         "伊斯坦堡": "伊斯坦堡-words", "印第安老斑鸠": "印第安老斑鸠-words",
         "反方向的钟": "反方向的钟-words", "娘子": "娘子-words", "完美主义": "完美主义-words"}


def norm(s):
    return re.sub(r"\s+", "", s or "")


def simp(s):
    # strip whitespace + unify traditional/simplified variants for matching
    return zhconv.convert(norm(s), "zh-cn")


def load_lyric_rows(path):
    rows = []
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        rows.append(ln)
    return rows


def load_segs(anchor_json):
    data = json.load(open(anchor_json, encoding="utf-8"))
    segs = []
    if isinstance(data, dict):
        for L in data.get("lines") or []:
            if L.get("text"):
                segs.append((L.get("t0"), L.get("t1"), simp(L.get("text", ""))))
    else:
        for it in data:
            if isinstance(it, dict) and it.get("text"):
                segs.append((it.get("start"), it.get("end"), simp(it.get("text", ""))))
    return [s for s in segs if s[2]]


def from_lrc(path):
    rows = []
    for ln in open(path, encoding="utf-8"):
        m = re.match(r"\[(\d+):(\d+)(?:[.:](\d{1,3}))?\](.*)$", ln.strip())
        if not m:
            continue
        frac = m.group(3) or "0"
        t = int(m.group(1)) * 60 + int(m.group(2)) + int(frac) / (100 if len(frac) == 2 else 1000)
        txt = m.group(4).strip()
        if txt:
            rows.append((round(t, 2), None, txt, False))
    return rows


def from_whisper(anchor_json, lyric_rows):
    segs = load_segs(anchor_json)
    if not segs:
        return None
    tgt = [simp(t) for t in lyric_rows]
    m, n = len(segs), len(tgt)
    # DP: 0=match(seg_i,line_j) 1=skip_seg(乐器/幻觉段) 2=skip_line(未覆盖行)
    GAP_SEG, GAP_LINE = -0.10, -0.40
    dp = [[0.0] * (n + 1) for _ in range(m + 1)]
    bt = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        dp[i][0] = dp[i - 1][0] + GAP_SEG
        bt[i][0] = 1
    for j in range(1, n + 1):
        dp[0][j] = dp[0][j - 1] + GAP_LINE
        bt[0][j] = 2
    for i in range(1, m + 1):
        si = segs[i - 1][2]
        sm = difflib.SequenceMatcher(None, si, "")
        for j in range(1, n + 1):
            sm.set_seq2(tgt[j - 1])
            s = 2.0 * (sm.ratio() - 0.5)
            a = dp[i - 1][j - 1] + s
            b = dp[i - 1][j] + GAP_SEG
            c = dp[i][j - 1] + GAP_LINE
            if a >= b and a >= c:
                dp[i][j], bt[i][j] = a, 0
            elif b >= c:
                dp[i][j], bt[i][j] = b, 1
            else:
                dp[i][j], bt[i][j] = c, 2
    res = [None] * n
    i, j = m, n
    while i > 0 or j > 0:
        op = bt[i][j] if (i > 0 and j > 0) else (1 if i > 0 else 2)
        if op == 0:
            res[j - 1] = segs[i - 1]
            i, j = i - 1, j - 1
        elif op == 1:
            i -= 1
        else:
            j -= 1
    out = []
    for j, txt in enumerate(lyric_rows):
        seg = res[j]
        if seg:
            out.append((seg[0], seg[1], txt, False))
        else:
            prev_t = next((res[k][1] for k in range(j - 1, -1, -1) if res[k]), None)
            next_t = next((res[k][0] for k in range(j + 1, n) if res[k]), None)
            out.append((prev_t, next_t, txt, True))
    return out


def emit(song, rows):
    rows = list(rows)
    for i, (t0, t1, txt, approx) in enumerate(rows):
        if t0 is not None and t1 is None:  # LRC only carries line-start times
            nxt = rows[i + 1][0] if i + 1 < len(rows) else None
            t1 = nxt if nxt is not None and nxt > t0 else (t0 + 3.0)
            rows[i] = (t0, round(t1, 2), txt, approx)
    jrows = [{"t0": t0, "t1": t1, "text": txt, "approx": approx} for t0, t1, txt, approx in rows]
    with open(os.path.join(ANC, song + "-calibrated.json"), "w", encoding="utf-8") as f:
        json.dump(jrows, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ANC, song + "-calibrated.txt"), "w", encoding="utf-8") as f:
        for t0, t1, txt, approx in rows:
            if t0 is None:
                f.write("   --.- -    --.- | %s\n" % txt)
            else:
                f.write("%7.2f - %7.2f | %s%s\n" % (t0, t1, txt, "  [approx]" if approx else ""))
    exact = sum(1 for r in rows if r[0] is not None and not r[3])
    approx_n = sum(1 for r in rows if r[0] is not None and r[3])
    none_n = sum(1 for r in rows if r[0] is None)
    return exact, approx_n, none_n, len(rows)


# argv song filter: `python lyric_calibration.py 斗牛 黑色幽默` processes only named
# songs (idempotent re-run of existing faces stays byte-identical); bare run = all SONGS.
only = [a for a in sys.argv[1:] if a]
targets = {k: v for k, v in SONGS.items() if not only or k in only}

for song, anchor in targets.items():
    lrc = os.path.join(LYR, song + ".lrc")
    txt = os.path.join(LYR, song + ".txt")
    aj = os.path.join(ANC, anchor + ".json")
    if os.path.exists(lrc):
        rows = from_lrc(lrc)
        if rows:
            e, a, x, total = emit(song, rows)
            print("CALIBRATED %s mode=lrc exact=%d approx=%d none=%d total=%d"
                  % (ascii(song), e, a, x, total))
            continue
    rows_l = load_lyric_rows(txt) if os.path.exists(txt) else []
    if not rows_l:
        print("MISS lyrics %s" % ascii(song))
        continue
    if not os.path.exists(aj):
        print("MISS anchor %s" % ascii(anchor))
        continue
    rows = from_whisper(aj, rows_l)
    if rows is None:
        print("ALIGN EMPTY %s" % ascii(song))
        continue
    e, a, x, total = emit(song, rows)
    print("CALIBRATED %s mode=whisper exact=%d approx=%d none=%d total=%d"
          % (ascii(song), e, a, x, total))
print("ALL DONE")
