# 《星晴》PACK-B · R4 单镜重烧回执（C2160）

> 前序：`DIRECTOR-REVISE-RESPONSE-PACKB-C2159.md` §2（R4 取证结论：画面层不可修，须重烧）
> 本轮性质：crash-adoption（前班 00:51 死于后端 502，零盘污、零号消耗）

## 一、本轮目标

把 C2159 的 R4 结论从「文档判定」变成「GPU 上的实际重烧」：S1-07（30.000-38.125s）单镜 1344×768 int8、226 帧、
提示词删掉「像年轻女人的云」全部指代，改为云朵本体的物性描述；出两枚候选供原生帧判读，不盲烧第三枚。

## 二、落地件

| 件 | 路径 | 说明 |
|---|---|---|
| 波清单 | `cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-packB-r4-s107-c2160.json` | 2 单元：`XQ_B-S1-07-r4a` seed 21009 / `XQ_B-S1-07-r4b` seed 21002（均在 21000-21015 未用带内），首帧沿用已批准帧 `media/MV/mv0001/xingqing/t1r1hd/S1-07_s21009.png` |
| runner 补丁 | `cph4/fleet/mv-album-001-jay/c2160_patch_seed.py` → `local-i2v/h3_i2v_album.py` | 新增单元级 `seed` 覆盖；未给 seed 时仍走 id-MD5 确定性种子（向后兼容，py_compile 通过） |
| 长烧自愈 runner | `cph4/fleet/mv-album-001-jay/c2160_s107r4_runner.ps1` | ComfyUI 探活 → 跑同一 manifest → 两枚齐则自停；runner 自带 SKIP（产物 >100KB 即跳）使重复点火零成本 |
| 计划任务 | `MiniGameComfyBurn-S107R4`（every:8m，InvisibleRunner 隐藏链） | 由 `Tools/task-register.ps1` 注册；S4U 被 UAC 拒绝 → 降级 InteractiveToken 并已入 `Tools/task-s4u-backlog.md`（登录期零窗，登出即停） |
| 收割旗 | `MiniGame/.codely-cli/engine-tick/wave-harvest-pending.json` | batch=C2160，三条 verdict 路径（日志 + 两枚候选） |
| 产能银行 | `cph4/fleet/work-bank/bm-c-gpu-bank.json` | `packb-s107-r4-rerender-c2159` blocked → claimed（by tick-C2160） |

## 三、提示词变更（R4 唯一实质改动面）

删除：「The soft white cloud **shaped like a young woman** drifts alongside them, its outline holding head,
shoulders and trailing hem as it keeps pace.」

替换：「A low cumulus cloud whose whole mass slowly drifts alongside the riders, **wind-eroded ragged edges,
warm sun-side rim, thinning into haze near the ground**.」

寓意留在剪辑里，不留在像素里（J-23 歌词意象律的又一次执行）。

## 四、点火实证

- ComfyUI 8188 由 `MiniGameComfyKeepAlive` 拉起，`vram_free=15.9 GB`；模型解析 int8 / turbo4step / nvfp4 CLIP / video VAE 全命中
- 01:01:21 首次点火（注册自带实弹）：`[XQ_B-S1-07-r4a] SUBMITTED frame=S1-07_s21009.png len=226 seed=21009`，轮询行 15s/60s/75s…
- 01:07 复查：只有一个烧进程（pid 39636），无重复提交
- 日志：`media/mv-album-001-jay/log-packB-r4-s107-c2160.out.txt`

## 五、下轮收割口径（未完成，不作完成宣称）

1. 原生帧判读两枚候选（约 2s / 5s / 7s）：云的轮廓必须能与天空分离、无粘贴硬边、不再读成行走人体
2. 胜出镜替换装配图 `S1-07` 映射（226 帧对 195 帧窗口，修剪逻辑不变）→ 重建 v6 → 复检 CHK-E1 剪辑语法 / 帧数 / 音频
3. 若两枚仍不可分：R4 升级为模型层结论（该模型把云与人体先验绑死），改走贴片替换方案，不再盲烧第三枚
4. 全片交导演席拉片，`DIRECTOR-REVIEW-PACKB-V6-PASS` 之前不经 CEO