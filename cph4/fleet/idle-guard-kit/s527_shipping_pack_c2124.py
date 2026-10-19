"""C2124 shipping pack: turn the six grain-0.10 4K plates into a delivery folder.

Byte-identical copies into media/MV/mv0001/xingqing/delivery/, SHA256 + size +
dimensions per plate, manifest + one-page README, then re-hash the copies.
"""
import hashlib
import json
import os
import shutil
import time

from PIL import Image

XQ = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing"
SRC = os.path.join(XQ, "s7r-4k")
DST = os.path.join(XQ, "delivery")
VERDICT_SRC = os.path.join(XQ, "xq-S527-SHIPPING-ADJUDICATION-c2123.json")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    plates = sorted(
        n for n in os.listdir(SRC)
        if n.endswith("_4k_grain010.png")
    )
    if len(plates) != 6:
        print("SHIPPING-PACK-END ok=%d FAIL expected 6 plates" % len(plates))
        return 1

    os.makedirs(DST, exist_ok=True)
    entries = []
    for name in plates:
        src = os.path.join(SRC, name)
        dst = os.path.join(DST, name)
        shutil.copyfile(src, dst)
        with Image.open(src) as im:
            width, height = im.size
        src_hash = sha256(src)
        dst_hash = sha256(dst)
        entries.append({
            "file": name,
            "shot": name.split("_")[0],
            "seed": name.split("_")[2],
            "path": "media/MV/mv0001/xingqing/delivery/" + name,
            "bytes": os.path.getsize(dst),
            "dimensions": [width, height],
            "sha256": dst_hash,
            "sha256_source": src_hash,
            "byte_identical": src_hash == dst_hash,
        })
        print("COPY %s %d %s" % (name, entry_bytes(entries[-1]), dst_hash[:16]))

    if not all(e["byte_identical"] for e in entries):
        print("SHIPPING-PACK-END ok=0 FAIL copy hash mismatch")
        return 1

    verdict = {}
    if os.path.exists(VERDICT_SRC):
        verdict = json.load(open(VERDICT_SRC, encoding="utf-8-sig"))

    manifest = {
        "batch": "c2124-s527-shipping-pack",
        "line": "S5-26/27/28 four-K grids, r1017 sec-8 shipping substrate",
        "grain": 0.10,
        "plate_count": len(entries),
        "spec": "r1017 sec-8 item-1 adjudicated on the shipping plates; these are the delivery masters",
        "adjudication": {
            "receipt": "xq-S527-SHIPPING-ADJUDICATION-c2123.json",
            "candidates": verdict.get("candidates"),
            "stars": verdict.get("stars"),
            "anomalies": verdict.get("anomalies"),
            "defects_found": verdict.get("defects_found"),
            "repair_targets": verdict.get("repair_targets"),
            "verdict": verdict.get("verdict"),
        },
        "entries": entries,
        "verify": "sha256 of every delivery copy re-read from disk in this run and equal to the source plate",
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "by": "tick-C2124",
    }
    manifest_path = os.path.join(DST, "MANIFEST-s527-4k.json")
    json.dump(manifest, open(manifest_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    readme = os.path.join(DST, "README-s527-4k.md")
    lines = [
        "# S5-26/27/28 4K 交付包（grain 0.10）",
        "",
        "批次：c2124-s527-shipping-pack｜产出时间：" + manifest["ts"],
        "",
        "## 内容",
        "",
        "六张 3840×2194 4K 母版（S5-26 ×2 / S5-27 ×2 / S5-28 ×2），胶片颗粒 0.10 档，",
        "由 s527-4k-esrgan（ESRGAN ×4 + LANCZOS）出底、s527-4k-grain010 上颗粒。",
        "每张与 media/MV/mv0001/xingqing/s7r-4k 下同名源件逐字节一致（SHA256 见 MANIFEST）。",
        "",
        "## 质检结论（C2123 判定）",
        "",
        "- 星点排除分类器候选 1605 / 星点 1571 / 异常 34（零颗粒底 2535 / 2436 / 99 → 上颗粒后不增反减）",
        "- 34 个异常中 33 个落在画框边缘（3840×2194 内 x≥3817 或 y≥2173）= 被画框裁切的星点，分类器按设计标为异常",
        "- 画内 2 例（s20193 @1888,1740 / s20205 @2615,649）为蓝色弥散星云团，径向均值平滑，无周期/复制结构",
        "- 缺陷 0，返工目标 0：sec-8 第 1 项（细线幻觉/点阵）判定为检测器假阳性类，非片源缺陷",
        "",
        "## 附件",
        "",
        "- MANIFEST-s527-4k.json：逐张 SHA256 / 字节数 / 尺寸 / 判定摘要",
        "- 同目录六张 PNG = 交付母版；诊断件（_4kraw / grain 0.05 / 0.07 对比板）留在 s7r-4k 不随包交付",
        "",
        "## 复验",
        "",
        "`python -c` 或 `certutil -hashfile <文件> SHA256` 与 MANIFEST 内 sha256 字段对数即验。",
        "",
    ]
    open(readme, "w", encoding="utf-8").write("\n".join(lines))

    # Final verification pass: re-read the delivery copies from disk.
    ok = 0
    for e in entries:
        p = os.path.join(DST, e["file"])
        if sha256(p) == e["sha256"] and os.path.getsize(p) == e["bytes"]:
            ok += 1
    parsed = json.load(open(manifest_path, encoding="utf-8-sig"))
    manifest_ok = len(parsed.get("entries", [])) == 6
    print("MANIFEST %s entries=%d parsed=%s" % (manifest_path, len(entries), manifest_ok))
    print("README %s %dB" % (readme, os.path.getsize(readme)))
    print("SHIPPING-PACK-END ok=%d manifest_ok=%s" % (ok if manifest_ok else 0, manifest_ok))
    return 0 if (ok == 6 and manifest_ok) else 1


def entry_bytes(e):
    return e["bytes"]


if __name__ == "__main__":
    raise SystemExit(main())