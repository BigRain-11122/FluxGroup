#!/usr/bin/env python3
"""probe_igd.py - read-only discovery of router port-mapping protocols (NAT-PMP / PCP / UPnP-IGD).

No mapping is created by this script; it only asks the gateway what it supports
and reports the external address. Safe to run repeatedly.
"""
import socket
import struct
import sys
import json

GW = "192.168.1.1"
TIMEOUT = 2.0
out = {"gateway": GW}


def natpmp_external_address():
    """RFC 6886: request external address (opcode 0)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(TIMEOUT)
    try:
        s.sendto(b"\x00\x00", (GW, 5351))
        data, _ = s.recvfrom(64)
        if len(data) < 12:
            return {"ok": False, "why": "short reply %d bytes" % len(data)}
        ver, op, result, epoch = struct.unpack("!BBHI", data[:8])
        ip = socket.inet_ntoa(data[8:12])
        # seconds since epoch of the mapping lifetime base
        return {"ok": result == 0, "result_code": result, "external_ip": ip,
                "lifetime_base_epoch": epoch, "raw_hex": data.hex()}
    except socket.timeout:
        return {"ok": False, "why": "timeout"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "why": repr(e)}
    finally:
        s.close()


def pcp_announce():
    """RFC 6887 ANNOUNCE (opcode 0) - proves PCP server presence, creates nothing."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(TIMEOUT)
    try:
        # version=2, R=0, opcode=0(ANNOUNCE), reserved=0, lifetime=0, client IP = 0.0.0.0
        pkt = struct.pack("!BBH I", 2, 0, 0, 0) + b"\x00" * 12
        s.sendto(pkt, (GW, 5351))
        data, _ = s.recvfrom(128)
        return {"ok": True, "bytes": len(data), "raw_hex": data.hex()[:64]}
    except socket.timeout:
        return {"ok": False, "why": "timeout"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "why": repr(e)}
    finally:
        s.close()


def upnp_ssdp():
    """SSDP M-SEARCH for InternetGatewayDevice; returns LOCATION urls."""
    msg = (
        "M-SEARCH * HTTP/1.1\r\n"
        "HOST: 239.255.255.250:1900\r\n"
        'MAN: "ssdp:discover"\r\n'
        "MX: 2\r\n"
        "ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1\r\n\r\n"
    ).encode()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.settimeout(TIMEOUT)
    locs = []
    try:
        s.sendto(msg, ("239.255.255.250", 1900))
        while True:
            try:
                data, addr = s.recvfrom(2048)
            except socket.timeout:
                break
            text = data.decode("utf-8", "replace")
            loc = ""
            for line in text.splitlines():
                if line.lower().startswith("location:"):
                    loc = line.split(":", 1)[1].strip()
            locs.append({"from": addr[0], "location": loc,
                         "server": next((l.split(":", 1)[1].strip()
                                         for l in text.splitlines()
                                         if l.lower().startswith("server:")), "")})
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "why": repr(e)}
    finally:
        s.close()
    return {"ok": bool(locs), "responses": locs}


if __name__ == "__main__":
    out["natpmp"] = natpmp_external_address()
    out["pcp"] = pcp_announce()
    out["upnp"] = upnp_ssdp()
    print(json.dumps(out, ensure_ascii=False, indent=1))
    # exit 0 always: this is a probe, absence is a valid answer
    sys.exit(0)
