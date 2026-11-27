# orders-registry.Tests.ps1 - Pester unit tests for the registry gate functions.
# OH-2026-09-28-cph4 slice1#1 first campaign target 2:
# Get-Lock stale-lock break + Test-OrderLine six-field schema + Quote-Sig truncation.
# Extraction = deterministic brace-counter (AST FindAll proved unreliable here);
# Pester v5 phase rule: all state lives in BeforeAll; never dot-source the script
# itself (its body runs a destructive switch on load).
BeforeAll {
    function Get-FunctionText {
        param($Path, $Name)
        $src = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        $m = [regex]::Match($src, ('function\s+' + [regex]::Escape($Name) + '\b'))
        if (-not $m.Success) { return $null }
        $start = $src.IndexOf('{', $m.Index)
        if ($start -lt 0) { return $null }
        $depth = 0
        for ($i = $start; $i -lt $src.Length; $i++) {
            $ch = $src[$i]
            if ($ch -eq '{') { $depth++ }
            elseif ($ch -eq '}') { $depth--; if ($depth -eq 0) { return $src.Substring($m.Index, $i - $m.Index + 1) } }
        }
        return $null
    }
    $regFile = Join-Path $PSScriptRoot '..\cph4\registry\orders-registry.ps1'
    $chunks = @()
    foreach ($name in @('Test-OrderLine', 'Quote-Sig', 'Get-Lock', 'Release-Lock')) {
        $t = Get-FunctionText -Path $regFile -Name $name
        if (-not $t) { throw "function $name not found in orders-registry.ps1" }
        $chunks += $t
    }
    $tmp = Join-Path $env:TEMP 'pester-orders-registry-funcs.ps1'
    Set-Content -Path $tmp -Value ($chunks -join "`n") -Encoding UTF8
    . $tmp
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    $script:Lock = Join-Path $TestDrive 'orders.lock'
}

Describe 'Test-OrderLine six-field schema' {
    It 'accepts a valid six-field line' {
        $valid = '{"id":"O-1","ts":"t","quote_sig":"0123456789abcdef","disposition":"d","status":"s","source_hash":"h"}'
        Test-OrderLine $valid | Should -Be $true
    }
    It 'rejects a line missing quote_sig' {
        $bad = '{"id":"O-1","ts":"t","disposition":"d","status":"s","source_hash":"h"}'
        Test-OrderLine $bad | Should -Be $false
    }
    It 'rejects invalid JSON' {
        Test-OrderLine '{bad json' | Should -Be $false
    }
    It 'accepts blank lines' {
        Test-OrderLine '   ' | Should -Be $true
        Test-OrderLine ''    | Should -Be $true
    }
}

Describe 'Quote-Sig normalization and truncation' {
    It 'produces 16 lowercase hex chars' {
        $sig = Quote-Sig 'hello   world'
        $sig | Should -Match '^[0-9a-f]{16}$'
    }
    It 'normalizes whitespace variants to the same sig' {
        (Quote-Sig 'hello   world') | Should -Be (Quote-Sig ' hello world ')
    }
    It 'different text yields different sig' {
        (Quote-Sig 'a b') | Should -Not -Be (Quote-Sig 'b a')
    }
}

Describe 'Get-Lock writer lock' {
    AfterEach { if (Test-Path $script:Lock) { Remove-Item $script:Lock -Force } }
    It 'throws when a fresh lock (age < 15min) is held' {
        Set-Content -Path $script:Lock -Value 'pid=1' -Encoding ASCII
        { Get-Lock } | Should -Throw
    }
    It 'breaks a stale lock (age > 15min) and re-creates it' {
        Set-Content -Path $script:Lock -Value 'pid=1' -Encoding ASCII
        (Get-Item $script:Lock).LastWriteTime = (Get-Date).AddMinutes(-16)
        { Get-Lock } | Should -Not -Throw
        Test-Path $script:Lock | Should -Be $true
    }
    It 'Release-Lock removes the lock' {
        Set-Content -Path $script:Lock -Value 'pid=1' -Encoding ASCII
        Release-Lock
        Test-Path $script:Lock | Should -Be $false
    }
}
