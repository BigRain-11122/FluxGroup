#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flux_eventlog.py - 事件日志（S1 影子期）：本机 outbox -> NATS JetStream FLUX_EVENTS。

为什么（2026-11-03 CEO：机队靠文档交流很不好）：
  现状是「共享可变文档 + git 乐观并发」做分布式协调——24 小时 1212 次提交、队列文件被整表
  重写 609 次、dispatcher/lanes 写 2601 次，只为了让四台机器互相告知「卡到哪一步」。
  文档被同时当成消息、状态、报告三种介质，三种需求互相破坏：没有 ack（同一活派过 3 张卡）、
  多套口径（QUEUE/BACKLOG/JUDGMENT/MASTER-STATE/lanes）、一改就脏树（脏树即断全机同步）。
  正解=分成四层：传输（事件流）/ 状态（SQLite）/ 接口（fluxctl）/ 投影（文档只读渲染）。
  本模块只做第一层，且按影子期设计：只写不读，生产路径永不等它。

语义（对外承诺，改之前先改这段）：
  * 事件六种：CARD / CLAIM / PROGRESS / RECEIPT / VERDICT / ARTIFACT
  * 先落本机 SQLite outbox（同步、原子），再由 relay 异步发到 JetStream（至少一次）
  * event_id = sha256(kind|card|node|attempt|payload) 前 32 位，内容相同即同一事件，
    服务器端按 Nats-Msg-Id 在 2 分钟去重窗内丢弃重复发布 -> 重投不产生重复
  * 消费者 per-node durable + AckExplicit：处理成功才 ack，崩溃自动重投；
    消费侧用 inbox 表按 event_id 去重（inbox 模式），重复投递不产生重复副作用
  * 传输层不做派单独占：独占由「租约」表达（谁持有租约谁干），不是「谁先读到谁干」

用法：
  python3 Tools/fleet/flux_eventlog.py init                 # 建流（幂等）
  python3 Tools/fleet/flux_eventlog.py status               # 本机 outbox + 流信息
  python3 Tools/fleet/flux_eventlog.py relay                # 把未发事件发出去
  python3 Tools/fleet/flux_eventlog.py backfill             # 用现有队列/回执补历史事件
  python3 Tools/fleet/flux_eventlog.py consume --node bm-m  # 拉本机未消费事件并 ack
  python3 Tools/fleet/flux_eventlog.py recon                # 事件 vs 文件 对账（影子期验收）
Exit: 0 正常；2 对账不一致（影子期只告警，不阻断生产）。
"""
import argparse
import hashlib
import json
import os
import socket
import sqlite3
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
DB = os.path.join(STATE, "eventlog.db")

STREAM = "FLUX_EVENTS"
SUBJECT = "flux.events"          # 单一 subject：kind/card 放 payload，避免 workqueue 过滤冲突
HUB = os.environ.get("FLEET_HUB", "100.110.185.62")
PORT = int(os.environ.get("FLEET_HUB_PORT", "4222"))
MAX_AGE_NS = 30 * 86400 * 1000000000      # 30 天
DUP_WINDOW_NS = 120 * 1000000000          # 2 分钟去重窗
MAX_BYTES = 512 * 1024 * 1024             # 兜底：不让日志把 hub 磁盘吃满

KINDS = ("CARD", "CLAIM", "PROGRESS", "RECEIPT", "VERDICT", "ARTIFACT")

SCHEMA = """
CREATE TABLE IF NOT EXISTS outbox(
  event_id TEXT PRIMARY KEY,
  ts TEXT NOT NULL,
  kind TEXT NOT NULL,
  card_id TEXT,
  node TEXT,
  attempt INTEGER DEFAULT 1,
  payload TEXT NOT NULL,
  sent_ts TEXT,
  stream_seq INTEGER
);
CREATE INDEX IF NOT EXISTS outbox_unsent ON outbox(sent_ts);
CREATE TABLE IF NOT EXISTS inbox(
  event_id TEXT PRIMARY KEY,
  ts TEXT NOT NULL,
  consumer TEXT
);
CREATE TABLE IF NOT EXISTS cursor(
  name TEXT PRIMARY KEY,
  seq INTEGER DEFAULT 0,
  ts TEXT
);
"""


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


# ---- storage -------------------------------------------------------------------
def db(path=None):
    p = path or DB
    os.makedirs(os.path.dirname(p), exist_ok=True)
    con = sqlite3.connect(p, timeout=5.0)
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    return con


def event_id(kind, card_id, node, attempt, payload):
    """内容寻址：同一次状态变化永远得到同一个 id，重发不产生重复事件。"""
    canon = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    raw = "%s|%s|%s|%s|%s" % (kind, card_id or "", node or "", attempt or 1, canon)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def emit(kind, card_id="", node="", attempt=1, payload=None, path=None):
    """写本机 outbox。绝不抛：影子期任何异常都不许影响生产调用方。"""
    try:
        if kind not in KINDS:
            raise ValueError("unknown kind %r (allowed: %s)" % (kind, ",".join(KINDS)))
        payload = payload or {}
        eid = event_id(kind, card_id, node, attempt, payload)
        con = db(path)
        try:
            con.execute(
                "INSERT OR IGNORE INTO outbox(event_id,ts,kind,card_id,node,attempt,payload)"
                " VALUES(?,?,?,?,?,?,?)",
                (eid, now_iso(), kind, card_id or "", node or "", int(attempt or 1),
                 json.dumps(payload, ensure_ascii=False, sort_keys=True)))
            con.commit()
        finally:
            con.close()
        return eid
    except Exception:
        return None


# ---- transport (raw NATS; no nats.exe on the Mac) -------------------------------
_HUB_OK = [None]   # 进程内缓存：同一轮不要为死链反复付超时


def hub_reachable(force=False):
    """1.5s 内能否建立到 NATS 的 TCP —— 不通就快速失败，别让每轮白等。

    Why (2026-11-07 实测)：hub 不可达时 relay 与 consume 各自 _connect(timeout=10/3)，
    一轮白烧 20-37s（eventlog 一度涨到 37s/轮成为最贵阶段）。事件不丢——outbox 里
    sent_ts 为空的记录原地保留，hub 恢复后照常补发。
    """
    if _HUB_OK[0] is None or force:
        try:
            _s = socket.create_connection((HUB, PORT), timeout=1.5)
            _s.close()
            _HUB_OK[0] = True
        except Exception:
            _HUB_OK[0] = False
    return _HUB_OK[0]


def _connect(timeout=4.0):
    s = socket.create_connection((HUB, PORT), timeout)
    s.settimeout(timeout)
    buf = b""
    while b"\r\n" not in buf:
        chunk = s.recv(4096)
        if not chunk:
            raise ConnectionError("nats closed during INFO")
        buf += chunk
    s.sendall(b'CONNECT {"verbose":false,"pedantic":false}\r\n')
    return s


_BUFS = {}


def _read_frame(s, timeout):
    """读一帧，返回 (subject, reply, headers_dict, payload)；超时返回 None。

    缓冲区必须挂在连接上而不是函数局部：一次 recv 常带回多帧，局部 buf 在第一次
    return 时被丢弃，后面的 ack 就永久消失——实测表现为"发了 500 条只回来 3 个 ack"，
    再被误判成 no-puback。同一连接的残留字节存在 _BUFS[s] 里接着解析。
    """
    end = time.time() + timeout
    buf = _BUFS.get(s, b"")
    try:
        while time.time() < end:
            while b"\r\n" not in buf:
                try:
                    chunk = s.recv(65536)
                except socket.timeout:
                    return None
                if not chunk:
                    return None
                buf += chunk
            line, buf = buf.split(b"\r\n", 1)
            parts = line.split()
            if not parts:
                continue
            if parts[0] == b"PING":
                s.sendall(b"PONG\r\n")
                continue
            if parts[0] in (b"+OK", b"PONG"):
                continue
            if parts[0] == b"-ERR":
                return ("", "", {"err": line.decode("utf-8", "replace")}, b"")
            if parts[0] not in (b"MSG", b"HMSG"):
                continue
            subject = parts[1].decode()
            reply = ""
            if parts[0] == b"MSG":
                # MSG <subject> <sid> [reply] <#bytes>
                if len(parts) == 5:
                    reply, n = parts[3].decode(), int(parts[4])
                else:
                    n = int(parts[-1])
                while len(buf) < n + 2:
                    chunk = s.recv(65536)
                    if not chunk:
                        return None
                    buf += chunk
                payload, buf = buf[:n], buf[n + 2:]
                return (subject, reply, {}, payload)
            # HMSG <subject> <sid> [reply] <hdr_len> <total_len>
            if len(parts) == 6:
                reply, hdr_len, total = parts[3].decode(), int(parts[4]), int(parts[5])
            else:
                hdr_len, total = int(parts[-2]), int(parts[-1])
            while len(buf) < total + 2:
                chunk = s.recv(65536)
                if not chunk:
                    return None
                buf += chunk
            raw, buf = buf[:total], buf[total + 2:]
            hdrs = {}
            for hl in raw[:hdr_len].decode("utf-8", "replace").split("\r\n")[1:]:
                if ":" in hl:
                    k, v = hl.split(":", 1)
                    hdrs[k.strip().lower()] = v.strip()
            return (subject, reply, hdrs, raw[hdr_len:])
        return None
    finally:
        _BUFS[s] = buf


def request(subject, payload=b"", timeout=5.0, headers=None):
    """JetStream API 请求（带 headers 时走 HPUB，用于 Nats-Msg-Id 去重）。"""
    s = _connect(timeout)
    try:
        inbox = "_INBOX." + os.urandom(6).hex()
        s.sendall(("SUB %s 1\r\n" % inbox).encode())
        if headers:
            hdr = "NATS/1.0\r\n" + "".join("%s: %s\r\n" % (k, v) for k, v in headers.items()) + "\r\n"
            hb = hdr.encode()
            s.sendall(("HPUB %s %s %d %d\r\n" % (subject, inbox, len(hb), len(hb) + len(payload))).encode())
            s.sendall(hb + payload + b"\r\n")
        else:
            s.sendall(("PUB %s %s %d\r\n" % (subject, inbox, len(payload))).encode())
            s.sendall(payload + b"\r\n")
        while True:
            frame = _read_frame(s, timeout)
            if frame is None:
                return {}
            subj, _, hdrs, body = frame
            if hdrs.get("err"):
                return {"error": hdrs["err"]}
            if subj != inbox:
                continue
            out = {}
            try:
                out = json.loads(body.decode("utf-8", "replace") or "{}")
            except Exception:
                out = {}
            if not out and hdrs:
                # 无载荷的 ack：错误说明在 header 里（例如 Nats-Description）
                desc = hdrs.get("nats-description") or hdrs.get("description") or ""
                code = hdrs.get("status") or hdrs.get("nats-response-code") or ""
                if desc or code:
                    out = {"error": "%s %s" % (code, desc)}
            return out
    finally:
        try:
            s.close()
        except Exception:
            pass


def stream_info():
    r = request("$JS.API.STREAM.INFO." + STREAM)
    return r if r and "error" not in r else None


def init_stream():
    cfg = {"name": STREAM, "subjects": [SUBJECT], "retention": "limits",
           "storage": "file", "discard": "old", "max_age": MAX_AGE_NS,
           "duplicate_window": DUP_WINDOW_NS, "max_bytes": MAX_BYTES,
           "max_msgs_per_subject": -1, "max_msg_size": 262144}
    info = stream_info()
    if info:
        return True, "exists msgs=%s" % (info.get("state", {}).get("messages"))
    r = request("$JS.API.STREAM.CREATE." + STREAM, json.dumps(cfg).encode())
    if r.get("error"):
        return False, "create error %s" % r["error"]
    return True, "created"


def relay(limit=500, timeout=10.0):
    """发布本机未发事件。失败就地保留（sent_ts 为空 = 下次再发）。

    批量做法：一条连接、一个 inbox，先把 N 条全推出去再按序收 N 个 PubAck。
    逐条重开连接实测 500 条要 35 秒，等于每轮脉冲卡半分钟。同一连接上发布与 ack
    严格同序，因此按序号对回 event_id 是安全的。
    """
    con = db()
    try:
        rows = con.execute(
            "SELECT event_id,kind,card_id,node,attempt,payload FROM outbox"
            " WHERE sent_ts IS NULL ORDER BY ts LIMIT ?", (limit,)).fetchall()
        if not rows:
            return {"sent": 0, "pending": 0, "error": None}
        if not hub_reachable():
            return {"sent": 0, "pending": len(rows), "error": "hub-unreachable (kept for retry)"}
        s = _connect(timeout)
        try:
            inbox = "_INBOX." + os.urandom(6).hex()
            s.sendall(("SUB %s 1\r\n" % inbox).encode())
            for eid, kind, card, node, attempt, payload in rows:
                body = json.dumps({"event_id": eid, "ts": now_iso(), "kind": kind,
                                   "card_id": card, "node": node, "attempt": attempt,
                                   "payload": json.loads(payload)},
                                  ensure_ascii=False, sort_keys=True).encode("utf-8")
                s.sendall(("PUB %s %s %d\r\n" % (SUBJECT, inbox, len(body))).encode()
                          + body + b"\r\n")
            sent, err = 0, None
            for eid, kind, card, node, attempt, payload in rows:
                frame = _read_frame(s, timeout)
                if frame is None:
                    err = "no-puback"
                    break
                subj, reply, hdrs, body = frame
                try:
                    ack = json.loads(body.decode("utf-8", "replace") or "{}")
                except Exception:
                    ack = {}
                # 只认 PubAck 的 seq：没有 seq 就不算发出去了。2026-11-03 实测过这一段
                # 漏解析 HMSG，relay 对每条事件都报"已发"而流里为零条——账面绿、实际没发。
                if ack.get("error") or not ack.get("seq"):
                    err = ack.get("error") or hdrs.get("err") or "no-puback"
                    break
                con.execute("UPDATE outbox SET sent_ts=?, stream_seq=? WHERE event_id=?",
                            (now_iso(), ack.get("seq"), eid))
                sent += 1
                if sent % 100 == 0:
                    con.commit()
            con.commit()
        finally:
            try:
                s.close()
            except Exception:
                pass
        left = con.execute("SELECT COUNT(*) FROM outbox WHERE sent_ts IS NULL").fetchone()[0]
        return {"sent": sent, "pending": left, "error": err}
    finally:
        con.close()


# ---- consume (per-node durable, explicit ack, inbox 去重) -----------------------
def ensure_consumer(node):
    cfg = {"stream_name": STREAM, "config": {
        "durable_name": node, "ack_policy": "explicit", "deliver_policy": "all",
        "replay_policy": "instant", "max_deliver": 5, "ack_wait": 30 * 1000000000,
        "max_ack_pending": 200, "filter_subject": SUBJECT}}
    r = request("$JS.API.CONSUMER.DURABLE.CREATE.%s.%s" % (STREAM, node),
                json.dumps(cfg).encode())
    return not r.get("error"), r.get("error")


def consume(node, limit=50, timeout=3.0):
    if not hub_reachable():
        return {"error": "hub-unreachable", "handled": 0}
    ok, err = ensure_consumer(node)
    if not ok:
        return {"error": "consumer: %s" % err, "handled": 0}
    s = _connect(timeout)
    try:
        inbox = "_INBOX." + os.urandom(6).hex()
        s.sendall(("SUB %s 1\r\n" % inbox).encode())
        req_body = json.dumps({"batch": limit, "expires": 2000000000}).encode()
        s.sendall(("PUB $JS.API.CONSUMER.MSG.NEXT.%s.%s %s %d\r\n"
                   % (STREAM, node, inbox, len(req_body))).encode() + req_body + b"\r\n")
        con = db()
        handled = dup = 0
        try:
            for _ in range(limit + 2):
                frame = _read_frame(s, timeout)
                if frame is None:
                    break
                subj, reply, hdrs, body = frame
                # pull 消费者把消息投到 inbox 上，ack 主题在 reply 位；没有 reply 的
                # 只有控制帧（404/超时/心跳），不能一律按"不是消息"丢掉。
                if not reply:
                    break
                try:
                    ev = json.loads(body.decode("utf-8", "replace"))
                except Exception:
                    ev = {}
                eid = ev.get("event_id") or ""
                if not eid:
                    # 毒丸：解析不出 event_id 的消息直接 ack 丢弃，否则会无限重投堵住消费位点
                    if reply:
                        s.sendall(("PUB %s 4\r\n+ACK\r\n" % reply).encode())
                    continue
                row = con.execute("SELECT 1 FROM inbox WHERE event_id=?", (eid,)).fetchone()
                if row:
                    dup += 1                      # 已处理过：直接 ack 丢弃（inbox 模式）
                else:
                    con.execute("INSERT INTO inbox(event_id,ts,consumer) VALUES(?,?,?)",
                                (eid, now_iso(), node))
                    con.commit()
                    handled += 1
                if reply:
                    s.sendall(("PUB %s 4\r\n+ACK\r\n" % reply).encode())
        finally:
            con.close()
        return {"handled": handled, "duplicate": dup, "error": None}
    finally:
        try:
            s.close()
        except Exception:
            pass


# ---- backfill & recon ----------------------------------------------------------
def _jsonl(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def backfill(node="hub"):
    """把现有队列行补成 CARD 事件、回执补成 RECEIPT 事件（幂等，可反复跑）。"""
    cards = _jsonl(os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl"))
    n_card = 0
    for c in cards:
        cid = c.get("id")
        if not cid:
            continue
        payload = {k: c.get(k) for k in ("state", "line", "owner", "rc", "title",
                                         "deliverable", "created_by", "created_at",
                                         "finished_at") if c.get(k) is not None}
        if emit("CARD", cid, c.get("owner") or "", 1, payload):
            n_card += 1
    rdir = os.path.join(FLEET, "queue-receipts")
    n_rec = 0
    if os.path.isdir(rdir):
        for name in sorted(os.listdir(rdir)):
            if not name.endswith(".json"):
                continue
            p = os.path.join(rdir, name)
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    rec = json.load(f)
            except Exception:
                continue
            if not isinstance(rec, dict):
                # 有些回执是多条结果的列表（一卡多机/多步）；按文件名记一条，载荷只记条数
                rec = {"id": name[:-5], "items": len(rec) if isinstance(rec, list) else 1}
            rid = str(rec.get("id") or name[:-5])
            payload = {k: rec.get(k) for k in ("rc", "outcome", "error_class", "node",
                                               "seconds", "deliverable_exists") if rec.get(k) is not None}
            if emit("RECEIPT", rid, rec.get("node") or "", 1, payload):
                n_rec += 1
    return {"card": n_card, "receipt": n_rec}


def recon():
    """影子期验收：文件里有几张卡、事件里有没有、流里有没有。缺一味就是没对齐。"""
    con = db()
    try:
        out_rows = con.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]
        pending = con.execute("SELECT COUNT(*) FROM outbox WHERE sent_ts IS NULL").fetchone()[0]
        ids = set(r[0] for r in con.execute(
            "SELECT DISTINCT card_id FROM outbox WHERE kind='CARD' AND card_id<>''").fetchall())
    finally:
        con.close()
    cards = _jsonl(os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl"))
    file_ids = set(str(c.get("id")) for c in cards if c.get("id"))
    info = stream_info() or {}
    st = info.get("state", {})
    out = {"ts": now_iso(),
           "outbox_rows": out_rows, "outbox_pending": pending,
           "cards_in_file": len(file_ids), "cards_in_events": len(ids),
           "missing_in_events": sorted(file_ids - ids)[:20],
           "only_in_events": sorted(ids - file_ids)[:20],
           "stream": {"msgs": st.get("messages"), "bytes": st.get("bytes"),
                      "first_ts": (st.get("first_ts") or "")[:19],
                      "last_ts": (st.get("last_ts") or "")[:19]}}
    out["aligned"] = (not out["missing_in_events"]) and pending == 0
    os.makedirs(STATE, exist_ok=True)
    with open(os.path.join(STATE, "eventbus-recon.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    return out


def tick(node):
    """一轮：发本机未发事件 -> 拉本机未消费事件。影子期整轮不超过几秒。"""
    out = {"relay": relay(2000)}
    out["consume"] = consume(node, 500)
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("init", "status", "relay", "backfill", "consume",
                                    "recon", "tick"))
    ap.add_argument("--node", default=os.environ.get("FLEET_NODE", "bm-m"))
    ap.add_argument("--limit", type=int, default=500)
    a = ap.parse_args(argv)

    if a.cmd == "init":
        ok, msg = init_stream()
        print("init:", ok, msg)
        return 0 if ok else 2
    if a.cmd == "status":
        con = db()
        try:
            for label, sql in (("outbox", "SELECT COUNT(*) FROM outbox"),
                               ("pending", "SELECT COUNT(*) FROM outbox WHERE sent_ts IS NULL"),
                               ("inbox", "SELECT COUNT(*) FROM inbox")):
                print("%-8s %s" % (label, con.execute(sql).fetchone()[0]))
            for kind, n in con.execute("SELECT kind,COUNT(*) FROM outbox GROUP BY kind ORDER BY 2 DESC"):
                print("  %-9s %s" % (kind, n))
        finally:
            con.close()
        st = (stream_info() or {}).get("state", {})
        print("stream   msgs=%s bytes=%s last=%s" % (st.get("messages"), st.get("bytes"),
                                                     (st.get("last_ts") or "")[:19]))
        return 0
    if a.cmd == "relay":
        print(json.dumps(relay(a.limit), ensure_ascii=False))
        return 0
    if a.cmd == "backfill":
        print(json.dumps(backfill(), ensure_ascii=False))
        return 0
    if a.cmd == "consume":
        print(json.dumps(consume(a.node, a.limit), ensure_ascii=False))
        return 0
    if a.cmd == "tick":
        out = tick(a.node)
        print(json.dumps(out, ensure_ascii=False))
        bad = out["relay"].get("error") or out["consume"].get("error")
        return 2 if bad else 0
    if a.cmd == "recon":
        out = recon()
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0 if out["aligned"] else 2
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))