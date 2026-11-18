# -*- coding: utf-8 -*-
"""用 ezdxf 自带绘图插件把 DXF 回渲成 PNG，用于目检（不参与交付）"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

HERE = os.path.dirname(__file__)
DXF = os.path.abspath(os.path.join(HERE, '..', '..', 'house', 'rental-conversion', 'drawings', 'plan-A03.dxf'))
PNG = os.path.abspath(os.path.join(HERE, '..', '..', 'house', 'rental-conversion', 'drawings', 'plan-A03-preview.png'))

doc = ezdxf.readfile(DXF)
msp = doc.modelspace()
fig = plt.figure(figsize=(12, 12), dpi=110)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_facecolor('#ffffff')
ctx = RenderContext(doc)
backend = MatplotlibBackend(ax)
Frontend(ctx, backend).draw_layout(msp, finalize=True)
fig.savefig(PNG, facecolor='#ffffff')
print('PNG:', PNG)
