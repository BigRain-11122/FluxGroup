#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""console_server.py - 主控常驻可视面（本机 8787，只绑 localhost）。

CEO 2026-11-05：「我需要你的自动化执行，而且我能看得到才放心」+「信息密度也要分主次」
→ 这一版按三级信息重排，全量数据仍可在三级折叠里查到，一个字段都不丢。

页面数据（全部来自盘上事实，不编）：
  state/progress.json        在跑/待派/最近完成/最近失败/远端回执/每机心跳与最后产出
  state/fleet-status.json    逐卡判定（死卡/假忙/心跳龄）+ 机队 verdict
  state/soak-summary.json    24h 探针 verdict/green_pct/samples/claimable
  state/unlocks.json         等 CEO 的物理件
  MASTER-SCREEN.md           一屏（四线一张表 + 最重要的一件事）
  DECISIONS.md / PROGRESS.md 分层决策 / 自动事实页（全文折叠）
  PRODUCTION-QUEUE.jsonl     队列原始行（/api/card?id= 取该行原文）

只读：GET /   /api/card?id=   /api/screen   /progress   /fleet-console.html
安全：默认只监听 127.0.0.1；不读凭据；无任何写操作。

用法：python3 Tools/fleet/console_server.py [--port 8787] [--host 127.0.0.1]
"""
import argparse
import html as HT
import json
import os
import re
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
ST = os.path.join(F, "state")

REFRESH_S = 15


# ----------------------------------------------------------------- utils
def _read(p, limit=400000):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read()[:limit]
    except Exception:
        return ""


def _json(p, default=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def esc(s):
    return HT.escape("" if s is None else str(s))


def dur(s):
    """秒 → 带单位字符串。"""
    if s is None:
        return "-"
    try:
        s = float(s)
    except (TypeError, ValueError):
        return "-"
    if s < 0:
        return "-"
    if s < 90:
        return "%ds" % int(s)
    if s < 5400:
        return "%dm" % int(s // 60)
    if s < 172800:
        return "%.1fh" % (s / 3600.0)
    return "%.1fd" % (s / 86400.0)


def chip(kind, text, title=""):
    t = ' title="%s"' % esc(title) if title else ""
    return ('<span class="dot %s"%s>&#9679;</span><span class="sx">%s</span>'
            % (kind, t, esc(text)))


def n(val, unit, f=None, src=None, title=""):
    """带单位的数字：<b class=v>N</b><span class=u>单位</span>（A4 规则）。"""
    a = ' data-f="%s"' % f if f else ""
    b = ' data-src="%s"' % src if src else ""
    t = ' title="%s"' % esc(title) if title else ""
    return '<b class="v"%s%s%s>%s</b><span class="u">%s</span>' % (
        a, b, t, esc(val), esc(unit))


def cardbtn(cid):
    return ('<button class="cid" type="button" data-card="%s" title="点开看队列原文">%s</button>'
            % (esc(cid), esc(cid)))


def copybtn(cid):
    return '<button class="cp" type="button" data-copy="%s" title="复制 id">复制</button>' % esc(cid)


_Q = {"mt": 0.0, "idx": {}}


def qidx():
    """PRODUCTION-QUEUE.jsonl 索引（同 id 后写覆盖），按 mtime 缓存。"""
    p = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
    try:
        mt = os.path.getmtime(p)
    except OSError:
        return {}
    if mt != _Q["mt"]:
        idx = {}
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        d = json.loads(ln)
                    except Exception:
                        continue
                    if isinstance(d, dict) and d.get("id"):
                        idx[str(d["id"])] = d
        except OSError:
            pass
        _Q["idx"] = idx
        _Q["mt"] = mt
    return _Q["idx"]


def md_tables(md):
    """取出 md 里所有表格（含表头行）。"""
    out, cur = [], []
    for ln in (md or "").splitlines():
        s = ln.strip()
        if s.startswith("|") and s.count("|") >= 3:
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            cur.append(cells)
        else:
            if cur:
                out.append(cur)
                cur = []
    if cur:
        out.append(cur)
    return out


def inline(s):
    s = HT.escape(s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def md_html(md):
    """极简 md→html：标题/表格/列表/段落。不引依赖。"""
    out, tbl, lst, first = [], False, False, True
    for ln in (md or "").splitlines():
        t = ln.strip()
        if not t:
            if tbl:
                out.append("</table>")
                tbl = False
            if lst:
                out.append("</ul>")
                lst = False
            continue
        if t.startswith("|") and t.count("|") >= 3:
            cells = [c.strip() for c in t.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            if lst:
                out.append("</ul>")
                lst = False
            if not tbl:
                out.append('<table class="mdt">')
                tbl, first = True, True
            tag = "th" if first else "td"
            out.append("<tr>" + "".join("<%s>%s</%s>" % (tag, inline(c), tag)
                                        for c in cells) + "</tr>")
            first = False
            continue
        if tbl:
            out.append("</table>")
            tbl = False
        if t.startswith("#"):
            if lst:
                out.append("</ul>")
                lst = False
            lvl = min(5, len(t) - len(t.lstrip("#")) + 2)
            out.append("<h%d>%s</h%d>" % (lvl, inline(t.lstrip("# ")), lvl))
        elif t.startswith(("- ", "* ")):
            if not lst:
                out.append("<ul>")
                lst = True
            out.append("<li>%s</li>" % inline(t[2:]))
        else:
            if lst:
                out.append("</ul>")
                lst = False
            out.append("<p>%s</p>" % inline(t))
    if tbl:
        out.append("</table>")
    if lst:
        out.append("</ul>")
    return "".join(out)


def _epoch(s):
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return time.mktime(time.strptime(str(s)[:19], fmt))
        except Exception:
            pass
    return None


def fmt_at(s):
    ep = _epoch(s)
    if ep is None:
        return "-", None
    lt = time.localtime(ep)
    same_day = time.strftime("%Y-%m-%d", lt) == time.strftime("%Y-%m-%d")
    return time.strftime("%H:%M" if same_day else "%m-%d %H:%M", lt), ep


# ----------------------------------------------------------------- page
CSS = """
:root{--bg:#0b0d11;--card:#141821;--card2:#10141b;--line:#232a37;--fg:#e9eef5;--dim:#8b95a7;
--ok:#3fbf7f;--bad:#e2685f;--warn:#e0a83c;--idle:#7a8698;--acc:#6fb3ff}
*{box-sizing:border-box}
html,body{margin:0;max-width:100%}
body{background:var(--bg);color:var(--fg);font:14px/1.42 -apple-system,"PingFang SC","Hiragino Sans GB",system-ui,sans-serif;-webkit-text-size-adjust:100%}
.wrap{max-width:1020px;margin:0 auto;padding:12px 12px 44px}
h1{font-size:17px;margin:0;letter-spacing:.4px}
.hrow{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between;margin-bottom:7px}
.hctl{display:flex;flex-wrap:wrap;gap:7px;align-items:center;font-size:11px;color:var(--dim)}
.one{margin:0 0 9px;font-size:12.5px;background:var(--card2);border-left:3px solid var(--acc);
padding:6px 10px;border-radius:0 6px 6px 0;word-break:break-word}
.one .k{color:var(--acc);margin-right:6px;font-size:11px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:9px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:7px 10px;min-width:0}
.stat .u{display:block;color:var(--dim);font-size:11px;margin-top:1px}
section{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:9px 11px;margin-bottom:9px;min-width:0}
h2{font-size:11.5px;margin:0 0 7px;color:var(--acc);font-weight:600;letter-spacing:.5px;
display:flex;gap:7px;align-items:center;flex-wrap:wrap}
h2 .sub{color:var(--dim);font-weight:400}
.duo{display:grid;grid-template-columns:1fr 1fr;gap:9px}
.duo>section{margin-bottom:9px}
table{width:100%;table-layout:fixed;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:3px 6px;border-bottom:1px solid var(--line);vertical-align:top;
word-break:break-word;overflow-wrap:anywhere}
th{color:var(--dim);font-weight:500;font-size:11px;padding-bottom:2px}
tr:last-child td{border-bottom:none}
td.tm{white-space:nowrap;color:var(--dim);font-size:11.5px;width:74px}
b.v{font-weight:600;font-variant-numeric:tabular-nums;font-size:14px}
.stat b.v{font-size:21px;line-height:1.15}
span.u{color:var(--dim);font-size:11px;margin-left:2px}
.dot{font-size:9px;vertical-align:1px}
.dot.ok{color:var(--ok)}.dot.bad{color:var(--bad)}.dot.warn{color:var(--warn)}.dot.idle{color:var(--idle)}
.sx{font-size:12px}.cx{font-size:12px}.px{font-size:11px;color:var(--dim)}
button{font:inherit;font-size:11.5px;background:#1b2230;color:var(--fg);border:1px solid var(--line);
border-radius:6px;padding:2px 7px;cursor:pointer}
button:hover{border-color:var(--acc);color:var(--acc)}
button.on{background:var(--acc);color:#0b0d11;border-color:var(--acc)}
button.cid{background:none;border:none;color:var(--acc);padding:0;font-size:12px;
font-family:ui-monospace,SFMono-Regular,Menlo,monospace;text-align:left;word-break:break-all}
button.cid:hover{text-decoration:underline}
button.cp{font-size:9.5px;padding:0 4px;margin-left:4px;color:var(--dim)}
section.need{border-left:3px solid var(--warn)}
.legend{font-size:11px;color:var(--dim);display:flex;gap:11px;flex-wrap:wrap;margin-top:5px}
details.dp{margin-bottom:8px;border:1px solid var(--line);border-radius:8px;background:var(--card2)}
details.dp>summary{cursor:pointer;padding:7px 11px;font-size:11.5px;color:var(--acc);outline:none}
.dpbody{padding:0 11px 10px}
pre{white-space:pre-wrap;word-break:break-word;font-size:11px;color:var(--dim);margin:0;
max-height:320px;overflow:auto}
.mdt td,.mdt th{font-size:12px}
.filters{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin-bottom:7px;font-size:11.5px;color:var(--dim)}
select{font:inherit;font-size:11.5px;background:#1b2230;color:var(--fg);border:1px solid var(--line);
border-radius:6px;padding:2px 4px;max-width:170px}
.panel{border:1px solid var(--acc);border-radius:8px;padding:9px 11px;background:#101620;margin-bottom:9px}
.panel .ph{display:flex;justify-content:space-between;gap:8px;margin-bottom:5px;font-size:12px}
.kv{display:grid;grid-template-columns:96px 1fr;gap:2px 8px;font-size:11.5px}
.kv .k{color:var(--dim)}
.kv .val{word-break:break-all;white-space:pre-wrap;font-family:ui-monospace,Menlo,monospace;font-size:11px}
code{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:var(--warn)}
h3,h4,h5{font-size:12px;margin:9px 0 4px;color:var(--fg)}
p{margin:3px 0;font-size:12px;color:var(--dim);word-break:break-word}
ul{margin:3px 0;padding-left:18px}li{font-size:12px;color:var(--dim);margin:2px 0}
footer{color:var(--dim);font-size:10.5px;margin-top:12px;line-height:1.6}
@media (max-width:760px){
 .duo{grid-template-columns:1fr}
 .wrap{padding:9px 9px 34px}
 table{font-size:12px}
 th,td{padding:3px 4px}
 td.tm{width:62px;font-size:10.5px}
 .opt{display:none}
}
@media (max-width:420px){
 .stats{grid-template-columns:repeat(2,1fr)}
 h1{font-size:15px}
 .stat b.v{font-size:19px}
 .kv{grid-template-columns:74px 1fr}
}
"""

JS = """
<script>
(function(){
var LS=window.localStorage,K='fg.pause';
var paused=LS.getItem(K)==='1',cd=%d,pb=document.getElementById('pause'),el=document.getElementById('cd');
function paint(){pb.textContent=paused?'\\u25b6 \\u6062\\u590d\\u5237\\u65b0':'\\u23f8 \\u6682\\u505c\\u5237\\u65b0';
 pb.className=paused?'on':'';el.textContent=paused?'\\u4e0d\\u5237\\u65b0 (\\u770b\\u7ec6\\u8282\\u65f6\\u4e0d\\u8df3)':cd+'s';}
paint();
pb.addEventListener('click',function(){paused=!paused;LS.setItem(K,paused?'1':'0');cd=%d;paint();});
setInterval(function(){if(paused)return;cd--;if(cd<=0){location.reload();return;}el.textContent=cd+'s';},1000);
var ds=document.querySelectorAll('details[data-k]');
for(var i=0;i<ds.length;i++)(function(d){var k='fg.fold.'+d.getAttribute('data-k'),v=LS.getItem(k);
 if(v!==null)d.open=(v==='1');
 d.addEventListener('toggle',function(){LS.setItem(k,d.open?'1':'0')});})(ds[i]);
function esc(s){return String(s==null?'-':s).replace(/[&<>]/g,function(c){
 return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]});}
document.addEventListener('click',function(ev){
 var t=ev.target;if(!t||!t.getAttribute)return;
 var cp=t.getAttribute('data-copy');if(cp){copy(cp,t);return;}
 var cid=t.getAttribute('data-card');if(cid){show(cid);return;}
});
function copy(v,btn){var old=btn.textContent,ok=false;
 function done(){btn.textContent='\\u5df2\\u590d\\u5236';setTimeout(function(){btn.textContent=old;},1200);}
 function fb(){var ta=document.createElement('textarea');ta.value=v;ta.style.position='fixed';ta.style.opacity='0';
  document.body.appendChild(ta);ta.select();try{document.execCommand('copy');ok=true;}catch(e){}
  document.body.removeChild(ta);if(ok)done();else{btn.textContent='\\u624b\\u52a8\\u590d\\u5236';}}
 if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(v).then(done,fb);}else fb();}
var box=document.getElementById('cardload');
var FLD=['id','state','owner','line','prio','title','cmd','cwd','deliverable','rc','ok_rc','error_class',
 'failure','accept','why','note','created_at','claimed_at','finished_at','receipt','evidence','verdict'];
function show(id){
 box.hidden=false;
 box.innerHTML='<div class="panel"><div class="ph"><b>'+esc(id)+'</b><span class="px">\\u8bfb\\u53d6\\u961f\\u5217\\u539f\\u6587\\u2026</span></div></div>';
 box.scrollIntoView({block:'nearest'});
 fetch('/api/card?id='+encodeURIComponent(id)).then(function(r){return r.json();}).then(function(d){
  var h='<div class="panel"><div class="ph"><b>'+esc(d.id||id)+'</b><span class="px">PRODUCTION-QUEUE.jsonl \\u539f\\u6587 \\u00b7 \\u53ea\\u8bfb</span></div><div class="kv">';
  for(var i=0;i<FLD.length;i++){var k=FLD[i];if(!(k in d))continue;var v=d[k];
   if(v===null||v===''||(typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===0))v='-';
   if(typeof v==='object')v=JSON.stringify(v);
   h+='<div class="k">'+esc(k)+'</div><div class="val">'+esc(v)+'</div>';}
  if(d._missing)h+='<div class="k">\\u8bf4\\u660e</div><div class="val">'+esc(d._missing)+'</div>';
  h+='</div></div>';box.innerHTML=h;
 }).catch(function(e){box.innerHTML='<div class="panel"><b>'+esc(id)+'</b> \\u8bfb\\u53d6\\u5931\\u8d25\\uff1a'+esc(e)+'</div>';});}
var st={line:'',owner:'',fail:false};
try{var sv=LS.getItem('fg.filter');if(sv)st=JSON.parse(sv)||st;}catch(e){}
var sl=document.getElementById('fline'),so=document.getElementById('fowner'),
 f3=document.getElementById('ffail'),fc=document.getElementById('fcount');
function apply(){var n=0,rows=document.querySelectorAll('tr[data-fx]');
 for(var i=0;i<rows.length;i++){var r=rows[i],a=r.getAttribute('data-line'),b=r.getAttribute('data-owner');
  var ok=(!st.line||a===st.line)&&(!st.owner||b===st.owner)&&(!st.fail||r.getAttribute('data-fail')==='1');
  r.style.display=ok?'':'none';if(ok)n++;}
 fc.textContent=n+' \\u884c\\u663e\\u793a';LS.setItem('fg.filter',JSON.stringify(st));}
sl.value=st.line;so.value=st.owner;f3.className=st.fail?'on':'';
sl.addEventListener('change',function(){st.line=sl.value;apply();});
so.addEventListener('change',function(){st.owner=so.value;apply();});
f3.addEventListener('click',function(){st.fail=!st.fail;f3.className=st.fail?'on':'';apply();});
apply();
})();
</script>
"""



_GPU_CACHE = {"ts": 0, "v": -1}


def _gpu():
    import subprocess
    now = time.time()
    if now - _GPU_CACHE["ts"] < 5:
        return _GPU_CACHE["v"]
    try:
        o = subprocess.run(["ioreg", "-r", "-d", "1", "-w", "0", "-c", "IOAccelerator"],
                           capture_output=True, text=True, timeout=3).stdout
        m = re.search(r'"Device Utilization %"=(\d+)', o)
        v = int(m.group(1)) if m else -1
    except Exception:
        v = -1
    _GPU_CACHE.update({"ts": now, "v": v})
    return v


def _jload(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def live_payload():
    now = time.time()
    def age(p):
        try:
            return round(now - os.path.getmtime(p))
        except OSError:
            return None
    pulse = _jload(os.path.join(F, "dispatcher", "PULSE.json"))
    sync = _jload(os.path.join(ST, "state-sync.json"))
    pat = _jload(os.path.join(ST, "patrol-local.json"))
    ana = _jload(os.path.join(ST, "local-analyst.json"))
    sw = _jload(os.path.join(ST, "selfwatch.json"))
    ob = _jload(os.path.join(ST, "output-board.json"))
    qs = {}
    try:
        for line in open(os.path.join(F, "PRODUCTION-QUEUE.jsonl"), encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                qs[d.get("state")] = qs.get(d.get("state"), 0) + 1
    except OSError:
        pass
    models = []
    try:
        ps = json.loads(urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=3).read())
        models = [(m.get("name"), round(m.get("size_vram", 0) / 1e9, 1)) for m in ps.get("models", [])]
    except Exception:
        pass
    verdicts = [(s.get("domain"), (s.get("result") or {}).get("verdict"))
                for s in (pat.get("seats") or [])]
    digest = 0
    try:
        digest = sum(1 for _ in open(os.path.join(ST, "local-digest.jsonl"), encoding="utf-8"))
    except OSError:
        pass
    import subprocess
    try:
        sw_mb = re.search(r"used = ([0-9.]+)M",
                          subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True,
                                         text=True, timeout=3).stdout)
        sw_mb = float(sw_mb.group(1)) if sw_mb else -1
    except Exception:
        sw_mb = -1
    return {
        "ts": time.strftime("%H:%M:%S"),
        "pulse_age": age(os.path.join(F, "dispatcher", "PULSE.json")),
        "pulse_sec": pulse.get("sec"), "pulse_git": pulse.get("git"),
        "sync_age": round(now - float(sync.get("ok_ts") or 0)) if sync.get("ok_ts") else None,
        "queue": qs, "models": models, "gpu": _gpu(), "swap_mb": sw_mb,
        "digest": digest, "patrol": verdicts,
        "analyst_age": age(os.path.join(ST, "local-analyst.json")),
        "analyst_text": (ana.get("text") or "")[:160],
        "stale": sw.get("stale") or [], "healed": sw.get("healed") or [],
        "output": {"product": ob.get("product"), "infra": ob.get("infra"),
                   "missing": ob.get("missing")},
    }


def page():
    pg = _json(os.path.join(ST, "progress.json"), {}) or {}
    fs = _json(os.path.join(ST, "fleet-status.json"), {}) or {}
    sk = _json(os.path.join(ST, "soak-summary.json"), {}) or {}
    un = _json(os.path.join(ST, "unlocks.json"), {}) or {}
    screen_md = _read(os.path.join(F, "MASTER-SCREEN.md"))
    decisions_md = _read(os.path.join(F, "DECISIONS.md"))
    progress_md = _read(os.path.join(F, "PROGRESS.md"))

    now = time.time()
    pg_ts = str(pg.get("ts") or "")
    _, pg_ep = fmt_at(pg_ts)
    pg_age = dur(now - pg_ep) + " 前" if pg_ep else "-"

    # ---- 总体状态（24h 探针）
    verdict = str(sk.get("verdict") or "-")
    vkind = "ok" if verdict == "GREEN" else ("bad" if verdict == "RED" else "idle")
    vtxt = {"GREEN": "达标", "RED": "未达标"}.get(verdict, "未跑")
    green = sk.get("green_pct")
    samples = int(sk.get("samples") or 0)

    # ---- 一级：需要 CEO 的（unlocks.waiting，物理件）
    wait = un.get("waiting") or []
    need_rows = []
    for x in wait[:3]:
        need_rows.append(
            '<li class="ceo-item"><span class="cx">%s</span> '
            '<b class="cx">%s</b> <span class="cx" style="color:var(--dim)">%s</span></li>'
            % (esc(x.get("id") or "-"), esc(x.get("line") or "-"),
               esc(x.get("waiting_on") or "-")))
    if not need_rows:
        need_rows.append('<li class="ceo-item cx" style="color:var(--dim)">'
                         '没有需要你决策的事（state/unlocks.json waiting 为空）</li>')
    more = len(wait) - len(wait[:3])
    need_more = ('<div class="legend"><span>另有 %d 条等 CEO 的件，见下方「逐条解锁件」</span></div>'
                 % more) if more > 0 else ""

    # ---- 二级：四线（MASTER-SCREEN 表格，取第一张表）
    tl = md_tables(screen_md)
    lane_rows = ""
    if tl:
        rows = tl[0]
        head, body = rows[0], rows[1:]
        lane_rows = "".join(
            '<tr class="lrow"><td>%s</td><td>%s</td><td class="opt">%s</td><td class="opt">%s</td>'
            '<td>%s</td></tr>' % tuple(
                [inline(c) for c in (r + ["-"] * len(head))[:5]])
            for r in body)
        lane_head = "".join("<th>%s</th>" % inline(c) for c in head[:5])
    else:
        lane_head = "<th>线</th>"
        lane_rows = '<tr class="lrow"><td colspan="5">-</td></tr>'
    # 四线在跑卡数（progress.running 里按 line 统计）
    run_by_line = {}
    for r in (pg.get("running") or []):
        run_by_line[str(r.get("line") or "-")] = run_by_line.get(str(r.get("line") or "-"), 0) + 1

    # ---- 二级：机队
    nodes = ["bm-a", "bm-b", "bm-c", "bm-d", "bm-m"]
    fnodes = fs.get("nodes") or {}
    planes = pg.get("lanes") or {}
    workers = fs.get("workers") or {}
    wlast = pg.get("worker_last_output_h") or {}
    slots = fs.get("slots") or {}
    SMAP = {"IDLE": ("idle", "空闲"), "RUNNING": ("ok", "在跑"), "FAILED": ("bad", "失败"),
            "NO-HEARTBEAT": ("bad", "无心跳"), "DONE": ("ok", "完成")}
    fleet_rows = ""
    for nm in nodes:
        N = fnodes.get(nm) or {}
        L = planes.get(nm) or {}
        state = N.get("state") or L.get("state")
        job = N.get("job") or L.get("job")
        age = N.get("age_s")
        if age is None:
            age = L.get("age_s")
        h = (workers.get(nm) or {}).get("last_output_h")
        if h is None:
            h = wlast.get(nm)
        sl_ = slots.get(nm) or {}
        kind, txt = SMAP.get(state, ("warn", state)) if state else ("idle", "-")
        fleet_rows += (
            '<tr class="frow" data-line="" data-owner="%s">'
            '<td><b>%s</b></td>'
            '<td>%s</td>'
            '<td>%s%s</td>'
            '<td>%s</td>'
            '<td>%s</td>'
            '<td class="opt">%s</td></tr>') % (
            esc(nm), esc(nm),
            (chip(kind, txt, "fleet-status.json: nodes.%s.state / progress.json: lanes.%s.state" % (nm, nm))
             if state else
             '<span style="color:var(--dim)" title="fleet-status.json nodes 与 progress.json lanes 都没有该机心跳件（unlocks U-BMD=bm-d 入网）">-</span>'),
            cardbtn(job) if job else '<span style="color:var(--dim)">-</span>',
            copybtn(job) if job else "",
            dur(age),
            ('<span%s>%.1fh 前</span>' % (
                ' style="color:var(--warn)" title="fleet-status.json workers[].verdict=STALE-WORKER"'
                if (workers.get(nm) or {}).get("verdict") == "STALE-WORKER" else "", h))
            if h is not None else
            '<span style="color:var(--dim)" title="fleet-status.json workers 与 progress.json worker_last_output_h 都没有该机记录">-</span>',
            ("%s/%s 槽" % (sl_.get("running", "-"), sl_.get("slots", "-"))) if sl_ else "-")
    fs_verdict = str(fs.get("verdict") or "-")
    fs_kind = "ok" if fs_verdict == "GREEN" else ("bad" if fs_verdict == "RED" else "idle")

    # ---- 最近动作（完成/失败/远端回执/释放），全量
    ev = []
    for r in (pg.get("recent_done") or []):
        t, ep = fmt_at(r.get("at"))
        ev.append({"ep": ep or 0, "time": t, "kind": "完成", "dot": "ok", "id": r.get("id") or "-",
                   "owner": r.get("owner") or "-", "line": r.get("line") or "",
                   "fail": False,
                   "text": "%s → %s" % (r.get("owner") or "-",
                                        (r.get("deliverable") or "-").split("/")[-1])})
    for r in (pg.get("recent_failed") or []):
        t, ep = fmt_at(r.get("at"))
        rc = r.get("rc")
        txt = "rc=%s %s %s" % ("-" if rc is None else rc, r.get("error_class") or "",
                               (r.get("failure") or "").replace("\n", " ")[:90]
                               or "（队列该行无 failure 原文）")
        ev.append({"ep": ep or 0, "time": t, "kind": "失败", "dot": "bad", "id": r.get("id") or "-",
                   "owner": r.get("owner") or "-", "line": r.get("line") or "",
                   "fail": True, "text": txt})
    for r in (pg.get("remote_receipts") or []):
        ag = r.get("age_s")
        rc = r.get("rc")
        fail = rc not in (0, "0", None)
        ev.append({"ep": now - (ag or 0), "time": dur(ag) + " 前", "kind": "远端回执",
                   "dot": "bad" if fail else "ok", "id": r.get("file") or "-",
                   "owner": "-", "line": "", "fail": fail,
                   "text": "rc=%s %s %s" % ("-" if rc is None else rc, r.get("error_class") or "",
                                            (r.get("stderr_tail") or "").replace("\n", " ")[:70]
                                            or "（无 stderr 尾巴）")})
    for r in (pg.get("recent_released") or []):
        ev.append({"ep": 0, "time": "-", "kind": "释放", "dot": "warn", "id": r.get("id") or "-",
                   "owner": r.get("by") or "-", "line": "", "fail": False,
                   "text": str(r.get("why") or "-")})
    ev.sort(key=lambda x: x["ep"], reverse=True)

    def evrow(e, fx):
        dl = ' data-line="%s"' % esc(e["line"]) if e["line"] else ""
        do = ' data-owner="%s"' % esc(e["owner"]) if e["owner"] and e["owner"] != "-" else ""
        return ('<tr class="ev row"%s%s%s data-fail="%s">'
                '<td class="tm">%s</td><td>%s</td><td>%s</td><td>%s</td></tr>') % (
            ' data-fx="1"' if fx else "", dl, do,
            "1" if e["fail"] else "0", esc(e["time"]), chip(e["dot"], e["kind"]),
            cardbtn(e["id"]), esc(e["text"]))

    ev_top = "".join(evrow(e, False) for e in ev[:3]) or \
        '<tr class="ev row"><td colspan="4" style="color:var(--dim)">最近没有可展示的动作</td></tr>'
    ev_all = "".join(evrow(e, True) for e in ev[:40])

    # ---- 三级：逐卡明细（fleet-status.cards + 待派/在跑队列卡）
    q = qidx()
    cards, seen = [], set()
    for c in (fs.get("cards") or []):
        cid = str(c.get("id") or "-")
        seen.add(cid)
        qd = q.get(cid) or {}
        cards.append({
            "id": cid, "line": qd.get("line") or c.get("line") or "-",
            "owner": qd.get("owner") or c.get("owner") or "-",
            "verdict": c.get("verdict") or c.get("state") or "-",
            "bytes": c.get("deliverable_bytes"), "hb": c.get("heartbeat_age_s"),
            "dl": qd.get("deliverable") or "-", "claimed": c.get("claimed_at") or qd.get("claimed_at"),
            "fail": str(c.get("verdict") or "").upper() in ("NO-HEARTBEAT", "FAILED", "STALE")})
    for cid, d in q.items():
        if d.get("state") in ("OPEN", "RUNNING") and cid not in seen:
            seen.add(cid)
            cards.append({
                "id": cid, "line": d.get("line") or "-", "owner": d.get("owner") or "-",
                "verdict": "待派" if d.get("state") == "OPEN" else "在跑",
                "bytes": None, "hb": None, "dl": d.get("deliverable") or "-",
                "claimed": d.get("claimed_at") or d.get("created_at"),
                "fail": d.get("state") == "FAILED"})
    card_rows = ""
    for c in cards:
        card_rows += (
            '<tr class="crow row" data-fx="1" data-line="%s" data-owner="%s" data-fail="%s">'
            '<td>%s%s</td><td>%s</td><td>%s</td><td>%s</td><td class="opt">%s</td><td class="opt">%s</td><td>%s</td></tr>') % (
            esc(c["line"]), esc(c["owner"]), "1" if c["fail"] else "0",
            cardbtn(c["id"]), copybtn(c["id"]), esc(c["line"]), esc(c["owner"]),
            esc(c["verdict"]),
            ("%s B" % c["bytes"]) if c["bytes"] is not None else "-",
            dur(c["hb"]),
            "%s<br><span style=\"color:var(--dim)\">%s</span>" % (
                esc(c["dl"] or "-"), esc((c["claimed"] or "-")[5:16])))
    card_rows = card_rows or '<tr class="crow row"><td colspan="7" style="color:var(--dim)">无卡片</td></tr>'

    # 筛选下拉的取值（来自页面已有数据，不编）
    lines = sorted({c["line"] for c in cards if c["line"] and c["line"] != "-"} |
                   {e["line"] for e in ev if e["line"]})
    owners = sorted({c["owner"] for c in cards if c["owner"] and c["owner"] != "-"} |
                    {e["owner"] for e in ev if e["owner"] and e["owner"] != "-"})
    line_opts = "".join('<option value="%s">%s</option>' % (esc(x), esc(x)) for x in lines)
    owner_opts = "".join('<option value="%s">%s</option>' % (esc(x), esc(x)) for x in owners)

    # ---- 原始回执 / 释放
    rc_rows = ""
    for r in (pg.get("receipts") or []):
        rc_rows += ('<tr><td>%s</td><td>%s</td><td>rc=%s %s</td><td>%s</td></tr>' % (
            esc(r.get("file") or "-"), esc(r.get("node") or "-"),
            "-" if r.get("rc") is None else esc(r.get("rc")),
            esc(r.get("error_class") or ""), dur(r.get("age_s")) + " 前"))
    for r in (pg.get("remote_receipts") or []):
        rc_rows += ('<tr><td>%s（远端）</td><td>%s</td><td>rc=%s %s</td><td>%s</td></tr>' % (
            esc(r.get("file") or "-"), esc(r.get("state") or "-"),
            "-" if r.get("rc") is None else esc(r.get("rc")),
            esc(r.get("error_class") or ""), dur(r.get("age_s")) + " 前"))
    for r in (pg.get("recent_released") or []):
        rc_rows += ('<tr><td>%s（释放）</td><td>%s</td><td>%s</td><td>-</td></tr>' % (
            esc(r.get("id") or "-"), esc(r.get("by") or "-"), esc(r.get("why") or "-")))
    rc_rows = rc_rows or '<tr><td colspan="4" style="color:var(--dim)">无回执记录</td></tr>'

    # 待派卡队列原文
    _op = [c["id"] for c in cards if c["verdict"] == "待派"]
    open_cnt = len(_op)
    _chunks = []
    for _cid in _op[:3]:
        _raw = json.dumps(q.get(_cid) or {}, ensure_ascii=False)
        _chunks.append(_raw[:500] + ("" if len(_raw) <= 500 else
                                     "\u2026\uff08\u622a\u65ad\uff0c\u5168\u6587 GET /api/card?id="
                                     + _cid + "\uff09"))
    open_lines = "\n".join(_chunks)

    # 解锁件全部
    unlock_rows = "".join(
        '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            esc(x.get("id") or "-"), esc(x.get("line") or "-"),
            esc(x.get("waiting_on") or "-"),
            "已触发" if x.get("triggered") else "等 CEO")
        for x in wait) or '<tr><td colspan="4" style="color:var(--dim)">无</td></tr>'

    prework = un.get("prework_ready") or []
    prework_txt = "、".join(esc(x) for x in prework) if prework else "-"

    # 最重要的一件事（MASTER-SCREEN 里的一行）
    m = re.search(r"最重要的一件事\**[：:]\s*(.+)", screen_md or "")
    top1 = inline(m.group(1).strip()) if m else "-"

    t_render = time.strftime("%H:%M:%S")
    running = len(pg.get("running") or [])
    claimed_only = len(pg.get("claimed_not_running") or [])
    open_n = int(pg.get("open") or 0)
    dead = int(fs.get("dead") or 0)

    P = []
    P.append('<!doctype html><html lang="zh"><head><meta charset="utf-8">')
    P.append('<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">')
    P.append('<title>FluxGroup 主控台</title><style>%s</style></head><body><div class="wrap">' % CSS)
    P.append('<div id="screen1">')

    # 头部：总体状态 + 刷新控制
    P.append('<header><div class="hrow"><h1>FluxGroup 主控台</h1><div class="hctl">')
    slo = (sk.get("slo") or {})
    slo_min = slo.get("green_pct_min")
    wfull = bool(sk.get("window_complete"))
    P.append('<span class="chin">%s</span>' % chip(
        vkind, "总体 %s %s（最近一次探针）" % (verdict, vtxt),
        "state/soak-summary.json verdict = 最近一次采样的判定，不是 24h 汇总"))
    if green is not None:
        ok24 = (slo_min is not None and float(green) >= float(slo_min))
        P.append('<span class="chin">%s</span>' % chip(
            "ok" if ok24 else "bad",
            "24h %s%% 绿 / SLO %s%%%s" % ("%.1f" % green,
                                          ("%.1f" % float(slo_min)) if slo_min is not None else "-",
                                          "" if wfull else "（窗口未满）"),
            "state/soak-summary.json green_pct vs slo.green_pct_min"))
    P.append('<span>数据 %s · %s</span>' % (esc(pg_ts[11:19] or "-"), esc(pg_age)))
    P.append('<span>渲染 %s</span>' % t_render)
    P.append('<button id="pause" type="button">⏸ 暂停刷新</button>')
    P.append('<span id="cd">%ds</span>' % REFRESH_S)
    P.append('</div></div>')
    P.append('<div class="one"><span class="k">最重要的</span>%s</div>' % top1)
    P.append('</header>')

    # ① 需要 CEO（一级）
    P.append('<section data-blk="ceo"%s><h2>① 需要你决定'
             '<span class="sub">一级 · %d 条等 CEO 的物理件（state/unlocks.json）</span></h2>'
             '<ul style="margin:0;padding-left:16px">%s</ul>%s</section>'
             % (' class="need"' if wait else "", len(wait), "".join(need_rows), need_more))

    # ② 数字条
    P.append('<div class="stats" data-blk="stats">')
    P.append('<div class="stat">%s<span class="u">在跑（队列 RUNNING）</span></div>'
             % n(running, "张", f="running", src="progress.json"))
    P.append('<div class="stat">%s<span class="u">待派（队列 OPEN）</span></div>'
             % n(open_n, "张", f="open", src="progress.json"))
    P.append('<div class="stat">%s<span class="u">死卡（fleet-status 判定）</span></div>'
             % n(dead, "张", f="dead", src="fleet-status.json"))
    reds = sk.get("red") or []
    red_by = sk.get("red_by_probe") or {}
    need_n = int(((sk.get("slo") or {}).get("samples_needed") or 0))
    P.append('<div class="stat">%s<span class="u">24h 探针绿 · '
             '<span data-f="samples">%d</span> 采样%s</span>%s</div>'
             % (n("%.1f" % green if green is not None else "-", "%", f="green",
                  src="soak-summary.json"), samples,
                  ("（窗口 %d/%d）" % (samples, need_n)) if need_n else "",
                  ('<span class="u" title="soak-summary.json red_by_probe 计数">红探针 %s</span>'
                   % esc("、".join("%s×%s" % (k, red_by.get(k, "-")) for k in reds)))
                  if reds else ('<span class="u">无红探针 · 比 SLO %s%% 差 %s 个点</span>'
                                % ("%.1f" % float(slo_min),
                                   "%.1f" % (float(slo_min) - float(green)))
                                if (slo_min is not None and green is not None
                                    and float(green) < float(slo_min))
                                else '<span class="u">无红探针</span>')))
    P.append('</div>')

    # 二级：四线 + 机队（宽屏并排，节省首屏高度）
    P.append('<div class="duo">')
    P.append('<section data-blk="lanes"><h2>② 四线<span class="sub">MASTER-SCREEN.md 原表</span></h2>'
             '<table><tr>%s</tr>%s</table>'
             '<div class="legend">四线在跑卡：%s</div></section>'
             % (lane_head, lane_rows,
                esc("、".join("%s=%d 张" % (k, v) for k, v in sorted(run_by_line.items())) or "全部 0 张")))
    P.append('<section data-blk="fleet"><h2>③ 机队%s<span class="sub">最后产出=fleet-status workers.last_output_h</span></h2>'
             '<table><tr><th>机器</th><th>状态</th><th>在跑卡</th><th>心跳龄</th><th>最后产出</th>'
             '<th class="opt">槽位</th></tr>%s</table>'
             '<div class="legend">假忙 %s 张 · 机队自报在跑 %s 张 · 队列未收口 %s 张 · 已释放 %s 张'
             '（口径：fleet-status.json fake_busy/running_total/open_total/released）</div></section>'
             % (chip(fs_kind, "机队 %s" % fs_verdict), fleet_rows,
                esc(fs.get("fake_busy", "-")), esc(fs.get("running_total", "-")),
                esc(fs.get("open_total", "-")), esc(fs.get("released", "-"))))
    P.append('</div>')

    # 二级：最近动作
    P.append('<section data-blk="events"><h2>④ 推进（最近 3 条动作）'
             '<span class="sub">全量 %d 条见三级折叠</span></h2>'
             '<table><tr><th>时间</th><th>类型</th><th>卡</th><th>结果</th></tr>%s</table>'
             '<div class="legend" data-legend="1">状态色：%s %s %s %s</div></section>'
             % (len(ev), ev_top,
                chip("ok", "绿=完成/达标"), chip("bad", "红=失败/不达标"),
                chip("idle", "灰=空闲/无记录"), chip("warn", "黄=释放/告警")))

    P.append('</div>')  # /screen1

    # ---------------- 三级：折叠区
    P.append('<div id="cardload" hidden></div>')
    P.append('<div id="deep" data-blk="deep">')

    P.append('<div class="filters" data-filter="bar">筛选（纯前端，不改数据；作用于下方「逐卡明细」与「全部动作」两张表）：'
             '<label>线 <select id="fline" data-filter="line"><option value="">全部线</option>%s</select></label>'
             '<label>机器 <select id="fowner" data-filter="owner"><option value="">全部机器</option>%s</select></label>'
             '<button id="ffail" type="button" data-filter="fail">只看失败</button>'
             '<span id="fcount">-</span></div>' % (line_opts, owner_opts))

    P.append('<details class="dp" data-k="cards"><summary>逐卡明细（死卡判定 + 待派 + 在跑）· %d 张</summary>'
             '<div class="dpbody"><table><tr><th>卡</th><th>线</th><th>机</th><th>判定</th>'
             '<th>产物</th><th>心跳龄</th><th>交付物 / 领取</th></tr>%s</table>'
             '<div class="legend">判定口径：fleet-status.json cards[].verdict（NO-HEARTBEAT=心跳断了还在占卡）</div>'
             '</div></details>' % (len(cards), card_rows))

    P.append('<details class="dp" data-k="events"><summary>全部动作 · %d 条（完成 / 失败 / 远端回执 / 释放）</summary>'
             '<div class="dpbody"><table><tr><th>时间</th><th>类型</th><th>卡</th><th>结果</th></tr>%s</table>'
             '</div></details>' % (len(ev), ev_all))

    P.append('<details class="dp" data-k="receipts"><summary>原始回执 / 释放记录 · %d 条</summary>'
             '<div class="dpbody"><table><tr><th>文件</th><th>机器</th><th>rc / 错误类</th><th>时间</th></tr>%s</table>'
             '</div></details>' % (len((pg.get("receipts") or [])) +
                                   len((pg.get("remote_receipts") or [])) +
                                   len((pg.get("recent_released") or [])), rc_rows))

    P.append('<details class="dp" data-k="unlock"><summary>逐条解锁件（等 CEO 的物理件）· %d 条</summary>'
             '<div class="dpbody"><table><tr><th>id</th><th>线</th><th>等什么</th><th>状态</th></tr>%s</table>'
             '<div class="legend">预打底已就绪：%s</div>'
             '<div class="legend">来源：state/unlocks.json（generated %s）</div>'
             '</div></details>' % (len(wait), unlock_rows, prework_txt, esc(str(un.get("ts") or "-"))))

    if open_lines:
        P.append('<details class="dp" data-k="openq"><summary>待派卡队列原文 · %d 行（PRODUCTION-QUEUE.jsonl）</summary>'
                 '<div class="dpbody"><pre>%s</pre></div></details>' % (open_cnt, esc(open_lines)))

    P.append('<details class="dp" data-k="progress"><summary>PROGRESS.md 全文（自动事实页）</summary>'
             '<div class="dpbody">%s</div></details>' % md_html(progress_md))
    P.append('<details class="dp" data-k="decisions"><summary>DECISIONS.md 全文（分层决策）</summary>'
             '<div class="dpbody">%s</div></details>' % md_html(decisions_md))
    P.append('<details class="dp" data-k="screen"><summary>MASTER-SCREEN.md 全文（主控一屏）</summary>'
             '<div class="dpbody">%s</div></details>' % md_html(screen_md))

    P.append('<details class="dp" data-k="src"><summary>字段来源与缺失说明（A10 口径）</summary>'
             '<div class="dpbody"><table>'
             '<tr><th>区块</th><th>字段</th><th>来源文件</th></tr>'
             '<tr><td>总体状态</td><td>verdict / green_pct / samples</td><td>state/soak-summary.json</td></tr>'
             '<tr><td>需要你</td><td>waiting[].id/line/waiting_on</td><td>state/unlocks.json</td></tr>'
             '<tr><td>在跑 / 待派</td><td>running[] / open</td><td>state/progress.json</td></tr>'
             '<tr><td>死卡 / 逐卡判定</td><td>dead / cards[].verdict / heartbeat_age_s</td><td>state/fleet-status.json</td></tr>'
             '<tr><td>机队心跳龄 / 状态 / 在跑卡 / 槽位</td><td>nodes / slots</td><td>state/fleet-status.json</td></tr>'
             '<tr><td>每机最后产出</td><td>workers.last_output_h（缺则 worker_last_output_h）</td><td>state/fleet-status.json · state/progress.json</td></tr>'
             '<tr><td>四线</td><td>第一张表（线/最后真实产出/今天完成/卡点/本轮动作）</td><td>MASTER-SCREEN.md</td></tr>'
             '<tr><td>最近动作</td><td>recent_done/recent_failed/remote_receipts/recent_released</td><td>state/progress.json</td></tr>'
             '<tr><td>卡详情</td><td>该 id 的队列原始行</td><td>PRODUCTION-QUEUE.jsonl（/api/card?id=）</td></tr>'
             '<tr><td>回执</td><td>receipts[] / remote_receipts[].rc/stderr_tail</td><td>state/progress.json</td></tr>'
             '</table><div class="legend">md 原文（PROGRESS / DECISIONS / MASTER-SCREEN）逐字引用未加工，表内数字的口径以该表表头为准（如 rc 列）。</div>'
             '<div class="legend">缺失规则：字段在来源里不存在时显示 “-”，不外推、不补零。'
             'bm-d 在 nodes/slots 里没有心跳件（unlocks U-BMD=bm-d 入网），故状态与最后产出显示 “-”。</div>'
             '</div></details>')

    P.append('</div>')  # /deep

    P.append('<footer>只读页面 · 每 %ds 自动刷新（可暂停）· 数据全来自 cph4/fleet/ 盘上事实 · '
             '接口：GET / · /api/card?id= · /api/screen · /progress<br>'
             '无外部依赖（无 CDN/无外链字体），单文件直出。</footer>' % REFRESH_S)
    P.append('</div>')
    P.append(JS % (REFRESH_S, REFRESH_S))

    P.append('<section id="live"><h2>实时 <span class="sub" id="lv_ts">--</span></h2>'
             '<div id="lv"></div></section>')
    P.append('<script>(function(){var el=document.getElementById("live");'
             'var wrap=document.querySelector(".wrap");var hdr=wrap&&wrap.querySelector("header");'
             'if(hdr&&hdr.nextSibling){wrap.insertBefore(el,hdr.nextSibling)}else if(wrap){wrap.insertBefore(el,wrap.firstChild)}'
             'function esc(s){return String(s==null?"-":s)}'
             'function tick(){fetch("/api/live").then(function(r){return r.json()}).then(function(d){'
             'var q=d.queue||{};var ms=(d.models||[]).map(function(m){return m[0]+" "+m[1]+"G"}).join(" · ")||"无";'
             'var pv=(d.patrol||[]).map(function(p){return p[0]+":"+p[1]}).join(" ");'
             'document.getElementById("lv_ts").textContent=d.ts;'
             'document.getElementById("lv").innerHTML='
             '"<div class=one><span class=k>脉</span>"+esc(d.pulse_age)+"s 前 · 拍 "+esc(d.pulse_sec)+"s · git "+esc(d.pulse_git)+"</div>"'
             '+"<div class=one><span class=k>同步</span>"+esc(d.sync_age)+"s 前</div>"'
             '+"<div class=one><span class=k>队列</span>OPEN "+esc(q.OPEN||0)+" · RUN "+esc(q.RUNNING||0)+" · DONE "+esc(q.DONE||0)+"</div>"'
             '+"<div class=one><span class=k>算力</span>GPU "+esc(d.gpu)+"% · swap "+Math.round(d.swap_mb)+"MB · "+esc(ms)+"</div>"'
             '+"<div class=one><span class=k>我的活</span>回执判读 "+esc(d.digest)+" 份 · 8B研判 "+esc(d.analyst_age)+"s 前</div>"'
             '+"<div class=one><span class=k>巡视</span>"+esc(pv)+"</div>"'
             '+"<div class=one><span class=k>产出</span>产品 "+esc(d.output&&d.output.product)+" · 内部 "+esc(d.output&&d.output.infra)+" · 缺失 "+esc(d.output&&d.output.missing)+"</div>"'
             '+"<div class=one><span class=k>自愈</span>stale "+(d.stale&&d.stale.length?d.stale.join(","):"无")+"</div>";'
             '}).catch(function(){})}tick();setInterval(tick,2000)})();</script>')
    P.append('</body></html>')
    return "".join(P)


# ----------------------------------------------------------------- server
class HBase(BaseHTTPRequestHandler):
    server_version = "FluxConsole/2"

    def _send(self, body, ctype):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        path = u.path
        if path == "/api/card":
            qs = urllib.parse.parse_qs(u.query)
            cid = (qs.get("id") or [""])[0]
            d = qidx().get(cid)
            if isinstance(d, dict):
                d = dict(d)
                fs = _json(os.path.join(ST, "fleet-status.json"), {}) or {}
                for c in (fs.get("cards") or []):
                    if str(c.get("id")) == cid:
                        d["_fleet_verdict"] = c
                        break
            else:
                d = {"id": cid,
                     "_missing": "PRODUCTION-QUEUE.jsonl 里没有这个 id（它可能只出现在 "
                                 "fleet-status 判定或回执里；也可能已被归档清理）"}
            return self._send(json.dumps(d, ensure_ascii=False, indent=1),
                              "application/json; charset=utf-8")
        if path.startswith("/fleet-console.html"):
            return self._send(_read(os.path.join(ROOT, "fleet-console.html")) or "（缺失）",
                              "text/html; charset=utf-8")
        if path.startswith("/progress"):
            return self._send(_read(os.path.join(F, "PROGRESS.md")),
                              "text/plain; charset=utf-8")
        if path == "/api/live":
            return self._send(json.dumps(live_payload(), ensure_ascii=False), "application/json; charset=utf-8")
        if path.startswith("/api/screen"):
            return self._send(_read(os.path.join(F, "MASTER-SCREEN.md")),
                              "text/markdown; charset=utf-8")
        if path in ("/", "/index.html", "/console"):
            return self._send(page(), "text/html; charset=utf-8")
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        return self._send(page(), "text/html; charset=utf-8")

    def log_message(self, *a):
        pass


class H(HBase):
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--host", default=os.environ.get("CONSOLE_HOST", "127.0.0.1"))
    a = ap.parse_args()
    # 默认只绑回环；--host 可绑 tailnet IP（手机也能看，公网不可见）。
    host = getattr(a, "host", "127.0.0.1") or "127.0.0.1"
    srv = ThreadingHTTPServer((host, a.port), H)
    print("console on http://%s:%d" % (host, a.port))
    srv.serve_forever()


if __name__ == "__main__":
    main()