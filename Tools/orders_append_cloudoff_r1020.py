# -*- coding: utf-8 -*-
"""orders 台账追加一行：T0 云道停用令落地（幂等）。"""
import io

ROW = (
    "| 2026-10-20 18:21（校时 18:21） | CEO 令（原话）「集团业务全部停止走云端，全部走本地了」→ **T0 云道停用·全面本地化** | "
    "**executed·口径落地**：权威件=`cph4/fleet/CLOUD-OFF-LOCAL-ONLY-v1.md`（废止 O-20261013-2245/O-20261016-2145/"
    "本地故障切云律/白名单免试/云端正式镜头主力五条）+落地台账=`cph4/fleet/CLOUD-OFF-LANDING-20261020.md`。"
    "**法条正身修法**=token-economy §10.1 六类白名单全冻（第 6 类产能不足单标废止）/resource-chain §一.0①+§二云行+§三云默认态+§9.1.2 必要闸①②废止（仅留 CEO 亲批）；"
    "**调度面**=DISPATCHER-CHARTER 加派单前云道闸（含云端模型名=拒发）+L2 脑改本地 35B+ROUND 白名单冻结+GAME-CLOUD-LANE-PLAN 整单废止转存档；"
    "**产线抬头注记**=MV 10 件/短剧 1/短视频 2/提示词 2/算力架构 1（逐句改口径：⑤视频、自动打磨引擎、正式镜头主力、SLA、云端生成为主等）；"
    "law-registry 增 10-20 一批。历史日志/判例/确认件/研究件**零改写**。扫描=改动前 fleet 113 文件 865 处；残留 182 文件 1295 处（多为史实与研究引证）；"
    "工具层无云端调用代码（云调用走交互 MCP）→ 停云靠派单闸+纪律。**未完成**=派单卡机械 lint/云端凭据清单/在飞云任务盘点/本地产能预算/Animate+LatentSync 装机/代理脑边界待 CEO 裁。 | "
    "executed（22 件改口径+1 件新增+1 工具；未提交 git） [via bm-a 控制台] |"
)


def main() -> None:
    p = "docs/orders.md"
    s = io.open(p, "r", encoding="utf-8", newline="").read()
    if "T0 云道停用·全面本地化" in s:
        print("skip (already logged)")
        return
    nl = "\r\n" if "\r\n" in s else "\n"
    if not s.endswith(nl):
        s += nl
    s += ROW + nl
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("orders row appended")


if __name__ == "__main__":
    main()