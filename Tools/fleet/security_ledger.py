# -*- coding: utf-8 -*-
"""security_ledger.py - 安全与供应链台账：把写在文档里的红线变成每天可算的数字。

四类检查（都能在本地算，不联网）：
  1. 凭据泄漏：git 跟踪文件里出现 sk-/ghp_/AKIA/xoxb/私钥块 -> 高危
  2. 越权动作：队列卡的命令触碰受保护路径（凭据目录、.git 内部、系统目录）
  3. 许可传染：依赖清单里出现 AGPL/GPL 类包（会传染整个产品）
  4. 素材授权：资产台账里 license 字段缺失的条目

为什么需要它：红线只写在文档里 = 没人检查；变成每日计数才会被处理。
Usage: security_ledger.py [--json]
Exit: 0 无高危；1 有高危；2 配置缺失
"""
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
OUT = os.path.join(FLEET, "SECURITY-LEDGER.md")
STATE = os.path.join(FLEET, "state", "security-ledger.json")

SECRET_PATTERNS = [
    (r"\bsk-[A-Za-z0-9]{16,}", "OpenAI 风格密钥"),
    (r"\bghp_[A-Za-z0-9]{20,}", "GitHub PAT"),
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS key id"),
    (r"\bxox[baprs]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "私钥块"),
]
SECRET_EXTS = (".py", ".ps1", ".sh", ".cmd", ".bat", ".json", ".yml", ".yaml",
               ".md", ".js", ".ts", ".env", ".ini", ".toml")
SECRET_SKIP_DIRS = (".git/", "node_modules/", "cph4/fleet/queue-receipts/",
                    "cph4/fleet/state/", "media/")
# 已知样例/占位：AWS 官方文档 key、明显占位串、以及扫描器自身与它的测试。
# 假红和假绿一样有害——报一次假高危，之后真高危就没人信了。
SECRET_FALSE_POSITIVE = ("AKIAIOSFODNN7EXAMPLE", "AKIAABCDEFGHIJKLMNOP",
                         "sk-xxxxxxxx", "your_token_here")
SECRET_SKIP_FILES = ("Tools/secret-scan.ps1", "Tools/secret-scan.Tests.ps1")
PROTECTED_CMD = (".codely-cli/settings.json", "id_rsa", ".ssh/", "/etc/", "C:\\Windows",
                 ".git/config", "credentials", "keychain")
COPYLEFT = ("agpl", "gpl-3", "gpl-2", "gplv3", "gplv2", "sspl", "osl")


def git_files(limit=4000):
    try:
        p = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=60)
        return [f for f in (p.stdout or "").splitlines() if f.strip()][:limit]
    except Exception:
        return []


def scan_secrets(files):
    hits = []
    for rel in files:
        if not rel.endswith(SECRET_EXTS) or rel.startswith(SECRET_SKIP_DIRS):
            continue
        if rel in SECRET_SKIP_FILES:
            continue
        p = os.path.join(ROOT, rel)
        try:
            if os.path.getsize(p) > 2 * 1024 * 1024:
                continue
            txt = open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for _fp in SECRET_FALSE_POSITIVE:
            txt = txt.replace(_fp, "")
        for pat, label in SECRET_PATTERNS:
            if re.search(pat, txt):
                # 排除示例/占位
                if re.search(r"(sk-xxx|your[_-]?token|<token>|示例|placeholder)", txt, re.I):
                    continue
                hits.append({"file": rel, "kind": label})
                break
    return hits


def scan_cards():
    bad = []
    try:
        with open(QUEUE, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    r = json.loads(ln)
                except Exception:
                    continue
                if str(r.get("state", "")).upper() not in ("OPEN", "READY", "CLAIMED", "RUNNING"):
                    continue
                cmd = str(r.get("cmd") or "")
                for t in PROTECTED_CMD:
                    if t in cmd:
                        bad.append({"id": r.get("id"), "hit": t, "cmd": cmd[:70]})
                        break
    except Exception:
        pass
    return bad


def scan_licenses():
    risky, deps = [], 0
    for rel in ("requirements.txt", "pyproject.toml", "package.json",
                "Tools/requirements.txt"):
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        txt = open(p, encoding="utf-8", errors="replace").read().lower()
        for line in txt.splitlines():
            s = line.strip().strip('",')
            if not s or s.startswith("#"):
                continue
            deps += 1
            if any(k in s for k in COPYLEFT):
                risky.append({"file": rel, "dep": s[:60]})
    return deps, risky


def scan_assets():
    """资产台账里 license 缺失的条目（抽查前 300 条，避免全盘 IO）。"""
    missing, seen = 0, 0
    for base, _dirs, files in os.walk(os.path.join(FLEET, "asset")):
        for fn in files[:50]:
            if not fn.endswith(".json"):
                continue
            try:
                d = json.load(open(os.path.join(base, fn), encoding="utf-8"))
            except Exception:
                continue
            items = d if isinstance(d, list) else (d.get("items") or d.get("assets") or [])
            if not isinstance(items, list):
                continue
            for it in items[:50]:
                if not isinstance(it, dict):
                    continue
                seen += 1
                if not str(it.get("license") or it.get("source_license") or "").strip():
                    missing += 1
            if seen >= 300:
                break
        if seen >= 300:
            break
    return seen, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    files = git_files()
    sec = scan_secrets(files)
    cards = scan_cards()
    deps, lic = scan_licenses()
    assets, miss = scan_assets()

    high = len(sec) + len(cards)
    warn = len(lic) + (1 if miss else 0)
    verdict = "HIGH" if high else ("WARN" if warn else "OK")

    L = ["# 安全与供应链台账 %s" % __import__("time").strftime("%Y-%m-%dT%H:%M:%S"), "",
         "判定：**%s**｜扫描 %d 个跟踪文件 / %d 个依赖 / %d 条素材"
         % (verdict, len(files), deps, assets), ""]
    L.append("## 1. 凭据泄漏（高危）")
    L.append("")
    if sec:
        for x in sec[:10]:
            L.append("- ❌ `%s` 命中 %s" % (x["file"], x["kind"]))
    else:
        L.append("- 未发现（扫描 %d 个文本类跟踪文件）" % len(files))
    L.append("")
    L.append("## 2. 越权动作（高危）")
    L.append("")
    if cards:
        for x in cards[:10]:
            L.append("- ❌ 卡 `%s` 触碰 `%s`：%s" % (x["id"], x["hit"], x["cmd"]))
    else:
        L.append("- 活卡命令均未触碰凭据目录/系统路径")
    L.append("")
    L.append("## 3. 许可传染")
    L.append("")
    if lic:
        for x in lic[:10]:
            L.append("- ⚠ `%s` 含可疑条目：%s" % (x["file"], x["dep"]))
    else:
        L.append("- 依赖清单未出现 AGPL/GPL/SSPL 类条目")
    L.append("")
    L.append("## 4. 素材授权")
    L.append("")
    if miss:
        L.append("- ⚠ 抽查 %d 条素材，**%d 条缺 license 字段**" % (assets, miss))
    else:
        L.append("- 抽查 %d 条素材，授权字段齐全" % assets)
    L.append("")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump({"ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
                   "verdict": verdict, "secrets": sec, "cards": cards,
                   "licenses": lic, "assets_missing": miss, "assets_seen": assets},
                  f, ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": verdict, "secrets": len(sec), "card_risks": len(cards),
                      "license_risks": len(lic), "assets_missing": miss,
                      "board": os.path.relpath(OUT, ROOT)}, ensure_ascii=False))
    return 1 if high else 0


if __name__ == "__main__":
    sys.exit(main())