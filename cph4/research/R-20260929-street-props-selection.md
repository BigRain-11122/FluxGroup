# R-20260929-street-props-selection — City3D 街景道具散布选型表（bm-a 机·Phase 2 街景道具层选型依据）

> 立项三问：为谁而研=City3D 主会话 Phase 2 街景道具层（主会话随后按表施工）；仓内已有=48 包全景索引（AD-022=City Pack v1.3·Prop×175/Bld×75/Env×65）+本轮三包磁盘一手实查；判据预注册=①在库街景件逐件分类清单 ②沿路散布规则 ③首期预算帽 ④缺口呈报。
> CEO 令 2026-09-29：3D 资源库=唯一来源·调用+标记双责——本件只盘点引用、零下载零 Unity；AD-NNN 引用法全程执行。

## 一、盘点面（shell 直查 gaming 子仓·普通 glob 静默忽略已绕行）
- AD-022 Props=174 件（.prefab 实数）、Environments=65 件；AD-015 Plants=42/Rocks=30/Trees=66；AD-048=58（点缀件 Small_Rocks×5/Tree×4）。
- 城市数据源实读（gaming/FluxVerse/Tools/city/td-organic-data.txt·13 行）：ROAD_COUNT=1031 格·WATER=565·SAND=104·PLAZA=81·PARK=78·TREES=53·BRIDGES=96·STARTS=8。
- 关键发现：路灯/长椅/垃圾箱/消防栓/邮筒/交通灯/停车站全在 Props 目录，Environments=路面/结构/绿化环境件——按实际件名归类，不按目录臆断。

## 二、选型清单（AD-NNN+一句话；★=首批入城；Props 174 件全数归类对账无遗漏）
1. 照明/信号类（14·AD-022 Props）：LightPole_Base_01/02+Arm_01+Lights_01/02+Box_01（★路灯=模块拼装成整灯预制后散布）、CrossLights_01+CrossButton_01（★行人过街灯钮）、Light_Attachment_01（挂灯附件）、SidewalkPoles_01/02（路口信号灯杆组）、TrafficLight_01~03（★交叉口红绿灯）。
2. 座位类（6）：ParkBench_01（★街角/广场长椅）、PicnicTable_01（★PARK/广场野餐桌）、Couch_01/Deckchair_01（休闲区沙发/躺椅）、Table_02+Umbrella_01（★露天咖啡座+遮阳伞）。
3. 围挡类（8 Props+3 Env）：Barrier_01（★水马施工围挡）、Cone_01/02（★雪糕筒）、Sidewalk_Panel_01~05（施工围板组）；SM_Env_Fence_01+Fence_End_01（★水岸/广场围栏·Environments）、SM_Env_Sidewalk_Construction_01（围挡人行道段）。
4. 箱体/市政类（23）：Trashbin_01/02+TrashCan_01+TrashCan_Lid_01+TrashBag_01~03（★垃圾桶组）、Skip_01/02（大垃圾箱）、Hydrant_01（★消防栓）、Mailbox_01（★邮筒）、ParkingMeter_01/02（★停车计时器）、ATM_01（取款机）、PowerBox_01（街头配电箱）、Manhole_01/02（★路面井盖）、Phones_01（路边投币电话组）、CardboardBox_01~04+Pallet_01（后巷纸箱/栈板杂物）。
5. 亭棚类（2）：BusStop_01（★公交站台含候车亭）、HotdogStand_01（街角餐车）；SM_Env_SubwayEntrance_01/02（地铁口·结构件归地编线）。
6. 绿化类：AD-022 Planter_01/02（★路缘花坛）、PlanterWindow_01/02+PotPlant_01/02（窗台花箱/盆栽）、SM_Env_Tree_01~03（街树·植被线主责）、SM_Env_Flower_01+Grass_01+Street_Divider_01/02（花/草地+中央分隔种植带）；AD-015 Grass_01~05+Flowers_01+FlowerPatch_01+PurpleFlower_01+Bush_01~03+Hedge_Bush_01/02（★PARK 草花灌）、Rock_Small_01/02+Rock_01~04（水岸石点缀）；AD-048 Small_Rocks_01~05（小岩点缀）。
7. 标识/街面类（57+纸屑 7）：Sign×26（★交通市政牌：Stop_01/GiveWay_01~03/Parking_01/Warning_01/Arrow_01/Street_01~02/Bustop_01/Entrance_01/Hospital_01/Hotel_01/FireDepartment_01/Police_01/Pub_01/Bar_01/Barber_01/Cafe_01/Pizza_01/DeliPizza_01/Chinese_Noodles_01/XXX_01+Attachment_01~03 杆件）、LargeSign×17（商铺立牌：Beer/Bottle/BowlingBall/BowlingPin/Burger/Coffee/Donut/Guitar/Hotdog/Icecream/Lollypop/Milkshake/Noodles/Pizza/Popcorn/Soda/Taco）、Billboard_01+Pole_01+Roof_01+Sign_01~07（看板/杆/屋顶版）、Poster_01~03+Poster_Frame_01（贴墙招贴）；Newspaper_01/02+Paper_01~05（地面散落纸屑·极低密度点缀）。
8. 不入本层（51·盘点在册不散布）：建筑附件=Aircon_01+Roof_Aircon_01~03（空调外机）、Pipe_Part_Connect/Corner/Straight/T+Preset_01~03+Small_01/02（管道×9）、Vents_Corner_01/02+End/Exhaust/Straight/Transition/Wide（通风格栅×7）、Power_Cables_01~03、Washingline_01~04、Door_01/02+Window_01+Skylight_01、SatDish_01、SecurityCamera_01+Arm_01；室内=ShopInterior_Cafe/Chair/Desk_01~02/Display_01~02/Shelf_01~04/Table_01（×11）；手持=Burger_01/SmartPhone_01/Soda_01~03/Police_Baton_01——归建筑 dress 层与角色层。

## 三、沿路散布规则建议（程序化律：数据驱动+确定性 seed+只做重复件分布·不做城市结构）
1. 路灯：干道每 4 格 1 盏、左右交替（同侧 8 格；米距随 Phase 0 一格定标折算·CEO 例示 20m/4 格）——读 ROAD 1031 格的干道子集；整灯=LightPole 模块拼装预制后作重复件散布，朝向垂直路缘；灯头=emission 材质变体（AD-022 自带 Emissive 贴图直供），禁加实时光（WebGL 实时光帽 9/16 归灯光线）。
2. 座位/市政箱体：PLAZA 81 格每广场 2~4 长椅+1 垃圾箱+1 咖啡座组；路口转角每 4~8 格 1 垃圾箱；Hydrant 沿干道每 16 格 1（路缘侧位）；ParkingMeter 仅沿停车位线段；Manhole 贴路面低密度随机。
3. 围挡：SM_Env_Fence 沿 WATER 565 格岸线直线段+广场周边；施工组（Barrier+Cone+Sidewalk_Panel）仅 STARTS 入口区 1~2 处点缀。
4. 绿化：PARK 78 格内 AD-015 草花灌确定性 seed 散布（密度高于路缘）；路缘 Planter 花坛每 8 格 1；街树按 TREES 53 点位走植被线，本层不重复散树。
5. 通用律：全部静态合批（<256 顶点件不宜 instancing·SRP Batcher 优先）；seed 固定入档可复现；位置锚=td-organic-data.txt 同源数据，禁手感摆放。

## 四、预算帽（首期·WebGL 性能+静态合批考量）
- 路灯 ≤120 盏（1031 路格干道子集·4 格交替侧）；交通灯 ≤40；座位类 ≤60；箱体市政 ≤100；绿化点缀 ≤250；**街景散布件总量 ≤600**（不含贴建筑立面件）。静态合批下 draw call 由材质变体数决定、与件数部分解耦，帽主要防 culling/CPU 面（WebGL 30fps 底线·16×16 chunk 流送）。

## 五、缺口呈报（库内无对应·等 CEO 填库·禁自行补）
1. 报刊亭/独立售货亭——BusStop/HotdogStand 可近似但非报刊亭；2. 封闭式电话亭——Phones_01 为开放式投币电话组非亭体；3. 广场喷泉/雕塑/街头钟——PLAZA 中心地标件缺；4. 自行车/单车停放架——街道生活感件缺。→ 挂缺口清单呈批留痕后走 CC0（search_asset_lib）或 AI 生成（恒 decimate 律），未批前不施工不补件。

## 验证声明
本件清单=shell Get-ChildItem 直查 gaming/FluxVerse/City3D 子仓实读（普通 glob 静默忽略已绕行）：AD-022 Props=174/Environments=65、AD-015 Plants=42/Rocks=30、AD-048=58、城市数据 ROAD_COUNT=1031/PLAZA=81/PARK=78/WATER=565/TREES=53 逐项带出处；48 包索引载 AD-022 Prop×175 与磁盘 174 prefab 差 1（索引口径含 1 件非 prefab 计数·以磁盘实查为准）。确认=磁盘实查逐件归类（174 件全数对账），推测=零；缺口判负=全清单核对后定负；失败面=Phones_01/SidewalkPoles/Street_Divider 等少数件语义按件名判读、顶点数与材质未逐件开验（留施工期 asset-audit 抽件核）。应用表=§二选型+§三散布规则+§四预算帽+§五缺口呈批，落点=主会话 Phase 2 街景道具层按表施工（缺口项呈批前不动）。
