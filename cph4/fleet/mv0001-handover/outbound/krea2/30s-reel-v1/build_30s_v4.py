# -*- coding: utf-8 -*-
# build_30s_v4.py - 30s重制 v4 顶级剪辑链
# 锚点法: 全部剪辑边界=whisper 词级实测锚(人声31.14起)·音频 -ss 17.5 -t 30
# 结构: S1-S7 硬切(A块) → S7|T xfade叠化0.4 → T|S8 xfade叠化0.4(全片唯一) → S8-S10 硬切(B块)
# BGM: 原曲段(画面+歌律)·一切AI原生音轨剥离·afade 0.3进/1.5出·视频 fade 0.4进/0.8出·无字幕
import subprocess, os, sys

FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
D = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\cloud-v4"
OUT_DIR = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
os.makedirs(OUT_DIR, exist_ok=True)
SONG = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\audio\mv001_source_320k.mp3"

# 锚点推导表（视频t=音频-17.5）:
# S1 0.00-4.40 | S2 4.40-8.40 | S3 8.40-11.90 | S4 11.90-13.64(人声31.14) 
# S5 13.64-17.24(刻34.74) | S6 17.24-19.42(距今36.92) | S7 19.42-21.72(橱窗39.18)
# T 21.72-22.72 | S8 22.72-24.72 | S9 24.72-28.12(欣赏你42.78 脸44.62)
# S10 28.12-30.00 → 总长30.00
TRIMS = [
    ("KF1_fire_wake", 4.40),
    ("KF2_sweep", 4.00),
    ("KF3_stele", 3.50),
    ("KF4_crown", 1.74),
    ("KF5_columns", 3.60),
    ("KF6_chisel", 2.18),
    ("KF7_hall", 2.30),
    ("KFT_glyphs", 1.00),
    ("KF8_case", 2.00),
    ("KF9_profile", 3.40),
    ("KF10_walkaway", 1.88),
]
TOTAL = 30.00
XF = 0.4  # 叠化时长


def main():
    # 1) 归一+裁切每镜(纯画面-an)
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

    # 2) A块=S1-S7 硬切 | B块=S8-S10 硬切
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

    # 3) 双 xfade 叠化(S7|T、T|S8) + 首尾 fade
    lenA = sum(t for _, t in TRIMS[0:7])          # 21.72
    lenT = TRIMS[7][1]                            # 1.00
    off1 = lenA - XF                              # 21.32
    lenAT = lenA + lenT - XF                      # 22.32
    off2 = lenAT - XF                             # 21.92
    out = os.path.join(OUT_DIR, "30s_reel_v4.mp4")
    fc = (
        "[0:v][1:v]xfade=transition=fade:duration=%f:offset=%f[at];"
        "[at][2:v]xfade=transition=fade:duration=%f:offset=%f[ab];"
        "[ab]fade=t=in:st=0:d=0.4,fade=t=out:st=%.2f:d=0.8,format=yuv420p[v]" % (XF, off1, XF, off2, TOTAL - 0.8)
    )
    cmd = [FF, "-y",
           "-i", A, "-i", T, "-i", B,
           "-ss", "17.5", "-t", str(TOTAL), "-i", SONG,
           "-filter_complex", fc + ";[3:a]afade=t=in:st=0:d=0.3,afade=t=out:st=28.5:d=1.5[a]",
           "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "slow", "-crf", "17",
           "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    subprocess.run(cmd, check=True, capture_output=True)
    print("FINAL", out)


if __name__ == "__main__":
    main()
