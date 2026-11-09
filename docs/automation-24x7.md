# 7x24 自动化运行手册（2026-11-09 修复后）

> 目标：智能体按集团规则 7x24 自动跑，算力分三层用，云端只在必要时碰。
> 本件只写「怎么跑、在哪看、坏了怎么救」，规则正典仍在 AI.md / docs/governance.md / cph4/fleet/*。

## 一、现在的运行面（launchd 常驻）

| 服务 | 作用 | 状态 |
|---|---|---|
| com.fluxgroup.pulse | 主控脉 `master_pulse.py --loop 45` | 运行中 |
| com.fluxgroup.gateway | 本地模型网关（令牌/并发/白名单） | 运行中 |
| com.fluxgroup.webai | 本地模型网页（8088） | 运行中 |
| com.fluxgroup.agentlane | 32k 单槽车道（11436） | 运行中 |
| com.fluxgroup.fleetbus | 机队事件总线 | 运行中 |
| com.fluxgroup.watchdog | 看门狗 | **未加载**（上次退出 0） |
| com.fluxgroup.loadwatch | 负载守望 | **未加载**（上次退出 1） |

主控脉一拍约 170s（blocker_loop 全量 95s + state_push 35s 是大头）；blocker_loop 已加 300s 节流，
其余拍 <1s 返回。

## 二、分层算力（谁干什么）

| 层 | 载体 | 什么时候用 | 入口 |
|---|---|---|---|
| L1 规则 | 主控脉 24 个阶段、门禁、台账、心跳 | 能算出来的判断，永不调模型 | `Tools/fleet/master_pulse.py` |
| L2 本地 | Ollama 11434（机队，parallel=3）/ 11436（agent，32k 单槽） | 分类/摘要/判重/短问答 | `local_model.py`、`llm_client.py` |
| L3 云端 | Codely（公司部署，litellm） | 深判、架构、跨域裁决，**人工或升级触发** | `codely` CLI（`~/Library/Application Support/Tuanjie Cowork/bin/codely`） |

L2 纪律：`llm_client` 没令牌=缺料（rc=3），先本地判、不发请求；失败熔断 300s，禁止空打网关。
L3 纪律（谨慎）：只给「L1/L2 都判不了」的阻塞与升级件；不放进任何循环；每次调用留记录；设日上限。

Codely 实测可用：CLI 1.0.0，endpoint `https://codely-litellm.tuanjie.cn/v1/models`，
model `codely-core`（context 600k），OAuth 凭据在 `~/.codely-cli/oauth_creds.json`。

## 三、今天修了什么

**症状**：主控脉 `phase=cycle-start`、`git=merge-conflict`，从 16:31 起反复 rebase abort，
09:00 之后大部分阶段没执行——等于自动化停摆。

**根因**：状态面塞在 git 里。本地 12 个提交 vs 远端 17 个，queue-receipts 每几分钟被写一次，
pull 每次都撞本地改动 → 合并失败 → rebase 中止 → 下一拍再来一遍。

**处置**：
1. 停脉（launchctl bootout）；
2. 备份队列与备队列到 /tmp；
3. 打 rescue tag，提交待同步回执；
4. `git merge origin/main -X ours`（本地状态优先，保住本机真实队列）；
5. 重启脉，验证 `git=ok`、阶段恢复、推送成功（ahead 3 / behind 0）。

**同轮产出**：两张真卡已 OPEN 并进队列——36 款隐私政策（bm-a）、bm-b 配音素材通道（bm-b）。

## 四、再堵了怎么救（30 秒版）

```bash
launchctl bootout gui/$(id -u)/com.fluxgroup.pulse
cp cph4/fleet/PRODUCTION-QUEUE.jsonl /tmp/q.bak
git add -A && git commit -m "state: pre-sync snapshot"
git fetch origin && git merge origin/main -X ours -m "sync: local truth wins"
git status --short            # 必须为空
launchctl kickstart -k gui/$(id -u)/com.fluxgroup.pulse
```

判断恢复：`python3 -c "import json;d=json.load(open('cph4/fleet/dispatcher/PULSE.json'));print(d['phase'],d['git'])"`
—— 出现 `git ok` 且阶段 sec 不再冻结即恢复。

## 五、下一步（未做，等拍板）

1. 根治 git 抖动：状态面迁事件总线（11-03 的 EVENTBUS 单已有影子期），git 只留正典与代码；
2. 把 watchdog / loadwatch 重新纳入常驻（现在没加载，等于少两道保险）；
3. L3 加日预算与调用台账（Codely 按次计费，谨慎使用）。

## 六、分层路由（2026-11-09 落地）

- 唯一源：cph4/fleet/LOCAL-MODEL-POLICY.json 的 routing 段；桥：Tools/fleet/codely_bridge.py。
- 优先级：L0 人/CEO > L1 确定性 > L2 本机 Ollama > L3 公司 Codely。
- 查层：python3 Tools/fleet/codely_bridge.py --route-check <task_class>
  实测 classification -> L2；architecture / unity_tool -> L3（需升级理由+数据分级+授权引用）。
- 自检：--self-test 28/28 通过；L2 实跑 37.3 tok/s、0.9s、JSON 合法。
- L3 不设次数上限（CEO 2026-11-09），但必须带升级理由、数据分级与授权引用，调用留记录在
  cph4/fleet/state/codely-bridge/logs。

### git 止血

.gitattributes 已给 cph4/fleet/*.jsonl 配 union 合并（队列/备队列/回执台账），
pull 不再整文件冲突——今天主控脉被 git 卡死的直接原因就是这几个 jsonl 的整文件覆盖。


## 七、看护服务（2026-11-09 18:4x 起）

- com.fluxgroup.watchdog：每 120s 跑 pulse_watchdog --apply --stale-s 1200，退出码 0；
- com.fluxgroup.loadwatch：每 60s 跑 supply_guard，退出码 0；
- 供给口径修正：bm-m（role=主控、heavy_forbidden）不再纳入产线卡水位考核
  （AUTONOMY-CONFIG.supply.exclude_nodes），只考核 bm-a/bm-b/bm-c；实测三台各 3 张可跑。

这样看护服务不再因为"调度机没有产线卡"长期报红——长期红等于没人看红。


## 八、状态同步面（2026-11-09 根治"脉被 git 卡死"）

根因：主控脉每拍先 commit 状态再 pull，任何冲突/脏树都会吃掉整拍（实测 152-188s）。

改法：把 git 从脉里拆出去。
- 脉：plist 注入 PULSE_NO_PULL=1，只跑阶段，**永不碰 git**；git 状态记为 skipped；
- 同步面：com.fluxgroup.statesync 每 60s 跑 Tools/fleet/state_sync.py——提交 cph4/fleet 生成态、
  fetch、快进或本地优先合并、push；失败 3 次熔断 15 分钟，只记 state/state-sync.log，不影响调度；
- 手写代码策略：Tools/ 与 docs/ 脏时同步面**不动**（交给人/会话），生成态可以自动提交。

代价：本机最坏晚 60s 看到远端状态；换来的是 git 再坏也不影响 7x24 调度。

