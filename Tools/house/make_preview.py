# -*- coding: utf-8 -*-
import io
import os

D = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..',
                                 'house', 'rental-conversion', 'drawings'))
files = sorted(f for f in os.listdir(D) if f.endswith('.svg'))
parts = []
for f in files:
    parts.append(f'<div class="wrap"><div class="cap">{f}</div><img src="{f}"></div>')
html = ('<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
        'body{margin:0;background:#dcd8d0;font-family:"Microsoft YaHei",sans-serif}'
        '.wrap{margin:18px auto;width:1260px;background:#fff;box-shadow:0 2px 10px rgba(0,0,0,.15)}'
        '.cap{padding:6px 10px;font-size:12px;color:#666;border-bottom:1px solid #eee}'
        'img{display:block;width:1260px}'
        '</style></head><body>' + ''.join(parts) + '</body></html>')
io.open(os.path.join(D, '_preview.html'), 'w', encoding='utf-8').write(html)
print('preview ok', len(files))
