# 跨机执行通道 v1（2026-11-07 立 · 实证打通）

> 一句话：**卡就是远程执行器**——节点认领卡后用 `shell=True` 执行卡里的 `cmd`，
> 所以"能不能远程让它干活"从来不是能力问题，只是没人用；真正卡住的是
> 「新代码到不了机器」，而自包含命令不需要任何文件。

---

## 一、事实基线（都实测过，不是推断）

1. **执行面存在**：`Tools/queue_claim.py` 第 376 行
   `subprocess.run(job["cmd"], shell=True, cwd=...)`。卡里的 cmd 在节点本机执行。
2. **取卡面存在且走 origin**：lane 模式读 `origin/main:cph4/fleet/lanes/<node>.json`
   （`fleet_lane.lane_payload` 优先取 origin 快照），所以**工作树分叉不影响收卡**。
3. **poke 只做 `git merge --ff-only`**：节点一旦有本地提交，pull 永远失败。
   这是"我们修好了、机器还在跑旧码"的唯一结构性原因。
4. **FleetLink 端点只有三个**：`/health`、`/status`、`/poke`（`GET /` = unknown-endpoint）。
   没有任何通用远程执行端点——不要再找第四条路。
5. **在场判定要三信号**：NATS KV（总线可能死）→ 车道文件 mtime（本侧不重写就过期）
   → FleetLink `/status`（tailnet，实测可用）。只信第一个会把在线的机器全判 OFFLINE，
   于是一张卡都派不出去（2026-11-07 实测）。

## 二、通道形态

```
master 写卡（cmd = 自包含命令） → origin:PRODUCTION-QUEUE/lanes
        ↓ (节点 pull/fetch 只读 origin 快照)
节点 queue_claim / lane_agent 认领 → shell=True 执行 cmd
        ↓
节点写回执 cph4/fleet/queue-receipts/<id>-<node>.json → push origin
        ↓
master closer 按 deliverable + rc 判定 DONE/FAILED
```

要点：**cmd 的产物路径必须等于卡的 deliverable**，否则被判 E-ARTIFACT
（实锚：v1 用 `$env:COMPUTERNAME` 写文件名，与 `closeout-bm-a.json` 对不上，白绿一次）。

## 三、Windows 自包含命令的写法（踩过的坑）

1. **用 `powershell -EncodedCommand <base64>`**，脚本 UTF-16LE 编码后 base64：
   - 躲开 cmd.exe 的引号转义地狱
   - 躲开 **PS 5.1 在 GBK 码页下读无 BOM .ps1 会吃掉引号字节**的老坑
   - 命令长度上限 8191，实测 3.7k 安全
2. 脚本文本必须**纯 ASCII**（中文注释会让某些代码页解析出错）。
3. 需要节点身份时由**卡注入节点 id**，不要依赖 `$env:COMPUTERNAME`（主机名≠节点代号）。

## 四、安全线（写在脚本里，不靠自觉）

收口动作只允许：救生分支 → `fetch origin main` → `reset --mixed origin/main`
（提交对齐、工作树文件保留）→ `checkout origin/main -- Tools`（工具树换 origin 版）
→ 自校验并写回执。

**禁止**：`reset --hard`、`rebase`、`push` 历史、动计划任务、删未提交业务文件。

## 五、用法

```bash
python3 Tools/fleet/remote_closeout_card.py --nodes bm-a,bm-c        # 预览
python3 Tools/fleet/remote_closeout_card.py --nodes bm-a,bm-c --apply # 投卡
python3 Tools/fleet/remote_closeout_card.py --print-cmd --nodes bm-b # 打印可粘贴命令
```

投卡后：`master_agent.py --node bm-m --root .` 派进车道 → `git push`（节点只读 origin）
→ `POST /poke` 唤醒 → 等 `cph4/fleet/queue-receipts/closeout-<node>.json`。

## 六、实证（2026-11-07）

| 节点 | 收口前 | 收口后 | 回执 |
|---|---|---|---|
| bm-a | 已对齐（0/0） | head==origin | `REMOTE-CLOSEOUT-bm-a-...-bm-a.json`（v1，E-ARTIFACT 仅文件名问题） |
| bm-c | ahead 9 / behind 27 | **head==origin，aligned:true** | `closeout-bm-c.json` |
| bm-b | ahead 542 / behind 316 | 待回执 | 进行中 |

## 七、能力边界（诚实）

1. 卡能跑的前提是**节点上有认领任务**（HQ-ProductionClaim）或 lane_agent 在跑。
   实测 bm-b 历史上无生产认领任务，这类机器需要本机装一次任务，或走 lane_agent。
2. 卡不是万能后门：它只能做"用节点现有解释器能跑的事"（powershell/git/python）。
3. 回执必须由节点自己 push 回来；节点 push 权限坏了，就只能靠下一轮 pull 时看产物。