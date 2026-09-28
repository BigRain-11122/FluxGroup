# secret-scan.Tests.ps1 - Pester regression for the secret-leak gate pattern table.
# OH-2026-09-28-cph4 slice1#1 (first campaign) + slice1#2 pairing law:
# any pattern-table change must pass this suite before commit.
# Pester v5 phase rule: ALL state (paths, table parse) must live in BeforeAll -
# top-level assignments from the discovery phase are null in the run phase.
# Assertions limited to the PS-inbox-Pester 3.4 compatible subset (-Be/-Match/
# -Throw/-Not): the runner machine has the in-box 3.4 Should shadowing risk.
BeforeAll {
    $script:ScanFile = Join-Path $PSScriptRoot 'secret-scan.ps1'
    $script:Table = @{}
    $inBlock = $false
    foreach ($line in (Get-Content -LiteralPath $script:ScanFile -Encoding UTF8)) {
        if ($line -match '^\$patterns\s*=\s*\[ordered\]@\{') { $inBlock = $true; continue }
        if ($inBlock -and $line -match '^\}') { break }
        if ($inBlock -and $line -match "^\s*'([^']+)'\s*=\s*'(.*)'\s*$") {
            $script:Table[$matches[1]] = $matches[2]
        }
    }
    $script:Raw = Get-Content -LiteralPath $script:ScanFile -Raw -Encoding UTF8
}

Describe 'secret-scan pattern table' {
    It 'has >= 17 high-confidence rules (6 original + 11 gitleaks-ported)' {
        ($script:Table.Count -ge 17) | Should -Be $true
    }
    It 'every pattern compiles as a .NET regex' {
        foreach ($r in $script:Table.Values) { { [regex]::new($r) } | Should -Not -Throw }
    }
    It 'known-positive vectors hit their rules' {
        $t = $script:Table
        'AKIAIOSFODNN7EXAMPLE'                | Should -Match $t['aws-access-key']
        ('ghp_' + ('a' * 36))                 | Should -Match $t['github-pat']
        ('sk-ant-api03-' + ('A' * 93) + 'AA') | Should -Match $t['anthropic-key']
        ('AIza' + ('a' * 35))                 | Should -Match $t['gcp-api-key']
        ('hf_' + ('a' * 34))                  | Should -Match $t['hf-token']
        ('npm_' + ('a' * 36))                 | Should -Match $t['npm-token']
        ('github_pat_' + ('a' * 82))          | Should -Match $t['github-fg-pat']
        ('glpat-' + ('a' * 20))               | Should -Match $t['gitlab-pat']
    }
    It 'benign lines do not hit any rule (false-positive guard)' {
        $t = $script:Table
        $benign = @(
            'normal commit message with issue 12345',
            'AIza prefix discussed in documentation text',
            'the sk-ant-api03- story in our notes',
            'npm install -g @playwright/mcp',
            'install huggingface token docs go here',
            'stripe test transaction narrative line'
        )
        foreach ($b in $benign) {
            foreach ($r in $t.Values) { $b | Should -Not -Match $r }
        }
    }
    It 'allowAnchors keeps the documented AWS fixture' {
        $script:Raw | Should -Match 'AKIAIOSFODNN7EXAMPLE'
    }
}
