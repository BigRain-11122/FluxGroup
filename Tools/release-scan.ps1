# release-scan.ps1 - Release-Gate scanner (cph4/release-gate.md gate 2).
# Scans a packaged tree (or exported image layer dir) for the SEVEN BANNED
# faces + secret patterns + local path leaks. Whitelist packaging is gate 1;
# this is the independent machine check (gate 2) - FAIL blocks release.
# Usage:   powershell -NoProfile -File release-scan.ps1 -Path <package-dir>
# Exit:    0 = PASS (clean), 2 = FAIL (findings listed), 1 = usage error
# Pure ASCII (encoding law). Read-only scan.

param(
    [Parameter(Mandatory = $true)][string]$Path
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Path)) { Write-Output "release-scan: FATAL path not found: $Path"; exit 1 }
$root = (Resolve-Path $Path).ProviderPath
$findings = New-Object System.Collections.Generic.List[string]

# --- banned FILE/DIR names (relative match on name) ---
$bannedNames = @(
    '.git', '.env', '.venv', '__pycache__', '.codely-cli',
    'CODELY.md', 'HQ-FEEDBACK.md', 'evolution-ledger.md', 'orders.md',
    'backlog.md', 'state.json', 'BLUEPRINT.md'
)
# --- banned name KEYWORDS (dir or file name contains) ---
$bannedKeywords = @('id_rsa', '.ppk', 'secret', 'passwords')
# --- banned DIRS whose entire content face is internal ---
$bannedDirs = @('research', 'spec')
# --- text-content secret patterns (regex, case-sensitive where it matters) ---
$secretPatterns = @(
    'BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY',
    'AKIA[0-9A-Z]{16}',
    'ghp_[A-Za-z0-9]{20,}',
    'sk-[A-Za-z0-9]{20,}'
)
# --- local path / username leaks ---
$pathLeakPatterns = @('C:\\Users\\', '/home/[a-z]+/', '/Users/[A-Za-z]+/')

$items = Get-ChildItem -LiteralPath $root -Recurse -Force
foreach ($it in $items) {
    $rel = $it.FullName.Substring($root.Length).TrimStart('\', '/')
    if ($bannedNames -contains $it.Name) { $findings.Add("BANNED-NAME: $rel"); continue }
    foreach ($kw in $bannedKeywords) { if ($it.Name -like "*$kw*") { $findings.Add("BANNED-KEYWORD($kw): $rel"); break } }
    if ($it.PSIsContainer) {
        if ($bannedDirs -contains $it.Name) { $findings.Add("INTERNAL-DIR: $rel") }
        continue
    }
    # content scan: only small text-ish files (skip binaries and huge files)
    if ($it.Length -gt 2MB) { continue }
    $extOk = $it.Extension -match '^\.(txt|md|json|yml|yaml|xml|html|js|css|py|ps1|sh|cfg|conf|ini|env|toml|sql|csv|log|example|template)?$' -or $it.Extension -eq ''
    if (-not $extOk) { continue }
    try { $text = [IO.File]::ReadAllText($it.FullName) } catch { continue }
    foreach ($p in $secretPatterns) {
        if ($text -match $p) { $findings.Add("SECRET($p): $rel"); break }
    }
    foreach ($p in $pathLeakPatterns) {
        if ($text -match [regex]::Escape($p) -or $text -match ($p -replace '\\\\','\\')) {
            $findings.Add("PATH-LEAK($p): $rel"); break
        }
    }
}

if ($findings.Count -gt 0) {
    Write-Output ("release-scan: FAIL ({0} findings) in {1}" -f $findings.Count, $root)
    $findings | Select-Object -First 30 | ForEach-Object { Write-Output "  $_" }
    exit 2
}
Write-Output "release-scan: PASS (no banned face / secret / path leak) in $root"
exit 0
