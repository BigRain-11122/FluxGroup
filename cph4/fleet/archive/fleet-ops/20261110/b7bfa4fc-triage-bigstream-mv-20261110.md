# 线级体检 bigstream-mv · 2026-11-10 21:25

## 工段与证据目录
- mv-plan        owner=导演席      lane=-      证据 2/2 存在 · 文件 412 · 最新 30.2h
- mv-kf          owner=导演席·美术   lane=bm-c   证据 1/1 存在 · 文件 47 · 最新 30.2h
- mv-i2v         owner=导演席      lane=bm-c   证据 0/1 存在 · 文件 0 · 最新 —
- mv-cut         owner=剪辑席      lane=bm-a   证据 1/1 存在 · 文件 776 · 最新 30.2h
- mv-gate        owner=质检席      lane=bm-a   证据 0/1 存在 · 文件 0 · 最新 —
- mv-approve     owner=导演席（自决放行） lane=-      证据 1/1 存在 · 文件 64 · 最新 71.0h

## 判定
- 最近产出 30.2h 前（阈值 24.0h）→ STALE 超阈
- 工段超阈 4/6（线级最近值不代表最差工段）：mv-plan 30.2h、mv-kf 30.2h、mv-cut 30.2h、mv-approve 71.0h
- 另有 2 个证据目录只在别的节点上（本机不据此判缺口）：D:/FluxGroup/media/mv-album-001-jay/clips-local-768、D:/FleetWorker/review

## 下一步（按缺口）
- mv-plan：产出已停 30.2h（阈值 24.0h）→ 补产出或正式收线（责任人=导演席）
- mv-kf：产出已停 30.2h（阈值 24.0h）→ 补产出或正式收线（责任人=导演席·美术）
- mv-cut：产出已停 30.2h（阈值 24.0h）→ 补产出或正式收线（责任人=剪辑席）
