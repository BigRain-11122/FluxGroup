# 线级体检 bigstream-mv · 2026-11-05 11:00

## 工段与证据目录
- mv-plan        owner=导演席      lane=-      证据 2/2 存在 · 文件 206 · 最新 34.9h
- mv-kf          owner=导演席·美术   lane=bm-c   证据 1/1 存在 · 文件 46 · 最新 63.3h
- mv-i2v         owner=导演席      lane=bm-c   证据 0/1 存在 · 文件 0 · 最新 —
- mv-cut         owner=剪辑席      lane=bm-a   证据 1/1 存在 · 文件 1019 · 最新 43.2h
- mv-gate        owner=质检席      lane=bm-a   证据 1/1 存在 · 文件 955 · 最新 176.2h
- mv-approve     owner=导演席（自决放行） lane=-      证据 1/1 存在 · 文件 55 · 最新 34.9h

## 判定
- 最近产出 34.9h 前（阈值 24.0h）→ STALE 超阈
- 工段超阈 5/6（线级最近值不代表最差工段）：mv-plan 34.9h、mv-kf 63.3h、mv-cut 43.2h、mv-gate 176.2h、mv-approve 34.9h
- 另有 1 个证据目录只在别的节点上（本机不据此判缺口）：D:/FluxGroup/media/mv-album-001-jay/clips-local-768

## 下一步（按缺口）
- mv-plan：产出已停 34.9h（阈值 24.0h）→ 补产出或正式收线（责任人=导演席）
- mv-kf：产出已停 63.3h（阈值 24.0h）→ 补产出或正式收线（责任人=导演席·美术）
- mv-cut：产出已停 43.2h（阈值 24.0h）→ 补产出或正式收线（责任人=剪辑席）
