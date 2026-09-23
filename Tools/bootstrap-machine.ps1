# bootstrap-machine.ps1 - One-click new machine onboarding (cph4/onboarding.md).
# CEO order 2026-09-23: one-click deployment capability for any new machine.
# GROUP-LEVEL ORCHESTRATOR: this script only checks/fixes/registers and CALLS
# the proven per-repo bootstrap pieces (it never duplicates them):
#   bigmoney  -> python bootstrap.py + Tools\register_loop_task.ps1 (their own)
#   biggame   -> tools\MachineBoot.ps1 (their own 08 self-bootstrap)
#   fluxverse -> Tools\devloop\register_loop_task.ps1 + FluxVerseTick registration
# Everything idempotent: re-running on an onboarded machine = a health check.
# SILENCE LAW: every scheduled task is registered via InvisibleRunner.vbs.
# ASCII-only (encoding law). Exit 0 = machine ready (or already ready).
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File Tools\bootstrap-machine.ps1
#   powershell ... -File Tools\bootstrap-machine.ps1 -Roles group,bigmoney,fluxverse
#   powershell ... -File Tools\bootstrap-machine.ps1 -Roles biggame -MachineId C

param(
    [string[]]$Roles = @('group'),
    [string]$MachineId = 'A',
    [switch]$FreshEnv,
    [string]$Root = ''
)

$ErrorActionPreference = 'Continue'
if(-not $Root){ $Root = Split-Path -Parent $PSScriptRoot }   # -> FluxGroup repo root

$results = New-Object System.Collections.Generic.List[object]
function Add-Result([string]$area, [string]$status, [string]$detail){
    $script:results.Add([PSCustomObject]@{ Area=$area; Status=$status; Detail=$detail })
    Write-Host ('[{0,-14}] {1,-10} {2}' -f $area, $status, $detail)
}

$physItems = New-Object System.Collections.Generic.List[string]
function Add-Phys([string]$item){ $script:physItems.Add($item) }

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$onbDir = Join-Path $Root '.codely-cli\onboarding'
if(-not (Test-Path $onbDir)){ New-Item -ItemType Directory -Path $onbDir -Force | Out-Null }

# ---------------- P0 prerequisites ----------------
Write-Host '== P0 prerequisites =='
$git = Get-Command git -ErrorAction SilentlyContinue
if($git){ Add-Result 'prereq.git' 'PASS' $git.Source }
else { Add-Result 'prereq.git' 'NEEDS_USER' 'install Git for Windows'; Add-Phys('install Git for Windows') }

$codely = Get-Command codely -ErrorAction SilentlyContinue
if($codely){ Add-Result 'prereq.codely' 'PASS' $codely.Source }
else {
    Add-Result 'prereq.codely' 'NEEDS_USER' 'codely CLI not on PATH - install Tuanjie Cowork'
    Add-Phys('install Tuanjie Cowork (codely CLI + AI runtime)')
}

if($Roles -contains 'bigmoney'){
    $py = Get-Command python -ErrorAction SilentlyContinue
    if($py){
        $pyv = (& python --version) 2>&1
        Add-Result 'prereq.python' 'INFO' ("bigmoney role: {0} (>=3.10 required, bootstrap.py enforces)" -f $pyv)
    } else {
        Add-Result 'prereq.python' 'NEEDS_USER' 'bigmoney role needs Python >=3.10'
        Add-Phys('install Python >=3.10 for the BigMoney role')
    }
}

$drv = Get-PSDrive -Name $Root.Substring(0,1)
$freeGB = [math]::Round($drv.Free/1GB,1)
if($freeGB -ge 20){ Add-Result 'prereq.disk' 'PASS' ("free {0} GB (watermark >=20)" -f $freeGB) }
else { Add-Result 'prereq.disk' 'WARN' ("free {0} GB below 20GB retention watermark" -f $freeGB) }

# ---------------- P1 identity (CEO physical item by design) ----------------
Write-Host '== P1 identity =='
$sshKey = Join-Path $env:USERPROFILE '.ssh\id_ed25519'
$sshKeyRsa = Join-Path $env:USERPROFILE '.ssh\id_rsa'
if((Test-Path $sshKey) -or (Test-Path $sshKeyRsa)){
    Add-Result 'identity.sshkey' 'PASS' 'SSH key present'
} else {
    & ssh-keygen -t ed25519 -N '""' -f $sshKey -C ("flux-machine-" + $env:COMPUTERNAME) 2>$null
    if(Test-Path $sshKey){
        Add-Result 'identity.sshkey' 'FIXED' 'generated id_ed25519'
        Add-Phys('add the new SSH public key to GitHub (fleet access) - see report')
    } else {
        Add-Result 'identity.sshkey' 'NEEDS_USER' 'ssh-keygen failed - create key manually'
    }
}
$authOut = & ssh -T -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 git@github.com 2>&1
if(($authOut | Out-String) -match 'successfully authenticated'){
    Add-Result 'identity.github' 'PASS' 'GitHub SSH auth OK'
} else {
    Add-Result 'identity.github' 'NEEDS_USER' 'GitHub SSH auth failed - add key / network?'
    Add-Phys('authorize this machine SSH key on GitHub (BigRain-11122 private repos)')
}

# ---------------- P2 repos (clone per role, skip if present) ----------------
Write-Host '== P2 repos =='
$repoMap = [ordered]@{
    'bigmoney'  = @{ dir='quant\bigmoney';  url='git@github.com:BigRain-11122/BigMoney.git' }
    'biggame'   = @{ dir='gaming\MiniGame';  url='git@github.com:BigRain-11122/MiniGame.git' }
    'media'     = @{ dir='media\BigStream';  url='git@github.com:BigRain-11122/BigStream.git' }
    'fluxverse' = @{ dir='gaming\FluxVerse'; url='git@github.com:BigRain-11122/FluxVerse.git' }
}
if(-not (Test-Path (Join-Path $Root '.git'))){
    Add-Result 'repo.hq' 'NEEDS_USER' 'run from a cloned FluxGroup repo (git clone first)'
} else {
    Add-Result 'repo.hq' 'PASS' 'HQ repo present (onboarding ran from it)'
}
foreach($role in $repoMap.Keys){
    if($Roles -notcontains $role){ continue }
    $m = $repoMap[$role]
    $dst = Join-Path $Root $m.dir
    if(Test-Path (Join-Path $dst '.git')){
        Add-Result ("repo.{0}" -f $role) 'PASS' 'already cloned'
        continue
    }
    & git clone $m.url $dst 2>&1 | Out-Null
    if($LASTEXITCODE -eq 0 -and (Test-Path (Join-Path $dst '.git'))){
        Add-Result ("repo.{0}" -f $role) 'FIXED' 'cloned'
    } else {
        Add-Result ("repo.{0}" -f $role) 'NEEDS_USER' 'clone failed (remote missing? BigStream/FluxVerse remotes may still be pending CEO)'
        Add-Phys(("ensure GitHub private repo exists + this key has access: " + $m.url))
    }
}

# ---------------- P3 per-repo environment (delegate to their own tools) ----------------
Write-Host '== P3 environment =='
$bm = Join-Path $Root 'quant\bigmoney'
if($Roles -contains 'bigmoney' -and (Test-Path (Join-Path $bm '.git'))){
    $marker = Join-Path $bm '.codely-cli\onboarding\bootstrap.done'
    if((Test-Path $marker) -and -not $FreshEnv){
        Add-Result 'env.bigmoney' 'PASS' 'bootstrap.py done before (use -FreshEnv to redo)'
    } else {
        Push-Location $bm
        & python bootstrap.py 2>&1 | ForEach-Object { Write-Host ("  bm| " + $_) }
        $rc = $LASTEXITCODE
        Pop-Location
        if($rc -eq 0){
            New-Item -ItemType Directory -Path (Split-Path $marker -Parent) -Force | Out-Null
            Set-Content -Path $marker -Value $stamp -Encoding ascii
            Add-Result 'env.bigmoney' 'FIXED' 'bootstrap.py OK (deps+smoke20+dashboard)'
        } else {
            Add-Result 'env.bigmoney' 'NEEDS_USER' ('bootstrap.py exit {0} - see its output' -f $rc)
        }
    }
}
$mg = Join-Path $Root 'gaming\MiniGame'
if($Roles -contains 'biggame' -and (Test-Path (Join-Path $mg '.git'))){
    $mj = Join-Path $mg 'tools\machine.json'
    $tpl = Join-Path $mg 'tools\machine.json.template'
    if(Test-Path $mj){ Add-Result 'env.biggame' 'PASS' 'machine.json present (local identity, untracked)' }
    elseif(Test-Path $tpl){
        Copy-Item $tpl $mj
        Add-Result 'env.biggame' 'FIXED' 'machine.json created from template (MachineBoot stamps ids)'
    } else {
        Add-Result 'env.biggame' 'NEEDS_USER' 'machine.json.template missing'
    }
    if(Test-Path (Join-Path $mg 'tools\MachineBoot.ps1')){
        Push-Location $mg
        & powershell -NoProfile -ExecutionPolicy Bypass -File 'tools\MachineBoot.ps1' -MachineId $MachineId 2>&1 |
            ForEach-Object { Write-Host ("  bg| " + $_) }
        Pop-Location
        Add-Result 'env.biggame.boot' 'INFO' 'MachineBoot ran (its own gates decide task registration)'
        Add-Phys('Tuanjie Hub login + MCP authorization are one-time manual steps (their checklist)')
    }
}

# ---------------- P4 scheduled tasks (silence law: VBS wrapper) ----------------
Write-Host '== P4 scheduled tasks =='
$vbs = Join-Path $Root 'Tools\InvisibleRunner.vbs'
if(Test-Path $vbs){ Add-Result 'task.vbs' 'PASS' 'HQ InvisibleRunner.vbs present' }
else { Add-Result 'task.vbs' 'NEEDS_USER' 'Tools\InvisibleRunner.vbs missing' }

if($Roles -contains 'group' -and (Test-Path $vbs)){
    $a = New-ScheduledTaskAction -Execute 'wscript.exe' `
        -Argument ('//B //nologo "' + $vbs + '" powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + (Join-Path $Root 'cph4\evolution-tick.ps1') + '"') `
        -WorkingDirectory $Root
    $t = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At '09:17'
    $s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
    Register-ScheduledTask -TaskName 'FluxGroup-EvolutionTick' -Action $a -Trigger $t -Settings $s -Force | Out-Null
    Add-Result 'task.evolution' 'FIXED' 'FluxGroup-EvolutionTick registered (SUN 09:17, silent, self-contained HQ vbs)'
}

if($Roles -contains 'bigmoney' -and (Test-Path (Join-Path $bm 'Tools\register_loop_task.ps1'))){
    Push-Location $bm
    & powershell -NoProfile -ExecutionPolicy Bypass -File 'Tools\register_loop_task.ps1' 2>&1 |
        ForEach-Object { Write-Host ("  bm| " + $_) }
    Pop-Location
    Add-Result 'task.bmloop' 'FIXED' 'Bigmoney-IterationLoop registered (their script, silent)'
}
$fv = Join-Path $Root 'gaming\FluxVerse'
if($Roles -contains 'fluxverse' -and (Test-Path (Join-Path $fv '.git'))){
    $fvTick = Join-Path $fv 'Tools\tick\tick.ps1'
    $fvVbs  = Join-Path $fv 'Tools\devloop\InvisibleRunner.vbs'
    if((Test-Path $fvTick) -and (Test-Path $fvVbs)){
        $start = Get-Date -Second 0
        while( (($start.Minute % 10) -ne 7) -or ($start -le (Get-Date)) ){ $start = $start.AddMinutes(1) }
        $a = New-ScheduledTaskAction -Execute 'wscript.exe' `
            -Argument ('//B //nologo "' + $fvVbs + '" powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $fvTick + '"') `
            -WorkingDirectory $fv
        $t = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration (New-TimeSpan -Days 3650)
        $s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
        Register-ScheduledTask -TaskName 'FluxVerseTick' -Action $a -Trigger $t -Settings $s -Force | Out-Null
        Add-Result 'task.fvtick' 'FIXED' ('FluxVerseTick registered (10min lane :x7, silent) first fire ' + $start)
    } else { Add-Result 'task.fvtick' 'NEEDS_USER' 'tick.ps1 or vbs missing in FluxVerse' }
    if(Test-Path (Join-Path $fv 'Tools\devloop\register_loop_task.ps1')){
        Push-Location $fv
        & powershell -NoProfile -ExecutionPolicy Bypass -File 'Tools\devloop\register_loop_task.ps1' 2>&1 |
            ForEach-Object { Write-Host ("  fv| " + $_) }
        Pop-Location
        Add-Result 'task.fvdevloop' 'FIXED' 'FluxVerse-DevLoop registered (their script, 5-min lane)'
    }
}

# ---------------- P5 report ----------------
Write-Host '== P5 report =='
$rep = @()
$rep += ('# Machine onboarding report ' + $stamp + '  (host ' + $env:COMPUTERNAME + ', roles: ' + ($Roles -join ',') + ')')
$rep += ''
$rep += ('| area | status | detail |'); $rep += ('|---|---|---|')
foreach($r in $results){ $rep += ('| {0} | {1} | {2} |' -f $r.Area, $r.Status, $r.Detail) }
$rep += ''
$rep += 'CEO physical items (deliberately not automated - identity/account law):'
if($physItems.Count -eq 0){ $rep += '- none this run' }
else { foreach($p in $physItems){ $rep += ('- ' + $p) } }
$repPath = Join-Path $onbDir ('onboarding-' + $stamp + '.md')
$rep | Out-File -FilePath $repPath -Encoding utf8
Get-ChildItem $onbDir -Filter 'onboarding-*.md' | Sort-Object Name -Descending |
    Select-Object -Skip 12 | Remove-Item -Force

Write-Host ''
Write-Host ('report: ' + $repPath)
$bad = @($results | Where-Object { $_.Status -eq 'NEEDS_USER' })
if($bad.Count -eq 0){ Write-Host 'RESULT: READY'; exit 0 }
else { Write-Host ('RESULT: PARTIAL - {0} item(s) need CEO/manual action (see report)' -f $bad.Count); exit 2 }
