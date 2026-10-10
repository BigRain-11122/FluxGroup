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
    norm = []
    for name, t in TRIMS:
        src = os.path.join(D, name + ".mp4")
        dst = os.path.join(D, "cut_" + name + ".mp4")
        if not os.path.isfile(src):
            print("MISSING", src); sys.exit(1)
        cmd = [FF, "-y", "-i", src, "-t", str(t), "-an",
               "-vf", "scale=1344:768:force_original_aspect_ratio=decrease,pad=1344:768:(ow-iw)/2:(oh-ih)/2,fps=24",
               "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p", dst]
        subprocess.run(cmd, check=True, capture_output=True)
        norm.append(dst)
        print("cut", name, t)

    def concat(files, out):
        lst = os.path.join(D, "list_" + os.path.basename(out) + ".txt")
        with open(lst, "w") as f:
            for x in files:
                f.write("file '" + x.replace("'", "'\"'\"'") + "'\n")
        subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out],
                       check=True, capture_output=True)

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
    # finishing 站(调色席+节奏席 v4.3.1 顺序): 暖饱和微推+黑位轻抬 → 暗角 → 统一颗粒最后
    fin = ("eq=saturation=1.05:gamma=0.98,"
           "vignette=PI/5,"
           "noise=alls=5:allf=t+u,format=yuv420p")
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
