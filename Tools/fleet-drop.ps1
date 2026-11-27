# fleet-drop.ps1 - Fleet file drop over Tailscale (Taildrop) v1.0
# Why (2026-11-27 audit): all three nodes are relayed through DERP (bm-a is on a
# CGNAT with a Singapore egress, bm-b/bm-c are homed to sfo). Measured single
# stream: ~8-20 KB/s. FleetLink :8790 listeners are dead on the peers, so
# Taildrop (the Tailscale peer API) is the only channel that works with zero
# peer-side software. This wrapper makes it one command, compresses text,
# splits big files into parallel parts, and verifies + reassembles on receive.
#
# Sender : powershell -NoProfile -File Tools\fleet-drop.ps1 -Send D:\x.zip -To bm-b
# Receiver: powershell -NoProfile -File Tools\fleet-drop.ps1 -Pick
# Status : powershell -NoProfile -File Tools\fleet-drop.ps1 -Status
# Selftest: powershell -NoProfile -File Tools\fleet-drop.ps1 -SelfTest
#
# Rules: ASCII-only body (encoding law); PS 5.1 safe; no child consoles
# (runspaces, not Start-Job); never overwrite an existing file without -Force.
param(
  [string[]]$Send = @(),
  [string]$To = '',
  [switch]$Pick,
  [string]$Inbox = '',
  [string]$Out = '',
  [string]$StageDir = '',
  [int]$ChunkMB = 4,
  [int]$Parallel = 4,
  [switch]$Compress,
  [switch]$NoSplit,
  [switch]$Force,
  [switch]$Status,
  [switch]$SelfTest
)

# Native commands (tailscale.exe) write progress/errors to stderr; Stop would
# turn that into a terminating error and abort the transfer. Handle rc explicitly.
$ErrorActionPreference = 'Continue'

$Ts = @("C:\Program Files\Tailscale\tailscale.exe", "C:\Program Files (x86)\Tailscale\tailscale.exe") |
  Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $Ts) { throw 'tailscale.exe not found' }

$CompressExt = @('.md', '.txt', '.json', '.jsonl', '.log', '.csv', '.xml', '.yml', '.yaml',
  '.ps1', '.py', '.js', '.ts', '.tsx', '.html', '.css', '.sql', '.ini', '.cfg')

function Get-Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }

function Test-Compressible([string]$name, [long]$size) {
  if ($size -le 65536) { return $false }
  $e = [IO.Path]::GetExtension($name).ToLower()
  return ($CompressExt -contains $e)
}

function Compress-Gz([string]$src, [string]$dst) {
  $i = [IO.File]::OpenRead($src)
  $o = [IO.File]::Create($dst)
  $g = New-Object IO.Compression.GZipStream($o, [IO.Compression.CompressionLevel]::Optimal)
  try { $i.CopyTo($g) } finally { $g.Dispose(); $o.Dispose(); $i.Dispose() }
}

function Expand-Gz([string]$src, [string]$dst) {
  $i = [IO.File]::OpenRead($src)
  $g = New-Object IO.Compression.GZipStream($i, [IO.Compression.CompressionMode]::Decompress)
  $o = [IO.File]::Create($dst)
  try { $g.CopyTo($o) } finally { $o.Dispose(); $g.Dispose(); $i.Dispose() }
}

function Invoke-TsCp([string]$file, [string]$target) {
  $o = & $Ts file cp $file $target 2>&1
  $rc = $LASTEXITCODE
  $txt = (@($o) | ForEach-Object { $_.ToString() }) -join "`n"
  return [pscustomobject]@{ rc = $rc; out = $txt.Trim() }
}

function Get-PartName([string]$stem, [string]$tag, [int]$i, [int]$n) {
  return ('{0}.{1}.fdpart{2:D4}of{3:D4}' -f $stem, $tag, $i, $n)
}

function Split-File([string]$src, [string]$dir, [long]$chunkBytes, [string]$stem, [string]$tag) {
  $total = (Get-Item -LiteralPath $src).Length
  $n = [int][Math]::Ceiling($total / [double]$chunkBytes)
  if ($n -lt 1) { $n = 1 }
  $parts = @()
  $in = [IO.File]::OpenRead($src)
  $buf = New-Object byte[] 1048576
  try {
    for ($i = 1; $i -le $n; $i++) {
      $name = Get-PartName $stem $tag $i $n
      $path = Join-Path $dir $name
      $remain = [long][Math]::Min($chunkBytes, $total - ([long]($i - 1) * $chunkBytes))
      $fs = [IO.File]::Create($path)
      try {
        while ($remain -gt 0) {
          $want = [int][Math]::Min([long]$buf.Length, $remain)
          $read = $in.Read($buf, 0, $want)
          if ($read -le 0) { break }
          $fs.Write($buf, 0, $read)
          $remain -= $read
        }
      } finally { $fs.Dispose() }
      $parts += [pscustomobject]@{
        i = $i; name = $name; path = $path
        size = (Get-Item -LiteralPath $path).Length
        sha256 = (Get-Sha $path)
      }
    }
  } finally { $in.Dispose() }
  return $parts
}

function Join-Parts([object[]]$chunks, [string]$dir, [string]$dst) {
  $out = [IO.File]::Create($dst)
  try {
    foreach ($c in ($chunks | Sort-Object { [int]$_.i })) {
      $p = Join-Path $dir ([string]$c.name)
      if (-not (Test-Path -LiteralPath $p)) { throw ('missing part: ' + $c.name) }
      $in = [IO.File]::OpenRead($p)
      try { $in.CopyTo($out) } finally { $in.Dispose() }
    }
  } finally { $out.Dispose() }
}

function Send-Parallel([object[]]$paths, [string]$target, [int]$maxParallel) {
  $limit = [Math]::Max(1, $maxParallel)
  $pool = [runspacefactory]::CreateRunspacePool(1, $limit)
  $pool.Open()
  $script = 'param($ts,$file,$target) $sw=[Diagnostics.Stopwatch]::StartNew(); $o = & $ts file cp $file $target 2>&1; [pscustomobject]@{ file=$file; rc=$LASTEXITCODE; ms=$sw.ElapsedMilliseconds; out=(($o | Out-String).Trim()) }'
  $runs = @()
  foreach ($p in $paths) {
    $ps = [powershell]::Create()
    $ps.RunspacePool = $pool
    $null = $ps.AddScript($script)
    $null = $ps.AddArgument($Ts)
    $null = $ps.AddArgument($p)
    $null = $ps.AddArgument($target)
    $runs += [pscustomobject]@{ ps = $ps; h = $ps.BeginInvoke() }
  }
  $res = @()
  foreach ($r in $runs) {
    foreach ($x in $r.ps.EndInvoke($r.h)) { $res += $x }
    $r.ps.Dispose()
  }
  $pool.Close()
  return $res
}

function Get-DefaultInbox {
  $root = Split-Path -Parent $PSScriptRoot
  return (Join-Path $root 'fleet-inbox')
}

function Show-Status {
  $s = & $Ts status --json | ConvertFrom-Json
  $selfDns = ([string]$s.Self.DNSName).TrimEnd('.')
  'self=' + $s.Self.HostName + ' dns=' + $selfDns + ' ip=' + ((@($s.Self.TailscaleIPs) | Where-Object { $_ -notmatch ':' }) -join ',') + ' online=' + $s.Self.Online
  $names = @{}
  foreach ($pp in $s.Peer.PSObject.Properties) {
    $p = $pp.Value
    if ($p.HostName -notlike 'bm-*') { continue }
    $dns = ([string]$p.DNSName).TrimEnd('.')
    if ($dns -eq '') { $dns = [string]$p.HostName }
    $ip = @($p.TailscaleIPs) | Where-Object { $_ -notmatch ':' } | Select-Object -First 1
    $k = [string]$p.HostName
    if (-not $names.ContainsKey($k)) { $names[$k] = 0 }
    $names[$k] = $names[$k] + 1
    $path = 'relay ' + [string]$p.Relay
    if ($p.CurAddr) { $path = 'direct ' + [string]$p.CurAddr }
    $state = 'offline'; if ($p.Online) { $state = 'online' }
    ('{0,-24} {1,-16} {2,-8} {3}' -f $dns, $ip, $state, $path)
  }
  foreach ($k in @($names.Keys)) {
    if ($names[$k] -gt 1) { 'WARN duplicate hostname "' + $k + '" x' + $names[$k] + ' -> use dns name or ip' }
  }
}

# Resolve a -To argument to exactly one device. Short host names are NOT unique
# (two devices named bm-m), so ambiguity is an error instead of a guess.
function Resolve-Target([string]$to) {
  $q = $to.Trim()
  if ($q.EndsWith(':')) { $q = $q.Substring(0, $q.Length - 1) }
  if ($q -eq '') { throw '-To is empty' }
  $s = & $Ts status --json | ConvertFrom-Json
  $hits = @()
  foreach ($pp in $s.Peer.PSObject.Properties) {
    $p = $pp.Value
    $dns = ([string]$p.DNSName).TrimEnd('.')
    $ips = @($p.TailscaleIPs) | Where-Object { $_ -notmatch ':' }
    $isHit = $false
    if ($ips -contains $q) { $isHit = $true }
    if ($dns -ne '' -and $dns -ieq $q) { $isHit = $true }
    if ($dns -ne '' -and $dns.Split('.')[0] -ieq $q) { $isHit = $true }
    if ([string]$p.HostName -ieq $q) { $isHit = $true }
    if ($isHit) {
      $hits += [pscustomobject]@{ host = [string]$p.HostName; dns = $dns; ip = [string](@($ips)[0]); online = [bool]$p.Online }
    }
  }
  $selfIps = @($s.Self.TailscaleIPs) | Where-Object { $_ -notmatch ':' }
  $selfDns = ([string]$s.Self.DNSName).TrimEnd('.')
  if (($selfIps -contains $q) -or ($selfDns -ne '' -and $selfDns -ieq $q) -or ($selfDns -ne '' -and $selfDns.Split('.')[0] -ieq $q) -or ([string]$s.Self.HostName -ieq $q)) {
    $hits += [pscustomobject]@{ host = [string]$s.Self.HostName; dns = $selfDns; ip = [string](@($selfIps)[0]); online = $true }
  }
  if ($hits.Count -eq 0) { throw ('target not found in tailnet: ' + $q) }
  if ($hits.Count -gt 1) {
    $list = (@($hits) | ForEach-Object { $_.dns + '(' + $_.ip + ',online=' + $_.online + ')' }) -join ', '
    throw ('ambiguous target "' + $q + '": ' + $list + ' -> use the dns name or ip')
  }
  return $hits[0]
}

if ($Status) { Show-Status; return }

if ($SelfTest) {
  $t = Join-Path $env:TEMP ('fleet-drop-selftest-' + [Guid]::NewGuid().ToString('N').Substring(0, 8))
  New-Item -ItemType Directory -Force -Path $t | Out-Null
  $fail = 0
  try {
    $src = Join-Path $t 'src.bin'
    $bytes = New-Object byte[] (9 * 1024 * 1024 + 12345)
    (New-Object Random 7).NextBytes($bytes)
    [IO.File]::WriteAllBytes($src, $bytes)
    $sha = Get-Sha $src
    $parts = Split-File $src $t 4194304 'src' 'deadbeef'
    $dst = Join-Path $t 'dst.bin'
    Join-Parts $parts $t $dst
    $ok1 = ((Get-Sha $dst) -eq $sha)
    $s1 = 'FAIL'; if ($ok1) { $s1 = 'PASS' }
    'selftest split/join: ' + $s1
    if (-not $ok1) { $fail++ }

    $txt = Join-Path $t 'note.md'
    [IO.File]::WriteAllText($txt, ('fleet-drop selftest ' * 200000), (New-Object System.Text.UTF8Encoding($false)))
    $gz = Join-Path $t 'note.md.gz'
    Compress-Gz $txt $gz
    $back = Join-Path $t 'note.back.md'
    Expand-Gz $gz $back
    $ok2 = ((Get-Sha $back) -eq (Get-Sha $txt))
    $s2 = 'FAIL'; if ($ok2) { $s2 = 'PASS' }
    'selftest gzip roundtrip: ' + $s2
    if (-not $ok2) { $fail++ }

    if ($fail -eq 0) { 'SELFTEST PASS' } else { 'SELFTEST FAIL' }
  } finally {
    Remove-Item -LiteralPath $t -Recurse -Force -ErrorAction SilentlyContinue
  }
  if ($fail -ne 0) { exit 1 }
  return
}

if ($Pick) {
  $dir = if ($Inbox -ne '') { $Inbox } else { Get-DefaultInbox }
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $before = @(Get-ChildItem -LiteralPath $dir -File | ForEach-Object { $_.Name })
  $o = & $Ts file get --conflict=rename $dir 2>&1
  $rc = $LASTEXITCODE
  if ($rc -ne 0) { throw ('tailscale file get failed: ' + (($o | Out-String).Trim())) }
  $mans = @(Get-ChildItem -LiteralPath $dir -Filter '*.fleetdrop.json' -File)
  if ($mans.Count -eq 0) { 'no fleet-drop manifest in ' + $dir; return }

  $outDir = if ($Out -ne '') { $Out } else { $dir }
  New-Item -ItemType Directory -Force -Path $outDir | Out-Null
  foreach ($m in $mans) {
    $man = Get-Content -Raw -Encoding UTF8 -LiteralPath $m.FullName | ConvertFrom-Json
    $name = [string]$man.name
    $wireName = [string]$man.wire_name
    $dst = Join-Path $outDir $name
    if ((Test-Path -LiteralPath $dst) -and (-not $Force)) {
      $dst = Join-Path $outDir ($name + '.new')
    }
    $bad = 0
    foreach ($c in @($man.chunks)) {
      $p = Join-Path $dir ([string]$c.name)
      if (-not (Test-Path -LiteralPath $p)) { 'MISSING ' + $c.name; $bad++; continue }
      if ((Get-Item -LiteralPath $p).Length -ne [long]$c.size) { 'SIZE-BAD ' + $c.name; $bad++; continue }
      if ((Get-Sha $p) -ne [string]$c.sha256) { 'HASH-BAD ' + $c.name; $bad++ }
    }
    if ($bad -gt 0) { 'SKIP ' + $name + ' (' + $bad + ' bad parts, files kept)'; continue }

    $tmpJoined = Join-Path $dir ('~join-' + [Guid]::NewGuid().ToString('N').Substring(0, 8))
    Join-Parts @($man.chunks) $dir $tmpJoined
    $wireSha = Get-Sha $tmpJoined
    if ($wireSha -ne [string]$man.wire_sha256) {
      'SKIP ' + $name + ' (wire sha mismatch, files kept)'
      Remove-Item -LiteralPath $tmpJoined -Force -ErrorAction SilentlyContinue
      continue
    }
    if ([bool]$man.compressed) {
      Expand-Gz $tmpJoined $dst
      Remove-Item -LiteralPath $tmpJoined -Force -ErrorAction SilentlyContinue
      if ((Get-Sha $dst) -ne [string]$man.sha256) {
        'SKIP ' + $name + ' (final sha mismatch)'
        continue
      }
    } else {
      Move-Item -LiteralPath $tmpJoined -Destination $dst -Force
    }
    foreach ($c in @($man.chunks)) {
      Remove-Item -LiteralPath (Join-Path $dir ([string]$c.name)) -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $m.FullName -Force -ErrorAction SilentlyContinue
    'OK ' + $name + ' -> ' + $dst
  }
  return
}

if ($Send.Count -eq 0) {
  'usage: -Send <path[,path]> -To <node> | -Pick [-Inbox dir] | -Status | -SelfTest'
  return
}
if ($To -eq '') { throw '-To is required (node name, e.g. bm-b)' }

$resolved = Resolve-Target $To
if (-not $resolved.online) { 'WARN target is offline: ' + $resolved.dns + ' (' + $resolved.ip + ')' }
$targetName = $resolved.dns
if ($targetName -eq '') { $targetName = $resolved.ip }
$target = $targetName + ':'
'to=' + $targetName + ' (' + $resolved.ip + ')'
$tmp = Join-Path $env:TEMP ('fleet-drop-' + [Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$failures = 0
try {
  foreach ($f in $Send) {
    $src = (Resolve-Path -LiteralPath $f).Path
    $origName = Split-Path -Leaf $src
    $origSize = (Get-Item -LiteralPath $src).Length
    $origSha = Get-Sha $src
    $wire = $src
    $wireName = $origName
    $compressed = $false

    if (($Compress -or (Test-Compressible $origName $origSize))) {
      $gz = Join-Path $tmp ($origName + '.gz')
      Compress-Gz $src $gz
      if ((Get-Item -LiteralPath $gz).Length -lt $origSize) {
        $wire = $gz
        $wireName = $origName + '.gz'
        $compressed = $true
      }
    }

    $wireSize = (Get-Item -LiteralPath $wire).Length
    $wireSha = Get-Sha $wire
    $stem = [IO.Path]::GetFileNameWithoutExtension($wireName)
    $tag = $wireSha.Substring(0, 8)
    $chunkBytes = [long]$ChunkMB * 1MB

    if ((-not $NoSplit) -and ($wireSize -gt $chunkBytes)) {
      $parts = Split-File $wire $tmp $chunkBytes $stem $tag
      $manChunks = @($parts | ForEach-Object { [ordered]@{ i = $_.i; name = $_.name; size = $_.size; sha256 = $_.sha256 } })
      $man = [ordered]@{
        tool = 'fleet-drop'; v = 1; name = $origName; size = $origSize; sha256 = $origSha
        wire_name = $wireName; wire_size = $wireSize; wire_sha256 = $wireSha
        compressed = $compressed; chunks = $manChunks
      }
      $manName = $stem + '.' + $tag + '.fleetdrop.json'
      $manPath = Join-Path $tmp $manName
      [IO.File]::WriteAllText($manPath, ($man | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding($false)))

      if ($StageDir -ne '') {
        New-Item -ItemType Directory -Force -Path $StageDir | Out-Null
        Copy-Item -LiteralPath $manPath -Destination $StageDir -Force
        foreach ($pt in $parts) { Copy-Item -LiteralPath $pt.path -Destination (Join-Path $StageDir $pt.name) -Force }
        'STAGED ' + $origName + ' parts=' + $parts.Count + ' wire=' + $wireSize + 'B -> ' + $StageDir
        continue
      }

      $r0 = Invoke-TsCp $manPath $target
      if ($r0.rc -ne 0) { 'FAIL manifest ' + $origName + ': ' + $r0.out; $failures++; continue }

      $sw = [Diagnostics.Stopwatch]::StartNew()
      $res = Send-Parallel @($parts | ForEach-Object { $_.path }) $target $Parallel
      $sw.Stop()
      $bad = @($res | Where-Object { $_.rc -ne 0 })
      $sec = [Math]::Max(0.001, $sw.Elapsed.TotalSeconds)
      $rate = [Math]::Round(($wireSize / 1024.0) / $sec, 1)
      if ($bad.Count -gt 0) {
        'FAIL ' + $origName + ' parts rc!=0: ' + (($bad | ForEach-Object { $_.out }) -join ' | ')
        $failures++
      } else {
        ('OK {0} parts={1} wire={2:N1}MB {3:N1}s {4}KB/s -> {5}' -f $origName, $parts.Count, ($wireSize / 1MB), $sec, $rate, $targetName)
        if ($compressed) { '   compressed ' + $origSize + ' -> ' + $wireSize + ' bytes' }
      }
    } else {
      if ($StageDir -ne '') {
        New-Item -ItemType Directory -Force -Path $StageDir | Out-Null
        Copy-Item -LiteralPath $wire -Destination (Join-Path $StageDir $wireName) -Force
        'STAGED ' + $origName + ' single wire=' + $wireSize + 'B -> ' + $StageDir
        continue
      }
      $sw = [Diagnostics.Stopwatch]::StartNew()
      $r = Invoke-TsCp $wire $target
      $sw.Stop()
      $sec = [Math]::Max(0.001, $sw.Elapsed.TotalSeconds)
      $rate = [Math]::Round(($wireSize / 1024.0) / $sec, 1)
      if ($r.rc -ne 0) {
        'FAIL ' + $origName + ': ' + $r.out
        $failures++
      } else {
        ('OK {0} single {1:N1}MB {2:N1}s {3}KB/s -> {4}' -f $origName, ($wireSize / 1MB), $sec, $rate, $targetName)
        if ($compressed) { '   compressed ' + $origSize + ' -> ' + $wireSize + ' bytes' }
      }
    }
  }
} finally {
  Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}

if ($failures -gt 0) { exit 1 }
