# 回执 · bm-c 视觉工位（2026-11-14 23:00 – 11-15 00:10）

## 一、交付

| 项 | 结果 |
|---|---|
| KF 批（PROD-MV-SINGLE / mv-kf） | **38/38 成功，0 失败**，1120s，krea2 8 步 1344×768；产物 `outbound/krea2/30s-reel-v1/kf/XQ*.png` + `_job_receipt.json`(rc=0) + `_perf.jsonl` |
| 卡状态机 | 卡 `HO-PROD-MV-SINGLE-mv-kf` → **DONE**（judge=drama_rules，产物 56.8MB），自动交接下一道 mv-i2v |
| i2v 抽检（2 镜） | 2/2 出片，零失败：`XQ38_01` 468s/1.36MB、`XQ38_19` 498s/0.80MB，均 141 帧 1344×768 24fps、**逐帧唯一（零复读）** |

## 二、质量判定（人眼 + 机械双证）

### KF 38 张
- PASS 36、FAIL 1（XQ22）、REVIEW 1（XQ33），详见同目录 `QC-KF-XQ-20261114.md`。
- XQ22：指星手四指粘连 + 直视镜头（与 10-24 同镜判例同型）。
- XQ33：镜注本来就写「i2v 禁现画线（残余④）」，而本帧天空出现一条横贯全幅的笔直光带——**正是镜注禁止的东西**。

### i2v 抽检（这是本轮最重要的技术结论）
- **XQ38_01（XQ01 中景等）**：机械全绿，但 5.9 秒内构图从「中景全身」推成「中近景特写」（提示词写的是锁定机位），颗粒/黄昏反差同步减弱 → 判 **REVISE-lite**（可作 animatic，进母版需重烧）。
- **XQ38_19（XQ19 并肩同坐）**：**FAIL** —— 5.9 秒内两个人被改成「背靠背侧脸朝上」，等于整段重新构图，连续性报废。
- 结论：**H3 i2v 在 141 帧/5.9s 档位下保不住首帧构图**。下一批要么压到 73 帧（≈3s），要么改用 first_frame+last_frame 双锚，要么在提示词里用更强的静态机位/姿势锁。这不是提示词个例，是档位问题——38 镜整批直烧会大面积报废，必须先定档。

## 三、本轮修掉的工具缺陷（都有实锚）

1. `station_drive._comfyui_alive`：单次 3 秒探针 → 忙时假 DOWN 整轮阻断。改 3s→10s→20s 递进 + 端口在听兜底。
2. `station_drive.consume_outbox`：已消费（seen）的交接卡被分片手术删掉后**永不补回**（38 镜 KF 就这样丢过一次）。改为复核卡是否真在队，丢了补回并标 `recovered_from_seen`（23:08 实测 recovered=2）。
3. `job_kf_batch`：必败任务（prompts 不存在）**先抢 GPU 租约**再挂死，毒化整卡 2 小时。改为先验输入再领卡，加 owner/job_id 幂等与硬超时。
4. `gpu_lease`：①acquire 失败也写租约 → 下一次直接 BUSY；②空闲 ComfyUI 把 krea2 12.2GB 享在显存里，剩 3.1GB → need 12GB 永远等不到。改为失败不落盘 + 领租约前对「队列为空」的 ComfyUI 发 `/free`（实测 3.1G→14.4G）。
5. `mv_kf_batch`：默认 unet 指向本机不存在的量化档 → 整批秒失败；且 UNETLoader 同时扫 `unet/` 与 `diffusion_models/`。改为按目录列表找同前缀实存权重并打印替换记录。
6. `job_kf_batch` 自检夹具用 POSIX `true` 当无操作命令，Windows 下 rc=1 让两条腿永远红 → 换成当前解释器。
7. `h3_i2v_album`：新增 `--out` 覆盖，新一批片子可落自己的目录，不再覆盖已交付旧片段。

自检：`station_drive --self-test` **41/41 全绿**。

## 四、卡住的、需要别人动的

- `PROD-DRAMA-EP/kf`：卡指向的 `cph4/fleet/out/drama/kf_prompts.json` **不存在**，连续 3 次 FAIL。缺的不是执行器，是「剧本→prompt 表」这道工序。已发 `inbox/MSG-20261114-2340-bmc-kf-exec-and-drama-gap.md`。
- `PROD-MV-SINGLE` 的输出根就是 `mv0001-handover/.../30s-reel-v1/`，星晴（XQ）与《爱在西元前》（KF1-10/S1-11）共用一棵树：①本次 38 张 XQ 落进巴比伦 KF 目录；②那 11 条巴比伦 i2v 旧片让 `mv-i2v` 工序看起来「已完成」，plan 不再给星晴建 i2v 卡。需要主控裁决是否给 PROD-MV-SINGLE 单开输出根。
- 推送面：本地 main 与 `origin/node/bm-c` 双向分叉（本地 231 / 远端 41），`git push` 被拒；worktree 外科重放时 `station_drive.py` 冲突（远端删了 `import signal`，与我加的 `import socket` 撞行）。本轮改动已本地提交，等收敛窗或执行器折枝。

## 五、下一步（按优先级）

1. XQ22 / XQ33 按 `plan/kf_prompts-fix-20261114.json` 重烧（两镜，约 1 分钟/镜）——治愈版提示词已写好，等 GPU 空档。
2. 定 i2v 档位（3s 短档 or 首尾双锚），再放 38 镜整批。
3. 收敛窗：本地 main 与 node/bm-c 对账。
