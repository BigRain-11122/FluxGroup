# local-only-mode.ps1 - bm-a local-compute-only switch (CEO order 2026-10-20).
#
# Purpose: from tonight bm-a is a LOCAL compute machine only. Codely CLI is
# repointed to the local 35B (llama.cpp OpenAI-compatible, 127.0.0.1:8090) and
# the cloud generator MCP is removed from this machine. No cloud fallback:
# if the local endpoint is down the switch still applies (fail-closed) and
# writes an alert file instead of silently going back to cloud.
#
# Usage:
#   local-only-mode.ps1 -Action Status
#   local-only-mode.ps1 -Action On  -Backend local
#   local-only-mode.ps1 -Action On  -Backend doubao -BaseUrl https://... -ApiKey ... -Model ...
#   local-only-mode.ps1 -Action Off
#
# Backups: <home>\.codely-cli\*.bak-localonly-<stamp> (never overwritten).

param(
    [ValidateSet('On', 'Off', 'Status')][string]$Action = 'Status',
    [ValidateSet('local', 'doubao')][string]$Backend = 'local',
    [string]$BaseUrl = '',
    [string]$ApiKey = '',
    [string]$Model = 'qwen3.6-35b-a3b',
    [int]$WaitSeconds = 600
)

$ErrorActionPreference = 'Stop'
$cliDir = Join-Path $env:USERPROFILE '.codely-cli'
$settingsPath = Join-Path $cliDir 'settings.json'
$envPath = Join-Path $cliDir '.env'
$statePath = Join-Path $cliDir 'local-only-state.json'
$alertPath = Join-Path $cliDir 'local-only-alert.txt'
$projSettings = Join-Path (Split-Path -Parent $PSScriptRoot) '.codely-cli\settings.json'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

function Write-Utf8NoBom([string]$path, [string]$text) {
    $dir = Split-Path -Parent $path
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    [System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding($false)))
}

function Backup-Once([string]$path, [string]$tag) {
    if (-not (Test-Path $path)) { return $null }
    $bak = "$path.bak-localonly-$tag"
    if (-not (Test-Path $bak)) { Copy-Item -LiteralPath $path -Destination $bak -Force }
    return $bak
}

function Test-Local([string]$url) {
    try {
        $u = $url -replace '/v1/?$', ''
        $null = Invoke-RestMethod -Uri ($u + '/health') -TimeoutSec 3
        return $true
    } catch {
        try {
            $null = Invoke-RestMethod -Uri ($url.TrimEnd('/') + '/models') -TimeoutSec 3
            return $true
        } catch { return $false }
    }
}

function Set-EnvKey([string]$path, [hashtable]$kv) {
    $lines = @()
    if (Test-Path $path) { $lines = @(Get-Content -LiteralPath $path -Encoding UTF8) }
    $out = New-Object System.Collections.Generic.List[string]
    $seen = @{}
    foreach ($l in $lines) {
        $m = [regex]::Match($l, '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=')
        if ($m.Success -and $kv.ContainsKey($m.Groups[1].Value)) {
            $k = $m.Groups[1].Value
            $out.Add("$k=$($kv[$k])")
            $seen[$k] = $true
        } else {
            $out.Add($l)
        }
    }
    foreach ($k in $kv.Keys) { if (-not $seen.ContainsKey($k)) { $out.Add("$k=$($kv[$k])") } }
    Write-Utf8NoBom $path ($out -join "`r`n")
}

switch ($Action) {
    'Status' {
        $st = $null
        if (Test-Path $statePath) { $st = Get-Content -Raw -Encoding UTF8 $statePath | ConvertFrom-Json }
        $url = ''
        if (Test-Path $envPath) {
            $line = Select-String -Path $envPath -Pattern '^\s*OPENAI_BASE_URL\s*=' | Select-Object -First 1
            if ($line) { $url = ($line.Line -split '=', 2)[1].Trim() }
        }
        $live = $false
        if ($url) { $live = Test-Local $url }
        [pscustomobject]@{
            mode      = if ($st) { $st.mode } else { 'unset' }
            backend   = if ($st) { $st.backend } else { '' }
            base_url  = $url
            endpoint  = if ($live) { 'UP' } else { 'DOWN' }
            applied_at = if ($st) { $st.applied_at } else { '' }
        } | Format-List
    }
    'On' {
        if ($Backend -eq 'local' -and -not $BaseUrl) { $BaseUrl = 'http://127.0.0.1:8090/v1' }
        if (-not $BaseUrl) { throw 'BaseUrl required for backend=doubao' }
        if ($Backend -eq 'doubao' -and -not $ApiKey) { throw 'ApiKey required for backend=doubao' }

        if ($Backend -eq 'local') {
            $deadline = (Get-Date).AddSeconds($WaitSeconds)
            while (-not (Test-Local $BaseUrl) -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 10 }
        }
        $live = Test-Local $BaseUrl
        if (-not $live) {
            $msg = '{0} local endpoint {1} NOT reachable; local-only applied anyway (fail-closed, no cloud fallback).' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $BaseUrl
            Write-Utf8NoBom $alertPath $msg
        } elseif (Test-Path $alertPath) { Remove-Item -LiteralPath $alertPath -Force }

        Backup-Once $settingsPath $stamp | Out-Null
        Backup-Once $envPath $stamp | Out-Null

        $key = if ($ApiKey) { $ApiKey } elseif ($Backend -eq 'local') { 'local-no-key' } else { '' }
        Set-EnvKey $envPath @{
            CUSTOM_AUTH    = '1'
            OPENAI_API_KEY = $key
            OPENAI_BASE_URL = $BaseUrl
        }

        $cfg = [pscustomobject]@{}
        if (Test-Path $settingsPath) {
            $cfg = Get-Content -Raw -Encoding UTF8 $settingsPath | ConvertFrom-Json
        }
        $slots = @('model', 'flashModel', 'multimodalModel', 'defaultAgentModel')
        foreach ($s in $slots) {
            if ($cfg.PSObject.Properties.Name -contains $s) { $cfg.$s = $Model }
            else { $cfg | Add-Member -NotePropertyName $s -NotePropertyValue $Model }
        }
        if (-not ($cfg.PSObject.Properties.Name -contains 'contentGenerator')) {
            $cfg | Add-Member -NotePropertyName contentGenerator -NotePropertyValue ([pscustomobject]@{ authType = 'openai'; wireApi = 'chat' })
        } else {
            $cg = $cfg.contentGenerator
            $cg | Add-Member -NotePropertyName authType -NotePropertyValue 'openai' -Force
            $cg | Add-Member -NotePropertyName wireApi -NotePropertyValue 'chat' -Force
        }
        Write-Utf8NoBom $settingsPath ($cfg | ConvertTo-Json -Depth 20)

        # Remove the cloud generator MCP from this machine (business generation is local-only).
        $mcpRemoved = $false
        if (Test-Path $projSettings) {
            Backup-Once $projSettings $stamp | Out-Null
            $p = Get-Content -Raw -Encoding UTF8 $projSettings | ConvertFrom-Json
            if ($p.PSObject.Properties.Name -contains 'mcpServers') {
                $names = @($p.mcpServers.PSObject.Properties.Name)
                foreach ($n in $names) {
                    if ($n -match '^(TJGenerators|tjgenerators)$') {
                        $p.mcpServers.PSObject.Properties.Remove($n)
                        $mcpRemoved = $true
                    }
                }
            }
            Write-Utf8NoBom $projSettings ($p | ConvertTo-Json -Depth 20)
        }

        $state = [pscustomobject]@{
            mode         = 'local-only'
            backend      = $Backend
            base_url     = $BaseUrl
            model        = $Model
            endpoint_up  = $live
            mcp_removed  = $mcpRemoved
            applied_at   = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
            applied_by   = 'Tools/local-only-mode.ps1'
        }
        Write-Utf8NoBom $statePath ($state | ConvertTo-Json -Depth 5)
        $state | Format-List
    }
    'Off' {
        $restored = @()
        foreach ($p in @($settingsPath, $envPath, $projSettings)) {
            $bak = Get-ChildItem -LiteralPath $p -Filter '*.bak-localonly-*' -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($bak) { Copy-Item -LiteralPath $bak.FullName -Destination $p -Force; $restored += $bak.Name }
        }
        if (Test-Path $statePath) { Remove-Item -LiteralPath $statePath -Force }
        if (Test-Path $alertPath) { Remove-Item -LiteralPath $alertPath -Force }
        "restored: $($restored -join ', ')"
    }
}