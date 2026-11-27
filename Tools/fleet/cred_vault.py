#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cred_vault.py — 账号密码库（仓库外、0600，只给机队读）。

CEO 2026-11-23：「建立账号密码库，以后这些登陆别来烦我」。
所以这里解决的是"凭据只有一个出处"，不是"多存一份"：
- 正身只有 `~/.fluxgroup/credentials/vault.json`（0600，目录 0700）；
- **任何仓库文件不写明文**（本仓库是 Public），工具在写入前会挡住"往仓库里写"；
- 每个账号除了手机号/密码，还要记 **各通道的实测状态**（device_login / web_session），
  免得以后又有人拿一个已知失效的密码反复重试、把风控越撞越重。

状态取值：ok / rejected / needs_human / unknown
- rejected   = 服务端明确拒绝（可附证据原文）
- needs_human= 只能人工过（短信码、点选验证码）

用法：
  cred_vault.py list                                  # 掩码列出
  cred_vault.py add --platform bilibili --alias acct1 --phone 1xx --password 'x'
  cred_vault.py get --key bilibili/acct1 --field password --reveal   # 供登录工具管道读取
  cred_vault.py mark --key bilibili/acct1 --field device_login --state rejected --evidence '用户名或密码错误'
  cred_vault.py import-legacy                         # 从既有 bili-accounts.json 等导入
  cred_vault.py doctor                                # 权限/位置自检
Exit: 0 正常；2 用法/环境问题（含"试图写进仓库"）；3 找不到账号
"""
from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import time

HOME = os.path.expanduser("~")
VAULT_DIR = os.path.join(HOME, ".fluxgroup", "credentials")
VAULT = os.path.join(VAULT_DIR, "vault.json")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LEGACY = {
    "accounts": os.path.join(HOME, ".fluxgroup", "bili-accounts.json"),
    "device": os.path.join(HOME, ".fluxgroup", "bili-device-login.json"),
}
STATES = ("ok", "rejected", "needs_human", "unknown")


def die(msg, rc=2):
    print(msg, file=sys.stderr)
    sys.exit(rc)


def inside_repo(path):
    try:
        p = os.path.realpath(path)
        r = os.path.realpath(REPO)
        return os.path.commonpath([p, r]) == r
    except Exception:
        return False


def ensure_secure():
    """仓库外 + 目录 0700 + 文件 0600。任何一条不满足就拒绝写。"""
    if inside_repo(VAULT):
        die("拒绝：凭据库路径落在仓库内（%s）。本仓库对外可见，明文凭据不许入库。" % VAULT)
    os.makedirs(VAULT_DIR, exist_ok=True)
    os.chmod(VAULT_DIR, 0o700)
    if os.path.exists(VAULT):
        mode = stat.S_IMODE(os.stat(VAULT).st_mode)
        if mode & 0o077:
            os.chmod(VAULT, 0o600)


def load():
    if not os.path.exists(VAULT):
        return {"version": 1, "accounts": {}}
    with open(VAULT, encoding="utf-8") as f:
        d = json.load(f)
    d.setdefault("accounts", {})
    return d


def save(d):
    ensure_secure()
    d["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    tmp = VAULT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.chmod(tmp, 0o600)
    os.replace(tmp, VAULT)
    os.chmod(VAULT, 0o600)


def mask(v):
    if not isinstance(v, str) or not v:
        return ""
    if len(v) <= 4:
        return "*" * len(v)
    return v[:2] + "*" * (len(v) - 4) + v[-2:]


def key_of(a):
    return "%s/%s" % (a.get("platform", "?"), a.get("alias", "?"))


def cmd_list(a):
    d = load()
    if not d["accounts"]:
        print("凭据库为空：%s" % VAULT)
        return 0
    print("凭据库 %s（%d 个账号）" % (VAULT, len(d["accounts"])))
    for k in sorted(d["accounts"]):
        e = d["accounts"][k]
        dev = (e.get("device_login") or {}).get("state", "unknown")
        web = (e.get("web_session") or {}).get("state", "unknown")
        print("  %-18s phone=%-6s pwd=%-10s device=%-11s web=%s"
              % (k, mask(e.get("phone", "")), mask(e.get("password", "")), dev, web))
    return 0


def cmd_add(a):
    if not (a.phone or a.password):
        die("至少给 --phone 或 --password")
    d = load()
    k = "%s/%s" % (a.platform, a.alias)
    existed = k in d["accounts"]
    e = d["accounts"].get(k, {})
    e.update({"platform": a.platform, "alias": a.alias})
    for f in ("phone", "password", "mid", "uname", "note"):
        v = getattr(a, f, None)
        if v:
            e[f] = v
    if a.method:
        e["login_methods"] = [m.strip() for m in a.method.split(",") if m.strip()]
    e.setdefault("device_login", {"state": "unknown"})
    e.setdefault("web_session", {"state": "unknown"})
    d["accounts"][k] = e
    save(d)
    print("%s %s" % ("更新" if existed else "新增", k))
    return 0


def cmd_get(a):
    d = load()
    e = d["accounts"].get(a.key)
    if not e:
        die("找不到账号：%s" % a.key, 3)
    if a.field:
        v = e.get(a.field, "")
        if isinstance(v, (dict, list)):
            print(json.dumps(v, ensure_ascii=False))
        else:
            print(v if a.reveal else mask(v))
        return 0
    out = dict(e)
    if not a.reveal:
        for f in ("phone", "password"):
            if f in out:
                out[f] = mask(out[f])
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def cmd_mark(a):
    if a.state not in STATES:
        die("--state 只能是 %s" % "/".join(STATES))
    d = load()
    e = d["accounts"].get(a.key)
    if not e:
        die("找不到账号：%s" % a.key, 3)
    slot = e.setdefault(a.field, {})
    slot["state"] = a.state
    slot["checked_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if a.evidence:
        slot["evidence"] = a.evidence
    save(d)
    print("%s.%s = %s" % (a.key, a.field, a.state))
    return 0


def cmd_import_legacy(a):
    d = load()
    n = 0
    try:
        acc = json.load(open(LEGACY["accounts"], encoding="utf-8"))
    except Exception:
        acc = {}
    for alias, e in (acc.get("accounts") or {}).items():
        if not isinstance(e, dict) or e.get("platform") != "bilibili":
            continue
        k = "bilibili/%s" % alias
        cur = d["accounts"].get(k, {})
        for f in ("phone", "password", "mid", "uname"):
            if e.get(f) and not cur.get(f):
                cur[f] = e[f]
        cur.setdefault("platform", "bilibili")
        cur.setdefault("alias", alias)
        if e.get("profile"):
            cur["note"] = "浏览器 profile: %s" % e["profile"]
        cur.setdefault("device_login", {"state": "unknown"})
        web = cur.setdefault("web_session", {"state": "unknown"})
        if e.get("checked_at"):
            web["checked_at"] = e["checked_at"]
        d["accounts"][k] = cur
        n += 1
    try:
        dev = json.load(open(LEGACY["device"], encoding="utf-8"))
    except Exception:
        dev = {}
    if dev.get("account"):
        k = "bilibili/device"
        cur = d["accounts"].get(k, {})
        cur.setdefault("platform", "bilibili")
        cur.setdefault("alias", "device")
        cur["phone"] = cur.get("phone") or dev.get("account")
        cur["password"] = cur.get("password") or dev.get("password")
        cur.setdefault("device_login", {"state": "unknown"})
        cur.setdefault("web_session", {"state": "unknown"})
        d["accounts"][k] = cur
        n += 1
    save(d)
    print("导入 %d 条 → %s" % (n, VAULT))
    return 0


def cmd_doctor(a):
    ok = True
    print("凭据库路径：%s" % VAULT)
    print("在仓库内：%s" % ("是（危险）" if inside_repo(VAULT) else "否（正确）"))
    ok &= not inside_repo(VAULT)
    if os.path.exists(VAULT):
        mode = stat.S_IMODE(os.stat(VAULT).st_mode)
        print("文件权限：%o" % mode)
        ok &= (mode & 0o077) == 0
        print("账号数：%d" % len(load()["accounts"]))
    else:
        print("文件权限：尚未创建")
    dmode = stat.S_IMODE(os.stat(VAULT_DIR).st_mode) if os.path.isdir(VAULT_DIR) else None
    print("目录权限：%s" % ("%o" % dmode if dmode is not None else "尚未创建"))
    print("结论：%s" % ("通过" if ok else "不通过"))
    return 0 if ok else 2


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list"); p.set_defaults(fn=cmd_list)
    p = sub.add_parser("add")
    p.add_argument("--platform", required=True)
    p.add_argument("--alias", required=True)
    p.add_argument("--phone")
    p.add_argument("--password")
    p.add_argument("--mid")
    p.add_argument("--uname")
    p.add_argument("--note")
    p.add_argument("--method", help="逗号分隔，如 cookie,sms,qr")
    p.set_defaults(fn=cmd_add)
    p = sub.add_parser("get")
    p.add_argument("--key", required=True)
    p.add_argument("--field")
    p.add_argument("--reveal", action="store_true")
    p.set_defaults(fn=cmd_get)
    p = sub.add_parser("mark")
    p.add_argument("--key", required=True)
    p.add_argument("--field", required=True, help="device_login / web_session / ...")
    p.add_argument("--state", required=True)
    p.add_argument("--evidence")
    p.set_defaults(fn=cmd_mark)
    p = sub.add_parser("import-legacy"); p.set_defaults(fn=cmd_import_legacy)
    p = sub.add_parser("doctor"); p.set_defaults(fn=cmd_doctor)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
