# R-20261008-2dlive-alternatives-02 — 2D LIVE 非视频方法族谱（CEO 令 P-2026-10-08-03·B 波）
> 溯源：ledger P-2026-10-08-03（CEO 原话「考虑别的模型和方法，多方调研」）·消费方=CPH4 2dlive-spike+Biggame 吸嘟嘟·判据预注册=三问（①重定向族商用许可+8-16GB+Q版适配 ②插值族许可+显存+口碑 ③2D-native 工具谱+Inochi2D 翻案触发器核查）
> 验证声明：外部 20/20 封顶（成源 14·失败 6 透明列：champ LICENSE raw 404/DynaCrafter 仓名误 404×2/AnimeInterp LICENSE raw 404/X-Portrait2 LICENSE raw 404/Live2D license 页 404）+仓内锚件 2 直读+姊妹件 R-00/-01/-03 复用；源级全 A=GitHub/HF/官网原文直读；**调研员死于终稿撰写超时（数据 14 读全收）·本终稿=HQ 按其证据代笔收口（早落盘回收律）**。

## 一、四族总矩阵（族|代表件|许可|显存|Q版适配|判）
| 族 | 代表件 | 许可（A 级直读） | 显存 | 2D Q版适配 | 判 |
|---|---|---|---|---|---|
| R2 重定向驱动 | LivePortrait/X-Portrait2/Animate-X/MimicMotion/Champ | 见 §二 | 见 §二 | 见 §二 | Animate-X=族首候选🟡·X-Portrait2 判负 |
| R3 关键帧插值 | ToonCrafter/DynamiCrafter/AnimeInterp | Apache/Apache/MIT(宣称) | 10-12G 社区档 | ToonCrafter=2D 动漫特化 | ToonCrafter=族首候选🟡 |
| R4b 2D-native | AnimatedDrawings/Inochi Creator | MIT（全三件）/Inochi 待证 | CPU 级/桌面工具 | 人形骨架假设 | 工具位·归 R5 车道 |
| R5 骨骼+程序化（仓内） | 引擎原生 2D Animation+U312 | 引擎自带 | 0 | 构造性零漂移 | 混合收口增味件（不重研） |

## 二、R2 重定向驱动族深挖（逐件·许可原文指针）
- **LivePortrait**（KwaiVGI/KlingAI·19.2k★）：代码 MIT ✓+insightface 模型非商用（LICENSE 原文「The models of InsightFace are for non-commercial research purposes only…you should remove and replace InsightFace's detection models」）→**商用合规径=ComfyUI-LivePortraitKJ 换 MediaPipe 检测**（README 社区注记）；定位=人/猫/狗**头像**动画（驱动建议「Focus on the head area」）→全身 Q 版适配弱/待证；被快手/抖音/剪映/视频号采编在册。判=🟡 头像特写位候选·商用须换检测件。
- **X-Portrait 2**（ByteAIGC）：**判负**——仓无 license 徽章+内容仅 clip/static/index.html=项目页仓·**无代码无权重发布**（61★/28 commits 实锚）。留痕。
- **Animate-X**（antgroup/animate-x·ICLR 2025）：代码 Apache-2.0（LICENSE raw）；官方定位「universal animation framework…various character types (collectively named X), including anthropomorphic characters」=**Q 版对口宣称最强**；权重许可/显存/DWPose 依赖=待证（预算封顶）。判=族首试点候选🟡（权重许可装机前必核）。
- **MimicMotion**（Tencent）：主许可 Apache-2.0（LICENSE 原文「except for the third-party components listed below」）·第三方清单尾部未读=待证；人形视频模拟先验→Q 版适配弱（推测）。判=🟡 备选。
- **Champ**：LICENSE raw 404（仓路径漂移）→M 待证；SMPL 人形先验不适配 Q 版（推测）→判负嫌疑留痕+翻案触发器=许可证核验。
- **HQ 补记**：本族最新成员=Wan2.2-Animate-2（端到端·取消中间提取器·Apache·**本窗装机实弹在飞**·证据见 R-00 §二与 C10 批）。

## 三、R3 关键帧插值族深挖（逐件）
- **ToonCrafter**（Doubiiu·SIGGRAPH Asia 2024·6k★）：代码 Apache-2.0（LICENSE raw+徽章双验）；官方自认「open-source research exploration, instead of commercial products」+「success rate is not guaranteed」；规格 320×512·≤16 帧·官方 24-27G→**社区降到 ~10G**（README 原文）·ComfyUI fp16 pruned=12G→**bm-c 16G 可跑（确认）·bm-a 12G 边缘（推测）**；权重许可未单独声明=待证。判=**族首候选🟡**（母版摆 2-4 关键帧→AI 中割=身份按构造锁·与 R5 混合强耦合）。
- **DynamiCrafter**（Doubiiu·仓名修正）：Apache-2.0（LICENSE raw）；open-domain 写实域先验→2D 特化弱于 ToonCrafter（推测）。判=🟡 备选。
- **AnimeInterp**（lisiyao21·CVPR21·458★）：README 宣称 MIT 但 sidebar 无 license 文件=宣称级；torch 0.4-1.1 老栈·权重链接未声明许可。后继件 **AnimeInbet（ICCV23·卡通线稿中割）在册**（README 原文）。判=🟡 备选/后继待查。
- Sprite Sheet Diffusion（arxiv 2412.03685·R-03 留指针）：本波预算尽未核→M 待证留痕。RIFE/FILM VFI 基件：未及读取→M 待证（预算封顶）。

## 四、R4b 2D-native 族+翻案核查
- **Meta AnimatedDrawings**（facebookresearch·12.8k★）：**MIT 全三件**（README 原文「code, model weights, and Amateur Drawings dataset is released under the MIT license」）=全谱系最干净；**但 2025-09-03 已归档只读**；人形骨架假设（「primarily designed with human-like characters」·六臂四腿可手配）；CPU 可跑（Mesa headless）·BVH 动捕重定向。判=工具位（Q 版骨架假设不符·归 R5 车道参考件）。
- **Inochi2D 翻案核查（重大）**：09-29 判负根因=rigging app「in development」→**官网 Download 页实读：Inochi Creator 已正式发布可下载**（Win/mac/Linux·免费评估版+付费买断「free evaluation with 10-second reminder screen…or buy」·Inochi Session=免费直播件）=**翻案触发器命中**；Inochi Creator 自身许可/商用条款=待证（预算尽·HQ 防线二核验位）；运行时 BSD-2 乾净照旧。判=🟡 翻案候选（引擎绑定生态+CEO 09-29「影视级再议」位并行）。
- **Live2D**：license 页 404（URL 漂移·与 09-29 R 件同症）→维持 09-29 判负留痕（发布许可+付费+提前一月签约条款照旧引 §一锚）。

## 五、结论应用表（落点四选一）
| 结论 | 落点 | 状态 |
|---|---|---|
| Animate-X=重定向族首试点候选（Apache 代码·Q 版宣称最强·权重许可待核） | 任务单（A/B 试点·与 Wan-Animate 2 同窗对照） | 待批 |
| ToonCrafter=插值族首试点候选（Apache·社区 10-12G 档·2D 特化） | 任务单（关键帧插值试点·判负=成功率抽验不过） | 待批 |
| X-Portrait 2 判负留痕（无许可+无代码发布） | 判负留痕 | 已闭环 |
| Inochi Creator 已发布=翻案触发器命中（自身许可待证） | 决策呈报（翻案核验+影视级需求并行呈 CEO） | 待呈 |
| LivePortrait 商用合规径=换 MediaPipe 检测件 | 判负留痕（头像特写位保留·全身弱） | 已闭环 |
| Sprite Sheet Diffusion/AnimeInbet/RIFE-FILM 三 M 待证 | 任务单（后续窗补验） | 待证 |

- 更新记录：T0 骨架（调研员）→ T1-T4 四批 20/20 采集（调研员）→ 终稿 HQ 代笔收口（调研员终稿撰写超时亡·数据全收·早落盘回收律执法）。终稿 ~54 行。
- 防线二注记：两承重主张留 HQ 抽验=①ToonCrafter Apache-2.0+社区 10G 档（github.com 仓页/LICENSE raw 复读）②Inochi Creator 发布态（inochi2d.com/download 复读）。
