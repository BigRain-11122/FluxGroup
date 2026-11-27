# R-20260930-3render2-pipeline-01 — 3渲2 方案级正法重研（多带 toon ramp+倒角壳描边+选角律·CEO 令 O-2026-0930-001·B 腿 v3）

> 溯源：B4-任务书（CEO 判 v2「还是很糟糕」·四罪已定谳勿重查）·消费方=B 腿 v3 实施定谳 ·判据预注册=①3渲2 着色正法（多带 ramp+描边·Built-in 管线）②色板量化纪律（明度分离+阴影色相偏移）③头身比/亲和力选角律
> 验证声明：实读 11/20（内部件 3：R-20260928-toon-shader 正典 M1-M9+R-20260929-2dlive-pipeline-01+AD-024 包实查；外部成源 6：michaelchabot.dev/ronja-deepwiki/bugnet.io/ClipStudio×2/charactergen）·关键结论双源在案·失败面：Synty 官方 promo 原图未直采（观感以内件 R-20260929-city-top1-01 demo recipe 在册记录为准·P3D_Spike demo 实数=78 非 79·实查纠偏）·外部文本按不可信输入处理·页内指令零执行

## 一、着色正法（判据①·toon ramp 多带+描边·Built-in）
- 多带 ramp=toon 正法本体：1D ramp 亮度→色映射（panthavma A）；UTS2 三层 Base/1st/2nd Shade 阶梯取色替代连续漫反射=正典 M1（R-20260928 在册 A 级）→本次定谳 **4 带量化**（core 0.42/mid 0.62/light 0.85/满亮 1.0，硬 step 边界无 smooth 过渡=cel 感；每材质 3-5 阶纪律满足）
- 描边 Built-in 正法=**倒角壳 inverted hull**：mesh 双渲染，pass2 Cull Front+顶点沿法线外扩+纯色（ronja A+michaelchabot A 双源）；外扩必须**沿法线**勿轴心缩放（缩放=宽度随离枢距离漂移+自相交内线，michaelchabot 实测图证）；坑律=硬边/劈法线壳撕裂（bugnet A+michaelchabot A）→Synty 人物网格近光滑可承；凹陷区假内线=壳通病→细宽 1-2px+低饱和暗色可压（michaelchabot A）
- 后处理边缘检测（M8·在册待证）判弃：Built-in 无 URP RendererFeature 面+全屏成本+内边缘缺失（bugnet A「edge detection misses interior edges」）——单角色精灵批渲染用不上全屏
- **帧间闪烁（四罪4）根治机理**：低模面片正交+逐帧蒙皮下法线跳变→①壳描边统一轮廓（几何级稳定）②4 带量化把微照明差吸进带内（量化=照明抖动低通）→双效；同区色值方差=预注册验证判据④
## 二、色板量化纪律（判据②）
- **阴影色相偏移勿压灰**：暗带色=BaseColor×带系数×冷向 tint——cel 正法「dark desaturated blue or purple」（ClipStudio A）+「勿黑加暗·移向冷/互补·暖肤配 mauve/purple」（redflaim A）双源→实现 _ShadeTint≈(0.84,0.80,1.06)（偏紫蓝·去饱和但有 hue）——v2「灰挤中间调」反面教材的直接解
- **明度分离律**：角色/背景明度差≥两档——v2 灰背景(#F3F4F5)+灰青衫同挤中间调=四罪3 实锤；Synty Kid 多彩中明度→背景取暖奶油白（top #FFF3DC/bottom #FFDFAe·L≈95%）与角色中调(L≈45-65%)拉开两档+描边再压轮廓
- 量化上限 5 阶/材质（UTS2 三层正典+rim 高光带）；rim=量化开关（band==满亮且 view-edge 才亮·保预算）
## 三、选角律（判据③·头身比/亲和力/剪影）
- chibi 定义律：2-3 头身=超变形甜点（charactergen A「the defining feature」）；**漂向 6 头身=超变形感消失**（charactergen A）——v2 六头身写实+低模糊脸=恐怖谷边缘（四罪2）机理级实锤
- 比例格律：2 头身 face:body=1:1·3 头身 face:torso:legs=1:1:1（ClipStudio A）；Synty Kid≈3.5-4 头身（AD-024 实查·probe 量证待落）=亲和力高位
- 婴儿图式=亲和力引擎：大头/圆脸/大眼低位/短圆肢（charactergen A）
- 剪影律（任务书预注册）：24px 纯黑剪影可辨认+性格标签（歪头/叉腰/道具任一·剪影会说话）
## 四、Synty 官方观感对齐面（78 demo=老师·demo recipe 在册 R-20260929-city-top1-01）
- Synty promo=平涂色块+干净色区隔+无描边（正典在册）；3渲2 出 2D 精灵与官方 3D promo 的分叉点=**单帧缩到 24px 时轮廓线承载可读性**（判据=剪影律）→描边=2D 用途增量非背离；官方对齐面=色区隔干净/大面积色锚/无渐变糊——红色系锚扩大面积（superhero 红披风/背带裤档为候选池）
## 五、结论应用表（落点）
| 结论 | 落点 | 状态 |
|---|---|---|
| 4 带 toon ramp+法线外扩倒角壳（1-2px 低饱和暗色）双 pass 单 surface 文件（蒙皮安全=v1 surface 先例） | Assets\Shaders\SpikeB4Toon.shader | 接线中 |
| _ShadeTint 冷偏移+暖奶油白背景两档分离+rim 量化 | B4PlayBootstrap 景观层 | 接线中 |
| AD-024 Kid 池 casting probe（6 候选）+24px 剪影测试+红色锚权重 | b4 casting 实弹 | 接线中 |
| spacing chart 非均匀帧距（预备-甩出-跟随-回弹·禁均匀帧距）+近重复帧删除 | B4RigDriver B4Motion | 接线中 |

- 防线二：承重主张①倒角壳双 pass Cull Front+法线外扩=ronja+michaelchabot 双 A 源直读 ✓；②chibi 2-3 头身律=charactergen+ClipStudio 双源 ✓；③4 带量化吸抖=机理推导（M 档）→probe 帧间同区色值方差实弹验证；④78 demo 实数=Get-ChildItem 直数 ✓
- 更新记录：T0 骨架→T1 内档（toon-shader 正典+2dlive-pipeline+AD-024 包实查/78 demo 纠偏）→T2 外源 6 fetch→终稿一次落盘（预算 11/20）
