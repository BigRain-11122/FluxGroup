#!/usr/bin/env python3
"""batch_recon.py — 竞品批量逆向流水线（编排现成工具，不自造解析器）

每个目标：下载 APK → apk_recon → 解包 → (Unity/il2cpp) Il2CppDumper → dump_schema → 生成卡片

用法: python Tools/recon/batch_recon.py <targets.json> [--limit N]

targets.json: [{"slug":"luobo4","title":"保卫萝卜4","genre":"塔防","url":"https://...apk"}]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APK_DIR = ROOT / "media/recon/apk"
OUT_DIR = ROOT / "media/recon/apk"
CARD_DIR = ROOT / "cph4/fleet/recon-dept-v1/cards"
DUMPER = ROOT / "media/recon/tools/il2cppdumper/Il2CppDumper.dll"
SEVENZ = r"C:\Program Files\7-Zip\7z.exe"


def run(cmd, **kw):
    p = subprocess.run(cmd, capture_output=True, text=True, errors="replace", **kw)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def download(url: str, dst: Path) -> bool:
    if dst.exists() and dst.stat().st_size > 1024 * 1024:
        try:
            with zipfile.ZipFile(dst) as z:
                if z.namelist():
                    return True
        except Exception:
            pass
    part = dst.with_suffix(".part")
    rc, out = run(["curl.exe", "-sS", "-L", "-C", "-", "--max-time", "1800",
                   "-A", "Mozilla/5.0", "-o", str(part), url])
    if part.exists():
        part.replace(dst)
    if not dst.exists():
        print("  download failed:", out[-200:])
        return False
    try:
        with zipfile.ZipFile(dst) as z:
            ok = bool(z.namelist())
    except Exception as e:
        print("  bad zip:", e)
        return False
    return ok


def main() -> int:
    targets = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    if limit:
        targets = targets[:limit]
    APK_DIR.mkdir(parents=True, exist_ok=True)
    CARD_DIR.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, DOTNET_ROLL_FORWARD="Major", PYTHONIOENCODING="utf-8")

    for i, t in enumerate(targets, 1):
        slug, title, genre, url = t["slug"], t["title"], t.get("genre", ""), t["url"]
        print(f"\n=== [{i}/{len(targets)}] {title} ({genre}) ===")
        apk = APK_DIR / f"{slug}.apk"
        if not download(url, apk):
            print("  SKIP: download")
            continue
        print(f"  apk {apk.stat().st_size/1048576:.0f} MB")

        rc, out = run([sys.executable, str(ROOT / "Tools/recon/apk_recon.py"), str(apk)])
        print("  apk_recon:", out.strip().splitlines()[-1] if out.strip() else rc)

        # Unity il2cpp 才继续
        ext = APK_DIR / f"{slug}_x"
        if not (ext / "lib").exists():
            run([SEVENZ, "x", str(apk), f"-o{ext}", "-y"])
        so = next(iter((ext / "lib").glob("*/libil2cpp.so")), None) if (ext / "lib").exists() else None
        meta = ext / "assets/bin/Data/Managed/Metadata/global-metadata.dat"
        if not (so and meta.exists()):
            print("  not il2cpp -> try Cocos plain-JSON configs")
            if (ext / "assets/assets").exists():
                rc, out = run([sys.executable, str(ROOT / "Tools/recon/cocos_cfg.py"), str(ext), slug])
                print("  cocos:", out.strip()[-300:])
            continue

        outdir = OUT_DIR / f"il2cpp_{slug}"
        outdir.mkdir(exist_ok=True)
        rc, out = run(["dotnet", str(DUMPER), str(so), str(meta), str(outdir)], env=env)
        dump = outdir / "dump.cs"
        if not dump.exists():
            print("  il2cpp dump failed:", out[-300:])
            continue
        rc, out = run([sys.executable, str(ROOT / "Tools/recon/dump_schema.py"),
                       str(dump), str(outdir / "schema.json")])
        print("  schema:", out.strip().splitlines()[0] if out.strip() else rc)

        # 卡片骨架（事实部分自动填，分析部分留给人）
        card = CARD_DIR / f"GAME-{slug}.md"
        size = apk.stat().st_size / 1048576
        card.write_text(
            f"# {title}（{genre}）— 自动拆解骨架\n\n"
            f"- APK: `{slug}.apk`（{size:.0f} MB）\n"
            f"- 包体报告: `media/recon/apk/recon/{slug}.apk.md`\n"
            f"- 配置表结构: `media/recon/apk/il2cpp_{slug}/schema.json`\n"
            f"- dump: `media/recon/apk/il2cpp_{slug}/dump.cs`\n\n"
            f"> 自动生成：数值与玩法逻辑需按 LOGIC-RECON 流程继续，勿把本骨架当结论。\n",
            encoding="utf-8")
    print("\nBATCH DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())