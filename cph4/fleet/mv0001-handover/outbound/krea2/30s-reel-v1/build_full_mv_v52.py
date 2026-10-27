# -*- coding: utf-8 -*-
# build_full_mv_v52.py — V5.2 特效伴切装配器（V5.1 全承+FX 层·CEO 令 O-20261017-1300）
# 设计正身=R-20261017-mv-fx-transitions-01：17 特效位点/8 转场语言族/纯叠加层/块件全缓存复用/PROXY 禁跑。
# 原承（V5.1 精修装配器·O-20261017-1020·CEO「现在是80分了 好好再打磨一下给成品」令）
# 承 build_full_mv_v5.py 全链正典（v5 复用 import·断言律 v1.1 全执），四修：
#  ①S4_crown 删（0.34s 眨眼闪帧·病灶①最刺眼刀）：SIL1_v4b 插行 dur 1.8→2.14（窗 29.0→31.14）
#    ——S4_crown [29.40,31.14] 被 SIL1 窗完全吞没自动消失·S5 起点 31.14 不动·A 块窗和守恒
#    ——顺带修病灶③（SIL1 展柜→S4 浮雕 POV 断链：现 SIL1 直切 S5·逻辑闭合）
#  ②21.90 微叠化 fade 0.36s（病灶② S1→S2 同主体同景别跳切·火把光态消失·曝光跳变）：
#    A 拆 A1[t0<21.90]/A2[21.90≤t0<38.82]·blocks=[A1,A2,T,G0..G7]
#    XFS 前插 (21.90,fade,0.36) 共 10 点·block_bounds=XFS[3:]
#    TAIL_EXT：A1 尾(S1)=0.36 / A2 尾(S7)=XFS[1][2]=0.40 / G_i 尾=XFS[3+i][2]
#  ③s9 金句 overlay 删（全曲字幕层覆盖同句·保留必双字打架·顺带销挂账①选位）
#    字层=歌名卡+AIGC 标识两枚·AIGC=重生成 badge（白@80%+双层软暗衬底·挂账②）
#  ④全曲逐句歌词 ASS 后置（[ov2]fin 之后 ass 滤镜·字不被做旧处理·最清晰）
#    55 事件·lyric_track.ass（make_lyric_ass.py 产出·词面已多源定谳+词级锚分割）
#    os.chdir(HERE)+ass 相对文件名（filter_complex 路径转义规避）
# 用法：
#   代理剪审档:  $env:PROXY='1'; $env:NO_MINTERP='1'; python build_full_mv_v51.py
#   终版:        python build_full_mv_v51.py
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
    raise SystemExit("V5.2 final-only: block cache is 768P; PROXY re-emits 540p over cache - forbidden")
DRYRUN = os.environ.get("DRYRUN") == "1"
NO_SIL4 = os.environ.get("NO_SIL4") == "1"
FF = v2.FF
W, H, CRF, PRE = v5.W, v5.H, v5.CRF, v5.PRE
FAST = v5.FAST

SIL1_DUR_V51 = 2.14                  # 29.00→31.14（S4 吞没+SIL1 窗延·病灶①③一刀双修）
XFS = [(21.90, "fade", 0.36)] + list(v5.XFS)   # 10 点 XF 链（前插 21.90 微叠化·病灶②）
ASS_FILE = "lyric_track.ass"
D51 = os.path.join(v2.D_CUT, "v51")
os.makedirs(D51, exist_ok=True)
v5.D_CUT = D51                       # v5.emit_shot 内部段件/调色件落 v51 目录（不踩 v5 件）
TITLE_PNG, AIGC_PNG = v5.TITLE_PNG, v5.AIGC_PNG
TITLE_IN_ST, TITLE_WIN = v5.TITLE_IN_ST, v5.TITLE_WIN
TITLE_IN_D, TITLE_OUT_D = v5.TITLE_IN_D, v5.TITLE_OUT_D


def build_rows_v51():
    """v5 行表 + SIL1 窗延（S4_crown 被 [29.0,31.14] 窗吞没自动消失）。"""
    ins = []
    for x in v3m.V3_INSERTS:
        iid, fn, a, d, v = x
        if iid == "SIL1_v4b":
            d = SIL1_DUR_V51
        ins.append((iid, fn, a, d, v))
    v3m.V3_INSERTS = ins
    return v5.build_rows_v5()        # 内含 CLAMP{SING1,SIL2}+SPEED_OVERRIDE+啃洞切分


def main():
    rows = build_rows_v51()
    sids = [r[0] for r in rows]
    assert not any(s.startswith("S4_crown") for s in sids), "FATAL S4_crown row still present"
    sil1 = [r for r in rows if r[0].startswith("SIL1_v4b@")]
    assert sil1 and abs(sil1[0][2] - 31.14) < 0.001, "FATAL SIL1 window not extended"
    print("V5.1 rows=%d  PROXY=%s DRYRUN=%s NO_SIL4=%s" % (len(rows), PROXY, DRYRUN, NO_SIL4), flush=True)
    print("FIX1-OK S4_crown swallowed by SIL1 29.00-31.14 (S5 anchor 31.14 intact)", flush=True)

    # ---- 源解析（v5 正典：V5REDO 优先·@ 后缀剥键·DRYRUN 顶替·计数硬断言 J-32）----
    resolved = []
    for sid, t0, t1, v, src_file, is_new in rows:
        base_sid = sid.split("@")[0]
        want = v5.V5_SOURCE_MAP.get(base_sid, src_file)
        src, kind = v5.find_src_v5(want)
        if src is None:
            src, kind = v2.find_src(src_file), "legacy-fallback"
        if src is None:
            if base_sid in v5.V5_SOURCE_MAP and not DRYRUN:
                raise SystemExit("FATAL v5redo source missing: %s -> %s (await bm-c; DRYRUN=1 to substitute)" % (sid, want))
            if resolved:
                prev = resolved[-1]; prev[2] = t1
                print("FALLBACK-MERGE %s -> %s" % (sid, prev[0]), flush=True)
                continue
            raise SystemExit("FATAL first shot missing " + sid)
        if base_sid in v5.V5_SOURCE_MAP and kind != "v5redo":
            if DRYRUN:
                print("DRY-SUB %s uses legacy %s (math-check only)" % (sid, os.path.basename(src)), flush=True)
            else:
                print("WARN %s fell back to legacy source" % sid, flush=True)
        resolved.append([sid, t0, t1, v, src, kind])
    n_v5 = sum(1 for r in resolved if r[5] == "v5redo")
    print("sources: v5redo=%d / %d" % (n_v5, len(v5.V5_SOURCE_MAP)), flush=True)
    if not DRYRUN and n_v5 != len(v5.V5_SOURCE_MAP):
        raise SystemExit("FATAL v5redo source count %d != %d (J-32)" % (n_v5, len(v5.V5_SOURCE_MAP)))

    # ---- 分块：A1/A2 拆（21.90 微叠化）+ T 特例 + G0..G7 ----
    T_id = "T_glyphs"
    block_bounds = [a for (a, _, _) in XFS[3:]]          # 47.50..219.84（7 边界·G0..G7）
    A1_ids = [r[0] for r in resolved if r[1] < 21.90 and r[0] != T_id]
    A2_ids = [r[0] for r in resolved if 21.90 <= r[1] < 38.82 and r[0] != T_id]
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
    TAIL_EXT = {A1_ids[-1]: XFS[0][2], A2_ids[-1]: XFS[1][2]}
    for i, ids in enumerate(G[:-1]):
        TAIL_EXT[ids[-1]] = XFS[3 + i][2]
    print("blocks: A1=%d A2=%d T=1 G=%s" % (len(A1_ids), len(A2_ids), [len(g) for g in G]), flush=True)
    print("A1=%s" % A1_ids, flush=True)
    print("A2=%s" % A2_ids, flush=True)
    print("tail-ext=%s" % {k: round(v, 2) for k, v in TAIL_EXT.items()}, flush=True)

    # ---- 发射全镜（块末镜带尾延·T 特例单独发射故跳过）----
    cuts = {}
    for sid, t0, t1, v, src, kind in resolved:
        if sid == T_id:
            continue
        ext = TAIL_EXT.get(sid, 0.0)
        dst = os.path.join(D51, "v51_%s.mp4" % sid.replace("@", "_at_"))
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
        outp = os.path.join(D51, name)
        if os.path.isfile(outp) and (v5.dur_of(outp) or 0) > 0:
            print("REUSE %s" % name, flush=True)
            return outp
        v2.concat([cuts[s][0] for s in ids], outp)
        return outp

    blocks = [concat_block(A1_ids, "v51_blockA1.mp4"), concat_block(A2_ids, "v51_blockA2.mp4")]
    # T 桥特例（v5 正典尾延律）：T 流=窗 1.40+尾延 0.4=1.80·KFT 源 0 起@0.90
    t_raw = v2.find_src("KFT_glyphs.mp4")
    assert t_raw, "KFT_glyphs source missing"
    T_dst = os.path.join(D51, "v51_T18.mp4")
    base = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=24" % (W, H, W, H))
    interp = ("minterpolate=fps=48:mi_mode=mci,setpts=PTS/%.4f," % 0.90) if not FAST else ("setpts=PTS/%.4f," % 0.90)
    subprocess.run([FF, "-y", "-i", t_raw, "-an", "-vf", interp + base, "-t", "1.8000",
                    "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF),
                    "-pix_fmt", "yuv420p", T_dst], check=True, capture_output=True)
    blocks.append(T_dst)
    for i, ids in enumerate(G):
        blocks.append(concat_block(ids, "v51_blockG%d.mp4" % i))
    assert len(blocks) == 11, "block count %d != 11" % len(blocks)

    target = v2.FILM_END if not NO_SIL4 else v2.FILM_END - 1.08

    # ---- 帧锁定块长（治本·断言律 v1.1 执法·r1017 首跑实录）----
    # 病：-t 发射段长被 24fps 帧量化向下取整→块长亏空累积（首跑 XF5 实测偏 0.08s>0.05 容差炸链）。
    # 法：块界钉整数帧 P_k=round((词锚+ΣD_j≤k)×24)（partial-sum pinning）——每个 XF offset
    #     与词锚偏差保证 ≤1 帧（0.021s）·终长帧级精确；差额帧由块尾 tpad/trim 补齐（落 fade 窗不可辨）。
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

    # ---- XF 链数学（10 点·链式 offset·窗内容零漂移自检）----
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

    # ---- loudnorm pass1 测量（v5 正典）----
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

    # ---- filter_complex：10 xfade 链 + 字层两枚（title/aigc·PTS 陷阱修复承 v5）+ fin + ASS 后置 ----
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
    fc_parts.append("[%s]fade=t=in:st=0:d=1.2,fade=t=out:st=%.2f:d=2.0[base]" % (cur, fade_out_st))
    SONG_IDX = len(blocks)                                  # 11：blocks 0..10
    TITLE_IDX, AIGC_IDX = SONG_IDX + 1, SONG_IDX + 2        # 12, 13
    fc_parts.append("[%d:v]scale=%d:%d,format=rgba,setpts=PTS+%.2f/TB,"
                    "fade=t=in:st=%.2f:d=%.2f:alpha=1,fade=t=out:st=%.2f:d=%.2f:alpha=1[tcard]"
                    % (TITLE_IDX, W, H, TITLE_IN_ST, TITLE_IN_ST, TITLE_IN_D,
                       TITLE_IN_ST + TITLE_WIN - TITLE_OUT_D, TITLE_OUT_D))
    fc_parts.append("[base][tcard]overlay=0:0[ov1]")
    fc_parts.append("[%d:v]scale=%d:%d,format=rgba,setpts=PTS+0/TB,"
                    "fade=t=in:st=0:d=1.2:alpha=1,fade=t=out:st=2.4:d=0.6:alpha=1[aigc]" % (AIGC_IDX, W, H))
    fc_parts.append("[ov1][aigc]overlay=0:0[ov2]")
    # ---- V5.2 特效伴切层（CEO 令 O-20261017-1300·正身=R-20261017-mv-fx-transitions-01 §二）----
    # 纯叠加层：底层剪辑数学/块链零改动；FX_EVENTS 置空表=v51 基线逐字节回归（保险丝）。
    FXDIR = os.path.join(HERE, "fx_plates")
    FX_EVENTS = [
        # (plate, st, dur, peak_alpha, drift, (fade_in, fade_out))  drift: sweepL/sweepR/static/drift
        ("fx_band.png",  38.62, 0.52, 0.85, "sweepL", (0.10, 0.16)),
        ("fx_band.png",  40.02, 0.52, 0.85, "sweepR", (0.10, 0.16)),
        ("fx_leak.png",  47.30, 0.95, 0.55, "static", (0.28, 0.35)),
        ("fx_flash.png", 77.30, 0.14, 0.80, "static", (0.04, 0.08)),
        ("fx_smoke.png", 80.05, 0.90, 0.45, "drift",  (0.28, 0.35)),
        ("fx_flash.png", 91.02, 0.13, 0.75, "static", (0.04, 0.08)),
        ("fx_dust.png",  93.05, 1.35, 0.55, "drift",  (0.45, 0.55)),
        ("fx_dust.png", 102.80, 1.15, 0.50, "drift",  (0.40, 0.50)),
        ("fx_smoke.png",110.42, 1.50, 0.42, "drift",  (0.45, 0.55)),
        ("fx_leak.png", 110.62, 1.45, 0.40, "static", (0.45, 0.50)),
        ("fx_dust.png", 131.62, 1.25, 0.50, "drift",  (0.40, 0.55)),
        ("fx_flash.png",141.72, 0.14, 0.80, "static", (0.04, 0.08)),
        ("fx_dust.png", 168.30, 2.20, 0.35, "drift",  (0.70, 0.80)),
        ("fx_echo.png", 187.24, 0.58, 0.60, "static", (0.07, 0.38)),
        ("fx_flash.png",212.62, 0.13, 0.78, "static", (0.04, 0.08)),
        ("fx_smoke.png",219.80, 1.25, 0.45, "drift",  (0.35, 0.50)),
        ("fx_dust.png", 231.90, 2.30, 0.40, "drift",  (0.70, 0.90)),
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

    out = os.path.join(HERE, "full_mv_v52.mp4")
    a_fade_st = final_len - 2.75
    cmd = [FF, "-y", "-i", blocks[0], "-i", blocks[1], "-i", blocks[2]]
    for b in blocks[3:]:
        cmd += ["-i", b]
    cmd += ["-i", v2.SONG,
            "-loop", "1", "-t", "%.2f" % (TITLE_WIN + 0.5), "-i", TITLE_PNG,
            "-loop", "1", "-t", "3.5", "-i", AIGC_PNG]
    for (_plate, _st, _dur, _a, _m, _f) in FX_EVENTS:
        cmd += ["-loop", "1", "-t", "%.2f" % (_dur + 0.10), "-i", os.path.join(FXDIR, _plate)]
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "%d:a" % SONG_IDX,
            "-af", "afade=t=in:st=0:d=0.8,afade=t=out:st=%.2f:d=2.5,%s" % (a_fade_st, ln),
            "-c:v", "libx264", "-preset", PRE, "-crf", str(22 if PROXY else 18),
            "-profile:v", "high", "-g", "12", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    print("rendering %d inputs xfade-chain(10) + ass -> %s" % (len(blocks) + 3, out), flush=True)
    subprocess.run(cmd, check=True)
    fl = v5.dur_of(out)
    print("DONE %s  FINAL-LEN %.2f (target %.2f)" % (out, fl, target), flush=True)
    if abs(fl - target) > 0.5:
        raise SystemExit("FATAL output len %.2f vs target %.2f" % (fl, target))

    # ---- CHK-T2 抽帧验字 + 衔接复验（导演席多模态执法面·16 点拼板）----
    tdir = os.path.join(D51, "chk_t2")
    os.makedirs(tdir, exist_ok=True)
    probes = [
        ("aigc_1s", 1.0), ("title_mid", TITLE_IN_ST + TITLE_WIN / 2),
        ("xf2190_mid", 22.05), ("s2_post", 22.60),
        ("sil1_late", 30.60), ("s5_in", 31.60),
        ("lyr01a", 32.20), ("lyr01b", 33.95),
        ("lyr04a", 39.60), ("lyr05b", 45.50),
        ("lyr12", 78.70), ("lyr17", 96.50),
        ("lyr26", 129.70), ("lyr36", 174.00),
        ("lyr37", 181.00), ("lyr47", 225.00),
    ]
    for i, (tag, tt) in enumerate(probes):
        subprocess.run([FF, "-y", "-ss", "%.2f" % tt, "-i", out, "-frames:v", "1", "-q:v", "3",
                        os.path.join(tdir, "f_%02d.jpg" % i)], capture_output=True)
    sheet = os.path.join(tdir, "CHK-T2-SHEET.jpg")
    subprocess.run([FF, "-y", "-framerate", "1", "-i", os.path.join(tdir, "f_%02d.jpg"),
                    "-vf", "scale=480:270,tile=4x4", "-frames:v", "1", "-q:v", "4", sheet],
                   capture_output=True)
    for i, (tag, tt) in enumerate(probes):
        print("CHK-T2 f_%02d %-11s @%.2f" % (i, tag, tt), flush=True)
    print("CHK-T2 sheet -> " + sheet, flush=True)
    print("ASSERT-OK len/xf-math(10pt)/S4-del/SIL1-ext/loudnorm/encode verified in single chain", flush=True)
    print("PENDING multimodal: lyric legibility + 2 transitions + badge contrast on sheet", flush=True)


if __name__ == "__main__":
    main()
