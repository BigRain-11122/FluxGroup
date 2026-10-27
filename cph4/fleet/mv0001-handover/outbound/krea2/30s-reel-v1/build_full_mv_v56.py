# -*- coding: utf-8 -*-
# build_full_mv_v56.py — V5.6 CEO 终审快改装配器（V5.5 反馈四条·2026-10-18）
# CEO 令：
#   ① 片头歌名卡「歌曲名和大喵没鱼吃」位置/字体不好看、要大一点、构图/字体/颜色好好设计
#   ②「我的意思开头几个写歌镜头不连贯，剪辑也不好，导演你是专业的，你给我去弄」
#   ③ 后段「边写歌边唱」镜头逻辑问题可换
#   ④ 其他全部通过——快速修改完给成品、高效
# 四改（v55 全链正典零回归：XFS 14 点/T 桥/尾声明/FX 28 位点/fin/loudnorm/alimiter 全不动）：
#   ① 开场 0-17.50 重导重剪六拍（导演席定稿·CEO 全权委托）：
#      A  INT1_desk_breath    0.00-3.00 @0.85 伏案书写（底拍·源 0-2.55s）
#      B  INT2_paper_fight    3.00-5.80 @0.92 停笔苦思（双手压纸=「卡住」转折）
#      R  V56_R_rubbing_macro 5.80-7.40 @1.00 拓片微距（INT3 源 0.30-1.90s punch-in 1.59x 真像素）
#      C  INT3_photo_stare    7.40-11.00 @0.85 举拓片凝视（源 1.90s 起续接段——R 同动作跨景别 matched-cut）
#      P  V56_P_pen_macro     11.00-13.40 @0.95 笔尖落笔（INT1 源 2.60-4.88s punch-in 2.1x·与 A 零重叠段）
#      E2 INT5_head_bow_E2    13.40-17.50 @0.85 靠背抬眼（源 1.50s 起·避首帧划痕·墙面亮块 delogo）
#      → S1_fire_wake 17.50-21.90 原样（火把点亮楔文石壁=「火焰苏醒」节拍本体·21.90 fade 锚零漂）
#      弃用镜：INT4_rubbing_glow（螺旋笔记本道具冲突+头顶撞边）/INT5 源 0-1.5s（划痕伪影段）
#   ② 字卡 v56 大字版（make_title_card_v56_r1018.py·主标 140px 画宽 57%·居中·双层暗衬底
#      ·真鎏金楔形铭带+光晕·窗 4.10-7.40=叠 B 尾段+R 微距·字离后 C 纸面全净）
#   ③ SING3b_v4 源覆盖 → V56_SING1_reprise（SING1 火炬尾段 2.88-4.88s·punch-in 1.12x+微压暗
#      ·与 78s 头段零重叠·「出土后古声重现」回环读法=CEO 可换令正法）
#   ④ 尾声明 tail_credit_v55 原样（CEO「其他全部通过」）
# 用法：python build_full_mv_v56.py（PROXY 禁跑闸承 v55；新源五件=v56src/）
import os, subprocess, sys, re
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
os.chdir(HERE)                      # ass 滤镜用相对文件名（lyric_track.ass）
sys.path.insert(0, HERE)
import build_full_mv_v2 as v2
import build_full_mv_v3 as v3m
import build_full_mv_v5 as v5

PROXY = os.environ.get("PROXY") == "1"
if PROXY:
    raise SystemExit("V5.6 final-only: block cache is 768P; PROXY re-emits 540p over cache - forbidden")
DRYRUN = os.environ.get("DRYRUN") == "1"
NO_SIL4 = os.environ.get("NO_SIL4") == "1"
FF = v2.FF
W, H, CRF, PRE = v5.W, v5.H, v5.CRF, v5.PRE
FAST = v5.FAST

SIL1_DUR_V51 = 2.14                  # 29.00→31.14（S4 吞没+SIL1 窗延·v51 正典承）
# V5.6 XFS 14 点（与 v55 逐点相同·anchor 全不变=窗表零漂移）
XFS = [
    (21.90,  "fade",  0.36),   # v51 正典微叠化
    (38.82,  "fade",  0.40),   # A→T
    (40.22,  "fade",  0.40),   # T→G0
    (44.00,  "hblur", 0.40),   # b09 入间奏（V5.4.2 hblur 过门）
    (47.50,  "fade",  1.00),   # S10→N01
    (80.18,  "hblur", 0.40),   # B3a：近黑谷减半（C01→C02 风沙糊面）
    (102.88, "fade",  0.60),   # C08→C09
    (110.52, "fade",  1.10),   # B3b：千年主渡保最长档
    (126.32, "fade",  0.40),   # b24 亮度断崖叠化（V5.4.2 fx_leak 伴切）
    (131.72, "hblur", 0.50),   # R05→R06
    (152.00, "hblur", 0.30),   # B2：双头中帧遮蔽（D03b→SIL3）
    (187.26, "fade",  0.90),   # B04→E01a
    (191.60, "hblur", 0.36),   # B1：构图错位糊化（E01b→E01c 同碑跨千年）
    (219.84, "fade",  1.20),   # E04→Z01
]
assert len(XFS) == 14, "XFS count %d != 14" % len(XFS)
ASS_FILE = "lyric_track.ass"
D56 = os.path.join(v2.D_CUT, "v56")
os.makedirs(D56, exist_ok=True)
v5.D_CUT = D56                      # v5.emit_shot 内部段件/调色件落 v56 目录（全新缓存零 stale）

# ---- V5.6 新源（v56src/ 五件·真像素 punch-in/续接段/delogo 段·2026-10-18 预切） ----
V56SRC = os.path.join(HERE, "v56src")
V56_SOURCE_MAP = {
    "V56_R_rubbing_macro": "V56_R_rubbing_macro.mp4",
    "V56_P_pen_macro":     "V56_P_pen_macro.mp4",
    "INT3_photo_stare":    "V56_C_gaze_seg.mp4",        # C 续接段替原整镜（源 1.90s 起）
    "INT5_head_bow_E2":    "V56_E2_lookup_seg.mp4",     # E2 抬眼段（源 1.50s 起·delogo）
    "SING3b_v4":           "V56_SING1_reprise.mp4",     # 边写边唱镜替换（CEO 可换令）
}
for k, f in V56_SOURCE_MAP.items():
    assert os.path.isfile(os.path.join(V56SRC, f)), "FATAL v56src missing: %s -> %s" % (k, f)

MERGED_MAP = dict(v5.V5_SOURCE_MAP)
MERGED_MAP.update(V56_SOURCE_MAP)

def find_src_v56(fname):
    p = os.path.join(V56SRC, fname)
    if os.path.isfile(p):
        return p, "v56src"
    return v5.find_src_v5(fname)

# ---- V5.6 字层参数（v56 大字版·窗 4.10-7.30+出 0.6=7.40 全离） ----
TITLE_PNG = os.path.join(HERE, "title_card_v56.png")
TITLE_IN_ST, TITLE_WIN = 4.10, 3.30   # 4.10-7.40 驻留（B 尾段+R 微距上·C 纸面全净）
TITLE_IN_D, TITLE_OUT_D = 0.70, 0.60
TAIL_PNG = os.path.join(HERE, "tail_credit_v55.png")   # 尾声明 CEO 已过·原样
TAIL_ST, TAIL_DUR = 230.50, 3.75
TAIL_IN_D, TAIL_OUT_D = 1.20, 0.80


def build_rows_v51():
    """v5 行表 + SIL1 窗延（S4_crown 被 [29.0,31.14] 窗吞没自动消失·v51 正典承）。"""
    ins = []
    for x in v3m.V3_INSERTS:
        iid, fn, a, d, v = x
        if iid == "SIL1_v4b":
            d = SIL1_DUR_V51
        ins.append((iid, fn, a, d, v))
    v3m.V3_INSERTS = ins
    return v5.build_rows_v5()        # 内含 CLAMP{SING1,SIL2}+SPEED_OVERRIDE+啃洞切分


def build_rows_v56():
    """v51 行表为基 → 开场 0-17.50 六拍重导重剪（其余行零触碰）。"""
    rows = build_rows_v51()
    assert not any(r[0].startswith("S4_crown") for r in rows), "FATAL S4_crown row still present"
    rest = [r for r in rows if r[1] >= 17.5]
    assert rest and abs(rest[0][1] - 17.5) < 0.001 and rest[0][0] == "S1_fire_wake", \
        "FATAL S1 window moved: %s %.3f" % (rest[0][0], rest[0][1])
    sil1 = [r for r in rows if r[0].startswith("SIL1_v4b@")]
    assert sil1 and abs(sil1[0][2] - 31.14) < 0.001, "FATAL SIL1 window not extended"
    open_rows = [
        ["INT1_desk_breath",    0.00,  3.00, 0.85, "INT1_desk_breath_v5.mp4", False],
        ["INT2_paper_fight",    3.00,  5.80, 0.92, "INT2_paper_v5.mp4",       False],
        ["V56_R_rubbing_macro", 5.80,  7.40, 1.00, "V56_R_rubbing_macro.mp4", True],
        ["INT3_photo_stare",    7.40, 11.00, 0.85, "V56_C_gaze_seg.mp4",      True],
        ["V56_P_pen_macro",     11.00, 13.40, 0.95, "V56_P_pen_macro.mp4",    True],
        ["INT5_head_bow_E2",    13.40, 17.50, 0.85, "V56_E2_lookup_seg.mp4",  True],
    ]
    rows = sorted(open_rows + rest, key=lambda r: r[1])
    # 窗表铺满断言（零缝零叠）
    assert abs(rows[0][1]) < 0.001, "FATAL first row not at 0"
    for a, b in zip(rows, rows[1:]):
        assert abs(b[1] - a[2]) < 0.001, "FATAL window gap/overlap %s(%.3f) -> %s(%.3f)" % (a[0], a[2], b[0], b[1])
    return rows


def main():
    rows = build_rows_v56()
    print("V5.6 rows=%d  PROXY=%s DRYRUN=%s NO_SIL4=%s" % (len(rows), PROXY, DRYRUN, NO_SIL4), flush=True)

    # ---- 源解析（V5/V56 双映射·缺源 FATAL·J-32 律扩展口径） ----
    resolved = []
    for sid, t0, t1, v, src_file, is_new in rows:
        base_sid = sid.split("@")[0]
        want = MERGED_MAP.get(base_sid, src_file)
        src, kind = find_src_v56(want)
        if src is None:
            src, kind = v2.find_src(src_file), "legacy-fallback"
        if src is None:
            if base_sid in MERGED_MAP and not DRYRUN:
                raise SystemExit("FATAL mapped source missing: %s -> %s (DRYRUN=1 to substitute)" % (sid, want))
            if resolved:
                prev = resolved[-1]; prev[2] = t1
                print("FALLBACK-MERGE %s -> %s" % (sid, prev[0]), flush=True)
                continue
            raise SystemExit("FATAL first shot missing " + sid)
        if base_sid in v5.V5_SOURCE_MAP and base_sid not in V56_SOURCE_MAP and kind != "v5redo":
            if DRYRUN:
                print("DRY-SUB %s uses legacy %s (math-check only)" % (sid, os.path.basename(src)), flush=True)
            else:
                print("WARN %s fell back to legacy source" % sid, flush=True)
        resolved.append([sid, t0, t1, v, src, kind])
    n_v5 = sum(1 for r in resolved if r[5] == "v5redo")
    exp_v5 = sum(1 for r in rows if r[0].split("@")[0] in v5.V5_SOURCE_MAP
                 and r[0].split("@")[0] not in V56_SOURCE_MAP)
    n_56 = sum(1 for r in resolved if r[5] == "v56src")
    print("sources: v5redo=%d(exp %d) / v56src=%d" % (n_v5, exp_v5, n_56), flush=True)
    if not DRYRUN and n_v5 != exp_v5:
        raise SystemExit("FATAL v5redo source count %d != %d (J-32 extended)" % (n_v5, exp_v5))

    # ---- 分块（v55 正典：A1/A2/T 特例 + G0..G11） ----
    T_id = "T_glyphs"
    block_bounds = [a for (a, _, _) in XFS[3:]]
    A1_ids = [r[0] for r in resolved if r[1] < XFS[0][0] and r[0] != T_id]
    A2_ids = [r[0] for r in resolved if XFS[0][0] <= r[1] < XFS[1][0] and r[0] != T_id]
    G = [[] for _ in range(len(block_bounds) + 1)]
    for r in resolved:
        sid, t0 = r[0], r[1]
        if sid == T_id or t0 < 38.82:
            continue
        bi = len(G) - 1
        for i, b in enumerate(block_bounds):
            if t0 < b:
                bi = i; break
        G[bi].append(sid)
    for i, ids in enumerate(G):
        assert ids, "empty block G%d" % i
    assert A1_ids and A2_ids, "A1/A2 split failed"
    seq_blocks = [A1_ids, A2_ids, None] + G
    TAIL_EXT = {}
    for i, ids in enumerate(seq_blocks[:-1]):
        if ids:
            TAIL_EXT[ids[-1]] = XFS[i][2]
    a1_win = sum(r[2] - r[1] for r in resolved if r[1] < XFS[0][0])
    assert abs(a1_win - 21.90) < 0.01, "FATAL A1 windows %.3f != 21.90" % a1_win
    print("blocks: A1=%d A2=%d T=1 G=%s (total %d)  A1win=%.2f" % (
        len(A1_ids), len(A2_ids), [len(g) for g in G], 3 + len(G), a1_win), flush=True)
    print("tail-ext=%s" % {k: round(v, 2) for k, v in TAIL_EXT.items()}, flush=True)

    # ---- 发射全镜（块末镜带尾延·v56 全新缓存目录零 stale） ----
    cuts = {}
    for sid, t0, t1, v, src, kind in resolved:
        if sid == T_id:
            continue
        ext = TAIL_EXT.get(sid, 0.0)
        dst = os.path.join(D56, "v56_%s.mp4" % sid.replace("@", "_at_"))
        if os.path.isfile(dst) and (v5.dur_of(dst) or 0) > 0:
            print("REUSE %s" % os.path.basename(dst), flush=True)
            cuts[sid] = (dst, t0, t1, v)
            continue
        dst, pads = v5.emit_shot(sid, t0, t1, v, src, dst, ext=ext)
        if pads > 0:
            print("PAD-WARN %s tpad=%.2fs (source short%s)" % (sid, pads, " + tail-ext in fade" if ext else ""), flush=True)
        print("cut %-22s %.2fs@%.2fx [%s]%s" % (sid, round(t1 - t0 + ext, 4), v, kind,
              " +ext%.2f" % ext if ext else ""), flush=True)
        cuts[sid] = (dst, t0, t1, v)

    def concat_block(ids, name):
        outp = os.path.join(D56, name)
        if os.path.isfile(outp) and (v5.dur_of(outp) or 0) > 0:
            print("REUSE %s" % name, flush=True)
            return outp
        v2.concat([cuts[s][0] for s in ids], outp)
        return outp

    blocks = [concat_block(A1_ids, "v56_blockA1.mp4"), concat_block(A2_ids, "v56_blockA2.mp4")]
    # T 桥特例（v5 正典尾延律·与 v55 逐字同）
    t_raw = v2.find_src("KFT_glyphs.mp4")
    assert t_raw, "KFT_glyphs source missing"
    T_dst = os.path.join(D56, "v56_T18.mp4")
    if os.path.isfile(T_dst) and (v5.dur_of(T_dst) or 0) > 0:
        print("REUSE v56_T18.mp4", flush=True)
    else:
        base = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=24" % (W, H, W, H))
        interp = ("minterpolate=fps=48:mi_mode=mci,setpts=PTS/%.4f," % 0.90) if not FAST else ("setpts=PTS/%.4f," % 0.90)
        subprocess.run([FF, "-y", "-i", t_raw, "-an", "-vf", interp + base, "-t", "1.8000",
                        "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF),
                        "-pix_fmt", "yuv420p", T_dst], check=True, capture_output=True)
    blocks.append(T_dst)
    for i, ids in enumerate(G):
        blocks.append(concat_block(ids, "v56_blockG%d.mp4" % i))
    assert len(blocks) == 15, "block count %d != 15" % len(blocks)

    target = v2.FILM_END if not NO_SIL4 else v2.FILM_END - 1.08

    # ---- 帧锁定块长（partial-sum pinning·断言律 v1.1·承 v53 治本正典） ----
    def block_frame_targets():
        P_prev, outp, cum = 0, [], 0.0
        for (anchor, _, D) in XFS:
            cum += D
            Pk = int(round((anchor + cum) * 24))
            outp.append(Pk - P_prev)
            P_prev = Pk
        outp.append(int(round((target + cum) * 24)) - P_prev)
        return outp

    def frames_of(p):
        d = v5.dur_of(p)
        return int(round(d * 24)) if d else -1

    def pin_block(p, want_frames):
        got = frames_of(p)
        if got == want_frames:
            return p
        d = want_frames - got
        fixed = p[:-4] + "_fx.mp4"
        if os.path.isfile(fixed) and frames_of(fixed) == want_frames:
            print("REUSE %s" % os.path.basename(fixed), flush=True)
            return fixed
        vf = ("tpad=stop_mode=clone:stop_duration=%.6f" % (d / 24.0)) if d > 0 else \
             ("trim=end_frame=%d,setpts=PTS-STARTPTS" % (got + d))
        subprocess.run([FF, "-y", "-i", p, "-an", "-vf", vf, "-c:v", "libx264", "-preset", PRE,
                        "-crf", str(CRF), "-pix_fmt", "yuv420p", fixed], check=True, capture_output=True)
        print("BLOCK-PIN %s %s%d fr" % (os.path.basename(p), "+" if d > 0 else "", d), flush=True)
        return fixed

    BF = block_frame_targets()
    print("block-frames targets=%s" % BF, flush=True)
    blocks = [pin_block(b, BF[i]) for i, b in enumerate(blocks)]

    lens = [v5.dur_of(b) for b in blocks]
    print("block lens: " + " ".join("%.2f" % l for l in lens), flush=True)

    # ---- XF 链数学（14 点·链式 offset·窗内容零漂移自检） ----
    win_sum = {0: sum(cuts[s][2] - cuts[s][1] for s in A1_ids) + TAIL_EXT.get(A1_ids[-1], 0),
               1: sum(cuts[s][2] - cuts[s][1] for s in A2_ids) + TAIL_EXT.get(A2_ids[-1], 0)}
    for i, ids in enumerate(G):
        win_sum[3 + i] = sum(cuts[s][2] - cuts[s][1] for s in ids) + TAIL_EXT.get(ids[-1], 0)
    for i, L in enumerate(lens):
        expect = 1.80 if i == 2 else win_sum.get(i)
        if expect and abs(L - expect) > 0.06:
            print("WARN block%d len %.2f vs windows+ext %.2f" % (i, L, expect), flush=True)
    offsets, running = [], 0.0
    xfi = 0
    for bi in range(len(blocks)):
        running += lens[bi]
        if xfi < len(XFS):
            anchor, trans, D = XFS[xfi]
            off = round(running - D, 4)
            offsets.append((anchor, trans, D, off))
            if abs(off - anchor) > 0.05:
                raise SystemExit("FATAL xf-math: transition %d starts at %.3f but anchor %.3f" % (xfi, off, anchor))
            running -= D
            xfi += 1
    assert xfi == len(XFS), "unconsumed XFS entries"
    final_len = running
    print("XF offsets: " + " ".join("%.2f" % o[-1] for o in offsets), flush=True)
    print("final_len computed = %.2f" % final_len, flush=True)
    if abs(final_len - target) > 0.5:
        raise SystemExit("FATAL final_len %.2f vs target %.2f (xfade-chain collapse? missing shot?)" % (final_len, target))

    # ---- loudnorm pass1 测量（v5 正典两遍·EBU R128） ----
    p1 = subprocess.run([FF, "-i", v2.SONG, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=summary",
                         "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    m = {k: re.search(k + r":\s*([-+]?[\d.]+)", p1.stderr) for k in ("Input Integrated", "Input True Peak", "Input LRA", "Input Threshold")}
    ln = "loudnorm=I=-14:TP=-1.5:LRA=11"
    if all(m.values()):
        mi, mtp, mlra, mth = (float(m[k].group(1)) for k in ("Input Integrated", "Input True Peak", "Input LRA", "Input Threshold"))
        ln = "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%.2f:measured_TP=%.2f:measured_LRA=%.2f:measured_thresh=%.2f:linear=true" % (mi, mtp, mlra, mth)
        print("loudnorm pass1: I=%.2f TP=%.2f LRA=%.2f" % (mi, mtp, mlra), flush=True)
    else:
        print("loudnorm pass1 measure failed -> single-pass dynamic mode", flush=True)

    # ---- filter_complex：14 xfade 链 + 字层（v56 大字卡+尾声明）+ fin + ASS 后置 ----
    fin = ("colorbalance=rs=.03:gs=.005:bs=-.03:rm=.02:gm=.005:bm=-.02:rh=.04:gh=.01:bh=-.05,"
           "curves=all='0/0.010 0.5/0.50 1/0.99',eq=saturation=.97,vignette=PI/5,"
           "noise=alls=6:allf=t+u,format=yuv420p")
    fade_out_st = final_len - 2.25
    fc_parts = []
    cur = "0:v"
    for i, (anchor, trans, D, off) in enumerate(offsets):
        nxt = "%d:v" % (i + 1)
        outl = "x%d" % i
        fc_parts.append("[%s][%s]xfade=transition=%s:duration=%.2f:offset=%.2f[%s]" % (cur, nxt, trans, D, off, outl))
        cur = outl
    fc_parts.append("[%s]fade=t=in:st=0:d=0.5,fade=t=out:st=%.2f:d=2.0[base]" % (cur, fade_out_st))  # B5 承 v55
    SONG_IDX = len(blocks)                                  # 15：blocks 0..14
    TITLE_IDX, TAIL_IDX = SONG_IDX + 1, SONG_IDX + 2        # 16, 17
    fc_parts.append("[%d:v]scale=%d:%d,format=rgba,setpts=PTS+%.2f/TB,"
                    "fade=t=in:st=%.2f:d=%.2f:alpha=1,fade=t=out:st=%.2f:d=%.2f:alpha=1[tcard]"
                    % (TITLE_IDX, W, H, TITLE_IN_ST, TITLE_IN_ST, TITLE_IN_D,
                       TITLE_IN_ST + TITLE_WIN - TITLE_OUT_D, TITLE_OUT_D))
    fc_parts.append("[base][tcard]overlay=0:0[ov1]")
    fc_parts.append("[%d:v]scale=%d:%d,format=rgba,setpts=PTS+%.2f/TB,"
                    "fade=t=in:st=%.2f:d=%.2f:alpha=1,fade=t=out:st=%.2f:d=%.2f:alpha=1[tcred]"
                    % (TAIL_IDX, W, H, TAIL_ST, TAIL_ST, TAIL_IN_D,
                       TAIL_ST + TAIL_DUR - TAIL_OUT_D, TAIL_OUT_D))
    fc_parts.append("[ov1][tcred]overlay=0:0[ov2]")
    # ---- 特效伴切层（28 位点·与 v55 逐字相同） ----
    FXDIR = os.path.join(HERE, "fx_plates")
    FX_EVENTS = [
        ("fx_flash.png",  17.42, 0.13, 0.50, "static", (0.04, 0.07)),
        ("fx_dust.png",   28.76, 1.05, 0.35, "drift",  (0.35, 0.45)),
        ("fx_band.png",   38.62, 0.52, 0.85, "sweepL", (0.10, 0.16)),
        ("fx_band.png",   40.02, 0.52, 0.85, "sweepR", (0.10, 0.16)),
        ("fx_leak.png",   47.30, 0.95, 0.55, "static", (0.28, 0.35)),
        ("fx_smoke.png",  58.20, 1.05, 0.32, "drift",  (0.35, 0.45)),
        ("fx_dust.png",   68.62, 1.00, 0.35, "drift",  (0.35, 0.45)),
        ("fx_flash.png",  77.30, 0.14, 0.80, "static", (0.04, 0.08)),
        ("fx_smoke.png",  80.05, 0.90, 0.45, "drift",  (0.28, 0.35)),
        ("fx_flash.png",  91.02, 0.13, 0.75, "static", (0.04, 0.08)),
        ("fx_dust.png",   92.56, 1.35, 0.55, "drift",  (0.45, 0.55)),
        ("fx_dust.png",  102.80, 1.15, 0.50, "drift",  (0.40, 0.50)),
        ("fx_smoke.png", 110.42, 1.50, 0.42, "drift",  (0.45, 0.55)),
        ("fx_leak.png",  110.62, 1.45, 0.40, "static", (0.45, 0.50)),
        ("fx_dust.png",  131.62, 1.25, 0.50, "drift",  (0.40, 0.55)),
        ("fx_leak.png",  126.32, 0.90, 0.40, "static", (0.30, 0.40)),
        ("fx_flash.png", 141.72, 0.14, 0.80, "static", (0.04, 0.08)),
        ("fx_leak.png",  150.34, 0.95, 0.38, "static", (0.30, 0.40)),
        ("fx_smoke.png", 159.42, 0.95, 0.28, "drift",  (0.30, 0.40)),
        ("fx_dust.png",  168.30, 2.20, 0.35, "drift",  (0.70, 0.80)),
        ("fx_smoke.png", 176.76, 1.05, 0.30, "drift",  (0.35, 0.45)),
        ("fx_echo.png",  187.24, 0.58, 0.60, "static", (0.07, 0.38)),
        ("fx_echo2.png", 191.44, 0.30, 0.30, "static", (0.08, 0.22)),
        ("fx_dust.png",  193.04, 0.85, 0.30, "drift",  (0.30, 0.35)),
        ("fx_leak.png",  199.30, 1.60, 0.30, "static", (0.50, 0.55)),
        ("fx_flash.png", 212.62, 0.13, 0.78, "static", (0.04, 0.08)),
        ("fx_flash.png", 215.30, 0.12, 0.30, "static", (0.04, 0.08)),
        ("fx_smoke.png", 219.80, 1.25, 0.45, "drift",  (0.35, 0.50)),
        ("fx_dust_z04.png", 231.90, 2.30, 0.50, "drift", (0.70, 0.90)),
    ]
    fx_src = "[ov2]"
    for k, (plate, st, dur, alpha, drift, (fdi, fdo)) in enumerate(FX_EVENTS):
        pp = os.path.join(FXDIR, plate)
        assert os.path.isfile(pp), "FX plate missing: %s (run make_fx_plates_r1017.py first)" % pp
        idx = len(blocks) + 3 + k
        fc_parts.append("[%d:v]scale=%d:%d,format=rgba,setpts=PTS+%.2f/TB,"
                        "fade=t=in:st=%.2f:d=%.2f:alpha=1,fade=t=out:st=%.2f:d=%.2f:alpha=1,"
                        "colorchannelmixer=aa=%.2f[fx%d]"
                        % (idx, W, H, st, st, fdi, st + dur - fdo, fdo, alpha, k))
        if drift == "sweepL":
            fc_parts.append("%s[fx%d]overlay=x='-1092+(t-%.2f)*4200':y=0[ovx%d]" % (fx_src, k, st, k))
        elif drift == "sweepR":
            fc_parts.append("%s[fx%d]overlay=x='1092-(t-%.2f)*4200':y=0[ovx%d]" % (fx_src, k, st, k))
        elif drift == "drift":
            fc_parts.append("%s[fx%d]overlay=x='(t-%.2f)*36':y='-(t-%.2f)*18'[ovx%d]" % (fx_src, k, st, st, k))
        else:
            fc_parts.append("%s[fx%d]overlay=0:0[ovx%d]" % (fx_src, k, k))
        fx_src = "[ovx%d]" % k
    fc_parts.append("%s%s,ass=%s[v]" % (fx_src, fin, ASS_FILE))   # FX 同过 fin 做旧+歌词后置
    fc = ";".join(fc_parts)

    out = os.path.join(HERE, "full_mv_v56.mp4")
    a_fade_st = final_len - 2.75
    cmd = [FF, "-y", "-i", blocks[0], "-i", blocks[1], "-i", blocks[2]]
    for b in blocks[3:]:
        cmd += ["-i", b]
    cmd += ["-i", v2.SONG,
            "-loop", "1", "-t", "%.2f" % (TITLE_WIN + 0.5), "-i", TITLE_PNG,
            "-loop", "1", "-t", "%.2f" % (TAIL_DUR + 0.5), "-i", TAIL_PNG]
    for (_plate, _st, _dur, _a, _m, _f) in FX_EVENTS:
        cmd += ["-loop", "1", "-t", "%.2f" % (_dur + 0.10), "-i", os.path.join(FXDIR, _plate)]
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "%d:a" % SONG_IDX,
            "-af", "afade=t=in:st=0:d=0.8,afade=t=out:st=%.2f:d=2.5,%s,alimiter=limit=0.8413:level=disabled" % (a_fade_st, ln),
            "-c:v", "libx264", "-preset", PRE, "-crf", str(22 if PROXY else 18),
            "-profile:v", "high", "-g", "12", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    print("rendering %d inputs xfade-chain(14) + title/tail cards + ass -> %s" % (len(blocks) + 3, out), flush=True)
    subprocess.run(cmd, check=True)
    fl = v5.dur_of(out)
    print("DONE %s  FINAL-LEN %.2f (target %.2f)" % (out, fl, target), flush=True)
    if abs(fl - target) > 0.5:
        raise SystemExit("FATAL output len %.2f vs target %.2f" % (fl, target))

    # ---- CHK-T6 抽帧验证面（V5.6：新开场六拍 8 + 转场中点 4 + SING3 替换槽 + 尾声明·16 帧拼板） ----
    tdir = os.path.join(D56, "chk_t6")
    os.makedirs(tdir, exist_ok=True)
    probes = [
        ("open_fade", 0.25), ("a_write", 1.50), ("b_pause", 4.50), ("title_macro", 6.20),
        ("r_macro_clean", 7.45), ("c_gaze", 9.00), ("p_macro", 12.00), ("e2_lookup", 15.00),
        ("s1_fire", 19.00), ("xf80_mid", 79.98), ("xf110_mid", 109.97), ("xf152_mid", 151.85),
        ("xf1916_mid", 191.42), ("sing3_reprise", 198.00), ("d08_arch", 169.00), ("tail_credit", 232.80),
    ]
    for i, (tag, tt) in enumerate(probes):
        subprocess.run([FF, "-y", "-ss", "%.2f" % tt, "-i", out, "-frames:v", "1", "-q:v", "3",
                        os.path.join(tdir, "f_%02d.jpg" % i)], capture_output=True)
    sheet = os.path.join(tdir, "CHK-T6-SHEET.jpg")
    subprocess.run([FF, "-y", "-framerate", "1", "-i", os.path.join(tdir, "f_%02d.jpg"),
                    "-vf", "scale=480:270,tile=4x4", "-frames:v", "1", "-q:v", "4", sheet],
                    capture_output=True)
    for i, (tag, tt) in enumerate(probes):
        print("CHK-T6 f_%02d %-15s @%.2f" % (i, tag, tt), flush=True)
    print("CHK-T6 sheet -> " + sheet, flush=True)
    print("ASSERT-OK len/xf-math(14pt)/A1win=21.90/S4-del/SIL1-ext/v5redo+v56src/loudnorm+alimiter/encode verified in single chain", flush=True)
    print("PENDING multimodal: new opening continuity + v56 card + sing3 reprise + 4 transitions on sheet", flush=True)


if __name__ == "__main__":
    main()
