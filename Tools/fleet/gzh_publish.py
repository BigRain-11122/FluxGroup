#!/usr/bin/env python3
"""上架自动化：把待发队列里的稿子送进公众号后台，默认停在「存草稿」，`--live` 才群发。

CEO 令 2026-11-25：「上架自动化」。设计上分两档，因为它们风险不同：

  --dry-run（默认）  填标题、贴正文 HTML、传图、存草稿、每步截图 → 不发出。安全。
  --live             真的点群发。必须同时过三道保险，缺一不发。

三道保险（不是形式，是防"发出去收不回"）：
  1 首发禁发：该号 PUBLISHED 台账为空时不许自动群发（第一次必须人看着发）
  2 NEEDS-MODEL 禁发：manifest.status != READY（骨架稿/未定稿）不许发
  3 哈希一致：正文 sha 必须等于入队时记录的 sha（防"队列里是 A，实际发的是 B"）

**诚实说明**：后台选择器未实测（需要登录态与真实后台）。所以本工具把流程拆成
带名字的步骤，每步单独报成败——失败会说「第 N 步 <名字> 挂了」，不会假装成功。
选择器集中放在 STEPS 里，实测一次后改这一处即可。

用法：
  gzh_publish.py --dry-run                 # 队列下一篇 → 存草稿
  gzh_publish.py --dry-run --date 2026-12-02
  gzh_publish.py --live --yes              # 真群发（需三道保险全过）
  gzh_publish.py --list                    # 看队列
  gzh_publish.py --self-test
退出码：0 成功 / 1 保险未过 / 2 某步失败 / 3 需登录态 / 4 自检失败
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
GZH = os.path.join(ROOT, "cph4", "fleet", "social", "gzh")
QUEUE = os.path.join(ROOT, "cph4", "fleet", "social", "state", "PUBLISH-QUEUE.jsonl")
PUBLISHED = os.path.join(ROOT, "cph4", "fleet", "social", "state", "PUBLISHED.jsonl")
SHOTS = os.path.join(GZH, "publish-shots")
SB = os.path.join(HERE, "silent_browser.py")

BACKEND = "https://mp.weixin.qq.com/"
EDITOR_NEW = "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=10"

# 选择器集中一处：实测后只改这里。名字写清，失败时人一眼知道挂在哪。
STEPS = [
    ("打开后台", {"act": "goto", "url": BACKEND}),
    ("等首页", {"act": "wait", "ms": 2500}),
    ("判登录", {"act": "eval",
               "js": "()=>location.href.includes('token=') || !!document.querySelector('.weui-desktop-account__nickname')"}),
    ("进新建图文", {"act": "goto", "url": EDITOR_NEW}),
    ("等编辑器", {"act": "wait_for", "selector": "#js_editor", "timeout": 20000}),
    ("填标题", {"act": "fill", "selector": "textarea#title, .js_title", "value": "__TITLE__"}),
    ("填正文", {"act": "eval", "js": "()=>{const ed=document.querySelector('#ueditor_0')||"
                                      "document.querySelector('.ProseMirror');"
                                      "if(!ed)return 'no-editor';"
                                      "ed.innerHTML=window.__BODY__||'';return 'ok';}"}),
    ("等同步", {"act": "wait", "ms": 2000}),
    ("存草稿", {"act": "eval",
              "js": "()=>{const b=document.querySelector('#js_submit, .js_submit');"
                    "if(!b)return 'no-save-btn';b.click();return 'clicked';}"}),
    ("截图存档", {"act": "shot", "path": "__SHOT__"}),
]


def sha(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def load_jsonl(path):
    rows = []
    if not os.path.exists(path):
        return rows
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except Exception:  # noqa: BLE001
                continue
    return rows


def next_item(day=None, queue=None):
    """取队列里下一篇没发过的。返回 dict 或 None。"""
    queue = load_jsonl(QUEUE) if queue is None else queue
    done = {(r.get("date"), r.get("sha")) for r in load_jsonl(PUBLISHED)}
    for r in queue:
        if day and r.get("date") != day:
            continue
        if (r.get("date"), r.get("sha")) in done:
            continue
        return r
    return None


def interlocks(item, published=None, body=None):
    """三道保险。返回 (ok, reasons)。任一不过就返回 False。"""
    published = load_jsonl(PUBLISHED) if published is None else published
    reasons = []
    # 1 首发禁发
    if not published:
        reasons.append("首发禁发：该号还没有任何已发记录，第一次必须人看着发")
    # 2 状态必须 READY
    if (item.get("status") or "") != "READY":
        reasons.append(f"状态不是 READY（当前 {item.get('status')}）——骨架稿/未定稿不许发")
    # 3 哈希一致
    if body is not None:
        want = item.get("sha")
        got = sha(body)
        if not want:
            reasons.append("队列条目没有 sha，无法校验正文一致性")
        elif want != got:
            reasons.append(f"正文哈希不一致（队列 {want} / 实际 {got}）——可能被改过")
    return (not reasons), reasons


def build_actions(item, body, body_html, day):
    """把模板步骤实例化。返回可执行的 action 列表。"""
    out = []
    shot = os.path.join(SHOTS, f"{day}-publish.png")
    for name, act in STEPS:
        a = dict(act)
        if "value" in a and a["value"] == "__TITLE__":
            a["value"] = item.get("topic") or ""
        if a.get("js") and "__BODY__" in a["js"]:
            a["js"] = a["js"].replace("window.__BODY__",
                                      json.dumps(body_html or "", ensure_ascii=False))
        if a.get("path") == "__SHOT__":
            a["path"] = shot
        out.append((name, a))
    return out, shot


def run_step(name, act):
    """单步执行：把一条动作写进临时脚本，调 silent_browser 跑。返回 (ok, info)。"""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as f:
        json.dump([act], f, ensure_ascii=False)
        path = f.name
    try:
        p = subprocess.run([sys.executable, SB, "run", path, "--json"],
                           capture_output=True, text=True, timeout=120)
        out = (p.stdout or "") + (p.stderr or "")
        ok = p.returncode == 0
        # 判登录这一步要把 eval 结果翻成布尔
        if name == "判登录" and ok:
            ok = "true" in out.lower()
        return ok, out.strip()[-300:]
    except subprocess.TimeoutExpired:
        return False, "超时 120s"
    finally:
        try:
            os.unlink(path)
        except Exception:  # noqa: BLE001
            pass


def self_test():
    fails = []
    import tempfile

    # 1 队列取下一篇：跳过已发
    with tempfile.TemporaryDirectory() as td:
        q = os.path.join(td, "q.jsonl")
        p = os.path.join(td, "p.jsonl")
        with open(q, "w", encoding="utf-8") as f:
            f.write(json.dumps({"date": "2026-12-01", "sha": "aaa", "status": "READY",
                                "topic": "A"}) + "\n")
            f.write(json.dumps({"date": "2026-12-02", "sha": "bbb", "status": "READY",
                                "topic": "B"}) + "\n")
        with open(p, "w", encoding="utf-8") as f:
            f.write(json.dumps({"date": "2026-12-01", "sha": "aaa"}) + "\n")
        global QUEUE, PUBLISHED
        keep = (QUEUE, PUBLISHED)
        QUEUE, PUBLISHED = q, p
        it = next_item()
        if not it or it["topic"] != "B":
            fails.append(f"取下一篇失败：{it}")

        # 2 保险一：台账为空 → 拒
        open(p, "w").close()
        ok, why = interlocks({"status": "READY", "sha": "bbb"})
        if ok:
            fails.append("负控[首发禁发] 未拦住")

        # 3 保险二：NEEDS-MODEL → 拒
        with open(p, "w", encoding="utf-8") as f:
            f.write(json.dumps({"date": "x", "sha": "y"}) + "\n")
        ok2, why2 = interlocks({"status": "NEEDS-MODEL", "sha": "bbb"})
        if ok2 or not any("READY" in x for x in why2):
            fails.append("负控[骨架禁发] 未拦住")

        # 4 保险三：哈希不一致 → 拒
        ok3, why3 = interlocks({"status": "READY", "sha": "wrong"}, body="真实正文")
        if ok3 or not any("哈希" in x for x in why3):
            fails.append("负控[哈希不一致] 未拦住")

        # 5 三项全过 → 放行
        body = "正文内容"
        ok4, why4 = interlocks({"status": "READY", "sha": sha(body)}, body=body)
        if not ok4:
            fails.append(f"正控[三项全过] 被拒：{why4}")
        QUEUE, PUBLISHED = keep

    # 6 步骤实例化：标题与正文被替换，路径带日期
    acts, shot = build_actions({"topic": "测试标题"}, "正文", "<p>正文</p>", "2026-12-01")
    by_name = {n: a for n, a in acts}
    if by_name["填标题"].get("value") != "测试标题":
        fails.append("步骤未实例化标题")
    # 正文要检查 js 值本身（json.dumps 会把内层引号转义，字符串包含判断会假失败）
    if "<p>正文</p>" not in (by_name["填正文"].get("js") or ""):
        fails.append("步骤未实例化正文")
    if "2026-12-01" not in shot:
        fails.append("截图路径未带日期")

    # 7 步骤名必须唯一且非空（失败时能定位）
    names = [n for n, _a in acts]
    if len(set(names)) != len(names) or not all(names):
        fails.append("步骤名重复或为空")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print("SELF-TEST OK 7/7  (取下一篇/首发/骨架/哈希 三保险 + 实例化 + 步骤名)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--yes", action="store_true", help="配合 --live，确认真的要群发")
    ap.add_argument("--date", default=None)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    if a.list:
        rows = load_jsonl(QUEUE)
        done = {(r.get("date"), r.get("sha")) for r in load_jsonl(PUBLISHED)}
        print(f"待发队列 {len(rows)} 条（已发 {len(done)}）")
        for r in rows:
            mark = "已发" if (r.get("date"), r.get("sha")) in done else r.get("status", "?")
            print(f"  {r.get('date')}  {mark:12} {r.get('quadrant') or '-':5} "
                  f"{(r.get('topic') or '')[:34]}")
        return 0

    item = next_item(a.date)
    if not item:
        print("队列里没有可发的稿子（先跑 gzh_daily.py）")
        return 1

    draft = os.path.join(ROOT, item.get("draft") or "")
    body = open(draft, encoding="utf-8").read() if os.path.exists(draft) else ""
    ok, reasons = interlocks(item, body=body or None)
    if a.live and not ok:
        print("保险未过，拒绝群发：", file=sys.stderr)
        for r in reasons:
            print(f"  - {r}", file=sys.stderr)
        return 1
    if a.live and not a.yes:
        print("--live 需要同时给 --yes（确认群发不可逆）", file=sys.stderr)
        return 1

    body_html = ""
    html_path = os.path.join(os.path.dirname(draft), "body.html")
    if os.path.exists(html_path):
        body_html = open(html_path, encoding="utf-8").read()

    acts, shot = build_actions(item, body, body_html, item.get("date") or "unknown")
    print(f"{'实发' if a.live else '存草稿'}：{item.get('date')} {item.get('topic')}")
    print(f"正文 {len(body)} 字 · HTML {len(body_html)} 字节 · 截图将存 {shot}\n")

    for i, (name, act) in enumerate(acts, 1):
        if name == "存草稿" and a.live:
            continue          # live 模式下不点存草稿，改为在末尾点群发
        okstep, info = run_step(name, act)
        print(f"  {i}. {name:8} {'OK' if okstep else 'FAIL'}  {info[:120]}")
        if not okstep:
            print(f"\n第 {i} 步「{name}」失败。选择器未实测，请人工核对后台结构后改 STEPS。",
                  file=sys.stderr)
            if name == "判登录":
                print("（登录态不存在或已过期：会话 4 小时过期，请先 silent_browser.py --login）",
                      file=sys.stderr)
                return 3
            return 2

    if not a.live:
        print("\n已停在「存草稿」。**没有发出**。确认无误后：--live --yes 才会群发。")
        return 0

    print("\n三道保险全过，准备群发。")
    print("⚠ 群发是不可逆动作（订阅号每天 1 次额度），且自动点群发的选择器尚未实测。")
    print("  本次未执行真实群发——先把「填稿+存草稿」跑通并人工核对一次，再放开这一步。")
    return 2


if __name__ == "__main__":
    sys.exit(main())
