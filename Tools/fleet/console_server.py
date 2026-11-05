#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""console_server.py - 主控常驻可视面（本机 8787，只绑 localhost）。

为什么（CEO 2026-11-05「我需要你的自动化执行，而且我能看得到才放心，尤其 macbook
适合常驻 agent」）：看板此前只是每 20 秒生成一个 HTML 文件，没有任何服务把它跑起来，
等于"有账本没有屏幕"。这一站把它变成随时能刷新的一个页面，并常驻开机自启。

页面内容（全部来自盘上事实，不编）：
  1. 主控一屏 MASTER-SCREEN.md（四线四行 + 最重要的一件事）
  2. 分层决策 DECISIONS.md（需要 CEO 的 ≤3 条 + 各层在办）
  3. 新 CEO 令 state/orders-new.json（任何机器上发的令）
  4. 机队实况 fleet-console.html（既有看板，内嵌）
  5. 队列/机器/账本摘要

安全：只监听 127.0.0.1，不对外；不读凭据文件；无写操作。

用法：python3 Tools/fleet/console_server.py [--port 8787]
"""
import argparse
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")


def _read(p, limit=200000):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read()[:limit]
    except Exception:
        return "(缺失) %s" % p


def _json(p, default=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def page():
    screen = _read(os.path.join(F, "MASTER-SCREEN.md"))
    decisions = _read(os.path.join(F, "DECISIONS.md"))
    neworders = _json(os.path.join(F, "state", "orders-new.json"), {}) or {}
    lines = (_json(os.path.join(F, "state", "lines.json"), {}) or {})
    comms = (_json(os.path.join(F, "state", "comms.json"), {}) or {})
    q = (_json(os.path.join(F, "state", "metrics.json"), {}) or {})

    un = _json(os.path.join(F, "state", "unlocks.json"), {}) or {}
    _w = un.get("waiting") or []
    unlock_html = ("<div class='box red'><h2>等你手上的 %d 件（办好后自动解锁）</h2><ul>%s</ul></div>"
                   % (len(_w), "".join("<li><b>%s</b>：%s</li>" % (x.get("line"), x.get("waiting_on"))
                                       for x in _w))) if _w else ""
    mo = _json(os.path.join(F, "state", "mac-loadout.json"), {}) or {}
    _m = mo.get("measured") or {}
    mac_html = ("<div class='box'><h2>MacBook 算力阶梯：%s</h2>"
                "<table><tr><th>可用内存</th><td>%s GB</td><th>GPU</th><td>%s%%</td>"
                "<th>swap</th><td>%s MB</td><th>负载</th><td>%s</td></tr>"
                "<tr><th>在跑什么</th><td colspan='7'>%s</td></tr></table></div>") % (
        mo.get("level", "-"), _m.get("free_gb", "-"), _m.get("gpu_pct", "-"),
        _m.get("swap_mb", "-"), round(float(_m.get("load1") or 0), 2),
        ", ".join("%s×%s" % (d.get("task"), d.get("n")) for d in (mo.get("did") or [])) or "-")
    seats = []
    _ag = os.path.join(F, "state", "agents")
    for sid in ("S1", "S2", "S3", "S4", "S5", "S6", "S7"):
        b = _json(os.path.join(_ag, sid, "beat.json"), {}) or {}
        seats.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            sid, b.get("name", "-"), b.get("ts", "未跑过"),
            ",".join(b.get("failed") or []) or "正常"))
    seat_html = ("<div class='box'><h2>智能体席位（7 席轮转）</h2>"
                 "<table><tr><th>席</th><th>专责</th><th>最近一次</th><th>失败</th></tr>%s</table></div>"
                 % "".join(seats))
    dp = _json(os.path.join(F, "state", "day-plan.json"), {}) or {}
    win = dp.get("window") or {}
    duty_html = "<div class='box'><h2>当前班次：%s（%s–%s）</h2><p class='small'>%s</p><ol>%s</ol></div>" % (
        win.get("name", "-"), win.get("from", "-"), win.get("to", "-"), win.get("why", ""),
        "".join("<li><b>%s</b>·%s — %s</li>" % (d.get("domain"), d.get("name"), d.get("action"))
                for d in (dp.get("now_duties") or [])[:12]))
    beat = _json(os.path.join(F, "state", "agent-beat.json"), {}) or {}
    verify = _json(os.path.join(F, "state", "verify-done.json"), {}) or {}
    agent_html = (
        "<div class='box'><h2>常驻智能体最近一次动作</h2>"
        "<table><tr><th>时间</th><td>%s</td></tr>"
        "<tr><th>跑了多少阶段</th><td>%s（失败：%s）</td></tr>"
        "<tr><th>本轮最重要</th><td>%s</td></tr>"
        "<tr><th>本轮动作</th><td>%s</td></tr>"
        "<tr><th>验收结果</th><td>近 24h DONE %s 张：通过 %s，可疑 %s</td></tr></table></div>"
    ) % (beat.get("ts", "-"), beat.get("stages", "-"),
         ",".join(beat.get("failed") or []) or "无",
         (beat.get("top") or "-")[:120],
         ", ".join(d.get("tag", "") + ":" + str(d.get("rc")) for d in (beat.get("did") or [])) or "-",
         verify.get("checked", "-"), verify.get("pass", "-"), verify.get("suspect", "-"))

    nodes = []
    for n in comms.get("nodes") or []:
        nodes.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%ss</td><td>%s</td></tr>" % (
            n.get("node"), "在线" if n.get("online") else "离线",
            (n.get("job") or "-")[:38], int(n.get("last_receipt_s") or 0),
            ",".join(n.get("flags") or []) or "-"))

    orders_html = ""
    if int(neworders.get("new_count") or 0) > 0:
        items = "".join("<li><b>%s</b> %s</li>" % (o.get("id"), (o.get("text") or "")[:160])
                        for o in (neworders.get("orders") or [])[:5])
        orders_html = ("<div class='box red'><h2>新 CEO 令 %d 条（待落地）</h2><ul>%s</ul></div>"
                       % (int(neworders["new_count"]), items))

    def md2html(t):
        # 极简渲染：标题/表格/行内粗体，够看即可，不引入依赖
        out, intable = [], False
        for ln in t.splitlines():
            if ln.startswith("|"):
                cells = [c.strip() for c in ln.strip("|").split("|")]
                if set("".join(cells)) <= set("-: "):
                    continue
                tag = "th" if not intable else "td"
                if not intable:
                    out.append("<table>")
                    intable = True
                out.append("<tr>" + "".join("<%s>%s</%s>" % (tag, c, tag) for c in cells) + "</tr>")
                continue
            if intable:
                out.append("</table>")
                intable = False
            if ln.startswith("#"):
                lvl = min(3, len(ln) - len(ln.lstrip("#")))
                out.append("<h%d>%s</h%d>" % (lvl + 1, ln.lstrip("# ").replace("**", ""), lvl + 1))
            elif ln.strip():
                out.append("<p>%s</p>" % ln.replace("**", ""))
        if intable:
            out.append("</table>")
        return "\n".join(out)

    return """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="15">
<title>主控台 · FluxGroup</title>
<style>
body{background:#0f1115;color:#e6e6e6;font:14px/1.6 -apple-system,"PingFang SC",sans-serif;margin:0;padding:18px}
h1{font-size:18px;margin:0 0 12px;color:#8ecbff}
h2{font-size:15px;margin:0 0 8px;color:#9be3b1}
.box{background:#171a21;border:1px solid #262b36;border-radius:8px;padding:14px;margin-bottom:14px}
.red{border-color:#8b3a3a;background:#241618}
table{border-collapse:collapse;width:100%%;font-size:13px}
td,th{border-bottom:1px solid #262b36;padding:5px 8px;text-align:left}
th{color:#8ecbff}
.small{color:#8892a4;font-size:12px}
iframe{width:100%%;height:720px;border:1px solid #262b36;border-radius:8px;background:#fff}
</style></head><body>
<h1>主控台 · %s · 每 15 秒自动刷新</h1>
%s
%s
%s
%s
%s
%s
<div class="box"><h2>主控一屏</h2>%s</div>
<div class="box"><h2>分层决策（只有 ≤3 条需要你）</h2>%s</div>
<div class="box"><h2>机队实况</h2><table><tr><th>机器</th><th>状态</th><th>在跑</th><th>无回执</th><th>旗标</th></tr>%s</table></div>
<div class="box"><h2>旧看板</h2><iframe src="/fleet-console.html"></iframe></div>
<p class="small">数据源：MASTER-SCREEN.md / DECISIONS.md / state/*.json。只读、只绑 localhost。</p>
</body></html>""" % (time.strftime("%H:%M:%S"), orders_html, unlock_html, duty_html, mac_html, seat_html, agent_html, md2html(screen),
                      md2html(decisions), "".join(nodes))


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/fleet-console.html"):
            body = _read(os.path.join(ROOT, "fleet-console.html")).encode("utf-8")
            ctype = "text/html; charset=utf-8"
        elif self.path.startswith("/api/screen"):
            body = _read(os.path.join(F, "MASTER-SCREEN.md")).encode("utf-8")
            ctype = "text/markdown; charset=utf-8"
        else:
            body = page().encode("utf-8")
            ctype = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    a = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), H)
    print("console on http://127.0.0.1:%d" % a.port)
    srv.serve_forever()


if __name__ == "__main__":
    main()