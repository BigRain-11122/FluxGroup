# -*- coding: utf-8 -*-
# make_lyric_ass.py — 全曲逐句歌词 ASS 字幕层生成器
# O-20261017-1020 V5.1 修片令·CEO 痛点②「唱歌的字我看不见」修复正身
# 词面定谳（2026-10-17 10:3x·多源交叉实录）：
#   语言（非预言：followlyrics 两词条全文两处均「难解的语言」+「难解的预言」全网零出）
#   祭司（多站一致）；漫延（两站四出一致·非「蔓延」）
#   「传说就成了永垂不朽的诗篇」两遍同句（whisper seg11/seg27 转写同长互证；
#     1633614 LRC 第二遍「不朽」为孤证弃用）
# §四映射表三处修正（whisper 词级实证·本窗 10:3x）：
#   seg36=我感到很疲倦离家乡还是很远（12 词 1:1 全窗对齐·「一切又重演」不在窗内）
#   seg37=害怕再也不能回到你身边（§四误排副歌句·whisper 10 词对齐）
#   seg46/47=爱在西元前×2 单行（尾段 gap 0.6s 不足容「一切又重演」·6993229 词面无此句）
#   副歌2/尾副歌结尾均无「一切又重演」（两站词面+whisper 无捕获互证·字幕宁缺勿错）
# 时间=whisper 段界（lyric_lines_r1017.json·r1017 实测·幻觉段 25.8 Zither Harp 跳过）
# 双行分割=音节比例目标点 snap 到最近 whisper 词尾（音节比例优先于 §四手派比例·更贴唱词）
# 样式=V5-TYPOGRAPHY 延续：SimSun Bold 56px 金 #E9C87A·软暗晕(深暖 Outline+\blur4·禁硬描边)
#   Alignment 2 底部居中 MarginV 40·每行 \fad(180,140)·尾句渐隐 \fad(180,700)
import json, os, sys
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
WAVJSON = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\audio\lyric_lines_r1017.json"
OUT = os.path.join(HERE, "lyric_track.ass")

# ---- 47 段映射表：(t0, t1, 行1, 行2或None)  时间=whisper 段界·文本=官方词面定谳版 ----
SEGS = [
    # 主歌1
    (31.10, 34.70, "古巴比伦王颁布了", "汉摩拉比法典"),
    (34.70, 37.00, "刻在黑色的玄武岩", None),
    (37.00, 38.92, "距今已经三千七百多年", None),
    (38.92, 42.42, "你在橱窗前", "凝视碑文的字眼"),
    (42.42, 46.66, "我却在旁静静欣赏", "你那张我深爱的脸"),
    (46.66, 50.54, "祭司神殿征战", "弓箭是谁的从前"),
    (50.54, 54.24, "喜欢在人潮中", "你只属于我的那画面"),
    (54.24, 58.44, "经过苏美女神身边", "我以女神之名许愿"),
    (58.44, 61.98, "思念像底格里斯河般的漫延", None),
    (61.98, 68.86, "当古文明只剩下难解的语言", None),
    (68.86, 74.60, "传说就成了永垂不朽的诗篇", None),
    # 副歌1
    (77.32, 80.16, "我给你的爱写在西元前", None),
    (80.16, 83.46, "深埋在美索不达米亚平原", None),
    (85.00, 87.72, "几十个世纪后出土发现", None),
    (87.72, 91.08, "泥板上的字迹依然清晰可见", None),
    (92.56, 95.24, "我给你的爱写在西元前", None),
    (95.24, 98.54, "深埋在美索不达米亚平原", None),
    (100.12, 102.88, "用楔形文字刻下了永远", None),
    (102.88, 106.20, "那已风化千年的誓言", None),
    (106.20, 108.22, "一切又重演", None),
    # 主歌2
    (110.52, 113.04, "祭司神殿征战", None),
    (113.04, 114.78, "弓箭是谁的从前", None),
    (114.78, 118.54, "喜欢在人潮中", "你只属于我的那画面"),
    (118.54, 122.82, "经过苏美女神身边", "我以女神之名许愿"),
    (122.82, 126.32, "思念像底格里斯河般的漫延", None),
    (127.04, 132.38, "当古文明只剩下难解的语言", None),
    (133.04, 138.64, "传说就成了永垂不朽的诗篇", None),
    # 副歌2（结尾无「一切又重演」·直入桥段——两站词面+whisper 互证）
    (141.82, 144.54, "我给你的爱写在西元前", None),
    (144.54, 147.84, "深埋在美索不达米亚平原", None),
    (149.38, 152.10, "几十个世纪后出土发现", None),
    (152.10, 155.38, "泥板上的字迹依然清晰可见", None),
    (156.90, 159.66, "我给你的爱写在西元前", None),
    (159.66, 162.88, "深埋在美索不达米亚平原", None),
    (164.48, 167.22, "用楔形文字刻下了永远", None),
    (167.22, 170.64, "那已风化千年的誓言", None),
    # 桥段（§四修正·seg36 词级 1:1 对齐单行）
    (171.74, 177.82, "我感到很疲倦离家乡还是很远", None),
    (177.82, 183.98, "害怕再也不能回到你身边", None),
    # 尾副歌
    (187.00, 190.18, "我给你的爱写在西元前", None),
    (190.18, 193.04, "深埋在美索不达米亚平原", None),
    (194.74, 197.52, "几十个世纪后出土发现", None),
    (197.52, 200.82, "泥板上的字迹依然清晰可见", None),
    (200.82, 205.16, "我给你的爱写在西元前", None),
    (205.16, 208.02, "深埋在美索不达米亚平原", None),
    (209.92, 212.68, "用楔形文字刻下了永远", None),
    (212.68, 215.92, "那已风化千年的誓言", None),
    # 尾声（§四修正·双句单行·无「一切又重演」）
    (216.92, 221.66, "爱在西元前", None),
    (221.66, 228.92, "爱在西元前", None),
]
LAST_FADE = (221.66, 228.92)   # 尾句渐隐窗（\fad(180,700)）


def syl(s):
    return len([c for c in s if not c.isspace()])


def fmt_t(sec):
    h = int(sec // 3600)
    m = int(sec % 3600 // 60)
    s = sec - int(sec // 3600) * 3600 - int(sec % 3600 // 60) * 60
    return "%d:%02d:%05.2f" % (h, m, s)


def main():
    data = json.load(open(WAVJSON, encoding="utf-8"))["segments"]

    def find_words(t0, t1):
        best, bo = None, 0.0
        for s in data:
            ov = min(s["end"], t1) - max(s["start"], t0)
            if ov > bo:
                best, bo = s, ov
        if not best or bo <= 0:
            return None
        return [(w[1], w[2]) for w in (best.get("words") or []) if w[2] > w[1] + 0.01]

    # 段界对账：每段须与某 whisper 段窗吻合（±0.06）
    for (t0, t1, _, _) in SEGS:
        if not any(abs(s["start"] - t0) < 0.06 and abs(s["end"] - t1) < 0.06 for s in data):
            print("WARN seg window not matched in whisper: %.2f-%.2f" % (t0, t1))

    events = []   # (start, end, text, split_src)
    for (t0, t1, l1, l2) in SEGS:
        if l2 is None:
            events.append((t0, t1, l1, "-"))
            continue
        n1, n2 = syl(l1), syl(l2)
        target = round(t0 + (t1 - t0) * n1 / (n1 + n2), 3)
        split, src = target, "ratio"
        ws = find_words(t0, t1)
        if ws:
            ends = [e for (_, e) in ws if t0 + 0.25 <= e <= t1 - 0.25]
            if ends:
                cand = min(ends, key=lambda e: abs(e - target))
                if abs(cand - target) <= 0.60:
                    split, src = round(cand, 2), "word"
        events.append((t0, split, l1, src))
        events.append((split, t1, l2, src))

    # 事件自检：升序·无重叠·最短行
    for i in range(1, len(events)):
        assert events[i][0] >= events[i - 1][1] - 0.001, "overlap at %d" % i
    shortest = min(events, key=lambda e: e[1] - e[0])
    print("EVENTS=%d  first=%.2f last=%.2f  shortest=%.2fs [%s]" % (
        len(events), events[0][0], events[-1][1], shortest[1] - shortest[0], shortest[2]))

    hdr = (
        "[Script Info]\n"
        "; generated by make_lyric_ass.py (O-20261017-1020 V5.1)\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1344\n"
        "PlayResY: 768\n"
        "ScaledBorderAndShadow: yes\n"
        "WrapStyle: 0\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Lyr,SimSun,56,&H007AC8E9,&H000000FF,&H00050E1A,&H00000000,-1,0,0,0,100,100,0,0,1,3.4,1.4,2,40,40,40,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = [hdr]
    for (st, en, tx, src) in events:
        fade = "\\fad(180,700)" if (st, en) == LAST_FADE else "\\fad(180,140)"
        lines.append("Dialogue: 0,%s,%s,Lyr,,0,0,0,,{%s\\blur4}%s\n" % (fmt_t(st), fmt_t(en), fade, tx))
    with open(OUT, "w", encoding="utf-8-sig") as f:
        f.writelines(lines)

    print("SAVED -> " + OUT)
    print("%-4s %-9s %-9s %-6s %-4s %s" % ("idx", "start", "end", "dur", "src", "text"))
    for i, (st, en, tx, src) in enumerate(events, 1):
        print("%-4d %-9.2f %-9.2f %-6.2f %-4s %s" % (i, st, en, en - st, src, tx))
    print("DOUBLE-SEGS=%d" % sum(1 for (_, _, l1, l2) in SEGS if l2))


if __name__ == "__main__":
    main()
