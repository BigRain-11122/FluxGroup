# lora_chain_guard.ps1 - LoRA 训练链保活护栏（静默、幂等、单实例）
# 为什么要有它：训练与队列原先是我会话里的子进程，会话一关就被 Job Object 连坐杀掉，
# 而报表上仍写着 running。护栏每 10 分钟看一眼：队列不在就拉起来，队列在就什么都不做。
# 零窗口：用 pythonw.exe（GUI 子系统，压根不分配控制台），不靠 -WindowStyle 隐藏赌运气。
$ErrorActionPreference = 'Stop'
$FG   = 'C:\Users\sjs20\Desktop\FluxGroup'
$H    = 'D:\FluxGroup-Offload\15-training'
$LOG  = Join-Path $H ('logs\guard-' + (Get-Date -Format 'yyyyMMdd') + '.log')
$OUT  = Join-Path $H 'logs\queue-stdout.log'
$ERR  = Join-Path $H 'logs\queue-stderr.log'
New-Item -ItemType Directory -Force -Path (Split-Path $LOG) | Out-Null

function Say($m) {
  Add-Content -Path $LOG -Value ("[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $m) -Encoding UTF8
}

# 单实例：同一秒内被重复触发时，只有拿到命名互斥的那个往下走
$mtx = New-Object System.Threading.Mutex($false, 'Global\FluxGroupLoraChainGuard')
if (-not $mtx.WaitOne(0)) { exit 0 }
try {
  $py  = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314\python.exe'
  $pyw = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314\pythonw.exe'
  if (-not (Test-Path $pyw)) { $pyw = $py }

  $procs = @(Get-CimInstance Win32_Process -Filter "Name='python.exe' or Name='pythonw.exe'" -ErrorAction SilentlyContinue)
  $queue  = @($procs | Where-Object { $_.CommandLine -match 'lora_queue\.py' })
  $train  = @($procs | Where-Object { $_.CommandLine -match 'lora_pipeline\.py\s+train' })

  if ($queue.Count -gt 0) {
    Say ("ok 队列在跑 pid={0} 训练进程={1} 个" -f $queue[0].ProcessId, $train.Count)
    exit 0
  }

  # 队列不在：读队列看还有没有活
  $q = Get-Content (Join-Path $FG 'cph4\fleet\mv-lora\LORA-TRAIN-QUEUE-v1.json') -Raw -Encoding UTF8 | ConvertFrom-Json
  $open = @($q.jobs | Where-Object { $_.status -notin @('done','trained') })
  if ($open.Count -eq 0) { Say 'idle 队列已全部收口，不拉起'; exit 0 }

  Say ("拉起队列（待办 {0} 条：{1}）" -f $open.Count, (($open | ForEach-Object { $_.id }) -join ','))
  Start-Process -FilePath $pyw `
    -ArgumentList @('-u', (Join-Path $FG 'Tools\lora_queue.py')) `
    -WorkingDirectory $FG `
    -RedirectStandardOutput $OUT -RedirectStandardError $ERR `
    -WindowStyle Hidden | Out-Null
  Start-Sleep -Seconds 6
  $now = @(Get-CimInstance Win32_Process -Filter "Name='python.exe' or Name='pythonw.exe'" -ErrorAction SilentlyContinue |
           Where-Object { $_.CommandLine -match 'lora_queue\.py' })
  if ($now.Count -gt 0) { Say ("started 队列 pid={0}" -f $now[0].ProcessId) }
  else { Say 'FAILED 队列没起来，看 queue-stderr.log' }
}
catch {
  Say ("EXC " + $_.Exception.Message)
}
finally {
  $mtx.ReleaseMutex()
  $mtx.Dispose()
}