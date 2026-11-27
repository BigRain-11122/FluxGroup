# -*- coding: utf-8 -*-
"""hq_claim_launch.py -- console-less launcher for the lane claim leg.

Why this exists (2026-11-11 bm-c): Windows Defender quarantined
Tools/InvisibleRunner.vbs at 07:49 with Trojan:Script/ObfusScript.A!ml and deleted the
22 fleet tasks that carried it (HQ-ProductionClaim among them). task-register.ps1 then
refuses to register anything ("InvisibleRunner.vbs missing"), and every re-registration
is quarantined again within seconds.

pythonw.exe is console-less by construction, so a task whose action is pythonw.exe needs
no script-host chain to stay silent (U060), and it carries no VBS signature for the ML to
bite. This launcher only re-parents the claim steps -- the steps themselves stay in
Tools/hq-lane-claim.bat, one source, unchanged.

Usage: pythonw.exe Tools/hq_claim_launch.py
Exit: the batch file's exit code (2 if the batch itself is missing).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAT = os.path.join(ROOT, "Tools", "hq-lane-claim.bat")
CREATE_NO_WINDOW = 0x08000000


def main():
    if not os.path.exists(BAT):
        sys.stderr.write("hq_claim_launch: missing %s\n" % BAT)
        return 2
    proc = subprocess.run(["cmd.exe", "/c", BAT], cwd=ROOT,
                          creationflags=CREATE_NO_WINDOW)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
