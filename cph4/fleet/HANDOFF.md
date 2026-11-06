# 交接一屏（2026-11-06 10:42）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（0 张）


## 二、待判（20 张在队列等机器）

- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `DOCS-_已封存_盛永康旧软著` 隐私政策 _已封存_盛永康旧软著（无归属）
- `DOCS-_报审提交区` 隐私政策 _报审提交区（fleet-ops）
- `FREE-MEM-DIAG-bm-c-20261106` @bm-c lane=gpu-production | 空闲内存诊断（dry-run，不杀进程）| 回执窗 3h（fleet-ops）
- `Q-MV-ANCHOR-WORDS-DRAIN-20261106` None（无归属）
- `Q-MV-ANCHOR-WORDS-DRAIN-BMA-20261106` None（无归属）
- `R-MODEL-RADAR-BMA-20261106` 本地模型日报·bm-a：扫上游新档+实测+按两条判据决定是否换档（已 1.9 天未跑）（无归属）
- `R-PLAN-BIGDOMAIN-20261106` BigDomain·硅基域商业化 线级体检与缺口清单（bigdomain）
- `R-NEXT-BIGGAME-SUBMIT-P-20261106` 游戏提审·真实缺件重盘（隐私已齐，重算图标/截图/台账/包体）（biggame）
- `R-NEXT-BIGSTREAMD-EVIDENCE-20261106` 漫剧证据目录补齐判定：画面/配音工段为何为空（一页含根因与补法）（bigstream-drama）

## 三、阻塞（8 项断言红 / 0 台机不一致）

- 断言 I1：5 条
- 断言 I2：8 条
- 断言 I3：55 条
- 断言 I4：18 条
- 断言 I6：7 条
- 断言 I7：3 条
- 断言 I12：26 条
- 断言 I14：4 条

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 86.2，返工 15，产出年龄 46.5
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 10.6
- bigstream-duanju：过闸率 71.4，返工 3，产出年龄 159.9
- biggame：过闸率 82.9，返工 47，产出年龄 65.3
- asset-lib：过闸率 63.9，返工 17，产出年龄 14.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。
