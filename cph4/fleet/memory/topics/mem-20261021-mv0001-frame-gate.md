# 首尾帧闸与提示词根因（2026-10-21·mv0001）

> L2 主题档。CEO 令「首尾帧错了视频一定错」＋「提示词最重要」，本件是执行后的实测结论。

## 一、首帧闸判据（F1–F8）

F1 无镜面人脸倒影（允许反光/反物/反手影）｜F2 人脸不崩｜F3 手部结构正常｜F4 **无拉丁字母**｜F5 信息量足够（黑场 <50%）｜F6 身份锚一致｜F7 **字幕繁简统一**｜F8 与镜头功能一致。
签核：R（角色）+ C（摄影）双签，D 复核。

## 二、尾帧闸判据（L1–L5）

L1 非半叠化帧｜L2 非运动模糊废帧｜L3 曝光一致｜L4 主体未误出画｜L5 与下一镜构成有意衔接（同向运动/视线/物质/明确硬切）。签核：E + D。

## 三、本轮实测（v5.13 首帧 1–36）

| 镜 | 缺陷 | 级别 |
|---|---|---|
| 1 | 约 2/3 纯黑，只露台灯一角 | 必修 |
| 16、17 | 玻璃上有半透明人脸倒影 | 必修 |
| 26、31、32 | 字幕**简体**，11–19 为**繁体** → 繁简混排 | 必修（属字幕资产，非提示词） |
| 33 | 碑顶刻痕疑似拉丁字母 | 待放大复核 |
| 35 | 接近死黑 | 观察项 |

## 四、缺陷 → 提示词根因 → 强制正向条款

| 缺陷 | 根因 | 必写正向锚 |
|---|---|---|
| 玻璃倒影脸 | 只写 `glass display case`；写 `no reflected face` 反而召唤 | `the glass carries only a soft sheen of the room light and the carved marks` |
| 开场纯黑 | 未要求主体可见 | `the man is clearly visible in frame from the first moment` |
| 拉丁字母 | 只写 `carved inscriptions` | `wedge-shaped cuneiform marks pressed into clay` |
| 唱歌嘴僵 | 只写 `sings` | `his lips shape each word, opening and closing several times` |
| 刻痕闪烁 | 只写 `carves` | `the marks stay fixed once cut` |
| 场景被换 | `scene=hall` 用在博物馆镜 | 场景 token 与首帧一致（museum） |

**结论**：5 项里 4 项可在提示词阶段拦掉，1 项属字幕资产。

## 五、判例：**闸自己也会错，误拒同样是缺陷**

- 首次给 R3/R4 上锚点检查时，用**子串猜镜头类型**（`"sing" in prompt`），把刻字镜误判成唱歌镜，四条 take 全部被误拒 → 浪费一轮排队时间。
- 正法：锚点由调用方**显式声明** `kinds=["carve","inscription"]`，闸不猜。
- 教训：闸的误拒会挡住正确工作，**闸本身必须接受审查**；新增闸后要先用"应当通过的样例"反向验证一次。

## 六、本轮产出

- `cph4/fleet/mv-album-001-jay/FRAME-GATE-v1.md`（判据+根因表）
- `Tools/frame_gate.py`（逐镜导出首尾帧，73 镜已导出）
- `Tools/preflight_gate.py` 第⑤项：正向必备锚（显式 kinds）
- `cph4/fleet/mv-album-001-jay/GATE-SPEC-v1.md`（数值判据 + 席位签核）
- `Tools/signoff.py` + `QA-SIGNOFF-LEDGER.jsonl`（缺记录即未通过）

## 七、重拍实测（480P）

| take | 结果 |
|---|---|
| R3a（书吏刻字） | **可用**：手部正常、刻痕 5 帧稳定、侧脸一致；小瑕疵＝火把 0→1 帧突入 |
| R3b | 产出缺失，需重烧 |
| R4a（手压泥板） | **可用**：五指正常、刻痕稳定；刷子→按压衔接略生硬 |
| R4b | **内容不符**：拍成"火把烘烤+刷子"，无"抹边缘"动作 |

## 八、算力与窗口

- 768P 正式件只在 **22:00–08:00** 烧；白天只跑 480P 验证。
- ComfyUI 用完即停：实测停后显存 9.8G → 4.7G。
- 生产令：`PRODUCTION-ORDER-mv0001-rebuild-v1.md`（A 前端补齐 / B 素材重拍 / C 剪辑重建 / D 调色字幕 / E 出品）。