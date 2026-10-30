1. **今日队列统计**：完成35，失败1，在队（Running）1。
2. **最优先堵点**：`bigstream-drama` 处于 BLOCKED 状态且无供给，需立即解锁其剧本/分镜输入。
3. **可执行活**：
   - **bm-b**：调用 `self-dispatch` 扫描并消费 `bigstream-drama/script.json` 以消除 IDLE-CONFIRMED x7 告警。
   - **bm-c**：针对 `fluxverse/city-assemble` 启动本地 GPU 任务，将产出写入 `fluxverse/viz_data.zip`。