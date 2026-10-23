# -*- coding: utf-8 -*-
"""fullchain_audit.py —— 全链条机器体检（一次跑完所有可测项）

覆盖：时长/帧率 · 响度 · 硬跳 · 孤岛 · 重复帧 · 场景切点 · 节奏分布 ·
      黑场 · 近黑镜 · 字幕资产（繁简混排）· 素材索引一致性
不可机测项（人脸一致性/鬼影/构图）明确列为"需人工或多模态"。
"""
import json, os, re, subprocess, sys
import numpy as np

FPS = 24.0
VIDEO = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\full_mv_v601.mp4"
PLAN = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv-album-001-jay\plan-cuts-mv0001-v5.json"
ASS = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\lyric_track.ass"
IDX = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv-album-001-jay\ASSET-INDEX.jsonl"
sys.path.insert(0, r"C:\Users\sjs20\Desktop\FluxGroup\Tools")
import release_gate as RG

R = {}
WARN = []


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=nb_frames,width,height,r_frame_rate",
                        "-show_entries", "format=duration,size,bit_rate",
                        "-of", "default=noprint_wrappers=1", path],
                       capture_output=True, text=True, errors="replace")
    return dict(l.split("=", 1) for l in r.stdout.strip().splitlines() if "=" in l)


def main():
    meta = probe(VIDEO)
    frames = int(meta.get("nb_frames", 0)); dur = float(meta.get("duration", 0))
    print("=== 全链条体检 ===")
    print("文件 %s" % os.path.basename(VIDEO))
    print("① 规格：%sx%s / %s fps / %d 帧 / %.2fs / %.1f MB" % (
        meta.get("width"), meta.get("height"), meta.get("r_frame_rate"), frames, dur,
        int(meta.get("size", 0)) / 1048576))
    R["规格"] = (frames == 5623 and abs(dur - 234.25) < 0.2)
    if not R["规格"]:
        WARN.append("规格不符（目标 5623 帧 / 234.25s）")

    # ② 响度
    I, lra, tp = RG.loudness(VIDEO)
    ok = (I is not None and -15 <= I <= -13 and tp is not None and tp <= -1.0)
    print("② 响度：I=%s LUFS / LRA=%s / TP=%s dBFS → %s" % (I, lra, tp, "PASS" if ok else "FAIL"))
    R["响度"] = ok
    if not ok:
        WARN.append("响度或真峰值超限")

    # ③ 帧差：硬跳/孤岛/重复帧
    d = RG.frame_diffs(VIDEO)
    isl, spikes = RG.islands(d)
    dups = [k + 1 for k in range(len(d)) if d[k] < 0.35]
    plan = json.load(open(PLAN, encoding="utf-8"))["cuts"]
    off = [s / FPS for s in spikes if not any(abs(s / FPS - p) <= 0.35 for p in plan)]

    # ③b 物理判据（不依赖计划表）：
    #   真切点 = 跳变后画面保持改变（|f(s+3)-f(s-1)| 大）
    #   单帧弹出 = 跳变后画面回到原样（|f(s+3)-f(s-1)| 小）
    #   微叠化 = 孤岛跨岛净变化小（<12）
    need = set()
    for s in spikes:
        need |= {s - 1, s + 3}
    for a0, b0 in isl:
        need |= {a0 - 1, b0}
    need = {i for i in need if 0 <= i < frames}
    fr = {}
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", VIDEO, "-vf", "scale=240:136",
                          "-fps_mode", "passthrough", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=10**8)
    k = 0
    while True:
        b = p.stdout.read(240 * 136 * 3)
        if len(b) < 240 * 136 * 3:
            break
        if k in need:
            fr[k] = np.frombuffer(b, np.uint8).reshape(136, 240, 3).astype(np.int16)
        k += 1
    p.stdout.close(); p.wait()

    pops, steps, realcuts = [], [], []
    for s in spikes:
        if s - 1 not in fr or s + 3 not in fr:
            continue
        d4 = float(np.abs(fr[s + 3] - fr[s - 1]).mean())
        if d4 < 12:
            pops.append((s, d4))          # 单帧弹出：画面弹回原样
        elif d4 < 22:
            steps.append((s, d4))         # 内容微跳：画面换了一小块并保持
        else:
            realcuts.append((s, d4))      # 真切点

    bad_isl = []
    for a0, b0 in isl:
        if a0 - 1 in fr and b0 in fr:
            d3 = float(np.abs(fr[b0] - fr[a0 - 1]).mean())
            if d3 < 12:
                bad_isl.append((a0, b0, d3))

    print("③ 切点：突跳 %d = 真切点 %d + 内容微跳 %d + 单帧弹出 %d｜微叠化真缺陷 %d｜重复帧 %d" % (
        len(spikes), len(realcuts), len(steps), len(pops), len(bad_isl), len(dups)))
    print("   陈旧计划表对照（v5 时代，v600 起已不同源，仅参考）：非计划 %d" % len(off))
    R["单帧弹出"] = len(pops) == 0
    R["微叠化"] = len(bad_isl) == 0
    if pops:
        WARN.append("单帧弹出 %d 处（%s）" % (len(pops), ", ".join("%.2fs" % (s / FPS) for s, _ in pops[:10])))
    if steps:
        WARN.append("内容微跳 %d 处（源内跳变，需重烧该镜，禁靠混合修）：%s" % (
            len(steps), ", ".join("%.2fs" % (s / FPS) for s, _ in steps[:12])))
    if bad_isl:
        WARN.append("微叠化真缺陷 %d 处（%s）" % (
            len(bad_isl), ", ".join("%.2fs" % (a0 / FPS) for a0, _, _ in bad_isl[:10])))

    # ④ 场景切点 vs 计划
    cuts, err = RG.detect_cuts(VIDEO)
    if err:
        print("④ 场景检测不可用")
    else:
        print("④ 场景切点：检测 %d / 计划 %d" % (len(cuts), len(plan)))

    # ⑤ 节奏分布
    bounds = [0.0] + plan + [dur]
    lens = [bounds[i + 1] - bounds[i] for i in range(len(bounds) - 1)]
    sd = float(np.std(lens))
    def seg(a, b):
        v = [(x, bounds[i], bounds[i + 1]) for i, x in enumerate(lens) if a <= bounds[i] < b]
        return (sum(x for x, _, _ in v), len(v), (sum(x for x, _, _ in v) / len(v)) if v else 0)
    c1 = seg(77.3, 108.2); c2 = seg(141.8, 171.7); br = seg(172.5, 187.3)
    print("⑤ 节奏：σ=%.3fs（门线 ≥1.8）｜副歌1均长 %.2fs｜副歌2 %.2fs｜桥段 %.2fs" % (sd, c1[2], c2[2], br[2]))
    R["节奏"] = sd >= 1.8 and c1[2] <= 1.6 and c2[2] <= 1.6 and br[2] >= 4.0
    if not R["节奏"]:
        WARN.append("节奏不达标 σ=%.2f 副歌 %.2f/%.2f 桥段 %.2f" % (sd, c1[2], c2[2], br[2]))

    # ⑥ 黑场 / 近黑
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", VIDEO, "-vf",
                        "blackdetect=d=0.15:pix_th=0.10", "-an", "-f", "null", "-"],
                       capture_output=True, text=True, errors="replace")
    blacks = re.findall(r"black_start:([\d.]+)", r.stderr)
    print("⑥ 黑场：%d 段（%s）" % (len(blacks), ", ".join("%.2f" % float(x) for x in blacks[:6])))

    # ⑦ 字幕资产：繁简混排
    txt = open(ASS, encoding="utf-8", errors="replace").read()
    lines = re.findall(r"Dialogue: [^,]+,[^,]+,[^,]+,([^,]*),.*?,(.+)$", txt, re.M)
    body = "".join(l[1] for l in lines)
    trad = set("愛這裡個來時說為國學發現實們麼樣對開關無聲東車長門問間點還將從會後過還")
    hit = sum(body.count(ch) for ch in trad)
    print("⑦ 字幕：%d 句，繁体字出现 %d 次" % (len(lines), hit))
    R["字幕字形"] = hit == 0
    if hit:
        WARN.append("字幕出现繁体字 %d 次（与标题卡繁体并存，需确认是否混排）" % hit)

    # ⑧ 素材索引一致性
    miss = []
    n = 0
    if os.path.exists(IDX):
        for line in open(IDX, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            j = json.loads(line); n += 1
            src = str(j.get("src", "")).replace("/", "\\")
            if "\\" in src and not os.path.exists(src):
                miss.append(os.path.basename(src))
    print("⑧ 素材索引：%d 条，缺失 %d（%s）" % (n, len(miss), ", ".join(miss[:5])))
    R["素材索引"] = len(miss) == 0

    # 汇总
    print("\n=== 判定 ===")
    passed = sum(1 for v in R.values() if v)
    for k, v in R.items():
        print("  %-8s %s" % (k, "PASS" if v else "FAIL"))
    print("\n需人工/多模态审：人脸一致性(#20/#45/#64/#69)、鬼影、构图、转场语法")
    print("\n问题清单：")
    for w in WARN:
        print("  - " + w)

    out = os.path.join(r"D:\FleetWorker\review", "fullchain-audit.json")
    json.dump({"video": VIDEO, "pass": R, "warnings": WARN}, open(out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n结果已存", out)


if __name__ == "__main__":
    main()