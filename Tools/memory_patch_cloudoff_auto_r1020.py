# -*- coding: utf-8 -*-
"""L1 记忆补丁：把「自动化全本地」追加令并进既有 T0 条目（幂等）。"""
import io

OLD = "代理脑边界待 CEO 裁。"
NEW = ("代理脑边界待 CEO 裁。"
       "**2026-10-20 追加令「自动化任务全部走本地」已落地**：17 个会拉起云端 codely 会话的脚本在 Start-Process 前加统一闸门"
       "（开关=`cph4/fleet/CLOUD-OFF-LOCAL-ONLY-v1.md` 存在即拦·留痕 `media/logs/cloud-off-suppressed.log`），"
       "无人值守 LLM 判断面（L2 八班/各域巡逻席/各司迭代轮）暂停，本地确定性巡班照跑；解令=改名或删除该正典。")


def main():
    p = "CODELY.md"
    s = io.open(p, "r", encoding="utf-8", newline="").read()
    if "自动化任务全部走本地" in s:
        print("skip (already noted)")
        return
    if OLD not in s:
        raise SystemExit("anchor not found")
    s = s.replace(OLD, NEW, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("updated")


if __name__ == "__main__":
    main()