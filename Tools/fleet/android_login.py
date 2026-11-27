#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""android_login.py - 模拟器内自动登录（凭据只从本地 0600 文件读，绝不进对话/日志/git）。

为什么（2026-11-23 CEO「我要求本来就是自动化」）：
  手动登录一次就断链，等于把自动化的关键一环留给人。这里把登录也自动化，
  但**凭据来源必须是人可控的本机文件**：密码/验证码不经过聊天记录。

凭据文件（~/.fluxgroup/bili-device-login.json，权限 0600，仓库外）：
  {"method":"password","account":"13800000000","password":"***"}
  {"method":"sms","phone":"13800000000"}
  method=password：账号密码，**首次可能遇到滑块/验证码**，那就一次性人工。
  method=sms：手机号 + 短信验证码 —— 码在手机上没有 API，只能人工读一次。

判据（机读，不靠目测）：
  - 成功 = 界面出现首页标志（推荐/热门/我的）且登录页消失
  - 需人工 = 出现 验证码/滑块/安全验证 → rc=3，并打印"要你做什么"
  - 失败 = 登录按钮点后 30s 仍在登录页 → rc=1

用法：
  python3 Tools/fleet/android_login.py --avd acct1                 # 读默认凭据文件
  python3 Tools/fleet/android_login.py --avd acct1 --cred /path/to/x.json
  python3 Tools/fleet/android_login.py --avd acct1 --snapshot      # 成功后存快照（免再登录）
Exit: 0 已登录；3 需要人工验证码；1 失败；2 环境问题
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SDK = os.environ.get("ANDROID_HOME") or os.path.expanduser("~/android-sdk")
ADB = os.path.join(SDK, "platform-tools", "adb")
CRED_DEFAULT = os.path.expanduser("~/.fluxgroup/bili-device-login.json")
ACCOUNTS = os.path.expanduser("~/.fluxgroup/bili-accounts.json")
VAULT = os.path.expanduser("~/.fluxgroup/credentials/vault.json")
HOME_HINTS = ("推荐", "热门", "我的", "直播")
LOGIN_HINTS = ("手机号登录", "账号密码登录", "请输入手机号", "验证登录")
MANUAL_HINTS = ("验证码", "安全验证", "滑块", "行为异常", "操作频繁", "人机")


def sh(cmd, timeout=40):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           errors="replace")
        return r.returncode, (r.stdout or ""), (r.stderr or "")
    except Exception as e:
        return 1, "", str(e)


def serial_of(avd):
    home = os.path.expanduser("~/.android/avd")
    names = sorted(f[:-4] for f in os.listdir(home) if f.endswith(".ini")) if os.path.isdir(home) else []
    if avd not in names:
        return None
    return "emulator-%d" % (5554 + 2 * names.index(avd))


def ui_texts(serial):
    sh([ADB, "-s", serial, "shell", "uiautomator", "dump", "/sdcard/_lg.xml"], 40)
    tmp = "/tmp/_lg_%s.xml" % serial
    sh([ADB, "-s", serial, "pull", "/sdcard/_lg.xml", tmp], 40)
    try:
        s = open(tmp, encoding="utf-8").read()
    except Exception:
        return [], ""
    return [t.strip() for t in re.findall(r'text="([^"]+)"', s) if t.strip()], s


def tap_text(serial, text, exact=False):
    texts, raw = ui_texts(serial)
    for m in re.finditer(r'text="([^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', raw):
        t = m.group(1).strip()
        if not t:
            continue
        if (t == text) if exact else (text in t):
            x0, y0, x1, y1 = map(int, m.group(2, 3, 4, 5))
            sh([ADB, "-s", serial, "shell", "input", "tap",
                str((x0 + x1) // 2), str((y0 + y1) // 2)], 20)
            return True
    return False


def clear_field(serial, x, y, n=40):
    """先点进输入框，全选删除——否则重复运行会把旧内容和新内容叠加（实锚：密码 10 位变 12 位）。"""
    sh([ADB, "-s", serial, "shell", "input", "tap", str(x), str(y)], 20)
    time.sleep(0.4)
    sh([ADB, "-s", serial, "shell", "input", "keyevent", "123"], 10)   # MOVE_END
    for _ in range(n):
        sh([ADB, "-s", serial, "shell", "input", "keyevent", "67"], 10)  # DEL
    return True


def fill_first_input(serial, value, nth=0):
    """按 EditText 的 bounds 点一下再输入；nth 用来区分账号/密码两个框。"""
    _, raw = ui_texts(serial)
    boxes = []
    for m in re.finditer(r'class="android\.widget\.EditText"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', raw):
        boxes.append(tuple(map(int, m.group(1, 2, 3, 4))))
    if len(boxes) <= nth:
        # 兜底：Compose 页面常没有 EditText class，用"请输入…"提示定位
        for m in re.finditer(r'text="(请输入[^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', raw):
            boxes.append(tuple(map(int, m.group(2, 3, 4, 5))))
            break
    if len(boxes) <= nth:
        return False
    x0, y0, x1, y1 = boxes[nth]
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    clear_field(serial, cx, cy)          # 先清空，避免叠字
    sh([ADB, "-s", serial, "shell", "input", "tap", str(cx), str(cy)], 20)
    time.sleep(0.6)
    # @ . - 等字符要给 input text 转义
    esc = "".join(("\\" + c) if c in "@.-_:" else c for c in value)
    sh([ADB, "-s", serial, "shell", "input", "text", esc], 30)
    return True


def vault_cred(avd):
    """从凭据库取该实例的凭据；顺带返回 device_login 状态。

    为什么先看状态：库里的 rejected 是"服务端已明确拒绝"的记录，
    再拿同一个密码去撞只会把风控越撞越重（实锚 2026-11-23：第 3 次即弹点选验证）。
    """
    if not os.path.exists(VAULT):
        return None
    try:
        d = json.load(open(VAULT, encoding="utf-8"))
    except Exception:
        return None
    acc = d.get("accounts") or {}
    # 先看该实例自己的记录；它若只有 profile/mid 而没有手机号密码，不能遮住
    # 同一账号另一条（实锚 2026-11-23：acct1 空壳遮住了 acct2 的 rejected）。
    order = ["bilibili/%s" % avd] + [k for k in acc if k != "bilibili/%s" % avd]
    cand = []
    for key in order:
        e = acc.get(key)
        if not isinstance(e, dict):
            continue
        if e.get("platform") not in (None, "bilibili"):
            continue
        cand.append((key, e))
    withc = [(k, e) for k, e in cand if e.get("phone") and e.get("password")]
    pick = withc[0] if withc else (cand[0] if cand else None)
    if not pick:
        return None
    key, e = pick
    slot = e.get("device_login") or {}
    state, ev = slot.get("state", "unknown"), slot.get("evidence", "")
    # 同号任何一条被判 rejected，都按 rejected 处理（避免换 alias 绕过风控记录）
    if withc and state != "rejected":
        for k2, e2 in withc:
            s2 = e2.get("device_login") or {}
            if s2.get("state") == "rejected" and e2.get("password") == e.get("password"):
                state, ev, key = "rejected", s2.get("evidence", ""), k2
                break
    return {"key": key, "state": state, "evidence": ev,
            "account": e.get("phone") or "", "password": e.get("password") or ""}


def mark_vault(avd, state, evidence):
    """把本轮结果写回凭据库，下一轮据此决定是否还值得重试。"""
    if not os.path.exists(VAULT):
        return
    key = "bilibili/%s" % avd
    rc, _, _ = sh(["python3", os.path.join(HERE, "cred_vault.py"), "mark",
                   "--key", key, "--field", "device_login", "--state", state,
                   "--evidence", evidence[:120]], 30)
    return rc == 0


def classify(texts):
    joined = " ".join(texts)
    if any(h in joined for h in MANUAL_HINTS):
        return "manual"
    if any(h in joined for h in HOME_HINTS) and not any(h in joined for h in LOGIN_HINTS):
        return "home"
    if any(h in joined for h in LOGIN_HINTS):
        return "login"
    return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--avd", default="acct1")
    ap.add_argument("--cred", default=CRED_DEFAULT)
    ap.add_argument("--snapshot", action="store_true")
    ap.add_argument("--from-accounts", metavar="ALIAS",
                    help="从机队既有账号台账(~/.fluxgroup/bili-accounts.json)取 phone/password，不再复制密码")
    a = ap.parse_args()

    serial = serial_of(a.avd)
    if not serial:
        print("AVD 不存在: %s" % a.avd, file=sys.stderr)
        return 2
    rc, devs, _ = sh([ADB, "devices"])
    if serial not in devs:
        print("%s 未运行" % serial, file=sys.stderr)
        return 2

    texts, _ = ui_texts(serial)
    state = classify(texts)
    if state == "home":
        print("已是登录态（首页可见），无需再登")
        return 0

    # 凭据来源优先级：显式 --cred / --from-accounts ＞ 凭据库 ＞ 默认文件
    if not a.from_accounts and a.cred == CRED_DEFAULT:
        vc = vault_cred(a.avd)
        if vc and vc["state"] in ("rejected", "needs_human"):
            print("凭据库：%s 的 device_login=%s（%s）\n"
                  "不再自动重试（会加重风控）：更新密码后 cred_vault.py mark 成 ok/unknown 再跑；"
                  "或一次性人工登录后存快照（android_farm.py snapshot save）。"
                  % (vc["key"], vc["state"], (vc["evidence"] or "无证据")[:60]), file=sys.stderr)
            return 3
        if vc and vc["account"] and vc["password"]:
            cred = {"method": "password", "account": vc["account"], "password": vc["password"]}
            a._cred_ready = True
            print("凭据来源：凭据库 %s（phone 长度 %d）" % (vc["key"], len(vc["account"])))

    if a.from_accounts:
        # 复用既有台账，避免"同一份密码存两处"
        try:
            acc = json.load(open(ACCOUNTS, encoding="utf-8")).get("accounts", {})
            e = acc.get(a.from_accounts) or {}
            phone, pwd = e.get("phone"), e.get("password")
        except Exception as ex:
            print("读账号台账失败: %s" % ex, file=sys.stderr)
            return 2
        if not (phone and pwd):
            print("台账里 %s 没有 phone/password（只有 profile 的话走浏览器 cookie，不能用于设备登录）"
                  % a.from_accounts, file=sys.stderr)
            return 2
        cred = {"method": "password", "account": phone, "password": pwd}
        st = os.stat(ACCOUNTS)
        if st.st_mode & 0o077:
            print("账号台账权限过宽(%o)" % (st.st_mode & 0o777), file=sys.stderr)
            return 2
        print("凭据来源：账号台账 %s（phone 长度 %d）" % (a.from_accounts, len(phone)))
        a._cred_ready = True

    if not a.from_accounts and not getattr(a, "_cred_ready", False) and not os.path.exists(a.cred):
        print("缺凭据文件：%s\n请写入（0600，仓库外）：\n"
              '  {"method":"password","account":"手机号或账号","password":"密码"}\n'
              '  {"method":"sms","phone":"手机号"}' % a.cred, file=sys.stderr)
        return 2
    if not a.from_accounts and not getattr(a, "_cred_ready", False):
        st = os.stat(a.cred)
        if st.st_mode & 0o077:
            print("凭据文件权限过宽（%o），请 chmod 600 %s" % (st.st_mode & 0o777, a.cred),
                  file=sys.stderr)
            return 2
        cred = json.load(open(a.cred, encoding="utf-8"))
    method = (cred.get("method") or "password").lower()

    if method == "sms" and not cred.get("phone"):
        print("sms 模式缺 phone", file=sys.stderr)
        return 2
    if method == "password" and not (cred.get("account") and cred.get("password")):
        print("password 模式缺 account/password", file=sys.stderr)
        return 2

    # 1) 选登录方式
    if method == "password":
        if not tap_text(serial, "账号密码登录"):
            print("未找到「账号密码登录」入口（当前界面：%s）" % " | ".join(texts[:6]), file=sys.stderr)
            return 1
        time.sleep(1.5)
    else:
        if not tap_text(serial, "验证登录"):
            print("未找到「验证登录」入口", file=sys.stderr)
            return 1
        time.sleep(1.5)

    # 2) 填字段
    user = cred.get("account") or cred.get("phone")
    ok1 = fill_first_input(serial, user, 0)
    ok2 = True
    if method == "password":
        ok2 = fill_first_input(serial, cred["password"], 1)
    if not (ok1 and ok2):
        print("输入框定位失败（ok1=%s ok2=%s）——页面结构可能变了，先 dump 看" % (ok1, ok2),
              file=sys.stderr)
        return 1

    # 3) 勾协议（若有）
    for t in ("我已阅读并同意", "同意", "隐私政策"):
        if tap_text(serial, t):
            break
    time.sleep(0.5)

    # 4) 提交
    if not tap_text(serial, "登录"):
        print("未找到登录按钮", file=sys.stderr)
        return 1

    # 5) 判结果（最多 40s）
    for i in range(13):
        time.sleep(3)
        texts, _ = ui_texts(serial)
        state = classify(texts)
        if state == "home":
            print("登录成功（%ds）" % ((i + 1) * 3))
            if a.snapshot:
                rc, out, err = sh([os.path.join(SDK, "emulator", "emulator"), "-avd", a.avd,
                                   "-no-window", "-snapshot", "save", "logged-in"], 60)
                print("快照：%s" % ("已保存" if rc == 0 else (out + err)[:120]))
            return 0
        if state == "manual":
            mark_vault(a.avd, "needs_human", "登录页出现验证码/安全验证，必须人工过一次")
            print("需要人工一次：界面出现验证码/安全验证。请在那个窗口里完成，然后重跑本命令。",
                  file=sys.stderr)
            return 3
    mark_vault(a.avd, "rejected", "点登录后 40s 仍在登录页（密码错或风控）")
    print("超时仍在登录页（可能密码错/风控）；已写回凭据库，下一轮不再盲目重试",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
