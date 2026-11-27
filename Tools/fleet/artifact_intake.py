#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""artifact_intake.py - 机队实际产出的收件口（唯一写入者 = MacBook Pro）。

为什么要有它（2026-11-02 实测）：lane_agent.git_publish 明确跳过 media/、gaming/、
quant/，队列里的 deliverable 又大量指向各机本地盘（D:\\、C:\\Fluxgroup、K:\\、
D:\\FleetWorker），结果机队真正产出的片子/配音/报告从来到不了主控这边。主控只能看
回执，看不到东西 —— 「DONE 但盘上没文件」就是这么来的。

方向选择：机队推送 → Mac 收取（push），而不是 Mac 去拉（pull）。
  * 盘在 Mac 上、写权限在 Mac 上，Windows 不必配 SMB 凭据；
  * Windows 侧只需要一个 Invoke-WebRequest，不引入新的服务端；
  * Mac 常开，收件口随 launchd 起来即可。

协议（单文件流式，避免 multipart 解析）：
    PUT /artifact?node=<bm-a|bm-b|bm-c>&card=<id>&name=<文件名>
        Content-Length: <bytes>
        X-Sha256: <hex>
        body = 原始字节
  成功 -> 200 {"ok":true,"stored":"<盘上路径>","bytes":N,"sha256":"..."}
  失败 -> 4xx/5xx {"ok":false,"err":"..."}

安全：只监听 tailnet 地址（默认 100.75.133.10），局域网/公网到不了。
     若存在令牌文件则额外要求头 X-Intake-Token 匹配。
"""
import hashlib
import json
import os
import re
import socket
import sys
import tempfile
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NODES = {"bm-a", "bm-b", "bm-c", "bm-m", "bm-d"}
MAX_BYTES = int(os.environ.get("INTAKE_MAX_BYTES", str(8 * 1024 ** 3)))  # 单件 8GB 上限
EXT = os.environ.get("INTAKE_ROOT") or ""   # 空=不落外盘（2026-11-11：移动盘退出长期存储）
# 2026-11-04：以前 DEST 直接落在移动盘上，盘不在就一律 503 —— bm-a 声明了 53 件产物，
# 从 11-02 起一件都没进来（PUSHED.jsonl 至今不存在），机队媒体因此永远到不了 Mac。
# 正法=内盘暂存永远可用，外盘只作归档副本；两种落点都记账，Health 如实报。
# 暂存必须落在仓内 media/inbox：脉冲的 ASR/转码/打标读的是 media/，若落到家目录，
# 文件收进来了也没有任何阶段会去加工——"通道通了但本机依旧闲着"。
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGE = os.environ.get("INTAKE_STAGE", os.path.join(_REPO, "media", "inbox"))
DEST = os.path.join(EXT, "产出归档")          # 归档位（挂盘时）
IDX_EXT = os.path.join(EXT, "Backup", "artifacts-index.jsonl")
IDX_STAGE = os.path.join(STAGE, "artifacts-index.jsonl")


ARCHIVE_MAX = int(os.environ.get("INTAKE_ARCHIVE_MAX_MB", "200")) * 1024 * 1024


RELEASE_FLAG = os.path.expanduser("~/.fluxgroup-disk-release")


def dest_now():
    """返回 (落盘目录, 索引路径, 模式)。

    2026-11-04 第二次修正：加工链（ASR/转码/打标）读的是仓内 media/inbox，所以
    **主落点必须是暂存**，外盘只作归档副本；否则盘一挂上，文件又跑到外盘去，
    本机照旧没活干（"盘在但脉看不到"与"盘不在"是同一种病）。
    """
    os.makedirs(STAGE, exist_ok=True)
    if os.path.exists(RELEASE_FLAG):
        # 用户要拔盘：仍收到内盘暂存（不丢件），但不碰外盘
        return os.path.join(STAGE, "intake"), IDX_STAGE, "stage(disk-released)"
    return os.path.join(STAGE, "intake"), IDX_STAGE, ("stage+archive" if os.path.isdir(EXT) else "stage")


def archive_copy(final, node, day, card, name):
    """外盘在时留一份归档副本（≤上限才复制，避免大文件回传时双倍 IO）。"""
    try:
        if not os.path.isdir(EXT) or os.path.getsize(final) > ARCHIVE_MAX:
            return None
        adir = os.path.join(DEST, node, day)
        os.makedirs(adir, exist_ok=True)
        dst = os.path.join(adir, "%s__%s" % (card, name))
        with open(final, "rb") as src, open(dst, "wb") as out:
            for chunk in iter(lambda: src.read(1 << 20), b""):
                out.write(chunk)
        return dst
    except Exception as e:
        log("ARCHIVE-SKIP %s/%s %s" % (node, name, str(e)[:80]))
        return None
TOKEN_FILE = os.path.expanduser("~/.codely-cli/fleet-intake-token")
LOG = "/tmp/fluxgroup-intake.log"

_lock = threading.Lock()


def log(msg):
    line = "[%s] %s" % (datetime.now().strftime("%F %T"), msg)
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def safe(s, limit=90):
    """只留下安全字符，防止 ../ 之类把文件写出归档目录。"""
    s = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "_", str(s or ""))
    return s.strip("._")[:limit] or "unnamed"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "FluxIntake/1"

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/health":
            _d, _i, _mode = dest_now()
            return self._json(200, {"ok": True, "dest": _d, "mounted": os.path.isdir(EXT),
                                    "stage": STAGE, "mode": _mode})
        if u.path == "/stats":
            n, tot = 0, 0
            try:
                for ln in open(IDX_EXT if os.path.exists(IDX_EXT) else IDX_STAGE,
                               encoding="utf-8"):
                    ln = ln.strip()
                    if not ln:
                        continue
                    j = json.loads(ln)
                    n += 1
                    tot += int(j.get("bytes") or 0)
            except Exception:
                pass
            return self._json(200, {"ok": True, "files": n, "bytes": tot})
        return self._json(404, {"ok": False, "err": "unknown-endpoint"})

    def do_PUT(self):
        u = urlparse(self.path)
        if u.path != "/artifact":
            return self._json(404, {"ok": False, "err": "unknown-endpoint"})
        # 令牌（可选启用）
        if os.path.exists(TOKEN_FILE):
            try:
                want = open(TOKEN_FILE, encoding="utf-8").read().strip()
            except Exception:
                want = ""
            if want and self.headers.get("X-Intake-Token", "") != want:
                return self._json(403, {"ok": False, "err": "bad-token"})
        q = parse_qs(u.query)
        node = (q.get("node") or [""])[0]
        card = safe((q.get("card") or ["na"])[0])
        name = safe((q.get("name") or ["artifact.bin"])[0])
        if node not in NODES:
            return self._json(400, {"ok": False, "err": "bad-node"})
        dest, index, mode = dest_now()
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._json(400, {"ok": False, "err": "bad-length"})
        if n <= 0 or n > MAX_BYTES:
            return self._json(400, {"ok": False, "err": "bad-size %d" % n})
        want_sha = (self.headers.get("X-Sha256") or "").strip().lower()

        day = datetime.now().strftime("%Y-%m-%d")
        outdir = os.path.join(dest, node, day)
        # 这里必须自己接住异常：TCC 拒写「可移除卷」时若让它冒泡，连接会被直接断掉，
        # 上传端只看到一个空响应，查不出是权限问题还是盘没插。
        try:
            os.makedirs(outdir, exist_ok=True)
            probe = os.path.join(outdir, ".writable")
            with open(probe, "a"):
                pass
            os.unlink(probe)
        except PermissionError as e:
            log("DENY %s write denied: %s" % (node, e))
            return self._json(503, {"ok": False, "err": "permission-denied",
                                    "hint": "TCC blocks removable-volume writes for launchd; "
                                            "grant Full Disk Access to /usr/bin/python3",
                                    "detail": str(e)[:160]})
        except OSError as e:
            log("FAIL %s cannot prepare %s: %s" % (node, outdir, e))
            return self._json(503, {"ok": False, "err": "dest-unavailable",
                                    "detail": str(e)[:160]})
        final = os.path.join(outdir, "%s__%s" % (card, name))

        h = hashlib.sha256()
        got = 0
        tmp = None
        try:
            fd, tmp = tempfile.mkstemp(dir=outdir, prefix=".part-")
            with os.fdopen(fd, "wb") as f:
                remain = n
                while remain > 0:
                    chunk = self.rfile.read(min(1 << 20, remain))
                    if not chunk:
                        break
                    f.write(chunk)
                    h.update(chunk)
                    got += len(chunk)
                    remain -= len(chunk)
            if got != n:
                raise IOError("short-read %d/%d" % (got, n))
            digest = h.hexdigest()
            if want_sha and digest != want_sha:
                raise IOError("sha mismatch got=%s want=%s" % (digest, want_sha))
            # 原子落地：先校验再改名，盘掉线不会留下半个文件当成品
            os.replace(tmp, final)
            tmp = None
        except Exception as e:
            if tmp and os.path.exists(tmp):
                try:
                    os.unlink(tmp)
                except Exception:
                    pass
            log("FAIL %s/%s %s" % (node, name, e))
            return self._json(500, {"ok": False, "err": str(e)[:200]})

        rec = {"ts": datetime.now().isoformat(timespec="seconds"), "node": node,
               "card": card, "name": name, "bytes": got, "sha256": digest,
               "stored": final, "mode": mode}
        with _lock:
            os.makedirs(os.path.dirname(index), exist_ok=True)
            with open(index, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        arch = archive_copy(final, node, day, card, name)
        if arch:
            log("ARCHIVED %s -> %s" % (name, arch))
        log("OK %s/%s %d bytes sha=%s mode=%s" % (node, name, got, digest[:12], mode))
        return self._json(200, {"ok": True, "stored": final, "bytes": got,
                                "sha256": digest, "mode": mode})


def pick_bind():
    """默认绑 tailnet 地址：只有 tailscale 内的设备能连，跨网到不了。"""
    want = os.environ.get("INTAKE_BIND") or "100.75.133.10"
    try:
        socket.inet_aton(want)
    except OSError:
        want = "127.0.0.1"
    return want


def main():
    port = int(os.environ.get("INTAKE_PORT", "11436"))
    bind = pick_bind()
    os.makedirs(DEST, exist_ok=True) if os.path.isdir(EXT) else None
    srv = ThreadingHTTPServer((bind, port), Handler)
    srv.daemon_threads = True
    log("intake listening on %s:%d -> %s" % (bind, port, DEST))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())