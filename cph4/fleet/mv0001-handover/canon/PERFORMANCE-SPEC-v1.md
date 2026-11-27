# PERFORMANCE-SPEC-v1 — 活人演员工艺（微表情/眼神/表演连续性·「要是一个活灵活现的真人演员」）

> 溯源：CEO 令 2026-10-12 19:5x「微表情，眼神等等，要是一个活灵活现的真人演员！你自己看如何实现！」（O-20261012-1955·承 O-1935 眼神戏律·表演工艺终极限）。
> 证据基：官方 12 字段 pose 库（head_orientation 含 gaze/muscle_tension 驱动可见解剖/movement_quality 表调/silhouette 最高杠杆四字段裁剪律）+Hailuo 官方 tuning 实锚（**micro-expressions 是该模型家族的官方调优方向**）+ai-cinematic-pipeline「micro-expression control·frame chaining」+本司 STRENGTH-MAP §六七（鬼相/眼神戏）+导演席表演论。
> 核心定谳：**活人感=三层叠加**——①KF 层「戏在帧」（微表情=半途瞬间+不对称+湿润度+肌张力）②i2v 层「保活+一微节拍」（H3 微表情强项喂法）③**连续性层「情绪基准帧库」**（表演一致性=真演员的表演连续性·参照链实现）。

## 一、情绪基准帧库（新结构·表演连续性的实现）

每角色建 **5-7 张「表演基准帧」**（canonical micro-expression frames）——不是造型板是**情绪板**：
- 男主：怔住帧（瞳孔微缩+嘴微张）/心动帧（内眼角软化+半笑未笑）/凝望帧（眼睑半垂+落点极远）/释然帧（眉心舒展+嘴角松）/决心帧（下颌微紧+直视）。
- 女主：入神帧（呼吸性眨眼中途）/被打动帧（泪光起点+唇线软）/回眸帧（回头 30°·眼神先于头到）/释然笑帧（眼先笑·嘴后到）。
- 工艺：RAW 52 步出帧（turbo 洗掉微细节·定版帧一律 RAW）+EYE-DRAMA 块+半途瞬间法（§二）→ 过 FRAME-GATE 四检+活人感检（§四）→ **全片各镜按情绪挂对应基准帧为参照**（krea2_style_reference+多参照/dn0.6 锁脸链在役）——同一情绪弧跨镜=同一张「演员的脸」在演，表演连续性达成。

## 二、KF 微表情法（戏在帧·三层写法）

1. **半途瞬间律**：表情永远抓「进行到一半」——`caught mid-blink`/`lips parting slightly as her breath catches`/`the start of a smile that has not yet reached his mouth`——完成态表情=蜡像·半途态=活人。
2. **不对称律**：真人脸永远不对称——`one brow a breath higher`/`the smile tilts to one side`/对称脸=AI 指纹。
3. **湿润度+肌张力锚**：`a faint wet gleam on the lower lid, lips slightly dry at the centre`+12 字段的 muscle_tension（minimal→very high 梯度写进表情块：怔住=`throat tight, jaw slack`）。
4. **movement_quality 定调**：每镜表演一句定调（reserved/explosive/quietly held）——官方四高杠杆字段之一（silhouette/weight_distribution/torso_orientation/movement_quality）。
5. 权重配方（FACE 镜）：`(mid-expression caught half-way:2)(asymmetry:1.5)(glistening catchlight:2.5)`——微表情三权+眼神权并存。

## 三、i2v 微节拍律（保活+一微节拍·H3 官方强项喂法）

- 每条 5s 脸镜**只给一个微节拍**（与生命脉冲并存）：`her brow knits for one breath, then eases` / `the corner of his mouth twitches toward a smile he does not let happen`——一拍/镜（一镜一拍律）·Hailuo 家族官方 tuned for character micro-expressions（喂它最擅长的）。
- 禁：多节拍串联/大幅度表情（=漂移+蜡变）；微节拍永远收尾于平静（`then eases/then settles`）——收束=稳态接帧链。
- **帧链**：连续表演镜 last frame→first frame 接力（表演连续性+视觉零漂）。

## 四、活人感检（FRAME-GATE 机器检·四检升格五检）

逐 FACE 帧五判（任缺=回炉）：①catchlight 眼底光 ②gaze intent 视线意图 ③眼轮匝肌张力 ④**mid-motion 半途瞬间**（表情在动还是定格）⑤**不对称**（左右脸有差异）。i2v 条检追加：微节拍是否真实呈现+收束回稳态。
- 三律联动：「活人感」门（去AI感律）执法自此有机器级判据。

## 五、执行清单（今夜起）

1. bm-c/bm-a：男女主情绪基准帧库各 7 张（RAW 52 步·四检+活人感检过闸）→ 入 canon/evidence/performance-keyset-{HIM,HER}.jpg 拼板。
2. mv_full_shots.py：kf() 表情块按 §二 重构（半途+不对称+湿润+肌张力）·i2v() 微节拍行按 §三 补·HIM/HER ID 块挂基准帧参照。
3. 定版帧一律 RAW 52 步（turbo 仅试构图档）；定版脸镜 face_enhance 精修（Real-ESRGAN face_enhance·眼部细节补强）。
4. 已烧 FACE 帧回溯活人感检→不过=回炉白名单外。
5. 星晴/可爱女人 ID 块同补（专辑线同法）。

---
*v1·bm-a 导演席·2026-10-12 20:0x·复引：STRENGTH-MAP §六七/FIDELITY-SPEC/官方 12 字段 pose 库/Krea2 RAW 档/upscale face_enhance·消费方=全 MV 线 FACE 镜*
