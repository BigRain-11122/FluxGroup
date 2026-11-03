# 交付面决策 · 2026-11-03

**决定：漫剧 60 集的有声交付面 = `media/drama-eps-audio`。**

- `media/drama-eps`（60 集）保留为**画面母版**，不覆盖、不删除、不重新混流。
- 对外发布、合流、上平台一律取 `media/drama-eps-audio/EPxxx.mp4`。
- 判定清单：`media/drama-eps-audio/MANIFEST-voiced.json`（verified 60/60）。

## 依据（全部为实测，不是计划）

1. 混音 60/60 完成：`drama-mix-out/r1203_ep001_060`，wall 161.9s，rc=0，peak 0.891。
2. 合轨 60/60 通过：逐集有 `a:0` 流，且与画面片长差 ≤ 0.25s。
3. 混音体检 60/60 OK：mean −20.9 dB，区间 −23.4 ~ −17.8 dB，零削波、零缺件。
4. 正片目录 60 集**全部无 a:0 流**（静音母版），不是"偶发缺音"。

## 为什么不是"直接覆盖正片"

覆盖会把唯一一份已验证的画面母版替换成混流版；一旦某集音轨有争议，无法回退对照。
两条目录并列，母版与交付版各自可核验，成本为零。

## 后续动作

- 平台改造（`bili_repurpose.py` 等）读入路径切到 `drama-eps-audio`。
- 若 CEO 要求"正片目录也要有声音"，用 `-c:v copy -map 0:v -map 1:a` 原地生成备份后再替换，不重编码画面。
- 混音器 `drama_mix3_r1003.py` 的 `render_sfx` 缺号落位补丁（`.bak-20261031-sfxsnap` 备份）不得回退。