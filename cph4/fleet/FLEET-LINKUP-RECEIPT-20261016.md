# FLEET-LINKUP-RECEIPT-20261016 · 机队联通打通战收据（CEO 全权授权令）

> CEO 令（2026-10-16 19:0x 原话）：「我授权你所有权限去打通，机队之间的高效联通。」
> 执行：bm-a 交互窗 19:53-20:1x。前置=FLEET-SYNC-AUDIT-20261016.md（他窗 17:00-18:25 体检+根治案·commit b988aa2）。
> 本件=联通令下的增量战果收据+剩余堵点台账（实测时间戳全部带）。

## 一、三机实时态（19:53-20:05 实测）

| 面 | bm-a | bm-b | bm-c |
|---|---|---|---|
| listener 版本 | **v1.9.2**（/health 160-270ms·pusher v1.3 监督在役） | **v1.8 带病**（8s socket 超时+出向内联自堵·升级在飞） | **v1.9.2**（849ms-1.4s·中继物理下限） |
| /health 可达性 | 本地秒级 | 周期性阻塞（撞内联推送窗即 20-40s 超时·空闲窗能答：19:55/20:03/20:05 三次实证活） | 稳定 |
| tailscale | relay sfo | relay sfo | relay sfo·tailscale ping 3 连「direct connection not established」 |
| pusher（出向） | **v1.3**（自刷新已生效·pid 68112·20:03:58） | v1.8 内联（369KB 明文互灌源头·被双端 256KB 快拒行实锤） | v1.9 独立进程 |

「bm-a /health ver 空」疑虑（上一窗移交项②）：排除——实测 `{"version":"1.9.2","ts":...}`，升级栈在跑。

## 二、当窗修复上链（commit **6e152fc**·本机自刷新点火实证）

1. **pusher v1.3 三修**（fleet-sync-pusher.ps1）：
   - `$rel` 未定义 bug：Poll-Publish 的 skip 日志空路径（审计面失明）→ `$e.rel`；
   - **gzip 空转根因（P0）**：对端 /health 探测失败（8s 超时·中继 RTT 370ms 下太紧）把**空版本缓存 10 分钟**（TTL 600s）→ bm-c（明明 1.9.2）被误判 legacy → orders.md 369KB 永久 skip、偶发探测成功轮走明文又被 bm-c 256KB 快拒打回——**热推送面整体空转、全靠 git 兜底**。修=失败缓存 TTL 60s+探测超时 8→12s+`peer-vers` 审计行；
   - skip 语义保守不变（防假成功黑洞：gz-only body 对 <1.9 对端=content 空→applied=0 假成功→pushed 标记毒化=数据黑洞，永不盲发 gz）。
2. **worker v1.6**（fleet-poke-worker.ps1）：单飞锁加 **pid 存活校验**——新鲜锁属死进程不再堵 poke 10 分钟，即时回收+`lock-reclaim` 留痕（向后兼容旧文本锁格式）。前对照：pusher 锁有 pid 校验、worker 没有（19:55 poke 后换血延迟疑似陈锁嫌疑面）。
3. **pusher v1.4**（commit **19dfc8f**·本机自刷新生效 pid 68844·20:15 实证）：**线上尺寸预检**——快拒线按 Content-Length 算的是 base64(gzip(...)) 信封尺寸而非明文；orders.md 实测 **711KB utf-8 → 线上体 452KB > 256KB** → v1.9.2 对端秒回 body-too-large → 旧版每 60s 空转弹跳一次**从未成功**。修=线上体 >256KB 诚实 skip（git carries）+fail 日志带路径。**勘误**：FLEET-SYNC-AUDIT §六「orders.md gzip 703KB→~130KB 过线/热文件秒级」宣称对 orders.md **从未实证成立**（当时 5 件成功全是小契约件）——audit 的 orders.md 热推收益作废，待 10-19 瘦身达标后才兑现。
4. 语法零错（Parser::ParseFile 两次）+pathspec 提交（防吞他窗暂存面）+range 行验真。

## 三、probe 实弹（20:0x·手动 gzip 原文推·零新增行零污染）

- **bm-c：HTTP 200 `{"ok":true,"applied":0,"kind":"union"}`——gzip 解码+union 链路全通**（PATROL LOG 18KB body·ms 级）；
- bm-b：HTTP 200 同体（v1.8 假成功面：无 gz 解码→content 空→applied=0）——同时证明 `cph4/fleet/dispatcher/PATROL-FLEET/` 目录在 bm-b **存在**（否则回 dir-missing）→**推翻 partial-clone 缺目录假设**；
- **bm-b 12s reject 病根定谳**：v1.8 socket 8s 超时 < 中继传 ~80KB 体需 12s → 读体切断 → 截断 JSON → 空 path → path-deny 响应 → pusher 记 reject。升级 v1.9.x（30s 超时+gz 解码）后**结构性自愈**，无需另修；
- **orders.md 决定性实验（20:11）**：pusher 同款格式全量推 bm-c → HTTP 200 `{"ok":false,"err":"body-too-large"}` 秒回——711KB utf-8/369005 字符 → 线上体 445-452KB > 262144 快拒线 → **orders.md gzip 热推从未成功过**（audit 档 §六 宣称勘误，见 §二.3）。

## 四、bm-b 换血在飞（当前唯一软堵点·三通道并行）

- 19:55 + 20:05 两次 poke 受理（ack 均 v1.8·accept 环活着）；
- 通道①poke→worker 刷新闸（盘码 fleet-link.ps1 1.9.2 > 运行 1.8 → 起新杀旧）；
- 通道②O-20261016-1745（BM 仓 origin/main 0cb8050dc 已核实）循环班消化：git heal（rebase 解楔）+监听器升级+回执；
- 通道③其夜班/晨班兜底（审计档既有安排）；
- 盯守=会话 cron 每 10 分钟探 /health 版本（勿重发 poke 添乱——接受队列积压会拖它阻塞窗）；
- 换血后预期全愈：监听环不再自堵（出向独立 pusher）+30s 超时+gz 解码+256KB 快拒自保护——本机日志的 bm-b reject/skip 族应归零。

## 五、物理层定谳（CEO 域候选·呈报不催办）

1. 本机**无 VPN TUN 适配器在跑**（Get-NetAdapter 实测：仅 Realtek 物理卡+Tailscale Tunnel+Hyper-V vSwitch）→「本机 VPN 接管」假设排除；但网关 10.86.96.1/自 IP 10.86.98.91 当日变更再次确认（netcheck portmap monitor 实证）；
2. **对称 NAT**（MappingVariesByDestIP=true）+零端口映射（PortMapping 空）→ UDP 打洞结构性失败（bm-b/bm-c 双对端 ping 全灭）；
3. LAN=10.86.96.0/22 大网段（arp 表 ~110 邻居·公司网）；三机曾同 LAN 直连 13ms（10-10 史），当日网络变更后 direct 全灭；
4. 三机 home DERP 全 pinned **sfo（232.9ms）**而本机最近 DERP=**sin（64.8ms）**→ 中继可优化空间 3.6 倍；但 DERP home 无 CLI 强制位（客户端自动选+sticky），换 DERP=对端重启 tailscaled 碰运气或改 derpmap（重工程）——候裁；
5. **对端出口疑 VPN**（bm-b 前科=Skyline TUN 工程·三机 home 全 sfo 佐证）→ 需 bm-b/bm-c 侧会话自查（对端 netcheck+Get-NetAdapter），本机不可代查；
6. 候选动作（物理件/对端域）：①bm-b/bm-c 查 VPN TUN ②网管面查网关变更后的客户端隔离 ③接受中继现状——软件层已压到当前物理下的最优（gzip+30s 超时+快拒+信号面解耦·实测时效=信号面秒级/热文件秒级/大件 git 10-20min）。

## 六、剩余项

1. bm-b 换血确认（cron 盯守中·换血后其推送面自动痊愈·对端 reject/skip 族应归零）；
2. orders.md 热推解锁条件（10-19 季度瘦身批次·阈值已数学化）：**base64(gzip(utf8)) ≤ 256KB**——当前 452KB 需减重 ~44%（归档旧年行可达）；
3. 物理直连恢复=CEO 域候选（§五·呈报不催办）；
4. bm-c 20:03:35 单次 ReadToEnd 连接重置（换血竞态窗孤例·probe 已证链路通·持续复发才立项）。

**当窗已闭环项**（勿重做）：
- bm-a /health ver 空→排除（v1.9.2 实测）；bm-c gzip 链路→probe 实证通；
- orders.md gzip 热推→定谳「从未成功」+v1.4 诚实 skip 已上线（弹跳空转终止）；
- pusher v1.3/v1.4+worker v1.6 三件→commit 6e152fc/19dfc8f 上链+本机点火实证。

**证据链**：本机 log.jsonl（pusher v1.3 起点/peer-vers/skip 带路径行）+ pusher.json（pid 68112 v1.3）+ origin 提交 6e152fc + probe 脚本 .codely-cli/tmp/sync_probe.py（输出双 ok）+ tailscale ping ×6 全 relay + netcheck（对称 NAT/网关变更）+ arp 表（/22 大段）。
