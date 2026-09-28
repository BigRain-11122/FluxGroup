# install-gh-skills.ps1 v2 - install curated GitHub AI skills into user-level Codely skills dir
# CEO order P-2026-09-28-15 (GitHub install wave). Idempotent, silent, user-scope.
# Licenses (repo-level, api.github.com verified): anthropics/skills Apache-2.0 (picked skills),
# obra/superpowers MIT, gamedev-skills/awesome-gamedev-agent-skills Apache-2.0,
# tradermonty/claude-trading-skills MIT, conorbronsdon/avoid-ai-writing MIT,
# Gamezxz/pixel-art-studio MIT. ASCII-only body per group encoding law.
param(
  [string]$SkillsDir = (Join-Path $env:USERPROFILE '.codely-cli\skills'),
  [string]$Dl = (Join-Path $env:USERPROFILE 'tools\dl')
)
$ErrorActionPreference = 'Continue'
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}
foreach ($d in @($SkillsDir, $Dl)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }

function Get-Clone($repo) {
  $cloneDir = Join-Path $Dl ('skill-src-' + ($repo -replace '/', '__'))
  if (-not (Test-Path (Join-Path $cloneDir '.git'))) {
    git clone --depth 1 ("https://github.com/" + $repo + ".git") $cloneDir 2>$null
  }
  if (-not (Test-Path (Join-Path $cloneDir '.git'))) { Write-Output "MISS clone $repo"; return $null }
  return $cloneDir
}

function Copy-SkillFromRepo($repo, $srcRoot, $names) {
  $cloneDir = Get-Clone $repo
  if (-not $cloneDir) { return }
  foreach ($n in $names) {
    $src = Join-Path (Join-Path $cloneDir $srcRoot) $n
    $dst = Join-Path $SkillsDir $n
    if (Test-Path $src) {
      if (Test-Path $dst) { Write-Output "SKIP skill $n (present)" }
      else { Copy-Item $src $dst -Recurse -Force; Write-Output "OK skill $n" }
    } else { Write-Output "MISS skill $n (not in clone)" }
  }
}

function Copy-RepoRootSkill($repo, $name) {
  $cloneDir = Get-Clone $repo
  if (-not $cloneDir) { return }
  $dst = Join-Path $SkillsDir $name
  if (Test-Path $dst) { Write-Output "SKIP skill $name (present)"; return }
  New-Item -ItemType Directory -Force -Path $dst | Out-Null
  robocopy $cloneDir $dst /E /XD .git | Out-Null
  if (Test-Path (Join-Path $dst 'SKILL.md')) { Write-Output "OK skill $name (repo-root)" } else { Write-Output "MISS skill $name (no SKILL.md)" }
}

# wave 1 - general engineering / QA / docs-adjacent
Copy-SkillFromRepo 'anthropics/skills' 'skills' @('webapp-testing', 'mcp-builder', 'canvas-design', 'algorithmic-art', 'frontend-design')
Copy-SkillFromRepo 'obra/superpowers' 'skills' @('verification-before-completion', 'systematic-debugging', 'test-driven-development', 'dispatching-parallel-agents')

# wave 2 - game dev lines (Tuanjie/Unity + 2D topdown city + 3D unban + SiliconToon shader)
Copy-SkillFromRepo 'gamedev-skills/awesome-gamedev-agent-skills' 'skills\unity' @('unity-tilemap-2d', 'unity-csharp-scripting', 'unity-navmesh', 'unity-animation', 'unity-physics', 'unity-build-pipeline', 'unity-input-system', 'unity-scriptableobjects')
Copy-SkillFromRepo 'gamedev-skills/awesome-gamedev-agent-skills' 'skills\disciplines' @('create-game-assets', 'shader-programming', 'procedural-gen', 'game-ai', 'level-design', 'game-ui-ux')

# wave 2 - quant methodology (BigMoney ETF swing line)
Copy-SkillFromRepo 'tradermonty/claude-trading-skills' 'skills' @('backtest-expert', 'trade-hypothesis-ideator', 'signal-postmortem', 'data-quality-checker', 'drawdown-circuit-breaker', 'position-sizer')

# wave 2 - writing quality (anti AI-tone, BigLife script line / BigStream content line)
Copy-SkillFromRepo 'conorbronsdon/avoid-ai-writing' 'skills' @('avoid-ai-writing', 'ai-writing-detector', 'voice-preserving-rewriter')

# wave 2 - pixel art (SDXL pixel pipeline companion)
Copy-RepoRootSkill 'Gamezxz/pixel-art-studio' 'pixel-art-studio'

# provenance + license attribution (redistribution hygiene)
$prov = Join-Path $SkillsDir 'PROVENANCE.md'
$lines = @(
  '# Skills provenance (GitHub install wave - CEO order P-2026-09-28-15)',
  ('- installed: ' + (Get-Date -Format 'yyyy-MM-dd')),
  '- webapp-testing / mcp-builder / canvas-design / algorithmic-art / frontend-design: source https://github.com/anthropics/skills (Apache-2.0)',
  '- verification-before-completion / systematic-debugging / test-driven-development / dispatching-parallel-agents: source https://github.com/obra/superpowers (MIT, root LICENSE)',
  '- unity-* x8 / create-game-assets / shader-programming / procedural-gen / game-ai / level-design / game-ui-ux: source https://github.com/gamedev-skills/awesome-gamedev-agent-skills (Apache-2.0)',
  '- backtest-expert / trade-hypothesis-ideator / signal-postmortem / data-quality-checker / drawdown-circuit-breaker / position-sizer: source https://github.com/tradermonty/claude-trading-skills (MIT)',
  '- avoid-ai-writing / ai-writing-detector / voice-preserving-rewriter: source https://github.com/conorbronsdon/avoid-ai-writing (MIT)',
  '- pixel-art-studio: source https://github.com/Gamezxz/pixel-art-studio (MIT)',
  '- Note: anthropics docx/pdf/pptx/xlsx + others were pre-installed by a parallel window (local reference use only; source-available terms - no redistribution, never commit into company repos).',
  '- Update: re-run Tools/install-gh-skills.ps1 (idempotent; delete a skill folder to force refresh).'
)
Set-Content -Path $prov -Value $lines -Encoding UTF8
Write-Output 'PROVENANCE_WRITTEN'
$n = (Get-ChildItem $SkillsDir -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }).Count
Write-Output ("SKILL_DIRS_WITH_SKILLMD=" + $n)
Write-Output 'SKILLS_INSTALL_DONE'
