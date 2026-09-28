# task-health.Tests.ps1 - Pester unit tests for Convert-IsoDuration.
# OH-2026-09-28-cph4 slice1#1 first campaign target 3: ISO8601 duration three states.
# Extraction = deterministic brace-counter (AST FindAll proved unreliable here);
# Pester v5 phase rule: all state lives in BeforeAll; never dot-source the script
# itself (its body runs scanners on load).
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
    $thFile = Join-Path $PSScriptRoot 'task-health.ps1'
    $t = Get-FunctionText -Path $thFile -Name 'Convert-IsoDuration'
    if (-not $t) { throw 'function Convert-IsoDuration not found in task-health.ps1' }
    $tmp = Join-Path $env:TEMP 'pester-task-health-funcs.ps1'
    Set-Content -Path $tmp -Value $t -Encoding UTF8
    . $tmp
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}

Describe 'Convert-IsoDuration ISO8601 three states' {
    It 'parses minute durations' {
        (Convert-IsoDuration 'PT10M') | Should -Be 10
    }
    It 'parses hour+minute combos' {
        (Convert-IsoDuration 'PT1H30M') | Should -Be 90
    }
    It 'parses days' {
        (Convert-IsoDuration 'P1D') | Should -Be 1440
    }
    It 'parses weeks' {
        (Convert-IsoDuration 'P1W') | Should -Be 10080
    }
    It 'returns -1 on empty input' {
        (Convert-IsoDuration '') | Should -Be -1
    }
    It 'returns -1 on unparsable input' {
        (Convert-IsoDuration 'garbage') | Should -Be -1
        (Convert-IsoDuration 'PT')      | Should -Be -1
    }
}
