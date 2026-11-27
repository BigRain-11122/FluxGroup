# 玩法推进 · 进度与自动任务说明

> 人类不用读这份；要看做了什么，直接看最后一节。
> 下一轮先读它，做完把结果追加到「六 轮次记录」。

## 一 边界

- 只写 `D:\FluxGroup\silicon-earth\DESIGN\`（含 `proto\`）。
- 禁改：`modules\` 下任何文件、`TASKS.json`、其他业务线目录。
- 不引入新依赖、不联网取数据；`entry.html` 必须自包含、`file://` 双击可用。
- 一轮只做一件事，改动 ≤3 个文件。

## 二 固定命令

```powershell
python D:\FluxGroup\silicon-earth\DESIGN\proto\build_entry.py

& "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless --disable-gpu --no-sandbox `
  --user-data-dir="$env:TEMP\chr-proto-<随机>" --window-size=1600,1000 `
  --virtual-time-budget=3000 --screenshot="...\shot.png" `
  "file:///D:/FluxGroup/silicon-earth/DESIGN/proto/entry.html?r=R03&still=1"
```

截图后 `read_image` 亲眼看；确认完删 png（不进 git）。
**注意**：本机无头 Chrome 最小视口实测 **500×693**（`--window-size=390,844` 只得到 500 宽），所以"手机 390"验不了，只能验到 500。

## 三 待办

- [ ] 5 每区三条往事：把「后来的人说」扩到 3 条不同事件类型，可轮播
- [ ] 6 夜间版区页复查（深色下卡片对比度）

## 四 做完了怎么办

待办全清空时不要开新方向：找出 3 个真实缺陷，修其中 1 个，三个都记进来。

## 五 已否决（别再试）

1. **本地 Ollama 生成内容：不可用。** qwen3.5:2b 生成 64 token 用 107 秒（≈0.6 tok/s）且输出为推理残片，第二次 240 秒超时；9b 写一条史料 180 秒超时。
2. **Cowork 定时任务：报告成功但不干活。** 手动触发 status=succeeded、耗时 0.75 秒，sessionId 查无 transcript。

## 六 轮次记录

- 2026-11-27 基线：球→区→人→帮/问/记→三天回访。
- 第 2 轮：事后题词、同名编号、三天回访三结局。
- 第 3 轮：「你到之前的三天」、记忆缺口(lost)后果、时间标签「第 N 天的事 · X 天前」。
- 第 4 轮：**首屏持久化**——记住上次帮过谁，底部出现「你上次帮过 X · 第 N 天 · 去看看」；点击直达该区。
  **移动布局**：修了 canvas 尺寸导致的横向溢出；500 宽下无裁切、面板整宽可滚动。
- 下一轮第一件：每区三条往事（用最近三条事件各生成一句"后来的人说"，首屏轮播）。
