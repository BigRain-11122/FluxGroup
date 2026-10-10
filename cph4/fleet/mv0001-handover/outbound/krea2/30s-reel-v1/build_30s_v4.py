# -*- coding: utf-8 -*-
# build_30s_v4.py - 30秒重制 v4.3.1 顶级剪辑链（十三席评审团版）
# 锚点法: 四主刀句首硬卡(31.14/34.74/36.92/39.18-T)+尾段跨句语义切(导演席收口切表)
# 结构: S1-S7 硬切(A块) → S7|T xfade叠化0.4 → T|S8 xfade叠化0.4(全片唯一) → S8-S10 硬切(B块)
# v4.3.1 修项(第二波席位7/9独立收敛):
#   ①T 裁长 1.80→2.20(文字席P1-2·节奏席复算收敛): 2.20=1.4净显示+双肩0.8·出肩借T尾素材
#     → B块内容窗归位(S8 起 40.22/S9 42.22-45.22/S10 45.22-47.5)·全片=30.00s·BGM同窗收在 47.5 拍点
#   ②S9 金字层(文字席P0-1·受众席叠字不叠脸定谳落地): 「我却在旁静静欣赏你」PNG 层
#     淡入 25.28-25.78(随词起·词起 42.78→片内 25.28)·持有至 26.85·淡出 26.85-27.30(词尽字散)
#     ·27.72 硬切前收干净·层插入点=finishing 站之前(字层吃统一颗粒=熔进一张拷贝)
#   ③finishing 顺序 调色→暗角→颗粒(节奏席P2: 颗粒最后=不被调色扭曲·暗角后颗粒均匀)
#   ④音淡出起点=末句词尾(节奏席P1: 原淡出从歌 46.00 起吞词尾 → 改从词尾 46.14 起)
# BGM: 原曲段(画面+歌律)·一切AI原生音轨剥离·S9 金字层=唯一艺术字层·首尾 fade
# 前置: bm-c 交付后先跑 make_s9_lyric.py 出字层 PNG(用 KF9 实帧选位·避脸避缘避高光)
import subprocess, os, sys

FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
D = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\cloud-v4"
OUT_DIR = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
os.makedirs(OUT_DIR, exist_ok=True)
SONG = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\audio\mv001_source_320k.mp3"
S9_TEXT = os.path.join(OUT_DIR, "s9_lyric.png")  # make_s9_lyric.py 产物(KF9 实帧选位后)

# 导演席收口切表（音频窗 17.5-47.5）:
# S1 17.5-21.9 | S2 -25.9 | S3 -29.4 | S4 -31.14(人声) | S5 -34.74(刻) | S6 -36.92(距今)
# | S7 -38.82 | T -40.22(压「你在橱窗前」整句·金字向她升去) | S8 -42.22(凝视)
# | S9 -45.22(欣赏你双句长持) | S10 -47.5(脸句内0.6s滞留转身·灯熄字存)
# v4.3.1: T 裁 2.2s(1.4 净显示+双肩 0.8·出肩借 T 尾素材=S8 内容窗归位 40.22 起)
#   全片=30.00s·BGM 同窗收在 47.5「爱在西元前」拍点
TRIMS = [
    ("KF1_fire_wake", 4.40),
    ("KF2_sweep", 4.00),
    ("KF3_stele", 3.50),
    ("KF4_crown", 1.74),
    ("KF5_columns", 3.60),
    ("KF6_chisel", 2.18),
    ("KF7_hall", 1.90),
    ("KFT_glyphs", 2.20),
    ("KF8_case", 2.00),
    ("KF9_profile", 3.00),
    ("KF10_walkaway", 2.28),
]
XF = 0.4  # 叠化时长
# S9 金字层时点(文字席 spec·绑定 T=2.20 时间轴)
TXT_IN_ST, TXT_IN_D = 25.28, 0.50    # 淡入=词起随字起
TXT_OUT_ST, TXT_OUT_D = 26.85, 0.45  # 淡出=词尾字散(27.12 脸句起声时字正消)
TXT_ENABLE_END = TXT_OUT_ST + TXT_OUT_D  # 27.30·硬切 27.72 前收干净
A_FADE_OUT_ST = 46.14 - 17.5        # 音淡出起点=末句词尾(歌 46.14·节奏席)


def main():
    if not os.path.isfile(S9_TEXT):
        print("MISSING s9_lyric.png - run make_s9_lyric.py first (needs real KF9 frame for placement)")
        sys.exit(1)
    def concat(files, out):
        lst = os.path.join(D, "list_" + os.path.basename(out) + ".txt")
        with open(lst, "w") as f:
            for x in files:
                f.write("file '" + x.replace("'", "'\"'\"'") + "'\n")
        subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out],
                       check=True, capture_output=True)

    # v4.5 变速档(CEO令 10-10 19:0x「AI感最重=匀速·有快有慢·自己评估」+立意案§二 速度五转折·禁匀速):
    #   邝盛语法「疾配快缓配慢」五段映射: 慢=显影/时间/注视链·快=人声起/凿击·定格=灯灭字存
    #   v=倍速(<1 慢 >1 快)·片内时长不变(收口切表卡点不动)·源裁量=片内时长×v
    SPEEDS = {
        "KF1_fire_wake": 0.85,  # 起·显影 极缓(前奏器乐段)
        "KF2_sweep": 0.95,      # 前奏尾 微缓
        "KF3_stele": 1.06,      # 人声前微催
        "KF4_crown": 1.16,      # 人声起 拍点脆
        "KF5_columns": 1.00,    # 基准锚
        "KF7_hall": 0.82,       # 「距今已经三千七百多年」=时间本身 极缓拉远
        "KFT_glyphs": 0.90,    # 金字悬浮缓(全片唯一叠化桥)
        "KF8_case": 0.92,       # 凝视缓入
        "KF9_profile": 0.87,    # 情感峰最缓(机位锁死·呼吸微动)
    }
    # S6 凿击burst: 近刀常速→冲击加速(段内变速·落凿击冲击帧)
    S6_SEGS = [(0.0, 0.90, 1.05), (0.945, 1.28, 1.38)]
    # S10 走远减速→定格 0.5s(灯灭字存·2001 年代 MV 经典定格收)
    S10_WALK, S10_FREEZE = (1.78, 0.96), 0.50

    def retime(src, dst, ss, film_dur, v, extra=""):
        vf = ("setpts=PTS/%.4f,scale=1344:768:force_original_aspect_ratio=decrease,"
              "pad=1344:768:(ow-iw)/2:(oh-ih)/2,fps=24%s" % (v, extra))
        # -t 在 -i 后=输出侧选项·作用于 setpts 后的片内时间线 → 必须截片内时长(勿乘 v·乘 v 截短镜头=断淡出/丢定格)
        cmd = [FF, "-y", "-ss", "%.4f" % ss, "-i", src, "-t", "%.4f" % film_dur, "-an",
               "-vf", vf,
               "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p", dst]
        subprocess.run(cmd, check=True, capture_output=True)

    norm = []
    for name, t in TRIMS:
        src = os.path.join(D, name + ".mp4")
        if not os.path.isfile(src):
            print("MISSING", src); sys.exit(1)
        dst = os.path.join(D, "cut_" + name + ".mp4")
        if name == "KF6_chisel":
            pieces = []
            for i, (ss, fd, v) in enumerate(S6_SEGS):
                p = os.path.join(D, "cut_s6_%d.mp4" % i)
                retime(src, p, ss, fd, v)
                pieces.append(p)
            concat(pieces, dst)
            print("cut KF6_chisel burst %s" % (S6_SEGS,))
        elif name == "KF10_walkaway":
            # tpad 在流尾·输出 -t 帽会连定格一起截(实测 1.79s 丢定格→块短→视频流早终断淡出)
            # 正法=链内 trim 先截走段→tpad 接定格(clone)·-t 只做 2.28 总帽兜底
            fd, v = S10_WALK
            fx = (",trim=duration=%.4f,setpts=PTS-STARTPTS,"
                  "tpad=stop_mode=clone:stop_duration=%.2f" % (fd, S10_FREEZE))
            retime(src, dst, 0.0, fd + S10_FREEZE, v, extra=fx)
            print("cut KF10_walkaway %.2fs@%.2fx + freeze %.2fs" % (fd, v, S10_FREEZE))
        else:
            v = SPEEDS[name]
            retime(src, dst, 0.0, t, v)
            print("cut", name, t, "@%.2fx" % v)
        norm.append(dst)

    A = os.path.join(D, "blockA.mp4")
    B = os.path.join(D, "blockB.mp4")
    concat(norm[0:7], A)
    concat(norm[8:11], B)
    T = norm[7]
    print("blocks built")

    lenA = sum(t for _, t in TRIMS[0:7])          # 21.32
    lenT = TRIMS[7][1]                            # 2.20
    off1 = lenA - XF                              # 20.92
    lenAT = lenA + lenT - XF                      # 23.12
    off2 = lenAT - XF                             # 22.72 → S8 内容窗=歌 40.22
    final_len = lenAT + sum(t for _, t in TRIMS[8:11]) - XF   # 30.00
    print("film length = %.2f" % final_len)

    out = os.path.join(OUT_DIR, "30s_reel_v4.mp4")
    # finishing 站(调色席+节奏席 v4.3.1 顺序): 调色→暗角→颗粒
    # v4.4 克制档(CEO 令 10-10 18:1x「做旧要克制·像2000前后古早MV电影」):
    #   罩染减半(去黄绿水洗)·黑位只轻抬 0.010 去数字黑(对比不压·crushed 保住)·
    #   饱和 .97(留琥珀)·暗角 PI/5·颗粒 9→6(5279 细颗粒)·gamma/contrast 还原
    fin = ("colorbalance=rs=.03:gs=.005:bs=-.03:rm=.02:gm=.005:bm=-.02:rh=.04:gh=.01:bh=-.05,"
           "curves=all='0/0.010 0.5/0.50 1/0.99',"
           "eq=saturation=.97,"
           "vignette=PI/5,"
           "noise=alls=6:allf=t+u,format=yuv420p")
    fc = (
        "[0:v][1:v]xfade=transition=fade:duration=%f:offset=%f[at];"
        "[at][2:v]xfade=transition=fade:duration=%f:offset=%f[ab];"
        "[ab]fade=t=in:st=0:d=0.4,fade=t=out:st=%.2f:d=0.8[base];"
        "[4:v]format=rgba,fade=t=in:st=%.2f:d=%.2f:alpha=1,fade=t=out:st=%.2f:d=%.2f:alpha=1[tex];"
        "[base][tex]overlay=0:0:enable='between(t,%.2f,%.2f)'[ov];"
        "[ov]%s[v]"
        % (XF, off1, XF, off2, final_len - 0.8,
           TXT_IN_ST, TXT_IN_D, TXT_OUT_ST, TXT_OUT_D,
           TXT_IN_ST, TXT_ENABLE_END, fin)
    )
    cmd = [FF, "-y",
           "-i", A, "-i", T, "-i", B,
           "-ss", "17.5", "-t", "%.2f" % final_len, "-i", SONG,
           "-loop", "1", "-framerate", "24", "-i", S9_TEXT,
           "-filter_complex",
           fc + ";[3:a]afade=t=in:st=0:d=0.3,afade=t=out:st=%.2f:d=%.2f[a]"
           % (A_FADE_OUT_ST, final_len - A_FADE_OUT_ST),
           "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "slow", "-crf", "17",
           "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(e.stderr.decode("utf-8", "replace") if e.stderr else "(no stderr)")
        sys.exit(1)
    print("FINAL", out)


if __name__ == "__main__":
    main()
