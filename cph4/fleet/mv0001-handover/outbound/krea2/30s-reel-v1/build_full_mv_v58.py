# -*- coding: utf-8 -*-
# build_full_mv_v58.py — V5.8 credits 四件套版（CEO 版权令 2026-10-18 14:32 credits 四件套：专辑/作词/作曲/导演+
# 二创标注+撤楔形符号）·承 V5.6 全链零改动（唯一改=title_card_v58.png 替换）
# 段件缓存复用 v56 目录（REUSE 全命中·仅终链重渲 ~15-25 分钟）
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
    raise SystemExit("V5.7 final-only: PROXY re-emits 540p over cache - forbidden")
DRYRUN = os.environ.get("DRYRUN") == "1"
NO_SIL4 = os.environ.get("NO_SIL4") == "1"
FF = v2.FF
W, H, CRF, PRE = v5.W, v5.H, v5.CRF, v5.PRE
FAST = v5.FAST

SIL1_DUR_V51 = 2.14
XFS = [
    (21.90,  "fade",  0.36), (38.82,  "fade",  0.40), (40.22,  "fade",  0.40),
    (44.00,  "hblur", 0.40), (47.50,  "fade",  1.00), (80.18,  "hblur", 0.40),
    (102.88, "fade",  0.60), (110.52, "fade",  1.10), (126.32, "fade",  0.40),
    (131.72, "hblur", 0.50), (152.00, "hblur", 0.30), (187.26, "fade",  0.90),
    (191.60, "hblur", 0.36), (219.84, "fade",  1.20),
]
assert len(XFS) == 14, "XFS count %d != 14" % len(XFS)
ASS_FILE = "lyric_track.ass"
D56 = os.path.join(v2.D_CUT, "v56")      # 复用 v56 段件缓存（REUSE 全命中）
os.makedirs(D56, exist_ok=True)
v5.D_CUT = D56

V56SRC = os.path.join(HERE, "v56src")
V56_SOURCE_MAP = {
    "V56_R_rubbing_macro": "V56_R_rubbing_macro.mp4",
    "V56_P_pen_macro":     "V56_P_pen_macro.mp4",
    "INT3_photo_stare":    "V56_C_gaze_seg.mp4",
    "INT5_head_bow_E2":    "V56_E2_lookup_seg.mp4",
    "SING3b_v4":           "V56_SING1_reprise.mp4",
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

# V5.7 字层：署名字卡（窗参承 v56 不变）
TITLE_PNG = os.path.join(HERE, "title_card_v58.png")
TITLE_IN_ST, TITLE_WIN = 4.10, 3.30
TITLE_IN_D, TITLE_OUT_D = 0.70, 0.60
TAIL_PNG = os.path.join(HERE, "tail_credit_v55.png")
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
    print("V5.7 rows=%d  PROXY=%s DRYRUN=%s NO_SIL4=%s" % (len(rows), PROXY, DRYRUN, NO_SIL4), flush=True)
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
            print("REUSE %s" % os.path.basename(dst), flush=True)
            cuts[sid] = (dst, t0, t1, v)
            continue
        dst, pads = v5.emit_shot(sid, t0, t1, v, src, dst, ext=ext)
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
        subprocess.run([FF, "-y", "-i", t_raw, "-an", "-vf", interp + base, "-t", "1.8000",
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
    TITLE_IDX, TAIL_IDX = SONG_IDX + 1, SONG_IDX + 2
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
        assert os.path.isfile(pp), "FX plate missing: %s" % pp
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
    fc_parts.append("%s%s,ass=%s[v]" % (fx_src, fin, ASS_FILE))
    fc = ";".join(fc_parts)

    out = os.path.join(HERE, "full_mv_v58.mp4")
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
            "-c:v", "libx264", "-preset", PRE, "-crf", "18",
            "-profile:v", "high", "-g", "12", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    print("rendering %d inputs -> %s" % (len(blocks) + 3, out), flush=True)
    subprocess.run(cmd, check=True)
    fl = v5.dur_of(out)
    print("DONE %s  FINAL-LEN %.2f (target %.2f)" % (out, fl, target), flush=True)
    if abs(fl - target) > 0.5:
        raise SystemExit("FATAL output len %.2f vs target %.2f" % (fl, target))

    tdir = os.path.join(D56, "chk_t8")
    os.makedirs(tdir, exist_ok=True)
    for i, tt in enumerate((0.25, 6.20, 9.00, 19.00, 79.98, 109.97, 151.85, 191.42, 198.00, 232.80)):
        subprocess.run([FF, "-y", "-ss", "%.2f" % tt, "-i", out, "-frames:v", "1", "-q:v", "3",
                        os.path.join(tdir, "f_%02d.jpg" % i)], capture_output=True)
    sheet = os.path.join(tdir, "CHK-T7-SHEET.jpg")
    subprocess.run([FF, "-y", "-framerate", "1", "-i", os.path.join(tdir, "f_%02d.jpg"),
                    "-vf", "scale=480:270,tile=5x2", "-frames:v", "1", "-q:v", "4", sheet],
                   capture_output=True)
    print("CHK-T7 sheet -> " + sheet, flush=True)
    print("ASSERT-OK V5.8 (v56 cache reuse + v58 four-piece credits card) verified", flush=True)


if __name__ == "__main__":
    main()
