# 线级体检 bigstream-mv · 2026-11-09 02:49

## 工段与证据目录
- mv-plan        owner=导演席      lane=-      证据 2/2 存在 · 文件 443 · 最新 2.6h
- mv-kf          owner=导演席·美术   lane=bm-c   证据 1/1 存在 · 文件 47 · 最新 15.0h
- mv-i2v         owner=导演席      lane=bm-c   证据 0/1 存在 · 文件 0 · 最新 —
- mv-cut         owner=剪辑席      lane=bm-a   证据 1/1 存在 · 文件 1000 · 最新 0.0h
- mv-gate        owner=质检席      lane=bm-a   证据 1/1 存在 · 文件 955 · 最新 264.0h
- mv-approve     owner=导演席（自决放行） lane=-      证据 1/1 存在 · 文件 95 · 最新 16.7h

## 判定
- 最近产出 0.0h 前（阈值 24.0h）→ FRESH 在阈内
- 工段超阈 1/6（线级最近值不代表最差工段）：mv-gate 264.0h
- 另有 1 个证据目录只在别的节点上（本机不据此判缺口）：D:/FluxGroup/media/mv-album-001-jay/clips-local-768

## 下一步（按缺口）
- mv-gate：产出已停 264.0h（阈值 24.0h）→ 补产出或正式收线（责任人=质检席）
