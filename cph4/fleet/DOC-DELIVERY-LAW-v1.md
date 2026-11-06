# 机队递送法 v1（DOC-DELIVERY-LAW-v1 · 2026-11-06 立）

> 一句话：**要回滚和历史的走 git；只要"对方此刻能读到"的走总线。**
> 立此法的原因：我们一直拿 git push 当广播，而推送成功 ≠ 对方收到——本机 main 与远端分叉 316/698 时，推送与拉取都会静默失效，令和文档卡在原地。

## 一、三条通道，按数据形态分流

| 数据 | 通道 | 键/位置 | 上限 |
|---|---|---|---|
| 命令、通知、裁决（结构化小消息） | NATS KV `FLEET_ORDERS` | 键=`<order-id>` | 每值 ≤1MB，实际应 ≤8KB |
| 文档、报告、交付说明、规格 | NATS KV `FLEET_DOCS` | 键=仓库相对路径点分化（`cph4.fleet.xxx.md`） | 每值 ≤1MB |
| 代码、二进制、模型、需版本回滚的正典 | **git**（唯一） | 正常分支/PR | 遵守大文件红线 |

判据自问两句：
1. 以后需要看「某一版」「谁改的」「回滚」吗？→ 是走 git。
2. 只是要让别的机器马上按最新这份干活吗？→ 是走总线。

## 二、送达必须有证明（本法的核心）

1. 写方：`python Tools/fleet/docbus.py put <文件>` 会打印 `sha256`，**把 sha 写进令里**。
2. 读方：`python Tools/fleet/docbus.py verify <key> <本地文件>`，`MATCH` 才算收到；`MISMATCH` 重取。
3. **「我已 push」不是送达证明**；「runner 日志里没有 PUSH-OK」也不是失败证明——一律以 sha 比对为准。

## 三、命令

```bash
# 文档递送
python Tools/fleet/docbus.py put cph4/fleet/xxx.md              # 自动生成键
python Tools/fleet/docbus.py ls cph4                            # 列出总线上的文档
python Tools/fleet/docbus.py get cph4.fleet.xxx.md 本地路径      # 取回
python Tools/fleet/docbus.py verify cph4.fleet.xxx.md 本地路径   # 校验

# 命令/通知
Tools\nats\bin\nats.exe --server 100.110.185.62:4222 kv put FLEET_ORDERS <id> <JSON>
Tools\nats\bin\nats.exe --server 100.110.185.62:4222 pub fleet.orders.broadcast <JSON>
```

hub = `100.110.185.62:4222`（四机共用，已实测跨机可读写）。

## 四、双写期（现在到取代 git 为止）

1. 新文档：**先总线（递送）→ 再 git（归档）**。总线是送达，git 是历史。
2. 两者冲突：以 `docs/orders.md` 台账里的 sha 为准，不以修改时间为准（跨机时钟有偏差）。
3. 命令文件 `cph4/fleet/cmd/<id>.json` 仍按旧法走 git，直到 `FLEET_ORDERS` 的读侧跑通一周无漏。

## 五、禁止

1. 禁止用 `git push` 当广播（分叉时静默失败）。
2. 禁止用总线传代码、模型、二进制（超 1MB 或需回滚）。
3. 禁止只在聊天/回执里说「已通知」，必须留总线键或 sha。
4. 禁止把 24h 后仍要引用的大段落只放总线——总线是递送层，不是档案层。

## 六、各机义务

1. 各机轮首：`docbus.py ls` 看一眼比自己本地新的键；发现新的按需 `get`。
2. 各机发令：令体走 `FLEET_ORDERS`，正文走 `FLEET_DOCS`，台账行仍写 `docs/orders.md`（簿记）
3. 主控：负责检查回执里有没有 sha；没有 sha 的回执视为未送达。