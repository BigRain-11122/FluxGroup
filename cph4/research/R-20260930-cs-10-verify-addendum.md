# R-20260930-cs-10 CS 调研债补证（Q1 CS2 ECS 官方表述/Q2 WebGL 线程 API 直读/Q3 渲染管线归属）
> 溯源：O-2026-0930-006 cs-city 波收口置债·消费方=City3D 升档判据+cs-02/cs-05 件完整性·判据预注册=上三问
> 验证声明：实读尝试 20/20（search 5+fetch 15；成功 10·失败 10 全列文末）；成源 11 条=A×8（直读 5+检索片段 3）/B×1/C×2/M×0；关键结论 A 双源=Q1 官方维基+官方频道双直读、Q2 双代官方文档直读；另短链展开×3（仅取链接元数据·未取页面内容·不计读）；三态=确认/推测/待证
## 一、Q1：CS2 ECS/DOTS 官方表述
- 结论：**升 A（原 C）**——官方表述已获，「CS2 基于 Unity ECS」主张成立【确认】；「DOTS」字样官方句未现，全栈组合维持 C 级佐证【确认】。
- 证据 1【A·开发方官方社媒·检索片段录原句】：Colossal Order 官方 LinkedIn 原句「Our Chief Technical Officer, Damien Morello, joined Unity for #Unite2024 to share the benefits and challenges we faced using Unity's Entity Component System (ECS) for Cities: Skylines II」URL=linkedin.com/posts/colossalorder_tapping-the-entity-component-system-for-cities-activity-7250128138125381632-ooev（2024-10·Unite Barcelona 2024 期）；同文官方 Facebook=facebook.com/ColossalOrder/posts/interested-in-the-technology-used-for-cities-skylines-ii-then-check-out-the-repl/1086279460167628/。
- 证据 2【A·官方频道·标题直读】：Unity 官方 Unite 2024 演讲《Tapping the Entity Component System for Cities: Skylines II》——YouTube 官方页 youtube.com/watch?v=nEkIyWhvq3o（简介原句「Join Damien Morello from Colossal Order to learn more about the benefits and challenges of using Unity's Entity Component System (ECS) for game development and enhancing performance」·检索片段录）；Unity 官方 B 站镜像标题直读「使用Unity ECS打造《Cities: Skylines II》| Unite Barcelona 2024」bilibili.com/video/BV1zgB9YJExX（UP 主=Unity 中国官方空间系据页面侧栏 Unity 系内容判定·推测级小注）。
- 证据 3【A·官方维基直读】：cs2.paradoxwikis（Paradox 官方维基平台）ECS 专页原文「Unity ECS is a data-oriented tech stack. It organizes game elements into efficient components, enhancing responsiveness…」+「Systems are an integral part of Cities: Skylines II, most of what happens in the game is done through systems」URL=cs2.paradoxwikis.com/ECS_-_Entity_Component_System（页仅标注 last verified for version 1.0·内容较旧小注；同站 ACG/Buildings 页带「Verified by Paradox Interactive v1.5.2f1」徽章证审核制）。Paradox 官方论坛同题帖（forum.paradoxplaza.com thread 1708828·页面被拦·标题经检索片段）。
- 附注 1：Burst/JobSystem 组合仅 C 级（GitHub 演讲笔记 2024-10-09：ECS+JobSystem+Burst+managed systems 组合；51 分钟时长佐证=C·classcentral 片段）→cs-02 L13 升级指针应写「ECS 主张 C→A·DOTS 字样维持 C」。
- 附注 2：2026-09 新闻面（B 检索片段·heise.de/en/news/…11083454.html）Paradox 与 CO 分道、CS2 自 2026 起 Iceflake 接开发——对 CO 期架构事实无影响，City3D 引用时注明版本归属期。
## 二、Q2：WebGL 线程 API 官方直读
- 结论：**升 A 直读（原 A 检索片段）**——API 在册、未废弃、未改名，2022.3 与 6000.6 双代直读成功【确认】。
- 2022.3【A 直读】：docs.unity3d.com/2022.3/Documentation/ScriptReference/PlayerSettings.WebGL-threadsSupport.html（页 Publication Date 2026-07-02）——`public static bool threadsSupport` 原文「Multithreading support in WebGL. (EXPERIMENTAL) When enabled, Unity generates a WebGL build with multithreading support enabled. The generated content requires a browser that supports WebAssembly threads (SharedArrayBuffer). Currently, multithreaded WebGL builds only enable multithreading on the native C/C++ language level. Multithreading C# code is not yet available.」
- Unity 6.6【A 直读】：docs.unity3d.com/6000.6/Documentation/ScriptReference/PlayerSettings.WebGL-threadsSupport.html（页 Built on 2026-09-29）——原文「…This support allows C/C++ code and C# jobs compiled with the Burst compiler to run on separate threads. The generated content requires a browser that supports WebAssembly threads (SharedArrayBuffer). Multithreading standard C# code is not yet available.」（EXPERIMENTAL 标记已去除）。
- 判读：①API 名 PlayerSettings.WebGL.threadsSupport 无讹，仅文档 URL slug 用连字符（WebGL-threadsSupport）——点号 URL 三连 404 属抓取面陷阱（录工具指针）；②代际增量=2022.3 仅原生 C/C++ 级多线程（C# 全不可）→6000.6 扩为「Burst 编译的 C# jobs 可跑独立线程」（标准 C# System.Threading 仍不可）→cs-05「2022.3 域 WebGL 主路径 Job 并行无收益」维持成立；Unity 6 域升档判据加注=threadsSupport 开启后 Burst jobs 有条件并行收益（COOP/COEP+SharedArrayBuffer 浏览器面由 cs-05 已直读的 WebGL Advanced 页承接，本件不重复）。
## 三、Q3：CS2 渲染管线归属（顺带·≤5 读）
- 结论：**判负留痕·维持待证**——官方源未获 HDRP/URP 明确命名，cs-02 L16 维持原态【确认】。
- 顺带官方证据【A 直读】：cs2.paradoxwikis/Asset_Pipeline:_Buildings（Verified by Paradox Interactive·v1.5.2f1）原文「Buildings in Cities: Skylines II uses a variation of the standard PBR pipeline (with metallic/glossiness), with custom additions in order to cover the game's special needs」+贴图组=BaseColor/ControlMask/MaskMap/Normal/Emissive+LOD 子网格制（LOD1/LOD2+Win/Gls/Gra 分件）——官方措辞刻意不点名 SRP；metallic/glossiness+MaskMap 约定与 HDRP 工作流同形仅【推测】级佐证，不作确认。
- 重访触发器：①人工观看/取字幕 Unity 官方 51 分钟演讲视频（渲染话题可能在其中）；②Colossal Order 技术博客或 GDC 稿公开；③官方 shader 深页（Asset_Creation_Guide 子页）解禁直读。
## 四、应用表（落点四选一·强制）
| 结论 | 落点 | 状态 |
|---|---|---|
| Q1 CS2 ECS 主张升 A（DOTS 维持 C） | 正典修改：cs-02 L3 验证声明+L13 架构句升级指针——派工窗防线二抽验后自行落，本件不改原件 | 已落（09-30·防线二双源直读过·cs-02 L3/L13/文末指针） |
| Q2 threadsSupport 双代直读+Unity 6 代际注记 | 法文修改：cs-05 L15 升级指针+CitySim 升档路径法文加「Unity 6 Burst jobs 条件并行」注 | 已落（09-30·防线二双源直读过·cs-05 L15+L26 加注） |
| Q3 官方 PBR 句+LOD/贴图组规格 | 判例登记：HDRP/URP 命名维持待证·规格入 asset-audit 对照素材册 | 已录 |
| 抓取面判例：paradoxwikis/paradoxplaza JS 挑战站 fetch_content 全拦而 web_fetch 可破；Unity 文档连字符 slug 陷阱；curl_cffi 仍未装 | 工具指针：后续调研对 JS 挑战站优先 web_fetch·Unity 文档先核 slug | 已录 |
- 失败面（10 次透明）：①search×1 零结果（「Tapping…unity.com」措辞·疑 DDG bot 拦）；②fetch×3 点号 slug 404（2022.3/6000.0/versionless 的 threadsSupport·正确 slug=连字符）；③fetch×1 ref://2656321a（展开后=paradox 论坛帖·JS 客户端挑战拦）；④fetch×2 论坛帖另试（curl 后端缺 curl_cffi 报错·默认后端 JS 挑战拦）；⑤fetch_content×2 paradoxwikis ECS/Asset_Creation_Guide 页（JS 挑战拦·同站 web_fetch 成=抓取器差异）；⑥web_fetch×1 YouTube 页空内容（bot 拦·简介改经检索片段录）。
