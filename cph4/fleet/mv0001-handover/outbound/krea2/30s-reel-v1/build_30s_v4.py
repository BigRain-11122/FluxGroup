# -*- coding: utf-8 -*-
# build_30s_v4.py - 30秒重制 v4.3 顶级剪辑链（六席评审团版）
# 锚点法: 四主刀句首硬卡(31.14/34.74/36.92/39.18-T)+尾段跨句语义切(导演席收口切表)
# 结构: S1-S7 硬切(A块) → S7|T xfade叠化0.4 → T|S8 xfade叠化0.4(全片唯一) → S8-S10 硬切(B块)
# v4.3 新增: ①导演收口切表(S7=1.9/T=1.8含双肩) ②finishing 站(调色师+摄影指导席必修):
#   统一 35mm 颗粒叠层+暖饱和微推+黑位轻抬+暗角(把 11 帧异种子颗粒熔成一张拷贝=最便宜去AI手段)
# BGM: 原曲段(画面+歌律)·一切AI原生音轨剥离·无字幕·首尾 fade
import subprocess, os, sys

FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
D = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\cloud-v4"
OUT_DIR = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
os.makedirs(OUT_DIR, exist_ok=True)
SONG = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\audio\mv001_source_320k.mp3"

# 导演席收口切表（音频窗 17.5-47.5）:
# S1 17.5-21.9 | S2 -25.9 | S3 -29.4 | S4 -31.14(人声) | S5 -34.74(刻) | S6 -36.92(距今)
# | S7 -38.82 | T -40.22(压「你在橱窗前」整句·金字向她升去) | S8 -42.22(凝视)
# | S9 -45.22(欣赏你双句长持) | S10 -47.5(脸句内0.6s滞留转身·灯熄字存)
# 注: T 裁 1.8s(1.4 净显示+双 dissolve 肩各0.4·肩部在叠化区内=暗接暗不可见);叠化压缩后全片≈29.6s·BGM 同窗
TRIMS = [
    ("KF1_fire_wake", 4.40),
    ("KF2_sweep", 4.00),
    ("KF3_stele", 3.50),
    ("KF4_crown", 1.74),
    ("KF5_columns", 3.60),
    ("KF6_chisel", 2.18),
    ("KF7_hall", 1.90),
    ("KFT_glyphs", 1.80),
    ("KF8_case", 2.00),
    ("KF9_profile", 3.00),
    ("KF10_walkaway", 2.28),
]
XF = 0.4  # 叠化时长
FILM_LEN = None  # 由叠化数学实算(lenA+T+lenB-2*XF)


def main():
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
    lenT = TRIMS[7][1]                            # 1.80
    off1 = lenA - XF
    lenAT = lenA + lenT - XF
    off2 = lenAT - XF
    final_len = lenAT + sum(t for _, t in TRIMS[8:11]) - XF
    print("film length = %.2f" % final_len)

    out = os.path.join(OUT_DIR, "30s_reel_v4.mp4")
    # finishing 站(评审团必修): 统一颗粒+暖饱和微推+黑位轻抬+暗角 —— 全片单一拷贝感
    fin = ("noise=alls=5:allf=t+u,"
           "eq=saturation=1.05:gamma=0.98,"
           "vignette=PI/5,format=yuv420p")
    fc = (
        "[0:v][1:v]xfade=transition=fade:duration=%f:offset=%f[at];"
        "[at][2:v]xfade=transition=fade:duration=%f:offset=%f[ab];"
        "[ab]fade=t=in:st=0:d=0.4,fade=t=out:st=%.2f:d=0.8,%s[v]"
        % (XF, off1, XF, off2, final_len - 0.8, fin)
    )
    cmd = [FF, "-y",
           "-i", A, "-i", T, "-i", B,
           "-ss", "17.5", "-t", "%.2f" % final_len, "-i", SONG,
           "-filter_complex", fc + ";[3:a]afade=t=in:st=0:d=0.3,afade=t=out:st=%.2f:d=1.5[a]" % (final_len - 1.5),
           "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "slow", "-crf", "17",
           "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    subprocess.run(cmd, check=True, capture_output=True)
    print("FINAL", out)


if __name__ == "__main__":
    main()
