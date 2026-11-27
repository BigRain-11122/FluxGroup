#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_identity.py - 本机是哪个工位：**唯一权威**。

2026-11-12 立。此前有三份独立实现（`station_shards._own_station` /
`local_model.local_station` / `station_drive.detect_station`），全部是
"FLEET_STATION > hostname，出异常就返回 None"。两个真问题：

1) 同一事实三处定义 —— 改一处等于没改（gate-rigor 第 4 问）。
2) **fail-open**：local_model 一次普通编辑把语法改坏（实测 IndentationError），
   身份就变成 None，一机一写者护栏随之静默失效，且无任何告警。

证据分级（强 → 弱）：
  ① identity 文件（部署时写入，权限 0600，内容即工位 id）—— 强证据
  ② hostname 匹配 STATIONS.json —— 中证据
  ③ FLEET_STATION 环境变量 —— 显式覆盖，仅当没有①时采信；与①冲突即拒绝

判据（不猜、不默认主控）：
  - 文件与 hostname 指向不同工位 → IdentityConflict（拒绝运行，rc=2）
  - 文件读取失败（不是"不存在"）→ IdentityError（fail-closed，不许当成无身份）
  - 没有任何证据 → None（调用方决定是拒绝还是仅提示）

用法：
  python3 Tools/fleet/fleet_identity.py            # 打印本机身份与证据
  python3 Tools/fleet/fleet_identity.py --write    # 把当前判定的身份写成本机文件（0600）
  python3 Tools/fleet/fleet_identity.py --self-test
"""
import argparse
import json
import os
import socket
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATIONS_JSON = os.path.join(ROOT, "cph4", "fleet", "STATIONS.json")
DEFAULT_IDENTITY = os.path.join(os.path.expanduser("~"), ".fluxgroup", "station")


class IdentityError(RuntimeError):
    """身份读取失败：**不许**降级成"无身份"（fail-closed）。"""


class IdentityConflict(RuntimeError):
    """两条强证据互相矛盾：拒绝运行，让人来判。"""


def identity_path():
    return os.environ.get("FLUX_IDENTITY") or DEFAULT_IDENTITY


def stations(root=None):
    p = os.path.join(os.path.abspath(root) if root else ROOT, "cph4", "fleet", "STATIONS.json")
    with open(p, encoding="utf-8-sig") as f:
        return {s["id"]: s for s in json.load(f).get("stations") or []}


def _from_file():
    p = identity_path()
    if not os.path.exists(p):
        return None, None
    try:
        with open(p, encoding="utf-8-sig") as f:
            v = f.read().strip()
    except OSError as e:
        raise IdentityError("身份文件不可读（%s）：%s" % (p, e))
    if not v:
        raise IdentityError("身份文件是空的：%s（要么写好，要么删掉）" % p)
    return v, p


def _from_hostname(root=None):
    try:
        host = socket.gethostname().lower()
    except Exception as e:
        raise IdentityError("取 hostname 失败：%s" % e)
    try:
        for sid, s in stations(root).items():
            h = str(s.get("hostname") or "").lower()
            if not h or h.startswith("pending"):
                continue
            if h == host or host.startswith(h.split(".")[0]):
                return sid, host
    except IdentityError:
        raise
    except Exception as e:
        raise IdentityError("读 STATIONS.json 失败：%s" % e)
    return None, host


def resolve(root=None):
    """返回 {station, mode, evidence, notes}；没有任何证据时 station=None。

    mode ∈ identity-file / hostname / env / conflicting(已抛) / none
    """
    notes = []
    fst, fpath = _from_file()
    hst, host = _from_hostname(root)
    env = (os.environ.get("FLEET_STATION") or "").strip() or None

    if fst:
        try:
            known = stations(root)
        except Exception:
            known = {}
        if known and fst not in known:
            raise IdentityConflict("身份文件写的工位不存在：%s（合法：%s）"
                                   % (fst, ", ".join(sorted(known))))
        if hst and hst != fst:
            raise IdentityConflict(
                "身份文件说本机是 %s，但 hostname(%s) 匹配到 %s —— 两条强证据互相矛盾，"
                "请人工确认后改正身份文件" % (fst, host, hst))
        if env and env != fst:
            notes.append("FLEET_STATION=%s 与身份文件不一致，以文件为准" % env)
        return {"station": fst, "mode": "identity-file",
                "evidence": {"file": fpath, "hostname": host, "hostname_station": hst},
                "notes": notes}

    if hst:
        if env and env != hst:
            notes.append("FLEET_STATION=%s 与 hostname 判定的 %s 不一致，以 hostname 为准"
                         % (env, hst))
        return {"station": hst, "mode": "hostname",
                "evidence": {"file": None, "hostname": host, "hostname_station": hst},
                "notes": notes}

    if env:
        try:
            known = stations(root)
        except Exception:
            known = {}
        if known and env not in known:
            raise IdentityConflict("FLEET_STATION=%s 不是合法工位（合法：%s）"
                                   % (env, ", ".join(sorted(known))))
        notes.append("仅凭 FLEET_STATION 判定（无身份文件、hostname 未匹配）")
        return {"station": env, "mode": "env",
                "evidence": {"file": None, "hostname": host, "hostname_station": None},
                "notes": notes}

    return {"station": None, "mode": "none",
            "evidence": {"file": None, "hostname": host, "hostname_station": None},
            "notes": notes + ["没有任何身份证据"]}


def station(root=None):
    """严格模式：解析不出就抛 IdentityError（写路径用，绝不放行）。"""
    r = resolve(root)
    if not r["station"]:
        raise IdentityError("无法判定本机工位：写 %s（内容=工位 id）或设 FLEET_STATION"
                            % identity_path())
    return r["station"]


def station_or_none(root=None):
    """宽松模式：没有任何证据时返回 None（显示/巡检用）。

    注意：读取失败仍然抛 IdentityError —— "读不到"不等于"没有身份"。
    """
    return resolve(root)["station"]


def write_identity(value=None, path=None):
    """把判定结果写成本机身份文件（0600）。返回写入路径。"""
    v = value or station()
    p = path or identity_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(v.strip() + "\n")
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass
    return p


def self_test():
    import tempfile
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    td = tempfile.mkdtemp(prefix="ident-")
    fake_root = os.path.join(td, "repo")
    os.makedirs(os.path.join(fake_root, "cph4", "fleet"))
    with open(os.path.join(fake_root, "cph4", "fleet", "STATIONS.json"), "w", encoding="utf-8") as f:
        json.dump({"stations": [
            {"id": "control", "hostname": "host-a"},
            {"id": "visual", "hostname": "host-b"},
        ]}, f)

    old_env = os.environ.pop("FLEET_STATION", None)
    old_idf = os.environ.get("FLUX_IDENTITY")
    try:
        # 1) 无文件 + hostname 不匹配 + 无 env -> None
        os.environ["FLUX_IDENTITY"] = os.path.join(td, "none")
        chk("无任何证据 -> None（不默认主控）", station_or_none(fake_root) is None)

        # 2) 只有 env -> env 模式
        os.environ["FLEET_STATION"] = "visual"
        chk("只有 FLEET_STATION -> 采信并标注来源", resolve(fake_root)["mode"] == "env")
        os.environ.pop("FLEET_STATION")

        # 3) 身份文件 -> 强证据优先
        p = os.path.join(td, "id")
        with open(p, "w", encoding="utf-8") as f:
            f.write("control\n")
        os.environ["FLUX_IDENTITY"] = p
        r = resolve(fake_root)
        chk("身份文件存在 -> identity-file 模式", r["mode"] == "identity-file" and r["station"] == "control")

        # 4) 负控：env 与文件冲突 -> 以文件为准并留提示
        os.environ["FLEET_STATION"] = "visual"
        r = resolve(fake_root)
        chk("负控：env 与文件冲突 -> 以文件为准", r["station"] == "control" and r["notes"])
        os.environ.pop("FLEET_STATION")

        # 5) 负控：文件写的工位不存在 -> 冲突
        with open(p, "w", encoding="utf-8") as f:
            f.write("not-a-station\n")
        try:
            resolve(fake_root)
            chk("负控：文件写非法工位必须拒绝", False)
        except IdentityConflict:
            chk("负控：文件写非法工位必须拒绝", True)

        # 6) 负控：文件空 -> IdentityError（不许当成无身份）
        with open(p, "w", encoding="utf-8") as f:
            f.write("   \n")
        try:
            resolve(fake_root)
            chk("负控：空身份文件必须 fail-closed", False)
        except IdentityError:
            chk("负控：空身份文件必须 fail-closed", True)

        # 7) 负控：hostname 与文件矛盾 -> 冲突（用 monkeypatch 模拟）
        with open(p, "w", encoding="utf-8") as f:
            f.write("control\n")
        _orig = globals()["_from_hostname"]
        try:
            globals()["_from_hostname"] = lambda root=None: ("visual", "host-b")
            try:
                resolve(fake_root)
                chk("负控：文件 control 但 hostname 判 visual 必须拒绝", False)
            except IdentityConflict:
                chk("负控：文件 control 但 hostname 判 visual 必须拒绝", True)
        finally:
            globals()["_from_hostname"] = _orig

        # 8) 严格模式：没有证据 -> 抛
        os.environ["FLUX_IDENTITY"] = os.path.join(td, "none")
        try:
            station(fake_root)
            chk("严格模式：无证据必须抛（写路径不放行）", False)
        except IdentityError:
            chk("严格模式：无证据必须抛（写路径不放行）", True)

        # 9) 写入权限 0600
        p2 = os.path.join(td, "id2")
        write_identity("control", p2)
        mode = oct(os.stat(p2).st_mode & 0o777)
        chk("身份文件权限 0600", mode == "0o600", mode)
    finally:
        if old_env is not None:
            os.environ["FLEET_STATION"] = old_env
        if old_idf is None:
            os.environ.pop("FLUX_IDENTITY", None)
        else:
            os.environ["FLUX_IDENTITY"] = old_idf

    print("[fleet_identity] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="把判定结果写成本机身份文件（0600）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    try:
        r = resolve()
    except (IdentityError, IdentityConflict) as e:
        print(json.dumps({"error": str(e), "type": type(e).__name__}, ensure_ascii=False, indent=1))
        return 2
    if a.write:
        if not r["station"]:
            print(json.dumps({"error": "判定不出工位，先设 FLEET_STATION 或修 hostname",
                              "evidence": r["evidence"]}, ensure_ascii=False, indent=1))
            return 2
        p = write_identity(r["station"])
        r["written"] = p
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print("本机工位：%s（依据：%s）" % (r["station"] or "未判定", r["mode"]))
        ev = r["evidence"]
        print("  hostname=%s → %s" % (ev.get("hostname"), ev.get("hostname_station") or "未匹配"))
        print("  身份文件=%s" % (ev.get("file") or "无（%s）" % identity_path()))
        for n in r["notes"]:
            print("  注：%s" % n)
        if r.get("written"):
            print("  已写入：%s（0600）" % r["written"])
    return 0 if r["station"] else 1


if __name__ == "__main__":
    sys.exit(main())
