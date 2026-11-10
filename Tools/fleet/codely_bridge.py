#!/usr/bin/env python3
"""Explicit bridge between a dispatch card and the local Tuanjie Cowork CLI.

Authority: cph4/fleet/CODELY-BRIDGE-DECISION-v1.md
Order anchor: CEO 2026-11-09 "self-decide and proceed".

Rules enforced here:
  1. Explicit invocation only. No scheduler, no master_pulse hook, no lanes/ writes.
  2. Single direction. Codely never spawns the control plane back.
  3. DONE is decided by on-disk facts, never by exit code or model text alone.
  4. Read-only by default. Writing files requires an explicit card mode.
  5. No git operations, no memory edits, no interactive windows.
  6. COMPLIANCE DEFAULT-DENY. The CLI runs on an employer-provided employee seat.
     Every card must declare an authorization reference, data classification,
     purpose and seat-owner confirmation, plus an escalation reason proving the
     cheaper layers were tried first, or the bridge blocks without touching the CLI.
  7. ROUTING PRECEDENCE (CEO order 2026-11-09): L0 hy4 > L1 deterministic >
     L2 Mac local model > L3 company Codely. The single machine-readable source is
     cph4/fleet/LOCAL-MODEL-POLICY.json -> routing. This file only reads it.

Usage:
  python3 Tools/fleet/codely_bridge.py --card cph4/fleet/CODELY-BRIDGE-DEMO-CARD-v1.json
  python3 Tools/fleet/codely_bridge.py --card <card.json> --emit-only
  python3 Tools/fleet/codely_bridge.py --card <card.json> --dry-run
  python3 Tools/fleet/codely_bridge.py --route-check classification
  python3 Tools/fleet/codely_bridge.py --local-run "<low-level prompt>"
  python3 Tools/fleet/codely_bridge.py --compliance-check
  python3 Tools/fleet/codely_bridge.py --self-test
  python3 Tools/fleet/codely_bridge.py --status

Exit codes: 0 DONE, 1 FAIL, 2 DEFER, 3 CARD-DEFECT, 4 TIMEOUT, 5 BLOCKED.
"""

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECEIPTS = ROOT / "cph4/fleet/queue-receipts"
STATE = ROOT / "cph4/fleet/state/codely-bridge"
LOGS = STATE / "logs"
MANUAL = STATE / "manual"
LOCK = STATE / "bridge.lock"
COMPLIANCE_FACE = ROOT / "cph4/fleet/CODELY-BRIDGE-COMPLIANCE-v1.json"
ROUTING_POLICY = ROOT / "cph4/fleet/LOCAL-MODEL-POLICY.json"
MAX_LIVE = 2
CLI_CANDIDATES = (
    Path.home() / "Library/Application Support/Tuanjie Cowork/bin/codely",
    Path("/Applications/Tuanjie Cowork.app/Contents/MacOS/app/resource/core/bin/darwin-arm64/codely"),
)


class CardDefect(Exception):
    """Raised when a card cannot be safely executed."""


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def resolve_cli(card):
    raw = card.get("cli_path") or os.environ.get("CODELY_CLI")
    if raw:
        p = Path(raw)
        if not p.is_file():
            raise CardDefect("cli_path is not a file: %s" % raw)
        return str(p)
    for p in CLI_CANDIDATES:
        if p.is_file():
            return str(p)
    raise CardDefect("Codely CLI not found; set CODELY_CLI or cli_path in the card")


def deliverable_path(card):
    raw = card["deliverable"]
    p = Path(raw) if os.path.isabs(raw) else ROOT / raw
    p = p.resolve()
    if ROOT not in p.parents:
        raise CardDefect("deliverable escapes the workspace")
    return p


def validate_card(card):
    if not isinstance(card, dict):
        raise CardDefect("card must be a JSON object")
    for key in ("card_id", "prompt", "deliverable"):
        if not card.get(key):
            raise CardDefect("missing required field: %s" % key)
    mode = card.get("mode", "ask")
    if mode not in ("ask", "plan", "default"):
        raise CardDefect("unsupported mode: %s" % mode)
    approval = card.get("approval", "default" if mode == "ask" else "auto_edit")
    if approval not in ("default", "auto_edit", "yolo"):
        raise CardDefect("unsupported approval: %s" % approval)
    dmode = card.get("deliverable_mode", "capture")
    if dmode not in ("capture", "file"):
        raise CardDefect("unsupported deliverable_mode: %s" % dmode)
    if dmode == "capture" and "expect_json" not in card:
        raise CardDefect("capture mode requires expect_json")
    deliverable_path(card)
    timeout = card.get("timeout_s", 300)
    if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 3600:
        raise CardDefect("timeout_s must be within (0, 3600]")
    return card


def live_codely_count():
    """Count live Codely processes; pgrep first, ps fallback, fail-open.

    /bin/ps is blocked by the macOS sandbox in some hosts, so relying on it
    alone silently reports zero and turns the concurrency cap into a fake green.
    Returns -1 when no probe works, which the caller reports as UNKNOWN.
    """
    probes = (["/usr/bin/pgrep", "-fl", "codely"], ["/bin/ps", "-Ao", "command="])
    for probe in probes:
        try:
            res = subprocess.run(probe, capture_output=True, text=True, timeout=8)
        except Exception:
            continue
        if probe[0].endswith("pgrep"):
            if res.returncode not in (0, 1) or res.stderr.strip().startswith("operation not permitted"):
                continue
        elif res.returncode != 0 or not res.stdout.strip():
            continue
        skip = ("codely_bridge.py", "pgrep ", "grep codely", "/bin/ps -ao")
        return sum(
            1
            for line in res.stdout.splitlines()
            if "codely" in line.lower() and not any(s in line.lower() for s in skip)
        )
    return -1


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, TypeError):
        return False


def acquire_lock(card_id, timeout_s):
    STATE.mkdir(parents=True, exist_ok=True)
    stale_after = timeout_s + 180
    if LOCK.exists():
        try:
            data = json.loads(LOCK.read_text(encoding="utf-8"))
            age = time.time() - float(data.get("ts", 0))
            if age < stale_after and pid_alive(int(data.get("pid", 0))):
                return False, "lock held by pid %s age %.0fs" % (data.get("pid"), age)
        except Exception:
            pass
        LOCK.unlink(missing_ok=True)
    tmp = STATE / ("bridge.lock.%d.tmp" % os.getpid())
    tmp.write_text(
        json.dumps({"pid": os.getpid(), "ts": time.time(), "card": card_id}),
        encoding="utf-8",
    )
    try:
        os.link(tmp, LOCK)
    except FileExistsError:
        return False, "lock race lost"
    finally:
        tmp.unlink(missing_ok=True)
    return True, ""


def release_lock():
    try:
        if not LOCK.exists():
            return
        data = json.loads(LOCK.read_text(encoding="utf-8"))
        if int(data.get("pid", -1)) == os.getpid():
            LOCK.unlink(missing_ok=True)
    except Exception:
        pass


def load_routing():
    if not ROUTING_POLICY.is_file():
        return {}
    try:
        return json.loads(ROUTING_POLICY.read_text(encoding="utf-8")).get("routing", {})
    except (ValueError, OSError):
        return {}


def route_for(task_class, routing=None):
    routing = routing if routing is not None else load_routing()
    layers = routing.get("layers", {})
    for layer in routing.get("precedence", []):
        if task_class in layers.get(layer, {}).get("task_classes", []):
            return layer, layers[layer]
    return "L0_HY4", layers.get("L0_HY4", {})


def route_check(task_class):
    routing = load_routing()
    if not routing:
        print("ROUTING-POLICY-MISSING: %s" % ROUTING_POLICY)
        return 3
    layer, spec = route_for(task_class, routing)
    print("task_class : %s" % task_class)
    print("route      : %s | %s" % (layer, spec.get("name", "")))
    print("cost       : %s" % spec.get("cost", ""))
    print("action     : %s" % spec.get("action", ""))
    if layer == "L3_CODELY":
        print("requires   : %s" % ", ".join(spec.get("requires", [])))
        print("rule       : %s" % routing.get("escalation_rule", ""))
    print("precedence : %s" % " > ".join(routing.get("precedence", [])))
    return 0


def local_run(prompt):
    """L2: run a low-level control task on the Mac local model."""
    routing = load_routing()
    spec = (routing.get("layers") or {}).get("L2_LOCAL_LLM", {})
    endpoint = spec.get("endpoint", "http://127.0.0.1:11434/api/generate")
    try:
        policy = json.loads(ROUTING_POLICY.read_text(encoding="utf-8"))
        model = policy["duties"]["resident"]["model"]
    except (ValueError, OSError, KeyError):
        model = "qwen3.5:4b-mlx"
    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "format": "json",
        "options": {"num_ctx": 4096, "temperature": 0},
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print("LOCAL-DOWN: %s" % exc)
        print("fallback  : queue locally, never promote to L3 (routing policy)")
        return 1
    ev, ec = data.get("eval_duration", 0), data.get("eval_count", 0)
    print("L2_LOCAL_LLM | model=%s" % model)
    print("response : %s" % str(data.get("response", ""))[:500])
    print("tok_s    : %.1f" % (ec / (ev / 1e9) if ev else 0))
    print("wall_s   : %.1f" % (time.time() - started))
    try:
        json.loads(data.get("response", ""))
        print("json     : valid")
        return 0
    except ValueError:
        print("json     : INVALID")
        return 1


PLACEHOLDER_REFS = ("PENDING", "TBD", "TODO", "DEMO", "NONE", "N/A")


def compliance_gate(card):
    """Default-deny gate for an employer-provided employee seat.

    A card is executable only when it carries a real authorization reference,
    a data classification, an employer-business purpose and seat-owner consent.
    """
    decl = card.get("compliance")
    if not isinstance(decl, dict):
        return False, "missing compliance declaration", {}
    ref = str(decl.get("authorization_ref") or "").strip()
    if not ref or any(p in ref.upper() for p in PLACEHOLDER_REFS):
        return False, "authorization_ref missing or placeholder", decl
    cls = decl.get("data_classification")
    if cls not in ("public", "internal", "confidential"):
        return False, "invalid data_classification", decl
    if cls == "confidential":
        return False, "confidential data must not pass through the seat", decl
    purpose = decl.get("purpose")
    if purpose not in ("company_business", "ceo_authorized"):
        return False, "purpose must be company_business or ceo_authorized", decl
    if purpose == "ceo_authorized" and not ref.startswith("CEO-"):
        return False, "ceo_authorized needs a CEO order id in authorization_ref", decl
    if decl.get("seat_owner_confirmed") is not True:
        return False, "seat_owner_confirmed must be true", decl
    if cls == "internal" and decl.get("model_target") == "cloud" and decl.get("cloud_export_approved") is not True:
        return False, "internal data on a cloud model needs a signed DPA", decl
    if not str(card.get("escalation_reason") or "").strip():
        return False, "escalation_reason required: L0/L1/L2 must be tried first", decl
    if card.get("l1_l2_exhausted") is not True:
        return False, "l1_l2_exhausted must be true before using the company seat", decl
    return True, "compliance gate passed", decl


def emit_manual_card(card):
    """Green lane: produce a human-in-the-loop card without touching the CLI."""
    MANUAL.mkdir(parents=True, exist_ok=True)
    out = MANUAL / ("%s.md" % card["card_id"])
    lines = [
        "# Manual execution card (human in the loop)",
        "",
        "- card_id: %s" % card["card_id"],
        "- generated: %s" % now_iso(),
        "- generator: Tools/fleet/codely_bridge.py --emit-only",
        "- NO CLI was invoked. NO enterprise seat was used. NO data left this machine.",
        "",
        "## Before you paste anything",
        "",
        "1. Confirm this task is within your employer's approved use of the tool.",
        "2. Confirm the prompt below contains no confidential or third-party data.",
        "3. Open YOUR OWN Tuanjie Cowork interactive session as the seat owner.",
        "4. Paste the prompt, review the answer, save it to the deliverable path.",
        "5. Never paste access tokens, refresh tokens or credentials into a prompt.",
        "",
        "## Deliverable path",
        "",
        "    %s" % card["deliverable"],
        "",
        "## Prompt",
        "",
        "```text",
        card["prompt"],
        "```",
        "",
        "## Compliance status",
        "",
        "Face list: cph4/fleet/CODELY-BRIDGE-COMPLIANCE-v1.json (green lane).",
        "Unresolved items: python3 Tools/fleet/codely_bridge.py --compliance-check",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def compliance_check():
    if not COMPLIANCE_FACE.is_file():
        print("COMPLIANCE-FACE-MISSING: %s" % COMPLIANCE_FACE)
        return 3
    data = json.loads(COMPLIANCE_FACE.read_text(encoding="utf-8"))
    items = data.get("items", [])
    settled = ("RESOLVED", "VERIFIED-SAFE")
    pending = [i for i in items if i.get("status") not in settled]
    print("verdict   : %s" % data.get("verdict"))
    print("items     : %d, undecided/incident/conflict: %d" % (len(items), len(pending)))
    decision = data.get("ceo_decision_20261109") or {}
    if decision:
        print("ceo order : %s | L0-L2 open, L3 conditional" % decision.get("order_id"))
        print("still gate: %s (L3 only)" % ", ".join(decision.get("still_open", [])))
    for item in pending:
        print("  %s [%-16s] %s -> owner=%s" % (
            item["id"], item["status"], item["domain"], item["owner"]
        ))
    print("green lane: --emit-only (no CLI invocation)")
    return 0


def build_cmd(card, cli):
    # 2026-11-10：云卡 prompt 超预算就头尾保留（token_guard，tiktoken 计数）。
    # 只裁中间、留头尾，避免把"要求"和"验收"裁掉；省下的 token 记 token-guard.jsonl。
    try:
        import token_guard as _tg
        card = dict(card)
        card["prompt"], _saved = _tg.guard(
            card.get("prompt") or "", int(card.get("token_budget") or _tg.DEFAULT_BUDGET))
    except Exception:
        pass
    mode = card.get("mode", "ask")
    approval = card.get("approval", "default" if mode == "ask" else "auto_edit")
    cmd = [
        cli,
        "-p", card["prompt"],
        "--output-format", "json",
        "--collaboration-mode", mode,
        "--approval-mode", approval,
        "--path-policy", "strict",
        "--no-auto-edit-memory",
        "--disable-next-speaker-check",
    ]
    optional = (
        ("skills", "--skills"),
        ("mcp_allowlist", "--allowed-mcp-server-names"),
        ("exclude_tools", "--exclude-tools"),
        ("model", "--model"),
        ("agent", "--agent"),
    )
    for key, flag in optional:
        val = card.get(key)
        if not val:
            continue
        cmd += [flag, ",".join(str(v) for v in val) if isinstance(val, list) else str(val)]
    return cmd


def parse_payload(stdout):
    decoder = json.JSONDecoder()
    for idx, ch in enumerate(stdout):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(stdout[idx:])
        except ValueError:
            continue
        if isinstance(obj, dict) and ("response" in obj or "stats" in obj):
            return obj
    return None


def strip_fence(text):
    lines = text.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


LEN_SUFFIX = "__len__"


def assert_equal(card, obj):
    expected = card.get("assert_equal") or {}
    if not isinstance(obj, dict):
        if expected:
            return False, "assert_equal needs a JSON object"
        return True, "no assertions"
    for key, want in expected.items():
        if key.endswith(LEN_SUFFIX):
            base = key[: -len(LEN_SUFFIX)]
            val = obj.get(base)
            if val is None:
                return False, "assert %s: field %s is missing" % (key, base)
            try:
                actual = len(val)
            except TypeError:
                return False, "assert %s: field %s is not sized" % (key, base)
        else:
            actual = obj.get(key)
        if actual != want:
            return False, "assert %s: expected %r got %r" % (key, want, actual)
    return True, "assertions passed"


def verify(card, payload, start_ts):
    """Return (ok, detail, evidence). DONE requires fresh bytes on disk."""
    evidence = {"deliverable": card["deliverable"]}
    path = deliverable_path(card)
    dmode = card.get("deliverable_mode", "capture")
    text_obj = None

    if dmode == "capture":
        response = (payload or {}).get("response")
        if not isinstance(response, str) or not response.strip():
            return False, "empty model response", evidence
        text = strip_fence(response)
        if card.get("expect_json"):
            try:
                text_obj = json.loads(text)
            except ValueError:
                return False, "response is not valid JSON", evidence
        else:
            text_obj = {"response": text}
        ok, detail = assert_equal(card, text_obj)
        if not ok:
            return False, detail, evidence
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(text_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    if not path.is_file():
        return False, "deliverable missing on disk", evidence
    stat = path.stat()
    if stat.st_size <= 0:
        return False, "deliverable is empty", evidence
    if stat.st_mtime < start_ts - 2:
        return False, "deliverable is stale (mtime predates this run)", evidence
    raw = path.read_bytes()
    if path.suffix.lower() == ".json":
        try:
            on_disk = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return False, "deliverable is not valid JSON", evidence
        ok, detail = assert_equal(card, on_disk)
        if not ok:
            return False, "on-disk " + detail, evidence

    evidence.update(
        {
            "bytes": stat.st_size,
            "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "oracle": "exists + size>0 + fresh mtime + json parse + assert_equal",
        }
    )
    return True, "disk facts verified", evidence


def token_stats(payload):
    models = ((payload or {}).get("stats") or {}).get("models") or {}
    prompt = sum(int((m.get("tokens") or {}).get("prompt", 0)) for m in models.values())
    candidates = sum(
        int((m.get("tokens") or {}).get("candidates", 0)) for m in models.values()
    )
    return {"prompt": prompt, "candidates": candidates, "models": sorted(models)}


def write_receipt(card, outcome, detail, evidence, meta, suffix=""):
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    receipt = {
        "id": card["card_id"],
        "node": "bm-m",
        "rc": meta.get("rc"),
        "seconds": meta.get("seconds"),
        "cmd": meta.get("cmd_redacted"),
        "ok_rc": [0],
        "outcome": outcome,
        "error_class": None if outcome == "OK" else detail,
        "deliverable": card["deliverable"],
        "deliverable_exists": bool(evidence.get("bytes")),
        "ts": now_iso(),
        "stdout_tail": meta.get("stdout", "")[-300:],
        "stderr_tail": meta.get("stderr", "")[-300:],
        "oracle": detail,
        "evidence": evidence,
        "tokens": meta.get("tokens", {}),
        "mcp_errors": meta.get("mcp_errors", 0),
        "live_probe": meta.get("live_probe"),
        "compliance_verdict": meta.get("compliance_verdict"),
        "mode": card.get("mode", "ask"),
        "deliverable_mode": card.get("deliverable_mode", "capture"),
        "source": "Tools/fleet/codely_bridge.py",
        "provenance": "CEO order 2026-11-09 self-decide; explicit invocation only",
    }
    out = RECEIPTS / ("%s%s-bm-m.json" % (card["card_id"], suffix))
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


def run_card(card, dry_run=False, emit_only=False):
    if emit_only:
        out = emit_manual_card(card)
        print("EMITTED | no CLI invoked, no enterprise seat used")
        print("manual card: %s" % out.relative_to(ROOT))
        return 0

    allowed, reason, decl = compliance_gate(card)
    verdict = {"allowed": allowed, "reason": reason, "declaration": decl}
    if not allowed:
        write_receipt(
            card, "BLOCKED", reason, {},
            {
                "rc": None, "seconds": 0, "cmd_redacted": "<not invoked>",
                "stdout": "", "stderr": "", "tokens": {}, "mcp_errors": 0,
                "live_probe": None, "compliance_verdict": verdict,
            },
            suffix="-BLOCKED",
        )
        print("BLOCKED | %s" % reason)
        print("no CLI invoked; face list: cph4/fleet/CODELY-BRIDGE-COMPLIANCE-v1.json")
        return 5

    cli = resolve_cli(card)
    cmd = build_cmd(card, cli)
    redacted = cli + " -p <prompt> " + " ".join(cmd[3:])
    if dry_run:
        print("CLI       : %s" % cli)
        print("CMD       : %s" % redacted[:400])
        print("CWD       : %s" % card.get("cwd", ROOT))
        print("DELIVER   : %s" % card["deliverable"])
        print("MODE      : %s / %s" % (card.get("mode", "ask"), card.get("deliverable_mode", "capture")))
        print("ORACLE    : exists + size>0 + fresh mtime + json parse + assert_equal")
        print("COMPLY    : %s" % reason)
        print("LIVE      : %d (cap %d)" % (live_codely_count(), MAX_LIVE))
        return 0

    live = live_codely_count()
    if live >= MAX_LIVE:
        print("DEFER: %d live Codely sessions, cap is %d" % (live, MAX_LIVE))
        return 2
    if live < 0:
        print("WARN: live-session probe unavailable; fail-open, recorded in receipt")

    timeout_s = card.get("timeout_s", 300)
    got, why = acquire_lock(card["card_id"], timeout_s)
    if not got:
        print("DEFER: %s" % why)
        return 2

    LOGS.mkdir(parents=True, exist_ok=True)
    started = time.time()
    stdout = stderr = ""
    rc = None
    timed_out = False
    try:
        env = os.environ.copy()
        env.setdefault("CI", "1")
        proc = subprocess.Popen(
            cmd,
            cwd=card.get("cwd", str(ROOT)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
            env=env,
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            stdout, stderr = proc.communicate()
            timed_out = True
        rc = proc.returncode
    finally:
        release_lock()
        (LOGS / ("%s.out.txt" % card["card_id"])).write_text(stdout or "", encoding="utf-8")
        (LOGS / ("%s.err.txt" % card["card_id"])).write_text(stderr or "", encoding="utf-8")

    payload = parse_payload(stdout or "")
    ok, detail, evidence = verify(card, payload, started)
    if timed_out:
        ok, detail = False, "timeout after %ss (process group killed)" % timeout_s
    outcome = "OK" if ok else "FAIL"
    mcp_errors = sum(
        1 for line in (stderr or "").splitlines() if "MCP server" in line or "Error connecting" in line
    )
    meta = {
        "rc": rc,
        "seconds": round(time.time() - started, 1),
        "cmd_redacted": redacted[:400],
        "stdout": stdout or "",
        "stderr": stderr or "",
        "tokens": token_stats(payload),
        "mcp_errors": mcp_errors,
        "live_probe": live,
        "compliance_verdict": verdict,
    }
    receipt_path = write_receipt(card, outcome, detail, evidence, meta)
    print("%s | %s" % (outcome, detail))
    print("deliverable: %s" % card["deliverable"])
    print("receipt    : %s" % receipt_path.relative_to(ROOT))
    print("tokens     : %s" % json.dumps(meta["tokens"]))
    if mcp_errors:
        print("note       : %d MCP connection warning(s), not treated as failure" % mcp_errors)
    if timed_out:
        return 4
    return 0 if ok else 1


def self_test():
    """Prove the oracle rejects bad results; no cloud call is made."""
    results = []
    tmp = STATE / "selftest"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)

    def check(name, condition):
        results.append((name, bool(condition)))

    try:
        base = {
            "card_id": "ST",
            "prompt": "stub",
            "deliverable": str(tmp / "positive.json"),
            "deliverable_mode": "capture",
            "expect_json": True,
            "assert_equal": {"ok": True},
        }
        good = {"response": '{"ok": true}', "stats": {"models": {}}}
        ok, _, _ = verify(base, good, time.time() - 1)
        check("positive: capture + assert passes", ok)

        empty = dict(base, deliverable=str(tmp / "empty.json"))
        ok, _, _ = verify(empty, {"response": ""}, time.time() - 1)
        check("negative: empty response rejected", not ok)

        bad_json = dict(base, deliverable=str(tmp / "badjson.json"))
        ok, _, _ = verify(bad_json, {"response": "not json"}, time.time() - 1)
        check("negative: invalid JSON rejected", not ok)

        wrong = dict(base, deliverable=str(tmp / "wrong.json"), assert_equal={"ok": False})
        ok, _, _ = verify(wrong, good, time.time() - 1)
        check("negative: wrong answer rejected", not ok)

        len_ok = dict(
            base,
            deliverable=str(tmp / "len-ok.json"),
            assert_equal={"items__len__": 2, "label": "x"},
        )
        ok, _, _ = verify(
            len_ok, {"response": '{"items": [1, 2], "label": "x"}'}, time.time() - 1
        )
        check("positive: __len__ suffix resolves the right field", ok)

        len_bad = dict(
            base,
            deliverable=str(tmp / "len-bad.json"),
            assert_equal={"items__len__": 3},
        )
        ok, _, _ = verify(len_bad, {"response": '{"items": [1, 2]}'}, time.time() - 1)
        check("negative: wrong __len__ rejected", not ok)

        len_missing = dict(
            base,
            deliverable=str(tmp / "len-missing.json"),
            assert_equal={"items__len__": 1},
        )
        ok, _, _ = verify(len_missing, {"response": '{"other": 1}'}, time.time() - 1)
        check("negative: missing __len__ field rejected", not ok)

        missing = dict(
            base,
            deliverable=str(tmp / "missing.json"),
            deliverable_mode="file",
        )
        ok, _, _ = verify(missing, good, time.time() - 1)
        check("negative: missing on-disk artifact rejected", not ok)

        stale = dict(
            base,
            deliverable=str(tmp / "stale.json"),
            deliverable_mode="file",
        )
        p = Path(stale["deliverable"])
        p.write_text('{"ok": true}', encoding="utf-8")
        ok, _, _ = verify(stale, good, time.time() + 3600)
        check("negative: stale artifact rejected", not ok)

        try:
            validate_card({})
            check("negative: card defect caught", False)
        except CardDefect:
            check("negative: card defect caught", True)

        try:
            validate_card(dict(base, deliverable="/etc/passwd"))
            check("negative: path traversal rejected", False)
        except CardDefect:
            check("negative: path traversal rejected", True)

        good_decl = {
            "authorization_ref": "IT-2026-0001",
            "data_classification": "public",
            "purpose": "company_business",
            "model_target": "cloud",
            "seat_owner_confirmed": True,
        }
        good_card = {
            "compliance": good_decl,
            "escalation_reason": "requires Unity VFS tooling, unavailable locally",
            "l1_l2_exhausted": True,
        }
        ok, _, _ = compliance_gate(good_card)
        check("compliance: fully declared card with escalation allowed", ok)
        ok, _, _ = compliance_gate({})
        check("compliance: missing declaration blocked", not ok)
        ok, _, _ = compliance_gate(
            dict(good_card, compliance=dict(good_decl, authorization_ref="PENDING-IT"))
        )
        check("compliance: placeholder authorization blocked", not ok)
        ok, _, _ = compliance_gate(
            dict(good_card, compliance=dict(good_decl, purpose="personal_group"))
        )
        check("compliance: undeclared purpose blocked", not ok)
        ok, _, _ = compliance_gate(
            dict(good_card, compliance=dict(good_decl, data_classification="confidential"))
        )
        check("compliance: confidential data blocked", not ok)
        ok, _, _ = compliance_gate(
            dict(good_card, compliance=dict(good_decl, seat_owner_confirmed=False))
        )
        check("compliance: unconfirmed seat blocked", not ok)
        ok, _, _ = compliance_gate(
            dict(good_card, compliance=dict(good_decl, data_classification="internal"))
        )
        check("compliance: internal data on cloud needs DPA", not ok)
        ok, _, _ = compliance_gate(
            dict(good_card, compliance=dict(
                good_decl, data_classification="internal", cloud_export_approved=True
            ))
        )
        check("compliance: internal plus cloud with DPA allowed", ok)
        ok, _, _ = compliance_gate(dict(good_card, escalation_reason=""))
        check("routing: missing escalation reason blocked", not ok)
        ok, _, _ = compliance_gate(dict(good_card, l1_l2_exhausted=False))
        check("routing: cheaper layers not exhausted blocked", not ok)
        ok, _, _ = compliance_gate(
            dict(good_card, compliance=dict(good_decl, purpose="ceo_authorized"))
        )
        check("compliance: ceo_authorized needs CEO order id", not ok)
        ok, _, _ = compliance_gate(
            dict(good_card, compliance=dict(
                good_decl, purpose="ceo_authorized",
                authorization_ref="CEO-20261109-MODEL-ROUTING"
            ))
        )
        check("compliance: CEO order id accepted", ok)

        routing = load_routing()
        layer, _ = route_for("classification", routing)
        check("routing: classification -> L2 local model", layer == "L2_LOCAL_LLM")
        layer, _ = route_for("format_check", routing)
        check("routing: format check -> L1 deterministic", layer == "L1_DETERMINISTIC")
        layer, _ = route_for("reasoning", routing)
        check("routing: reasoning -> L0 hy4", layer == "L0_HY4")
        layer, _ = route_for("unity_tool", routing)
        check("routing: unity tool -> L3 Codely", layer == "L3_CODELY")
        layer, _ = route_for("unknown_task", routing)
        check("routing: unknown class defaults to L0 hy4", layer == "L0_HY4")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for name, ok in results:
        print("%s  %s" % ("PASS" if ok else "FAIL", name))
    passed = sum(1 for _, ok in results if ok)
    print("%d/%d passed" % (passed, len(results)))
    return 0 if passed == len(results) else 1


def status():
    print("root       : %s" % ROOT)
    try:
        print("cli        : %s" % resolve_cli({}))
    except CardDefect as exc:
        print("cli        : MISSING (%s)" % exc)
    print("live       : %d (cap %d)" % (live_codely_count(), MAX_LIVE))
    if LOCK.exists():
        print("lock       : %s" % LOCK.read_text(encoding="utf-8").strip())
    else:
        print("lock       : free")
    files = sorted(RECEIPTS.glob("*-bm-m.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    bridge_receipts = [p for p in files if "CODELY" in p.name or "ST" == p.name[:2]]
    if bridge_receipts:
        print("last bridge: %s" % bridge_receipts[0].name)
    return 0


def main():
    ap = argparse.ArgumentParser(description="Explicit Codely dispatch bridge")
    ap.add_argument("--card", help="path to a card JSON file")
    ap.add_argument("--dry-run", action="store_true", help="print the plan without calling the CLI")
    ap.add_argument("--emit-only", action="store_true", help="green lane: write a manual card, never call the CLI")
    ap.add_argument("--compliance-check", action="store_true", help="report unresolved compliance face items")
    ap.add_argument("--route-check", metavar="TASK_CLASS", help="show which model layer handles a task class")
    ap.add_argument("--local-run", metavar="PROMPT", help="run a low-level task on the Mac local model (L2)")
    ap.add_argument("--self-test", action="store_true", help="verify the oracle, gate and router with local fixtures")
    ap.add_argument("--status", action="store_true", help="show CLI, lock and live sessions")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if args.route_check:
        return route_check(args.route_check)
    if args.local_run:
        return local_run(args.local_run)
    if args.compliance_check:
        return compliance_check()
    if args.status:
        return status()
    if not args.card:
        ap.print_help()
        return 3
    path = Path(args.card)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        print("CARD-DEFECT: card not found: %s" % path)
        return 3
    try:
        card = validate_card(json.loads(path.read_text(encoding="utf-8")))
    except (ValueError, CardDefect) as exc:
        print("CARD-DEFECT: %s" % exc)
        return 3
    return run_card(card, dry_run=args.dry_run, emit_only=args.emit_only)


if __name__ == "__main__":
    sys.exit(main())
