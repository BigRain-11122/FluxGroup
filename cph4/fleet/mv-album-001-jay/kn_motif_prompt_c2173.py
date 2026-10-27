# kn_motif_prompt_c2173.py - how many of the 30 authored KN i2v prompts ask for the same
# "paper plane over the city" setup? The felt repetition in the interim cut either comes from
# the shot list (authored) or from the model converging, and the fix differs: an authored
# cluster has to be spaced or re-framed, a model convergence has to be re-burned.
import io
import json
import os

MANIFEST = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay\local-i2v\run-bmc-kn-i2v.json"
units = json.load(io.open(MANIFEST, encoding="utf-8"))["units"]
rows = []
for u in units:
    p = u.get("i2v_prompt", "")
    rows.append({"id": u["id"], "plane": "paper plane" in p.lower(),
                 "city": ("city" in p.lower()) or ("skyline" in p.lower()),
                 "frame_in": ("in frame" in p.lower()) or ("close-up" in p.lower())})
plane_city = [r["id"] for r in rows if r["plane"] and r["city"]]
plane_any = [r["id"] for r in rows if r["plane"]]
print("total=%d plane_any=%d plane_and_city=%d" % (len(rows), len(plane_any), len(plane_city)))
print("plane_and_city:", ", ".join(plane_city))
print("plane_any:", ", ".join(plane_any))