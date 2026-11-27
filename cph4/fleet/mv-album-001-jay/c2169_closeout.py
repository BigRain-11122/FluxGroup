# c2169_closeout.py - M1 closeout for batch C2169 (machine C).
# 1) merge lane-inbox-M5.json into state-c.json (top-level subtree replace)
# 2) append the nine missing STATUS-c rows C2160-C2168 plus this round (P2-1)
# 3) write last_round / snapshot id / next_round_at
# Contracts: state=indent 1 + LF; STATUS=BOM + CRLF.
import json
import os
import time

ROOT = r"K:\Fluxgroup\MiniGame"
STATE = os.path.join(ROOT, "state-c.json")
STATUS = os.path.join(ROOT, "STATUS-c.md")
INBOX = os.path.join(ROOT, ".codely-cli", "engine-tick", "lane-inbox-M5.json")

NOW = time.strftime("%Y-%m-%d %H:%M")
SNAP_ID = time.strftime("tick-20261024-%H%M") + "@C2169"

ROWS = [
    ("2026-10-24 01:04", "C2160", "《星晴》PACK-B R4 重渲染本地点火：2 种子 S1-07 清单+逐单种子覆写+自愈长烧任务+银行 job claimed（云中人形病灶走重烧不走修图）", "packB-s107-r4-rerender-fired"),
    ("2026-10-24 01:24", "C2161", "R6-1/R6-3 落装配层（蝴蝶去物种化+蒙太奇 punch-in），窗口级探针机器验收，不重建成片", "packB-r6-assembly-layer"),
    ("2026-10-24 01:55", "C2162", "PACK-B R4 判决：两 take 模型级皆 FAIL（云中人形在首帧板内锁死）→R5 首帧板波+胜者+V6 探针+R5 i2v 预挂", "packB-s107-r4-verdict-r5-plate"),
    ("2026-10-24 02:25", "C2163", "v7 装配回执（5712 帧/238.000s，剪辑语法 PASS）；S1-07 R5 take 本体判读 PASS 后 v7 装配点火", "packB-v7-assembly"),
    ("2026-10-24 02:37", "C2164", "PACK-B v7 导演席拉片=REVISE（S2-10/11 色彩断层；232s 伪手写字迹）", "packB-v7-director-revise"),
    ("2026-10-24 03:14", "C2165", "PACK-B v8 关闭 v7 两项硬伤（S2-10/11 调色补偿+真实可读手写注记）→导演席 PASS", "packB-v8-director-pass"),
    ("2026-10-24 04:15", "C2166", "《可爱女人》KN 帧闸 F1-F8 签署 PASS（6 张返工零残留 FAIL）+shots v2.7+银行收口", "kn-frame-gate-signed"),
    ("2026-10-24 04:59", "C2167", "KN i2v 词闸签署（30 单 lint+guard 双绿，18 处 FIX 落地）+pack+480P/768P 清单+shots v2.8+银行武装", "kn-i2v-promptgate-signed"),
    ("2026-10-24 05:47", "C2168", "KN 480P 验证判决 GO（KN21/KN22b 干净，KN04 两轮词面修复 PASS）→768P 30 单波上膛", "kn-verify480-go"),
]

THIS_ROW = ("__NOW__", "C2169",
            "KN 768P 30 单波在飞监护（1/30 已出，KN01 175 帧/dup 单帧/1344x768）+ 帧检局收割件 authored（kn_pa768_harvest_c2169.py：ffprobe+framemd5 复读游程+原生帧抽样+双接触板+机读判决）+ 银行预挂两件（harvest p66/conform 站4 p67）+ M5 inbox 合并 + STATUS-c 补记 C2160-C2168 九行（P2-1）",
            "kn-pa768-wave-guard-harvest-gate")


def read_json(path):
    return json.loads(open(path, "rb").read().decode("utf-8-sig"))


def write_json(path, data):
    text = json.dumps(data, ensure_ascii=False, indent=1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    state = read_json(STATE)

    merged = []
    if os.path.exists(INBOX):
        inbox = read_json(INBOX)
        for key, subtree in (inbox.get("state_patch") or {}).items():
            state[key] = subtree
            merged.append(key)
        for alert in inbox.get("snapshot_alerts") or []:
            merged.append("alert:" + str(alert)[:60])

    state["current_snapshot_id"] = SNAP_ID
    state["last_round"] = {
        "ts": NOW,
        "result": ("C2169 (train guard + harvest gate). The KN A 768P 30-unit wave is burning on the idle guard's "
                   "self-healing loop (unit 1 KN01 landed 06:03, 1344x768 / 175 frames / max duplicate run 1 frame). "
                   "Authored the zero-GPU harvest gate kn_pa768_harvest_c2169.py (probe + framemd5 repeat run + "
                   "three native frames per unit + two contact boards + machine-readable verdict) and smoke-tested "
                   "it against KN01. Producer law: pre-stowed two successors in the bank (harvest p66, station-4 "
                   "conform authoring p67) so the bank is never empty. Merged the M5 lane inbox (audit health "
                   "0.58 calibration / 0.68 closure) and closed its P2-1 by appending the nine missing STATUS-c "
                   "rows C2160-C2168."),
        "build_ok": True,
    }
    state["next_round_at"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() + 600))
    write_json(STATE, state)
    print("STATE_OK merged=%s snapshot=%s" % (",".join(merged) or "none", SNAP_ID))

    raw = open(STATUS, "rb").read()
    assert raw[:3] == b"\xef\xbb\xbf", "STATUS BOM contract changed"
    text = raw.decode("utf-8-sig")
    last = text.rstrip("\r\n").splitlines()[-1]
    assert last.startswith("- [") and " | " in last, "STATUS tail row shape changed"
    add = []
    for ts, batch, summary, tag in ROWS + [THIS_ROW]:
        stamp = NOW if ts == "__NOW__" else ts
        add.append("- [%s] %s | %s | %s" % (stamp, batch, summary, tag))
    new_text = text.rstrip("\r\n") + "\r\n" + "\r\n".join(add) + "\r\n"
    with open(STATUS, "wb") as f:
        f.write(b"\xef\xbb\xbf" + new_text.encode("utf-8"))
    print("STATUS_OK rows_added=%d" % len(add))

    if os.path.exists(INBOX):
        os.remove(INBOX)
        print("INBOX_MERGED_AND_REMOVED lane-inbox-M5.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())