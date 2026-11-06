# 机队必用工具三件套（2026-11-06 实测通过）

> 只收录**本轮真跑出数**的东西。每条含：干什么、命令、判据、坑。
> 适用：所有出片的线（MV / 漫剧 / 短剧 / 短视频 / 游戏录屏）。

## 一、成片出厂三检（零安装，必跑）

```bash
# 1) 定格 + 黑帧（一次过）
ffmpeg -hide_banner -nostats -i IN.mp4 -an \
  -vf "blackdetect=d=0.1:pic_th=0.98:pix_th=0.10,freezedetect=n=0.003:d=0.4" -f null -

# 2) 响度与真峰值
ffmpeg -hide_banner -nostats -i IN.mp4 -vn -af ebur128=peak=true -f null -
```

判据：
1. 黑帧段 = **0**（除非有设计好的黑场，需在剪辑表注明）
2. 定格 **≤ 0.4s 且不与设计定格重叠**；任何 >0.4s 的定格都要写理由
3. 集成响度 **-14 ± 0.5 LUFS**
4. **真峰值 ≤ -1 dBFS**（实测 v722g/v723 都是 +2.3，会削波）

## 二、双路定格取并集（硬规则）

单跑一路会漏一半。实测：v723 上 `ffmpeg freezedetect` 报 169.8/203.4，`Tools/mv_stability_gate.py` 报 114.5/234.2，**两处完全不重叠**。

规则：`mv_stability_gate.py` 与 ffmpeg `freezedetect` 都跑，**取并集**判 pass；只报一个来源的结论不算过关。

## 三、出片必带剪辑索引（补 D5 缺口）

```bash
python -m pip install "scenedetect[opencv]==0.7.2"
python .codely-cli/tmp/cutindex.py IN.mp4 OUT.csv   # 或用仓库内等价脚本
```

产出：
1. `OUT.csv` — 每镜起止时间码/帧号/时长（实测 v723：72 镜、均 3.26s、仅 1 镜 <0.5s）
2. `.otio` — 标准剪辑交换格式，可被 NLE 与脚本读取（实测回读 72 clips、总时长 234.4s 与成片一致）

判据：索引总时长必须与成片时长逐秒吻合；镜头数、硬切占比写进交付说明，供 D5「剪辑语言≥4类、硬切≤70%」机判。

## 四、压片质检（VMAF）

```bash
ffmpeg -i REF.mp4 -i DIST.mp4 \
  -lavfi "libvmaf=log_path=./vmaf.json:log_fmt=json:n_threads=4" -f null -
```

判据：**mean ≥ 93** 为「肉眼无差」线；mean 在 90-93 之间需人眼复核；**min < 80 说明有单帧劣化点，要定位**。
实测参照：我们自己的 MV 内容 CRF28 对 CRF16 = mean 91.50 / min 79.16 → 我们这条线 CRF28 不够，应走 CRF 22-24。

## 五、踩过的坑（照抄别重踩）

1. `libvmaf=log_path=` 里写 Windows 反斜杠路径会**静默不产出 json** → 一律正斜杠或相对路径。
2. OpenTimelineIO 在 Python 3.14 无轮子、3.12 源码编译会超时 → `pip install --only-binary :all: opentimelineio`（实测 0.18.1）。
3. faster-whisper 与 `av 19` 不兼容（`metadata_errors` 参数没了）→ 降 `av==13.1.0`。
4. faster-whisper 的 VAD 会把**唱歌**判成噪声、直接转 0 段 → 测歌声必须 `vad_filter=False`。
5. **纯 ASR 认歌词不可信**（实测产出「用借金蚊子割下的永远」这类无意义句）→ 字幕正解是「已知歌词 + 强制对齐」，不是裸 ASR。

## 六、明确不用（本轮判死）

1. **LLMLingua-2 / leanctx**（同源）— 中文丢路径与否定词，禁入中文产线，详见 TOKEN-OPT-TOOLBOX §四·五。
2. **contextshield --skeleton** — 省 86% 但数值常量只剩 66%、字符串只剩 12%，只能看大概。
3. **mem0 / claude-slim / just / splitrail** — 与本仓架构冲突或无安装路径，不引入。

## 七、各线怎么用

1. MV / 漫剧 / 短剧 / 短视频：一 + 二 + 三 + 四 全跑，出片同时交 cutindex。
2. 游戏录屏 / 演示片：一 + 二 必跑，三 建议跑。
3. 主控与调度：不跑这些（不是生产机），负责检查回执里有没有这三项的实测数字。