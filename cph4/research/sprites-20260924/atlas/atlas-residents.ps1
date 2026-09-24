# atlas-residents.ps1 - parts atlas + palette-swap composition (P-71, CEO order ~21:10)
# Law: residents share ONE atlas of part masks; each resident = one palette row.
# Zero per-resident image files. 27" 4K spec: wall cells 128px, integer scaling.
# ASCII-only body per encoding law.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$root = 'C:\Users\sjs20\Desktop\FluxGroup'
$out = Join-Path $root 'cph4\research\sprites-20260924\atlas'
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

# parts as logical 16x16 rect lists (mask color: W=base, G=derived shade)
# NOTE: unary comma before each sub-array - @() enumerates pipeline output,
# so @( @(..), @(..) ) flattens; ,@(..) emits the array as ONE item.
$PART_SKIN = @( ,@(4, 1, 8, 6, 'W'), ,@(3, 7, 1, 4, 'W'), ,@(12, 7, 1, 4, 'W'), ,@(6, 5, 4, 1, 'G') )
$PART_CLOTH = @( ,@(4, 7, 8, 5, 'W') )
$PART_PANT = @( ,@(5, 12, 2, 3, 'W'), ,@(9, 12, 2, 3, 'W'), ,@(5, 15, 2, 1, 'G'), ,@(9, 15, 2, 1, 'G') )
$PART_HAIR_S = @( ,@(4, 1, 8, 2, 'W'), ,@(3, 2, 1, 2, 'W'), ,@(12, 2, 1, 2, 'W') )
$PART_HAIR_L = @( ,@(4, 1, 8, 2, 'W'), ,@(3, 2, 1, 7, 'W'), ,@(12, 2, 1, 7, 'W') )
$PART_EYES_LED = @( ,@(5, 3, 2, 2, 'W'), ,@(9, 3, 2, 2, 'W'), ,@(6, 8, 1, 1, 'W'), ,@(9, 10, 1, 1, 'W') )
$PART_EYES_DOT = @( ,@(6, 3, 1, 1, 'W'), ,@(9, 3, 1, 1, 'W') )
$PART_BADGE = @( ,@(7, 8, 2, 2, 'W') )

$CELL = 32  # 16 logical x2
$ACOLS = 4
$PART_NAMES = @('skin', 'cloth', 'pant', 'hair-short', 'hair-long', 'eyes-led', 'eyes-dot', 'badge', 'being')

function Draw-Part {
  param($g, [object]$rects)
  foreach ($wrap in $rects) {
    $r = $wrap[0]   # unwrap unary-comma wrapper
    $c = [System.Drawing.Color]::White
    if ($r[4] -eq 'G') { $c = [System.Drawing.Color]::FromArgb(255, 210, 210, 210) }
    $br = New-Object System.Drawing.SolidBrush($c)
    $g.FillRectangle($br, $r[0] * 2, $r[1] * 2, $r[2] * 2, $r[3] * 2)
    $br.Dispose()
  }
}

# --- 1. build atlas: 9 cells of 32x32 on a 128x128 (4 cols x 3 rows) ---
$atlas = New-Object System.Drawing.Bitmap(128, 128)
$ag = [System.Drawing.Graphics]::FromImage($atlas)
$ag.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None
# NOTE: hashtable not @()-list - PS flattens a comma-list of arrays at top level
$parts = @{
  skin = $PART_SKIN; cloth = $PART_CLOTH; pant = $PART_PANT
  'hair-short' = $PART_HAIR_S; 'hair-long' = $PART_HAIR_L
  'eyes-led' = $PART_EYES_LED; 'eyes-dot' = $PART_EYES_DOT; badge = $PART_BADGE
}
$layout = [ordered]@{}
for ($i = 0; $i -lt 8; $i++) {
  $cellBmp = New-Object System.Drawing.Bitmap($CELL, $CELL)
  $cg = [System.Drawing.Graphics]::FromImage($cellBmp)
  $cg.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None
  Draw-Part $cg $parts[$PART_NAMES[$i]]
  $cg.Dispose()
  $cx = ($i % $ACOLS) * $CELL
  $cy = [Math]::Floor($i / $ACOLS) * $CELL
  $ag.DrawImage($cellBmp, $cx, $cy)
  $cellBmp.Dispose()
  $layout[$PART_NAMES[$i]] = @{ x = $cx; y = $cy; w = $CELL; h = $CELL }
}
# being cell: OPAQUE gray bands (no alpha blending in atlas; alpha injected at remap)
# band stack (later draws fully replace earlier - opaque, no blend artifacts)
$cellBmp = New-Object System.Drawing.Bitmap($CELL, $CELL)
$cg = [System.Drawing.Graphics]::FromImage($cellBmp)
$cg.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None
$bandDefs = @(
  @(4, 3, 8, 8, 50),    # outer aura  -> core@70
  @(5, 4, 6, 6, 120),   # mid aura    -> core@150
  @(6, 5, 4, 4, 200),   # body        -> core@225
  @(5, 6, 6, 3, 200),
  @(7, 6, 2, 2, 230),   # inner core  -> core@245
  @(5, 13, 1, 1, 120),  # sparks
  @(10, 12, 1, 1, 120),
  @(12, 9, 1, 1, 120)
)
foreach ($bd in $bandDefs) {
  $c = [System.Drawing.Color]::FromArgb(255, $bd[4], $bd[4], $bd[4])
  $br = New-Object System.Drawing.SolidBrush($c)
  $cg.FillRectangle($br, $bd[0] * 2, $bd[1] * 2, $bd[2] * 2, $bd[3] * 2)
  $br.Dispose()
}
foreach ($e in @( @(6, 6, 1, 1), @(9, 6, 1, 1), @(7, 9, 2, 1) )) {
  $c = [System.Drawing.Color]::FromArgb(255, 210, 210, 210)
  $br = New-Object System.Drawing.SolidBrush($c)
  $cg.FillRectangle($br, $e[0] * 2, $e[1] * 2, $e[2] * 2, $e[3] * 2)
  $br.Dispose()
}
$cg.Dispose()
$bi = 8
$bx = ($bi % $ACOLS) * $CELL
$by = [Math]::Floor($bi / $ACOLS) * $CELL
$ag.DrawImage($cellBmp, $bx, $by)
$cellBmp.Dispose()
$layout[$PART_NAMES[$bi]] = @{ x = $bx; y = $by; w = $CELL; h = $CELL }
$ag.Dispose()
$atlas.Save((Join-Path $out 'atlas.png'), [System.Drawing.Imaging.ImageFormat]::Png)
[IO.File]::WriteAllText((Join-Path $out 'layout.json'), (ConvertTo-Json $layout -Depth 4), (New-Object System.Text.UTF8Encoding($false)))
Write-Output 'ATLAS_BUILT parts=9 size=128x128'

# --- 2. compose residents FROM the atlas (zero per-resident files) ---
function HexColor([string]$hex) {
  return [System.Drawing.ColorTranslator]::FromHtml($hex)
}
function ShadeHex {
  param([string]$hex, [double]$f)
  $c = [System.Drawing.ColorTranslator]::FromHtml($hex)
  return [System.Drawing.Color]::FromArgb(255, [int]($c.R * $f), [int]($c.G * $f), [int]($c.B * $f))
}
function Make-Attrs {
  param([System.Drawing.Color]$c1, [System.Drawing.Color]$c2)
  $ia = New-Object System.Drawing.Imaging.ImageAttributes
  $m1 = New-Object System.Drawing.Imaging.ColorMap
  $m1.OldColor = [System.Drawing.Color]::White; $m1.NewColor = $c1
  $m2 = New-Object System.Drawing.Imaging.ColorMap
  $m2.OldColor = [System.Drawing.Color]::FromArgb(255, 210, 210, 210); $m2.NewColor = $c2
  $ia.SetRemapTable(@($m1, $m2))
  return $ia
}
function Make-AttrsGlow {
  param([string]$coreHex)
  # opaque gray bands in atlas -> alpha-carrying core color at remap time
  $core = [System.Drawing.ColorTranslator]::FromHtml($coreHex)
  $ia = New-Object System.Drawing.Imaging.ImageAttributes
  $maps = @()
  foreach ($band in @( @(50, 70), @(120, 150), @(200, 225), @(230, 245) )) {
    $m = New-Object System.Drawing.Imaging.ColorMap
    $m.OldColor = [System.Drawing.Color]::FromArgb(255, $band[0], $band[0], $band[0])
    $m.NewColor = [System.Drawing.Color]::FromArgb($band[1], $core.R, $core.G, $core.B)
    $maps += $m
  }
  $mg = New-Object System.Drawing.Imaging.ColorMap
  $mg.OldColor = [System.Drawing.Color]::FromArgb(255, 210, 210, 210); $mg.NewColor = [System.Drawing.ColorTranslator]::FromHtml('#F5EFFF')
  $maps += $mg
  $ia.SetRemapTable($maps)
  return $ia
}
function Blit-Part {
  param($dst, $name, $c1, $c2)
  $lay = $script:layoutObj.$name
  $ia = Make-Attrs $c1 $c2
  $rect = New-Object System.Drawing.Rectangle(0, 0, $CELL, $CELL)
  $dst.DrawImage($script:atlasBmp, $rect, $lay.x, $lay.y, $lay.w, $lay.h, [System.Drawing.GraphicsUnit]::Pixel, $ia)
  $ia.Dispose()
}

$all = New-Object System.Collections.Generic.List[object]
foreach ($ln in (Get-Content $CENSUS -Encoding UTF8)) {
  if ($ln.Trim()) { $all.Add(($ln | ConvertFrom-Json)) }
}
$sel = New-Object System.Collections.Generic.List[object]
$step = [Math]::Floor($all.Count / $TAKE)
if ($step -lt 1) { $step = 1 }
for ($i = 0; $i -lt $all.Count -and $sel.Count -lt $TAKE; $i += $step) { $sel.Add($all[$i]) }

$P_SKIN_C = @('#E6B184', '#D8A87A', '#C9986B', '#E8C098', '#DBAF85', '#C9A47E')
$P_HAIR_C = @('#2E2A26', '#6B4A32', '#8A4A32', '#C9A56A', '#5A5A5A', '#D8D8D0', '#6E5A80', '#3E7A72')
$P_CLOTH_C = @('#A83A3A', '#C07A2E', '#B3A23E', '#4E7A3E', '#3E7A72', '#3E6E9E', '#3A4E7E', '#7A4E9E', '#9E4E7E', '#8A5A3E', '#7A746A', '#5A6E4E')
$P_SKIN_S = @('#D8C8B0', '#CFC2AC', '#B8AC98')
$P_HAIR_S = @('#8A9AB8', '#2E6E6E', '#C8D4E8', '#3E4A5E', '#9E7EB8')
$P_CLOTH_S = @('#2E5E4E', '#3E8E8E', '#3E6E9E', '#2A3A5E', '#6E5E9E', '#9E5E8E', '#6A7484', '#8E7A4E', '#4E6E3E', '#5E8E5E', '#4E4E7E', '#7E4E5E')
$P_SPRITE = @('#5EEAD4', '#A78BFA', '#60A5FA', '#F472B6', '#4ADE80')
$P_BADGE = @('#FBBF24', '#5EEAD4', '#A78BFA', '#F472B6', '#4ADE80', '#60A5FA')

$script:atlasBmp = New-Object System.Drawing.Bitmap((Join-Path $out 'atlas.png'))
$script:layoutObj = Get-Content (Join-Path $out 'layout.json') -Raw -Encoding UTF8 | ConvertFrom-Json

$chNan = [string][char]0x7537
$chNv = [string][char]0x5973
$used = New-Object 'System.Collections.Generic.HashSet[string]'
$manifest = New-Object System.Collections.Generic.List[string]
$wallCell = 128; $wallPad = 16; $wallCols = 8
$wallRows = [Math]::Ceiling($TAKE / $wallCols)
$mw = ($wallCell + $wallPad) * $wallCols + $wallPad
$mh = ($wallCell + $wallPad) * $wallRows + $wallPad
$wall = New-Object System.Drawing.Bitmap($mw, $mh)
$wg = [System.Drawing.Graphics]::FromImage($wall)
$wg.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None
$wg.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
$wg.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Half
$bgc = [System.Drawing.ColorTranslator]::FromHtml('#060A13')
$wg.FillRectangle((New-Object System.Drawing.SolidBrush($bgc)), 0, 0, $wall.Width, $wall.Height)

$n = 0
foreach ($r in $sel) {
  $id = [string]$r.id
  $sp = [string]$r.species
  $gcode = 2
  if ($r.gender -and ([string]$r.gender).Contains($chNan)) { $gcode = 1 }
  elseif ($r.gender -and ([string]$r.gender).Contains($chNv)) { $gcode = 0 }
  $eye = '#FFD27A'
  $iSkin = HashInt $id $P_SKIN_C.Count
  $iHair = HashInt ($id + 'h') $P_HAIR_C.Count
  $iCloth = HashInt ($id + 'c') $P_CLOTH_C.Count
  $iBadge = HashInt ($id + 'b') $P_BADGE.Count
  $iCore = HashInt ($id + 's') $P_SPRITE.Count
  $skin = $P_SKIN_C[$iSkin]; $hair = $P_HAIR_C[$iHair]; $cloth = $P_CLOTH_C[$iCloth]; $badge = $P_BADGE[$iBadge]
  if ($sp -eq 'silicon') {
    $skin = $P_SKIN_S[$iSkin % $P_SKIN_S.Count]
    $hair = $P_HAIR_S[$iHair % $P_HAIR_S.Count]
    $cloth = $P_CLOTH_S[$iCloth % $P_CLOTH_S.Count]
    $eye = '#40F0E0'
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
  # compose on a 32x32 canvas (from atlas only)
  $cb = New-Object System.Drawing.Bitmap($CELL, $CELL)
  $cg = [System.Drawing.Graphics]::FromImage($cb)
  $cg.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None
  if ($sp -eq 'sprite') {
    $core = $P_SPRITE[$iCore]
    $lay = $script:layoutObj.'being'
    $ia = Make-AttrsGlow $core
    $rect = New-Object System.Drawing.Rectangle(0, 0, $CELL, $CELL)
    $cg.DrawImage($script:atlasBmp, $rect, $lay.x, $lay.y, $lay.w, $lay.h, [System.Drawing.GraphicsUnit]::Pixel, $ia)
    $ia.Dispose()
  } else {
    Blit-Part $cg 'pant' (HexColor $(if ($sp -eq 'silicon') { '#3D4A5C' } else { '#3A3440' })) (HexColor '#241E16')
    Blit-Part $cg 'skin' (HexColor $skin) (ShadeHex $skin 0.85)
    Blit-Part $cg 'cloth' (HexColor $cloth) (ShadeHex $cloth 0.8)
    Blit-Part $cg 'badge' (HexColor $badge) (HexColor $badge)
    if ($gcode -eq 0) { Blit-Part $cg 'hair-long' (HexColor $hair) (HexColor $hair) }
    else { Blit-Part $cg 'hair-short' (HexColor $hair) (HexColor $hair) }
    if ($sp -eq 'silicon') { Blit-Part $cg 'eyes-led' (HexColor $eye) (HexColor $eye) }
    else { Blit-Part $cg 'eyes-dot' (HexColor $eye) (HexColor $eye) }
  }
  $cg.Dispose()
  # blit into wall (4x integer upscale 128 = 4K spec cell)
  $cx = $wallPad + ($n % $wallCols) * ($wallCell + $wallPad)
  $cy = $wallPad + [Math]::Floor($n / $wallCols) * ($wallCell + $wallPad)
  $wg.DrawImage($cb, $cx, $cy, $wallCell, $wallCell)
  $cb.Dispose()
  $manifest.Add((ConvertTo-Json ([ordered]@{ id = $id; name = [string]$r.name; species = $sp; skin = $skin; hair = $hair; cloth = $cloth; eye = $eye; badge = $badge }) -Compress))
  $n++
}
$wg.Dispose()
[IO.File]::WriteAllLines((Join-Path $out 'manifest.jsonl'), $manifest, (New-Object System.Text.UTF8Encoding($false)))
$wall.Save((Join-Path $out 'wall-from-atlas.png'), [System.Drawing.Imaging.ImageFormat]::Png)
Write-Output ('COMPOSED residents=' + $n + ' per-resident-files=0 wall-cell=128px')
