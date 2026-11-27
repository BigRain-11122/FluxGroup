# clock-probe-nats.ps1 - measure clock offset against the fleet hub over NATS.
# Raw TCP, one connection for all samples: no subprocess per request.
# NTP formula with the hub timestamp taken at receive time: offset = hub - (t1+t4)/2.
# Accuracy = network asymmetry (~RTT/2). Same-machine calibration must read ~0ms;
# over the Tailscale relay the physical floor is ~RTT/2 (100-130ms at 200-260ms RTT).
param(
    [string]$Hub = '100.110.185.62',
    [int]$Port = 4222,
    [int]$Samples = 5,
    [string]$OutFile = ''
)
$ErrorActionPreference = 'Continue'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not $OutFile) { $OutFile = Join-Path $root 'Tools\nats\data\clock-offset.json' }
$dir = Split-Path $OutFile -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }

function Read-Line([System.IO.Stream]$s) {
    $sb = New-Object System.Text.StringBuilder
    while ($true) {
        $b = $s.ReadByte()
        if ($b -lt 0) { return $null }
        if ($b -eq 13) { $null = $s.ReadByte(); return $sb.ToString() }
        [void]$sb.Append([char]$b)
    }
}
function Read-Exact([System.IO.Stream]$s, [int]$n) {
    $buf = New-Object byte[] $n
    $off = 0
    while ($off -lt $n) {
        $r = $s.Read($buf, $off, $n - $off)
        if ($r -le 0) { return $null }
        $off += $r
    }
    return $buf
}
function Send-Ascii([System.IO.Stream]$s, [string]$text) {
    $b = [System.Text.Encoding]::ASCII.GetBytes($text)
    $s.Write($b, 0, $b.Length)
    $s.Flush()
}

$probes = @()
$client = $null
try {
    $client = New-Object System.Net.Sockets.TcpClient
    $client.NoDelay = $true
    $client.Connect($Hub, $Port)
    $ns = $client.GetStream()
    $null = Read-Line $ns
    $inbox = '_INBOX.CLOCK.' + [Guid]::NewGuid().ToString('N')
    Send-Ascii $ns ("CONNECT {`"verbose`":false}`r`n")
    Send-Ascii $ns ("SUB $inbox 1`r`n")

    for ($i = 0; $i -lt $Samples; $i++) {
        $body = [System.Text.Encoding]::ASCII.GetBytes('x')
        $t1 = [DateTime]::UtcNow.Ticks
        Send-Ascii $ns ("PUB clock.ask $inbox $($body.Length)`r`n")
        $ns.Write($body, 0, $body.Length)
        $ns.WriteByte(13); $ns.WriteByte(10); $ns.Flush()
        $got = $false
        while (-not $got) {
            $line = Read-Line $ns
            if (-not $line) { break }
            if ($line -eq 'PING') { Send-Ascii $ns "PONG`r`n"; continue }
            if ($line -match ('^MSG\s+' + [regex]::Escape($inbox) + '\s+\d+\s+(\d+)$')) {
                $n = [int]$Matches[1]
                $buf = Read-Exact $ns $n
                $null = Read-Exact $ns 2
                $t4 = [DateTime]::UtcNow.Ticks
                $txt = [System.Text.Encoding]::ASCII.GetString($buf).Trim()
                if ($txt -match '^\d{15,}$') {
                    $hubTicks = [int64]$txt
                    $probes += [pscustomobject]@{
                        offset_ms = (($hubTicks - (($t1 + $t4) / 2.0)) / 10000.0)
                        rtt_ms = (($t4 - $t1) / 10000.0)
                    }
                }
                $got = $true
            }
        }
    }
} catch {
} finally {
    if ($client) { try { $client.Close() } catch { } }
}
if ($probes.Count -eq 0) {
    $res = [ordered]@{ ts = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss.fff'); hub = $Hub; ok = $false; offset_ms = $null; rtt_ms = $null; samples = 0; error = 'hub-unreachable' }
    ($res | ConvertTo-Json -Compress) | Set-Content -Path $OutFile -Encoding UTF8
    Write-Output 'CLOCK-PROBE FAIL hub-unreachable'
    exit 1
}
$sorted = @($probes | Sort-Object offset_ms)
$median = $sorted[[int]($sorted.Count / 2)]
$bestRtt = ($probes | Sort-Object rtt_ms | Select-Object -First 1)
$res = [ordered]@{
    ts = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss.fff')
    hub = $Hub; ok = $true
    offset_ms = [math]::Round($median.offset_ms, 1)
    rtt_ms = [math]::Round($median.rtt_ms, 1)
    best_rtt_ms = [math]::Round($bestRtt.rtt_ms, 1)
    precision_ms = [math]::Round(($median.rtt_ms / 2.0), 1)
    samples = $probes.Count
}
($res | ConvertTo-Json -Compress) | Set-Content -Path $OutFile -Encoding UTF8
Write-Output ('CLOCK-PROBE ok offset_ms=' + $res.offset_ms + ' rtt_ms=' + $res.rtt_ms + ' precision_ms=' + $res.precision_ms)