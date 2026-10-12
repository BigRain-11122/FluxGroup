# SELF-AUDIT-v1 — BigStream 自审自查短板清单 + 工具补缺表 + 业界第一路线（O-20261012-2030）

> 溯源：CEO 令 2026-10-12 20:3x「你公司再去自审自查自己的短板，去github和一些专业网站找答案或者工具，好好做到业界第一」。

## 一、短板自审（诚实盘点·每条带今日实锚·禁粉饰）

| # | 短板 | 实锚 | 严重度 |
|---|---|---|---|
| 1 | **法厚器薄**：今天立了 10+ 部正典法，但配套自动化工具 ≈0——FRAME-GATE 五检/HOLD 律/情绪副词 lint/块字数检全靠人读 | 五检靠我肉眼·lint 三新检项只写进 spec 未实现 | **最高** |
| 2 | **法-品时差**：正典已业界级深（20 域矩阵），产品仍是半成品（鬼相/K 感/拍摄手法是样片阶段病） | 30s 样片=昨法产物·全曲版今晚才按新法烧 | 高 |
| 3 | **反馈零环**：零发布→零数据复盘→判例全来自内审·受众真实反应缺位 | 数据复盘件 ⬜ 从未启动 | 高 |
| 4 | **机队不完备**：bm-b 8G ComfyUI 未装+离线 12h+（满载包在案未消费）| 14:57 实测 GPU_COMFY_MISSING | 中 |
| 5 | **台账竞态税**：多窗同台账每轮 1-3 次冲突重放（我今日经历 4 轮 rebase）| worktree+双保循环已成 SOP 但成本在 | 中 |
| 6 | **模型浪潮跟踪零机制**：AI 视频生态月更（H3→Sora 弃用→Veo preview），我们无固定盯梢面 | arXiv 综述/社区榜今日才首次采 | 中 |
| 7 | **交付规格空白**：LUFS/码率/封装从没量过（prompt-architects 提醒「必须实测不能读页面」）| ⬜ 件从未落地 | 中 |

## 二、工具补缺表（GitHub/专业站定向猎取·弱点→工具→接入动作）

| 弱点 | 工具（源·星/等级） | 接入动作 |
|---|---|---|
| 帧闸自动化（#1 最高优先） | **ffmpeg-quality-metrics**（PSNR/SSIM/VMAF·CI 门禁化范式）+ **FastPix Video-Quality-Benchmark-Tool**（含 **temporal-flicker/motion-stability/audio-sync** 逐帧 JSON——**morph 漂移的客观量化器**）+ **Netflix libvmaf**（Emmy 级·5.5k 星） | 今夜装 bm-a/bm-c（CPU 级零 GPU）→ 装配站出口质量门禁：**回炉帧 vs 重烧帧 VMAF 对比**（客观判「修好了没有」）+ morph 检从人眼升客观指标 |
| 帧闸五检自动化 | 多模态判官脚本化（已有 analyze_multimedia 面）→ **frame_gate_check.py** 落 Tools/：catchlight/对称性/倒影脸/意图四要素逐帧 JSON 出分 | 明日 bm-a 夜窗实现（纯 CPU） |
| 提示词 lint 落地 | HOLD 句缺失/情绪副词表/动词计数/主体字数>风格块——**prompt_lint_v2.py** 扩展现有 lint | 同上 |
| 音乐-画面同步 | **librosa**（beat/BPM/乐句分析事实标准）→ 词窗表×beat 网格对齐脚本 | 随六路深研波 #9 |
| 交付规格 | ffmpeg **loudnorm**（EBU R128 内置）+码率/封装实测脚本 | 深研波 #17 首件 |
| 生产级一致性 | **Jellyfish**（6.3k·script→storyboard→跨镜一致性→final cut）+ **waoowaoo**（14.3k·工业级 AI 影视全流程）——已在 tw-mv-director 工具库·从未接入 | 评审：适配点=跨镜一致性管线的参照方案（不直接换栈·取其一致性实现思路） |
| 模型浪潮跟踪 | aicreativelead 综评/arXiv cs.CV 月扫→雷达班并入（M2/M3 周深扫加挂「AI 视频模型」面） | 下周雷达班起 |

## 三、业界第一路线（分阶段·可验）

**P0（本周）=「器补法」**：七类工具全部装机+frame_gate_check.py+prompt_lint_v2.py 上线——**判据=mv0001 全曲版成片闸全绿且 5 检自动出分**（不再靠导演肉眼当唯一检测器）。
**P1（两周）=「环闭合」**：首支发布→真实数据回流（完播/赞播/评论抓取→AUDIENCE-VOICE S2 面）→判例从内审扩到外验。
**P2（月度）=「浪潮盯梢」**：雷达班 AI 视频面+月度生态综评入 EXPERIENCE-LEDGER。
**判据总锚**：业界第一=「老粉认得出+新粉看不出 AI+同行抄不走」（L+F+G+P+A 公式全绿×真实数据验证）。

---
*v1·bm-a·2026-10-12 20:4x·工具源分级=B（GitHub 官方仓 Netflix/FastPix/ffmpeg-quality-metrics·librosa 事实标准）·接入纪律=MIT/Apache 直用·署名登记·AGPL 禁（承收获机制许可门）*
