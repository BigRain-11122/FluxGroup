# 公众号算力归属 + 出稿闸（2026-11-27 实测批）

> 本文件是 2026-11-27 一批改动的正身细节。memory.md 只留短指针，避免膨胀。

## 一、CEO 两条令（原话）

1. 「每周要有一个主题 围绕主题去写」
2. 「要从根本上把这块算力和模型全部给公众号，可以做公众号的采集，训练，实战出稿什么的」

这两条覆盖了此前「主控只做调度+轻量模型、公众号排在机队后面抢时段」的定位。

## 二、算力归属（机器面）

正身 = `cph4/fleet/GZH-COMPUTE-ALLOCATION-v1.json`（v1-20261127）。四子线：

| 子线 | 执行体 | 吃什么 | 判据 |
|---|---|---|---|
| collect | `Tools/fleet/gzh_loop.py` | 浏览器（browserd 单线程） | ARTICLES 净增>0 且失败率<30% |
| train | `Tools/fleet/gzh_trainset.py` | GPU 独占窗口 | trainset ≥100 行且盲评差≥10pt |
| write | `Tools/fleet/gzh_write.py` | GPU 独占（`gpu_lease("gzh")`），9B 9.1GB | 结构+严谨+权威三闸全过 |
| quality | 三闸 + 盲评 | CPU | 喂 AI 腔稿必须判红 |

配套改动：
- `LOCAL-MODEL-POLICY.json` 新增席位 `gzh_writer` = `qwen3.5:9b-mlx`（8.9G，keep_alive 20m，reserved=true）。
- `res_alloc.py` 平台权重改：gzh 6、chejiahao 5、bilibili/zhihu/xhs/douyin/toutiao 各 1；allowed 增 `gzh_write`。自检 16/16。
- 停用 `com.fluxgroup.trainloop`、`com.fluxgroup.trainpipeline`（吃 B 站评论语料）。恢复命令写在正身 `compute_policy.restore_cmd`；8788 的 mlx_lora_server 不停不重启。

## 三、每周主题（机器面）

- 正身：`THEME-SEASONS-v1.json` 新增 `weeks`（W0–W10，2026-11-24 → 2027-02-08）+ `weekly_rule`（每周期望 1-2 篇；偏离主题=对不上本周关键词即跑题；热点可插但周主题必须补）。
- 解析器：`Tools/fleet/gzh_week.py`，`--self-test` 4/4：连续性无空档无重叠 / 周主题不重复 / 日期可反解 / **负控（把主题抠空必须判红）**。
- `gzh_loop.py` 增 `write` 相位：当天 `drafts/<date>/draft.md` 不存在或 <1200 字节就按本周主题出一篇，出完不再重复。
- 踩到的自伤 bug：`_now()` 返回 datetime，写成 `_now()[:10]` 直接 TypeError 把整拍判 CRASHED，而原自检没覆盖新分支 → 已补回归断言（日期助手+decide 能跑）。

## 四、9B 出稿的实测结论（这条最重要）

同题（深色模式发灰，硬核，要求 2000-3500 字）两轮：

| 轮次 | 字数 | 结构闸 | 严谨闸 | 权威闸 |
|---|---|---|---|---|
| 1 | 1039 | 未过（0 小标题，5 段>120 字） | 过（12/100） | 未过 |
| 2 | 1153 | 未过 | 过 | 未过 |

模型编造清单（全部是它自己生出来的，没有任何来源）：
- `ISO 15008:2017`「车机必须维持高对比度」
- `SAE J3016`「L2+ 要求信息呈现清晰无误」
- `NHTSA`「触控目标不小于屏宽 1.5%、外扩 8px」
- 「韦伯对比度 >60% 安全区间」
- 履历：「我曾参与某项目的视觉迭代」「我的团队在重构某旗舰车型」

关键判据：**「像人写的」≠「说的是真的」**。AI 指纹闸（`gzh_rigor_check.py`）给这篇 12/100（阈值 45）判通过——它只管句式，抓不到编造。所以编造必须另设一道闸。

## 五、新增权威闸

`Tools/fleet/gzh_authority_check.py` + `cph4/fleet/social/gzh/AUTHORITY-WHITELIST.json`：
- 标准/法规编号（ISO/IEC/SAE/JIS/DIN/NHTSA/FMVSS/UN R/ECE/GB/T/GB/QC/T/JJF/EN）必须命中白名单，否则 FAIL（不是 WARN）。
- 履历句式（我曾参与/我的团队/我司/我在某项目/我主导/我负责过/我带队…）一律 FAIL，无论真假——要写由人写。
- 两位以上小数的阈值 → WARN。
- 自检 4/4；用真模型稿做负控，4 处编造全抓到。
- 白名单当前只有 `WCAG 2.1`（W3C 原文核过）。加条目流程写在文件 `_how_to_add`：先找到原文再填。

## 六、时间与功耗

- 两轮重写合计 59 分钟：真因是当时在**电池**上，GPU 限速（实测 18.6s/步 vs 接电 4s/步），train-loop 日志同时记着「暂停开训：电池供电」。
- 已给重写加时间预算 `--budget-s`（默认 420s），剩余不足 60s 就停手交初稿加备注。
- 9B 解码实测 18.9 tok/s（接电），加载 9.1GB，生成全程 swap 不涨（3665MB 持平）。

## 七、运维坑（本机）

- macOS **没有 setsid**（`setsid: command not found`）；`nohup ... &` 会被回收。长期跑用 launchd，或工具自带后台模式。
- `launchctl disable` 对「已在跑的实例」不生效：禁用后仍可能有一个 StartInterval 起的实例跑 40+ 分钟，要 `kill` 掉才算停。
- 判「算力不够」之前先 `pmset -g batt`：电池态 GPU 限速 4-5 倍，先接电再谈分配。

## 八、交付物位置

- 人工稿（四闸全过，约 2500 字）：`~/BigLoom/gzh/drafts/2026-11-27/draft.md`
- 模型稿（对照证据）：同目录 `draft.model.md`
- manifest 里 `model_baseline.verdict` 写了不达标原因；`write_lane_verdict` 写在算力正身文件里。
