# R-20260929-city-top1-01-synty-demo-recipe — Synty 官方 demo 头部视觉配方·裸装修法·同资产复现判定
- 溯源=CEO 令 2026-09-29「怎么做到头部 top1 你们自己去研究，不要给我看垃圾」·消费方=City3D 施工线·判据预注册=Q1 官方配方面/Q2 修法清单面/Q3 可复现判定面
- 验证声明：web 读取 20/20 用尽（检索 7+直读 13·直读成源 5 页：unity.com、Synty 产品页×2、KinematicSoup 团队访谈、m3m-studio）·分级 A=8 条（直读 3+官方视频/Unity 手册检索快照 5）·B=1·C=3·三态标注·数字必带出处·失败面见文末

## 一、配方面（Q1：官方 demo 头部水准的要素配方）
- 灯光/后处理官方四件套【确认·A】官方《Key Art Lighting in Unity (Tutorial)》(youtube.com/watch?v=hJ2rolSv-5M·Unity6/URP) 官方描述="add **environment lighting and fog**, refining shadows on your main directional light, adding **post processing** effects, and using **light layers** to make your models pop"——环境光+雾打头阵，主光阴影精修、后处理、光层突出主体
- 官方同系教程【确认·A】《A Quick Post Processing Guide for URP in Unity!》(youtube.com/watch?v=7YzWexOAggc)·《How To Quickly Light A Scene In Unity》(youtube.com/watch?v=OGiQ6H0tPLk)·官方播放列表 PL2QPFqe01WRkGN7J8X0Okgq7R3REbCt48——打光+后处理=官方正式教学内容，非社区偏方
- 官方配置随包附带【确认·A·syntystore.com/products/polygon-city-pack changelog v1.12.0 直读】"**Added lighting and post processing**"+"Converted shaders to shader graph"——参数级配置就在本地 48 包 demo 场景里，web 拿不到数字（见失败面）→本地提取=唯一权威参数通道
- 顶级 demo 加料【确认·A·unity.com/demos/fantasy-kingdom 直读】Unity 官方 Demo 团队（Unity Originals+Incineration Productions）用 Synty POLYGON 资产配方=**Adaptive Probe Volumes** 间接漫反射（"illuminated every object and corner"）+**VFX Graph**（蝴蝶/落叶/水花）+**SpeedTree 10** 植被+Shader Graph
- 天空与雾【确认·A·syntystore.com/products/simple-sky-cartoon-assets 直读】官方天空资产在售（SIMPLE Sky·免费·含日月星云+"Offset the X UV's to change the time of day"昼夜机制+自带 demo scene）——天空=官方配方正式组成；雾-天融合技法【确认·A·Unity 手册】"match the fog color to the color of the skybox"；POLYGON demo 具体用何天空=待证（本地可直验）
- 密度/构图/色彩【确认·B·kinematicsoup.com/blog/synty-studios-case-study 直读·Synty 团队访谈】demo 生产=先灰盒（"greybox out the demo scene"）→多艺术家同场景共建（Pirates 后 demos "**more detailed and expansive**"）→全员加"story-telling easter eggs and world-building"→**眼高尺度复查**（Reactor "at eye-level with other characters running around"）——头部密度=多人迭代+叙事道具的产物；产品页 14 张截图即 demo 实拍（A）；x4 换色行=色彩纪律工具（doctrine ④已证·不重复）

## 二、修法清单面（Q2：Synty 裸装→头部·社区共识修法·每条带源）
- 病根定谳【确认·C·m3m-studio.com 直读】"The problem is often not only the asset. The problem is **the asset in default lighting**. And **Unity default look can kill almost anything**."
- 修法列表【确认·C·m3m-studio.com 直读】"lower ambient, stronger local lights, fog, color grading, vignette, careful bloom, higher contrast, darker atmosphere"——低环境光/强局部光/雾/色彩分级/暗角/**bloom 必须克制**/高对比/暗氛围
- 底盘设置【确认·C·同源】Linear 色彩空间+低环境光+雾+后处理栈+vignette+色彩分级+局部光承担导航信息；内景可用纯色清屏替代天空盒
- 视觉识别律【确认·C·同源】"The player often does not read the shape. **They read light on the edge of the shape**"——立面告别纯黑靠环境光+受光边对比，不靠贴图
- 社区判差标准【确认·C·Reddit r/Unity3D jpsa1f 检索快照】"Most Synty games have **poor lighting, standard unity shaders, and no color correction**"——与我方自评 3.5-4/10 五症状（零后处理/光影硬/色彩失谐/街面空/渲染噪音）完全同构
- 资产不救命【确认·C·Reddit r/gamedev 1bchhkk 检索快照】"buying Synty assets will not make up for lack of **design, lighting, shader, composition, and colour theory** skills"——设计/构图/色彩理论须自补

## 三、可复现判定面（Q3：同款 POLYGON 资产+正确配方=头部？）
- 官方宣传图级=**确认可复现**【A】产品页截图由包内 demo 场景+包内资产制作；我方持同款 48 包→抄官方 demo 配方（环境光+雾+主光阴影+后处理+光层）即可对齐宣传图
- Unity 官方 showcase 级=**部分可**【A】Fantasy Kingdom 证 Synty 资产可达官方 demo 水准，但加料 SpeedTree+VFX Graph（非纯包资产）——纯 POLYGON 到此级需外部植被/动效补强
- 我方归因判定=**确认（症状带匹配）**五症状全落「默认光裸装」病因带=非资产上限问题；修复后可达 demo 对齐级【推测·A+C 因果链推得】

## 四、适配结论面（俯视角 320m 总览 + 24m 街景双机位怎么用）
- 总览机位（320m）：雾+大气透视优先级最高（远视距把色彩失谐暴露最大）；fog 色对齐天空色（Unity 手册 A 法）；color grading 统一米黄×土棕×饱和蓝三色失谐；bloom 管窗灯
- 街景机位（24m）：官方 Key Art 四件套正对——主光软阴影精修+环境光补偿+局部光；密度按官方 demo 生产律：灰盒→叙事道具细节→**眼高尺度复查**；「读受光边」律治立面纯黑
- 参数权威通道：**禁网络猜参**——逐包开本地 demo 提取灯光/雾/后处理 Volume 配置建「官方基准档」（changelog v1.12.0 已证随包附带）
- 净空前置：渲染噪音（地面黑碎屑/水面死黑/调试红圈）先于配方清除——官方图零调试残留

## 五、结论应用表（落点四选一）
| 结论 | 落点 | 状态 |
|---|---|---|
| 官方配方=环境光+雾+主光阴影精修+后处理+光层（一）| 任务单：City3D 施工线按官方《Key Art Lighting》四件套重打光 | 接线中 |
| 灯光+后处理配置随包附带（一）| 任务单：逐包提取 48 包 demo 配置建「官方基准档」·禁猜参 | 接线中 |
| 社区修法六步（二）| 任务单：低环境光/雾/grading/vignette/克制 bloom/局部光落地顺序表 | 接线中 |
| demo 生产律=灰盒→叙事密度→眼高复查（一·B）| 任务单：装配 SOP 补「密度共建+眼高验收」两步 | 接线中 |
| Q3=宣传图级确认可复现·资产非瓶颈（三）| 决策呈报：支撑继续 Synty 路线·瓶颈=配方缺失非资产 | 已闭环（本件即呈报件）|
| 参数级数字未从 web 获得（一注）| 判负留痕：YouTube 正文不可抓→改判「本地包提取」通道 | 已闭环 |

- 更新记录：T0 骨架落盘→T1 三路检索波（官方视频/Fantasy Kingdom/Reddit 判 403）→T2 m3m 全文+两检索波→T3 City Pack changelog 直读→T4 主体成文落盘→T5 终稿（补 SIMPLE Sky+KinematicSoup 访谈·预算 20/20 恰好用尽）。
- 失败面：①Reddit 全通道 403（old/www/redditmedia+curl 后端未装）→帖子仅以检索快照作证(C)；②YouTube 页只吐 boilerplate×3→视频内容与参数级数字未能直读；③gamedeveloper.com 403；④1 次 skybox 检索遭 DuckDuckGo bot 拦截（换措辞后第 2 次成功）；⑤POLYGON demo 天空具体件+官方 demo 主色数=待证（本地 48 包 demo 可直验）。
