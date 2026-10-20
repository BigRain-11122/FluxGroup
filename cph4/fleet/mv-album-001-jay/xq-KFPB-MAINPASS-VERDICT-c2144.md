# 星晴 KF-PACK-B 主批判定（c2144 原生尺寸读 · c2145 S3-17 重烧）

- 日期：2026-10-20
- 判定席：bm-c 引擎 tick（C2144 收割轮 + C2145 重烧轮）
- 输入批：`xq-kf-packb-mainpass-c2144`（6 帧 @1344×768，锁定种子，jman 0.6 于含男主两帧）
- 判读法：逐帧原生尺寸读（每帧单独送读，**未用拼板替代原生读**——拼板 q90 缩略会吃掉手部细节，C2139 已立判例）
- **结论：六帧全过（4 PASS / 2 MINOR / 0 FAIL），KF-PACK-B 解锁，进 A+B 合装。**

证据总图：`cph4/fleet/mv-album-001-jay/xq-KFPB-MAINPASS-APPROVED-c2144.jpg`

---

## 一、逐帧判定

| 帧 | 种子 | 判 | 原生读要点 | 处置 |
|---|---|---|---|---|
| S1-08 手/车 | 726816 | MINOR | 手部解剖干净（拇指+四指、无粘连），构图无脸、年代校服/车铃/后货架全对、肌肤纹理自然 | 采用。**偏差是握住车把不是车座**——中文拍点写「车把」，英文格写 seat frame，属剧本自相矛盾（见 §三-1） |
| S3-17 脚 | 266291 | ~~FAIL~~ → PASS（重烧） | C2144 原烧**退化成全身背影双人远景**，脚部特写拍点未兑现、鞋型不可辨 → 判 FAIL；c2145 重烧后脚+白线占满画面、两双鞋轮廓可辨、接触阴影正确 | 以 c2145 帧替换（见 §二） |
| S3-21 抬眼 | 129686 | MINOR | 低头含笑半拍读得准，五官对称无畸变，年代发型对，无妆造韩感；毛孔在 2800K 逆光下不可分辨（属光位物理结果，非肌理缺失） | 采用 |
| S5-31 双人 | 323825 | PASS | 两张脸各自连贯无换脸，视线互相咬合（不看镜头），肤色在冷调夜色里暖而自然不蜡，年代服装 | 采用 |
| B-EX1 线轴 | 143992 | PASS | 双手握线轴合物理，风筝线张力与出画方向正确，表情专注 | 采用 |
| B-EX2 遮手 | 204921 | PASS | 手完整藏在外套下摆后（无指/拇指穿出、无印透）、小臂角度可读、单一眼线、无级联畸变 | 采用。C2142 死结（手特写不可渲染）至此确认已由换锚根治 |

## 二、S3-17 重烧（C2145）

- runner=`cph4/fleet/idle-guard-kit/kfpb_s317_feet_c2145.py`（由 c2144 主批 runner Copy-Item + 定点 replace 派生，非手抄）
- 改点：锚词加显式景别锁——`an extreme close-up of two pairs of feet cropped at the ankles ... the frame filled by feet and road only`
- 烧制：1344×768，8 步，cfg 1.0，euler/simple，krea2_turbo_fp8_scaled，65s/帧
- 产出：`media/MV/mv0001/xingqing/xq-kf-s317-feet-c2145/KFPB_MP_S3-17_feet_s266291.png`（1,363,703B）
- 判：脚部占比到 100% 画高、四人脚两双鞋、无融合趾、接触阴影正确、无字无 logo、年代对
- 余留两处不追第三次烧（导演席裁定）：
  1. 裁切落在**膝下小腿**而非脚踝——景别比要求宽一档，但该拍点是「数步节奏」，膝下构图信息更足，改用更窄裁切无收益；
  2. 两双鞋**都是系带款**（一深橄榄高帮、一白低帮），「一运动鞋一素面帆布鞋」的材质区分没兑现——轮廓区分已可读，观众层面不可辨此细节，判为可接受。
- 顺带勘误：首跑时三 seed 共用同一 cid，runner 的 skip-if-done 闸按 cid 记录，导致只烧第一张却报 `ok=3/3`——已在本轮修脚本（cid 加 a/b/c 后缀）并把该坑写进 §三-2。

## 三、新判例（出生地闸）

1. **剧本英文格与中文拍点冲突 = 帧批方向性风险**（本批首次实锤）
   S1-08 中文拍点「风灌进她飞扬的衣角与**车把**上的手」，英文格写 `gripping bicycle seat frame`，runner 照英文格出词，模型画成车把——**帧其实是对的，错的是英文格**。判例：KF 提示词的「持有物/接触点」一律以中文拍点为真值源，英文格只作翻译面；发现冲突当轮改英文格，禁改帧去凑英文格。本轮已修剧本文本（seat frame → handlebar）。

2. **派生 runner 的 cid 必须逐 seed 唯一**（三 seed 同 cid → 只烧第一张，却打印 3/3）
   skip-if-done 闸按 cid 记账，多 seed 变体共用 cid 时后两张被静默跳过，`stats.ok` 计数照满——**假绿且无任何告警**。法规：一帧多 seed 的批，cid 必须带 seed 序号后缀；收片判据一律以「盘上文件数 × 尺寸」为准，禁只看 END 行 ok=n/n。已修 `kfpb_s317_feet_c2145.py` 并投 FE 队列。

## 四、证据清单

- 帧目录：`media/MV/mv0001/xingqing/xq-kf-packb-mainpass-c2144/`（6 PNG，956KB–1.60MB）
- 重烧帧：`media/MV/mv0001/xingqing/xq-kf-s317-feet-c2145/KFPB_MP_S3-17_feet_s266291.png`
- 主批拼板：`cph4/fleet/mv-album-001-jay/xq-KFPB-MAINPASS-BOARD-c2144.jpg`（286,945B）
- 重烧拼板：`cph4/fleet/mv-album-001-jay/xq-KFPB-S317-BOARD-c2145.jpg`
- 执行回执：`xq-KFPB-RECEIPT-c2144-mainpass.json` / `xq-KFPB-S317-RECEIPT-c2145.json`
- 判定总图：`xq-KFPB-MAINPASS-APPROVED-c2144.jpg`（4 PASS / 2 MINOR / 0 FAIL）
- 日志：`media/MV/mv0001/logs/kfpb_mainpass*.log` / `kfpb_s317*.log`

## 五、下一步（银行已挂后继）

1. `kfpb-ab-coverage-c2145`（blocked·待起）：A 包 32 帧 + B 包 6 帧合装成**全曲时间轴覆盖板**，按 SHOTLIST-v3 时间码标出已覆盖/空档（A 包样片 196.14s / 全表 238s / 原曲 259.4s）——这是 i2v 开烧的前置件，无覆盖板禁起 i2v 波。
2. 覆盖板过了才起 i2v first_frame 锚定波（B 包 6 帧按拍点顺序，先 480P 低清验运动再 768P）。