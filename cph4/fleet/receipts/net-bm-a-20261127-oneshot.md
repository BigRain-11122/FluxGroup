# net receipt — bm-a — one-shot 2026-11-27 18:56

node=bm-a dns=bm-a.tail316e0c.ts.net ip=100.110.185.62 host=DASHENG when=2026-11-27T18:56:10
nat=symmetric:true portmap=none ipv6=none egress=SG/AS21859 Zenlayer vpn=none
path_to_bm_a=self rtt_ms=0 taildrop_1mb=11.8KB/s (2026-11-27 15:2x)
listener=1.9.9 exec_selftest=ok rc=0 264ms fleetlink_8790=up bind=100.110.185.62:8790 task=Ready health=ok logontype=Interactive
git=dirty diverge=56/53 autocrlf=true clock=skew (w32time stopped 0x80070426)
naming=OK; taildrop_receive=ok (rc=0, 0 files); leases=none
peers=bm-c relay:sfo 8790:up(v1.9.7) | bm-b relay:sfo 8790:down | bm-m-1 direct 192.168.160.100 18ms

actions:
- §0 self: root=D:\FluxGroup, id=bm-a (host DASHENG), admin=False
- §2 listener: health 1.9.9; POST /exec selftest -> rc=0, EXEC_OK DASHENG, 264ms
- §1 naming: Self.DNSName=bm-a.tail316e0c.ts.net; fleet-drop -To bm-a resolves to bm-a.tail316e0c.ts.net (100.110.185.62), no ambiguity
- §3 forensics: fleet-net-doctor + fleet-anchor-check ran (fresh); CGNAT, PortMapping empty, no global IPv6, egress SG/AS21859, vpn_adapters empty; bm-c/bm-b relay sfo, bm-m-1 direct
- §4 triage: A noop; B Tailscale Running/Automatic + unattended(rc=0); C no local TUN; D not anchor (relay not enabled); E CGNAT client-only; F 8790 up + health ok, task Interactive; G taildrop get rc=0, fleet-drop -Status self line ok
- §5 admin: not elevated -> UAC step skipped by policy; blockers below
- §7 git: pull not attempted (diverged 56/53, ff-only would fail); autocrlf=true; refs/leases empty; clock skew

blockers:
- FluxGroup-FleetLink task LogonType=Interactive -> admin: Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','D:\FluxGroup\Tools\fleet-fix-admin.ps1'
- w32time stopped (0x80070426) -> same admin script (starts service, Auto, resync)
- D clone diverged 56/53 -> no pull/push; this receipt was published via GitHub API (server-side, guarded)
- bm-c listener v1.9.7 (no /exec) -> run the one-shot prompt there; bm-b 8790 down -> same
- bm-a CGNAT -> cannot be an anchor (no public IPv4/IPv6/portmap)

verify:
- fleet-drop -Status: self=bm-a dns=bm-a.tail316e0c.ts.net ip=100.110.185.62 online=True; bm-c/bm-b relay sfo; bm-m-1 direct
- exec selftest: rc=0, EXEC_OK DASHENG
- fleet-net-doctor: can_host_direct=no; bm-c 8790=True; bm-b 8790=False

push=OK via GitHub API (only this file; base tree guarded >=20)
