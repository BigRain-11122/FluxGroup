# fleet-order-bus.ps1 - one-command fan-out to every fleet lane (CEO 2026-10-27).
# CEO issues one sentence on any machine; this script:
#   1) splits it into lane assignments (deterministic keyword router, no LLM)
#   2) appends the order row to docs/orders.md (git = command plane)
#   3) commits + pushes the HOT repo
#   4) pokes FleetLink with each node's wake_tasks and verifies the node fetched OUR sha
#   5) writes a receipt so "who got it / when" is auditable
# After the poke the machines' own OS loops pull and start; no manual assignment.
# Usage:
#   powershell Tools/fleet-order-bus.ps1 -Send "把漫剧 60 集全部补上配音并合流"
#   powershell Tools/fleet-order-bus.ps1 -Send "..." -DryRun
#   powershell Tools/fleet-order-bus.ps1 -Status
param(
    [string]$Send = '',
    [string]$SendFile = '',
    [string]$Lanes = '',
    [switch]$DryRun,
    [switch]$Status,
    [string]$Root = ''
)
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
if (-not $Root) { $Root = Split-Path -Parent $PSScriptRoot }
# PS5.1 argv mangles Chinese through the console code page; a UTF-8 file is the safe path.
if ($SendFile -and (Test-Path $SendFile)) { $Send = [System.IO.File]::ReadAllText($SendFile, [System.Text.Encoding]::UTF8).Trim() }
$cfgF = Join-Path $Root 'Tools\fleet-nodes.json'
$ordersF = Join-Path $Root 'docs\orders.md'
$busDir = Join-Path $Root 'cph4\fleet\order-bus'
$receiptDir = Join-Path $busDir 'receipts'
if (-not (Test-Path $receiptDir)) { New-Item -ItemType Directory -Force -Path $receiptDir | Out-Null }
$git = 'git'

function Now-Stamp { (Get-Date).ToString('yyyy-MM-dd HH:mm') }
function New-Id { 'OB-' + (Get-Date).ToString('yyyyMMdd-HHmmss') + '-' + (Get-Random -Minimum 100 -Maximum 999) }

function Route-Lanes([string]$text) {
    if ($Lanes) { return $Lanes }
    $t = $text.ToLower()
    $explicit = ([regex]::Matches($t, 'bm-[abc]')).Count
    if ($explicit -ge 2 -or $t -match '所有|全部|全域|全集团|各司|子公司|机队|全员|自检|回执|三机|全线|各机') { return 'bm-a,bm-b,bm-c' }
    $set = New-Object System.Collections.Generic.HashSet[string]
    if ($t -match '视频|渲染|出片|mv|镜头|kf|i2v|图|画|美术|lora|模型|gpu|comfy|升档') { [void]$set.Add('bm-c') }
    if ($t -match '配音|音|tts|bgm|混音|歌|语音|旁白|whisper|字幕') { [void]$set.Add('bm-b') }
    if ($t -match '装配|剪辑|合流|核验|签|提交|仓库|订单|调度|日报|台账|发布|自动化|命令') { [void]$set.Add('bm-a') }
    if ($set.Count -eq 0) { return 'bm-a,bm-b,bm-c' }
    $arr = @()
    foreach ($x in $set) { $arr += [string]$x }
    return ($arr -join ',')
}

function Lane-Duty([string]$lane) {
    switch ($lane) {
        'bm-a' { '拆解/装配/核验/回执；HQ 车道可执行件立即开工' }
        'bm-b' { '配音/混音/词锚/声音车道可执行件立即开工' }
        'bm-c' { 'KF/i2v/渲染/画质链可执行件立即开工' }
        default { '按令自领' }
    }
}

if ($Status) {
    $files = @(Get-ChildItem $receiptDir -Filter '*.json' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 10)
    if ($files.Count -eq 0) { Write-Output 'NO-ORDERS'; exit 0 }
    foreach ($f in $files) {
        try {
            $j = Get-Content -Raw -Encoding UTF8 $f.FullName | ConvertFrom-Json
            Write-Output ('{0} lanes={1} nodes={2} sha={3} {4}' -f $j.id, ($j.lanes -join ','), ($j.nodes -join ','), $j.sha, $j.dispatch)
        } catch { }
    }
    exit 0
}

if (-not $Send) { Write-Output 'usage: -Send "<command>" [-DryRun] | -Status'; exit 2 }

$id = New-Id
$laneList = @()
$laneStr = [string](Route-Lanes $Send)
foreach ($p in $laneStr.Split(',')) { $q = $p.Trim(); if ($q) { $laneList = $laneList + $q } }
$stamp = Now-Stamp
# Unique command file = conflict-free transport. Every machine writes docs/orders.md
# locally, so that file diverges and blocks fast-forward; a new file per command does not.
if (-not $DryRun) {
$cmdDir = Join-Path $Root 'cph4\fleet\cmd'
if (-not (Test-Path $cmdDir)) { New-Item -ItemType Directory -Force -Path $cmdDir | Out-Null }
$cmdFile = Join-Path $cmdDir ($id + '.json')
$cmdObj = [ordered]@{ id = $id; ts = $stamp; text = $Send; lanes = $laneList; src = $env:COMPUTERNAME; status = 'dispatched' }
$cmdObj | ConvertTo-Json -Depth 4 | Set-Content -Path $cmdFile -Encoding UTF8
}
$sha = ''
if ($DryRun) {
    Write-Output ('DRY id={0} lanes={1}' -f $id, ($laneList -join ','))
    foreach ($l in $laneList) { Write-Output ('  ' + $l + ' :: ' + (Lane-Duty $l)) }
    exit 0
}

# ---- 1) order row (canonical ledger) ----
$duty = ($laneList | ForEach-Object { $_ + '=' + (Lane-Duty $_) }) -join '；'
$row = '| {0}（自动分发 {1}） | CEO 令（原话）：「{2}」 | **机队自动分发令（id={1}）**：车道={3}；{4}；各车道轮首自领、禁等人工分配；回执落 cph4/fleet/order-bus/receipts/ | dispatched {1} | [via fleet-order-bus] |' -f $stamp, $id, ($Send -replace '\|', '/'), ($laneList -join '/'), $duty
Add-Content -LiteralPath $ordersF -Value $row -Encoding UTF8

# ---- 2) commit + push (HOT repo = command plane) ----
& $git -C $Root add -- docs/orders.md ('cph4/fleet/cmd/' + $id + '.json') 2>$null
& $git -C $Root commit -m ('orders: auto fanout ' + $id) -m ('CEO one-line command split to lanes: ' + ($laneList -join ',')) -- docs/orders.md ('cph4/fleet/cmd/' + $id + '.json') 2>$null | Out-Null
& $git -C $Root fetch origin main:refs/remotes/origin/main -q 2>$null
$behind = 0
try { $behind = [int](& $git -C $Root rev-list --count 'HEAD..origin/main') } catch { }
if ($behind -gt 0) {
    & $git -C $Root -c rebase.autostash=true rebase origin/main 2>$null | Out-Null
}
$pushOut = & $git -C $Root push origin HEAD:main 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Output ('PUSH-FAIL ' + ($pushOut -join ' '))
    exit 1
}
try { $sha = [string](& $git -C $Root rev-parse HEAD) } catch { }

# ---- 3) poke each node with its own wake_tasks ----
$cfg = $null
try { $cfg = Get-Content -Raw -Encoding UTF8 $cfgF | ConvertFrom-Json } catch { }
$nodes = @()
$dispatch = 'no-cfg'
if ($cfg -and $cfg.nodes) {
    foreach ($n in @($cfg.nodes)) {
        if (-not $n.enabled) { continue }
        if ($n.lane -eq 'hq-central-night-gpu' -and ($laneList -notcontains 'bm-a')) { continue }
        if ($n.lane -eq 'cpu-sound' -and ($laneList -notcontains 'bm-b')) { continue }
        if ($n.lane -eq 'gpu-production' -and ($laneList -notcontains 'bm-c')) { continue }
        $nodes += [string]$n.id
    }
    $tasks = @()
    foreach ($n in @($cfg.nodes)) {
        if (-not $n.enabled) { continue }
        if ($n.id -notin $nodes) { continue }
        foreach ($t in @($n.wake_tasks)) { if ($t) { $tasks += [string]$t } }
    }
    $tasks = @($tasks | Sort-Object -Unique)
    $disp = & (Join-Path $Root 'Tools\fleet-dispatch.ps1') -Root $Root -Reason ('order:' + $id) -Tasks $tasks -ExpectSha $sha 2>&1
    $dispatch = ($disp -join ' ').Trim()
}

# ---- 4) receipt ----
$receipt = [ordered]@{
    id = $id; ts = $stamp; text = $Send; lanes = $laneList; nodes = $nodes
    sha = $sha; dispatch = $dispatch; dry = $false
}
$receipt | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $receiptDir ($id + '.json')) -Encoding UTF8
& $git -C $Root add -- (Join-Path 'cph4\fleet\order-bus\receipts' ($id + '.json')) 2>$null

Write-Output ('ORDER {0} lanes={1} nodes={2} sha={3}' -f $id, ($laneList -join ','), ($nodes -join ','), $sha)
Write-Output ('DISPATCH ' + $dispatch)