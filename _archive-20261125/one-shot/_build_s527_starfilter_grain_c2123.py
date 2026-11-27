import io

SRC = r"K:\Fluxgroup\FluxGroup\cph4\fleet\idle-guard-kit\s527_starfilter_c2122.py"
DST = r"K:\Fluxgroup\FluxGroup\cph4\fleet\idle-guard-kit\s527_starfilter_grain_c2123.py"

s = io.open(SRC, encoding="utf-8").read()
pairs = [
    ('"""C2122: star-excluded artifact triage on the six zero-grain 4K plates.',
     '"""C2123: star-excluded artifact triage on the six SHIPPING grain-0.10 4K plates.'),
    ('after the locator was shown to flag stars on both grain and zero-grain substrates',
     'on the adopted grain-0.10 plates, so the sec-8 item-1 closure is verified where it matters'),
    ('*_4kraw.png', '*_4k_grain010.png'),
    ('xq-S527-STARFILTER-BOARD-c2122.jpg', 'xq-S527-STARFILTER-GRAIN-BOARD-c2123.jpg'),
    ('xq-S527-STARFILTER-c2122.json', 'xq-S527-STARFILTER-GRAIN-c2123.json'),
    ('c2122-s527-starfilter-triage', 'c2123-s527-starfilter-grain'),
    ('S527-STARFILTER-END', 'S527-STARFILTER-GRAIN-END'),
]
for a, b in pairs:
    n = s.count(a)
    assert n == 1, (a[:40], n)
    s = s.replace(a, b)
io.open(DST, "w", encoding="utf-8", newline="\n").write(s)
print("OK bytes=%d" % len(s))