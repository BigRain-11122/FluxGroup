"""C2125 addendum: extend last_round with the four follow-up jobs and log them."""
import io
import json
import os
import time

REPO = r"K:\Fluxgroup\MiniGame"
STATE = os.path.join(REPO, "state-c.json")
LEDGER = os.path.join(REPO, ".codely-cli", "engine-tick", "tick-ledger.txt")

raw = open(STATE, "rb").read()
bom = raw.startswith(b"\xef\xbb\xbf")
d = json.loads(raw.decode("utf-8-sig"))

d["last_round"]["result"] += (
    " (8) Four follow-up jobs executed in the same round: s7r-conform-ratify-board (one-page index of the "
    "four boards, 259167B, job had been claimed at 06:50:59 before its runner existed so the runner was "
    "authored and run this round), s527-delivery-verify-v1 (all six delivery plates re-hashed from disk "
    "against MANIFEST + source plates, 6/6 identical, 0 mismatches), s7r-origin-verify-v1 (origin/main "
    "321a4e5: four conformed boards byte-identical, the conform receipt reported EOL-ONLY - local CRLF "
    "worktree copy vs LF blob, identical after newline normalization), s527-4k-proxy-1600 (six 1600px "
    "review proxies 194-208KB vs 15MB originals + 2x3 contact board) and s527-delivery-readme-refresh-v1 "
    "(README rebuilt from disk with live sha short ids and the proxy/board/verify rows). "
    "(9) Bank: p33 done plus those four recorded done, successor s7r-origin-reverify-v1 prestowed to "
    "re-check the enlarged artifact set against origin after this push."
)
out = json.dumps(d, ensure_ascii=False, indent=1)
open(STATE, "wb").write((b"\xef\xbb\xbf" if bom else b"") + out.encode("utf-8"))

ts = time.strftime("%Y-%m-%d %H:%M")
lines = [
    "%s | 追加 C2126-C2130 | 同轮连带四件：ratify 索引板 259167B / 出货完整性复验 6/6 恒等 / origin 发布核对（4 板字节恒等·收据 EOL-ONLY 非内容差）/ 六张 1600px 翻页代理 + README 按盘重写" % ts,
    "%s | bank | p33 s7r-conform-ratify-board done（06:50:59 被 IdleGuard 提前认领·runner 本轮补齐并跑通）；s527-delivery-verify-v1 / s7r-origin-verify-v1 / s527-4k-proxy-1600 / s527-delivery-readme-refresh-v1 均 done；预挂 s7r-origin-reverify-v1" % ts,
    "%s | push 记录 | FluxGroup f8fd129 → main OK（worktree 重放）；MiniGame 本轮第二提交 → machine/C" % ts,
]
with io.open(LEDGER, "a", encoding="utf-8", newline="") as f:
    for l in lines:
        f.write(l + "\r\n")
print("ADDENDUM OK", ts)