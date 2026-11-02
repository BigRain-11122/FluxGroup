# 线级体检 bigstream-mv · 2026-11-02 10:39

## 工段与证据目录
- mv-plan        owner=导演席      lane=-      证据 2/2 存在 · 文件 189 · 最新 44.4h
- mv-kf          owner=导演席·美术   lane=bm-c   证据 1/1 存在 · 文件 45 · 最新 0.2h
- mv-i2v         owner=导演席      lane=bm-c   证据 0/1 存在 · 文件 0 · 最新 —
- mv-cut         owner=剪辑席      lane=bm-a   证据 1/1 存在 · 文件 1014 · 最新 44.4h
- mv-gate        owner=质检席      lane=bm-a   证据 1/1 存在 · 文件 955 · 最新 103.8h
- mv-approve     owner=导演席（自决放行） lane=-      证据 1/1 存在 · 文件 46 · 最新 44.4h

## 判定
- 最近产出 0.2h 前（阈值 24.0h）→ FRESH 在阈内
- 工段超阈 4/6（线级最近值不代表最差工段）：mv-plan 44.4h、mv-cut 44.4h、mv-gate 103.8h、mv-approve 44.4h
- 另有 1 个证据目录只在别的节点上（本机不据此判缺口）：D:/FluxGroup/media/mv-album-001-jay/clips-local-768

## 下一步（按缺口）
- mv-plan：产出已停 44.4h（阈值 24.0h）→ 补产出或正式收线（责任人=导演席）
- mv-cut：产出已停 44.4h（阈值 24.0h）→ 补产出或正式收线（责任人=剪辑席）
- mv-gate：产出已停 103.8h（阈值 24.0h）→ 补产出或正式收线（责任人=质检席）
