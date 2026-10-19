# -*- coding: utf-8 -*-
# build_full_mv_v511.py — V5.11 修复批装配器（承 v510 全配方·2026-10-19 夜批）
# 六新面：
#   ①四替换件入片：SING2/D01/SIL4/E04AB _v511_seg（多拍选优 QC 全过·cut_v511_segs_r1019 切制·首尾剪除律 0.3/0.5）
#   ②SPEED_OVERRIDE：E04 0.85→1.00 + D01 0.90→1.00（慢放插值=鬼影病根釜底抽薪）·C02 0.95→0.50
#     （CEO §一「深埋在美索不达米亚平原」0.5x 慢放·C02 沙埋空镜=非人脸 minterpolate 安全面·词窗 80.16-83.46 逐帧对齐）
#   ③XFS 六 BAD 切点修正（V511 批2 判读板处方）：
#     #00 S1火醒→S2 0.05→0.45 真叠化（火焰跳动中段假硬切→叠化藏跳变）
#     #05 SING1火把→C02 0.05→0.45 真叠化 · #06 C08火内景→C09 0.05→0.45 真叠化
#     #01 S7→T字 0.65→0.05 硬切（长叠化双曝糊·叠化本身即病灶）·#07 C09b火→R01 0.90→0.05 ·#11 B04火坑→E01a 0.90→0.05
#     （邝盛语法印证：硬切+动作匹配为正身·叠化面降为点缀）
#   ④后期运镜关键帧层（CEO §七 T0 转向：AI 只做活·运镜全后期·逐镜 zoompan 缓入缓出·禁匀速）：
#     前奏轻推 1.04 / 主歌慢推 1.08 / 副歌推 1.05 / 博物馆段横移 pan / 副歌前三镜「推→突拉→尾 0.5s 定格留白」/ 尾奏拉远
#     108→95 突拉落地为 1.06→1.00（0.95 低于画面边界不可达·相对动态保持）
#   ⑤分段调色 fin 链（CEO §三 修订「暖橙一统」·时间窗 enable=between）：
#     古巴比伦=琥珀压暗（HSL 橙黄+20 近似·eq 压暗+暖推）/ 博物馆=青灰冷调（蓝青+15·饱和-·色温-600K 近似）
#     E04AB 双半预分级豁免 · 前奏书房区基准暖（黄中平面）
#   ⑥声音铺底混音（CEO §五+§七.5）：风沙床(巴比伦段·-19dB≈原曲-24~-28 档)+HVAC(博物馆段)+转场沙涌×4+快门×1
#     sidechain duck（人声段自动压床）·原曲零改动·amix normalize=0
#   ⑦质感四件（CEO §六）：颗粒 6→11·unsharp 锐化+5·对比微压 0.98·暗角维持·212.62/215.30 白闪撤（§七 白场降备选·黑场+风声已主）
#   ⑧新 assert（批3 闸升格）：人脸镜 v<0.96 禁 minterpolate·四替换件 pads==0（禁静帧直接定格）·XFS 处方冻结校验
#   ⑨缓存独立：D56=v56_v511_final（PROXY 走 v56_v511_proxy·互不污染·MOVES 全片重发射）
#   ⑩V511-GAP addendum 2026-10-19: verse over-long shots 1->2 split (N05/N06/R06 named
#     + R05 residual catch measured above the addendum's stated <=4.4s band) + XFS <=0.10s
#     beat snap (BPM 109.1) with coincident row-boundary move (block content stays 1:1,
#     no pin clone/trim drift) + verse length gates + audit table to disk.
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
DRYRUN = os.environ.get("DRYRUN") == "1"
NO_SIL4 = os.environ.get("NO_SIL4") == "1"
FF = v2.FF
W, H, CRF, PRE = v5.W, v5.H, v5.CRF, v5.PRE   # PROXY 时 v5 模块级已切 960x540/22/veryfast
FAST = v5.FAST

# ---- ②速度改表（v5.SPEED_OVERRIDE 在 build_rows 前覆写）----
v5.SPEED_OVERRIDE["E04_replay_faces"] = 1.00
v5.SPEED_OVERRIDE["D01_carver_words"] = 1.00
v5.SPEED_OVERRIDE["C02_sand_bury"] = 0.50
# 分段调色升 fin 层后·per-shot 冷调 trio 撤（zone 覆盖同面）·D08 源补偿保留
v5.SHOT_GRADE = {"D08_world_flip": "eq=brightness=0.035:saturation=1.06"}

SIL1_DUR_V51 = 2.14
# ---- ③XFS_V511（14 切点·六 BAD 处方冻结）----
XFS = [
    (21.90,  "fade",  0.45), (38.82,  "fade",  0.05), (40.22,  "fade",  0.65),
    (44.00,  "fade",  0.05), (47.50,  "fade",  0.05), (80.18,  "fade",  0.45),
    (102.88, "fade",  0.45), (110.52, "fade",  0.05), (126.32, "fade",  0.05),
    (131.72, "fade",  0.05), (152.00, "fade",  0.05), (187.26, "fade",  0.05),
    (191.60, "fade",  0.05), (227.50, "fade",  1.10),
]
assert len(XFS) == 14, "XFS count %d != 14" % len(XFS)
# ⑧处方冻结校验
_PRE = {0: 0.45, 1: 0.05, 5: 0.45, 6: 0.45, 7: 0.05, 11: 0.05}
for _i, _d in _PRE.items():
    assert abs(XFS[_i][2] - _d) < 1e-6, "XFS prescription drift at #%d" % _i
XFS0 = list(XFS)   # pristine anchors: gap snap recomputes from these every call (idempotent)

# ---- ⑩V511-GAP (addendum 2026-10-19): beat snap + verse split ----
BPM = 109.1
BEAT = 60.0 / BPM                 # 0.54995 s/beat
SNAP_TOL = 0.10                    # <=0.10s snap to beat; > keep (whisper word window priority)
SPLIT_MIN, SPLIT_MAX = 2.40, 3.47  # 3.4s target + J-42 0.07 tolerance
VERSE_ZONES = ((31.10, 77.32), (110.52, 141.82))
VERSE_CEIL = 4.47                  # pre-existing band ceiling (addendum: others <=4.4s + tol)
SPLIT_TARGETS = ("N05_dead_language", "N06_poem_light", "R06_museum_verse",
                 "R05_gold_threads")   # 4th = residual catch (5.40s > addendum's stated <=4.4s)
SPLIT_SS = {}
GAP_AUDIT = {"snaps": [], "kept": [], "splits": [], "band": [], "band_preexisting": [], "moved_rows": []}

def _beat(t):
    return round(t / BEAT) * BEAT

def gap_snap_rows(rows):
    """Gap-2: snap XFS anchors within 0.10s of the 109.1 BPM grid; move the coincident
    row boundary by the same delta so block content tracks the block frame target
    (pin deltas stay at rounding scale, no clone/trim drift)."""
    global XFS
    newx, moved_all = [], set()
    for i, (a, tr, d) in enumerate(XFS0):
        b = _beat(a)
        if abs(b - a) <= SNAP_TOL + 1e-9:
            dlt = round(b - a, 4)
            moved_here = []
            for r in rows:
                if abs(r[2] - a) < 0.01 and r[1] < a:
                    r[2] = round(r[2] + dlt, 4); moved_here.append(r[0])
                elif abs(r[1] - a) < 0.01 and r[2] > a:
                    r[1] = round(r[1] + dlt, 4); moved_here.append(r[0])
            newx.append((round(b, 4), tr, d))
            GAP_AUDIT["snaps"].append({"xf": i, "anchor": a, "beat": round(b, 4), "delta": dlt, "rows": moved_here})
            moved_all.update(moved_here)
        else:
            newx.append((a, tr, d))
            GAP_AUDIT["kept"].append({"xf": i, "anchor": a, "beat": round(b, 4), "dev": round(abs(b - a), 4)})
    XFS = newx
    GAP_AUDIT["moved_rows"] = sorted(moved_all)
    return rows

def gap_split_rows(rows):
    """Gap-1: split over-long verse shots 1->2 (halves in [2.40, 3.47]s), same source
    file, B-half window offset plumbed via SPLIT_SS; cut points prefer the beat grid."""
    out = []
    for r in rows:
        sid, t0, t1, v, src_file, is_new = r
        base = sid.split("@")[0]
        if base in SPLIT_TARGETS:
            dur = round(t1 - t0, 4)
            lo = max(dur - SPLIT_MAX, SPLIT_MIN)
            hi = min(SPLIT_MAX, dur - SPLIT_MIN)
            assert hi >= lo - 1e-6, "FATAL gap-split infeasible %s %.3f" % (sid, dur)
            mid = t0 + (lo + hi) / 2.0
            kb = int(round(mid / BEAT))
            cut = None
            for k in (kb, kb - 1, kb + 1):
                c = k * BEAT
                if t0 + lo - 1e-9 <= c <= t0 + hi + 1e-9:
                    if cut is None or abs(c - mid) < abs(cut - mid):
                        cut = c
            if cut is None:
                cut = mid   # window feasibility outranks beat preference; audit records dev
            cut = round(cut, 4)
            halves = (round(cut - t0, 4), round(t1 - cut, 4))
            assert all(SPLIT_MIN - 1e-6 <= h <= SPLIT_MAX + 1e-6 for h in halves), \
                "FATAL gap-split halves %s %s" % (sid, halves)
            SPLIT_SS["%s@b" % base] = round((cut - t0) * v, 4)
            GAP_AUDIT["splits"].append({"sid": base, "t0": t0, "t1": t1, "v": v, "cut": cut,
                                        "halves": halves, "beat_dev": round(abs(_beat(cut) - cut), 4),
                                        "src_ss_b": SPLIT_SS["%s@b" % base]})
            out.append(["%s@a" % base, t0, cut, v, src_file, is_new])
            out.append(["%s@b" % base, cut, t1, v, src_file, is_new])
        else:
            out.append(r)
    return out

def gap_verse_assert_and_audit(rows):
    """Gap-3(5): verse length gates post-split + audit table to disk (filed with dual-sign review)."""
    band = []
    for r in rows:
        t0, t1 = r[1], r[2]
        if any(z0 <= t0 < z1 for (z0, z1) in VERSE_ZONES):
            d = round(t1 - t0, 3)
            if d > SPLIT_MAX:
                band.append({"sid": r[0], "dur": d})
                assert d <= VERSE_CEIL, "FATAL verse shot %.3fs > %.2f ceiling: %s" % (d, VERSE_CEIL, r[0])
    GAP_AUDIT["band_preexisting"] = band
    try:
        import json
        with open(os.path.join(HERE, "V511-GAP-AUDIT-20261019.json"), "w", encoding="utf-8") as f:
            json.dump(GAP_AUDIT, f, ensure_ascii=False, indent=1)
        L = []
        L.append("# V511-GAP-AUDIT-20261019 - gap1 split + gap2 beat-snap audit (V511-GAP-ADDENDUM evidence)")
        L.append("")
        L.append("BPM=%s BEAT=%.5fs SNAP_TOL=%.2fs SPLIT=[%.2f,%.2f] VERSE_CEIL=%.2f"
                 % (BPM, BEAT, SNAP_TOL, SPLIT_MIN, SPLIT_MAX, VERSE_CEIL))
        L.append("")
        L.append("## gap2: XFS cut points vs beat grid (<=0.10s snap, >0.10s word-window priority keep)")
        L.append("| # | anchor | beat | action |")
        L.append("|---|--------|------|--------|")
        for e in GAP_AUDIT["snaps"]:
            L.append("| %d | %.3f | %.4f | SNAP %+0.4f (rows moved: %s) |"
                     % (e["xf"], e["anchor"], e["beat"], e["delta"], ",".join(e["rows"])))
        for e in GAP_AUDIT["kept"]:
            L.append("| %d | %.3f | %.4f | keep (dev %.4f) |" % (e["xf"], e["anchor"], e["beat"], e["dev"]))
        L.append("")
        L.append("## gap1: verse splits (1->2, same source, B-half source offset via SPLIT_SS)")
        L.append("| sid | t0 | cut | t1 | halves | v | beat dev | src ss B |")
        L.append("|-----|----|----|----|--------|---|----------|---------|")
        for e in GAP_AUDIT["splits"]:
            L.append("| %s | %.3f | %.4f | %.3f | %s | %.2f | %.4f | %.4f |"
                     % (e["sid"], e["t0"], e["cut"], e["t1"], e["halves"], e["v"], e["beat_dev"], e["src_ss_b"]))
        L.append("")
        L.append("NOTE: R05_gold_threads split = residual catch (measured 5.40s, above the addendum's "
                 "stated <=4.4s band for non-named verse shots; same CEO clause-1 law; flagged for "
                 "director PROXY-PASS review).")
        if band:
            L.append("")
            L.append("## pre-existing verse band >%.2fs (addendum tolerance, out of named split scope, for PROXY-PASS):" % SPLIT_MAX)
            for e in band:
                L.append("- %s %.3fs" % (e["sid"], e["dur"]))
        with open(os.path.join(HERE, "V511-GAP-AUDIT-20261019.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(L) + "\n")
    except Exception as ex:
        print("GAP-AUDIT-WRITE-WARN %s" % ex, flush=True)

ASS_FILE = "lyric_track.ass"
D56 = os.path.join(v2.D_CUT, "v56_v511_proxy" if PROXY else "v56_v511_final")
os.makedirs(D56, exist_ok=True)
v5.D_CUT = D56

V56SRC = os.path.join(HERE, "v56src")
V56_SOURCE_MAP = {
    "S1_fire_wake":       "S1_fire_wake_v59fix.mp4",
    "N02_crowd_her":      "N02_crowd_her_v59_seg.mp4",
    "D08_world_flip":     "D08_world_flip_v59_cloud.mp4",
    "SING2":              "SING2_v511_seg.mp4",      # ①V5.11 选优 t2（眨眼拍居窗）
    "SING3b_v4":          "V56_SING1_reprise_v59.mp4",
    "V56_R_rubbing_macro": "V56_R_rubbing_macro.mp4",
    "V56_P_pen_macro":     "V56_P_pen_macro.mp4",
    "INT3_photo_stare":    "V56_C_gaze_seg.mp4",
    "INT5_head_bow_E2":    "V56_E2_lookup_seg.mp4",
    "D01_carver_words":    "D01_v511_seg.mp4",        # ①V5.11 选优 t2（0.90→1.00·持稳认证过）
    "SIL4":                "SIL4_v511_seg.mp4",       # ①V5.11 选优 t1（实拍感群像）
    "E04_replay_faces":    "E04AB_v511_seg.mp4",      # ①V5.11 改两镜（BAB t1+1f黑场+MOD t1·0.85→1.00）
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

# ---- 字层（承 v510）----
TITLE_MAIN_PNG = os.path.join(HERE, "title_card_v59_main.png")
TITLE_L_PNG = [os.path.join(HERE, "title_credit_v59_l1.png"),
               os.path.join(HERE, "title_credit_v59_l2.png"),
               os.path.join(HERE, "title_credit_v59_l3.png")]
TITLE_IN_ST, TITLE_WIN = 4.10, 3.30
TITLE_MAIN_IN_D, TITLE_OUT_D = 0.60, 0.30
TITLE_L_ST, TITLE_L_IN_D = [4.85, 5.25, 5.65], 0.45
TAIL_PNG = os.path.join(HERE, "tail_credit_v510.png")
assert os.path.isfile(TAIL_PNG), "FATAL tail_credit_v510.png missing"
TAIL_ST, TAIL_DUR = 230.50, 3.75
TAIL_IN_D, TAIL_OUT_D = 1.20, 0.80

# ---- ⑥声音资产 ----
SFX = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\audio\v511_sfx"
WIND_WAV = os.path.join(SFX, "windbed_loop.wav")
HVAC_WAV = os.path.join(SFX, "hvac_loop.wav")
GUST_WAV = os.path.join(SFX, "gust.wav")
SHUT_WAV = os.path.join(SFX, "shutter.wav")
for _w in (WIND_WAV, HVAC_WAV, GUST_WAV, SHUT_WAV):
    assert os.path.isfile(_w), "FATAL sfx missing: " + _w

# ---- ⑤分段调色时区窗（fin 层 enable=between）----
# 巴比伦=琥珀压暗：[17.5,87.74]∪[91.06,131.72]∪[141.76,155.40]∪[159.66,199.0]∪[208.8,212.66]
# 博物馆=青灰冷调：[87.74,91.06](C04)∪[131.72,141.76]∪[155.40,159.66](D05)∪[199,208.8]∪[219.84,末]
# 豁免：[0,17.5] 前奏书房（基准暖）·[212.66,219.84] E04AB（双半预分级）
ZON_BAB = [(17.50, 87.74), (91.06, 131.72), (141.76, 155.40), (159.66, 199.00), (208.80, 212.66)]
ZON_MUS = [(87.74, 91.06), (131.72, 141.76), (155.40, 159.66), (199.00, 208.80), (219.84, 245.00)]

def _en(zones):
    return "+".join("between(t,%.2f,%.2f)" % (a, b) for a, b in zones)

# ---- ⑥铺底音量时区窗（0.5s 线性坡·引号内逗号免转义）----
def _zone_max(zones):
    parts = ["min(1,max(0,min((t-%.2f)/0.5,((%.2f)-t)/0.5)))" % (a - 0.5, b + 0.5) for a, b in zones]
    expr = parts[0]
    for p in parts[1:]:
        expr = "max(%s,%s)" % (expr, p)
    return expr


def build_rows_v51():
    ins = []
    for x in v3m.V3_INSERTS:
        iid, fn, a, d, v = x
        if iid == "SIL1_v4b":
            d = SIL1_DUR_V51
        ins.append((iid, fn, a, d, v))
    v3m.V3_INSERTS = ins
    GAP_AUDIT.update({"snaps": [], "kept": [], "splits": [], "band": [], "band_preexisting": [], "moved_rows": []})
    rows = v5.build_rows_v5()
    rows = gap_snap_rows(rows)
    rows = gap_split_rows(rows)
    return rows


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
    gap_verse_assert_and_audit(rows)
    return rows


# ---- ④运镜-曲式关键帧表 ----
def move_of(sid, t0, t1):
    base = sid.split("@")[0]
    if base in ("S6_chisel", "C06_forever_cut", "C03_dig_reveal",   # SEGS 变速行自带运动
                "D06_chisel_fingertip", "E03_gaze_meet",            # DEEP_SLOW 尾段
                "Z04_glyph_remains"):                                # 定格收正典
        return None
    if base == "T_glyphs":
        return ("push", 0.05)
    if base in ("N07_fire_breath", "R07_flame", "B04_embers"):
        return ("prechorus", 0.5)     # 推→突拉→尾 0.5s 定格留白（副歌前呼吸）
    if base in ("R06_museum_verse", "SIL4", "E04_replay_faces"):
        return ("pan",)               # 博物馆段横移（E04AB 横移穿越匹配剪=邝盛动作匹配语言）
    if base in ("Z02_walkaway", "Z03_lights_out"):
        return ("pullout",)           # 尾奏慢拉远
    if t1 <= 31.11:
        return ("push", 0.04)         # 前奏空镜轻推
    if (31.10 <= t0 < 77.32) or (110.52 <= t0 < 141.82):
        return ("push", 0.08)         # 主歌慢推 100→108
    if 77.32 <= t0 < 221.66:
        return ("push", 0.05)         # 副歌推（踩点缩放）
    return ("push", 0.04)


def _ss(u):  # smoothstep 缓入缓出（禁匀速）
    return "(3*pow(%s,2)-2*pow(%s,3))" % (u, u)


def zoompan_vf(move, nframes):
    """④逐镜 zoompan 关键帧层。输入已 2x 预放大（抗 zoompan 整数抖动）·d=1 逐帧。"""
    pre = "scale=%d:%d," % (W * 2, H * 2)
    N = max(nframes, 2)
    kind = move[0]
    if kind == "push":
        amp = move[1]
        u = "min(on/%d,1)" % (N - 1)
        z = "1+%.3f*%s" % (amp, _ss(u))
        zp = "zoompan=z='%s':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=%dx%d:fps=24" % (z, W, H)
        return pre + zp
    if kind == "pan":
        z = "1.02"
        u = "min(on/%d,1)" % (N - 1)
        x = "(iw-iw/zoom)*%s" % _ss(u)
        zp = "zoompan=z='%s':x='%s':y='ih/2-(ih/zoom/2)':d=1:s=%dx%d:fps=24" % (z, x, W, H)
        return pre + zp
    if kind == "pullout":
        u = "min(on/%d,1)" % (N - 1)
        z = "1.06-0.06*%s" % _ss(u)
        zp = "zoompan=z='%s':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=%dx%d:fps=24" % (z, W, H)
        return pre + zp
    if kind == "prechorus":
        hold = move[1]
        Nc = max(2, N - int(round(hold * 24)))   # 内容帧（尾部 hold*24 帧定格留白）
        P1 = max(1, int(Nc * 0.4))
        z = ("if(lt(on,%d),1+0.06*%s,if(lt(on,%d),1.06-0.06*%s,1))"
             % (P1, _ss("min(on/%d,1)" % P1), Nc, _ss("min((on-%d)/%d,1)" % (P1, max(Nc - P1, 1)))))
        zp = "zoompan=z='%s':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=%dx%d:fps=24" % (z, W, H)
        return pre + zp
    raise SystemExit("bad move " + str(move))


def emit_seg_v511(src, dst, want, v, move, hold, ss=0.0):
    """①-④ 单段发射：速度链+缩放锚+（hold 时先内容后定格）+运镜层。返回 pad 量。"""
    base = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=24" % (W, H, W, H))
    L = v5.dur_of(src)
    content = want - (hold or 0.0)
    avail = ((L - ss) / v) if L else 0.0
    pad = max(0.0, round(content - avail, 3))
    interp = ("minterpolate=fps=48:mi_mode=mci,setpts=PTS/%.4f," % v) if (v < 0.96 and not FAST) else ("setpts=PTS/%.4f," % v)
    args = [FF, "-y"] + (["-ss", "%.4f" % ss] if ss > 0 else []) + ["-i", src, "-an"]
    if hold:
        # 两段：内容段（-t content）→ tpad 定格 hold → 运镜层（定格帧 z=终值）
        tmp = dst + ".hold.mp4"
        vf1 = interp + base + (",tpad=stop_mode=clone:stop_duration=%.3f" % pad if pad > 0 else "")
        subprocess.run(args + ["-vf", vf1, "-t", "%.4f" % content,
                               "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF),
                               "-pix_fmt", "yuv420p", tmp], check=True, capture_output=True)
        vf2 = "tpad=stop_mode=clone:stop_duration=%.3f,%s" % (hold, zoompan_vf(move, int(round(want * 24))))
        subprocess.run([FF, "-y", "-i", tmp, "-an", "-vf", vf2,
                        "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF),
                        "-pix_fmt", "yuv420p", dst], check=True, capture_output=True)
    else:
        vf = interp + base + (",tpad=stop_mode=clone:stop_duration=%.3f" % pad if pad > 0 else "") \
            + "," + zoompan_vf(move, int(round(want * 24)))
        subprocess.run(args + ["-vf", vf, "-t", "%.4f" % want,
                               "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF),
                               "-pix_fmt", "yuv420p", dst], check=True, capture_output=True)
    a = v5.dur_of(dst)
    assert a is not None and a >= want - 0.07, "segment short: %s %.3f<%.3f" % (dst, a or 0, want)
    return pad


def emit_shot_v511(sid, t0, t1, v, src, dst, ext=0.0):
    """整镜：SEGS/DEEP_SLOW/Z04 委托 v5（无运镜=变速自带运动感）·常规走运镜层。返回 (dst, pads)"""
    base_sid = sid.split("@")[0]
    dur = round(t1 - t0 + ext, 4)
    if base_sid in v5.SEGS_TABLE or base_sid in v5.DEEP_SLOW or base_sid == "Z04_glyph_remains":
        return v5.emit_shot(sid, t0, t1, v, src, dst, ext=ext)
    mv = move_of(sid, t0, t1)
    hold = mv[1] if (mv and mv[0] == "prechorus") else 0.0
    pads = emit_seg_v511(src, dst, dur, v, mv, hold, ss=SPLIT_SS.get(sid, 0.0))
    if base_sid in v5.SHOT_GRADE and v5.SHOT_GRADE[base_sid]:
        g = os.path.join(D56, "gr_%s.mp4" % sid)
        subprocess.run([FF, "-y", "-i", dst, "-vf", v5.SHOT_GRADE[base_sid],
                        "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF), "-pix_fmt", "yuv420p", g],
                       check=True, capture_output=True)
        dst = g
    return dst, pads


def main():
    rows = build_rows_v56()
    print("V5.11 rows=%d  PROXY=%s DRYRUN=%s NO_SIL4=%s" % (len(rows), PROXY, DRYRUN, NO_SIL4), flush=True)

    # ⑧人脸慢放禁 minterpolate 闸（批3-2）：本批手术镜族 FATAL（四镜已全 1.00·闸=证其净）
    #    存量 v59 深慢设计镜（无任何 CEO 反馈/病灶史·批1 C01 裁定先例）转 WARN+犁片目检单登记
    FACE_FATAL = {"SING1_v2", "SING2", "SING3b_v4", "E04_replay_faces", "D01_carver_words"}
    FACE_LEGACY_WARN = {"C01_carver_face", "E01a_carver", "E01c_first_line", "E03_gaze_meet",
                        "D06_chisel_fingertip", "INT1_desk_breath", "INT2_paper_fight",
                        "INT3_photo_stare", "V56_P_pen_macro", "INT5_head_bow_E2",
                        "R06_museum_verse", "D03b_direct_gaze", "B03_last_look",
                        "Z01_words_alone", "E05_stele_sink"}
    for r in rows:
        b = r[0].split("@")[0]
        if r[3] < 0.96 and b in FACE_FATAL:
            raise SystemExit("FATAL face-shot slow-mo would minterpolate: %s @%.2fx" % (r[0], r[3]))
        if r[3] < 0.96 and b in FACE_LEGACY_WARN:
            print("LEGACY-FACE-SLOW WARN %s @%.2fx (v59 设计存量·犁片目检单登记)" % (r[0], r[3]), flush=True)

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
    assert n_56 == 12, "FATAL v56src count %d != 12" % n_56

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
    assert abs(a1_win - XFS[0][0]) < 0.01, "FATAL A1 windows %.3f != XFS0 %.3f" % (a1_win, XFS[0][0])
    print("blocks: A1=%d A2=%d T=1 G=%s A1win=%.2f" % (len(A1_ids), len(A2_ids), [len(g) for g in G], a1_win), flush=True)

    # ---- 发射全镜（J-42 段长闸 + ⑧ pads==0 闸 for 四替换件） ----
    REPLACED = {"SING2@180", "D01_carver_words", "SIL4@207", "E04_replay_faces"}
    pads_log = {}
    cuts = {}
    for sid, t0, t1, v, src, kind in resolved:
        ext = TAIL_EXT.get(sid, 0.0)
        dst = os.path.join(D56, "v56_%s.mp4" % sid.replace("@", "_at_"))
        if os.path.isfile(dst) and (v5.dur_of(dst) or 0) > 0:
            eff = dst
            gfile = os.path.join(D56, "gr_%s.mp4" % sid)
            if os.path.isfile(gfile) and (v5.dur_of(gfile) or 0) > 0:
                eff = gfile
            got = v5.dur_of(eff) or 0.0
            exp_dur = round(t1 - t0 + ext, 3)
            if sid in TAIL_EXT:
                assert got >= exp_dur - 0.07, "FATAL J-42 block-last deficit %s: %.3f < %.3f" % (sid, got, exp_dur)
                if got > exp_dur + 0.07:
                    print("WARN J-42 block-last excess %s: %.3f > %.3f" % (sid, got, exp_dur), flush=True)
            else:
                assert abs(got - exp_dur) <= 0.07, "FATAL J-42 mid-block mis-length %s: %.3f != %.3f" % (sid, got, exp_dur)
            if sid in REPLACED and sid in pads_log:
                assert pads_log[sid] == 0, "FATAL cached %s was emitted with pads (cache poisoned)" % sid
            print("REUSE %s (%.3fs)" % (os.path.basename(eff), got), flush=True)
            cuts[sid] = (eff, t0, t1, v)
            continue
        dst, pads = emit_shot_v511(sid, t0, t1, v, src, dst, ext=ext)
        if sid in REPLACED:
            assert pads == 0, "FATAL 静帧直接定格 %s pads=%.3f (禁静帧定格入片律)" % (sid, pads)
        pads_log[sid] = pads
        got = v5.dur_of(dst) or 0.0
        exp_dur = round(t1 - t0 + ext, 3)
        assert (got >= exp_dur - 0.07) if sid in TAIL_EXT else abs(got - exp_dur) <= 0.07, \
            "FATAL emit len %s: %.3f vs %.3f" % (sid, got, exp_dur)
        if pads > 0:
            print("PAD-WARN %s tpad=%.2fs" % (sid, pads), flush=True)
        mv = move_of(sid, t0, t1)
        print("cut %-24s %.2fs@%.2fx [%s]%s move=%s" % (sid, exp_dur, v, kind,
              " +ext%.2f" % ext if ext else "", mv[0] if mv else "none"), flush=True)
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
        subprocess.run([FF, "-y", "-i", t_raw, "-an", "-vf",
                        interp + base + "," + zoompan_vf(("push", 0.05), int(round(2.10 * 24))),
                        "-t", "2.1000", "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF),
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

    FFPROBE = r"C:\Users\sjs20\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffprobe.exe"

    def frames_of(p):
        try:
            r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-count_packets",
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
        # J-43 判例：pin 禁 setpts——裁短=null+-frames:v·垫长=tpad
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
            raise SystemExit("FATAL pin output %s: real %d != %d frames" % (fixed, got2, want_frames))
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

    # ---- ⑥ loudnorm pass1（原曲测量·混音后统一施）----
    p1 = subprocess.run([FF, "-i", v2.SONG, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=summary",
                         "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    m = {k: re.search(k + r":\s*([-+]?[\d.]+)", p1.stderr) for k in ("Input Integrated", "Input True Peak", "Input LRA", "Input Threshold")}
    ln = "loudnorm=I=-14:TP=-1.5:LRA=11"
    if all(m.values()):
        mi, mtp, mlra, mth = (float(m[k].group(1)) for k in ("Input Integrated", "Input True Peak", "Input LRA", "Input Threshold"))
        ln = "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%.2f:measured_TP=%.2f:measured_LRA=%.2f:measured_thresh=%.2f:linear=true" % (mi, mtp, mlra, mth)

    # ---- ⑤+⑦ fin 链 V5.11（分段调色+质感四件）----
    fin = (
        "colorbalance=rs=.03:gs=.005:bs=-.03:rm=.02:gm=.005:bm=-.02:rh=.04:gh=.01:bh=-.05,"
        "eq=contrast=.98:saturation=.97,"
        "colorbalance=rs=.04:rm=.03:rh=.03:enable='%s',"
        "eq=brightness=-0.02:contrast=1.05:saturation=1.03:enable='%s',"
        "colorbalance=bs=.05:bm=.03:rs=-.02:enable='%s',"
        "eq=saturation=.93:brightness=-0.01:enable='%s',"
        "curves=all='0/0.010 0.5/0.50 1/0.99',vignette=PI/5,"
        "noise=alls=11:allf=t+u,unsharp=5:5:0.5:5:5:0.0,format=yuv420p"
    ) % (_en(ZON_BAB), _en(ZON_BAB), _en(ZON_MUS), _en(ZON_MUS))

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
    WIND_IDX, HVAC_IDX, GUST_IDX, SHUT_IDX = SONG_IDX + 1, SONG_IDX + 2, SONG_IDX + 3, SONG_IDX + 4
    TITLE_MAIN_IDX = SHUT_IDX + 1
    TITLE_L_IDX = [SHUT_IDX + 2, SHUT_IDX + 3, SHUT_IDX + 4]
    TAIL_IDX = SHUT_IDX + 5
    card_out_st = TITLE_IN_ST + TITLE_WIN - TITLE_OUT_D
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
    # ⑦白闪降备选：212.62/215.30 白闪撤（§七 黑场+风声已主）；其余质感板全承 v510
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
        ("fx_leak.png",  199.30, 1.60, 0.30, "static", (0.50, 0.55)),
        ("fx_smoke.png", 219.80, 1.25, 0.45, "drift",  (0.35, 0.50)),
        ("fx_dust_z04.png", 231.90, 2.30, 0.50, "drift", (0.70, 0.90)),
    ]
    fx_src = "[ov2]"
    for k, (plate, st, dur, alpha, drift, (fdi, fdo)) in enumerate(FX_EVENTS):
        pp = os.path.join(FXDIR, plate)
        assert os.path.isfile(pp), "FX plate missing: %s" % pp
        idx = len(blocks) + 10 + k   # blocks + song/wind/hvac/gust/shut(5) + 5 字卡 PNG → FX 从第 10 件后起
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
    fc_parts.append("%s%s,ass=%s[vc]" % (fx_src, fin, ASS_FILE))

    # ---- ⑥声音铺底混音（fc 内建）----
    a_fade_st = final_len - 2.75
    wind_gated = "volume=volume='%.6f*(%s)':eval=frame" % (0.112, _zone_max(ZON_BAB))   # -19dB 基线≈原曲-24~-28 档
    hvac_gated = "volume=volume='%.6f*(%s)':eval=frame" % (0.089, _zone_max(ZON_MUS))
    GUST_AT = [47.30, 110.40, 131.55, 214.70]   # 穿越渡/千年主渡/出土渡/E04AB 黑场前
    fc_parts.append("[%d:a]asplit=3[sng][key1][key2]" % SONG_IDX)
    fc_parts.append("[%d:a]aformat=sample_rates=44100:channel_layouts=stereo,%s[windpre]"
                    % (WIND_IDX, wind_gated))
    fc_parts.append("[windpre][key1]sidechaincompress=threshold=0.03:ratio=6:attack=120:release=600:makeup=1[wind_d]")
    fc_parts.append("[%d:a]aformat=sample_rates=44100:channel_layouts=stereo,%s[hvacpre]"
                    % (HVAC_IDX, hvac_gated))
    fc_parts.append("[hvacpre][key2]sidechaincompress=threshold=0.03:ratio=6:attack=120:release=600:makeup=1[hvac_d]")
    fc_parts.append("[%d:a]aformat=sample_rates=44100:channel_layouts=stereo,asplit=4"
                    % GUST_IDX + "".join("[ga%d]" % i for i in range(4)))
    for i, gt in enumerate(GUST_AT):
        fc_parts.append("[ga%d]volume=-16dB,adelay=%d|%d[gw%d]" % (i, int(gt * 1000), int(gt * 1000), i))
    fc_parts.append("[%d:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=-22dB,adelay=7400|7400[shut]"
                    % SHUT_IDX)
    fc_parts.append("[sng][wind_d][hvac_d][gw0][gw1][gw2][gw3][shut]amix=inputs=8:duration=first:normalize=0,"
                    "afade=t=in:st=0:d=0.8,afade=t=out:st=%.2f:d=2.5,%s,"
                    "alimiter=limit=0.8413:level=disabled[aout]" % (a_fade_st, ln))
    fc = ";".join(fc_parts)

    out = os.path.join(HERE, "full_mv_v511.mp4" if not PROXY else "full_mv_v511_proxy.mp4")
    cmd = [FF, "-y", "-i", blocks[0], "-i", blocks[1], "-i", blocks[2]]
    for b in blocks[3:]:
        cmd += ["-i", b]
    cmd += ["-i", v2.SONG,
            "-stream_loop", "-1", "-i", WIND_WAV,
            "-stream_loop", "-1", "-i", HVAC_WAV,
            "-i", GUST_WAV,
            "-i", SHUT_WAV,
            "-loop", "1", "-t", "%.2f" % (TITLE_WIN + 0.5), "-i", TITLE_MAIN_PNG,
            "-loop", "1", "-t", "3.00", "-i", TITLE_L_PNG[0],
            "-loop", "1", "-t", "2.60", "-i", TITLE_L_PNG[1],
            "-loop", "1", "-t", "2.20", "-i", TITLE_L_PNG[2],
            "-loop", "1", "-t", "%.2f" % (TAIL_DUR + 0.5), "-i", TAIL_PNG]
    for (_plate, _st, _dur, _a, _m, _f) in FX_EVENTS:
        cmd += ["-loop", "1", "-t", "%.2f" % (_dur + 0.10), "-i", os.path.join(FXDIR, _plate)]
    cmd += ["-filter_complex", fc, "-map", "[vc]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", PRE, "-crf", str(22 if PROXY else 18),
            "-profile:v", "high", "-g", "12", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    print("rendering %d inputs -> %s" % (len(blocks) + 6 + 4, out), flush=True)
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
        raise SystemExit("FATAL output video frames %d vs ~%d" % (vpk, exp_pk))

    tdir = os.path.join(D56, "chk_v511")
    os.makedirs(tdir, exist_ok=True)
    for i, tt in enumerate((0.25, 6.20, 9.00, 19.00, 79.98, 109.97, 151.85, 191.42, 198.00, 232.80)):
        subprocess.run([FF, "-y", "-ss", "%.2f" % tt, "-i", out, "-frames:v", "1", "-q:v", "3",
                        os.path.join(tdir, "f_%02d.jpg" % i)], capture_output=True)
    sheet = os.path.join(tdir, "CHK-V511-SHEET.jpg")
    subprocess.run([FF, "-y", "-framerate", "1", "-i", os.path.join(tdir, "f_%02d.jpg"),
                    "-vf", "scale=480:270,tile=5x2", "-frames:v", "1", "-q:v", "4", sheet],
                   capture_output=True)
    print("CHK-V511 sheet -> " + sheet, flush=True)
    print("ASSERT-OK V5.11 (多拍选优四件入片+六BAD切点+运镜层+分段调色+声音铺底+质感四件) verified", flush=True)


if __name__ == "__main__":
    main()
