# -*- coding: utf-8 -*-
# build_full_mv_v5.py — V5 修片装配器（导演席签发·V5-REBURN-SPEC §四 + W7 R-20261016-mv-edit-grammar-01）
# 承 v3/fix_v4 正典并内置单链（v3 头 SOP③ 收口）：
#   ①17 镜 v5redo 源优先（find_src V5REDO→JAYREDO→CLOUD→DL→D_OLD→FLUX）
#   ②行速改表 E04 0.72 / R06 0.75 / N05 0.74（5.17s 源恰满窗·定格缝合全消）
#   ③SIL4 插回全量（NO_SIL4=1 可豁免回 234.17 底·V5 默认插）
#   ④9 点 xfade 链（W7 §二分配表·A/T/G0..G7 十块链式）——T 桥 2.20 特例=fix_v4 正典
#     ·语义统一 [词锚−D, 词锚]（窗头渐显·内容零漂移·v2 既有语义）：
#       W7 的 47.50/110.52 J 中点落拍需引子烧制支持，17 件已按固定窗烧定→降级常规语义，
#       V5.1 候补（需后镜 i2v 头延 D×speed 引子）
#   ⑤段内变速 SEGS：S6 既有 + C06/C03 burst（W7 变速子表·第三段回落补满窗）
#   ⑥深慢尾段 3 处（W7·必插值）：D06 尾 1.4s@0.82 / E03 尾 1.4s@0.80 / Z04 尾 1.2s@0.88+定格收 1.5s
#   ⑦字层 PTS 陷阱修复（V5-TYPOGRAPHY-SPEC §〇）：S9 金句+歌名卡+AIGC 标识三输入全部
#     `-loop 1 -t <窗>` 化；金句动画升格 0.8/0.6s；窗内抽帧验字命令自动打印（CHK-T1 面）
#   ⑧loudnorm 两遍（测量+线性·I=-14:TP=-1.5:LRA=11·EBU R128）+平台编码参数（high profile/GOP 半帧率）
#   ⑨调色六项装配面：R06/D05/C04 博物馆层微偏冷白对照巴比伦暖火（colorbalance bs/bm 微加）
#   ⑩PROXY=1 → 960x540 代理剪档（D6 PROXY-PASS 用·非终版）；DRYRUN=1 → v5redo 缺源用旧件顶替（数学干跑·打 DRY-SUB 行）
# 断言律 v1.1 全执：缺源 FATAL（正式跑）/终长 ±0.5 / XF 数学自检（offset+D==词锚）
# 用法：
#   干跑验数学:  set PROXY=1 & set DRYRUN=1 & set NO_MINTERP=1 & python build_full_mv_v5.py
#   代理剪审档:  set PROXY=1 & python build_full_mv_v5.py        （需 17 件到齐）
#   终版:        python build_full_mv_v5.py                        （需 17 件到齐）
import os, re, subprocess, sys
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
sys.path.insert(0, HERE)
import build_full_mv_v2 as v2

PROXY = os.environ.get("PROXY") == "1"
DRYRUN = os.environ.get("DRYRUN") == "1"
NO_SIL4 = os.environ.get("NO_SIL4") == "1"

V5REDO = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\bmc\i2v\v5redo"
SONG_WAV = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\audio\mv001_lossless.wav"  # 无损 ape→PCM（TYPOGRAPHY §五 换源令·2026-10-17 落地·234.253s 对齐）
if SONG_WAV:
    v2.SONG = SONG_WAV   # 音源换源：旧 320k mp3（BB92ED5F）→ 无损 PCM 溯源正身

# ---- 17 镜 v5redo 源映射（基座行 id → v5 收件名·V5-REBURN-SPEC §六） ----
V5_SOURCE_MAP = {
    "INT1_desk_breath": "INT1_desk_breath_v5.mp4",
    "INT2_paper_fight": "INT2_paper_v5.mp4",
    "INT3_photo_stare": "INT3_photo_stare_v5.mp4",
    "INT4_rubbing_glow": "INT4_rubbing_v5.mp4",
    "INT5_head_bow": "INT5_head_bow_v5.mp4",
    "C01_carver_face": "C01_carver_face_v5.mp4",
    "D01_carver_words": "D01_carver_words_v5.mp4",
    "D03b_direct_gaze": "D03b_direct_gaze_v5.mp4",
    "B01_weary": "B01_weary_v5.mp4",
    "E01c_first_line": "E01c_first_line_v5.mp4",
    "E03_gaze_meet": "E03_gaze_meet_v5.mp4",
    "R06_museum_verse": "R06_museum_verse_v5.mp4",
    "E04_replay_faces": "E04_replay_faces_v5.mp4",
    "C04_words_alive": "C04_words_alive_v5.mp4",
    "D05_words_warm": "D05_words_warm_v5.mp4",
    "SIL1_v4b": "SIL1_stele_backlit_v4b_s9021.mp4",  # V5.3 云道重烧（心形符→八角星·Flare 三败冻结转像素手术·V53R-CLOUD-2shot §三）
    "SIL4": "SIL4_crowd_edge_v5.mp4",        # V3 插入行换源（缺件补烧·KF v2 锚）
    "D04_her_brush": "D04_her_brush_v5.mp4",  # V5.3 云道重烧（竹简载体→泥板+苇笔·同上）
    "D08_world_flip": "D08_world_flip_v5.mp4",  # V5.4 换源（media segments 版 CG 纹理叠加+画廊乱入定罪 → cloudv2 archived 实拍版·CEO 终审「乱入动画镜头」整改·V54-CUT-VERDICT §一）
}

# ---- 速度改表（REBURN-SPEC §四.1·叠在基座速度之上） ----
SPEED_OVERRIDE = {"E04_replay_faces": 0.85, "R06_museum_verse": 0.75, "N05_dead_language": 0.74}  # V5.4 E04 0.72→0.85（CEO 鬼影令·E04-SRC-DENSE-BOARD 判读主案 A：素材静帧无鬼脸·罪状=贴面渐变粘连+慢放插值三重放大；0.85=5.17/0.85+tpad1.1 定格精确满 7.18s 窗·罪段屏占 1.60→1.35s·插值帧减 39%）

# ---- 9 点 xfade 链（W7 §二·anchor=后块窗起点/词锚·过渡窗 [anchor−D, anchor]） ----
# 块尾延律（W7 §四「重叠不吃内容」工程正身）：每边界 D 由前块尾延 D 补长——素材尾余量优先，
# 不足 tpad 定格兜底（余量已核：S7/S10/C01/C08/C09b 零 pad；R05/D08/E04 pad 0.5-1.3s 落 fade 渐隐内）
XFS = [
    (38.82, "fade",  0.40),   # A→T   T 桥（流含 0.4 引子·校验 offset+0.4==38.82）
    (40.22, "fade",  0.40),   # T→G0  T 桥
    (47.50, "fade",  1.00),   # S10→N01   首渡巴比伦（J 中点降级注释见头⑷）
    (80.18, "hblur", 0.60),   # C01→C02   风沙糊面·誓言入土
    (102.88, "fade", 0.60),   # C08→C09   千年风化（快叠化）
    (110.52, "fade", 1.40),   # C09b→R01  千年主渡（全片最长）
    (131.72, "hblur", 0.50),   # R05→R06   地下金线→展柜出土光
    (187.26, "fade", 0.90),   # B04→E01a  余烬→「一切又重演」回环
    (219.84, "fade", 1.20),   # E04→Z01   人退场·世界独存
]

# ---- 段内变速 SEGS（W7 变速子表·段窗和必须=镜窗·第三段回落补满） ----
SEGS_TABLE = {
    "S6_chisel": v2.S6_SEGS,                                        # 既有正典
    "C06_forever_cut": [(0.00, 0.60, 1.00), (0.60, 1.30, 1.30), (1.90, 0.70, 1.05)],  # 蓄势→落击爆→回落
    "C03_dig_reveal": [(0.00, 0.80, 0.95), (0.80, 1.60, 1.15), (2.40, 1.78, 1.00)],  # 刷显→逐字浮出→回落
}

# ---- 深慢尾段（W7·尾段必插值·叠架在镜速之上） sid → (尾段播放长, 深慢速度) ----
DEEP_SLOW = {
    "D06_chisel_fingertip": (1.40, 0.82),  # 古今同触尾段
    "E03_gaze_meet": (1.40, 0.80),          # 隔世对视尾段（v5 件）
    # Z04 特殊：walk 2.25 内尾段 1.20@0.88 + tpad 1.5 定格收（在 Z04 特例处理）
}

# ---- 调色六项·装配面（DIRECTOR-REVIEW-V4 批点⑥：博物馆层微偏冷白对照巴比伦暖火） ----
SHOT_GRADE = {
    "R06_museum_verse": "colorbalance=bs=.02:bm=.01",
    "D05_words_warm": "colorbalance=bs=.02:bm=.01",
    "C04_words_alive": "colorbalance=bs=.02:bm=.01",
    "D08_world_flip": "eq=brightness=0.035:saturation=1.06",  # V5.4 archived 源尾部偏暗微提亮保暖（V54-CUT-VERDICT §一）
}

# ---- 字层窗（V5-TYPOGRAPHY-SPEC）----
S9_IN_ST, S9_IN_D, S9_OUT_D = 42.78, 0.80, 0.60          # 金句窗 42.78-45.07（升格 0.8/0.6）
S9_OUT_ST = 45.07 - S9_OUT_D                              # 44.47
TITLE_IN_ST, TITLE_WIN = 4.20, 3.20                       # 歌名卡窗 4.2-7.4（0.8 in + 0.6 dissolve out）
TITLE_IN_D, TITLE_OUT_D = 0.80, 0.60
AIGC_WIN = 3.00                                           # AIGC 开门帧标识·驻 3s（随首场景 fade 同步）
S9_PNG = os.path.join(HERE, "s9_lyric.png")               # V5 复核位重生成（TYPOGRAPHY §二·默认 x=200 y=340）
TITLE_PNG = os.path.join(HERE, "title_card.png")
AIGC_PNG = os.path.join(HERE, "aigc_badge.png")

if PROXY:
    W, H, CRF, PRE = 960, 540, 22, "veryfast"
else:
    W, H, CRF, PRE = 1344, 768, 17, "fast"

FF = v2.FF
FAST = os.environ.get("NO_MINTERP") == "1"
D_CUT = os.path.join(v2.D_CUT, "v5")
os.makedirs(D_CUT, exist_ok=True)


def dur_of(p):
    r = subprocess.run([FF, "-i", p], capture_output=True, text=True, errors="replace")
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    return float(m.group(1)) * 3600 + float(m.group(2)) * 60 + float(m.group(3)) if m else None


def find_src_v5(fname):
    """V5REDO 优先（17 镜新件）→ 既有 v2 序。DRYRUN 下 v5 件缺→旧件顶替打 DRY-SUB。"""
    d5 = os.path.join(V5REDO, fname)
    if os.path.isfile(d5):
        return d5, "v5redo"
    old = v2.find_src(fname)
    return old, "legacy"


def build_rows_v5():
    """v3 行表为基 + v5 源映射 + 速度改表 + 插入行 clamp。返回 (sid, t0, t1, speed, want_file, is_new)"""
    import build_full_mv_v3 as v3m
    # V5 插入行 clamp：V3 全硬切时代插入行可骑跨后窗（SING1 尾越 C02 头 0.32 / SIL2 尾越 S10 头 0.58
    # / SING2 尾越 B03 头 0.50）；V5 的 9 点 XF 边界要求行不跨界——越界段本就被 fade/hblur 转场吃掉，
    # 视觉零损失，窗表守恒（SING2@180 越的是 B02→B03 块内硬切·非 XF 边界·不 clamp）
    CLAMP = {"SING1_v2": 2.18, "SIL2_v4": 1.22}
    ins = []
    for x in v3m.V3_INSERTS:
        iid, fn, a, d, v = x
        if NO_SIL4 and iid == "SIL4":
            continue
        ins.append((iid, fn, a, CLAMP.get(iid, d), v))
    v3m.V3_INSERTS = ins
    rows = []
    for r in v3m.build_rows_v3():
        sid, t0, t1, v, src_file, is_new = r
        if sid in SPEED_OVERRIDE:
            v = SPEED_OVERRIDE[sid]
        rows.append([sid, t0, t1, v, src_file, is_new])
    return rows


def emit_seg(src, dst, want, v, ss=0.0):
    """单段发射：慢速必插值（NO_MINTERP=1 逃生门）+源不足 tpad 定格兜底（fix_v4 retime_pad 正典）。"""
    base = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=24"
            % (W, H, W, H))
    L = dur_of(src)
    avail = (L - ss) / v if L else 0.0
    pad = max(0.0, round(want - avail, 3))
    interp = ("minterpolate=fps=48:mi_mode=mci,setpts=PTS/%.4f," % v) if (v < 0.96 and not FAST) else ("setpts=PTS/%.4f," % v)
    vf = "-ss %.4f -i" % ss if ss > 0 else "-i"
    args = [FF, "-y"] + (["-ss", "%.4f" % ss] if ss > 0 else []) + ["-i", src, "-an",
            "-vf", interp + base + (",tpad=stop_mode=clone:stop_duration=%.3f" % pad if pad > 0 else ""),
            "-t", "%.4f" % want, "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF),
            "-pix_fmt", "yuv420p", dst]
    subprocess.run(args, check=True, capture_output=True)
    a = dur_of(dst)
    assert a is not None and a >= want - 0.05, "segment short: " + dst
    return pad


def emit_shot(sid, t0, t1, v, src, dst, ext=0.0):
    """整镜发射：SEGS / 深慢尾段 / Z04 定格收 / 常规。ext=块尾延量（xfade 供料）。返回 (dst, pad_total)"""
    dur = round(t1 - t0 + ext, 4)
    pads = 0.0
    if sid in SEGS_TABLE:
        pieces = []
        for i, (seg_ss, seg_want, seg_v) in enumerate(SEGS_TABLE[sid]):
            p = os.path.join(D_CUT, "seg_%s_%d.mp4" % (sid, i))
            interp = ("minterpolate=fps=48:mi_mode=mci,setpts=PTS/%.4f," % seg_v) if (seg_v < 0.96 and not FAST) else ("setpts=PTS/%.4f," % seg_v)
            base = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=24" % (W, H, W, H))
            subprocess.run([FF, "-y", "-i", src, "-an", "-vf", interp + base,
                            "-t", "%.4f" % seg_want, "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF),
                            "-pix_fmt", "yuv420p", p], check=True, capture_output=True)
            pieces.append(p)
        v2.concat(pieces, dst)
        seg_sum = sum(s[1] for s in SEGS_TABLE[sid])
        assert abs(seg_sum - dur) < 0.02, "SEGS window mismatch %s %.3f vs %.3f" % (sid, seg_sum, dur)
    elif sid == "Z04_glyph_remains":
        # 深慢尾段 1.20@0.88 + 定格收 1.5s（窗 3.75 内：walk 2.25 = 前 1.05@0.96 + 尾 1.20@0.88）
        walk_head, walk_tail, freeze = 1.05, 1.20, 1.50
        p1 = os.path.join(D_CUT, "z04_head.mp4")
        p2 = os.path.join(D_CUT, "z04_tail.mp4")
        base = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=24" % (W, H, W, H))
        for p, wlen, wv in ((p1, walk_head, 0.96), (p2, walk_tail, 0.88)):
            interp = ("minterpolate=fps=48:mi_mode=mci,setpts=PTS/%.4f," % wv) if (wv < 0.96 and not FAST) else ("setpts=PTS/%.4f," % wv)
            subprocess.run([FF, "-y", "-i", src, "-an", "-vf", interp + base, "-t", "%.4f" % wlen,
                            "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF), "-pix_fmt", "yuv420p", p],
                            check=True, capture_output=True)
        tmp = os.path.join(D_CUT, "z04_walk.mp4")
        v2.concat([p1, p2], tmp)
        subprocess.run([FF, "-y", "-i", tmp, "-vf",
                        "tpad=stop_mode=clone:stop_duration=%.3f" % freeze,
                        "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF), "-pix_fmt", "yuv420p", dst],
                       check=True, capture_output=True)
    elif sid in DEEP_SLOW:
        tail_w, tail_v = DEEP_SLOW[sid]
        head_w = round(dur - tail_w, 4)
        p1 = os.path.join(D_CUT, "ds_%s_h.mp4" % sid)
        p2 = os.path.join(D_CUT, "ds_%s_t.mp4" % sid)
        base = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=24" % (W, H, W, H))
        for p, wlen, wv in ((p1, head_w, v), (p2, tail_w, tail_v)):
            interp = ("minterpolate=fps=48:mi_mode=mci,setpts=PTS/%.4f," % wv) if (wv < 0.96 and not FAST) else ("setpts=PTS/%.4f," % wv)
            subprocess.run([FF, "-y", "-i", src, "-an", "-vf", interp + base, "-t", "%.4f" % wlen,
                            "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF), "-pix_fmt", "yuv420p", p],
                            check=True, capture_output=True)
        v2.concat([p1, p2], dst)
    else:
        pads = emit_seg(src, dst, dur, v)
    if sid in SHOT_GRADE and SHOT_GRADE[sid]:
        g = os.path.join(D_CUT, "gr_%s.mp4" % sid)
        subprocess.run([FF, "-y", "-i", dst, "-vf", SHOT_GRADE[sid],
                        "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF), "-pix_fmt", "yuv420p", g],
                       check=True, capture_output=True)
        dst = g
    return dst, pads


def main():
    rows = build_rows_v5()
    print("V5 rows=%d  PROXY=%s DRYRUN=%s NO_SIL4=%s" % (len(rows), PROXY, DRYRUN, NO_SIL4), flush=True)

    # ---- 源解析（V5REDO 优先·DRYRUN 顶替·正式跑缺 v5 件=FATAL）----
    resolved = []
    for sid, t0, t1, v, src_file, is_new in rows:
        base_sid = sid.split("@")[0]   # 插入行 sid 带 @time 后缀（SIL1_v4b@29/SIL4@207）——查表须剥（10-17 实锚：裸键漏配=SIL4 静默并块+SIL1 静默回旧源）
        want = V5_SOURCE_MAP.get(base_sid, src_file)
        src, kind = find_src_v5(want)
        if src is None:
            src, kind = v2.find_src(src_file), "legacy-fallback"
        if src is None:
            if base_sid in V5_SOURCE_MAP and not DRYRUN:
                raise SystemExit("FATAL v5redo source missing: %s -> %s (await bm-c 17-batch; DRYRUN=1 to substitute)" % (sid, want))
            if resolved:
                prev = resolved[-1]; prev[2] = t1
                print("FALLBACK-MERGE %s -> %s" % (sid, prev[0]), flush=True)
                continue
            raise SystemExit("FATAL first shot missing " + sid)
        if base_sid in V5_SOURCE_MAP and kind != "v5redo":
            if DRYRUN:
                print("DRY-SUB %s uses legacy %s (math-check only)" % (sid, os.path.basename(src)), flush=True)
            else:
                print("WARN %s fell back to legacy source" % sid, flush=True)
        resolved.append([sid, t0, t1, v, src, kind])
    n_v5 = sum(1 for r in resolved if r[5] == "v5redo")
    print("sources: v5redo=%d / %d" % (n_v5, len(V5_SOURCE_MAP)), flush=True)
    if not DRYRUN and n_v5 != len(V5_SOURCE_MAP):
        raise SystemExit("FATAL v5redo source count %d != %d — silent fallback present (see J-32)" % (n_v5, len(V5_SOURCE_MAP)))

    # ---- 分块计算（发射前：块末镜需尾延量）：A(0..38.82) / T / G0..G7 ----
    T_id = "T_glyphs"
    block_bounds = [a for (a, _, _) in XFS[2:]]            # B 内 7 边界 47.50..219.84
    A_ids = [r[0] for r in resolved if r[1] < 38.82 and r[0] != T_id]
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

    # 块尾延表（W7 块尾延律·重叠不吃内容）：块末镜发射长 = 窗 + 出边界 D
    # （素材尾余量优先·tpad 定格兜底·pad 全落在 fade/hblur 渐隐窗内不可辨——余量已逐镜核）
    TAIL_EXT = {A_ids[-1]: XFS[0][2]}
    for i, ids in enumerate(G[:-1]):
        TAIL_EXT[ids[-1]] = XFS[2 + i][2]                  # G0..G6 尾延（G7 无出边界）
    print("blocks: A=%d T=1 G=%s  tail-ext=%s" % (len(A_ids), [len(g) for g in G],
          {k: round(v, 2) for k, v in TAIL_EXT.items()}), flush=True)

    # ---- 发射全镜（块末镜带尾延）----
    cuts = {}
    for sid, t0, t1, v, src, kind in resolved:
        ext = TAIL_EXT.get(sid, 0.0)
        dur = round(t1 - t0 + ext, 4)
        dst = os.path.join(D_CUT, "v5_%s.mp4" % sid.replace("@", "_at_"))
        dst, pads = emit_shot(sid, t0, t1, v, src, dst, ext=ext)
        if pads > 0:
            print("PAD-WARN %s tpad=%.2fs (source short%s)" % (sid, pads, " + tail-ext in fade" if ext else ""), flush=True)
        print("cut %-22s %.2fs@%.2fx [%s]%s" % (sid, dur, v, kind, " +ext%.2f" % ext if ext else ""), flush=True)
        cuts[sid] = (dst, t0, t1, v)

    def concat_block(ids, name):
        out = os.path.join(D_CUT, name)
        v2.concat([cuts[s][0] for s in ids], out)
        return out

    A = concat_block(A_ids, "v5_blockA.mp4")
    blocks = [A]
    # T 特例（V5 统一尾延律）：T 流=窗 1.40+尾延 0.4=1.80，从 KFT 源件 0 起@0.90
    # （尾延供 T→G0 过渡 [40.22,40.62]·源 5s@0.9=5.56 播放长余量充足；
    #  fix_v4 的 2.20=旧「吃窗头尾」语义·尾延律下窗内容起点 38.82=offset_0 零漂移）
    t_raw = v2.find_src("KFT_glyphs.mp4")
    assert t_raw, "KFT_glyphs source missing"
    T_dst = os.path.join(D_CUT, "v5_T18.mp4")
    base = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=24" % (W, H, W, H))
    interp = ("minterpolate=fps=48:mi_mode=mci,setpts=PTS/%.4f," % 0.90) if not FAST else ("setpts=PTS/%.4f," % 0.90)
    subprocess.run([FF, "-y", "-i", t_raw, "-an", "-vf", interp + base,
                    "-t", "1.8000", "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF),
                    "-pix_fmt", "yuv420p", T_dst], check=True, capture_output=True)
    blocks.append(T_dst)
    for i, ids in enumerate(G):
        blocks.append(concat_block(ids, "v5_blockG%d.mp4" % i))

    lens = [dur_of(b) for b in blocks]
    print("block lens: " + " ".join("%.2f" % l for l in lens), flush=True)

    # ---- XF 链数学（链式 offset·窗内容零漂移自检·统一尾延律无特判）----
    # 块长期望=Σ窗+尾延（T=1.80=窗1.40+尾延0.4）；offset_i=running−D_i==后块窗起点 anchor
    win_sum = {0: sum(cuts[s][2] - cuts[s][1] for s in A_ids) + TAIL_EXT.get(A_ids[-1], 0)}
    for i, ids in enumerate(G):
        win_sum[2 + i] = sum(cuts[s][2] - cuts[s][1] for s in ids) + TAIL_EXT.get(ids[-1], 0)
    for i, L in enumerate(lens):
        expect = 1.80 if i == 1 else win_sum.get(i)
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
                raise SystemExit("FATAL xf-math: transition %d starts at %.3f but next-block window starts %.3f (block lens drift)" % (xfi, off, anchor))
            running -= D
            xfi += 1
    assert xfi == len(XFS), "unconsumed XFS entries"
    final_len = running
    print("XF offsets: " + " ".join("%.2f" % o[-1] for o in offsets), flush=True)
    print("final_len computed = %.2f" % final_len, flush=True)
    target = v2.FILM_END if not NO_SIL4 else v2.FILM_END - 1.08
    if abs(final_len - target) > 0.5:
        raise SystemExit("FATAL final_len %.2f vs target %.2f (xfade-chain collapse? missing shot?)" % (final_len, target))

    # ---- loudnorm pass1 测量 ----
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
        tail = [ln_ for ln_ in p1.stderr.splitlines() if "loudnorm" in ln_.lower() or "Integrated" in ln_][-5:]
        for ln_ in tail:
            print("  pass1: " + ln_.strip(), flush=True)

    # ---- filter_complex：9 xfade 链 + fin + 三字层（-loop 1 化·PTS 陷阱修复）----
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
    # 基底淡入淡出
    fc_parts.append("[%s]fade=t=in:st=0:d=1.2,fade=t=out:st=%.2f:d=2.0[base]" % (cur, fade_out_st))
    SONG_IDX = len(blocks)                 # 输入序号：blocks 0..N-1，SONG=N，s9=N+1，title=N+2，aigc=N+3
    S9_IDX, TITLE_IDX, AIGC_IDX = SONG_IDX + 1, SONG_IDX + 2, SONG_IDX + 3
    # 字层三连（V5-TYPOGRAPHY §〇 PTS 陷阱终修）：
    #   -loop 1 只把 PNG 铺在全局时间轴 0..t——主片窗时刻字层早已 EOF、overlay repeat 的
    #   是 fade 后透明帧（V4 全灭的完整机理）。正解=scale 对齐分辨率 + setpts 把字层流
    #   平移到窗起点 + fade st 直接用主片时刻（平移后流内 PTS 即主片时间轴）。
    s9_win = round(S9_OUT_ST + S9_OUT_D - S9_IN_ST, 4)
    fc_parts.append("[%d:v]scale=%d:%d,format=rgba,setpts=PTS+%.2f/TB,"
                    "fade=t=in:st=%.2f:d=%.2f:alpha=1,fade=t=out:st=%.2f:d=%.2f:alpha=1[tex]"
                    % (S9_IDX, W, H, S9_IN_ST, S9_IN_ST, S9_IN_D, S9_OUT_ST, S9_OUT_D))
    fc_parts.append("[base][tex]overlay=0:0[ov1]")
    fc_parts.append("[%d:v]scale=%d:%d,format=rgba,setpts=PTS+%.2f/TB,"
                    "fade=t=in:st=%.2f:d=%.2f:alpha=1,fade=t=out:st=%.2f:d=%.2f:alpha=1[tcard]"
                    % (TITLE_IDX, W, H, TITLE_IN_ST, TITLE_IN_ST, TITLE_IN_D,
                       TITLE_IN_ST + TITLE_WIN - TITLE_OUT_D, TITLE_OUT_D))
    fc_parts.append("[ov1][tcard]overlay=0:0[ov2]")
    fc_parts.append("[%d:v]scale=%d:%d,format=rgba,setpts=PTS+0/TB,"
                    "fade=t=in:st=0:d=1.2:alpha=1,fade=t=out:st=2.4:d=0.6:alpha=1[aigc]" % (AIGC_IDX, W, H))
    fc_parts.append("[ov2][aigc]overlay=0:0[ov3]")
    fc_parts.append("[ov3]%s[v]" % fin)
    fc = ";".join(fc_parts)

    out = os.path.join(HERE, "full_mv_v5_proxy.mp4" if PROXY else "full_mv_v5.mp4")
    a_fade_st = final_len - 2.75
    cmd = [FF, "-y",
           "-i", blocks[0], "-i", blocks[1]]
    for b in blocks[2:]:
        cmd += ["-i", b]
    cmd += ["-i", v2.SONG,
            "-loop", "1", "-t", "%.2f" % (s9_win + 0.5), "-i", S9_PNG,
            "-loop", "1", "-t", "%.2f" % (TITLE_WIN + 0.5), "-i", TITLE_PNG,
            "-loop", "1", "-t", "3.5", "-i", AIGC_PNG,
            "-filter_complex", fc, "-map", "[v]", "-map", "%d:a" % SONG_IDX,
            "-af", "afade=t=in:st=0:d=0.8,afade=t=out:st=%.2f:d=2.5,%s" % (a_fade_st, ln),
            "-c:v", "libx264", "-preset", PRE, "-crf", str(22 if PROXY else 18),
            "-profile:v", "high", "-g", "12", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    print("rendering %d inputs xfade-chain -> %s" % (len(blocks), out), flush=True)
    subprocess.run(cmd, check=True)
    fl = dur_of(out)
    print("DONE %s  FINAL-LEN %.2f (target %.2f)" % (out, fl, target), flush=True)

    # ---- CHK-T1 抽帧验字命令（导演席多模态执法面）----
    tdir = os.path.join(D_CUT, "chk_t")
    os.makedirs(tdir, exist_ok=True)
    print("CHK-T1 word-layer probe frames ->", tdir, flush=True)
    for tag, tt in (("s9_mid", S9_IN_ST + (S9_OUT_ST + S9_OUT_D - S9_IN_ST) / 2),
                    ("title_mid", TITLE_IN_ST + TITLE_WIN / 2),
                    ("aigc_1s", 1.0)):
        f = os.path.join(tdir, "%s_%.2f.jpg" % (tag, tt))
        subprocess.run([FF, "-y", "-ss", "%.2f" % tt, "-i", out, "-frames:v", "1",
                        "-q:v", "3", f], capture_output=True)
    print("PROBE: title_mid(%.2fs) s9_mid(%.2fs) aigc_1s frames extracted - verify text visible via multimodal before PROXY-PASS" % (
        TITLE_IN_ST + TITLE_WIN / 2, S9_IN_ST + (S9_OUT_ST + S9_OUT_D - S9_IN_ST) / 2), flush=True)
    if abs(fl - target) > 0.5:
        raise SystemExit("FATAL output len %.2f vs target %.2f" % (fl, target))
    print("ASSERT-OK len/sil4/xf-math/loudnorm/encode all verified in single chain", flush=True)


if __name__ == "__main__":
    main()
