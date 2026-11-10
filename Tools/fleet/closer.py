#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""closer.py - the audit+ingest leg that turns "done" into "accepted".

Loop: assign(master) -> produce(lane) -> **audit+ingest(closer)** -> supervise/report.
A card is only closed when its declared deliverable is on disk; the closer records who
produced it, when, what was checked, and appends one event. No deliverable = stays RUNNING
and is reported, never silently marked DONE.
"""
import json, os, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402
import flux_contracts as fc  # noqa: E402
F = os.path.join(ROOT, "cph4", "fleet")
Q = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
EV = os.path.join(F, "dispatcher", "events.jsonl")
RECEIPT_DIR = os.path.join(F, "queue-receipts")


# 阈值统一来自 cph4/fleet/CARD-POLICY-v1.json（唯一源，别再在这里写数字）
import card_policy as _cp
HEARTBEAT_TIMEOUT_S = _cp.heartbeat_timeout_s()


def _cfg():
    try:
        with open(os.path.join(F, "AUTONOMY-CONFIG.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


CFG = _cfg()
STALL_S = _cp.stall_after_s()
MAX_ATTEMPTS = _cp.max_attempts()
RETRY_CLASSES = _cp.retry_error_classes()


def lane_progress():
    """owner -> (job, out_bytes, ts) from MASTER-STATE.

    2026-11-05 起因：心跳只证明进程活着。lane_agent 现在每 45s 报一次子进程已捕获的
    stdout 字节数（out_bytes），这个数不涨 = 命令没有产生任何新输出，才算真的卡住。
    """
    try:
        ms = json.load(open(os.path.join(F, "dispatcher", "MASTER-STATE.json"),
                            encoding="utf-8-sig"))
    except Exception:
        return {}
    out = {}
    for n, v in (ms.get("lanes") or {}).items():
        lr = v.get("last_result") or {}
        if lr.get("job"):
            out[n] = (lr.get("job"), int(lr.get("out_bytes") or 0), lr.get("ts"))
    return out


def release(r, why):
    """Open the card again, or stop it for good once the same card keeps failing.

    3 次未成 = 停线落根因（AUTONOMY-CONFIG.failures）。此前同一任务连续三天对四台机
    重派、全失败、error_class 为空，谁也不知道为什么——重派不是解决。
    """
    att = int(r.get("retries") or 0) + 1
    r["retries"] = att
    if att >= MAX_ATTEMPTS:
        r["state"] = "FAILED"
        r["error_class"] = (CFG.get("failures") or {}).get("error_class") or "E-ROOTCAUSE-3X"
        r["note"] = "3 次未成，停线待根因：%s" % why
        r.pop("owner", None)
        # 2026-11-10：停线必须留下可判的题，而不是只写一行 note。
        try:
            jp = os.path.join(ROOT, "cph4", "fleet", "dispatcher", "JUDGMENT-QUEUE.jsonl")
            row = {"id": "JUDGE-3X-%s" % r.get("id"), "kind": "E-ROOTCAUSE-3X",
                   "state": "OPEN", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "question": "卡 %s 三次未成（%s），根因是什么、下一步怎么做？" % (r.get("id"), why),
                   "evidence": {"card": r.get("id"), "line": r.get("line"),
                                "cmd": (r.get("cmd") or "")[:200],
                                "prompt": (r.get("prompt") or "")[:200]}}
            with open(jp, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + chr(10))
        except Exception:
            pass
        return "blocked"
    r["state"] = "OPEN"
    r["owner"] = None
    r["note"] = why
    return "requeued"


def lane_beat():
    """owner -> seconds since that lane last reported a result; None = never reported.

    Why None instead of 1e9 (2026-11-07 实锚): MASTER-STATE.json 里三台机的
    last_result.ts 全是 None（它们从来没跑完过一张卡），旧实现把"没有记录"当成
    "已经静默 1e9 秒"，于是任何卡 claim 后 ~3 分钟就被 lease-heartbeat-timeout
    (1000000000s) 杀掉、重试三次转 FAILED——派单→执行整条链对全部机器失效，
    症状恰好是"车道永远空、机器报 IDLE、队列有活派不出去"。
    "没有记录"不是"静默很久"，两者必须分开：没有记录时由调用方按卡的 claim 时间算。
    """
    import time as _t
    try:
        ms = json.load(open(os.path.join(F, "dispatcher", "MASTER-STATE.json"),
                            encoding="utf-8-sig"))
    except Exception:
        return {}
    out = {}
    for n, v in (ms.get("lanes") or {}).items():
        lr = v.get("last_result") or {}
        ts = lr.get("ts")
        if not ts:
            out[n] = None          # 无记录 ≠ 长期静默
            continue
        try:
            from datetime import datetime as _d
            out[n] = _t.time() - _d.fromisoformat(ts).timestamp()
        except Exception:
            out[n] = None
    return out


def _since(ts_text):
    """卡片自 claim 以来的秒数；解析不了返回 None（不猜）。"""
    try:
        from datetime import datetime as _d
        import time as _t
        return _t.time() - _d.fromisoformat(str(ts_text)).timestamp()
    except Exception:
        return None


def lane_rc():
    """owner -> last reported rc. The artifact on disk is not proof of success: a card
    that never ran (rc=9009, command not found on this host) can still leave a stale
    file behind. Closing on the file alone fabricated 20+ green cards in October.
    """
    try:
        ms = json.load(open(os.path.join(F, "dispatcher", "MASTER-STATE.json"),
                            encoding="utf-8-sig"))
    except Exception:
        return {}
    out = {}
    for n, v in (ms.get("lanes") or {}).items():
        lr = v.get("last_result") or {}
        if lr.get("rc") is not None:
            try:
                out[n] = (lr.get("job"), int(lr.get("rc")))
            except (TypeError, ValueError):
                pass
    return out


def receipt_index():
    """id -> True for receipts declaring a landed artifact with an OK outcome.

    Built once with a per-file guard. Before 2026-11-10 one malformed .json raised
    inside the scan loop and the bare `except: pass` swallowed it, so receipt_ok was
    False for EVERY card: cross-machine cards fell through to the STALL leg and were
    marked FAILED over deliverables that really existed (7 bad files, 16 cards).
    """
    out = {}
    try:
        names = os.listdir(RECEIPT_DIR)
    except Exception:
        return out
    for n in names:
        if not n.endswith(".json"):
            continue
        try:
            rec = json.load(open(os.path.join(RECEIPT_DIR, n), encoding="utf-8-sig"))
        except Exception:
            continue            # one bad file must not void the whole scan
        if not isinstance(rec, dict):
            continue
        if rec.get("id") and rec.get("deliverable_exists") \
                and str(rec.get("outcome") or "OK").upper() == "OK":
            out[rec["id"]] = True
    return out


def main():
    rows = [json.loads(l) for l in open(Q, encoding="utf-8") if l.strip()]
    beats = lane_beat()
    rcs = lane_rc()
    progs = lane_progress()
    receipts = receipt_index()
    now_iso = datetime.now().isoformat(timespec="seconds")
    closed, waiting, requeued, awaiting, blocked = [], [], [], [], []
    touched = []
    for r in rows:
        # UNVERIFIED is a legitimate holding state: the lane said done but the artifact had
        # not landed yet. The moment it does land, this leg upgrades it - so the state
        # machine self-heals instead of leaving an unproven closure on the books.
        # FAILED belongs here too (2026-11-02): a card was marked failed because the
        # executor never reported, but the artifact can still land afterwards (a retry on
        # another box, a manual run). FAILED was terminal, so the queue kept saying
        # "failed" over a deliverable that existed on disk - the books lied about reality.
        if r.get("state") not in ("RUNNING", "DONE", "UNVERIFIED", "FAILED"):
            continue
        dl = r.get("deliverable") or ""
        local = os.path.join(ROOT, dl) if dl and not os.path.isabs(dl) else dl
        # 产物可能落在别的机器上（跨机路径假红，2026-11-02 自审）：本机看不见不代表没做出来。
        # 以回执为准——回执说产物在、退出码合格，就认。
        receipt_ok = bool(receipts.get(r.get("id")))
        # artifact_ok rejects a refusal receipt that landed on the promised path: the
        # BLOCKED file exists but nothing was produced (2026-11-03, twice).
        ok = fc.artifact_ok(local) or receipt_ok
        owner = r.get("owner")
        allowed = r.get("ok_rc") if isinstance(r.get("ok_rc"), list) and r.get("ok_rc") else [0]
        allowed = [int(x) for x in allowed]
        lane_rc_v = None
        rep = rcs.get(owner)
        if rep and (rep[0] is None or rep[0] == r.get("id")):
            lane_rc_v = rep[1]          # only trust a report that belongs to this card
        rc_ok = lane_rc_v is None or lane_rc_v in allowed
        if ok and not rc_ok:
            # File exists but the executor's exit code says it did not succeed.
            # Do not upgrade; record the contradiction so it can be triaged.
            r["evidence"] = "artifact-on-disk-but-rc=%s (allowed=%s)" % (lane_rc_v, allowed)
            touched.append(r)
            awaiting.append(r["id"])
            continue
        if ok and r.get("state") in ("RUNNING", "UNVERIFIED", "FAILED"):
            was = r.get("state")
            r["state"] = "DONE"
            r["closed_by"] = "closer.py"
            r["closed_at"] = datetime.now().isoformat(timespec="seconds")
            r["audit"] = {"deliverable": dl, "exists": True,
                          "size": os.path.getsize(local) if os.path.isfile(local) else None}
            if was == "UNVERIFIED":
                r.pop("evidence", None)
                r["audit"]["upgraded_from"] = "UNVERIFIED"
            elif was == "FAILED":
                r.pop("error", None)
                r["audit"]["upgraded_from"] = "FAILED"
            closed.append(r["id"])
            touched.append(r)
        elif (not ok) and r.get("state") == "FAILED":
            # 无人监管的关键一环（2026-11-02）：失败不等人。
            # 路径类/未知类错误换一台机器再来一次；其余错误保持隔离等人判。
            cls = str(r.get("error_class") or "")
            retries = int(r.get("retries") or 0)
            if cls in RETRY_CLASSES and retries < MAX_ATTEMPTS - 1:
                r["state"] = "OPEN"
                r["owner"] = None
                r["retries"] = retries + 1
                r["note"] = "auto-retry: %s 换机重试（第 %d 次）" % (cls, retries + 1)
                touched.append(r)
                requeued.append(r["id"])
        elif not ok and r.get("state") == "RUNNING":
            owner = r.get("owner")
            # No heartbeat for that owner at all is not "a very long lease" - it is a
            # card whose owner never reported (fallback node, renamed host, stale lane).
            # Formatting it as 1e9 seconds (2026-11-03: "lease-heartbeat-timeout(1000000000s)")
            # buried the real reason in a number nobody could read.
            if owner not in beats:
                if release(r, "lease-owner-unknown: %s 无心跳，释放重排" % (owner or "(none)")) == "blocked":
                    blocked.append(r["id"])
                else:
                    requeued.append(r["id"])
                touched.append(r)
                continue
            age = beats.get(owner)
            if age is None:
                # 该车道从未报过结果：没有证据说它静默，就按卡自己握了多久来判。
                # 超过租约仍无任何回执/产出，才释放——这是"卡被占着没动"，可判。
                age = _since(r.get("claimed_at") or r.get("assign_ts"))
                if age is None:
                    continue          # 连 claim 时间都没有：不判，留给 master 侧
                lease_s = int(r.get("lease_minutes") or 45) * 60
                if age > lease_s:
                    if release(r, "lease-no-heartbeat: 已握 %.0fs（租约 %ds）且该车道从无回执"
                                      % (age, lease_s)) == "blocked":
                        blocked.append(r["id"])
                    else:
                        requeued.append(r["id"])
                    touched.append(r)
                    continue
            elif age > HEARTBEAT_TIMEOUT_S:      # worker silent -> release, do not hang forever
                if release(r, "lease-heartbeat-timeout(%.0fs)" % age) == "blocked":
                    blocked.append(r["id"])
                else:
                    requeued.append(r["id"])
                touched.append(r)
                continue

            # 进展判据（2026-11-05）：心跳在跳 ≠ 活在干。机器握着 RUNNING 卡、心跳新鲜，
            # 卡却几小时没有任何输出来——实测 bm-a/bm-b 4.2h、bm-c 17.5h 回执为零而三台都
            # "online"。这里用 stdout 字节数 + 交付物大小作为进展信号，30 分钟不涨即 STALL。
            job, out_bytes, _ts = progs.get(owner, (None, 0, None))
            dl_bytes = 0
            try:
                if local and os.path.exists(local):
                    dl_bytes = os.path.getsize(local) if os.path.isfile(local) else len(os.listdir(local))
            except Exception:
                dl_bytes = 0
            sig = max(int(out_bytes or 0) if job == r.get("id") else 0, dl_bytes)
            prev = r.get("progress_bytes")
            if prev is None or sig > int(prev):
                r["progress_bytes"] = sig
                r["progress_ts"] = now_iso
                touched.append(r)
                waiting.append(r["id"])
            else:
                try:
                    idle_s = (datetime.now() - datetime.fromisoformat(str(r.get("progress_ts")))).total_seconds()
                except Exception:
                    idle_s = None
                    r["progress_ts"] = now_iso
                    touched.append(r)
                if idle_s is not None and idle_s > STALL_S:
                    if release(r, "STALL: %ds 无新输出（sig=%s），释放" % (int(idle_s), sig)) == "blocked":
                        blocked.append(r["id"])
                    else:
                        requeued.append(r["id"])
                    touched.append(r)
                else:
                    waiting.append(r["id"])
    if touched:
        # commit only the rows this leg changed; a whole-file rewrite erased the master's
        # dispatch in the same cycle (lost update, 2026-11-02 review).
        fl.merge_jsonl(Q, touched)
        with open(EV, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                "kind": "close", "cards": closed,
                                "requeued": requeued, "blocked": blocked}, ensure_ascii=False) + "\n")
    print("[closer] closed=%d requeued=%d blocked=%d waiting=%d awaiting-evidence=%d %s"
          % (len(closed), len(requeued), len(blocked), len(waiting), len(awaiting),
             ",".join(requeued[:3] or blocked[:3] or awaiting[:3] or waiting[:3])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
