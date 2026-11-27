# -*- coding: utf-8 -*-
"""gate_selftest.py —— 闸上线前的双向验证（PROCESS-REVIEW-v1 M1）

每个闸必须同时满足：该通过的能过（正样本）、该拦的能拦（负样本）。
跑不过 → 闸不许上线。
"""
import sys, os

sys.path.insert(0, r"C:\Users\sjs20\Desktop\FluxGroup\Tools")
import preflight_gate as G

TOK = dict(shot="cu", angle="eye", move="static", scene="tablet", light="flame",
           grade="tw2001", texture="film_night")

CASES = [
    # (名称, 期望是否应被拒, 调用)
    ("正样本-合法刻字", False, lambda: G.guard(
        "SELFTEST_OK", "he carves cuneiform marks that stay fixed, warm torchlight",
        TOK, True, "checked 1 frame", None, ["carve", "inscription"])),
    ("负样本-含否定句", True, lambda: G.guard(
        "SELFTEST_NEG", "no reflected face, he carves cuneiform marks that stay fixed",
        TOK, True, "checked 1 frame", None, ["carve", "inscription"])),
    ("负样本-缺刻痕锚", True, lambda: G.guard(
        "SELFTEST_ANCHOR", "he carves marks", TOK, True, "checked 1 frame", None,
        ["carve", "inscription"])),
    ("负样本-场景冲突", True, lambda: G.guard(
        "SELFTEST_SCENE", "she stands inside a torchlit temple hall with cuneiform marks that stay fixed",
        TOK, True, "checked 1 frame", None, ["inscription"])),
    ("负样本-首帧未签", True, lambda: G.guard(
        "SELFTEST_KF", "he carves cuneiform marks that stay fixed", TOK, False, "",
        None, ["carve", "inscription"])),
    ("负样本-黑名单镜", True, lambda: G.guard(
        "S9_profile", "she stands still", TOK, True, "checked", "reflected_face", [])),
]


def main():
    bad = 0
    print("== 闸自检（preflight_gate）==")
    for name, expect_reject, fn in CASES:
        fails = fn()
        rejected = bool(fails)
        ok = (rejected == expect_reject)
        print("%-22s 期望%s 实际%s  %s" % (
            name, "拒" if expect_reject else "过", "拒" if rejected else "过",
            "PASS" if ok else "FAIL"))
        if not ok:
            bad += 1
            print("     返回:", fails)
    print()
    if bad:
        print("SELFTEST FAIL：%d 条不符合预期，闸不许上线" % bad)
        sys.exit(1)
    print("SELFTEST PASS：双向验证通过（该过的过、该拦的拦）")


if __name__ == "__main__":
    main()