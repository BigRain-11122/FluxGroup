Fleet net bundle 2026-11-27 (from bm-a)
Windows node:
  1) git -C <root> fetch origin main
  2) git -C <root> checkout origin/main -- Tools/fleet-drop.ps1 Tools/fleet-net-doctor.ps1 Tools/fleet-anchor-check.ps1 Tools/fleet-fix-admin.ps1 cph4/fleet/AGENT-NET-UNIVERSAL-PROMPT.md
  3) powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-net-doctor.ps1
  4) paste cph4/fleet/AGENT-NET-UNIVERSAL-PROMPT.md into Codely and let it run
  5) admin once: Tools\fleet-fix-admin.ps1 (Run as administrator)
macOS node:
  1) git -C <root> fetch origin main
  2) git -C <root> checkout origin/main -- cph4/fleet/AGENT-NET-UNIVERSAL-PROMPT.md
  3) paste the prompt into Codely