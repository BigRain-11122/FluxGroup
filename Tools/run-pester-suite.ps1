$ErrorActionPreference = 'Continue'
Import-Module Pester -RequiredVersion 5.9.1 -Global
Write-Output ('Pester loaded: ' + (Get-Module Pester).Version)
$files = @(
    'C:\Users\sjs20\Desktop\FluxGroup\Tools\secret-scan.Tests.ps1',
    'C:\Users\sjs20\Desktop\FluxGroup\Tools\orders-registry.Tests.ps1',
    'C:\Users\sjs20\Desktop\FluxGroup\Tools\task-health.Tests.ps1'
)
foreach ($f in $files) {
    Write-Output ('=== ' + (Split-Path -Leaf $f) + ' ===')
    $r = Invoke-Pester -Path $f -Output Detailed -PassThru
    Write-Output ('SUMMARY ' + (Split-Path -Leaf $f) + ' passed=' + $r.PassedCount + ' failed=' + $r.FailedCount + ' total=' + $r.TotalCount)
    if ($r.FailedCount -gt 0) {
        foreach ($t in ($r.Tests | Where-Object { $_.Result -eq 'Failed' })) {
            Write-Output ('FAIL: ' + $t.ExpandedPath)
            foreach ($err in $t.ErrorRecord) { Write-Output ('  ' + ($err | Out-String).Trim()) }
        }
    }
}
Write-Output 'RUNNER_DONE'
