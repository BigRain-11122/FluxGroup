# -*- coding: utf-8 -*-
import io
import json
import os

base = os.path.join(os.environ["USERPROFILE"], ".codely-cli")
for name in ("model-config.json", "trusted_hooks.json", "settings.json"):
    p = os.path.join(base, name)
    print("==", name)
    if not os.path.exists(p):
        print("  (missing)")
        continue
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except Exception as e:
        print("  parse error:", e)
        continue
    text = json.dumps(d, ensure_ascii=False, indent=1)
    # hide obvious secrets
    import re

    text = re.sub(r'(?i)(sk-[A-Za-z0-9_-]{6,})', "<hidden>", text)
    text = re.sub(r'(?i)("(?:api[_-]?key|token|secret|password)"\s*:\s*")[^"]*', r"\1<hidden>", text)
    print(text[:2000])