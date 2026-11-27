# -*- coding: utf-8 -*-
"""Daily workflow audit collector (deterministic, zero LLM, zero network).

CEO order 2026-10-27: "这样的复盘，每天来一次".
Writes cph4/fleet/workflow-audit/AUDIT-<date>.md + .json and appends one line to
that folder's LEDGER.md. Rule-based flags map to the seven balance laws (R1..R7)
in AUDIT-20261027-workflow-director.md.

Exit 0 always (a report is the deliverable); non-zero only on hard IO failure.
"""
import io
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FG = r"C:\Fluxgroup\FluxGroup"
BM = os.path.join(FG, "quant", "bigmoney")
MV = os.path.join(FG, "cph4", "fleet", "mv-album-001-jay")
DRAMA_EPS = os.path.join(FG, "media", "drama-eps")
DRAMA_TTS = os.path.join(FG, "media", "drama-tts-out")
DRAMA_MIX = os.path.join(FG, "media", "drama-mix-out")
OUTDIR = os.path.join(FG, "cph4", "fleet", "workflow-audit")
SENTINEL_REG = r"C:\Fluxgroup\.codely-cli\sentinel\bmb-work-registry.json"
SENTINEL_LOG = r"C:\Fluxgroup\.codely-cli\sentinel\sentinel.log"
AUDIO_OUT = os.path.join(FG, "media", "drama-eps-audio")


def run(cmd, timeout=30):
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return p.stdout.decode("utf-8", "replace").strip()
    except Exception:
        return ""


def gpu_state():
    out = run(["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu",
               "--format=csv,noheader,nounits"])
    if not out:
        return None
    try:
        used, total, util = [float(x) for x in out.splitlines()[0].split(",")]
        return {"used_mb": used, "total_mb": total, "util_pct": util}
    except Exception:
        return None


def cpu_pct():
    out = run(["powershell", "-NoProfile", "-Command",
               "(Get-Counter '\\Processor(_Total)\\% Processor Time' -SampleInterval 1 -MaxSamples 1).CounterSamples[0].CookedValue"], 30)
    try:
        return round(float(out.replace(",", ".")), 1)
    except Exception:
        return None


def repo_lag(path):
    """Return (ahead, behind) for the current branch vs origin."""
    out = run(["git", "-C", path, "rev-list", "--left-right", "--count", "origin/main...HEAD"])
    try:
        left, right = [int(x) for x in out.split()]
        return right, left  # ahead, behind
    except Exception:
        return None, None


def newest_mtime(path, pattern=None):
    newest = 0.0
    for root, _d, files in os.walk(path):
        for n in files:
            if pattern and not n.lower().endswith(pattern):
                continue
            try:
                newest = max(newest, os.path.getmtime(os.path.join(root, n)))
            except OSError:
                pass
    return newest


def age_days(ts):
    if not ts:
        return None
    return round((time.time() - ts) / 86400.0, 1)


def count_files(path, pattern):
    if not os.path.isdir(path):
        return 0
    return sum(1 for n in os.listdir(path) if pattern in n and os.path.isfile(os.path.join(path, n)))


def count_ep_mp4(path):
    """Episode deliverables only: EP###.mp4 (excludes tmp_/diag_/diagfix_ leftovers)."""
    if not os.path.isdir(path):
        return 0, 0
    ep = junk = 0
    for n in os.listdir(path):
        p = os.path.join(path, n)
        if not (n.lower().endswith(".mp4") and os.path.isfile(p)):
            continue
        if n.upper().startswith("EP") and n.count("_") == 0:
            ep += 1
        else:
            junk += 1
    return ep, junk


def sentinel_state():
    st = {"open_items": None, "last_line": "", "work": None}
    try:
        raw = open(SENTINEL_REG, "rb").read().decode("utf-8-sig")
        items = json.loads(raw).get("items", [])
        st["open_items"] = sum(1 for i in items
                               if i.get("status") == "open" and i.get("lane") == "cpu-only"
                               and int(i.get("fail_count") or 0) < 2)
    except Exception:
        pass
    try:
        with open(SENTINEL_LOG, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-30:]
        for ln in reversed(lines):
            if "work=" in ln:
                st["last_line"] = ln.strip()
                for token in ln.split():
                    if token.startswith("work="):
                        st["work"] = token.split("=", 1)[1]
                break
    except Exception:
        pass
    return st


def main():
    now = datetime.now()
    gpu = gpu_state()
    cpu = cpu_pct()
    fg_ahead, fg_behind = repo_lag(FG)
    bm_ahead, bm_behind = repo_lag(BM)
    sent = sentinel_state()

    mv_last = age_days(newest_mtime(MV))
    ep_count, junk_count = count_ep_mp4(DRAMA_EPS)
    drama_eps_last = age_days(newest_mtime(DRAMA_EPS))
    tts_last = age_days(newest_mtime(DRAMA_TTS))
    mix_last = age_days(newest_mtime(DRAMA_MIX))
    audio_out_last = age_days(newest_mtime(AUDIO_OUT)) if os.path.isdir(AUDIO_OUT) else None

    m = {
        "ts": now.strftime("%Y-%m-%d %H:%M:%S"),
        "gpu": gpu,
        "cpu_pct": cpu,
        "repos": {
            "FluxGroup": {"ahead": fg_ahead, "behind": fg_behind},
            "bigmoney": {"ahead": bm_ahead, "behind": bm_behind},
        },
        "ages_days": {
            "mv_line_last_write": mv_last,
            "drama_eps_last": drama_eps_last,
            "drama_tts_last": tts_last,
            "drama_mix_last": mix_last,
            "drama_audio_out_last": audio_out_last,
        },
        "counts": {
            "mv_scripts": count_files(MV, "剧本"),
            "mv_prompt_gates": count_files(MV, "PROMPT-GATE"),
            "mv_reports": count_files(MV, "R-2026"),
            "drama_ep_mp4": ep_count,
            "drama_ep_mp4_junk": junk_count,
            "drama_ep_audio": count_files(AUDIO_OUT, ".mp4") if os.path.isdir(AUDIO_OUT) else 0,
        },
        "sentinel": sent,
    }

    flags = []
    # R4 capacity balance: GPU idle while claimable work exists
    if gpu and gpu["util_pct"] < 10 and (sent.get("open_items") or 0) > 0:
        flags.append("R4 产能：GPU %.0f%% 空闲 + 本机可领工件 %d 件未开 → 调度缺陷候选"
                     % (gpu["util_pct"], sent["open_items"]))
    # R5 sync window
    for name, info in m["repos"].items():
        if info["behind"] and info["behind"] > 50:
            flags.append("R5 同步：%s 落后 %d 提交（>50=事故线）" % (name, info["behind"]))
    # R4/R2 line idle
    for label, d in (("漫剧 TTS", tts_last), ("漫剧混音", mix_last), ("MV 线", mv_last)):
        if d is not None and d > 3:
            flags.append("R2/R4 产线：%s 已 %.1f 天无产出" % (label, d))
    # R1 paper vs output
    if m["counts"]["mv_scripts"] >= 10 and m["counts"]["drama_ep_audio"] < m["counts"]["drama_ep_mp4"]:
        flags.append("R1/R6 门与产：MV 剧本 %d 版、漫剧带声 %d/%d 集 → 纸面厚于成片"
                     % (m["counts"]["mv_scripts"], m["counts"]["drama_ep_audio"], m["counts"]["drama_ep_mp4"]))
    if sent.get("open_items") == 0:
        flags.append("R4 池：本机可领工件为 0 → 触发秘书处补货 SLA")
    if junk_count > 100:
        flags.append("GC：drama-eps 有 %d 个 tmp_/diag_ mp4 残留（非交付件，占盘待清）" % junk_count)

    m["flags"] = flags

    os.makedirs(OUTDIR, exist_ok=True)
    date = now.strftime("%Y-%m-%d")
    md_path = os.path.join(OUTDIR, "AUDIT-%s.md" % date)
    js_path = os.path.join(OUTDIR, "AUDIT-%s.json" % date)

    def fmt(v, unit=""):
        return "—" if v is None else ("%s%s" % (v, unit))

    lines = []
    lines.append("# 工作流日审 %s（确定性采集·零 LLM）\n" % now.strftime("%Y-%m-%d %H:%M"))
    lines.append("> 法源=AUDIT-20261027-workflow-director.md（七失衡/七律）；本件只出**底数与规则旗标**，判断与动作由当日复盘席补。\n")
    lines.append("## 一、产能\n")
    lines.append("| 项 | 值 |")
    lines.append("|---|---|")
    if gpu:
        lines.append("| GPU 利用率 | %.0f%% |" % gpu["util_pct"])
        lines.append("| 显存占用 | %.0f / %.0f MB |" % (gpu["used_mb"], gpu["total_mb"]))
    else:
        lines.append("| GPU | 采集失败 |")
    lines.append("| CPU | %s |" % fmt(cpu, "%"))
    lines.append("\n## 二、同步面\n")
    lines.append("| 仓 | ahead | behind |")
    lines.append("|---|---|---|")
    for name, info in m["repos"].items():
        lines.append("| %s | %s | %s |" % (name, fmt(info["ahead"]), fmt(info["behind"])))
    lines.append("\n## 三、产线活跃度（距今天数）\n")
    lines.append("| 线 | 最后产出 |")
    lines.append("|---|---|")
    for k, v in m["ages_days"].items():
        lines.append("| %s | %s |" % (k, fmt(v, " 天")))
    lines.append("\n## 四、产出计数\n")
    lines.append("| 项 | 数 |")
    lines.append("|---|---|")
    for k, v in m["counts"].items():
        lines.append("| %s | %s |" % (k, v))
    lines.append("| 本机可领工件 | %s |" % fmt(sent.get("open_items")))
    lines.append("\n## 五、规则旗标\n")
    if flags:
        for f in flags:
            lines.append("- %s" % f)
    else:
        lines.append("- 无（七律未触发）")
    lines.append("\n## 六、哨兵尾行\n\n```\n%s\n```\n" % (sent.get("last_line") or "—"))

    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    with open(js_path, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)

    led = os.path.join(OUTDIR, "LEDGER.md")
    if not os.path.exists(led):
        open(led, "w", encoding="utf-8").write("# 工作流日审台账（append-only）\n\n| 日期 | GPU | CPU | FG behind | BM behind | 旗标 |\n|---|---|---|---|---|---|\n")
    with open(led, "a", encoding="utf-8", newline="\n") as f:
        f.write("| %s | %s | %s | %s | %s | %d |\n" % (
            now.strftime("%Y-%m-%d %H:%M"),
            ("%.0f%%" % gpu["util_pct"]) if gpu else "—",
            fmt(cpu, "%"), fmt(fg_behind), fmt(bm_behind), len(flags)))

    print("AUDIT-WRITTEN %s flags=%d" % (md_path, len(flags)))
    for f in flags:
        print("FLAG " + f)
    return 0


if __name__ == "__main__":
    sys.exit(main())