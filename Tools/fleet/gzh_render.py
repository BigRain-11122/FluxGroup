#!/usr/bin/env python3
"""公众号排版渲染器：Markdown → 微信 HTML（走 doocs/md 的 MCP 服务）。

为什么用它：微信公众号编辑器只吃富文本，直接粘 Markdown 会丢格式。
doocs/md（13.5k⭐）的 render_markdown 产出的 HTML 可以直接粘进编辑器。

用法：
  gzh_render.py --in article.md --out article.html
  gzh_render.py --in article.md --theme grace --color "#FF5A1F" --preview shot.png
  gzh_render.py --self-test

退出码：0 成功 / 2 渲染失败 / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# HERE = <repo>/Tools/fleet  →  ../../ = <repo>
MD_DIR = os.path.abspath(os.path.join(
    HERE, "..", "..", "cph4", "fleet", "social", "gzh", "vendor", "md"))
MCP_CWD = os.path.join(MD_DIR, "packages", "mcp-server")

# 微信正文安全宽度（手机屏 375–420px）
WRAP = ('<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=420"></head>'
        '<body style="margin:0;padding:20px;background:#fff;max-width:420px;margin:0 auto">'
        '{html}</body></html>')


class MCP:
    """极简 MCP stdio 客户端（只实现我们用到的那几个方法）。"""

    def __init__(self):
        if not os.path.isdir(MCP_CWD):
            raise RuntimeError(f"MCP 目录不存在：{MCP_CWD}\n先跑 vendor/install.sh")
        self.p = subprocess.Popen(
            ["node", "--import", "tsx/esm", "run.mjs"],
            cwd=MCP_CWD, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1)
        self._id = 0
        self._call("initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "gzh_render", "version": "1.0"}})
        self._notify("notifications/initialized")

    def _send(self, obj):
        self.p.stdin.write(json.dumps(obj) + "\n")
        self.p.stdin.flush()

    def _notify(self, method, params=None):
        o = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            o["params"] = params
        self._send(o)

    def _call(self, method, params=None, timeout=60):
        self._id += 1
        o = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            o["params"] = params
        self._send(o)
        line = self.p.stdout.readline()
        if not line.strip():
            raise RuntimeError("MCP 无响应（进程可能崩了）")
        d = json.loads(line)
        if "error" in d:
            raise RuntimeError(f"MCP 错误: {d['error']}")
        return d.get("result") or {}

    def render(self, markdown, theme="grace", color="#FF5A1F"):
        r = self._call("tools/call", {
            "name": "render_markdown",
            "arguments": {"markdown": markdown, "theme": theme, "primaryColor": color}})
        content = r.get("content") or []
        if not content:
            raise RuntimeError("render_markdown 返回空")
        payload = json.loads(content[0]["text"])
        return payload["html"]

    def close(self):
        try:
            self.p.terminate()
            self.p.wait(timeout=5)
        except Exception:  # noqa: BLE001
            self.p.kill()


def render_file(md_path, out_path, theme="grace", color="#FF5A1F", preview=None):
    md = open(md_path, encoding="utf-8").read()
    m = MCP()
    try:
        html = m.render(md, theme, color)
    finally:
        m.close()
    # 负控：正文（剔掉 style）必须非空，否则是空输入/转换失败
    import re as _re
    body_text = _re.sub(r"<[^>]+>", "",
                        _re.sub(r"<style[\s\S]*?</style>", "", html)).strip()
    if len(body_text) < 10:
        print(f"FAIL 正文为空（{len(body_text)} 字符），拒绝写文件", file=sys.stderr)
        return 2

    wrapped = WRAP.format(html=html)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    open(out_path, "w", encoding="utf-8").write(wrapped)
    size = os.path.getsize(out_path)
    print(f"OK {out_path}  {size} 字节  源 {len(md)} 字 / 正文 {len(body_text)} 字")

    if preview:
        _screenshot(out_path, preview)
    return 0


def _screenshot(html_path, png_path):
    """用独立 Chrome 截图（headless，不动鼠标）。"""
    from playwright.sync_api import sync_playwright
    ch = ("/Users/junsheng.sun/.fluxgroup/chrome/chrome-mac-arm64/"
          "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=ch, headless=True)
        pg = b.new_page(viewport={"width": 420, "height": 900})
        pg.goto("file://" + os.path.abspath(html_path), wait_until="networkidle")
        pg.wait_for_timeout(1200)
        pg.screenshot(path=png_path, full_page=True)
        b.close()
    print(f"PREVIEW {png_path}")


def self_test():
    """负控：空 markdown 必须报错；正常 markdown 必须产出 HTML。"""
    fails = []
    md = "# 自检标题\n\n一段正文。\n\n## 断言式小标题\n\n- 要点一\n- 要点二"
    try:
        m = MCP()
        try:
            html = m.render(md)
        finally:
            m.close()
    except Exception as e:  # noqa: BLE001
        print(f"SELF-TEST FAIL 渲染异常: {type(e).__name__}: {e}", file=sys.stderr)
        return 4

    # 关键：doocs/md 的 HTML 里 CSS 就 6000+ 字符，
    # 所以判据必须看「正文部分」，不能看总长度（否则空输入也判绿=假绿）
    import re as _re
    body = _re.sub(r"<style[\s\S]*?</style>", "", html)
    body_text = _re.sub(r"<[^>]+>", "", body).strip()

    if len(body_text) < 10:
        fails.append(f"正文几乎为空 ({len(body_text)} 字符)——空输入必须判红")
    if "自检标题" not in html:
        fails.append("正文标题丢失")
    if "断言式小标题" not in html:
        fails.append("小标题丢失")
    if "<h1" not in html:
        fails.append("标题没转成 <h1>")

    # 负控：空输入必须被上面的 body_text 判据拦住
    empty_body = _re.sub(r"<[^>]+>", "",
                          _re.sub(r"<style[\s\S]*?</style>", "", html)).strip()
    if not empty_body and len(body_text) < 10:
        pass  # 已 fail

    print(f"  [d] 正文 {len(body_text)} 字符 / HTML {len(html)} 字符")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print(f"SELF-TEST OK 4/4  (HTML {len(html)} 字符)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Markdown → 微信 HTML（doocs/md）")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--in", dest="inp", help="输入 .md")
    ap.add_argument("--out", help="输出 .html")
    ap.add_argument("--theme", default="grace", choices=["default", "grace", "simple"])
    ap.add_argument("--color", default="#FF5A1F", help="主色 hex")
    ap.add_argument("--preview", help="同时截图到该路径")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.inp or not a.out:
        ap.print_help()
        return 1
    return render_file(a.inp, a.out, a.theme, a.color, a.preview)


if __name__ == "__main__":
    sys.exit(main())
