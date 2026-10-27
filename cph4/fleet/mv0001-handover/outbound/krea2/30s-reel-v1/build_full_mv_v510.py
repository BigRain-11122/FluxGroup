# -*- coding: utf-8 -*-
# build_full_mv_v510.py — V5.10 发布准备版（CEO 10-19 终审令：闪烁跳帧修复+片尾出处字+暗水印前站）
# 承 V5.9（build_full_mv_v59.py 全配方）；本版四改：
#   ①TAIL_PNG → tail_credit_v510.png（CEO 令「片尾写好 转载需注明出处 @大喵没鱼吃」·v55 同风格）
#   ②J-42 新闸：REUSE 段长验证——块中镜 |dur-window|>0.07=FATAL（E04_replay 陈旧超长吃 Z01 头槽→
#     221.08 硬跳实锚）；块尾镜 dur<window+ext-0.07=FATAL（Z02 缺 1.10 尾延→225.25 硬跳实锚）。
#     病根：REUSE 只验 dur>0 不验长度→陈旧发射件毒害块拼装（BLOCK-PIN 只数帧数对内容盲·断言全绿假象）
#   ③J-42 姊妹闸：分级件优先——SHOT_GRADE 镜首建用 gr_ 件·裸 REUSE 用 v56_=掉级回归（C04/D05/D08 实锚）
#   ④chk 板换 chk_v510 目录（不覆写 v59 判读件）
# 修复批=fix_v510_segments_r1019.py：deflicker hm 31/5（C08/E06 脉动+Z04/C06/B04 台阶）+C03 中间帧重建
#   +E04_replay/Z02 按窗重发射；S6@35.625 目检=锤击合法动作帧不修
import os, subprocess, sys, re
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
os.chdir(HERE)
sys.path.insert(0, HERE)
import build_full_mv_v2 as v2
import build_full_mv_v3 as v3m
import build_full_mv_v5 as v5

PROXY = os.environ.get("PROXY") == "1"
if PROXY:
    raise SystemExit("V5.10 final-only: PROXY re-emits 540p over cache - forbidden")
DRYRUN = os.environ.get("DRYRUN") == "1"
NO_SIL4 = os.environ.get("NO_SIL4") == "1"
FF = v2.FF
W, H, CRF, PRE = v5.W, v5.H, v5.CRF, v5.PRE
FAST = v5.FAST

SIL1_DUR_V51 = 2.14
# V5.9 剪辑语法表 v2（缺陷①·R-20261018-mv-transitions-v1 §4 对照表：14→6·特效转场-57%·hblur 全撤）
# 硬切=fade D0.05：0.04 版结构性踩雷（2026-10-19 定谳）——off=块长−D 永远落在 in1 末帧 PTS（块长−1/24≈−0.0417）
# 之后→xfade 等不到 pts≥offset 的 in1 帧即 EOF→in2 以本地 PTS 原样吐出→混流器按非单调时间戳全丢
# （4 块铔接复现 drop=563 实锚；D=0.05 复验 1057 帧零 drop）。硬切 D 必须 >1/24=41.67ms，0.05=最小安全档
# 段界叠化保留×3；T 桥双 0.65s 叠化过桥（v3 更正口径）；219.84 fade 移位 227.50 尾段界锚
XFS = [
    (21.90,  "fade",  0.05), (38.82,  "fade",  0.65), (40.22,  "fade",  0.65),
    (44.00,  "fade",  0.05), (47.50,  "fade",  0.05), (80.18,  "fade",  0.05),
    (102.88, "fade",  0.05), (110.52, "fade",  0.90), (126.32, "fade",  0.05),
    (131.72, "fade",  0.05), (152.00, "fade",  0.05), (187.26, "fade",  0.90),
    (191.60, "fade",  0.05), (227.50, "fade",  1.10),
]
assert len(XFS) == 14, "XFS count %d != 14" % len(XFS)
ASS_FILE = "lyric_track.ass"
D56 = os.path.join(v2.D_CUT, "v56")      # 复用 v56 段件缓存（REUSE 全命中·V5.10 修复批已就位）
os.makedirs(D56, exist_ok=True)
v5.D_CUT = D56

V56SRC = os.path.join(HERE, "v56src")
V56_SOURCE_MAP = {
    "S1_fire_wake":       "S1_fire_wake_v59fix.mp4",     # 挂账修：火焰贴右缘（12px 左移+右缘镜像条·对比板 PASS）
    "N02_crowd_her":      "N02_crowd_her_v59_seg.mp4",   # 缺陷④⑥：观展表演重烧（云 H3·ACCEPT·1.00s 起转身读楔文弧线段）
    "D08_world_flip":     "D08_world_flip_v59_cloud.mp4", # 缺陷②：乱入动画→实拍感沙掠碑面（云 H3·S3 碑面锚·验收见确认单）
    "SING2":              "SING2_v59_seg.mp4",            # 缺陷③：火堆演唱重烧（云 H3·ACCEPT·1.30s 起开口曲线段）
    "SING3b_v4":          "V56_SING1_reprise_v59.mp4",   # 缺陷③：SING1 张口段 1.20-3.30s 复用回环（V5.9 修复批定稿件）
    "V56_R_rubbing_macro": "V56_R_rubbing_macro.mp4",
    "V56_P_pen_macro":     "V56_P_pen_macro.mp4",
    "INT3_photo_stare":    "V56_C_gaze_seg.mp4",
    "INT5_head_bow_E2":    "V56_E2_lookup_seg.mp4",
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

# 字层：V5.10 片尾出处字卡换新（CEO 令 10-19·tail_credit_v510.png=v55 同风格新文本）
TITLE_MAIN_PNG = os.path.join(HERE, "title_card_v59_main.png")
TITLE_L_PNG = [os.path.join(HERE, "title_credit_v59_l1.png"),
               os.path.join(HERE, "title_credit_v59_l2.png"),
               os.path.join(HERE, "title_credit_v59_l3.png")]
TITLE_IN_ST, TITLE_WIN = 4.10, 3.30
TITLE_MAIN_IN_D, TITLE_OUT_D = 0.60, 0.30
TITLE_L_ST, TITLE_L_IN_D = [4.85, 5.25, 5.65], 0.45
TAIL_PNG = os.path.join(HERE, "tail_credit_v510.png")   # ★V5.10 改①：新出处字卡
assert os.path.isfile(TAIL_PNG), "FATAL tail_credit_v510.png missing"
TAIL_ST, TAIL_DUR = 230.50, 3.75
TAIL_IN_D, TAIL_OUT_D = 1.20, 0.80


def build_rows_v51():
    ins = []
    for x in v3m.V3_INSERTS:
        iid, fn, a, d, v = x
        if iid == "SIL1_v4b":
            d = SIL1_DUR_V51
        ins.append((iid, fn, a, d, v))
    v3m.V3_INSERTS = ins
    return v5.build_rows_v5()


def build_rows_v56():
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
    assert abs(rows[0][1]) < 0.001, "FATAL first row not at 0"
    for a, b in zip(rows, rows[1:]):
        assert abs(b[1] - a[2]) < 0.001, "FATAL window gap/overlap %s(%.3f) -> %s(%.3f)" % (a[0], a[2], b[0], b[1])
    return rows


def main():
    rows = build_rows_v56()
    print("V5.10 rows=%d  PROXY=%s DRYRUN=%s NO_SIL4=%s" % (len(rows), PROXY, DRYRUN, NO_SIL4), flush=True)
    resolved = []
    for sid, t0, t1, v, src_file, is_new in rows:
        base_sid = sid.split("@")[0]
        want = MERGED_MAP.get(base_sid, src_file)
        src, kind = find_src_v56(want)
        if src is None:
            src, kind = v2.find_src(src_file), "legacy-fallback"
        if src is None:
            if base_sid in MERGED_MAP and not DRYRUN:
                raise SystemExit("FATAL mapped source missing: %s -> %s" % (sid, want))
            if resolved:
                prev = resolved[-1]; prev[2] = t1
                print("FALLBACK-MERGE %s -> %s" % (sid, prev[0]), flush=True)
                continue
            raise SystemExit("FATAL first shot missing " + sid)
        resolved.append([sid, t0, t1, v, src, kind])
    n_v5 = sum(1 for r in resolved if r[5] == "v5redo")
    exp_v5 = sum(1 for r in rows if r[0].split("@")[0] in v5.V5_SOURCE_MAP
                 and r[0].split("@")[0] not in V56_SOURCE_MAP)
    n_56 = sum(1 for r in resolved if r[5] == "v56src")
    print("sources: v5redo=%d(exp %d) / v56src=%d" % (n_v5, exp_v5, n_56), flush=True)
    if not DRYRUN and n_v5 != exp_v5:
        raise SystemExit("FATAL v5redo source count %d != %d" % (n_v5, exp_v5))
    assert n_56 == 9, "FATAL v56src count %d != 9 (S1/N02/D08/SING2/SING3b + 4 legacy)" % n_56

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
    print("blocks: A1=%d A2=%d T=1 G=%s A1win=%.2f" % (len(A1_ids), len(A2_ids), [len(g) for g in G], a1_win), flush=True)

    cuts = {}
    for sid, t0, t1, v, src, kind in resolved:
        if sid == T_id:
            continue
        ext = TAIL_EXT.get(sid, 0.0)
        dst = os.path.join(D56, "v56_%s.mp4" % sid.replace("@", "_at_"))
        if os.path.isfile(dst) and (v5.dur_of(dst) or 0) > 0:
            # ★V5.10 改③：分级件优先（首建 emit 返回 gr_·裸 REUSE 掉级=J-42 姊妹病）
            eff = dst
            gfile = os.path.join(D56, "gr_%s.mp4" % sid)
            if os.path.isfile(gfile) and (v5.dur_of(gfile) or 0) > 0:
                eff = gfile
            # ★V5.10 改②：J-42 REUSE 段长验证闸（本案病根闸·两 FATAL 形）
            got = v5.dur_of(eff) or 0.0
            exp_dur = round(t1 - t0 + ext, 3)
            if sid in TAIL_EXT:
                assert got >= exp_dur - 0.07, \
                    "FATAL J-42 block-last deficit %s: %.3f < %.3f (xfade 供料缺口=块尾硬跳出生地)" % (sid, got, exp_dur)
                if got > exp_dur + 0.07:
                    print("WARN J-42 block-last excess %s: %.3f > %.3f (pin 尾裁安全)" % (sid, got, exp_dur), flush=True)
            else:
                assert abs(got - exp_dur) <= 0.07, \
                    "FATAL J-42 mid-block mis-length %s: %.3f != %.3f (块中错长=全块时移+镜中硬跳出生地)" % (sid, got, exp_dur)
            print("REUSE %s (%.3fs)" % (os.path.basename(eff), got), flush=True)
            cuts[sid] = (eff, t0, t1, v)
            continue
        dst, pads = v5.emit_shot(sid, t0, t1, v, src, dst, ext=ext)
        got = v5.dur_of(dst) or 0.0
        exp_dur = round(t1 - t0 + ext, 3)
        assert (got >= exp_dur - 0.07) if sid in TAIL_EXT else abs(got - exp_dur) <= 0.07, \
            "FATAL emit len %s: %.3f vs %.3f" % (sid, got, exp_dur)
        cuts[sid] = (dst, t0, t1, v)

    def concat_block(ids, name):
        outp = os.path.join(D56, name)
        if os.path.isfile(outp) and (v5.dur_of(outp) or 0) > 0:
            print("REUSE %s" % name, flush=True)
            return outp
        v2.concat([cuts[s][0] for s in ids], outp)
        return outp

    blocks = [concat_block(A1_ids, "v56_blockA1.mp4"), concat_block(A2_ids, "v56_blockA2.mp4")]
    t_raw = v2.find_src("KFT_glyphs.mp4")
    assert t_raw, "KFT_glyphs source missing"
    T_dst = os.path.join(D56, "v56_T18.mp4")
    if os.path.isfile(T_dst) and (v5.dur_of(T_dst) or 0) > 0:
        print("REUSE v56_T18.mp4", flush=True)
    else:
        base = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=24" % (W, H, W, H))
        interp = ("minterpolate=fps=48:mi_mode=mci,setpts=PTS/%.4f," % 0.90) if not FAST else ("setpts=PTS/%.4f," % 0.90)
        subprocess.run([FF, "-y", "-i", t_raw, "-an", "-vf", interp + base, "-t", "2.1000",
                        "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF),
                        "-pix_fmt", "yuv420p", T_dst], check=True, capture_output=True)
    blocks.append(T_dst)
    for i, ids in enumerate(G):
        blocks.append(concat_block(ids, "v56_blockG%d.mp4" % i))
    assert len(blocks) == 15, "block count %d != 15" % len(blocks)

    target = v2.FILM_END if not NO_SIL4 else v2.FILM_END - 1.08

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
        # 真实包数（-count_packets）——容器 Duration 可虚报（concat/-c copy 病族），时长推导帧数对 pin 是盲的
        try:
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
                                "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", p],
                               capture_output=True, text=True, errors="replace", timeout=60)
            return int(r.stdout.strip().splitlines()[-1])
        except Exception:
            return -1

    def pin_block(p, want_frames):
        got = frames_of(p)
        if got == want_frames:
            return p
        d = want_frames - got
        fixed = p[:-4] + "_fx.mp4"
        if os.path.isfile(fixed) and frames_of(fixed) == want_frames:
            print("REUSE %s" % os.path.basename(fixed), flush=True)
            return fixed
        # J-43 判例（V5.10 实锚）：pin trim 禁用 setpts=PTS-STARTPTS——concat 的 B 帧流上 setpts 按解码序
        # 重写 PTS→下游非单调→混流器丢帧（G3 实测 558→380·T7/T8/T9 三分离实锚：仅 setpts 丢·仅 trim 全过·
        # null+-frames:v 精确）。正法：裁短=null 滤镜+-frames:v 精确限帧（免 setpts）；垫长=tpad（无 setpts）
        if d > 0:
            vf = "tpad=stop_mode=clone:stop_duration=%.6f" % (d / 24.0)
            extra = []
        else:
            vf = "null"
            extra = ["-frames:v", str(want_frames)]
        subprocess.run([FF, "-y", "-i", p, "-an", "-vf", vf] + extra +
                       ["-c:v", "libx264", "-preset", PRE,
                        "-crf", str(CRF), "-pix_fmt", "yuv420p", fixed], check=True, capture_output=True)
        print("BLOCK-PIN %s %s%d fr" % (os.path.basename(p), "+" if d > 0 else "", d), flush=True)
        got2 = frames_of(fixed)
        if got2 != want_frames:
            raise SystemExit("FATAL pin output %s: real %d != %d frames (container duration lies)" % (fixed, got2, want_frames))
        return fixed

    BF = block_frame_targets()
    blocks = [pin_block(b, BF[i]) for i, b in enumerate(blocks)]
    lens = [v5.dur_of(b) for b in blocks]

    offsets, running = [], 0.0
    xfi = 0
    for bi in range(len(blocks)):
        running += lens[bi]
        if xfi < len(XFS):
            anchor, trans, D = XFS[xfi]
            off = round(running - D, 4)
            offsets.append((anchor, trans, D, off))
            if abs(off - anchor) > 0.05:
                raise SystemExit("FATAL xf-math %d: %.3f vs %.3f" % (xfi, off, anchor))
            running -= D
            xfi += 1
    assert xfi == len(XFS)
    final_len = running
    print("final_len computed = %.2f" % final_len, flush=True)
    if abs(final_len - target) > 0.5:
        raise SystemExit("FATAL final_len %.2f vs target %.2f" % (final_len, target))

    p1 = subprocess.run([FF, "-i", v2.SONG, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=summary",
                         "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    m = {k: re.search(k + r":\s*([-+]?[\d.]+)", p1.stderr) for k in ("Input Integrated", "Input True Peak", "Input LRA", "Input Threshold")}
    ln = "loudnorm=I=-14:TP=-1.5:LRA=11"
    if all(m.values()):
        mi, mtp, mlra, mth = (float(m[k].group(1)) for k in ("Input Integrated", "Input True Peak", "Input LRA", "Input Threshold"))
        ln = "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%.2f:measured_TP=%.2f:measured_LRA=%.2f:measured_thresh=%.2f:linear=true" % (mi, mtp, mlra, mth)

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
    fc_parts.append("[%s]fade=t=in:st=0:d=0.5,fade=t=out:st=%.2f:d=2.0[base]" % (cur, fade_out_st))
    SONG_IDX = len(blocks)
    TITLE_MAIN_IDX = SONG_IDX + 1
    TITLE_L_IDX = [SONG_IDX + 2, SONG_IDX + 3, SONG_IDX + 4]
    TAIL_IDX = SONG_IDX + 5
    card_out_st = TITLE_IN_ST + TITLE_WIN - TITLE_OUT_D   # 7.10 整卡淡出防尾闪
    fc_parts.append("[%d:v]scale=%d:%d,format=rgba,setpts=PTS+%.2f/TB,"
                    "fade=t=in:st=%.2f:d=%.2f:alpha=1,fade=t=out:st=%.2f:d=%.2f:alpha=1[tmain]"
                    % (TITLE_MAIN_IDX, W, H, TITLE_IN_ST, TITLE_IN_ST, TITLE_MAIN_IN_D,
                       card_out_st, TITLE_OUT_D))
    fc_parts.append("[base][tmain]overlay=0:0[ovt]")
    for k, st in enumerate(TITLE_L_ST):
        fc_parts.append("[%d:v]scale=%d:%d,format=rgba,setpts=PTS+%.2f/TB,"
                        "fade=t=in:st=%.2f:d=%.2f:alpha=1,fade=t=out:st=%.2f:d=%.2f:alpha=1[tl%d]"
                        % (TITLE_L_IDX[k], W, H, st, st, TITLE_L_IN_D, card_out_st, TITLE_OUT_D, k))
        fc_parts.append("%s[tl%d]overlay=x=0:y='6*max(0,1-min(1,(t-%.2f)/%.2f))'[ovl%d]"
                        % ("[ovt]" if k == 0 else "[ovl%d]" % (k - 1), k, st, TITLE_L_IN_D, k))
    fc_parts.append("[%d:v]scale=%d:%d,format=rgba,setpts=PTS+%.2f/TB,"
                    "fade=t=in:st=%.2f:d=%.2f:alpha=1,fade=t=out:st=%.2f:d=%.2f:alpha=1[tcred]"
                    % (TAIL_IDX, W, H, TAIL_ST, TAIL_ST, TAIL_IN_D,
                       TAIL_ST + TAIL_DUR - TAIL_OUT_D, TAIL_OUT_D))
    fc_parts.append("[ovl2][tcred]overlay=0:0[ov2]")
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
        ("fx_leak.png", 150.34, 0.95, 0.38, "static", (0.30, 0.40)),
        ("fx_smoke.png", 159.42, 0.95, 0.28, "drift",  (0.30, 0.40)),
        ("fx_dust.png",  168.30, 2.20, 0.35, "drift",  (0.70, 0.80)),
        ("fx_smoke.png", 176.76, 1.05, 0.30, "drift",  (0.35, 0.45)),
        ("fx_echo.png",  187.24, 0.58, 0.60, "static", (0.07, 0.38)),
        ("fx_echo2.png", 191.44, 0.30, 0.30, "static", (0.08, 0.22)),
        ("fx_dust.png",  193.04, 0.85, 0.30, "drift",  (0.30, 0.35)),
        ("fx_leak.png",  199.30, 1.60, 0.30, "static",  (0.50, 0.55)),
        ("fx_flash.png", 212.62, 0.13, 0.78, "static", (0.04, 0.08)),
        ("fx_flash.png", 215.30, 0.12, 0.30, "static", (0.04, 0.08)),
        ("fx_smoke.png", 219.80, 1.25, 0.45, "drift",  (0.35, 0.50)),
        ("fx_dust_z04.png", 231.90, 2.30, 0.50, "drift", (0.70, 0.90)),
    ]
    fx_src = "[ov2]"
    for k, (plate, st, dur, alpha, drift, (fdi, fdo)) in enumerate(FX_EVENTS):
        pp = os.path.join(FXDIR, plate)
        assert os.path.isfile(pp), "FX plate missing: %s" % pp
        idx = len(blocks) + 6 + k
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
    fc_parts.append("%s%s,ass=%s[v]" % (fx_src, fin, ASS_FILE))
    fc = ";".join(fc_parts)

    out = os.path.join(HERE, "full_mv_v510.mp4")     # ★V5.10 改：出片名
    a_fade_st = final_len - 2.75
    cmd = [FF, "-y", "-i", blocks[0], "-i", blocks[1], "-i", blocks[2]]
    for b in blocks[3:]:
        cmd += ["-i", b]
    cmd += ["-i", v2.SONG,
            "-loop", "1", "-t", "%.2f" % (TITLE_WIN + 0.5), "-i", TITLE_MAIN_PNG,
            "-loop", "1", "-t", "3.00", "-i", TITLE_L_PNG[0],
            "-loop", "1", "-t", "2.60", "-i", TITLE_L_PNG[1],
            "-loop", "1", "-t", "2.20", "-i", TITLE_L_PNG[2],
            "-loop", "1", "-t", "%.2f" % (TAIL_DUR + 0.5), "-i", TAIL_PNG]
    for (_plate, _st, _dur, _a, _m, _f) in FX_EVENTS:
        cmd += ["-loop", "1", "-t", "%.2f" % (_dur + 0.10), "-i", os.path.join(FXDIR, _plate)]
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "%d:a" % SONG_IDX,
            "-af", "afade=t=in:st=0:d=0.8,afade=t=out:st=%.2f:d=2.5,%s,alimiter=limit=0.8413:level=disabled" % (a_fade_st, ln),
            "-c:v", "libx264", "-preset", PRE, "-crf", "18",
            "-profile:v", "high", "-g", "12", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    print("rendering %d inputs -> %s" % (len(blocks) + 6, out), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        tail = "\n".join((r.stderr or "").splitlines()[-25:])
        print("RENDER-FAIL rc=%d stderr-tail:\n%s" % (r.returncode, tail), flush=True)
        raise SystemExit("FATAL render failed rc=%d" % r.returncode)
    fl = v5.dur_of(out)
    print("DONE %s  FINAL-LEN %.2f (target %.2f)" % (out, fl, target), flush=True)
    if abs(fl - target) > 0.5:
        raise SystemExit("FATAL output len %.2f vs target %.2f" % (fl, target))
    vpk = frames_of(out)
    exp_pk = int(round(target * 24))
    print("VIDEO-FRAMES %d (expect ~%d)" % (vpk, exp_pk), flush=True)
    if abs(vpk - exp_pk) > 6:
        raise SystemExit("FATAL output video frames %d vs ~%d - xfade chain collapse / muxer drops (len gate is audio-blinded)" % (vpk, exp_pk))

    tdir = os.path.join(D56, "chk_v510")          # ★V5.10 改④：判读板独立目录
    os.makedirs(tdir, exist_ok=True)
    for i, tt in enumerate((0.25, 6.20, 9.00, 19.00, 79.98, 109.97, 151.85, 191.42, 198.00, 232.80)):
        subprocess.run([FF, "-y", "-ss", "%.2f" % tt, "-i", out, "-frames:v", "1", "-q:v", "3",
                        os.path.join(tdir, "f_%02d.jpg" % i)], capture_output=True)
    sheet = os.path.join(tdir, "CHK-V510-SHEET.jpg")
    subprocess.run([FF, "-y", "-framerate", "1", "-i", os.path.join(tdir, "f_%02d.jpg"),
                    "-vf", "scale=480:270,tile=5x2", "-frames:v", "1", "-q:v", "4", sheet],
                   capture_output=True)
    print("CHK-V510 sheet -> " + sheet, flush=True)
    print("ASSERT-OK V5.10 (闪烁跳帧修复批: G10 拼装复位+deflicker×5+C03 帧手术+S6 合法保留) verified", flush=True)


if __name__ == "__main__":
    main()
