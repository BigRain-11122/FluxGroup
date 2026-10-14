# coder-serve.ps1 - bm-a resident 35B coder LLM server (CEO order 2026-10-14: resident coding model, latest, 12G-fit, save cloud tokens)
# Idempotent watchdog+launcher: scheduled task bm-a-CoderServe runs this every 10m.
#   - pause-flag respect (CEO machine-let law: machine-state pause kills llama-server; flag blocks revival)
#   - port-alive guard: no double-start
#   - BelowNormal priority: yields to CEO foreground always (CEO 10% CPU reserve law)
#   - logs in safe zone media/logs (night-sweep-proof)
$ErrorActionPreference = 'Continue'
$root  = 'C:\Users\sjs20\Desktop\FluxGroup'
$flag  = Join-Path $root '.codely-cli\engine-tick\keepwarm.pause'
if (Test-Path $flag) { exit 0 }   # CEO pause window - do not revive
try { $null = Invoke-RestMethod -Uri 'http://127.0.0.1:8090/health' -TimeoutSec 3; exit 0 } catch { }

$model = 'C:\Users\sjs20\models\qwen36-35b\Qwen3.6-35B-A3B-UD-IQ4_XS.gguf'
$exe   = 'C:\Users\sjs20\models\llamacpp-b11429\llama-server.exe'
if (-not (Test-Path $model)) { exit 0 }
if (-not (Test-Path $exe))   { exit 0 }

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$logDir = Join-Path $root 'media\logs'
$null = New-Item -ItemType Directory -Force -Path $logDir
$outLog = Join-Path $logDir ("coder-serve-$stamp.out.log")
$errLog  = Join-Path $logDir ("coder-serve-$stamp.err.log")

$argList = '-m "{0}" --n-cpu-moe 999 -ngl 999 -c 16384 -np 2 --host 0.0.0.0 --port 8090 --jinja -t 24 -fa auto --no-webui' -f $model
$p = Start-Process -FilePath $exe -ArgumentList $argList -WindowStyle Hidden `
     -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru
try { $p.PriorityClass = 'BelowNormal' } catch { }   # PS5.1: no -Priority param, set post-launch
"launched pid=$($p.Id) at $(Get-Date -Format 'HH:mm:ss')" | Add-Content (Join-Path $logDir 'coder-serve-launch.log')
exit 0
