# R-20261017-drama-ep-qc-anchorfix-01 — 批一抽检帧验定谳与锚系统修复报告

- 日期：2026-10-17 凌晨（承 2026-10-16 批一装配+抽检）
- 域：drama-001《一路长虹》60 集量产线（cph4/fleet/drama-001-stockera）
- 状态：根因定谳 · 补丁全落盘 · 重烧自愈中

## 一、批一装配实绩（2026-10-16）

- `drama_ep_assemble.py 1 10` → 10/10 MP4 落成（C:\Fluxgroup\FluxGroup\media\drama-eps\EP001-010.mp4）
- 规格：540×960 竖屏，74/62/73/75/76/80/76/77/76/71 秒，7.8-13.9MB/件，纯画面+硬字幕（音轨禁令 O-20261009 合规）

## 二、抽检结果（3 代表系多模态过审）

| 集 | 评分 | 指控 |
|---|---|---|
| EP001 | GO 9/10 | 微瑕：00:16 表带非钢链；00:55 蓝发人待核 |
| EP007 | NO-GO 4/10 | 00:49-00:51 满仓锚崩坏=瘦高白衬衫人 |
| EP010 | NO-GO 2/10 | 金发西装长虹/满仓黑风衣/熊长发/JoJo 画风混入/字幕裁切/逐镜 1 秒黑帧/字卡裁切 |

## 三、帧验实证（AI 诚实律：涉事帧抽 PNG 亲验，对照各镜 JSON spec）

证实（四真）：
- EP007 n15（49-52s，ids=[MC]）：帧=铁链倒吊青年+城市俯瞰；spec=满仓写字台特写。锚文本（chubby/floral shirt）零出现。
- EP010 n10（ids=[CH,MANCANG]）：帧=岩壁洞穴+夸张肌肉巨人+浅金发西装瘦小人（JoJo 风实锤）；spec=交易大厅双人对镜。
- EP010 n16（ids=[MANCANG]）：帧=空旷商业街黑长风衣背影；spec=大厅人群回头+拖把立于大盘前。
- EP010 n20（ids=[XIONG]）：帧=黑长发披散+和服交领+青眼中性人物；spec=50 岁银鬓角黑西装佛珠特写。

不实（二驳）：
- 「逐镜 1 秒黑帧」=幻觉。blackdetect 客观实测 EP010 仅 69.0-70.96s 一段黑（片尾字卡白字面积<2%，设计内）；EP001 对照 10-12.04s（「十年后」转场卡，设计内）。装配源码转场=每镜 0.12s 淡入淡出。
- 「字幕裁切」证据不足。58s 抽帧=fade 交界单帧黑屏（无字幕可裁）；31s 帧三行字幕完整（「再教……」为台词原省略号）。字幕面 fontsize=30×wrap17=510px<540px 安全。

另证（一真，装配面）：EP010 片尾字卡裁切实锤。原文「来历，是查出来的，也是等出来的——沈红利的抽屉里，还压着一张照片。」22 字单行 drawtext，fontsize=48 下 11 全角字即超 540px；textfile 多行渲染按最长行宽计算 x 偏移，短行贴左缘、长行右溢，两行均被画面边缘截断。

## 四、根因定谳

### 4.1 anchor 炸弹（图像面，51% 镜带伤）

烧制器 expand() = `out.replace(k + ' ', IDS[k] + ', ')` 只认「大写 token+尾随空格」字面形态。剧本 60 集六个席位的 detail_en 方言分三谱系：

1. 全名形态（EP010-015 席）：Chang Hong / Man Cang / Hongli / Xiong Tiancheng —— token 零出现；
2. token+撇号形态（EP001-009 席）：MC's / CH's —— `'s` 非空格，不命中；
3. 描述方言（EP040-060 席）：young man in white shirt / round-faced man in loud floral shirt —— 文本自带描述但无 canon 锚，跨镜跨集人物面孔漂移。

全量审计（60 JSON × expand 模拟）：1236 非字卡镜中零锚 631 + 部分锚 66（51%），全锚 431 + 场景镜 108。EP010-015、EP040-060 两板块几乎全灭。附雷：EP025/026 席 ids 用中文「散户甲/散户乙」，IDS 字典无此键 → 12:41 起烧制 KeyError 卡死全线 11 小时（停在 EP025_02.png）。

### 4.2 字卡折行缺失（装配面）

wrap_sub 限宽 17 单位为 fontsize=30 字幕量制；build_card 沿用同逻辑但 fontsize=48，未按 540px/48px≈11 字限宽折行。

## 五、修复动作（已全部落盘）

1. drama_ep_burn.py expand() 三件套：FULLNAME 全名→token 归一化（长在前防子串误伤）+ 正则注入（token 后跟空格/撇号/标点/结尾均命中，`CHIEF` 不误伤实证）+ anchor_of 未知 token 防 KeyError + 零锚兜底尾部 append canon 锚（描述方言席文内描述保留、一致性锚补齐）。9 涉事用例全绿（含散户甲防崩、EP040 兜底、partial 双锚）。
2. drama_ep_assemble.py：wrap_sub 参数化 limit；build_card 改逐行折行（limit=10）+逐行独立 drawtext 居中。EP010 片尾卡实测折 5 行每行 ≤10 单位。
3. 重烧律：旧命中 295 张保留；零/部分锚 233 张先备份 C:\Fluxgroup\archive\eps-kf-bak-20261016-anchorfix\ 再删；runner seed 确定性（91000000+ep*100+n）自愈重烧，REMAIN≈941。烧制顺序 EP001 起顺烧，批一缺口最优先补。
4. 工具件备份：C:\Fluxgroup\archive\tools-comfy-patched-20261017\（burn/assemble/runner 三件）。

## 六、产线状态与后续

- 烧制线：runner 8 分钟自愈拍在役（S4U drama-EPBurn-oneshot）；环境=bm-b 车道 10 分钟 GPU 清场，comfy 反复被杀由 runner 每拍自动重启，爬速推进（判例：勿手修）。
- 批一重装配：候 EP001-010 缺口 64 张重烧齐装后 `drama_ep_assemble.py 1 10` 重出 10 集 → 复抽检（重点：锚人物+片尾卡）→ CEO 首批呈报。
- 批二至批六顺次循环；全 60 集齐装后 runner 自停哨（60 JSON + REMAIN 0 → schtasks /DISABLE）。

## 附：判例索引

- 记忆 EPBurn 判例⑥（anchor 炸弹 v2·expand 三件套·重烧律）@CODELY.md 2026-10-17 00:05
- 记忆 批一抽检轮一判例（评审指控逐项帧验实证律）@CODELY.md 2026-10-17 00:05
- 前序：EPBurn 判例④⑤（ids 别名锚/健康判读）@CODELY.md 2026-10-16 12:17
