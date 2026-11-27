# silence-window-guard.ps1 - window-level silence enforcement (v4).
#
# What actually pops (measured on this machine, 2026-10-25):
#   Windows 11 defaults to Windows Terminal, so a console program started directly by
#   the Task Scheduler is handed to a WT window. The console process is NOT a child of
#   the WT process, so scanning down from a window finds nothing -- that is why v3
#   could not see it.
#
# The reliable discriminator is the PARENT:
#   * Task Scheduler launches a console app -> parent is svchost.exe / taskhostw.exe
#     -> a window is painted (this is the popup)
#   * every task that is meant to be silent goes through wscript + InvisibleRunner
#     -> parent is wscript.exe, and WshShell.Run(..., 0, ...) keeps it hidden
# So: a console app whose parent is the scheduler is killed on sight and logged with its
# full command line, which names the offending task's script.
param(
  [int]$Minutes = 9,
  [string]$LogPath = 'K:\Fluxgroup\FluxGroup\Tools\logs\window-guard.log'
)

$ErrorActionPreference = 'Continue'

$created = $false
$mutex = New-Object System.Threading.Mutex($true, 'Local\HQ_SilenceWindowGuard', [ref]$created)
if (-not $created) { exit 0 }

# Never listed here: wt.exe / WindowsTerminal.exe. Windows Terminal is the default host
# on this machine, so it is also what a person's Start-menu launch activates; killing it
# would close the user's own terminal. Killing the console program that occupies the tab
# is enough -- the window goes away with its last tab.
$consoleProcs = @('cmd.exe', 'powershell.exe', 'pwsh.exe', 'python.exe', 'node.exe',
                  'conhost.exe', 'OpenConsole.exe')
$schedulerParents = @('svchost.exe', 'taskhostw.exe')
$selfProtected = '(?i)(silence-window-guard|window-watch|guard-probe)'

function Write-GuardLog([string]$text) {
  $dir = Split-Path -Parent $LogPath
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  Add-Content -Encoding utf8 -Path $LogPath -Value $text
}

$end = (Get-Date).AddMinutes($Minutes)
Write-GuardLog ("{0} | guard v4 start (pid {1}, {2} min)" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $PID, $Minutes)

# Server-side filter: a full Win32_Process scan takes long enough under load that a
# whole poll period can be missed, which is how a popup slips through. Only console
# names are of interest, so ask WMI for exactly those.
$procFilter = ($consoleProcs | ForEach-Object { "Name='$_'" }) -join ' OR '

# Warm the WMI provider before entering the loop: the first Win32_Process query costs
# ~10s on a loaded box (provider init), and a poll that slow lets a popup live long
# enough to be seen.
$null = Get-CimInstance Win32_Process -Filter $procFilter -ErrorAction SilentlyContinue

$killed = 0
$seen = @{}

while ((Get-Date) -lt $end) {
  $procs = Get-CimInstance Win32_Process -Filter $procFilter -ErrorAction SilentlyContinue
  $parentNames = @{}

  foreach ($p in $procs) {
    $ppid = [int]$p.ParentProcessId
    $cmdline = [string]$p.CommandLine
    $pname = ''
    if ($parentNames.ContainsKey($ppid)) { $pname = $parentNames[$ppid] }
    else {
      $par = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $ppid) -ErrorAction SilentlyContinue
      if ($par) { $pname = $par.Name }
      $parentNames[$ppid] = $pname
    }
    if ($schedulerParents -notcontains $pname) {
      # Second suspect class, logged only: an autonomous agent session's shell shows the
      # same symptom (a console window titled with the pwsh path) but its parent is
      # codely.exe / powershell.exe under wscript, not the scheduler. Killing those
      # would break live work (batch runners), so record the occurrence instead and let
      # the operator decide. Deduped by pid.
      if (@('codely.exe', 'wscript.exe', 'powershell.exe', 'pwsh.exe') -contains $pname) {
        $diagKey = 'diag:' + [string]$p.ProcessId
        if (-not $seen.ContainsKey($diagKey)) {
          $seen[$diagKey] = $true
          $up = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $p.ParentProcessId) -ErrorAction SilentlyContinue
          $up2 = $null
          if ($up) { $up2 = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $up.ParentProcessId) -ErrorAction SilentlyContinue }
          Write-GuardLog ("{0} | AGENT-CONSOLE-SEEN pid={1} name={2} parent={3} grandparent={4} cmd={5}" -f `
            (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $p.ProcessId, $p.Name, $pname,
            $(if ($up2) { $up2.Name } else { '' }), $cmdline)
        }
      }
      continue
    }
    $cmdline = [string]$p.CommandLine
    if ($cmdline -match $selfProtected) { continue }
    $key = [string]$p.ProcessId
    if ($seen.ContainsKey($key)) { continue }
    $seen[$key] = $true
    try {
      # Kill the whole tab subtree: the console host and the program inside it have
      # separate parents once Windows Terminal hands the console off, so stopping only
      # the host leaves an orphan running with no window.
      $victims = New-Object System.Collections.ArrayList
      $queue = New-Object System.Collections.Queue
      $queue.Enqueue([int]$p.ProcessId)
      $guard = 0
      while ($queue.Count -gt 0 -and $guard -lt 50) {
        $cur = [int]$queue.Dequeue()
        [void]$victims.Add($cur)
        $kids = Get-CimInstance Win32_Process -Filter ("ParentProcessId=" + $cur) -ErrorAction SilentlyContinue
        foreach ($k in $kids) { $queue.Enqueue([int]$k.ProcessId) }
        $guard++
      }
      for ($i = $victims.Count - 1; $i -ge 0; $i--) {
        Stop-Process -Id $victims[$i] -Force -ErrorAction SilentlyContinue
      }
      $killed++
      Write-GuardLog ("{0} | KILLED-SCHEDULER-CONSOLE pid={1} name={2} tree={3} cmd={4}" -f `
        (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $p.ProcessId, $p.Name,
        ($victims -join ','), $cmdline)
    } catch {
      Write-GuardLog ("{0} | KILL-FAIL pid={1} name={2} err={3}" -f `
        (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $p.ProcessId, $p.Name, $_.Exception.Message)
    }
  }
  Start-Sleep -Seconds 1
}

Write-GuardLog ("{0} | guard v4 exit, killed={1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $killed)
$mutex.ReleaseMutex()
$mutex.Dispose()