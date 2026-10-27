# -*- coding: utf-8 -*-
"""Zoom recheck boards — full-res frames for thumbnail-scale FLAGs (CEO O-20261017-1330).
ZOOM-A tool/hand chains, ZOOM-B crowds/statues/faces, ZOOM-C objects/textures, ZOOM-D light."""
import os, json, subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
FF   = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
MV   = os.path.join(HERE, "full_mv_v52.mp4")
OUT  = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments\_cut\v51\fullcover"
TL = json.load(open(os.path.join(HERE, "timeline_v52.json"), encoding="utf-8"))
W, H, TMAX = 1344, 768, 234.20
shots = TL["shots"]
for s in shots:
    s["mid"] = round((s["win"][0] + s["win"][1]) / 2.0, 3)

def fnt(sz):
    for p in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
F22, F32 = fnt(22), fnt(32)

def shot_by(prefix):
    for s in shots:
        b = s["sid"].split("@")[0]
        if b == prefix or b.startswith(prefix):
            return s
    raise SystemExit("sid missing " + prefix)

def grab(t, path):
    if os.path.isfile(path) and os.path.getsize(path) > 1000:
        return path
    t = max(0.0, min(TMAX, round(t * 24) / 24.0))
    r = subprocess.run([FF, "-y", "-ss", "%.3f" % t, "-i", MV, "-frames:v", "1", path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert r.returncode == 0 and os.path.isfile(path), "grab fail @%.2f" % t
    return path

def zoom_sheet(name, items):
    cols, rows = 3, (len(items) + 2) // 3
    im = Image.new("RGB", (W * cols, 46 + (34 + H) * rows), (12, 12, 12))
    ImageDraw.Draw(im).text((12, 8), name + "  (full-res 1344x768)", fill=(240, 226, 160), font=F32)
    for k, (pf, frac, desc) in enumerate(items):
        s = shot_by(pf)
        t = s["win"][0] + (s["win"][1] - s["win"][0]) * frac
        x = (k % 3) * W; y = 46 + (k // 3) * (34 + H)
        im.paste(Image.new("RGB", (W, 34), (14, 14, 14)), (x, y))
        ImageDraw.Draw(im).text((x + 10, y + 5), "%s @%.2f | %s" % (s["sid"], t, desc),
                                fill=(240, 226, 160), font=F22)
        p = os.path.join(OUT, "zoom_%s_%d.png" % (name.split()[-1], k))
        im.paste(Image.open(grab(t, p)).resize((W, H)), (x, y + 34))
    q = os.path.join(OUT, "%s.jpg" % name.replace(" ", "-"))
    im.save(q, quality=88)
    print("SHEET " + q)

zoom_sheet("ZOOM-A tool hand chains", [
    ("S6_chisel", 0.5, "chisel+hammer hand joint / finger glue"),
    ("C08_strike_burst", 0.42, "hammer-chisel-hand chain in burst light"),
    ("C06_forever_cut", 0.5, "chisel upper end held? no floating tool"),
    ("D01_carver_words", 0.5, "reed pen finger grip"),
    ("D04_her_brush", 0.5, "brush tip contact object form (clay vs bamboo?)"),
    ("E06_strike", 0.35, "strike hand chain in flash"),
])
zoom_sheet("ZOOM-B crowds statues faces", [
    ("N01_war_relief", 0.5, "soldier array limbs/spears melt?"),
    ("N02_crowd_her", 0.5, "crowd faces + phone-holding fingers"),
    ("N03_goddess_pass", 0.5, "statue face/fingers + girl features"),
    ("SING1_v2", 0.5, "hand-torch grip joint"),
    ("E03_gaze_meet", 0.4, "two-face gaze: second face? eye positions"),
    ("E04_replay", 0.5, "two faces: hairline seam, arm-cuff, right-face drift"),
])
zoom_sheet("ZOOM-C objects textures", [
    ("C03_dig_reveal", 0.5, "upper-right dark mass semantics + cuneiform repetition"),
    ("C09_oath_weather", 0.5, "weathered glyph legibility (cuneiform vs bark?)"),
    ("C09b_flame", 0.45, "flame top horizontal bar: rim vs artifact"),
    ("D08_world_flip", 0.45, "bloom center human silhouette? mirror ghost"),
    ("INT3_photo_stare", 0.5, "paper pseudo-cuneiform: latin/mojibake mixed in?"),
    ("SIL1_v4b", 0.6, "symbol band: modern glyphs mixed in?"),
])
zoom_sheet("ZOOM-D light rechecks", [
    ("E01c_first_line", 0.75, "stone chips present + chisel-finger at strike"),
    ("E02a_dig", 0.5, "brush hand at frame edge"),
    ("Z03_lights_out", 0.92, "lights-out tail frame (fade to dark)"),
    ("B01_weary", 0.5, "hand-face boundary + eye slit"),
    ("SING2", 0.5, "singing mouth/teeth natural"),
    ("E01a_carver", 0.5, "close-up eyes symmetry + skin wax"),
])
print("ALL-DONE")
