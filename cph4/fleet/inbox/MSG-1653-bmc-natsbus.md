# MSG-1653-bmc-natsbus — NATS 机队总线 bm-c 铺装回执（@bm-c 派单）

**执行窗**: bm-c r1121-continuation（2026-10-19 16:4x-16:5x）
**溯源**: docs/orders.md 16:1x 机队实时通信总线铺装收口行〔via bm-a 交互窗〕·正身 R-20261019-fleet-realtime-comm-01
**结果**: 三步全 PASS — bm-c 节点上线·KV 心跳在册·fleet-live-status 三机行全绿

## 步 a: Tools\nats\bootstrap-nats.ps1
- 首跑 github 直连下载 5min 零输出挂死（GFW 已知面）→ **gh-proxy.com 镜像前缀愈合**（常设镜像律）落钉版二进制 → 复跑 bootstrap = `NATS-BIN OK (pinned versions present)` rc=0（幂等验证过）
- nats-server **v2.15.1** / natscli **0.5.0**（钉版恒等·K:\Fluxgroup\FluxGroup\Tools\nats\bin\）

## 步 b: register-nats-bus.ps1 -Role node -Server nats://100.110.185.62:4222
- NodeId=**bm-c**（Tools\fleet-nodes.json host 匹配实测命中）
- 任务 **FluxGroup-NatsHB** every:1m 注册 OK（wscript //B //nologo 隐藏链零闪）
- S4U 未提权拒（0x80070005 已知面）→ InteractiveToken 降级 + S4U 转换已入 Tools\task-s4u-backlog.md 候提权窗口（D-20261002-02 既有裁决面如实延续）
- **deploy=ignite: fire OK observed 2026-10-19 16:48:58 result=0 (deployed)**
- **BUS OK role=node node=bm-c server=nats://100.110.185.62:4222**

## 步 c: netdiag 全文

=== tailscale netcheck ===
Report:
	* Time: 2026-10-19 16:52:43.6959454+08:00
	* UDP: true
	* IPv4: yes, 117.81.73.25:1796
	* IPv6: yes, [240e:3a8:4cc3:2260:e5d4:d97d:dbd9:7ef0]:54447
	* MappingVariesByDestIP: false
	* PortMapping:
	* CaptivePortal: false
	* Nearest DERP: San Francisco
	* DERP latency: sfo 141.3ms / lax 158.2 / den 175.3 / sea 177 / dfw 185.6 / nue 187.3 / mia 204.1 / ord 205.6 / tor 206.6 / hnl 207.8 / nyc 208.4 / iad 212.3 / tok 217.7 / par 219.7 / lhr 221.2 / ams 221.3 / fra 228.5 / hel 231.4 / mad 235.4 / hkg 236.3 / waw 239.3 / **sin 253.8** / syd 290.9 / blr 338.1 / nai 342.8 / dbi 351.6 / sao 376.2 / jnb 392.3

=== tailscale status ===
100.123.74.104  bm-c  sunjs666@  windows  -
100.110.185.62  bm-a  sunjs666@  windows  active; relay "sin", tx 1733228 rx 1739384
100.82.175.0    bm-b  sunjs666@  windows  idle, tx 796 rx 668

（netdiag 定谳面：直连失败同 FleetLink 2026-10-16 实锚——bm-a 经 sin 中继 active·bm-c home DERP=sfo 141ms 但最近可用中继含 sin 253.8ms·传输层阶梯[选区修复/国内自建 DERP=需云服务器·CEO 物理件域/直连=同址或端口映射·CEO 物理件域]与 R- 件口径一致·git 降级双轨照旧不切热路径）

## KV 收据证据（派单回执要件）

`nats -s nats://100.110.185.62:4222 kv get FLEET_STATE state.bm-c` →
```
FLEET_STATE > state.bm-c revision: 71 created @ 2026-10-19 16:49:10

{"node":"bm-c","host":"FLUXGROUP","ts":"2026-10-19T16:49:08","ram_free_gb":7.6,"cpu_load_pct":8,"disk_free_gb":545}
```

## 验收线实况（fleet-live-status.ps1 -Server nats://100.110.185.62:4222 @ 16:51:27）

```
bm-a   ts=2026-10-19T16:51:12 age=  19s ram_free=31.1GB cpu=26% disk_free=616.4GB host=DASHENG
bm-b   ts=2026-10-19T16:51:23 age=  10s ram_free=13.2GB cpu=1% disk_free=358.8GB host=BIGMONEY
bm-c   ts=2026-10-19T16:51:06 age=  29s ram_free=7.6GB cpu=15% disk_free=544.9GB host=FLUXGROUP
bm-d   MISSING/STALE (装配未完·预期)
```

**三机行全绿**（bm-d 在装=预期缺失）。

## 坑律追加（bm-c 实跑发现·双向回灌）

1. node 机跑 fleet-live-status.ps1 **须带 -Server 指中枢**（脚本默认 127.0.0.1=hub 假设）——不带则四机全 MISSING/STALE 假面（本窗首跑实锚）。建议下版默认从 fleet-nodes.json 读 hub 地址或按 role 解析。
2. github 直连 zip 下载在 bm-c 挂死（5min 零输出）——bootstrap-nats.ps1 的 Invoke-WebRequest 无超时参数，gh-proxy 镜像前缀是正解（本窗已用·钉版字节恒等幂等验证过）。

回执完毕。bm-c 总线面=常设在役（心跳任务 every:1m 自续）。
