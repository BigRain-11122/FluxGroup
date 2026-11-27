# -*- coding: utf-8 -*-
"""L1 记忆补丁：云道停用令（memory 工具 project-scope EEXIST 在册故障 → 外置 UTF-8 字节补丁正法）。"""
import io

OLD = "云算力默认态=并行全量调用——CEO 指令=唯一变更通道，AI 禁自行设限"
NEW = ("**原「云算力默认态=并行全量调用」已废止（2026-10-20 T0 云道停用令）**"
       "——业务生产一律本地，例外仅 CEO 亲批（正典=cph4/fleet/CLOUD-OFF-LOCAL-ONLY-v1.md）")

ENTRY = (
    "- [2026-10-20 18:21] T0 云道停用令（CEO「集团业务全部停止走云端，全部走本地」）："
    "业务生成/推理一律本地机队；云端 API 停作生产路径，例外仅 CEO 亲批+留痕；本地满载=排队+报障，不切云。"
    "权威件=cph4/fleet/CLOUD-OFF-LOCAL-ONLY-v1.md；落地台账=cph4/fleet/CLOUD-OFF-LANDING-20261020.md"
    "（22 件改口径·日志判例研究零改写）。未完成=云端凭据清单/派单卡机械 lint/在飞云任务盘点/"
    "本地产能预算/Animate+LatentSync 装机/代理脑边界待 CEO 裁。"
)


def main() -> None:
    p = "CODELY.md"
    s = io.open(p, "r", encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    changed = []
    if OLD in s:
        s = s.replace(OLD, NEW, 1)
        changed.append("old-clause-updated")
    if "[2026-10-20 18:21]" not in s:
        anchor = "### Reference"
        if anchor not in s:
            raise SystemExit("anchor not found")
        s = s.replace(anchor, ENTRY + nl + anchor, 1)
        changed.append("entry-added")
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print(",".join(changed) if changed else "no change")


if __name__ == "__main__":
    main()