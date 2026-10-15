# -*- coding: utf-8 -*-
"""model-whitelist-probe.py - 机队模型白名单探针（O-20261015-1505 优化点④·防复活）

Why: 10-15 实录——CEO 令已删的 qwen2.5 旧款被消费方残留引用自动回拉复活两度
（flash 槽引用+脚本硬编码）。本探针每小时对 Ollama 清单做白名单对账：
  - 命中旧款家族模式（qwen2.5:* / qwen3-8b-ud:*）→ 自动 rm + RESURRECTED 日志行
  - 白名单外的其他款 → 不删只记 NEED-JUDGMENT（防误删合法新拉）
  - serve 未启（pause 态）→ 静默跳过
Usage: python model-whitelist-probe.py -w "qwen3:4b-instruct,bge-m3:latest"
Exit: 0=clean/skip  1=found-and-handled(删了复活件)  2=probe fault(honest)
"""
import argparse
import datetime
import json
import re
import urllib.request

LEGACY_PAT = re.compile(r"^(qwen2\.5|qwen3-8b-ud)")
LOG = r"C:\Users\sjs20\Desktop\FluxGroup\media\logs\model-whitelist-probe.log"
ALERT = r"C:\Users\sjs20\Desktop\FluxGroup\media\logs\model-whitelist-alert.json"


def ts():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def log(line):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("%s %s\n" % (ts(), line))
    print(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--whitelist", "-w", required=True,
                    help="comma-separated model tags allowed on this machine")
    a = ap.parse_args()
    allowed = {x.strip() for x in a.whitelist.split(",") if x.strip()}

    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as r:
            models = [m["name"] for m in json.loads(r.read().decode("utf-8")).get("models", [])]
    except Exception as e:
        log("SKIP serve-unreachable (%s)" % str(e)[:60])
        return 0

    extras = [m for m in models if m not in allowed]
    if not extras:
        log("CLEAN %d models all whitelisted" % len(models))
        return 0

    deleted, flagged = [], []
    for m in extras:
        if LEGACY_PAT.search(m):
            try:
                req = urllib.request.Request("http://127.0.0.1:11434/api/delete",
                                             data=json.dumps({"model": m}).encode("utf-8"),
                                             headers={"Content-Type": "application/json"},
                                             method="DELETE")
                with urllib.request.urlopen(req, timeout=60) as r:
                    r.read()
                deleted.append(m)
                log("RESURRECTED-DELETED %s (legacy family auto-rm)" % m)
            except Exception as e:
                log("WARN delete-fail %s (%s)" % (m, str(e)[:60]))
        else:
            flagged.append(m)
            log("NEED-JUDGMENT extra model not in whitelist: %s" % m)
    if deleted or flagged:
        with open(ALERT, "w", encoding="utf-8") as f:
            json.dump({"ts": ts(), "deleted": deleted, "need_judgment": flagged},
                      f, ensure_ascii=False, indent=1)
    return 1 if (deleted or flagged) else 0


if __name__ == "__main__":
    raise SystemExit(main())
