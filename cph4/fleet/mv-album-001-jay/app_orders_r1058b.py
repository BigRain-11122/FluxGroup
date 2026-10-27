# -*- coding: ascii -*-
# app_orders_r1058b.py - append the r1058 window full receipt row to
# docs/orders.md (byte-preserving, EOL-detecting, idempotency guard).

import os

REPO = r"K:\Fluxgroup\FluxGroup"
ORD = os.path.join(REPO, "docs", "orders.md")
ROWFILE = os.path.join(REPO, "media", "mvtools", "scripts_r1058",
                       "orders_row_r1058b.txt")
GUARD = "r1058-receipt-mimicmotion-done"


def main():
    with open(ORD, "rb") as f:
        raw = f.read()
    if GUARD.encode("utf-8") in raw:
        print("SKIP row already present")
        return
    with open(ROWFILE, "rb") as f:
        rows = f.read().strip()
    eol = b"\r\n" if b"\r\n" in raw else b"\n"
    if not raw.endswith(eol):
        raw = raw + eol
    with open(ORD, "wb") as f:
        f.write(raw + rows + eol)
    print("APPEND %d bytes (eol=%s)" % (len(rows), eol))


if __name__ == "__main__":
    main()
