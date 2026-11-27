# bake-residents.ps1 - resident sprite generator v0 (P-68 batch 1.5, CEO order ~20:35)
# Reads BigLife census light export (read-only), deterministically derives a
# 32x32 HD-pixel sprite per resident per design language v0. Zero LLM.
# Species rules: carbon=amber LED eyes+warm wear; silicon=cyan LED+cool+circuit;
# sprite=glow blob. Human-host path reserved (dot eyes + white ring).
# ASCII-only body per encoding law. Output: r-*.png + manifest.json + contact-sheet.png
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$root = 'C:\Users\sjs20\Desktop\FluxGroup'
$out = Join-Path $root 'cph4\research\sprites-20260924\batch1'
New-Item -ItemType Directory -Path $out -Force | Out-Null

$CENSUS = Join-Path $root 'life\BigLife\census\export\citizens-light.jsonl'
$TAKE = 32

function HashInt {
  param([string]$s, [int]$mod)
  $sha = [System.Security.Cryptography.SHA256]::Create()
  $h = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($s))
  $v = [int]$h[0] + ([int]$h[1] -shl 8) + ([int]$h[2] -shl 16)
  if ($v -lt 0) { $v = -$v }
  return ($v % $mod)
}

$P_SKIN_C = @('#E6B184', '#D8A87A', '#C9986B', '#E8C098', '#DBAF85', '#C9A47E')
# v0.1: perceptually-distinct pools - hex-unique == eye-unique (combo dedupe law)
$P_HAIR_C = @('#2E2A26', '#6B4A32', '#8A4A32', '#C9A56A', '#5A5A5A', '#D8D8D0', '#6E5A80', '#3E7A72')
$P_CLOTH_C = @('#A83A3A', '#C07A2E', '#B3A23E', '#4E7A3E', '#3E7A72', '#3E6E9E', '#3A4E7E', '#7A4E9E', '#9E4E7E', '#8A5A3E', '#7A746A', '#5A6E4E')
$P_SKIN_S = @('#D8C8B0', '#CFC2AC', '#B8AC98')
$P_HAIR_S = @('#8A9AB8', '#2E6E6E', '#C8D4E8', '#3E4A5E', '#9E7EB8')
$P_CLOTH_S = @('#2E5E4E', '#3E8E8E', '#3E6E9E', '#2A3A5E', '#6E5E9E', '#9E5E8E', '#6A7484', '#8E7A4E', '#4E6E3E', '#5E8E5E', '#4E4E7E', '#7E4E5E')
$P_SPRITE = @('#5EEAD4', '#A78BFA', '#60A5FA', '#F472B6', '#4ADE80')
$P_BADGE = @('#FBBF24', '#5EEAD4', '#A78BFA', '#F472B6', '#4ADE80', '#60A5FA')

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

function Draw-Humanoid {
  param($gr, [string]$sp, [int]$gcode, [string]$skin, [string]$hair, [string]$cloth, [string]$eye, [string]$badge)
  $pant = '#3A3440'
  $cheek = '#C98F63'
  if ($sp -eq 'silicon') { $pant = '#3D4A5C'; $cheek = '#B4A48E' }
  Px $gr 4 1 8 6 $skin
  Px $gr 4 1 8 2 $hair
  Px $gr 3 2 1 2 $hair; Px $gr 12 2 1 2 $hair
  if ($gcode -eq 0) { Px $gr 3 2 1 7 $hair; Px $gr 12 2 1 7 $hair }  # long hair (F) to shoulders
  Px $gr 5 3 2 2 $eye; Px $gr 9 3 2 2 $eye                          # LED square eyes
  Px $gr 6 5 4 1 $cheek
  Px $gr 4 7 8 5 $cloth
  Px $gr 7 8 2 2 $badge                                              # chest badge
  if ($sp -eq 'silicon') {
    Px $gr 6 8 1 1 $eye; Px $gr 9 10 1 1 $eye                       # circuit traces
  }
  Px $gr 3 7 1 4 $skin; Px $gr 12 7 1 4 $skin
  Px $gr 5 12 2 3 $pant; Px $gr 9 12 2 3 $pant
  Px $gr 5 15 2 1 '#241E16'; Px $gr 9 15 2 1 '#241E16'
}

function Draw-SpriteBeing {
  param($gr, [string]$core, [string]$eye)
  PxA $gr 4 3 8 8 70 $core
  PxA $gr 5 4 6 6 120 $core
  PxA $gr 6 5 4 4 200 $core
  PxA $gr 5 6 6 3 220 $core
  Px $gr 7 6 2 2 '#F5EFFF'
  Px $gr 6 6 1 1 $eye; Px $gr 9 6 1 1 $eye
  Px $gr 5 13 1 1 $core; Px $gr 10 12 1 1 $core; Px $gr 12 9 1 1 $core
}

# --- load census (read-only), stride-select 32 across id order ---
$all = New-Object System.Collections.Generic.List[object]
foreach ($ln in (Get-Content $CENSUS -Encoding UTF8)) {
  if ($ln.Trim()) { $all.Add(($ln | ConvertFrom-Json)) }
}
$sel = New-Object System.Collections.Generic.List[object]
$step = [Math]::Floor($all.Count / $TAKE)
if ($step -lt 1) { $step = 1 }
for ($i = 0; $i -lt $all.Count -and $sel.Count -lt $TAKE; $i += $step) { $sel.Add($all[$i]) }

$chNan = [string][char]0x7537
$chNv = [string][char]0x5973
$used = New-Object 'System.Collections.Generic.HashSet[string]'
$manifest = New-Object System.Collections.Generic.List[object]
$files = New-Object System.Collections.Generic.List[string]
foreach ($r in $sel) {
  $id = [string]$r.id
  $sp = [string]$r.species
  $gcode = 2
  if ($r.gender -and ([string]$r.gender).Contains($chNan)) { $gcode = 1 }
  elseif ($r.gender -and ([string]$r.gender).Contains($chNv)) { $gcode = 0 }
  $eye = '#FFD27A'
  $skin = ''
  $hair = ''
  $cloth = ''
  $badge = ''
  $core = ''
  $iSkin = HashInt $id $P_SKIN_C.Count
  $iHair = HashInt ($id + 'h') $P_HAIR_C.Count
  $iCloth = HashInt ($id + 'c') $P_CLOTH_C.Count
  $iBadge = HashInt ($id + 'b') $P_BADGE.Count
  $iCore = HashInt ($id + 's') $P_SPRITE.Count
  if ($sp -eq 'silicon') {
    $skin = $P_SKIN_S[$iSkin % $P_SKIN_S.Count]
    $hair = $P_HAIR_S[$iHair % $P_HAIR_S.Count]
    $cloth = $P_CLOTH_S[$iCloth % $P_CLOTH_S.Count]
    $eye = '#40F0E0'
  } else {
    $skin = $P_SKIN_C[$iSkin]
    $hair = $P_HAIR_C[$iHair]
    $cloth = $P_CLOTH_C[$iCloth]
  }
  if ($sp -ne 'sprite') {
    $poolC = $P_CLOTH_C; $poolH = $P_HAIR_C
    if ($sp -eq 'silicon') { $poolC = $P_CLOTH_S; $poolH = $P_HAIR_S }
    $try = 0
    while ($used.Contains($hair + '|' + $cloth) -and $try -lt 96) {
      $iCloth = ($iCloth + 1) % $poolC.Count
      $cloth = $poolC[$iCloth]
      if ($try -ge $poolC.Count) { $iHair = ($iHair + 1) % $poolH.Count; $hair = $poolH[$iHair] }
      $try++
    }
    [void]$used.Add($hair + '|' + $cloth)
  }
  $badge = $P_BADGE[$iBadge]
  $core = $P_SPRITE[$iCore]
  $gr = @{ v = (New-PxGrid) }
  $f = 'r-' + ($id -replace '[^A-Za-z0-9]', '') + '.png'
  if ($sp -eq 'sprite') {
    Draw-SpriteBeing $gr $core '#F5EFFF'
  } else {
    Draw-Humanoid $gr $sp $gcode $skin $hair $cloth $eye $badge
  }
  $gr.v.gfx.Dispose()
  $gr.v.bmp.Save((Join-Path $out $f), [System.Drawing.Imaging.ImageFormat]::Png)
  $files.Add($f)
  $manifest.Add([ordered]@{
    id = $id; name = [string]$r.name; species = $sp; gender = [string]$r.gender
    district = [string]$r.district; profession = [string]$r.profession
    file = $f; skin = $skin; hair = $hair; cloth = $cloth; eye = $eye; badge = $badge
  })
}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'), (ConvertTo-Json ($manifest) -Depth 4), (New-Object System.Text.UTF8Encoding($false)))

# --- contact sheet: 8 cols x 4 rows @ 96px ---
$cell = 96; $pad = 8; $cols = 8
$rowCount = [Math]::Ceiling($files.Count / $cols)
$mw = ($cell + $pad) * $cols + $pad
$mh = ($cell + $pad) * $rowCount + $pad
$m = New-Object System.Drawing.Bitmap($mw, $mh)
$mg = [System.Drawing.Graphics]::FromImage($m)
$mg.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None
$mg.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
$mg.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Half
$bgc = [System.Drawing.ColorTranslator]::FromHtml('#060A13')
$bbr = New-Object System.Drawing.SolidBrush($bgc)
$mg.FillRectangle($bbr, 0, 0, $m.Width, $m.Height)
for ($i = 0; $i -lt $files.Count; $i++) {
  $sb = New-Object System.Drawing.Bitmap((Join-Path $out $files[$i]))
  $cx = $pad + ($i % $cols) * ($cell + $pad)
  $cy = $pad + [Math]::Floor($i / $cols) * ($cell + $pad)
  $mg.DrawImage($sb, $cx, $cy, $cell, $cell)
  $sb.Dispose()
}
$mg.Dispose()
$m.Save((Join-Path $out 'contact-sheet.png'), [System.Drawing.Imaging.ImageFormat]::Png)
Write-Output ('BAKED residents=' + $files.Count + ' dir=' + $out)
