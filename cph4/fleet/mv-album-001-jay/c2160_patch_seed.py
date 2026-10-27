# -*- coding: utf-8 -*-
# c2160_patch_seed.py -- allow a per-unit "seed" in the i2v manifest (R4 re-render seed bands).
# Default behaviour stays the id-MD5 deterministic seed.
import io
import os
import py_compile

P = os.path.join("cph4", "fleet", "mv-album-001-jay", "local-i2v", "h3_i2v_album.py")
s = io.open(P, encoding="utf-8").read()
old = "        seed = seed_for(oid)\n"
new = ('        seed = int(u.get("seed") or 0) or seed_for(oid)'
       "  # per-unit seed override; id-MD5 remains the default\n")
assert s.count(old) == 1, "anchor count=%d" % s.count(old)
s = s.replace(old, new, 1)
io.open(P, "w", encoding="utf-8", newline="").write(s)
s2 = io.open(P, encoding="utf-8").read()
assert "per-unit seed override" in s2
py_compile.compile(P, doraise=True)
print("PATCH OK compile ok")