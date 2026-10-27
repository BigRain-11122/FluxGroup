# R-20260930-cs-06-lighting-pairing — 城市灯光搭配配方面（CEO 令 2026-09-30·cs-city 波）
> 溯源：CEO 令 2026-09-30 原话（见上）·消费方=City3D 重构主线 R4 光影成色（含室内光池）+city-3d-lighting 技能正典增补·判据预注册=Q1 URP 大场景光影搭配官方配方带源（light layers/阴影级联/SSAO/探针布设）/Q2 可进入建筑的室内照明做法带源/Q3 夜景城市灯光组合序（雾×bloom×emission×环境光）外部佐证+转译 ≥8 条
> 验证声明：终稿=外部读取共 19 次（fetch 14·内含失败/被拦 6 次计入；search 3；unity_docs 2）；成源 15 条=A 官方 7（URP13.1 light-layers/URP14 资产 Shadows/URP14 Shadows 页/URP14 SSAO/Manual LightProbes/Manual ReflectionProbes/Manual Lightmapping）+B 权威 1（ps1ke·CS2 反编译 API 文档）+C 社区 4（bugnet/discussions 室内外帖/Paradox 夜窗帖快照/CS2 夜景批评帖快照）+M 待证 3（SSAO WebGL 实测/InteriorMapping 推测/URP14 无 SSGI·SSR 未见官方页）；关键结论双源达标（Light Layers=A 官方+C 社区用法·emissive 主导=B+Paradox 快照）；防重红线核对=雾距/五色律/夜黑场/bloom 默认值/灯帽/只烘 AO 均按「正典不重采」引用未新采。

## 一、URP 光影搭配官方面（Q1）
- **Light Layers 机制（A·URP13.1 官方 light-layers 页·URP14 同机制）**：开启=URP 资产 Lighting 段(⋮)Show Additional Properties→勾 Light Layers；开启后每盏 Light 多出两属性：**General>Light Layer**（勾选影响哪些层）+**Shadows>Custom Shadow Layers**（被排除物体仍可对该光投影）；物体侧=Mesh Renderer>Additional Settings>**Rendering Layer Mask**（取消勾选即不被该光影响）；改名=Project Settings>Graphics>URP Global Settings>**Light Layer Names (3D)**（8 槽）；**坑：开启即禁用灯光的 Culling Mask**（外观/室内双态切换只能走 Rendering Layer Mask 路）。Unity 6 新统一 Rendering Layers 系统=版本不可用（我方 2022.3 无）。
- **阴影级联/距离（A·URP14 官方 universalrp-asset）**：Shadows 段=Main Light（Sun Source 槽指认·未指认取最亮定向光）→Cast Shadows→ShadowResolution→**Max Distance**（米制·以相机为起点·超出不渲影）→**Cascade Count**（官方原话：级联可避免近处粗影并压低分辨率占用·**增多即降性能·仅作用主光**）+Split 1..n 分界距离。俯视搭配：L0 320m 高机位=Max Distance 随相机档≥600（定谳·技能正典）+**级联取 2-4**（远处精度靠末级距而非全图加密）。
- **每光 bias 官方旋钮（A·官方 Shadows 页）**：Light>Shadows 把 Bias 从 Use Pipeline Settings 改 Custom→展开 Depth Bias/Normal Bias/Near Plane；**官方明示高 bias=光穿模泄漏**（影与投体脱节）——室内/楼缝防漏光先调此三参，禁先加灯。
- **SSAO（A·URP14 官方 post-processing-ssao）**：挂法=加在 URP Renderer 上→该 Renderer 全部相机生效；Method=Interleaved Gradient Noise（静态）vs Blue Noise（动态·动帧更细腻）；Source=**Depth Normals**（走 DepthNormals Pass·法线更准）vs **Depth**（免该 Pass·深度重建法线·Normal Quality 采样 Low1/Med5/High9）；Intensity/Radius 性能影响官方原话=**Insignificant**。WebGL：官方文档**无平台排除条款**（未列不支持）→可用性=「无排除」+**样区实测待证**双态。
- **SSAO 布线排障（C·bugnet 实测文）**：五件套对齐=URP 资产开 **Depth Texture**→Renderer Data 挂 SSAO feature→**相机 Post Processing 勾开**（不开则全后效静默跳过）→Source 选 Depth Normals（最佳质）/Depth（更快）→**Frame Debugger 验 SSAO pass**（应在 Depth Normals pass 后）；性能：桌面 1-3ms（C 原话）·移动降 Sample/Source 或独立 Renderer Data 分平台——WebGL 端按移动法对待（低档+实测）。我方 URP14 无官方 SSGI/SSR 对应件=待证（M·未见官方页·Unity 6 才有则标版本不可用）。
- **Light/Reflection Probes（A·官方 Manual）**：Light Probes=存空间中传播的烘焙光→动态物近似间接光（+LOD 静景用）；Reflection Probes 布设官方律=**「反射观感会明显变化之处必设」**（隧道口/建筑旁/地面换色点），多探针间**插值渐变**——城市级转译=街区网格布 Light Probes+地标节点加密 Reflection Probes。
## 二、室内照明面（Q2·可进入建筑独有需求）
- **室内外隔离官方法（A·Light Layers 官方页）**：日光/月光主光的 Light Layer 取消勾选「Interior」层→定向光永不入室；室内灯勾 Interior 层+室内网格 Rendering Layer Mask 只含 Interior→双向不污染；外墙/屋顶开 **Custom Shadow Layers** 保住对主光的投影（防影穿帮）。**外观档/室内档双态切换正路=相机 Culling Mask 切网格组**（Light 组件的 Culling Mask 已被 Light Layers 禁用=官方坑，只能此路）。
- **室内漏光三源（C·discussions.unity 室内外同场景帖·2023 实答）**：①定向光直射（开影+调级联/距离即止）②**天空盒环境光间接渗入=最大坑**（答者原话：Unity 光「只算直射」，间接光默认来自 skybox·无遮蔽概念）③无反弹 GI。对策=环境光 Source 由 Skybox 换 **Color**（我方正典 Color 直写曲线同构·此处外部佐证）或烘焙（C 原话：烘 lightmap 后 skybox 间接不再贡献 lightmapped 物体）；Enlighten 路不可依赖（A·官方 Lightmapping 页：Enlighten 烘焙后端 2022.2 起 UI 默认隐藏·2023.1 起移除）。
- **烘焙 vs 实时（我方裁决）**：室内禁烘焙 GI（同全城禁烘律·与日夜循环冲突）→**室内配方=自发光灯板**（emission 天花板灯槽/灯带·零灯位）+**≤3 实时补光**（进 L2 档才开·计入 16 灯帽）+动态物接 Light Probes（正典）。判据帧=进楼帧：地面光斑形可见·日帧外墙无渗·出楼回外观档帧。
## 三、夜景组合序与转译面（Q3·转译 10 条·组合序定谳=①环境光压暗→②月光基线→③emission 窗灯→④bloom→⑤雾末位）
1. **夜灯主力=emissive 材质层非实光**（B·ps1ke CS2 反编译 API 文档：EmissiveProperties/ProceduralEmissiveSystem/StreetLightObject 全走 emissive 驱动）→落地：窗灯/路灯/霓虹全 emission（五色律正典不重采），实光仅爆闪/警灯；判据帧=L2 夜帧窗灯全亮+实光数≤16。
2. **灯必配剔除系统**（B·ps1ke：LightCullingSystem 为独立渲染系统）→落地：按相机档开关实光与灯板（L0 档关点光）；判据帧=L0 夜帧 profiler 灯渲染数≤帽。
3. **夜色=后处理栈联动非单参数**（B·ps1ke Climate 预制：FogProperties+ColorAdjustmentsProperties+WhiteBalanceProperties+VignetteProperties 同栈）→落地：夜档 Volume 联调=雾色贴夜天色+压亮+冷白平衡；判据帧=L0 夜帧楼-天明度差≥2-3 档（夜黑场正典）。
4. **雾=末位收口（增量=序·非值）**（雾距判例族正典 0.0015/0.0006 不重采；B·3 条同栈互调）→落地：先 bloom 后雾、雾为整体罩层最后调；判据帧=改雾必过 L0/L1 双判据帧再定。
5. **窗灯色克制**（C·Paradox 论坛帖检索快照：夜窗「garish neon mixes→noisy and unrealistic」）→落地：窗灯色收五色律归属（外部佐证非新采）；判据帧=夜帧取色器抽检窗灯全落 5 色带内。
6. **先立对比框架再加灯**（C·CS2 夜景批评帖检索快照：night「flat/washed-out/overly bright or artificially dark/poor contrast/fake emissive」）→落地：先地面基色+月光基线（三连乘正典）后上窗灯；判据帧=全关 emission 时剪影仍可读。
7. **SSAO 补夜景接地感**（A·URP14 官方：挂 Renderer 全相机生效·Intensity/Radius 官方标 Insignificant）→落地：楼脚/道具接触暗角进夜档标配；判据帧=L2 夜帧楼底 AO 可见+帧时增幅≤2ms（桌面 1-3ms·C bugnet）。
8. **SSAO 布线五件套+WebGL 双态**（C·bugnet+A 官方无排除条款）→五件套见第一节；判据帧=Frame Debugger 见 SSAO pass+WebGL 样区帧时入帽；WebGL 实测=**待证（M）**。
9. **月光=主光复用非新灯**（A·URP 官方：主光由 Lighting 的 Sun Source 槽指认·未指认取最亮定向光）→落地：夜档主光转色温即月光（自动继承主光阴影/级联预算·省 1 灯位）；判据帧=夜帧全场仅 1 定向光无第二盏。
10. **窗内景深幻觉=备选（M·待证）**（B·ps1ke ArtPipeline 见 InteriorMappingProcessor/Window/Room 类名）→推测 CS2 窗内=interior mapping 贴图幻觉而非真实内构；落地备选=远档窗贴图替内构；判据帧=L0 夜帧窗亮度与帧时无崩；采信前须直读源证。
## 四、结论应用表（research-protocol §二.1 强制·落点四选一：任务单/法文修改/决策呈报/判负留痕）
| 结论 | 落点 | 状态 |
|---|---|---|
| Light Layers 室内外隔离+双态切换走相机 Culling Mask（A 官方机制） | city-3d-lighting 技能正典增补（室内光章节）+R4 光影任务单 | ✓ |
| 夜景组合序 ①环境光压暗→②月光→③emission→④bloom→⑤雾末位+后处理栈联调 | 技能正典增补（组合序条目）+夜景调试任务单 | 🟡 序=转译裁决·佐证 B/C |
| SSAO 布线五件套·桌面 1-3ms·WebGL 官方无排除 | R4 光影任务单（SSAO 样区实测项） | 🟡 WebGL 实测=M |
| 室内配方=灯板 emission+≤3 补光+禁烘焙+Light Layers 隔离 | R4 室内光池任务单 | ✓ A 机制+C 社区 |
| CS2 窗内=interior mapping（推测） | 判负留痕（未采信·须直读源证） | M 待证 |

- 更新记录：T0 骨架落盘→T1 第一节（阴影/SSAO/探针官方面）→T2 Light Layers 官方机制并入→T3 Q2 室内面→T4 Q3 十条转译+应用表+验证声明收口。
- 失败面：paradoxwikis（CS2 官方 wiki emissive 页）与 Paradox 论坛夜景帖两站 JS 墙拦截（fetch_content curl 后端因 curl_cffi 未装不可用·纪律内二法已试）→该两源降级为 ps1ke 反编译文档+检索快照佐证；URP14 light-layers 直链 404→以 URP13.1 官方页代读（同机制·正文已注）；discussions.unity 首取 403→fetch_content 重试一次成功；unity_docs 批查工具空格式查询失效一次（改驼峰类名法）。
