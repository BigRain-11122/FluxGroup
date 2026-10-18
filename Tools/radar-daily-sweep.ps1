# radar daily sweep - first run demo (per cph4/github-radar.md daily section, CEO order 2026-10-16)
# Method: anonymous GitHub search REST API (10 req/min quota, zero credentials) - fallback on machines without gh auth.
$ErrorActionPreference = 'Continue'

function Sweep($query, $label, $limit) {
    Write-Output $label
    $q = [uri]::EscapeDataString($query)
    try {
        $r = Invoke-RestMethod -Uri ("https://api.github.com/search/repositories?q=" + $q + "&sort=stars&order=desc&per_page=" + $limit) -TimeoutSec 20
        foreach ($it in $r.items) {
            $d = 'no-desc'
            if ($it.description) { $d = $it.description.Substring(0, [Math]::Min(95, $it.description.Length)) }
            Write-Output ("{0} | {1} | {2}" -f $it.stargazers_count, $it.full_name, $d)
        }
    } catch { Write-Output ("SWEEP-ERR: " + $_.Exception.Message) }
}

$dA = (Get-Date).AddDays(-30).ToString('yyyy-MM-dd')
$dB = (Get-Date).AddDays(-7).ToString('yyyy-MM-dd')
Sweep ('created:>' + $dA + ' stars:>150') '--- A: new high-star repos created within 30 days ---' 14
Sweep ('agent OR i2v OR unity OR backtesting stars:>400 pushed:>' + $dB) '--- B: group-relevant domains, active + high star ---' 10
Sweep ('comfyui OR "video generation" OR "text-to-video" OR lora OR animediff stars:>600 pushed:>' + $dB) '--- C: production-craft refresh (workflows/models/params, CEO order 2026-10-18) ---' 12
