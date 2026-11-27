# HOUSEKEEPING — 全盘梳理 v1（2026-11-27·bm-c 自媒体主力机）

> CEO 令「把无用的文件该删的删，该移交的移交，全硬盘梳理，把散落其他地方的文件挪过来」
> 原则：**只删可再生件与临时件**；个人文件（游戏/下载/备份/微信缓存）一律不动，只登记。

## 一、空间账（实测）

| 盘 | 清理前空闲 | 清理后空闲 | 回收 |
|---|---|---|---|
| K: | 391.0 GB | **436.8 GB** | **+45.8 GB** |
| C: | 1136.5 GB | **1151.8 GB** | **+15.3 GB** |
| **合计** | | | **≈ +61.1 GB** |

## 二、删了什么（全部可再生）

| # | 项目 | 大小 | 为什么能删 |
|---|---|---|---|
| 1 | `C:\Users\Dasheng\.codely-cli\tmp\*` | 15.56 GB / 34 万文件 | 代理临时目录 |
| 2 | `K:\Fluxgroup\.codely-cli\tmp\*` | 4.50 GB | 代理临时目录 |
| 3 | 18 个 Unity 工程的 `Library/obj/Temp/Logs/UserSettings` | ≈38 GB | Unity 重开自动重建（Assets/ 全保留，17/18 工程 Assets 在位） |
| 4 | `K:\Fluxgroup\.tools\motionprobe-t15` | 1.79 GB | 一次性探针工程（结论已入判例） |
| 5 | `K:\Test` | 0 | 空目录 |

## 三、挪了什么（散落件归位）

| 来源 | 去向 |
|---|---|
| `K:\ziyuanku`（素材包 0.18GB） | `K:\Fluxgroup\archive\stray-20261127\ziyuanku` |
| `K:\ComfyUICore`（旧 sidecar 0.08GB） | `…\archive\stray-20261127\ComfyUICore` |
| `K:\dsh-acl-recovery`（ACL 救援件） | `…\archive\stray-20261127\dsh-acl-recovery` |

## 四、没动的（个人/在用·只登记）

| 项 | 大小 | 说明 |
|---|---|---|
| `K:\game` | 307 GB | 游戏库，非我管辖 |
| `C:\Users\Dasheng\Downloads` | 66.9 GB | 个人下载（含 content-p1..p5 素材包 33GB、Rocky/Ubuntu ISO 36GB） |
| `D:\个人资料备份` / `D:\BaiduNetdiskDownload` | 22.9 / 22.3 GB | 个人备份与网盘下载 |
| `D:\huancun` | 12.8 GB | 微信文件缓存（内有用户文档，不代删） |
| `D:\ComfyUI` | 215.6 GB | 在役模型与输出 |
| `D:\krea2_weights` | 50.1 GB | 在役权重 |

## 五、下一轮候选（需一句话授权再动）

1. `D:\Studios` **26 GB**——正典已判"退役冻结态"，可整目录归档或删；
2. `Downloads\content-p1..p5-20261120.zip` **33 GB**——素材包，若已解包可取删；
3. `D:\huancun` **12.8 GB**——微信缓存，可清（会丢聊天文件缓存）；
4. `media\musepose`（15.7GB）/`mvtools`（6GB）/`latentsync`（5GB）——工具权重，若产线弃用可移 D: 统一模型库。

## 六、移交（handover）

- **成片**：`media/mv-album-001-jay/release/AXYQ-FINAL-v1-768p.mp4`（1344×768·234.25s·102.5MB）+ 回执 `DELIVERY-AYXQ-FINAL-v1.md`；
- **全盘交付索引**：`cph4/fleet/MEDIA-INDEX-20261127.md`（38 件≥3MB 成片；含 11-25 全片 master 与本日新版、30s v7–v14 历史）；
- **可复现件**：`build_ayxq_final_v1.py` / `ayxq-subs-v1.ass` / `.assembly-plan-v2.json` / `.assembly-audit.md`；
- **本回执** + 清理脚本（`.codely-cli/ayxq_cleanup.py`）随仓留档。

---
署名：bm-c 自媒体主力机·2026-11-27
