# R-20260928-alive3d-01-crowd-perf — WebGL 群体居民性能底（CEO 令「让硅基城市真正的活起来」·活性三波①）
> 溯源：CEO 令 2026-09-28·消费方=活性升维方案细胞活面+居民呈现形态决策·判据预注册=Q1-Q3
> 验证声明：实读 20 次（web 16·本地 4·预算 20/20 用尽）·成源 A 6 直读/B 1/C 6 快照·失败面：仓库名误写 404×2→消歧后成；GitHub MCP 凭证失效×3；unity.com 博客直读 403（快照摘录替代·降 B🟡）；VFXGraph 手册页过薄 compute 未直证→相关项降🟡
## 一、Q1 答面（instancing 技法与量级）
- 定位与平台【确认·A·https://docs.unity3d.com/2022.3/Documentation/Manual/GPUInstancing.html】：同 mesh 同材质单 draw call 渲多份·「GPU instancing is available on every platform except WebGL 1.0」；「By default, Unity WebGL builds support the WebGL 2.0 API」且 WebGL2 优势明列「Support for GPU Instancing」【确认·A·https://docs.unity3d.com/2022.3/Documentation/Manual/webgl-graphics.html】→项目 WebGL2 下 instancing 默认可用。
- URP 双坑【确认·A·GPUInstancing 页】：①SRP Batcher 优先级高于 instancing——GameObject 路（含 SMR）走 Batcher 不走 instancing·吃 instancing 须直绘 API（官方原文荐 Graphics.RenderMeshInstanced）；②「Unity does not support GPU instancing for SkinnedMeshRenderers」——骨骼人形本体不可 instancing。
- 硬数字【确认·A·https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Graphics.DrawMeshInstanced.html】：单调用上限 1023 实例（多批可叠·每批一 draw）；整组 AABB 剔除·不逐实例视锥剔除（离屏照画→区景档须自行分区批）；per-instance 属性走 MaterialPropertyBlock→居民状态着色可用；该 API 已 obsolete→RenderMeshInstanced。
- 顶点阈值【确认·A·GPUInstancing 页】：<256 顶点 mesh 不宜 instancing（GPU 摊不满）→光点 billboard（4 顶点）不宜此路·官方建议单 buffer 合批；500-2000 面人形（AD-042 在库·几百~2 千面=R-02 技能锚）≈250-1000 顶点·在阈值上。
- AnimationInstancing 官方仓定谳【确认·A·https://github.com/Unity-Technologies/Animation-Instancing（带连字符·README 直读）】：声明特性=Instancing SkinnedMeshRenderer/root motion/attachments/LOD/Support mobile platform/Culling——未声明 WebGL；README 最低 Unity5.4（2016 代技术·与 2022.3 版本锚不符注记）；https://github.com/Unity-Technologies/Animation-Instancing/issues/121（2022-10-27「Can't this work on WebGL build」）至今 Open 零官方回复→WebGL 支持度=⬜ 无官方定谳·判负不采为承重依赖。
- 30fps 量级例证：官方无 WebGL 实例数公开数字=⬜ 如实标注；最接近权威主张=官方博客「标准 SkinnedMeshRenderer+Animator 只能几十个角色…VAT+GPU instancing 可 push thousands of animated entities」【🟡B·https://unity.com/blog/rendering-at-scale-efficient-strategies-for-massive-object-counts·快照摘录】；社区侧证=WebGL 无 ComputeShader·桌面 10 万 instanced cube 案不可照搬【C·https://discussions.unity.com/t/gpu-instance-in-webgl/913863 快照】；工程推断🟡：区景档可承重域=假动画/VAT 人形数百~数千+光点万级（真瓶颈=单线程 WASM 矩阵更新+填充率）→数字定谳须闸3 实测（30fps 底线）。
## 二、Q2 答面（skinning 限制与绕行技法）
- 官方定谳复核【确认·A·https://docs.unity3d.com/2022.3/Documentation/Manual/webgl-performance.html】：原文「The JavaScript language does not support multi-threading or SIMD…One example is mesh skinning, which is both multi-threaded and SIMD-optimized」→在册坑律成立·措辞修正：非「skinning 整体失效」而是「skinning 的多线程+SIMD 双优化失效→蒙皮动画在 WebGL 显著变贵」；同页：GPU 侧近原生·CPU(WASM)=瓶颈面。
- GPU/CPU 蒙皮路径：预算内未获官方直证 ⬜（社区传 WebGL 强制 CPU 蒙皮·未采信为结论）。
- 绕行①序列帧贴片：quad+贴图集换帧·零 skinning 不触坑；WebGL 无相关限制记载→可用🟡（无官方专页直证）；成本=overdraw+贴图带宽。
- 绕行②VAT（顶点动画纹理）：社区工具链成熟（isrooky/VAT-Mass-Instancing·VATMachine·UnityVATBaker【C 快照】）+官方博客「数千动画实体」背书【B🟡】；WebGL2≈OpenGL ES 3.0【确认·A·webgl-graphics 页】·顶点纹理采样为 ES3 核心能力→WebGL2 可用🟡·URP 须自写 shader 工程化+闸3 实测。
- 绕行③无骨骼假动画（位移/弹跳/朝向变化）：纯 A 级原语直构（实例矩阵+per-instance 属性）→WebGL2 可用【确认】·最省最稳·首选；位移轨迹=真实作息数据·形变仅呈现层——合禁装饰性动画律。
- 工具面附注【🟡】：VFX Graph 须 compute shader·WebGL 无 compute（C 快照证+WebGL2≈ES3.0 规范事实）→光尘/光点禁走 VFX Graph·须 CPU ParticleSystem 或自写合批 quad。
## 三、Q3 答面（人形 vs 光态载体对比）
- 骨骼人形（Animator+SMR·AD-042 量级）：不可 instancing（A）+双优化失效（A）→同屏几十即掉性能【B🟡】→区景档不可承重。
- VAT 低模人形：绕开 SMR·可 instancing·面数在 256 顶点阈值上→数千级【B🟡】；身份感强（个体=真实居民投影·细胞活面叙事承重）·代价=烘焙管线+URP shader 工程量。
- 发光生命体（billboard 光点/低模光态·4-16 顶点 unlit）：<256 顶点→官方明示不宜 instancing·走单 buffer 合批/CPU 粒子【确认·A】；瓶颈=填充率；量级=万级🟡（比 VAT 人形高一档·比骨骼人形高约三档）·WebGL 实测待闸3⬜；语义弱（个体身份感低·与真实居民叙事有张力）。
- 定谳：数量级=光态≫VAT 人形≫骨骼人形；语义=人形≫光态；30fps 底线下区景档建议=VAT 人形（数百·身份层）×光点（万级·密度层）混合呈现·呈 CEO 裁。
## 四、结论应用表（research-protocol 强制·落点四选一：任务单/法文修改/决策呈报/判负留痕）
| 结论 | 落点 | 接线 |
|---|---|---|
| 技法定谳：区景档承重=③假动画（A 原语·首选）+②VAT（量级跃升·工程化+闸3 实测）；禁 Animator+SMR 群体路；AnimationInstancing 判负不采（⬜WebGL 无定谳） | 任务单：《城市活性 3D 升维方案》细胞活面·居民实装技法节 | 待派 |
| 载体对比：骨骼几十/VAT 人形数千/光点万级（A/B/C/🟡 分级如实）·instancing 批内 1023 上限·离屏不逐实例剔除须分区批 | 决策呈报：CEO 居民 3D 呈现形态决策（建议 VAT 人形×光点混合） | 待呈 |
| 坑律复核：「WebGL skinning 失效」→修正「skinning 双优化失效（多线程/SIMD）·蒙皮动画显著变贵」（A 直证）；新增坑律：SMR 不吃 instancing+SRP Batcher 优先于 instancing+<256 顶点不宜 instancing | 法文修改：R-02 七坑律措辞+City3D 坑律速查（lowpoly-city-3d 技能§三） | 待改 |
| 光尘工具面：总览档光尘禁 VFX Graph（WebGL 无 compute🟡）→CPU ParticleSystem/自写合批 quad | 任务单：活性三波②总览档光尘技法节 | 待派 |
- 更新记录：T0 骨架落盘→T1 官方 4 页直读+Q2 定谳落盘（web4）→T2 WebGL2 默认态/VFX 页采集（web3·404×1）→T3 本地锚（R-02 坑律/AD-042）+三路搜索快照+MCP 失败×3→T4 仓库名消歧+README/Issue#121 直读（404×2 后成）→终稿 30 行·预算 20/20 用尽。
- 防线二（主会话 2026-09-28 22:4x）：两承重主张直读复核过——GPUInstancing 页原文逐字命中（SMR 不可 instancing/SRP Batcher 优先/除 WebGL1.0 外全平台）+webgl-performance 页原文逐字命中（JS 无多线程/SIMD·skinning 双优化失效措辞修正采纳）；坑律修正已入 lowpoly-city-3d 技能。
