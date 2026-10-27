# KN 整片装配收据 c2183 · 2026-10-24 14:45 · 《可爱女人》首条可看整片落地

- **本轮时间**：2026-10-24 14:17-14:46（tick = C2183，batch C2183，normal_iteration）
- **Step0**：preflight 全 PASS（INFO：LOCK 2m / GPU_COMFY_MISSING / NOT-GREEN-IDLE ram 11.4% vram 1.8G / foreign guid meta 14）
- **运行模式**：normal_iteration（10 分钟盒，实际超盒至 29 分钟——编码前三次失败排障计入，见坑录）

## 司实况（CEO 过程可见面·三行）

- **当前活**：《可爱女人》整片装配站 v1——把 30 单 768P 渲染按分镜表 41 个窗（30 新镜 + 11 重演窗）铺满 239.03s 全曲，落调色/字卡/AIGC 标/原曲音轨
- **最近实物**：`K:\Fluxgroup\FluxGroup\media\mv-album-001-jay\assembly-packA-KN\KN-FULL-v1-C2183.mp4`（239.04s / 5737 帧 / 1344×768 / 48k 立体声 / 89.8MB，14:44）
- **下个里程碑**：导演席拉片出 verdict + KN17/KN18 银河伪影处置（重烧或裁接受），窗 ≤48h

## 本轮实质产出

- **装配站（新）**：`cph4/fleet/mv-album-001-jay/kn_full_assembly_c2183.py`
  - 单一真值=分镜表脚本（import 读 NEW+REUSE，不手抄窗口）＋ i2v manifest（片源与光锚）；
  - 断言：41 窗覆盖 0→239.03 零空档零叠窗、逐窗片源在位、缺单不填占位；
  - **重演窗补足法**：源在 0.85 速地板下仍不足时，尾段用同一 take 的 punch-in 第二遍（crop 86% 回铺 + 亮度 +0.015），不用长冻结——星晴 v10 已验证的同一手法；
  - 调色按 GRADE-v1 六锚族逐镜落（roof_dusk / roof_night / city_bowl / city_moon / cloud_moon / warm_window / streak / galaxy_gold）；
  - 字卡=歌名卡（0.6-3.4s）+ 片尾权属卡（235.03-239.03s，"词曲著作权 / 录音制作者权 授权中"）+ 全片 AIGC 角标；
  - 音轨=原曲裁到歌长，loudnorm -14 LUFS，头 0.3s 淡入 / 尾 2.4s 淡出。
- **成片机检**：时长 239.042s、nb_frames 5737（=239.04×24）、h264 1344×768@24、aac 48k 双声道、bitrate 3.0Mbps；
  **逐帧哈希重复度：最长同哈希连跑 = 2 帧（0.083s）**，无多秒冻结/复读（原 tpad 方案会留 2.9s 冻结，已改 punch-in）。
- **字卡人眼核**：抽帧 1.6s / 236.5s 均实读——「可爱女人」上屏无豆腐块；片尾权属卡可读；AIGC 角标右下常在。
- **证据**：`KN-FULL-INDEX-C2183.json`（41 窗逐条：片源/窗长/有效速/拟合方式/pad/光锚）、抽检帧 `chk-1.6/60/120/236.5.png`。

## 导演席初判（详见 DIRECTOR-REVIEW-KN-FULL-v1-c2183.md）

- verdict = **REVISE**（不给 PASS）：
  - (红) **KN17/KN18 银河段伪影**：抽帧 120.0s 实读为金色线状/环状缠绕（似枝条、网状或虫形），不是星尘海；与「星星铺满夜空」的镜义冲突，sediment 感强。
  - (黄) 重演窗第二遍为 punch-in 放大（86% 源），清晰度略低于首遍，肉眼可辨但可接受；若导演席要求，可改第二 take。
  - (黄) 全片**零剪辑层转场**（全硬切）：本曲分镜自述「物质转场 + 全片唯一叠化在 KN20 内（渲染层）」，故 v1 不加编辑层叠化；与通用剪辑语法 CHK-E1（硬切 ≤70%）的偏差按「旧约束复审制」以本曲正身脚本为准，需导演席确认。
  - (蓝) KN04 自适应 0.8958 速仍在慢镜可读边缘（c2180 已记）。

## 资产台账

- **i2v 片**：《可爱女人》768P **30/30**；《星晴》PACK-B v10 母版待导演席复核
- **整片**：KN v1 239.04s（调色脊 + 字卡 + 原曲；编辑层转场 0；音轨 loudnorm 单遍）
- **门禁**：时间轴断言（0 空档/0 叠窗）✓、片源在位 ✓、帧唯一性（最长连跑 2 帧）✓、字卡人眼 ✓
- **缺口**：KN17/KN18 银河伪影处置；调色 v2（halation 位与逐锚实测）；导演席 verdict

## 问题清单

- (红) KN17/KN18 银河段金色线状伪影——重烧候选（480P 探针先行）或导演席裁接受
- (黄) 重演窗 punch-in 清晰度下降
- (黄) 编辑层零叠化 vs 通用剪辑语法偏差（本曲正身脚本覆盖，待导演席签）
- (蓝) KN04 慢镜边缘

## 坑录（本轮三坑全实证）

1. **ffmpeg drawtext 路径在 argv 直传下必须加单引号**：`fontfile=C\:/Windows/...` 直接传 argv 会被滤器解析器按 `C` + `:` 拆开（报 "No option name near '/Windows/...'"），正确形态是 `fontfile='C\:/Windows/Fonts/simhei.ttf'`（引号 + 逃逸冒号）。
2. **PowerShell 里 `$var:xxx` 是作用域语法**：`"...textfile=$te:fontsize=24..."` 会被吃成 `$te:fontsize` 作用域变量，拼出 `textfile==24`；内联验证一律用 `${te}`。
3. **pythonw + RedirectStandardError 抓不到子进程 stderr**：ffmpeg 自身的报错要 `subprocess.run(capture_output=True)` 显式回收并打印尾 3000 字符，否则只有 Python traceback（本轮两次盲试的时间代价）。

## 下轮选线

1. KN17/KN18 银河重烧（480P 探针 → 768P），伪影清零后重跑装配站（脚本幂等，一条命令）
2. 导演席拉片 verdict → 若 REVISE 项只余调色，进 v2 调色（halation 位 + 逐锚实测 + 盲评）
3. 星晴 PACK-B v10 母版复核（bm-a 侧）与本机并行不冲突

## 对方机摘要（A 机）

A 机以自动化快照与 orders.md 尾行为准（本机未新增对 A 派单）。