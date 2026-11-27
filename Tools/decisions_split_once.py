import re, io, os, shutil
root = r"C:\Users\sjs20\Desktop\FluxGroup"
src = os.path.join(root, "docs", "decisions.md")
arc = os.path.join(root, "docs", "decisions-archive-2026-11.md")
CUT = "2026-11-05"

def read(p):
    with open(p, "r", encoding="utf-8", errors="strict") as f:
        return f.read()

text = read(src)
lines = text.splitlines(keepends=True)
# split into (datekey, block)
blocks = []
cur = {"date": None, "lines": []}
for ln in lines:
    m = re.match(r"^##\s.*?(\d{4}-\d{2}-\d{2})", ln)
    if m:
        blocks.append(cur)
        cur = {"date": m.group(1), "lines": [ln]}
    else:
        cur["lines"].append(ln)
blocks.append(cur)

preamble = "".join(blocks[0]["lines"]) if blocks and blocks[0]["date"] is None else ""
body = [b for b in blocks[1:]] if blocks and blocks[0]["date"] is None else blocks

old = [b for b in body if b["date"] and b["date"] < CUT]
keep = [b for b in body if not (b["date"] and b["date"] < CUT)]

shutil.copy2(src, src + ".bak-prediv")
a = read(arc) if os.path.exists(arc) else ""
if a and not a.endswith("\n"):
    a += "\n"
with open(arc, "w", encoding="utf-8", newline="") as f:
    f.write(a + "\n" + "".join("".join(b["lines"]) for b in old))
with open(src, "w", encoding="utf-8", newline="") as f:
    f.write(preamble + "".join("".join(b["lines"]) for b in keep))

print("moved_blocks=%d kept_blocks=%d old_bytes=%d new_bytes=%d arc_kb=%.1f" % (
    len(old), len(keep), len(text.encode('utf-8')),
    os.path.getsize(src), os.path.getsize(arc)/1024))