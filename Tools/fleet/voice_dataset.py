#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""音色数据集装配：voices/<group>/ → 授权核查 → 逐组过准入闸。

与角色线对称，但有一处**刻意不同**：本工具**不写 RIGHTS.json**。
角色是我方原创生成，授权可自证；音色语料的来源不受我方控制，
所以缺授权声明就是 BLOCKED——伪造一份 RIGHTS.json 等于绕过 SOURCES-V1 的红线。

判据（缺一即 BLOCKED）：
  1. 组目录里必须有 RIGHTS.json，且 license ∈ {own, public-domain, cc0, cc-by, licensed}
     且 real_person=true 时必须有 consent=true 与 consent_ref
  2. 交给 asset_dataset_audit --mode voice 判数量/时长/停顿密度/LRA

Exit: 0 = 至少一组过闸；3 = 一组都没过（等投料或等授权），不算工具坏。
"""

import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VOICES = os.path.join(ROOT, "media", "asset", "voices")
RECEIPTS = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
AUDIT = os.path.join(ROOT, "Tools", "fleet", "asset_dataset_audit.py")
OK_LICENSE = {"own", "public-domain", "cc0", "cc-by", "licensed"}


def check_rights(p):
    if not os.path.exists(p):
        return False, "缺 RIGHTS.json（来源不明一律不进训练）"
    try:
        r = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        return False, "RIGHTS.json 不可解析：%s" % e
    lic = str(r.get("license") or "").lower()
    if lic not in OK_LICENSE:
        return False, "license=%r 不在白名单 %s" % (r.get("license"), sorted(OK_LICENSE))
    if r.get("real_person") and not r.get("consent"):
        return False, "real_person=true 但无 consent（真人克隆一律不做）"
    if r.get("real_person") and not r.get("consent_ref"):
        return False, "real_person=true 但缺 consent_ref（口头授权不算）"
    return True, "ok:%s" % lic


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    out = a.out or os.path.join(RECEIPTS, "voice-dataset-%s.json" % time.strftime("%Y%m%d"))
    if not os.path.isdir(VOICES):
        rec = {"rc": 3, "verdict": "BLOCKED", "error_class": "E-BLOCKED-INPUT",
               "gaps": ["没有 media/asset/voices 目录"], "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("voice-dataset: BLOCKED（无 voices 目录）")
        return 3

    per, ok = [], 0
    for g in sorted(os.listdir(VOICES)):
        d = os.path.join(VOICES, g)
        if not os.path.isdir(d):
            continue
        clips = [n for n in os.listdir(d) if n.lower().endswith((".wav", ".mp3", ".flac", ".m4a"))]
        good, why = check_rights(os.path.join(d, "RIGHTS.json"))
        e = {"group": g, "clips": len(clips), "rights": why, "verdict": "SKIP"}
        if not good:
            e["gap"] = why
            per.append(e)
            continue
        if not clips:
            e["gap"] = "0 个音频片段（等投料）"
            per.append(e)
            continue
        rp = os.path.join(RECEIPTS, "voice-audit-%s.json" % g)
        try:
            p = subprocess.run([sys.executable, AUDIT, "--mode", "voice", "--dir", d, "--out", rp],
                               cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
            res = json.load(open(rp, encoding="utf-8")) if os.path.exists(rp) else {}
            e["audit"] = {"rc": p.returncode, "verdict": res.get("verdict"), "gaps": res.get("gaps")}
            e["verdict"] = "PASS" if res.get("verdict") in ("PASS", "OK") else "FAIL"
            if e["verdict"] == "PASS":
                ok += 1
        except Exception as ex:
            e["audit"] = {"error": str(ex)[:160]}
        per.append(e)

    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "rc": 0 if ok else 3,
           "verdict": "PASS" if ok else "BLOCKED",
           "error_class": None if ok else "E-BLOCKED-INPUT",
           "groups": per, "passed": ok,
           "gaps": [] if ok else ["没有任何音色组同时满足 有授权 且 有片段 且 过准入闸"]}
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("voice-dataset: passed=%d/%d -> %s" % (ok, len(per), os.path.relpath(out, ROOT)))
    for e in per:
        print("  %-20s %-5s clips=%d %s" % (e["group"], e["verdict"], e["clips"], e.get("gap") or ""))
    return rec["rc"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))