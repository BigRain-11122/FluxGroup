# TJGenerators 异步任务 15 分钟无轮询超时坑（10-12 实锚·机队通用）

**现象**：meme-daily-v1 S3 微距镜任务（10-11 晚创建·status=running·progress 0）在续接会话中死单——check_task 报 `cancelled`，error 原文「**Task cancelled due to timeout (no status check for 15 minutes)**」；不扣费、无 output。同批 S4 备选镜因原会话 poller 曾查过一次状态而存活 completed。

**机制**：TJGenerators 服务端对异步任务要求 15 分钟内至少一次状态检查（poll），超窗即自杀取消——「在途任务能自己跑完」是错觉，**无轮询=死**。

**正法**：
1. 会话中断/续接后的接手窗，第一时间 check_task 验活在途单；死单立即重发（CDN file_url 永久，首帧引用可直接复用免重传）。
2. 生成后 poller 必须当会话跟完——Seedance 短任务 1-3 分钟即完成，「派了等待代理就走」的窗口=超时风险位；等待代理至少每 10 分钟内打一次状态面。
3. completed 单产物 TOS URL 直下有效（curl 直拉+ffmpeg -an 剥轨即用）。

**Why**：V1《慢慢踩》装配被此坑卡 12h+重摇一轮（S3 重发单 6acc3c7a3c134814fe38696f）。

**关联**：与 10-09 12:29「轮询失败≠生成失败」条互补——那条讲 poll 通道假阴性，本条讲无 poll 的服务端自杀面。两合成一句：**MCP 异步任务=轮询是生命线，一次都不能断 15 分钟**。
