# AUTO-SEND.ps1 - unattended sender for the content-line handover payload (bm-a -> bm-c).
# ASCII ONLY (PS 5.1 decodes BOM-less .ps1 as ANSI).
#
# Why this exists: the tailnet path to FLUXGROUP measured <14 KB/s on 2026-11-21
# (5 MB never finished in 349 s), most likely because the peer has no active user
# session for Taildrop to land in. Rather than wait on a human, this runs on a
# schedule: probe first, and only when the path is actually healthy does it send
# the sealed packages, one at a time, resumably, recording what it delivered.
#
# Writes:  <Src>\sender.log   (append-only, human readable)
#          <Src>\SENT.json    (name -> sha256 delivered this host)
# Exit:    0 = nothing to do / all sent    2 = probe says path is still bad    3 = a send failed
param(
  [string]$Peer  = 'bm-c',
  [string]$Src   = 'D:\handover-content-20261120',
  [int]$ProbeMB  = 2,
  [int]$MinKBps  = 20,          # measured path is ~29 KB/s; below this we do not start
  [int]$MaxSendHours = 8
)
$ErrorActionPreference = 'Continue'
$log  = Join-Path $Src 'sender.log'
$state= Join-Path $Src 'SENT.json'

function Log($m) {
  $line = "{0} {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m
  Add-Content -Path $log -Value $line -Encoding UTF8
}

if (-not (Test-Path $Src)) { Log "ABORT: payload dir missing $Src"; exit 2 }

# ---------- single instance ----------
# A send can run for hours; the 20-minute schedule must not pile up behind it.
$busy = Get-CimInstance Win32_Process -Filter "Name='tailscale.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'file\s+cp' }
if ($busy) { Log ("BUSY: another send in flight (pid {0})" -f ($busy.ProcessId -join ',')); exit 5 }

# ---------- probe ----------
$probe = Join-Path $env:TEMP ("tdprobe-{0}.bin" -f $PID)
$fs = [IO.File]::Create($probe); $fs.SetLength($ProbeMB * 1MB); $fs.Close()
$sw = [Diagnostics.Stopwatch]::StartNew()
$p = Start-Process tailscale -ArgumentList 'file','cp',"`"$probe`"","${Peer}:" -PassThru -WindowStyle Hidden
$finished = $p.WaitForExit(90000)     # 90 s ceiling for the 2 MB probe
$sw.Stop()
if (-not $finished) { try { $p.Kill() } catch {} }
Remove-Item $probe -Force -ErrorAction SilentlyContinue
$probeKBps = if ($sw.Elapsed.TotalSeconds -gt 0) { $ProbeMB * 1024 / $sw.Elapsed.TotalSeconds } else { 0 }
Log ("PROBE {0}MB -> {1:N0} KB/s (finished={2})" -f $ProbeMB, $probeKBps, $finished)

if (-not $finished -or $probeKBps -lt $MinKBps) {
  Log "SKIP: link below threshold, nothing sent this cycle"
  exit 2
}

# ---------- state ----------
$sent = @{}
if (Test-Path $state) {
  try { $o = Get-Content $state -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($k in $o.PSObject.Properties) { $sent[$k.Name] = $k.Value } } catch {}
}

# ---------- send ----------
$failed = 0
foreach ($zip in (Get-ChildItem $Src -Filter 'content-*.zip' | Sort-Object Name)) {
  $sha = (Get-FileHash $zip.FullName -Algorithm SHA256).Hash.ToLower()
  if ($sent.ContainsKey($zip.Name) -and $sent[$zip.Name] -eq $sha) { Log ("SKIP-ALREADY {0}" -f $zip.Name); continue }

  $estSec = [int](($zip.Length / 1KB) / [Math]::Max($probeKBps, 1) * 1.6) + 120
  $capMs  = [Math]::Min($estSec * 1000, $MaxSendHours * 3600 * 1000)
  Log ("SEND {0} ({1:N0} MB, ceiling {2:N0}s)" -f $zip.Name, ($zip.Length/1MB), ($capMs/1000))

  $started = Get-Date
  $proc = Start-Process tailscale -ArgumentList 'file','cp',"`"$($zip.FullName)`"","${Peer}:" -PassThru -WindowStyle Hidden
  $ok = $proc.WaitForExit($capMs)
  $elapsed = ((Get-Date) - $started).TotalSeconds
  if (-not $ok) {
    try { $proc.Kill() } catch {}
    Log ("TIMEOUT {0} after {1:N0}s - stopping this cycle (peer likely still cannot receive)" -f $zip.Name, $elapsed)
    exit 3
  }
  if ($proc.ExitCode -ne 0) {
    Log ("FAIL {0} rc={1}" -f $zip.Name, $proc.ExitCode)
    $failed++
    continue
  }
  Log ("SENT {0} in {1:N0}s  sha256={2}" -f $zip.Name, $elapsed, $sha)
  $sent[$zip.Name] = $sha
  $sent | ConvertTo-Json | Set-Content -Encoding UTF8 $state
}

if ($failed -eq 0) { Log 'CYCLE-DONE: all payload sent' } else { Log "CYCLE-DONE: $failed failed" }
exit ([int]($failed -gt 0) * 3)
