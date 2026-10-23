#!/usr/bin/env python3
"""apk_recon.py — 小游戏/手游 APK 包体结构与工程痕迹静态拆解（只读，不改包）

用法:
  python Tools/recon/apk_recon.py <app.apk> [--out <dir>]

产出:
  <out>/<stem>.apk.json  体积归因 / 引擎识别 / SDK 痕迹 / 资源统计
  <out>/<stem>.apk.md    人读摘要

说明:
  - 纯静态：只读 zip 目录与 dex 字符串，不反编译、不运行、不联网。
  - 需要更深资源反编译时另用 jadx/apktool（本脚本给结论与优先级）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ENGINE_SIGNS = {
    "Unity": ["lib/arm64-v8a/libunity.so", "lib/armeabi-v7a/libunity.so", "assets/bin/Data/", "libil2cpp.so"],
    "Cocos": ["libcocos2d", "assets/src/", "assets/jsb-adapter", "cocos2djs"],
    "Laya": ["liblayaair", "assets/layaair"],
    "Egret": ["egret", "libegret"],
    "CryEngine": ["libcryengine"],
    "Unreal": ["libUE4.so", "libUnreal.so"],
    "Godot": ["libgodot"],
    "H5/WebView": ["assets/*.wasm", "assets/index.html", "cordova.js"],
}

SDK_SIGNS = {
    "AdMob": [b"com/google/android/gms/ads"],
    "UnityAds": [b"com/unity3d/ads", b"UnityAds"],
    "AppLovin": [b"com/applovin"],
    "ironSource/LevelPlay": [b"com/ironsource", b"com/unity3d/ironsource"],
    "Pangle/穿山甲": [b"com/bytedance/sdk/openadsdk", b"com/ss/android"],
    "优量汇/GDT": [b"com/qq/e/ads"],
    "TopOn": [b"com/anythink"],
    "Mintegral": [b"com/mbridge"],
    "Facebook Ads": [b"com/facebook/ads"],
    "Vungle/Liftoff": [b"com/vungle"],
    "Adjust": [b"com/adjust/sdk"],
    "AppsFlyer": [b"com/appsflyer"],
    "Firebase": [b"com/google/firebase"],
    "友盟/Umeng": [b"com/umeng"],
    "腾讯Bugly": [b"com/tencent/bugly"],
    "微信SDK": [b"com/tencent/mm/opensdk"],
    "抖音SDK": [b"com/bytedance/sdk/openadsdk", b"com/ss/android/ugc"],
}

ABI_RE = re.compile(r"^lib/([^/]+)/")
RES_EXT = {".png", ".jpg", ".jpeg", ".webp", ".ktx", ".astc", ".etc", ".etc2", ".pkm", ".basis",
           ".ogg", ".mp3", ".wav", ".m4a", ".aac", ".bank", ".fsb",
           ".ttf", ".otf", ".atlas", ".skel", ".json", ".bin", ".dat", ".bytes", ".asset", ".assets", ".bundle", ".ab"}


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}B"
        n /= 1024
    return f"{n:.1f}GB"


def detect_engine(names: set[str], joined: str) -> list[str]:
    hits = []
    for engine, signs in ENGINE_SIGNS.items():
        for s in signs:
            if "*" in s:
                pat = re.escape(s).replace(r"\*", ".*")
                if re.search(pat, joined):
                    hits.append(engine)
                    break
            elif s in names or s in joined:
                hits.append(engine)
                break
    return sorted(set(hits))


def scan_dex(zf: zipfile.ZipFile, limit_bytes: int = 60_000_000) -> dict:
    found: dict[str, int] = defaultdict(int)
    dex_names = [n for n in zf.namelist() if n.endswith(".dex")]
    read = 0
    for n in dex_names:
        info = zf.getinfo(n)
        if info.file_size > 25_000_000:  # 超大 dex 只读前 25MB 足够命中 SDK 常量
            with zf.open(n) as f:
                blob = f.read(25_000_000)
        else:
            with zf.open(n) as f:
                blob = f.read()
        read += len(blob)
        for sdk, needles in SDK_SIGNS.items():
            if any(x in blob for x in needles):
                found[sdk] += 1
        if read > limit_bytes:
            break
    return {"dex_files": len(dex_names), "sdk_hits": dict(sorted(found.items(), key=lambda kv: -kv[1]))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("apk")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    apk = Path(args.apk).resolve()
    if not apk.exists():
        print(f"not found: {apk}", file=sys.stderr)
        return 2
    outdir = Path(args.out) if args.out else apk.parent / "recon"
    outdir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(apk) as zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
        names = {i.filename for i in infos}
        total = sum(i.file_size for i in infos)
        comp = sum(i.compress_size for i in infos)

        groups: dict[str, dict] = defaultdict(lambda: {"files": 0, "raw": 0, "comp": 0})
        abi: dict[str, int] = defaultdict(int)
        ext: dict[str, int] = defaultdict(int)
        biggest = []
        for i in infos:
            n = i.filename
            if n.startswith("lib/"):
                g = "lib"
                m = ABI_RE.match(n)
                if m:
                    abi[m.group(1)] += i.file_size
            elif n.startswith("assets/"):
                g = "assets"
            elif n.startswith("res/"):
                g = "res"
            elif n.startswith("META-INF/"):
                g = "META-INF"
            elif n.endswith(".dex"):
                g = "dex"
            else:
                g = "root/other"
            groups[g]["files"] += 1
            groups[g]["raw"] += i.file_size
            groups[g]["comp"] += i.compress_size
            ext[Path(n).suffix.lower() or "(none)"] += i.file_size
            biggest.append((i.file_size, n))

        joined = "\n".join(names)
        engine = detect_engine(names, joined)
        dex = scan_dex(zf)

        # Unity 专属线索
        unity_hint = {}
        for key, pat in {
            "il2cpp": r"libil2cpp\.so",
            "mono": r"libmono\.so",
            "global-metadata": r"global-metadata\.dat",
            "unity_data_dir": r"assets/bin/Data/",
            "addressables": r"\.bundle$|catalog.*\.json",
        }.items():
            unity_hint[key] = bool(re.search(pat, joined, re.I))

        manifest_size = next((i.file_size for i in infos if i.filename == "AndroidManifest.xml"), 0)

    result = {
        "apk": str(apk),
        "size": {"raw": total, "raw_h": human(total), "compressed": comp, "compressed_h": human(comp),
                 "compression_ratio": round(comp / total, 3) if total else 0},
        "file_count": len(infos),
        "engine_candidates": engine,
        "unity_hints": unity_hint,
        "groups": {k: {**v, "raw_h": human(v["raw"]),
                       "share": round(v["raw"] / total, 3) if total else 0}
                   for k, v in sorted(groups.items(), key=lambda kv: -kv[1]["raw"])},
        "abi": {k: human(v) for k, v in sorted(abi.items(), key=lambda kv: -kv[1])},
        "top_ext": [{"ext": k, "mb": round(v / 1048576, 2), "share": round(v / total, 3) if total else 0}
                    for k, v in sorted(ext.items(), key=lambda kv: -kv[1])[:12]],
        "biggest_files": [{"mb": round(s / 1048576, 2), "path": n} for s, n in sorted(biggest, reverse=True)[:15]],
        "dex": dex,
        "manifest_bytes": manifest_size,
    }

    jpath = outdir / f"{apk.stem}.apk.json"
    jpath.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# APK 包体拆解：{apk.name}",
        "",
        f"- 总解压体积：{result['size']['raw_h']}｜压缩后 {result['size']['compressed_h']}｜压缩率 {result['size']['compression_ratio']}",
        f"- 文件数：{result['file_count']}｜dex：{dex['dex_files']}",
        f"- 引擎候选：{', '.join(engine) if engine else '未识别'}",
    ]
    if any(unity_hint.values()):
        lines.append(f"- Unity 线索：{json.dumps(unity_hint, ensure_ascii=False)}")
    lines += ["", "## 体积归因"]
    for k, v in result["groups"].items():
        lines.append(f"- {k}: {v['raw_h']}（{v['share']*100:.1f}%）")
    if result["abi"]:
        lines.append("")
        lines.append("## ABI")
        for k, v in result["abi"].items():
            lines.append(f"- {k}: {v}")
    lines += ["", "## 最大文件 Top10"]
    for b in result["biggest_files"][:10]:
        lines.append(f"- {b['mb']} MB  {b['path']}")
    if dex["sdk_hits"]:
        lines.append("")
        lines.append("## SDK 痕迹（字符串命中）")
        for k, v in dex["sdk_hits"].items():
            lines.append(f"- {k}（{v} dex）")
    lines.append("")
    lines.append("> 仅静态观察，未反编译；结论按 METHOD-v1 §二 九面补完后方可成卡。")
    mpath = outdir / f"{apk.stem}.apk.md"
    mpath.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"ok": True, "json": str(jpath), "md": str(mpath),
                      "size_h": result["size"]["raw_h"], "engine": engine}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())