# Keep the Ollama pause valve fresh while a GPU batch owns the card.
# Why: sentinel's stale-valve TTL (12h) + per-tick repin will reload the text
# model mid-batch and cut TTS speed ~15x (ledger P-13). The valve must stay young
# for the whole batch, not just be created once.
$ErrorActionPreference = 'SilentlyContinue'
$valve = 'C:\Fluxgroup\MiniGame\Tools\Ollama\keepwarm.pause'
$done  = 'C:\Fluxgroup\FluxGroup\media\drama-tools\voicegen_r1202_ep001_060.DONE.json'
$chain = 'C:\Fluxgroup\FluxGroup\media\drama-tools\chain_full.DONE.json'

if (Test-Path $chain) { exit 0 }              # chain finished -> stop touching
if (-not (Test-Path $done)) {
    New-Item -ItemType File -Force -Path $valve | Out-Null
    (Get-Item $valve).LastWriteTime = Get-Date
    Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force
}
exit 0