# ===== 断言有已知缺陷·勿直接采信（2026-09-30）=====
# T1 断言：切片错位 + 标准差口径(总体n vs 样本n-1)——外审自测未通过，故本件判分无效。
# T2 判分：对'输入不足时抛异常'的合理实现过严；且 qwen3 思考模式会超时。
# 结论详见 docs/audits/LOCAL-CODING-VERDICT-20260930.md
# ==============================================
#!/usr/bin/env python3
# local_coding_bench.py -- 本地模型"能不能接手项目 coding"客观测试
# 原则：不看文风，只看【能否跑通】。三题全部机器判分。
# 判分实现：同进程 exec（不用 subprocess——本沙箱禁管道捕获）。
# 用法: python Tools/local_coding_bench.py [--model qwen3:8b]
import argparse, json, math, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLLAMA = "http://127.0.0.1:11434/api/generate"


def gen(prompt, model, timeout=900):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "options": {"temperature": 0, "num_ctx": 8192}}).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "ignore")).get("response", "")


def strip_code(txt):
    m = re.search(r"```(?:python)?\s*(.*?)```", txt, re.S)
    return (m.group(1) if m else txt).strip()


def run_block(code, check_src):
    """在同一进程 exec 选手代码 + 检查代码。返回 (ok, detail)。"""
    ns = {"__name__": "__bench__"}
    try:
        exec(compile(code, "<solution>", "exec"), ns)
    except Exception as e:
        return False, "solution raised: " + str(e)[:120]
    try:
        exec(compile(check_src, "<check>", "exec"), ns)
    except AssertionError as e:
        return False, "assert: " + str(e)[:150]
    except Exception as e:
        return False, type(e).__name__ + ": " + str(e)[:150]
    return True, "ok"


T1_PROMPT = """Write two Python functions. Output code only, no explanation.

def rolling_sharpe(returns, window):
    # Return a list the same length as returns. Element i is the annualised Sharpe of
    # returns[i-window+1 .. i], annualised by sqrt(252). Positions with fewer than
    # window values are None. Sharpe = mean / population_stdev(n) * sqrt(252).
    # If the stdev is 0, return 0.0 for that position.

def max_drawdown(equity):
    # Return the max drawdown as a negative number or 0.0.
    # Example: [1, 1.2, 0.9, 1.1] -> -0.25
"""

T1_CHECK = """
import math
R = rolling_sharpe([0.01,-0.02,0.03,0.01,-0.01,0.02], 3)
assert len(R) == 6, "length"
assert R[0] is None and R[1] is None, "warmup"
src = [0.01,-0.02,0.03,0.01,-0.01,0.02]
for idx in (2,3,4,5):
    seg = src[idx-2:idx+1]
    m = sum(seg)/3
    sd = math.sqrt(sum((x-m)**2 for x in seg)/3)
    exp = 0.0 if sd == 0 else m/sd*math.sqrt(252)
    assert abs(R[idx]-exp) < 1e-6, "sharpe at %d: got %r want %r" % (idx, R[idx], exp)
assert rolling_sharpe([0.0,0.0,0.0],2)[1] == 0.0, "zero_sd"
assert abs(max_drawdown([1,1.2,0.9,1.1]) - (-0.25)) < 1e-9, "mdd"
assert max_drawdown([1,2,3]) == 0.0, "mdd_up"
"""

T2_BUGGY = '''def sharpe_from_curve(equity):
    rets = []
    for i in range(1, len(equity)):
        if equity[i-1] > 0:
            rets.append(equity[i] / equity[i-1] - 1.0)
    n = len(rets)
    mean = sum(rets) / n
    var = sum((r - mean) ** 2 for r in rets) / n
    sd = var ** 0.5
    return mean / sd * (252 ** 0.5)
'''

T2_PROMPT = """This Python function computes an annualised Sharpe ratio from an equity curve.

```python
{code}
```

It has a real defect that produces a mathematically meaningless result for some inputs
(hint: think about a monotonically declining equity curve, and about very short inputs).
It does not raise an exception.

Answer in two parts:
1. One sentence naming the defect.
2. The corrected complete function inside a single python code block.
""".format(code=T2_BUGGY)

T2_CHECK = """
import math
v1 = sharpe_from_curve([100, 90, 80, 70, 60])
assert v1 is not None, "monotone_down returned None (want finite)"
assert isinstance(v1, float) and math.isfinite(v1), "monotone_down not finite"
v2 = sharpe_from_curve([100])
assert v2 is None or (isinstance(v2, float) and (v2 == 0.0 or math.isfinite(v2))), "len1"
v3 = sharpe_from_curve([100, 100, 100, 100])
assert v3 is None or (isinstance(v3, float) and (v3 == 0.0 or math.isfinite(v3))), "flat"
"""

T3_DOC = """# Prereg: LOWAMP-P1

## S0 identity
- batch id: T-2026-10-01-07
- dept: research
- budget: 40 min / 4 workers

## S1 mechanism
- [x] structural: index rebalancing friction
- family correlation gate: max|corr| = 0.42

## S3 methodology
- evidence_cutoff (forward lockbox): 2026-09-24
- cost basis: V2 (ADV20 three-tier slippage)
"""

T3_PROMPT = """Extract fields from the document below. Output ONLY one JSON object, no explanation,
no markdown fences.
Fields: batch_id, dept, cutoff, cost_basis, max_corr (number), mechanism (the ticked option)
Use null for anything not present.

Document:
{doc}
""".format(doc=T3_DOC)


def check_t3(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return False, "no JSON found"
    try:
        d = json.loads(m.group(0))
    except Exception as e:
        return False, "json parse: " + str(e)[:60]
    bad = []
    if d.get("batch_id") != "T-2026-10-01-07":
        bad.append("batch_id=%r" % d.get("batch_id"))
    if str(d.get("dept") or "").lower() not in ("research", "dept:research"):
        bad.append("dept=%r" % d.get("dept"))
    if str(d.get("cutoff") or "") != "2026-09-24":
        bad.append("cutoff=%r" % d.get("cutoff"))
    try:
        if abs(float(d.get("max_corr")) - 0.42) > 1e-9:
            bad.append("max_corr=%r" % d.get("max_corr"))
    except Exception:
        bad.append("max_corr=%r" % d.get("max_corr"))
    if "V2" not in str(d.get("cost_basis") or ""):
        bad.append("cost_basis=%r" % d.get("cost_basis"))
    if "structural" not in str(d.get("mechanism") or "").lower():
        bad.append("mechanism=%r" % d.get("mechanism"))
    return (not bad), ("all fields correct" if not bad else "wrong: " + ", ".join(bad))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3:8b")
    a = ap.parse_args()
    M = a.model
    print("=== local coding bench (model=%s) ===" % M)
    print("scoring: not style, only whether it runs\n")

    t0 = time.time()
    code = strip_code(gen(T1_PROMPT, M))
    ok1, d1 = run_block(code, T1_CHECK)
    print("[T1 pure function / executable]  %s   (%.0fs)" % ("PASS" if ok1 else "FAIL", time.time() - t0))
    if not ok1:
        print("     " + d1)

    t0 = time.time()
    raw2 = gen(T2_PROMPT, M)
    code2 = strip_code(raw2)
    ok2, d2 = run_block(code2, T2_CHECK)
    print("[T2 real bug fix / executable]   %s   (%.0fs)" % ("PASS" if ok2 else "FAIL", time.time() - t0))
    if not ok2:
        print("     " + d2)

    t0 = time.time()
    raw3 = gen(T3_PROMPT, M)
    ok3, d3 = check_t3(raw3)
    print("[T3 structured extract / check]  %s   (%.0fs)   %s" % ("PASS" if ok3 else "FAIL", time.time() - t0, d3))

    n = sum([ok1, ok2, ok3])
    print("\nscore %d/3" % n)
    if n == 3:
        print("verdict: can take routine coding work")
    elif n == 2:
        print("verdict: can take coding work with human review")
    else:
        print("verdict: judgement chores only, do not hand it coding")


if __name__ == "__main__":
    main()
