# R-20260928-lowpoly3d-04-lighting — URP 灯光面（lowpoly3d 波·04 灯光）
> 溯源：lowpoly3d 波派工单·消费方=FluxVerse City3D（URP·Tuanjie 1.10.3≈Unity 2022.3·俯视角 lowpoly·Synty 平涂·WebGL 参观端·真实北京时间昼夜色轮：黄昏暖紫/夜蓝黑）·判据预注册=①日夜循环标准实现 ②Bloom/后处理 ③烘焙与灯预算
> 验证声明：实读 20 次触顶（纪律读 3+搜索 5+外链 11〔成 9/404×2〕+unity_docs 1）·成源 15（A=9/C=6/B=0）·失败面透明=post-processing-mobile.html 与 universalrp-features.html 双 404、GitHub API 按令规避未用、6000.x 文页用于 URP14 已逐条注记版本；关键结论 A 双源或 A+仓内锚件承接，未获证处一律 M 待样区验

## 一、日夜循环标准实现（判据①）
- 【确认·A】主灯槽：URP 取 Lighting 窗 Sun Source 指定的定向光为 Main Light，未指定则取场景最亮定向光〔URP14 URP Asset 手册〕→日夜脚本须锁此唯一太阳灯
- 【确认·A】脚本可控面：Light.intensity（与颜色相乘）；Light.colorTemperature（CCT：白 6500K/烛光 1800K/暖灯 2700K，须开 GraphicsSettings.lightsUseLinearIntensity+Light.useColorTemperature）；RenderSettings.ambientLight（平色环境光）；RenderSettings.sun（程序化天空盒太阳槽）〔ScriptReference×4〕
- 【确认·A】环境 cubemap 机制件：DynamicGI.UpdateEnvironment()=调度环境 cubemap 刷新（异步回读平台可滞后数帧、过频被静默忽略=无 crash；无异步回读平台逐面阻塞线程；替代=DynamicGI.SetEnvironmentData 直喂）〔ScriptReference〕
- 【待证·M】「运行时改天空盒后须调 UpdateEnvironment 才刷环境光」触发条件未直证（6000.6 版式原文未见此句）→实操取低频定时调用（1-5s·建议值）
- 【确认·C】社区成熟方案四源同构「旋转+曲线+环境光」三件套：URP 脚本 lerp 定向光 color/intensity+天空盒 _Exposure+正弦缓入+HDR 色〔Wayline 实读〕；太阳自转+环境/定向渐变+雾距+星空〔GitHub m-gebhard〕；AnimationCurve 驱动环境光/雾=专业做法〔unityqueen〕；「只需旋转定向光+压环境光」〔VionixStudio〕；预算内未见官方日夜循环专页（负发现，非断言）
- 【判定】落地组合：北京时间（UTC+8 换算·工程件 M）驱动定向光旋转+强度/色温曲线+环境光二选一——a)Source=Skybox+渐变天空盒+低频 UpdateEnvironment；b)Source=Color+ambientLight 曲线直写（零 cubemap 回读、色轮四档直控）→WebGL 的 supportsAsyncGPUReadback 未采证（M）保底走 b；黄昏暖紫/夜蓝黑色值归设计端
## 二、Bloom/后处理（判据②）
- 【确认·A】Bloom 参数〔URP14 手册·仓内 2D 线 sibling 同页双源承接〕：Threshold=gamma 空间阈，默认 0.9（低于阈不上晕）；Intensity 0-1 默认 0=必须显式开；Scatter 0-1 默认 0.7=晕半径；Clamp 默认 65472；Tint/Lens Dirt 可选
- 【确认·A】官方性能排查序（WebGL 照收）：①关 High Quality Filtering（bicubic→bilinear）②Downscale=Quarter ③降 Max Iterations（默认 6）④低分辨率 Lens Dirt
- 【确认·A】Tonemapping〔URP14 手册〕：Neutral=仅范围重映射、色相饱和影响最小、官方称「大幅调色的一般起点」；ACES=对比更强、影响实际色相/饱和、ACES 空间内 grading（Android Adreno 300 系不支持注记）→真实北京时间色轮需保档→**选 Neutral**（判定）
- 【确认·A】URP Asset 后处理/质量节：Grading Mode=HDR（tonemapping 前高精度调色）vs LDR（tonemapping 后经典流）；LUT Size 默认 32；Volume Update Mode=Every Frame 耗 CPU 可 Via Scripting；「需宽动态或 Bloom 则开 HDR」+HDR Precision 32bit 省带宽〔URP14 Asset/性能页〕
- 【待证·M】「开后处理令 MSAA 失效/降收益」无官方页明示（社区论坛有观察〔C〕）；官方仅定性 MSAA=内存带宽成本项、移动平台缺 StoreAndResolve 时 Opaque Texture 下 MSAA 被忽略〔A〕→WebGL 档 MSAA 按样区实测定
## 三、烘焙与灯预算（判据③）
- 【确认·A】灯上限〔6000.5 手册 Light limits in URP·URP14 未单页复核注记〕：默认 Forward 路径每物体上限 9 灯=1 主灯+8 Additional（默认逐像素，可改逐顶点；C 佐证：论坛称 8 帽源于 constant buffer 性能）；每相机 Additional 上限=桌面/主机 256·移动 32·OpenGL ES 3.0 及更早 16；主灯恒可见；加量须 Forward+/Deferred
- 【确认·A】WebGL 2.0「is derived from OpenGL® ES 3.0」〔Khronos 规范〕→16/相机为最贴近参考；URP 未将 WebGL 归入任一档（M）→参观端按 16 保守预算、样区校准
- 【确认·A】官方性能律〔URP14 configure-for-better-performance〕：低端「Additional Lights→Disabled 或 Per Vertex（Forward）」；静态物 Baked Lit/动态物 Simple Lit；低端关反射探针 Blending+Box Projection
- 【确认·A】烘焙体系〔2022.3 手册 Introduction to lighting〕：烘焙=提前算好存光照数据、运行时套用；Baked GI=lightmaps（静态物预渲染纹理）+Light Probes（存空间光传播信息，改善移动对象与静态 LOD 照明）+Reflection Probes；烘焙走 Progressive Lightmapper（CPU/GPU），Enlighten 烘焙已默认弃用
- 【判定】动态太阳×烘焙 GI：烘焙定义即「运行时套用不可变」→连续昼夜下太阳贡献不可烘→维持基线「斜定向光实时+烘焙只走 AO」；车流/行人接 Light Probes；URP14 Asset 灯光节（Per Object Limit 滑条+Mixed Lighting+探针+SH Evaluation）齐备〔A〕
- 【推测】大城市场景 lightmap 体积/内存对 WebGL 加载与内存压力未获官方数字→「探针为主、lightmap 面积克制」执行、样区实测
- 【建议】参观端灯预算（依据=A 性能律+灯上限）：附加灯 Per Vertex·Per Object Limit≤4（硬帽 8 内取保守·默认值未采证 M）·实体附加灯 0-4 盏；窗灯/霓虹一律自发光+Bloom 不占灯数（2D 线同判承接）
## 四、增量判定与适配
- 增量判定：sibling R-20260928-td-craft-light-daynight=URP 2D（Light2D）线，不覆盖本件 3D 定向光/烘焙/逐像素灯域；其 URP14 Bloom 参数段本件已双源承接——增量成立，非重复调研
- 适配：俯视远景+Synty 平涂→灯种二分即闭环=一盏实时太阳（主灯）+窗灯自发光；实体附加灯只留地标/街心；Forward 为默认路径〔A〕，Forward+ 的 WebGL 支持面未采证（M）不启
## 五、结论应用表（落点四选一）
| 结论 | 落点 | 状态 |
|---|---|---|
| 日夜三件套=北京时间驱动定向光旋转+强度/色温曲线+环境光建议 Source=Color 曲线直写（Skybox 源+低频 UpdateEnvironment 留备选） | 任务单（施工参数单·灯光节） | 接线中 |
| 后处理档=Neutral Tonemapping+Bloom 初值组（M 待样区校准：Threshold 0.9 起步、HDR 自发光可上移 1.0+·Intensity 0.5-0.8·Scatter 0.7·HQ Filtering 关·Downscale=Quarter·MaxIterations≤6） | 任务单（施工参数单·灯光节） | 接线中 |
| 灯预算=附加灯 Per Vertex+Per Object Limit≤4·实体附加灯 0-4 盏·窗灯零实体灯·HDR 开+Precision 32bit | 任务单（施工参数单·灯光节） | 接线中 |
| Phase 1 窗灯改造=窗材质 Emission HDR 1.5-3（M 初值）入夜曲线抬升+Bloom 收晕；白天压回阈值下；禁逐窗实体灯 | 任务单（Phase 1 窗灯改造） | 接线中 |
| WebGL 待证组移交样区=异步回读支持·每相机灯档归属·MSAA×后处理·Bloom 阈值上移·Per Object Limit 默认值 | 任务单（样区实证注记） | 已闭环（移交） |
- 更新记录：T0 骨架落盘→T1 搜索 3+官方 4 页（灯上限/UpdateEnvironment/URP Asset/性能页）→T2 URP Asset 后半+Bloom/Tonemapping（404×2 记失败）→T3 ScriptRef API×4+Wayline+Khronos→T4 烘焙 GI 2022.3 页→终稿 20 读触顶·38 行
- 防线二：（留空待主会话抽验）
