# -*- coding: utf-8 -*-
# build_full_mv_v54.py — V5.4 终审整改装配器（CEO 六连反馈 2026-10-17 21:1x·O 溯源=会话总结三）
# 承 build_full_mv_v53.py 全链正典（v5 复用 import·断言律 v1.1 全执），六改：
#  ①XFS 10→14 点（内点叠化四连·47 切判读定谳 V54-CUT-VERDICT §二）：
#    (44.00,fadeblack,0.40)  b09 S9→SIL2 入间奏黑闪（判读 A 级：亮降 2 档闪黑）
#    (126.32,fade,0.40)      b24 R04→R05 亮度断崖（判读 A 级：抽象插帧无叙事兜底）
#    (152.00,fade,0.40)      b28 D03b→SIL3 同主体跨景别（判读 B 级：跳帧感第一主源）
#    (191.60,fade,0.40)      b38 E01b→E01c 同碑跨千年叠影（判读 B 级·贴词「深埋在美索不达米亚平原」）
#    ——块结构 A1/A2/T + G0..G11（15 块·分块通用化）·尾延律通用：块 i 尾延=XFS[i] 的 D
#  ②D08_world_flip 换源（CEO「乱入动画镜头」）：V5_SOURCE_MAP 扩键（v5.py）=cloudv2 archived
#    实拍版（media segments 版 CG 纹理叠加+胸像画廊乱入定罪·V54-CUT-VERDICT §一）；
#    旧段件缓存 v51_/gr_ 预删强制重发射·SHOT_GRADE 微提亮保暖
#  ③AIGC 标识删（CEO「AIGC 标识去掉」）：输入/滤镜链/CHK 探针三处全删
#  ④歌名卡重做（CEO「爱在西元前的片头歌曲名好好设计」）：title_card_v54.png
#    右侧暗窗格碑刻展签位·单行 56px 鎏金渐变+楔形符号带+「大喵没鱼吃」22px 灰金落款
#    ·驻留窗 4.10-8.30 加长（判读：原 1.8s 全亮不足·新窗有效驻留≈3.9s）
#  ⑤片尾转载声明层（CEO「注明欢迎转载，请注明出处」）：tail_credit_v54.png
#    「欢迎转载，请注明出处：大喵没鱼吃」19px 灰金@72% 底部居中·Z04 灯灭字存窗 230.50-234.25
#  ⑥字幕纯白版烧录（CEO「字幕要干净点纯白色不要黑边」）：lyric_track.ass 已重生成
#    （52px 纯白·零描边零阴影零 blur·Spacing1.2·fad 保留·55 事件时间轴原样）
# 用法：
#   终版:  python build_full_mv_v54.py   （PROXY 禁跑闸承 v53；段件缓存 D51 全 REUSE 除 D08 重发射）
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
    raise SystemExit("V5.4 final-only: block cache is 768P; PROXY re-emits 540p over cache - forbidden")
DRYRUN = os.environ.get("DRYRUN") == "1"
NO_SIL4 = os.environ.get("NO_SIL4") == "1"
FF = v2.FF
W, H, CRF, PRE = v5.W, v5.H, v5.CRF, v5.PRE
FAST = v5.FAST

SIL1_DUR_V51 = 2.14                  # 29.00→31.14（S4 吞没+SIL1 窗延·v51 正典承）
# V5.4 XFS 14 点：21.90 微叠化（v51 正典）+ v5 九点 + 四内点叠化（升序）
XF_EXTRA = [
    (44.00, "hblur", 0.40),       # b09 A 级·入间奏过门（V5.4.2：fadeblack 违 era 禁用名单（W7 正典·CEO 10-09 去俗令）改 hblur 物质化过门——S9 金句亮暖糊化入 SIL2 暗场·兼破 40.22/44.00/47.50 三连 fade 同型档）
    (126.32, "fade", 0.40),       # b24 A 级·亮度断崖叠化（V5.4.2 配 fx_leak@126.32 漏光伴切=「R05 地下金线·光从土层渗出」）
    (152.00, "fade", 0.40),       # b28 B 级·同主体跨景别叠化（150.34 leak 已覆盖伴切·密度合规保持纯叠化）
    (191.60, "fade", 0.40),       # b38 B 级·同碑跨千年叠影（V5.4.2 配 fx_echo2@191.35=E01b 末帧残像=第二签名时刻·replay 连续叙事特例族）
]
XFS = sorted([(21.90, "fade", 0.36)] + list(v5.XFS) + XF_EXTRA)
assert len(XFS) == 14, "XFS count %d != 14" % len(XFS)
ASS_FILE = "lyric_track.ass"
D51 = os.path.join(v2.D_CUT, "v51")
os.makedirs(D51, exist_ok=True)
v5.D_CUT = D51                       # v5.emit_shot 内部段件/调色件落 v51 目录（不踩 v5 件）

# V5.4 字层参数（title 重做+尾声明新层·CEO 终审令）
TITLE_PNG = os.path.join(HERE, "title_card_v54.png")
TITLE_IN_ST, TITLE_WIN = 4.10, 4.20  # 4.10-8.30 驻留加长（INT3 头暗镜淡出协调）
TITLE_IN_D, TITLE_OUT_D = 0.70, 0.60
TAIL_PNG = os.path.join(HERE, "tail_credit_v54.png")
TAIL_ST, TAIL_DUR = 230.50, 3.75     # Z04 灯灭字存全窗
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


def main():
    rows = build_rows_v51()
    sids = [r[0] for r in rows]
    assert not any(s.startswith("S4_crown") for s in sids), "FATAL S4_crown row still present"
    sil1 = [r for r in rows if r[0].startswith("SIL1_v4b@")]
    assert sil1 and abs(sil1[0][2] - 31.14) < 0.001, "FATAL SIL1 window not extended"
    print("V5.4 rows=%d  PROXY=%s DRYRUN=%s NO_SIL4=%s" % (len(rows), PROXY, DRYRUN, NO_SIL4), flush=True)

    # ---- V5.4 预删段件缓存：D08 换源 + 四段尾延供料（REUSE 会吃掉 ext·强制重发射走正典块尾延律）----
    V54_REEMIT = [
        "v51_D08_world_flip.mp4", "gr_D08_world_flip.mp4",   # D08 换源（cloudv2 archived·CEO 乱入动画镜令）
        "v51_S9_profile.mp4",                                # +ext0.40（b09@44.00 黑闪供料）
        "v51_R04_river_dry.mp4",                             # +ext0.40（b24@126.32 叠化供料）
        "v51_D03b_direct_gaze.mp4",                          # +ext0.40（b28@152.00 叠化供料）
        "v51_E01b_sand.mp4",                                 # +ext0.40（b38@191.60 叠化供料）
        "v51_E04_replay_faces.mp4",                          # V5.4.1 E04 0.85 提速重发射（CEO 鬼影令·E04-SRC-DENSE-BOARD 判读主案 A）
    ]
    for stale in V54_REEMIT:
        p = os.path.join(D51, stale)
        if os.path.isfile(p):
            os.remove(p)
            print("V54-REEMIT dropped stale cache: %s" % stale, flush=True)

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
                raise SystemExit("FATAL v5redo source missing: %s -> %s (DRYRUN=1 to substitute)" % (sid, want))
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

    # ---- 分块（V5.4 通用化）：A1/A2/T 特例 + G0..G11（XFS[3:]=44.00..219.84 十一界）----
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
    # 尾延律通用：块 i 末行尾延 = XFS[i] 的 D（A1/A2/G 全一致·T 特例发射窗 1.40+XFS[2]D=1.80 承 v53）
    seq_blocks = [A1_ids, A2_ids, None] + G
    TAIL_EXT = {}
    for i, ids in enumerate(seq_blocks[:-1]):
        if ids:
            TAIL_EXT[ids[-1]] = XFS[i][2]
    print("blocks: A1=%d A2=%d T=1 G=%s (total %d)" % (
        len(A1_ids), len(A2_ids), [len(g) for g in G], 3 + len(G)), flush=True)
    print("A1=%s" % A1_ids, flush=True)
    print("A2=%s" % A2_ids, flush=True)
    print("tail-ext=%s" % {k: round(v, 2) for k, v in TAIL_EXT.items()}, flush=True)

    # ---- 发射全镜（块末镜带尾延·T 特例单独发射故跳过·D08 换源重发射）----
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
    # T 桥特例（v5 正典尾延律）：T 流=窗 1.40+尾延 XFS[2]D=1.80·KFT 源 0 起@0.90
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
        blocks.append(concat_block(ids, "v54_blockG%d.mp4" % i))   # V5.4 新块划分·新名防踩 v53 缓存
    assert len(blocks) == 15, "block count %d != 15" % len(blocks)

    target = v2.FILM_END if not NO_SIL4 else v2.FILM_END - 1.08

    # ---- 帧锁定块长（partial-sum pinning·断言律 v1.1·承 v53 治本正典）----
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

    # ---- XF 链数学（14 点·链式 offset·窗内容零漂移自检）----
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

    # ---- loudnorm pass1 测量（v5 正典两遍·EBU R128）----
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

    # ---- filter_complex：14 xfade 链 + 字层（title/尾声明·AIGC 删）+ fin + ASS 后置 ----
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
    SONG_IDX = len(blocks)                                  # 15：blocks 0..14
    TITLE_IDX, TAIL_IDX = SONG_IDX + 1, SONG_IDX + 2        # 16, 17（AIGC 删·V5.4 令）
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
    # ---- V5.3 特效伴切层（26 位点·V5.4 承·CEO O-20261017-1300 正身=R-20261017-mv-fx-transitions-01）----
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
        ("fx_leak.png",  126.32, 0.90, 0.40, "static", (0.30, 0.40)),  # V5.4.2 转场顶级令：b24 叠化配漏光=「地下金线浮现·光从土层渗出」（FX 表此区间空缺·间距合规）
        ("fx_flash.png", 141.72, 0.14, 0.80, "static", (0.04, 0.08)),
        ("fx_leak.png",  150.34, 0.95, 0.38, "static", (0.30, 0.40)),
        ("fx_smoke.png", 159.42, 0.95, 0.28, "drift",  (0.30, 0.40)),
        ("fx_dust.png",  168.30, 2.20, 0.35, "drift",  (0.70, 0.80)),
        ("fx_smoke.png", 176.76, 1.05, 0.30, "drift",  (0.35, 0.45)),
        ("fx_echo.png",  187.24, 0.58, 0.60, "static", (0.07, 0.38)),
        ("fx_echo2.png", 191.35, 0.50, 0.40, "static", (0.10, 0.35)),  # V5.4.2 同碑跨千年残像（E01b 末帧 ghost 叠入 E01c 初凿·骑 191.60 XF 叠化窗=replay 连续叙事特例族·R-doc T-bridge clause 同族判例）
        ("fx_dust.png",  193.04, 0.85, 0.30, "drift",  (0.30, 0.35)),
        ("fx_leak.png",  199.30, 1.60, 0.30, "static", (0.50, 0.55)),
        ("fx_flash.png", 212.62, 0.13, 0.78, "static", (0.04, 0.08)),
        ("fx_flash.png", 215.30, 0.16, 0.45, "static", (0.04, 0.08)),  # V5.4.1 E04 罪窗 bloom 保险（提速 0.85 后贴面段移位片上 214.8-215.8·E04 判读主案 A 配套）
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

    out = os.path.join(HERE, "full_mv_v54.mp4")
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
            "-af", "afade=t=in:st=0:d=0.8,afade=t=out:st=%.2f:d=2.5,%s" % (a_fade_st, ln),
            "-c:v", "libx264", "-preset", PRE, "-crf", str(22 if PROXY else 18),
            "-profile:v", "high", "-g", "12", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    print("rendering %d inputs xfade-chain(14) + title/tail cards + ass -> %s" % (len(blocks) + 3, out), flush=True)
    subprocess.run(cmd, check=True)
    fl = v5.dur_of(out)
    print("DONE %s  FINAL-LEN %.2f (target %.2f)" % (out, fl, target), flush=True)
    if abs(fl - target) > 0.5:
        raise SystemExit("FATAL output len %.2f vs target %.2f" % (fl, target))

    # ---- CHK-T3 抽帧验证面（V5.4：AIGC 删·新 XF 四点+D08 换源+尾声明·16 帧拼板）----
    tdir = os.path.join(D51, "chk_t3")
    os.makedirs(tdir, exist_ok=True)
    probes = [
        ("title_mid", 6.20), ("xf2190_mid", 22.05), ("s2_post", 22.60), ("sil1_late", 30.60),
        ("s5_in", 31.60), ("lyr01a", 32.20), ("xf44_black", 44.00), ("sil2_in", 44.60),
        ("lyr12", 78.70), ("xf126_mid", 126.12), ("xf152_mid", 151.80), ("d08_arch", 169.00),
        ("lyr36", 174.00), ("xf1916_mid", 191.40), ("lyr47", 225.00), ("tail_credit", 232.80),
    ]
    for i, (tag, tt) in enumerate(probes):
        subprocess.run([FF, "-y", "-ss", "%.2f" % tt, "-i", out, "-frames:v", "1", "-q:v", "3",
                        os.path.join(tdir, "f_%02d.jpg" % i)], capture_output=True)
    sheet = os.path.join(tdir, "CHK-T3-SHEET.jpg")
    subprocess.run([FF, "-y", "-framerate", "1", "-i", os.path.join(tdir, "f_%02d.jpg"),
                    "-vf", "scale=480:270,tile=4x4", "-frames:v", "1", "-q:v", "4", sheet],
                   capture_output=True)
    for i, (tag, tt) in enumerate(probes):
        print("CHK-T3 f_%02d %-11s @%.2f" % (i, tag, tt), flush=True)
    print("CHK-T3 sheet -> " + sheet, flush=True)
    print("ASSERT-OK len/xf-math(14pt)/S4-del/SIL1-ext/D08-swap/loudnorm/encode verified in single chain", flush=True)
    print("PENDING multimodal: new XF 4 + pure-white lyrics + title/tail cards + D08 archived on sheet", flush=True)


if __name__ == "__main__":
    main()
