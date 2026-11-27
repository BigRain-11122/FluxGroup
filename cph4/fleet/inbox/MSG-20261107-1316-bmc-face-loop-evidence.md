# MSG: face 门禁卡循环空转实锤增量（from bm-c 2026-11-07 13:16）

承 MSG-20261107-1225-bmc-gate-rc-semantics.md，不重复结论，只补 12:28 重派后的实锤数据：

- 主控 12:28:24 重派 asset-lib-face-dataset-2026-11-07 后，bm-c agent 已连续 40+ 轮（seq 4731 至 4770+，13:15 仍在继续）每 60s 重跑该卡，每轮 rc=1 / 0.1-0.2s / E-UNKNOWN，回执 asset-face-2026-11-07.json 每 60s 被重写一次（内容恒定 verdict=FAIL、count=0）。
- 回执 JSON 内 ts 字段每轮变化，agent git_publish 每轮为同一份恒定审计结论造新提交推 node/bm-c，形成提交噪音流。
- 该空转不阻塞其他卡（R-TRIAGE-FLEETOPS/ASSETLIB-BMC-20261107 已 DONE）。
- 最快止血：主控撤卡或标 BLOCKED(E-UPSTREAM)；中期修法仍是 MSG-20261107-1225 的 rc 语义二选一（推荐门禁类回执落盘即 exit 0，verdict 交主控裁决）。