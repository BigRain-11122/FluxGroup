# -*- coding: utf-8 -*-
"""m-v1-globe · 生成九区地球视图（单文件 HTML，双击即开，无依赖，读当前数据）"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
REGIONS = os.path.join(ROOT, "modules", "m-w1-regions", "data", "regions.json")
STATE = os.path.join(ROOT, "modules", "m-w3-settle", "data", "state.json")
TIME = os.path.join(ROOT, "modules", "m-w2-clock", "data", "time.json")
EVENTS = os.path.join(ROOT, "modules", "m-w2-clock", "data", "events.jsonl")
OUT = os.path.join(HERE, "dist", "globe.html")

COLOR = {"growing": "#4fb3d9", "repairing": "#69c47f", "waiting": "#e8b44a",
         "dispersing": "#e2764a", "stalled": "#6b6b6b"}
CN = {"growing": "在长", "repairing": "在修", "waiting": "在等",
      "dispersing": "在散", "stalled": "停摆"}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    regions = json.load(open(REGIONS, encoding="utf-8"))["regions"]
    state = {}
    if os.path.exists(STATE):
        for r in json.load(open(STATE, encoding="utf-8"))["regions"]:
            state[r["id"]] = r
    day = json.load(open(TIME, encoding="utf-8"))["day"] if os.path.exists(TIME) else 0
    ev = 0
    if os.path.exists(EVENTS):
        with open(EVENTS, encoding="utf-8", errors="replace") as f:
            ev = sum(1 for line in f if line.strip())

    homes = [r for r in regions if r["kind"] == "home"]
    bads = [r for r in regions if r["kind"] == "badland"]
    nodes = []
    for i, r in enumerate(homes):
        a = -math.pi / 2 + i * (2 * math.pi / max(1, len(homes)))
        nodes.append((r, 400 + 150 * math.cos(a), 300 + 150 * math.sin(a)))
    for i, r in enumerate(bads):
        a = -math.pi / 2 + math.pi / 6 + i * (2 * math.pi / max(1, len(bads)))
        nodes.append((r, 400 + 250 * math.cos(a), 300 + 250 * math.sin(a)))

    parts = []
    for r, x, y in nodes:
        s = state.get(r["id"], {})
        st = s.get("state", "waiting")
        c = COLOR.get(st, "#888")
        pop = r.get("population", 0)
        rad = 14 + min(26, pop / 120.0)
        parts.append(
            f'<g class="n" data-name="{r["name"]}" data-note="{r.get("note","")}" '
            f'data-state="{CN.get(st, st)}" data-pop="{pop}" data-pos="{s.get("positivity","—")}">'
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rad:.0f}" fill="{c}" opacity="0.85"/>'
            f'<text x="{x:.0f}" y="{y + rad + 16:.0f}" text-anchor="middle" '
            f'fill="#cfd8e3" font-size="13">{r["name"]}</text></g>')

    html = f"""<!doctype html><html lang="zh"><meta charset="utf-8">
<title>硅基地球 · 第 {day} 天</title>
<style>
body{{margin:0;background:#0b0f14;color:#cfd8e3;font:14px/1.6 system-ui,"Microsoft YaHei",sans-serif}}
.wrap{{display:flex;gap:24px;padding:24px;align-items:flex-start}}
svg{{background:#0e141b;border-radius:16px}}
.n{{cursor:pointer}} .n:hover circle{{opacity:1;stroke:#fff;stroke-width:2}}
#info{{min-width:250px;background:#111a23;border-radius:12px;padding:16px}}
h1{{font-size:16px;margin:0 0 8px;color:#9fb3c8;font-weight:500}}
.k{{color:#6b7f95;font-size:12px}}
.bar{{padding:0 24px;color:#7b8fa6;font-size:13px}}
</style>
<div class="bar">第 <b>{day}</b> 天 · {len(regions)} 块区域 · {ev} 条事件　
<span class="k">重新生成即刷新：python modules/m-v1-globe/build.py</span></div>
<div class="wrap">
<svg width="800" height="600" viewBox="0 0 800 600">
  <circle cx="400" cy="300" r="290" fill="#0d1620" stroke="#1d2b3a"/>
  <circle cx="400" cy="300" r="150" stroke="#1d2b3a" fill="none" stroke-dasharray="3 6"/>
  <circle cx="400" cy="300" r="250" stroke="#1d2b3a" fill="none" stroke-dasharray="3 6"/>
  {''.join(parts)}
</svg>
<div id="info"><h1>点一块区域</h1>
<p class="k">内圈＝住人的六块，外圈＝三块烂地。<br>
颜色：蓝在长 · 绿在修 · 黄在等 · 橙在散 · 灰停摆。<br>圆的大小＝人口。</p></div>
</div>
<script>
document.querySelectorAll('.n').forEach(function(g){{
  g.addEventListener('click', function(){{
    var d = g.dataset;
    document.getElementById('info').innerHTML =
      '<h1>' + d.name + '</h1><p>' + d.note + '</p>' +
      '<p class="k">状态：' + d.state + '　人口：' + d.pop + '　指数：' + d.pos + '</p>';
  }});
}});
</script>
</html>"""

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ {OUT}（{os.path.getsize(OUT)/1024:.0f} KB · 第 {day} 天 · {len(nodes)} 区）")


if __name__ == "__main__":
    sys.exit(main() or 0)
