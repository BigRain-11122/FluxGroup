#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mail-direct-send.py — FluxGroup direct-to-MX email sender (no SMTP auth code needed).

Rationale (CEO order O-20261006-1215): QQ-mail SMTP authorization codes are
blocked/unavailable. Standard email delivery does not require any auth when
connecting DIRECTLY to the recipient domain's MX servers — auth codes only
matter when relaying through a provider's submission service (port 465/587).

Usage:
  python Tools/mail-direct-send.py --to sjs208@qq.com \
      --from-addr flux-brief@fluxverse.cn \
      --subject "FluxGroup Brief" --body-file docs/audits/CEO-brief.md
      [--helo dasheng.fluxverse.cn] [--timeout 30] [--save-transcript PATH]

Exit codes: 0 = queued by remote MX (250); 2 = protocol rejection;
3 = connection failure; 4 = bad args/local error.
"""
import argparse
import os
import random
import re
import smtplib
import socket
import ssl
import subprocess
import sys
import time
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

DNS_SERVER_FALLBACK = "114.114.114.114"


def resolve_mx(domain):
    """Return sorted MX hostnames for a domain (lowest preference first)."""
    try:
        out = subprocess.run(
            ["nslookup", "-type=mx", domain, DNS_SERVER_FALLBACK],
            capture_output=True, timeout=15,
        ).stdout.decode("utf-8", "replace")
        pairs = re.findall(r"MX preference = (\d+), mail exchanger = (\S+)", out)
        pairs.sort(key=lambda x: int(x[0]))
        hosts = [h for _, h in pairs if h and not h.startswith("UnKnown")]
        if hosts:
            return hosts
    except Exception:
        pass
    return [None]  # sentinel: fall back to bare A record of the domain


def spf_exists(domain):
    """Cheap check: does the sender domain publish an SPF TXT record?"""
    try:
        out = subprocess.run(
            ["nslookup", "-type=txt", domain, DNS_SERVER_FALLBACK],
            capture_output=True, timeout=15,
        ).stdout.decode("utf-8", "replace")
        return "v=spf1" in out
    except Exception:
        return False


def build_message(from_addr, to_addr, subject, body_text):
    """Build a UTF-8 plain-text message with honest headers."""
    msg = MIMEText(body_text, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=from_addr.split("@")[-1])
    msg["X-Mailer"] = "FluxGroup mail-direct-send v1.0 (direct-MX, no relay auth)"
    msg["Auto-Submitted"] = "auto-generated"
    return msg


def send_via_mx(mx_host, port, helo_name, from_addr, to_addr, msg_bytes, timeout, use_starttls=True):
    """Speak raw SMTP to the MX. Returns (final_code, transcript_text)."""
    transcript = []

    def trace(direction, data):
        text = data.decode("utf-8", "replace").rstrip("\r\n")
        transcript.append("%s %s" % (direction, text[:300]))

    sock = socket.create_connection((mx_host, port), timeout=timeout)
    try:
        f = sock.makefile("rb")
        sock.settimeout(timeout)

        def read_reply():
            lines = []
            while True:
                raw = f.readline()
                if not raw:
                    break
                trace("<-", raw)
                lines.append(raw)
                if len(raw) < 4 or raw[3:4] != b"-":
                    break
            return lines

        def send_cmd(cmd_bytes):
            trace("->", cmd_bytes)
            sock.sendall(cmd_bytes)
            return read_reply()

        greeting = read_reply()
        code0 = int(greeting[-1][:3]) if greeting else 0
        if code0 != 220:
            raise smtplib.SMTPConnectError(code0, b"greeting rejected")
        r = send_cmd(("EHLO %s\r\n" % helo_name).encode("ascii"))
        ehlo_lines = b"".join(r)
        starttls_ok = use_starttls and b"STARTTLS" in ehlo_lines
        if starttls_ok:
            r = send_cmd(b"STARTTLS\r\n")
            if int(r[-1][:3]) == 220:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                sock = ctx.wrap_socket(sock)
                f = sock.makefile("rb")
                send_cmd(("EHLO %s\r\n" % helo_name).encode("ascii"))
        r = send_cmd(("MAIL FROM:<%s>\r\n" % from_addr).encode("ascii"))
        mail_code = int(r[-1][:3])
        if mail_code != 250:
            return mail_code, "\n".join(transcript)
        r = send_cmd(("RCPT TO:<%s>\r\n" % to_addr).encode("ascii"))
        rcpt_code = int(r[-1][:3])
        if rcpt_code != 250 and rcpt_code != 251:
            return rcpt_code, "\n".join(transcript)
        r = send_cmd(b"DATA\r\n")
        data_code = int(r[-1][:3])
        if data_code != 354:
            return data_code, "\n".join(transcript)
        payload = msg_bytes.replace(b"\r\n.", b"\r\n..") + b"\r\n.\r\n"
        sock.sendall(payload)
        trace("->", b"[body %d bytes + terminator]" % (len(msg_bytes)))
        r = read_reply()
        final_code = int(r[-1][:3])
        send_cmd(b"QUIT\r\n")
        return final_code, "\n".join(transcript)
    finally:
        try:
            sock.close()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True, dest="to_addr")
    ap.add_argument("--from-addr", required=True, dest="from_addr")
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--helo", default="dasheng.fluxverse.cn")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--save-transcript", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if "@" not in args.to_addr or "@" not in args.from_addr:
        print("bad address syntax", file=sys.stderr)
        return 4
    body_path = args.body_file
    if not os.path.isfile(body_path):
        print("body file missing: %s" % body_path, file=sys.stderr)
        return 4
    with open(body_path, "rb") as f:
        body_text = f.read().decode("utf-8", "replace")

    rcpt_domain = args.to_addr.split("@")[-1]
    from_domain = args.from_addr.split("@")[-1]
    mx_hosts = resolve_mx(rcpt_domain)
    print("[mx] %s -> %s" % (rcpt_domain, ", ".join(h or "(A fallback)" for h in mx_hosts)))
    print("[spf] sender domain %s SPF record present: %s" % (from_domain, spf_exists(from_domain)))

    msg = build_message(args.from_addr, args.to_addr, args.subject, body_text)
    msg_bytes = msg.as_bytes()
    print("[msg] subject=%s bytes=%d" % (args.subject, len(msg_bytes)))
    if args.dry_run:
        print("[dry-run] no network send performed")
        return 0

    last_rc, last_tx = 3, ""
    for mx in mx_hosts:
        host = mx
        if host is None:
            host = rcpt_domain
        try:
            print("[smtp] connecting %s:25 ..." % host)
            code, tx = send_via_mx(host, 25, args.helo, args.from_addr, args.to_addr,
                                   msg_bytes, args.timeout)
        except Exception as e:
            print("[smtp] %s failed: %s" % (host, e))
            code, tx = 3, str(e)
        last_rc, last_tx = code, tx
        if args.save_transcript:
            with open(args.save_transcript, "w", encoding="utf-8") as f:
                f.write(tx)
        print("[smtp] %s final code=%d" % (host, code))
        if code == 250:
            print("[result] QUEUED by %s — protocol-level delivery accepted" % host)
            return 0
        # 4xx -> transient, try next MX; 5xx -> permanent rejection, still try next MX for evidence
        time.sleep(1)
    print("[result] NOT accepted (last code=%d). See transcript." % last_rc)
    return 2 if last_rc != 3 else 3


if __name__ == "__main__":
    sys.exit(main())
