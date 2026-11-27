# V53R-CLOUD-2shot-r1017 — V5.3 三镜重烧·D04/SIL1 云道顶替包（PROMPT 过闸件）

> id=V53R-CLOUD-2shot-r1017 · 2026-10-17 20:0x · 签发面=bm-a 导演席（承 canon/V5.3-REBURN-ADDENDUM-3shot-20261017 P1-1/P1-2 + CEO O-20261017-1741「马上弄好」+ 19:30 升级预案〔bm-c 5h+ 零消费实证·19:5x git log 复核〕）
> 路线=云道顶替：generate_image edit_mode=local（局部编辑·区外像素保全）修帧 → 云端 first_frame i2v（minimax_h3 768P 首选=与现版段件同栈族·seedance2 720p 备道）→ ffmpeg 零音轨/1344×768/24fps/≥5.17s 合格化 → V5REDO 同名落位
> C01 人脸镜留 bm-c（云端必拒人脸近景·增补单 P2-3 维持在途）

## 一 修帧单（generate_image · edit_mode=local）

### P1-1 D04_her_brush（载体形制+刷杆缺失）
- 源帧=现版 1344×768 首帧（segments/D04_her_brush.mp4 @0.5s 抽帧·reburn_D04_ref.jpg）
- 定位实读：手部 bbox 归一 (0.577,0.111,0.423,0.456)·红甲捏握点 (0.580,0.326,0.115,0.189)·毛状虚影 (0.357,0.417,0.268,0.195)·右上灯焰 flare y<60 避开
- **edit_region=[0.268, 0.078, 0.732, 0.755]**（载体受光面+手+刷具整块·避灯焰·含泥板落位区约 pixel 520-1260/140-620）
- **prompt（过闸正身）**：
  `Replace the cord-bound bamboo-slip tablet under her hand with a single wet clay tablet with incised cuneiform rows, rounded corners and a damp sheen catching the upper-right lamp light; put a reed stylus with its full pale handle clearly held in her grip, its tip resting on the clay; keep her hand pose, skin tone, red manicured nails and white shirt cuff identical; render the surface beneath as a plain worn wooden table; keep the upper-right lamp flare, the raking light axis from upper right to lower left, the warm amber palette and all shadows as they are.`
- 验收（增补单 P1-1）：载体=泥板（无编绳/无竹条可读）+苇杆完整入画+五指正常+红甲手保留+暖灯年代感+区外零改动

### P1-2 SIL1_stele_backlit_v4b_s9021（心形符现代符号违例）
- 源帧=现版首帧（segments/SIL1_stele_backlit_v4b_s9021.mp4 @0.5s·reburn_SIL1_ref.jpg）
- 定位实读：心形符 bbox 归一 [0.376,0.299,0.049,0.081]（符带第 4 行 x≈0.400）·左邻蝶形符间隙 ≈6px·右缘贴人物发丝剪影（间隙 4-6px=溢出风险位）
- **edit_region=[0.368, 0.286, 0.068, 0.107]**（心形符+10-14px 边距）
- **prompt（过闸正身）**：
  `Replace the heart-shaped carved glyph in the selected area with an eight-pointed star votive glyph, carved in the same single-line V-groove style and the same size as the neighboring glyphs in the band, its upper-left edges catching the same warm torch light, the grooves holding the same deep shadow; keep the stone surface texture, the torch backlight, the silhouette edges and everything outside the area exactly as they are.`
- 验收（增补单 P1-2）：符带逐符扫查零现代字形+剪影背线完整+八角星与邻符同格同深同风格+区外零改动

## 二 i2v 单（云端 first_frame · PROMPT-SPEC-v2-I2V 五律正身 · 窗内取段）

### D04 i2v（装配窗 153.6→155.4·源件 ≥5.17s·1344×768·零音轨）
- 帧源=§一修帧产物（验收过后）
- **prompt（过闸正身）**：
  `Locked-off tripod close-up. Her wrist traces one short cuneiform stroke at a time across the wet clay tablet with the reed stylus, small arcs landing one after another, fine clay dust lifting into the lamp beam toward the upper right, the shadow of her hand swaying in step on the tablet face. The lamp flare holds steady. The camera stays still. Preserve the film grain and the original color palette.`
- 参数：duration=8s（≥5.17 闸）·generate_audio=false·768P 档·动作幅度上限=腕摆 ±10-15°/指控行程 80-150px（帧分析活动空间实读）

### SIL1 i2v（装配窗 29.0→31.14·源件 ≥5.17s·1344×768·零音轨）
- 帧源=§一修帧产物
- **prompt（过闸正身）**：
  `Locked-off tripod shot. The twin torch flames breathe in small flickers, their halos swelling and easing along the carved band, fine ash drifting through the beams; the votive symbols hold their grooves in the raking light, the backlit silhouette edge keeping its line. The camera stays still. Preserve the film grain and the original color palette.`
- 参数：duration=8s·generate_audio=false·768P 档

## 三 合格化与落位
- ffmpeg：-an 零音轨·scale/pad 1344×768·24fps·时长 ≥5.17s 裁定
- 落位：`V5REDO/D04_her_brush_v5.mp4` + `V5REDO/SIL1_stele_backlit_v4b_s9021.mp4`（V5REDO=cph4/fleet/mv0001-handover/outbound/krea2/kf-demo-20261012/bmc/i2v/v5redo）
- build_full_mv_v5.py V5_SOURCE_MAP 扩两键：`"D04_her_brush": "D04_her_brush_v5.mp4"`·`"SIL1_v4b": "SIL1_stele_backlit_v4b_s9021.mp4"`（J-32 计数同步 +2）
- QC 板（前后对照+帧级探针）+判读回执上链 bmc/；装配重建候 C01 回件（bm-c 在途）——三镜齐后删缓存（v51_ 三段件+_fx pin+受影响块件 A2/G1/G5）→重建→三镜帧级复验→水印四闸→专家组→DIRECTOR-REVIEW-V5.3-PASS→终批推→呈 CEO 亲审

## 四 闸（PROMPT-EXPERT-GATE v1·云端批零豁免）
- 第 1 层 lint 机核：三名单+video[FLAT]+[CULTURE]+API 参数检（runner=.codely-cli/tmp/lint_v53r_cloud_r1017.py·回执随包上链）
- 第 2 层专家审 verdict=PROMPT-GATE-V53R-CLOUD-2shot-r1017.md（独立席位·禁自审自签）
- 第 3 层导演席签发后点火（本档 §四 即签发位）

## 五 风险注记
- D04 区内大手笔重绘（板面→木桌+泥板+苇笔）=形制级 inpaint：手部保真为最大风险位——修帧 QC 逐指核（五指/红甲/袖口）·不过即重试同参数或缩 region 两遍法（先板后笔）
- SIL1 右缘贴人物剪影 4-6px：若重绘渗色伤剪影→缩 region 右界至 0.430（px 577·心形右缘 571 内 6px/剪影 590 外 13px）重试〔原值 0.370 系乱码勘误·承 PROMPT-GATE §二核正〕
- 云道风格漂移风险=物件/剪影镜最低位（预案选此二镜依据）·帧检基准=现版首帧对照板

—— bm-a 导演席 · 2026-10-17 20:0x
