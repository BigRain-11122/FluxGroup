# 主控 MacBook 电源与性能档位 v1（2026-11-03）

CEO 令：「插电就满性能释放，拔电就回归正常」。
本文件是这台机器的**唯一电源档位正身**；改档先改这里，再执行命令，避免下次靠记忆。

## 一、两档到底设了什么（已实测回读）

| 项 | 插电（AC） | 拔电（Battery） | 为什么 |
|---|---|---|---|
| lowpowermode | 0（关） | 1（开） | Apple Silicon 唯一的性能/省电开关；插电关掉=满性能，拔电打开=回归正常 |
| sleep | 0（永不系统睡眠） | 15 分钟 | 插电主机常醒（CEO 令「主机正常」）；拔电按系统默认 15 分钟 |
| displaysleep | 10 分钟 | 5 分钟 | CEO 2026-11-03 令：插电 10 分钟无操作屏幕休眠，主机不休眠；拔电 5 分钟 |
| disksleep | 0 | 0 | 外置盘一睡就掉卷（11-02 实测 3 小时重枚举 3 次） |
| powernap | 1 | 1 | 苹果默认，不动 |
| womp | 1 | 0 | 插电可网络唤醒（远端起服务开会话） |
| debug.lowpri_throttle_enabled | 1 | 1 | 苹果默认，不动（CEO 令「其他设置按照苹果系统逻辑走」） |

## 二、必须说清的事实（别被"满性能"骗了）

1. **Apple Silicon 没有 CPU 调频器**。没有 `cpufreq`、没有 governor、没有倍频可锁。
   能动的只有三样：低电量模式、睡眠/挂起策略、I/O 优先级。
2. 真正的上限由**散热与功耗墙**决定，任何软件设置都改不了它。温度到线就掉频，属正常保护。
3. 除「插电屏幕 10 分钟 / 拔电屏幕 5 分钟 / 插电主机不睡」这三条外，其余一律保持苹果默认
   （powernap、womp、sleep、I/O 节流都不做非标准改动）。

## 三、执行命令（照抄可用）

```bash
# 插电：满性能
sudo pmset -c lowpowermode 0 sleep 0 displaysleep 10 powernap 1 womp 1
# 拔电：回归正常
sudo pmset -b lowpowermode 1 sleep 15 displaysleep 5 powernap 1
# 两块都不许盘睡（外置盘保命项）
sudo pmset -a disksleep 0
# 不关 I/O 节流（苹果默认，2026-11-03 CEO「其他设置按苹果逻辑」）
```

本机 sudo 走 GUI 提权，实跑用的是：
`osascript -e 'do shell script "..." with administrator privileges'`（会弹一次系统授权框）。

## 四、怎么验

```bash
pmset -g custom          # 看 AC / Battery 两段是否与上表一致
pmset -g                 # 看当前生效与谁在阻止睡眠
pmset -g therm           # 有无热警告/性能警告
pmset -g ps              # 当前是 AC 还是电池
```

## 五、回滚

```bash
sudo pmset -c lowpowermode 0 sleep 15 displaysleep 10 powernap 1 womp 1
sudo pmset -b lowpowermode 0 sleep 15 displaysleep 10 powernap 1
sudo sysctl -w debug.lowpri_throttle_enabled=1
```

## 六、失效条件

1. 插电仍频繁掉频（`pmset -g therm` 出现 performance warning）→ 是散热问题，改用外置散热或降载，不要加软件开关。
2. 外置盘再次掉卷 → 先查 `disksleep` 是否被人改回，再查供电（无源 hub 有实测断电记录）。
3. 拔电续航明显变差 → 查是否有进程在拔电时仍跑重活（拔电时应让重活排队）。