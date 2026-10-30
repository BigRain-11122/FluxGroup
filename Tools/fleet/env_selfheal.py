# -*- coding: utf-8 -*-
"""env_selfheal.py - a node installs its own missing dependencies (CEO 2026-10-30:
"缺什么让他自己装啊").

Runs ON THE WORKER BOX, by the lane agent, before a job starts. The master never
remote-installs anything (fleet design forbids cross-box execution).

Installer source is the repo's own canon: bootstrap-machine.ps1 already uses
`winget install --id Git.Git -e --silent --accept-package-agreements`, and CODELY.md
records that ffmpeg on these boxes comes from winget (the old hardcoded
C:\\Program Files\\ffmpeg\\bin path died after that migration). Same shape, per tool.
"""
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_lane as fl

WIN = "win"
# tool -> {os: (installer cmd, timeout_s)}
DEPS = {
    "ffmpeg": {WIN: ('winget install --id Gyan.FFmpeg -e --silent '
                     '--accept-source-agreements --accept-package-agreements', 900)},
    "ffprobe": {WIN: ('winget install --id Gyan.FFmpeg -e --silent '
                      '--accept-source-agreements --accept-package-agreements', 900)},
    "git": {WIN: ('winget install --id Git.Git -e --silent '
                  '--accept-source-agreements --accept-package-agreements', 900)},
    "python": {WIN: ('winget install --id Python.Python.3.12 -e --silent '
                     '--accept-source-agreements --accept-package-agreements', 900)},
}
# winget portable installs land here; PATH of an already-running process misses them
EXTRA_PATH = [
    r"C:\Users\Public\wavded\ffmpeg\bin",
    r"C:\ProgramData\chocolatey\bin",
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links"),
    os.path.expandvars(r"%ProgramFiles%\ffmpeg\bin"),
]


def platform():
    return WIN if os.name == "nt" else "posix"


def have(tool):
    if shutil.which(tool):
        return True
    for d in EXTRA_PATH:
        if os.path.isdir(d) and shutil.which(tool, path=d + os.pathsep + os.environ.get("PATH", "")):
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
            return True
    return False


def ensure(tool, log=print):
    """Install a missing dependency locally. Returns (ok, detail)."""
    if not tool or tool not in DEPS:
        return True, "no-registry:%s" % tool      # unknown tool -> let the job try anyway
    if have(tool):
        return True, "already-present"
    spec = DEPS[tool].get(platform())
    if not spec:
        return False, "no-installer-for-%s" % platform()
    cmd, tmo = spec
    log("[selfheal] %s missing -> installing locally (winget canon)" % tool)
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=tmo, errors="replace")
        out = ((p.stdout or "") + (p.stderr or ""))[-400:]
    except Exception as e:
        return False, "installer-error:%s" % str(e)[:120]
    ok = have(tool)
    log("[selfheal] %s -> ok=%s rc=%s %s" % (tool, ok, p.returncode, out[-160:]))
    return ok, ("installed" if ok else "install-failed-rc%s:%s" % (p.returncode, out[-200:]))


def first_tool(cmd):
    t = (cmd or "").strip().lstrip('"').split()
    if not t:
        return ""
    t0 = os.path.basename(t[0]).replace(".exe", "").replace(".py", "")
    if t0 in ("python", "py", "python3") and len(t) > 1:
        t0 = os.path.basename(t[1]).replace(".py", "")
    return t0


if __name__ == "__main__":
    # lane-side entrypoint: python env_selfheal.py "python Tools/x.py ..."
    tool = first_tool(" ".join(sys.argv[1:]))
    ok, detail = ensure(tool)
    print("[selfheal] %s %s :: %s" % (tool, "OK" if ok else "FAIL", detail))
    sys.exit(0 if ok else 1)
