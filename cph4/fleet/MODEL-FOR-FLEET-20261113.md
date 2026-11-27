# 机队用模型：主控端点已开放（2026-11-13）

> 一句话：主控的 8 个模型现在**机队任意一台都能连**，端点 `http://100.75.133.10:11434`。
> 以前这个 url 写在配置里但服务只监听 127.0.0.1 —— 配置在、连不上，等于没有。

## 一、验证（在任意一台机子上跑这一条）

```bash
curl -s -m 8 http://100.75.133.10:11434/api/tags
```

返回 `{"models":[...]}` 就是通的；`connection refused` 说明主控服务没起或 tailnet 不通。

## 二、三种用法

1. **环境变量优先**（推荐，各机脚本不用改）：
   ```bash
   OLLAMA_URL=http://100.75.133.10:11434 python Tools/fleet/<你的工具>.py
   ```
2. **走统一通路**（自动按阶梯退：本机 → 大脑 → 主控）：
   ```python
   import local_model as lm
   out = lm.generate("……", cls="triage")
   ```
3. **直接调 API**（临时排查用）：
   ```bash
   curl -s http://100.75.133.10:11434/api/generate \
     -d '{"model":"qwen3.5:4b","prompt":"……","stream":false,"think":false}'
   ```

## 三、限制（先看清再依赖）

- **只在 tailnet 内可达**：这是私网 + 加密链路，等价于访问控制；公网连不上。
- **无应用层认证**：谁能进 tailnet 谁就能用。不要把端点写进任何对外文档或客户端。
- **常驻 10 分钟**（显式配置）：用完即卸，不长期占内存；连续调用不受影响。
- **模型档位**：4B（triage/摘要）、8B（评审/长文）、9B/14B（重活，按需）。
  4B 会把"机队"听成"航空公司"，所以**事实与数字一律由规则算，模型只负责措辞**。
- **主控内存 32G**：同时跑多个大模型会吃紧。批量任务请错峰，或等算力大脑入网。

## 四、回滚（如果不想开放）

```bash
launchctl bootout gui/$(id -u)/com.fluxgroup.ollamamodel
open -a Ollama        # 回到 App 托管，只监听 127.0.0.1
```

服务定义：`~/Library/LaunchAgents/com.fluxgroup.ollamamodel.plist`（不入库，属本机配置）。

## 五、为什么不用 Ollama.app

App 固定监听 `127.0.0.1`，`launchctl setenv OLLAMA_HOST` 传不进去（实测重启两次仍是 127.0.0.1）。
所以改用我们自己的 launchd 服务直接起 `ollama serve` 并显式绑 `0.0.0.0:11434`。
