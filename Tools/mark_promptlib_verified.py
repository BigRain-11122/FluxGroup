# -*- coding: utf-8 -*-
"""Mark the three tested entries per test #1/#2, and append test #2 to the log."""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = os.path.join(ROOT, "cph4", "fleet", "prompt-library", "seeds")
VERDICTS = {
    "structure.h3-integrated-multimodal": (True, "2026-11-05 local H3 480p test#1: accepted, face locked"),
    "camera.slow-push-in": (True, "2026-11-05 local H3 test#2: push-in clearly readable at 90 words"),
    "performance.micro-expression": (False, "2026-11-05 local H3 test#1-2: three-beat acting NOT readable in 5s/480p"),
}

for fn in os.listdir(SEEDS):
    if not fn.endswith(".jsonl"):
        continue
    p = os.path.join(SEEDS, fn)
    out = []
    changed = 0
    for line in io.open(p, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        e = json.loads(line)
        if e.get("id") in VERDICTS:
            ok, note = VERDICTS[e["id"]]
            e["verified"] = ok
            e["verified_on"] = note
            changed += 1
        out.append(json.dumps(e, ensure_ascii=False))
    io.open(p, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("%s: %d entries updated" % (fn, changed))

log = os.path.join(ROOT, "cph4", "fleet", "prompt-library", "tests", "TEST-20261105.md")
add = """
## 测试 2 · 同 KF，压到 90 词重跑（本地 H3 480p）

- **改动**：196 词 → **65 词**；11 条 `no xxx` 负向清单全删，改正向约束；三段表演压成一句。
- **产出**：`tests/out/p2_perf_short.mp4`（864×480 / 124 帧 / ~5s）
- **对照**：`tests/out/p2-compare.png`（0.2s / 2.0s / 4.6s）

| 检查项 | 测试1（196词+负向） | 测试2（65词+正向） | 判 |
|---|---|---|---|
| 人脸一致 | 一致 | 一致 | 均 PASS |
| 推轨强度 | 弱 | **明显**（末帧已近特写） | 测试2 胜 |
| 微表情三层可读 | 读不出 | 略好（眼抬→落），仍读不出三层 | **仍 FAIL** |
| 崩坏 | 无 | 无 | 均 PASS |

### 结论（已写回词条 verified 字段）

- `structure.h3-integrated-multimodal` → **verified=true**（本地接受该结构，锁脸成立）
- `camera.slow-push-in` → **verified=true**（90 词版本推轨明确可读）
- `performance.micro-expression` → **verified=false**：本地 H3 在 5 秒/480p 下演不出"渴望→抑制→泄露"三层。
  下一步试法：①时长拉到 8-10s；②改成 **ECU 只拍眼与唇**（不给整脸）；③三层压成一动作（"她眨眼时下唇轻颤"）。

### 由此新增的本地写法规矩

1. **≤90 词**（超出即稀释，第一条指令吃掉全部注意力）。
2. **禁 `no xxx`**：本地 lint 判负向为噪声，改用正向描述（same face / one person / hands still）。
3. 表演想读出层次，**必须给特写 + 至少 8 秒**；5 秒内只能承载一个动作。
"""
with io.open(log, "a", encoding="utf-8") as fh:
    fh.write(add)
print("appended test #2 to TEST-20261105.md")