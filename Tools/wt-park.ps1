# wt-park.ps1 - keep a minimized Windows Terminal catch-all alive (U060 machine silence)
# Why: codely headless sessions spawn one console per shell command without hiding
# (vendor bug, 2026-10-08 CEO popup order). With WT windowingBehavior=useExistingQuiet
# (set in WT settings.json), every new console session attaches as a silent tab to an
# EXISTING window instead of popping a visible window. This script guarantees that
# catch-all window exists after every logon: spawns a regular window with a never-exit
# keeper tab, then minimizes it. If a WT window already exists (user's own terminal),
# it does nothing - new consoles attach to the user's window quietly by the same rule.
# v2 2026-10-17 (bm-c, PR-20261017-02): v1 quake form showed the window and stole
# foreground focus on EVERY console attach (measured: visible+foreground for the whole
# attached-command lifetime). Regular minimized window absorbs silently (measured:
# iconic, zero focus, zero restore for the whole attach). Quake args removed.
$ErrorActionPreference = 'SilentlyContinue'
$existing = Get-Process WindowsTerminal -ErrorAction SilentlyContinue
if ($existing) { Write-Output 'WT already running - consoles will attach quietly'; exit 0 }
Start-Process wt.exe -ArgumentList 'new-tab','--title','keepalive','powershell.exe','-NoExit','-Command','Start-Sleep -Seconds 2147483647'
Start-Sleep -Seconds 8
Add-Type -Namespace UPark -Name W -MemberDefinition '[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);'
Get-Process WindowsTerminal -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.MainWindowHandle -ne 0) { [UPark.W]::ShowWindow($_.MainWindowHandle, 6) | Out-Null; Write-Output ('parked+minimized pid=' + $_.Id) }
}
