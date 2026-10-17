# -*- coding: utf-8 -*-
# append_order_svfix.py — orders.md 追加 sv V1 修版派单行（UTF-8 追加·PS 编码律规避·一次性）
import io, sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\sjs20\Desktop\FluxGroup\docs\orders.md"
ts = datetime.now().strftime("%H:%M")
ROW = (
    "| 2026-10-17 " + ts + " | **@bm-c 执行 sv V1《慢慢踩》修版三连重装配（站5/6 REVISE 修项·导演席件已齐备·"
    "承 O-20261016-2110 三线质量令·纯 CPU 装配活零 GPU 冲突·MV 重烧 4 镜批次后接续）** | "
    "①git pull 后先读：cph4/fleet/meme-daily-v1/topics/v1-shots-v33.json（C2 拆 C2a 脚踩 1.2s[trim 1.9-3.1]+C2b 三车 1.0s 拍2 恒等 2.2s"
    "+热线窗 11.80→11.30）+tools/assemble_v1_33.py（c6 系统级禁止徽标）+meme-daily-v1/LEDGER.md J-M21 翻案行"
    "+DIRECTOR-GATE-sv-V1.md 修版执行记录；"
    "②两件入 K:/Fluxgroup/FluxGroup/media/meme-daily-v1/v1-zunjie-brake/："
    "clips/clip_S2fix.mp4（5.17s·-an 已剥轨）+frames/S2fix.png——源=git 树 cph4/fleet/meme-daily-v1/outbound/v1-zunjie-brake/fixwork/ 直复制"
    "（CDN 备胎=https://tuanjie-ai-prd.tos-cn-shanghai.volces.com/mcp-upload/f42b5224050071e550417c498174cb1a/clip_S2fix.mp4 "
    "与 https://tuanjie-ai-prd.tos-cn-shanghai.volces.com/aigc/image/1792200999_e19dd29b.png）；"
    "③python tools/assemble_v1_33.py --repo K:/Fluxgroup/FluxGroup --media K:/Fluxgroup/FluxGroup/media/meme-daily-v1/v1-zunjie-brake "
    "--out K:/Fluxgroup/FluxGroup/media/meme-daily-v1/v1-zunjie-brake/final（同名覆盖出片）；"
    "④成片 file_upload CDN+URL 回填本行回执节+HEAD 字节数；"
    "⑤验收物=新 v1-sucheng-brake-final.mp4（14.1s±0.1·拍2 脚部物理锚在场+拍5 热线行 1.1s+拍6 红环禁止徽标）→回 bm-a 站6 复签（J-M21 对账）+片级 GC "
    "| dispatched（@bm-c·回执窗 24h·lane=gpu-production 但本件 CPU 面） [via bm-a] |\n"
)
with io.open(P, "r", encoding="utf-8") as f:
    tail = f.read()[-200:]
with io.open(P, "a", encoding="utf-8", newline="\n") as f:
    if not tail.endswith("\n"):
        f.write("\n")
    f.write("\n" + ROW)
print("APPENDED at", ts)
