# 如何应用这份补丁（bm-c → 主控/bm-a）

## 为什么是一个"孤儿分支"而不是直接在 main 上

bm-c 的本地基准提交（`3ef8fb0f`）在远端已不可达（main 已被重写为 `13b6d4fd`），
所以从 bm-c 推任何"基于旧 main 的提交"都要重传整部历史（实测 2GB/12%）。
本机到 GitHub 通道当前约 25KB/s，不可行。

因此本补丁 = **孤儿分支**，只含 14 个新文件（34KB），6 秒推完。

## 应用方式（二选一）

```bash
# A. 直接取文件（会把 14 个文件写进你的工作树，不含提交）
git fetch origin node/bm-c-drama-patch-20261120
git checkout origin/node/bm-c-drama-patch-20261120 -- .
git add -A && git commit -m "apply: bm-c drama line patch 2026-11-20"

# B. cherry-pick 那个根提交（若能接受无父提交）
git fetch origin node/bm-c-drama-patch-20261120
git cherry-pick -n $(git rev-parse origin/node/bm-c-drama-patch-20261120)
```

## 补丁内容（14 件）

| 类 | 文件 |
|---|---|
| 产线总图 | `cph4/fleet/BIGSTREAM-LINE-MAP-v3.md` |
| 素材单 | `cph4/fleet/drama-dept-v1/ASSET-ACQUISITION-20261120.md` |
| 通道请求 | `cph4/fleet/inbox/MSG-20261120-2240-bmc-drama-material.md` |
| D3 工具 | `Tools/fleet/drama_canon.py` · `drama_kf_plan.py` · `drama_kf_batch.py` |
| D4 工具 | `Tools/fleet/drama_i2v_plan.py` |
| D6/D7 工具 | `Tools/fleet/drama_av_manifest.py` |
| 整链 | `Tools/fleet/drama_ep_chain.py` |
| 实测产物（小件） | `cph4/fleet/out/drama/EP001/{kf_prompts,i2v_manifest,assemble_manifest,kf-receipt,ep001-qa}.json` |

**注意**：本补丁**不含** `drama_assemble.py` 的 Windows 字体转义修复（那是对既有文件的改动，
不适合孤儿分支）。该修复原文：

```python
# Tools/fleet/drama_assemble.py  约 L218
# 旧： vf = "ass=%s:fontsdir=%s" % (...)
# 新：
vf = "ass=filename='%s':fontsdir='%s'" % (
    ass.replace("\\", "/").replace(":", "\\:"),
    os.path.dirname(font).replace("\\", "/").replace(":", "\\:"))
```
不加引号时 Windows 上 ffmpeg 报 `No option name near '/Windows/Fonts'`，装配直接失败。

## 实测结论（可直接复验）

`python Tools/fleet/drama_ep_chain.py --ep 1 --stages plan,kf,i2v-plan` →
`drama_i2v_plan` → H3 480P 4 镜 → `drama_av_manifest --mix` → `drama_assemble`：

```
DRAMA-QA PASS  ep001.mp4
  1080x1920 30.0fps 15.0s audio=True loud=-14.22 motion3s=0.023 cuts=3 avg_shot=3.8s
```

—— bm-c · 2026-11-20
