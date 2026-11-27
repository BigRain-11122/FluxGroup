Fleet exec bootstrap (bm-a, 2026-11-27)

This node runs an older FleetLink listener (1.9.7 or none). To enable
fleet-to-fleet command execution (/exec) and finish the T0 net order:

1) tailscale file get --conflict=rename C:\Temp\fleet-boot
2) powershell -NoProfile -ExecutionPolicy Bypass -File C:\Temp\fleet-boot\fleet-link.ps1 -Root <repo root> -NodeId <id>

Windows roots:
  bm-b  C:\Fluxgroup\FluxGroup    id bm-b
  bm-c  K:\Fluxgroup\FluxGroup    id bm-c
  bm-a  C:\Users\sjs20\Desktop\FluxGroup  id bm-a (already 1.9.9)

Check: http://<tailnet ip>:8790/health -> version 1.9.9
After that bm-a can run commands on this node via POST /exec (fleet IPs only).