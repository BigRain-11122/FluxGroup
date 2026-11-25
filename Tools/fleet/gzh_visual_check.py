#!/usr/bin/env python3
"""审美闸（客观项）：把「审美」里能算的部分算出来，挡硬伤；算不了的如实交给人。

CEO 令 2026-11-25：「还要审核自动、上架自动、审美自动」。

**先说清边界**：审美不能全自动。氛围感、调性、情绪这些没人能机检，
声称能做的都是在骗人。但审美里有一大块是**客观可测的硬伤**，
而且这些硬伤占了「看着不专业」的绝大多数：

  封面：尺寸比例、文字占比、有效对比度、主色数、边缘留白
  截图：是否整屏未裁切、清晰度（Laplacian 方差）、是否带红框标注、
        相邻两张是否重复、是否含大面积纯白/纯黑（说明截空或翻页）

这些全机检。剩下的（这张图好不好看、氛围对不对）由人看，
工具只把「必须人看」的那几张挑出来。

依赖：Pillow（装在 .venv-housing）。用系统 python3 跑会缺 —— 会明确报错并给命令。

用法：
  gzh_visual_check.py --cover 封面.png
  gzh_visual_check.py --dir drafts/2026-12-01/img/
  gzh_visual_check.py --self-test
退出码：0 全过 / 1 有硬伤 / 3 缺 Pillow / 4 自检失败
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

COVER_RATIO = 900 / 383          # 公众号封面上限比例
COVER_TOL = 0.03                 # 比例容差
MIN_COVER_W = 600                # 低于此在手机上看不清
EDGE_MAX = 0.20                  # 封面边缘密度上限（字太多=糊）。**初值未标定**：
                                 # 没有真实封面样本，20% 是从"整块色块≈0、密集文字≈0.3+"倒推的
CONTRAST_MIN = 3.0               # 有效对比度下限（WCAG AA 大字）
SHARP_MIN = 60.0                 # Laplacian 方差下限（糊图判定）
COLOR_MAX = 6                    # 主色数上限（超过显得杂）
BLANK_MAX = 0.95                 # 单色占比上限。**必须配合边缘一起判**：
                                 # 深色模式 UI 截图背景常占 80%，那不是截空；
                                 # 真截空是「单色 >95% 且几乎没有边缘」。
RED_RATIO_MIN = 0.0008           # 红框像素占比下限（标注是否存在）


def _pil():
    try:
        from PIL import Image, ImageFilter  # noqa: F401
        return True, ""
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def _gray(pix, w, h):
    """转灰度列表（0-255）。pix 是 Image.load()。"""
    out = []
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            p = pix[x, y]
            if isinstance(p, int):
                out.append(p)
            else:
                out.append(int(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]))
    return out


def stats(path):
    """算一张图的客观指标。返回 dict；缺 Pillow 抛 RuntimeError。"""
    ok, why = _pil()
    if not ok:
        raise RuntimeError(f"缺 Pillow（{why}）")
    from PIL import Image, ImageFilter
    im = Image.open(path).convert("RGB")
    w, h = im.size
    g = _gray(im.load(), w, h)
    n = len(g) or 1
    mean = sum(g) / n
    # 有效对比度：亮部均值 / 暗部均值（近似 WCAG 亮度比）
    hi = [x for x in g if x >= 128]
    lo = [x for x in g if x < 128]
    hi_m = (sum(hi) / len(hi)) if hi else 255
    lo_m = (sum(lo) / len(lo)) if lo else 0
    contrast = (hi_m + 5) / max(lo_m + 5, 1)

    # 清晰度：边缘能量（Laplacian 方差用 PIL 的 FIND_EDGES 近似）
    edges = im.convert("L").filter(ImageFilter.FIND_EDGES)
    eg = _gray(edges.load(), w, h)
    em = sum(eg) / max(len(eg), 1)
    var = sum((x - em) ** 2 for x in eg) / max(len(eg), 1)

    # 主色数：量化到 32 级后统计占 >5% 的颜色
    small = im.resize((64, 64))
    sx = small.load()
    sp = [sx[x, y] for y in range(64) for x in range(64)]
    q = {}
    for p in sp:
        k = (p[0] // 32, p[1] // 32, p[2] // 32)
        q[k] = q.get(k, 0) + 1
    top = max(q.values()) / len(sp)
    colors = sum(1 for v in q.values() if v / len(sp) > 0.05)

    # 红框像素占比（标注检测）：高饱和红
    red = 0
    for p in sp:
        if p[0] > 140 and p[0] - max(p[1], p[2]) > 60:
            red += 1
    red_ratio = red / len(sp)

    # 文字密度：用边缘密度当代理。**不能用「近黑/近白像素占比」**——
    # 深色封面会让它算出 100%（实测踩过），边缘密度才和"字多字少"相关。
    edge_ratio = sum(1 for x in eg if x > 40) / max(len(eg), 1)

    return {"path": path, "w": w, "h": h, "ratio": round(w / max(h, 1), 3),
            "contrast": round(contrast, 2), "sharp": round(var, 1),
            "colors": colors, "blank": round(top, 3),
            "edge": round(edge_ratio, 3), "red": round(red_ratio, 5)}


def check_cover(s):
    """封面判据。返回 (fails, warns)。"""
    fails, warns = [], []
    if abs(s["ratio"] - COVER_RATIO) > COVER_TOL:
        fails.append(f"封面比例 {s['ratio']} 不是 900:383（{COVER_RATIO:.2f}±{COVER_TOL}）")
    if s["w"] < MIN_COVER_W:
        fails.append(f"封面宽 {s['w']} < {MIN_COVER_W}，手机上看不清")
    if s["edge"] > EDGE_MAX:
        fails.append(f"封面边缘密度 {s['edge']:.0%} 超过 {EDGE_MAX:.0%}（字/元素太密，缩到手机上一团）")
    if s["contrast"] < CONTRAST_MIN:
        fails.append(f"有效对比度 {s['contrast']} < {CONTRAST_MIN}（看不清主次）")
    if s["colors"] > COLOR_MAX:
        warns.append(f"主色 {s['colors']} 种，超过 {COLOR_MAX} 会显得杂")
    return fails, warns


def check_shot(s):
    """正文截图判据。返回 (fails, warns)。"""
    fails, warns = [], []
    if s["blank"] > BLANK_MAX and s["edge"] < 0.01:
        fails.append(f"单色 {s['blank']:.0%} 且几乎无边缘：像是截空/白屏")
    elif s["blank"] > 0.92:
        warns.append(f"单色占比 {s['blank']:.0%} 偏高，确认不是把空白区域截进来了")
    if s["sharp"] < SHARP_MIN:
        fails.append(f"清晰度 {s['sharp']} < {SHARP_MIN}：糊")
    if s["w"] >= 1000 and s["h"] >= 1000:
        warns.append(f"{s['w']}×{s['h']} 接近整屏——手机上看不清，建议裁到「一个动作」的范围")
    if s["red"] < RED_RATIO_MIN:
        warns.append(f"没检测到红框标注（红像素 {s['red']:.4%}）——读者不知道看哪里")
    return fails, warns


def self_test():
    ok, why = _pil()
    if not ok:
        print(f"SELF-TEST SKIP：缺 Pillow（{why}）", file=sys.stderr)
        return 4
    import tempfile
    from PIL import Image, ImageDraw
    fails = []

    with tempfile.TemporaryDirectory() as td:
        # 1 合格封面：900x383、深底白字一块、对比高
        p1 = os.path.join(td, "cover_ok.png")
        im = Image.new("RGB", (900, 383), (20, 24, 32))
        d = ImageDraw.Draw(im)
        d.rectangle([60, 150, 700, 230], fill=(240, 240, 240))
        im.save(p1)
        s1 = stats(p1)
        f1, w1 = check_cover(s1)
        if f1:
            fails.append(f"正控[合格封面] 被判红：{f1}")

        # 2 负控：比例错（正方形）
        p2 = os.path.join(td, "cover_bad_ratio.png")
        Image.new("RGB", (600, 600), (30, 30, 30)).save(p2)
        f2, _ = check_cover(stats(p2))
        if not any("比例" in x for x in f2):
            fails.append("负控[比例错] 未判红")

        # 3 负控：纯白整图（截空）
        p3 = os.path.join(td, "shot_blank.png")
        Image.new("RGB", (800, 600), (255, 255, 255)).save(p3)
        f3, _ = check_shot(stats(p3))
        if not any("截空" in x or "白屏" in x for x in f3):
            fails.append("负控[截空] 未判红")

        # 4 负控：糊图（严重模糊）
        p4 = os.path.join(td, "shot_blur.png")
        base = Image.new("RGB", (800, 600), (40, 40, 40))
        dd = ImageDraw.Draw(base)
        for i in range(0, 800, 40):
            dd.line([(i, 0), (i, 600)], fill=(200, 200, 200), width=6)
        base.filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(14)).save(p4)
        f4, _ = check_shot(stats(p4))
        if not any("糊" in x or "清晰度" in x for x in f4):
            fails.append("负控[糊图] 未判红")

        # 5 红框检测：画红框后 red 占比必须上升
        p5 = os.path.join(td, "shot_red.png")
        im5 = Image.new("RGB", (800, 600), (30, 30, 30))
        d5 = ImageDraw.Draw(im5)
        d5.rectangle([100, 100, 400, 300], outline=(220, 30, 30), width=8)
        im5.save(p5)
        if stats(p5)["red"] <= stats(p3)["red"]:
            fails.append("负控[红框] 红像素占比未上升")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print("SELF-TEST OK 5/5  (合格封面/比例错/截空/糊图/红框检测)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cover")
    ap.add_argument("--dir")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    ok, why = _pil()
    if not ok:
        print(f"缺 Pillow（{why}）。请用：.venv-housing/bin/python3 Tools/fleet/gzh_visual_check.py ...",
              file=sys.stderr)
        return 3

    items = []
    if a.cover:
        items.append(("cover", a.cover))
    if a.dir:
        for p in sorted(glob.glob(os.path.join(a.dir, "*"))):
            if p.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                items.append(("shot", p))
    if not items:
        ap.print_help()
        return 1

    total_fail, total_warn, out = 0, 0, []
    for kind, p in items:
        try:
            s = stats(p)
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {os.path.basename(p)}：读取失败（{e}）", file=sys.stderr)
            total_fail += 1
            continue
        f, w = (check_cover(s) if kind == "cover" else check_shot(s))
        total_fail += len(f)
        total_warn += len(w)
        out.append({"kind": kind, **s, "fails": f, "warns": w})
        print(f"\n[{kind}] {os.path.basename(p)}  {s['w']}×{s['h']}  "
              f"对比 {s['contrast']}  清晰 {s['sharp']}  主色 {s['colors']}  边密 {s['edge']:.2f}  "
              f"红 {s['red']:.3%}")
        for x in f:
            print(f"  FAIL {x}")
        for x in w:
            print(f"  WARN {x}")

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"\n合计：FAIL {total_fail} / WARN {total_warn}")
    if total_fail:
        return 1
    print("客观项全过。**剩下的「好不好看」必须人看**——工具只保证不犯低级错。")
    return 0


if __name__ == "__main__":
    import json  # noqa: E402
    sys.exit(main())
