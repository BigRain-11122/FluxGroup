# Resident sprite samples (CEO order 2026-09-24 ~20:10) - design language v0
# ASCII-only body per encoding law. Logical 16x16 grid, x2 -> 32x32 HD pixel (P-17).
# NOTE: draw funcs named Px/PxA - 'R' collides with the built-in alias r=Invoke-History.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$out = 'C:\Users\sjs20\Desktop\FluxGroup\cph4\research\sprites-20260924'
New-Item -ItemType Directory -Path $out -Force | Out-Null

function New-PxGrid {
  $b = New-Object System.Drawing.Bitmap(32, 32)
  $g = [System.Drawing.Graphics]::FromImage($b)
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None
  return @{ bmp = $b; gfx = $g }
}
function Px {
  param($gr, [int]$x, [int]$y, [int]$w, [int]$h, [string]$hex)
  $c = [System.Drawing.ColorTranslator]::FromHtml($hex)
  $br = New-Object System.Drawing.SolidBrush($c)
  $gr.v.gfx.FillRectangle($br, $x * 2, $y * 2, $w * 2, $h * 2)
  $br.Dispose()
}
function PxA {
  param($gr, [int]$x, [int]$y, [int]$w, [int]$h, [int]$a, [string]$hex)
  $base = [System.Drawing.ColorTranslator]::FromHtml($hex)
  $c = [System.Drawing.Color]::FromArgb($a, $base.R, $base.G, $base.B)
  $br = New-Object System.Drawing.SolidBrush($c)
  $gr.v.gfx.FillRectangle($br, $x * 2, $y * 2, $w * 2, $h * 2)
  $br.Dispose()
}
function Save-PxGrid {
  param($gr, [string]$name)
  $gr.v.gfx.Dispose()
  $gr.v.bmp.Save((Join-Path $out $name), [System.Drawing.Imaging.ImageFormat]::Png)
  Write-Output ("SAVED " + $name)
}

# --- 1. native-carbon: warm LED eyes + life-warm clothing (AA-016.04 vibe) ---
$g1 = @{ v = (New-PxGrid) }
Px $g1 4 1 8 6 '#E6B184'
Px $g1 4 1 8 2 '#6B4A32'
Px $g1 3 2 1 2 '#6B4A32'; Px $g1 12 2 1 2 '#6B4A32'
Px $g1 5 3 2 2 '#FFD27A'; Px $g1 9 3 2 2 '#FFD27A'   # amber LED square eyes
Px $g1 6 5 4 1 '#C98F63'
Px $g1 4 7 8 5 '#B0552F'
Px $g1 6 8 4 3 '#C96A3F'
Px $g1 4 11 8 1 '#8A3F22'
Px $g1 3 7 1 4 '#E6B184'; Px $g1 12 7 1 4 '#E6B184'
Px $g1 5 12 2 3 '#4A3828'; Px $g1 9 12 2 3 '#4A3828'
Px $g1 5 15 2 1 '#2E2419'; Px $g1 9 15 2 1 '#2E2419'
Save-PxGrid $g1 'sample-native-carbon.png'

# --- 2. native-silicon: cyan LED eyes + cool machine-room palette + circuit px ---
$g2 = @{ v = (New-PxGrid) }
Px $g2 4 1 8 6 '#D8C8B0'
Px $g2 4 1 8 2 '#55627A'
Px $g2 3 2 1 2 '#55627A'; Px $g2 12 2 1 2 '#55627A'
Px $g2 5 3 2 2 '#40F0E0'; Px $g2 9 3 2 2 '#40F0E0'   # cyan LED square eyes
Px $g2 6 5 4 1 '#B4A48E'
Px $g2 4 7 8 5 '#5A7089'
Px $g2 4 11 8 1 '#46586E'
Px $g2 6 8 1 1 '#40F0E0'; Px $g2 7 9 2 1 '#40F0E0'; Px $g2 6 10 1 1 '#40F0E0'  # circuit traces
Px $g2 3 7 1 4 '#D8C8B0'; Px $g2 12 7 1 4 '#D8C8B0'
Px $g2 5 12 2 3 '#3D4A5C'; Px $g2 9 12 2 3 '#3D4A5C'
Px $g2 5 15 2 1 '#2A3442'; Px $g2 9 15 2 1 '#2A3442'
Save-PxGrid $g2 'sample-native-silicon.png'

# --- 3. pixel-sprite: tiny translucent glow being (no human rig) ---
$g3 = @{ v = (New-PxGrid) }
PxA $g3 4 3 8 8 70 '#A78BFA'
PxA $g3 5 4 6 6 120 '#5EEAD4'
PxA $g3 6 5 4 4 200 '#5EEAD4'
PxA $g3 5 6 6 3 220 '#5EEAD4'
Px $g3 7 6 2 2 '#E9D5FF'
Px $g3 6 6 1 1 '#F5EFFF'; Px $g3 9 6 1 1 '#F5EFFF'
Px $g3 7 9 2 1 '#C7F9EF'
Px $g3 5 13 1 1 '#A78BFA'; Px $g3 10 12 1 1 '#5EEAD4'; Px $g3 12 9 1 1 '#A78BFA'
Save-PxGrid $g3 'sample-pixel-sprite.png'

# --- 4. user-avatar: realistic dot eyes (no LED) + white halo ring (human-host mark) ---
$g4 = @{ v = (New-PxGrid) }
Px $g4 5 0 6 1 '#F2F6FF'
Px $g4 3 1 1 6 '#F2F6FF'; Px $g4 12 1 1 6 '#F2F6FF'
Px $g4 5 7 6 1 '#F2F6FF'
Px $g4 4 1 8 6 '#E6B184'
Px $g4 4 1 8 2 '#2E2A26'
Px $g4 3 2 1 2 '#2E2A26'; Px $g4 12 2 1 2 '#2E2A26'
Px $g4 6 3 1 1 '#1A1A22'; Px $g4 9 3 1 1 '#1A1A22'   # realistic dark dot eyes
Px $g4 6 5 4 1 '#C98F63'
Px $g4 4 7 8 5 '#3D8F86'
Px $g4 6 8 4 3 '#2E6B64'
Px $g4 4 11 8 1 '#256059'
Px $g4 3 7 1 4 '#E6B184'; Px $g4 12 7 1 4 '#E6B184'
Px $g4 5 12 2 3 '#35506E'; Px $g4 9 12 2 3 '#35506E'
Px $g4 5 15 2 1 '#222A38'; Px $g4 9 15 2 1 '#222A38'
Save-PxGrid $g4 'sample-user-avatar.png'

# --- 5. ceo-jason: tall pure-white robe + lucy-blue rim glow (sole glow privilege) ---
$g5 = @{ v = (New-PxGrid) }
PxA $g5 2 0 12 15 60 '#60A5FA'
PxA $g5 3 1 10 13 90 '#60A5FA'
Px $g5 5 0 6 3 '#F2F6FF'
Px $g5 7 1 1 1 '#2A3444'; Px $g5 9 1 1 1 '#2A3444'   # realistic dark dot eyes (human-host signal)
Px $g5 4 4 8 8 '#F2F6FF'
Px $g5 10 4 2 8 '#D6E0F2'
Px $g5 5 8 6 1 '#C9D6EE'
Px $g5 3 4 1 6 '#F2F6FF'; Px $g5 12 4 1 6 '#F2F6FF'
Px $g5 5 12 2 2 '#D6E0F2'; Px $g5 9 12 2 2 '#D6E0F2'
Px $g5 7 4 2 8 '#FFFFFF'
Save-PxGrid $g5 'sample-ceo-jason.png'

# --- montage: 5 cells x6 nearest-neighbor on dark bg ---
$cell = 192; $pad = 16
$names = @('sample-native-carbon.png', 'sample-native-silicon.png', 'sample-pixel-sprite.png', 'sample-user-avatar.png', 'sample-ceo-jason.png')
$mw = ($cell + $pad) * 5 + $pad
$mh = $cell + 2 * $pad
$m = New-Object System.Drawing.Bitmap($mw, $mh)
$mg = [System.Drawing.Graphics]::FromImage($m)
$mg.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None
$mg.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
$mg.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Half
$bgc = [System.Drawing.ColorTranslator]::FromHtml('#060A13')
$bbr = New-Object System.Drawing.SolidBrush($bgc)
$mg.FillRectangle($bbr, 0, 0, $m.Width, $m.Height)
for ($i = 0; $i -lt 5; $i++) {
  $sb = New-Object System.Drawing.Bitmap((Join-Path $out $names[$i]))
  $mg.DrawImage($sb, $pad + $i * ($cell + $pad), $pad, $cell, $cell)
  $sb.Dispose()
}
$mg.Dispose()
$m.Save((Join-Path $out 'montage-samples.png'), [System.Drawing.Imaging.ImageFormat]::Png)
Write-Output 'SAVED montage-samples.png'
