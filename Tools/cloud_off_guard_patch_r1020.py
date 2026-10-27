# -*- coding: utf-8 -*-
"""T0 云道停用（2026-10-20）：给所有会自动拉起 codely 云端会话的脚本插入统一闸门。

闸门逻辑：从脚本目录向上找到仓库根（含 cph4/fleet/CLOUD-OFF-LOCAL-ONLY-v1.md），
命中即在 Start-Process 之前记一行日志并 exit 0 —— 本地前置工作照常完成，云端回合不点火。
"""
import io
import os

MARK = "T0 CLOUD-OFF guard (CEO 2026-10-20)"

GUARD = [
    "# T0 CLOUD-OFF guard (CEO 2026-10-20): automation is local-only; never spawn the cloud CLI.",
    "$__co = $PSScriptRoot",
    "while ($__co -and -not (Test-Path (Join-Path $__co 'cph4\\fleet\\CLOUD-OFF-LOCAL-ONLY-v1.md'))) { $__co = Split-Path -Parent $__co }",
    "if ($__co) {",
    "    $__cl = Join-Path $__co 'media\\logs\\cloud-off-suppressed.log'",
    "    $__cd = Split-Path -Parent $__cl",
    "    if (-not (Test-Path $__cd)) { New-Item -ItemType Directory -Force -Path $__cd | Out-Null }",
    "    Add-Content -Path $__cl -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' | ' + [System.IO.Path]::GetFileName($PSCommandPath) + ' | suppressed cloud round (T0)') -Encoding UTF8",
    "    exit 0",
    "}",
]

TARGETS = [
    ("Tools/patrol-runner.ps1", "$p = Start-Process -FilePath $codely"),
    ("Tools/patrol-fleet-carrier.ps1", "$p = Start-Process -FilePath $codely"),
    ("Tools/proxy-event-carrier.ps1", "$p = Start-Process -FilePath $codely"),
    ("Tools/shift-supervisor.ps1", "$p = Start-Process -FilePath $codely"),
    ("gaming/MiniGame/tools/EngineTick.ps1", "$p = Start-Process -FilePath $codely"),
    ("compute/BigCompute/Tools/iteration_loop.ps1", "$p = Start-Process -FilePath $codelyPath"),
    ("quant/bigmoney/Tools/iteration_loop.ps1", "$p = Start-Process -FilePath $codelyPath"),
    ("gaming/FluxVerse/Tools/devloop/iteration_loop.ps1", "$p = Start-Process -FilePath $codelyPath"),
    ("domain/BigDomain/src/os/iteration_loop.ps1", "$p = Start-Process -FilePath $codelyPath"),
    ("life/BigLife/Tools/iteration_loop.ps1", "$p = Start-Process -FilePath $codelyPath"),
    ("media/BigStream/src/os/iteration_loop.ps1", "$p = Start-Process -FilePath $codelyPath"),
    ("cph4/decision-round.ps1", "& $cli -y -p $prompt"),
    ("cph4/evolution-tick.ps1", "& $cli -y -p $prompt"),
    ("cph4/night-round.ps1", "& $cli -y -p $prompt"),
    ("gaming/MiniGame/tools/ModeTick.ps1", "$p = Start-Process -FilePath $codely"),
    ("gaming/MiniGame/tools/BoardForge.ps1", "$p = Start-Process -FilePath $codely"),
    ("gaming/MiniGame/tools/c2147_glyphtower_e4_firstfire_wave.ps1", "$cp = Start-Process -FilePath $cli"),
]


def read_text(path):
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    body = raw[3:] if bom else raw
    for enc in ("utf-8", "gbk"):
        try:
            return body.decode(enc), bom, enc
        except UnicodeDecodeError:
            continue
    raise SystemExit("decode failed: " + path)


def patch(rel):
    path = rel.replace("/", os.sep)
    text, bom, enc = read_text(path)
    if MARK in text:
        return "skip (already guarded)"
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    target = None
    for i, line in enumerate(lines):
        if line.strip().startswith(TARGETS_DICT[rel]):
            target = i
            break
    if target is None:
        return "MISS (anchor not found)"
    indent = lines[target][: len(lines[target]) - len(lines[target].lstrip())]
    block = [indent + g if g else g for g in GUARD]
    lines[target:target] = block
    out = nl.join(lines)
    data = out.encode(enc)
    if bom:
        data = b"\xef\xbb\xbf" + data
    open(path, "wb").write(data)
    return "guarded (line %d)" % (target + 1)


TARGETS_DICT = dict(TARGETS)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for rel, _ in TARGETS:
        print("%-58s %s" % (rel, patch(rel)))