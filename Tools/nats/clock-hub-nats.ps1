# clock-hub-nats.ps1 - fleet time reference over the existing NATS bus (no new port,
# no firewall change). Subscribes to "clock.ask" and answers with hub UTC ticks the
# microsecond it receives the request. Raw TCP client = no subprocess per request,
# which is what made the first nats-cli version biased by ~100ms.
param(
    [string]$Server = '127.0.0.1',
    [int]$Port = 4222,
    [string]$Subject = 'clock.ask'
)
$ErrorActionPreference = 'Continue'

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

while ($true) {
    $client = $null
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $client.NoDelay = $true
        $client.Connect($Server, $Port)
        $ns = $client.GetStream()
        $null = Read-Line $ns
        Send-Ascii $ns ("CONNECT {`"verbose`":false}`r`n")
        Send-Ascii $ns ("SUB $Subject 1`r`n")
        while ($true) {
            $line = Read-Line $ns
            if (-not $line) { break }
            if ($line -eq 'PING') { Send-Ascii $ns "PONG`r`n"; continue }
            if ($line -match ('^MSG\s+' + [regex]::Escape($Subject) + '\s+\d+\s+(\S+)\s+(\d+)$')) {
                $reply = $Matches[1]
                $n = [int]$Matches[2]
                $null = Read-Exact $ns $n
                $null = Read-Exact $ns 2
                $ticks = [DateTime]::UtcNow.Ticks
                $p = [System.Text.Encoding]::ASCII.GetBytes($ticks.ToString())
                Send-Ascii $ns ("PUB $reply $($p.Length)`r`n")
                $ns.Write($p, 0, $p.Length)
                $ns.WriteByte(13); $ns.WriteByte(10); $ns.Flush()
            }
        }
    } catch {
        Start-Sleep -Seconds 1
    } finally {
        if ($client) { try { $client.Close() } catch { } }
    }
    Start-Sleep -Seconds 1
}