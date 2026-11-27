#!/usr/bin/env python3
"""200 人名单批量备料（network + CPU only，绝不碰 GPU）。

CEO 2026-11-13：「你可以去准备素材，不占用算力，这么多要训练的」。
本脚本只做三件事，全部可在白天做：
  1. 从 casting-pool-v1.json 读 200 人名单（字段 internal_index_only）
  2. 逐人调 face_source_collect.py 采集（360 图源，网络活）
  3. 逐人调 face_lora_prep.py build 出数据集（YuNet 检测，CPU 单进程）

严格不做：不训练、不加载模型、不写 GPU。

断点续跑：状态落 media/faces/_batch-state.json，重跑只处理未完成的。
可用数达标线：>=20 硬下限 / >=40 目标。不足的记 insufficient，等下一轮补采。

用法：
  python Tools/face_source_batch.py list                 # 看名单与当前进度
  python Tools/face_source_batch.py run --limit 20       # 推进 20 人
  python Tools/face_source_batch.py run --family ql      # 只做清冷破碎族
  python Tools/face_source_batch.py run --retry-low      # 只补采不够 40 张的人
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup"
POOL = os.path.join(ROOT, "cph4", "fleet", "mv-album-001-jay", "casting-pool-v1.json")
FACES = os.path.join(ROOT, "media", "faces")
STATE = os.path.join(FACES, "_batch-state.json")
LOCK = os.path.join(FACES, "_batch.lock")
PY = r"C:\Users\sjs20\train-lora\.venv\Scripts\python.exe"
COLLECT = os.path.join(ROOT, "Tools", "face_source_collect.py")
PREP = os.path.join(ROOT, "Tools", "face_lora_prep.py")

TARGET = 120         # 采集目标（过闸数）——2026-11-17 从 60 提高：curate 要 45 张，60 的池子
                     # 经过单脸+一致性筛选只剩 14，直接导致"永远不够、永远重采"。池子够大 kNN 才稳。
HARD_MIN = 20        # 训练硬下限
IDEAL = 40           # 目标线（建成的训练图数）
MAX_TRIES = 3        # 补采轮次上限：够硬下限后不再无限追 40

# 英文名/别名表：360 中文源命中率已经够，别名只在明显需要时补。
# 键=中文名，值=逗号分隔别名。
ALIAS = {
    "张柏芝": "Cecilia Cheung",
    "陈都灵": "Chen Duling",
    "韩素希": "Han Sohee",
    "刘浩存": "Liu Haocun",
    "沈银河": "Shen Yinhe",
    "董洁": "Dong Jie",
    "李沁": "Li Qin",
    "周也": "Zhou Ye",
    "张婧仪": "Zhang Jingyi",
    "小松菜奈": "Nana Komatsu",
    "中谷美纪": "Miki Nakatani",
    "娜塔莉·波特曼": "Natalie Portman",
    "莉莉·柯林斯": "Lily Collins",
    "凯拉·奈特莉": "Keira Knightley",
    "文淇": "Wen Qi",
    "邓恩熙": "Deng Enxi",
    "金智秀": "Jisoo",
    "裴秀智": "Suzy",
    "许玮甯": "Tiffany Hsu",
    "广末凉子": "Ryoko Hirosue",
    # 2026-11-18 补：日系/韩系人物用中文译名在 360 命中极差（rx 族 14 人 <20 张），
    # 原名（汉字旧字体/假名/罗马字）才是她们的图库主标签。名单里的译名有错字也一并纠回。
    "泽尻英龙华": "沢尻エリカ,泽尻绘里香,Erika Sawajiri",
    "伊藤由奈": "伊藤由奈,Yuna Ito",
    "西奈真里": "西内まりや,西内玛利亚,Mariya Nishiuchi",
    "古畑奈和": "古畑奈和,Nao Furuhata",
    "街山美穗": "街山美穂,街山みほ",
    "东云海": "東雲うみ,东云海",
    "桃月梨子": "桃月なしこ,桃月梨子",
    "牧野真莉爱": "牧野真莉愛,牧野真莉爱",
    "尾茂井奏良": "尾茂井奏良,尾茂井そら",
    "永江梨乃": "永江梨乃,永江りの",
    "贺喜遥香": "賀喜遥香,贺喜遥香,Haruka Kaki",
    "enako": "えなこ,エナコ,enako",
    "宫泽理惠": "宮沢りえ,宫泽理惠,Rie Miyazawa",
    "中条彩未": "中条あやみ,中条彩未,Ayami Nakajo",
    "苍井优": "蒼井優,苍井优,Aoi Yu",
    "宫崎葵": "宮崎あおい,宫崎葵,Aoi Miyazaki",
    "鬼束千寻": "鬼束ちひろ,鬼束千寻,Chihiro Onitsuka",
    "永作博美": "永作博美,Hiromi Nagasaku",
    "濑户朝香": "瀬戸朝香,濑户朝香,Asaka Seto",
    "三原羽衣": "三原羽衣,三原羽衣",
    "出口夏希": "出口夏希,Natsuki Deguchi",
    "朴善英": "박선영,朴善英,Park Sun-young",
    # 2026-11-18 第二轮：这几个人不是图少，是**名字歧义**——raw 上百张但 kNN 判"不是同一个人"
    # （rx15 119 张挑不出 20、wm18 73 张挑不出 20）。加职业/作品限定词把检索钉到本人身上。
    "尾茂井奏良": "尾茂井奏良 女優,尾茂井そら グラビア,尾茂井奏良 作品",
    "Cece Natalie": "Cece Natalie model,Cece Natalie 模特,Cece Natalie cosplay",
    "东云海": "東雲うみ グラビア,東雲うみ 写真集,东云海 写真",
    "Lykke Li": "Lykke Li singer,莉琦李,Lykke Li 歌手",
    "Charlotte Gainsbourg": "夏洛特·甘斯布,Charlotte Gainsbourg actress,夏洛特甘斯布 电影",
    "Sasha Sloan": "Sasha Sloan singer,萨莎斯隆,Sasha Sloan 歌手",
}

BAD_NAME_CHARS = re.compile(r"[\\/:*?\"<>|]")


def pinyin_key(name: str, fam: str, idx: int) -> str:
    """目录名：族id+序号，避开中文路径在工具链里的编码坑。"""
    return f"{fam}{idx:02d}"


def load_people() -> list[dict]:
    with open(POOL, encoding="utf-8") as f:
        d = json.load(f)
    out = []
    for fam in d["families"]:
        # kr=韩系爱豆是 ANTI_K 反韩锚的禁项库，整族不备料（CEO「不要像韩国的」）
        if fam["id"] == "kr":
            continue
        names = fam.get("internal_index_only") or []
        for i, nm in enumerate(names, 1):
            out.append({
                "key": pinyin_key(nm, fam["id"], i),
                "family": fam["id"],
                "family_name": fam["name"],
                "name": nm,
            })
    return out


def load_state() -> dict:
    if os.path.isfile(STATE):
        try:
            with open(STATE, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}


def save_state(st: dict) -> None:
    os.makedirs(FACES, exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE)


def run(cmd: list[str], timeout: int = 3600) -> tuple[int, str]:
    # 子进程默认按系统 GBK 输出；不钉 UTF-8 就会被上层按 UTF-8 解成乱码，
    # 正则匹配不到「可用 N 张」，结果被误记为 0（2026-11-13 实锚）。
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    # 计划任务用 pythonw 承载时本进程无控制台，子进程须显式不建窗口，否则闪黑窗
    flags = 0x08000000 if os.name == "nt" else 0
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, env=env, creationflags=flags)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def collect_one(p: dict, rounds: int) -> tuple[int, str]:
    """采到 TARGET 可用；每轮 pages 递增，命中率低时多翻几页。"""
    outdir = os.path.join(FACES, p["key"])
    alias = ALIAS.get(p["name"], "")
    best = 0
    last = ""
    for r in range(rounds):
        cmd = [PY, COLLECT, "collect", "--person", p["name"],
               "--pages", str(3 + r * 2), "--want-links", str(400 + r * 200),
               "--target", str(TARGET), "--min-side", "600", "--out", outdir]
        if alias:
            cmd += ["--alias", alias]
        rc, out = run(cmd)
        last = out
        m = re.search(r"可用 (\d+) 张", out)
        n = int(m.group(1)) if m else 0
        best = max(best, n)
        if n >= IDEAL:
            break
        time.sleep(1)
    return best, last


def curate_one(p: dict) -> tuple[int, str]:
    """人物一致性挑选：把混进来的他人脸清出去（不挑干净会训出"多张脸的平均"）。

    2026-11-17 改：源目录从 keep/ 改为 raw/ 优先。keep/ 是下载端的粗筛产物，
    它的单脸阈值一度比这里更严（0.3 vs 0.6），于是"上游截流、下游再松也没用"
    ——实测 ql05 raw 100 张，从 keep 挑只出 14 张，从 raw 挑能出 37 张。
    curate 自带置信度/脸宽/kNN/文字四项判据，不依赖 keep 的预筛。
    """
    raw = os.path.join(FACES, p["key"], "raw")
    keep = os.path.join(FACES, p["key"], "keep")
    src = raw if os.path.isdir(raw) else keep
    if not os.path.isdir(src):
        return 0, "no raw/keep dir"
    out = os.path.join(FACES, p["key"], "curated")
    board = os.path.join(FACES, "_boards", p["key"] + ".jpg")
    rc, out_txt = run([PY, PREP, "curate", src, "--out", out,
                       "--keep", "45", "--board", board])
    m = re.search(r"留存 (\d+) 张", out_txt)
    return (int(m.group(1)) if m else 0), out_txt


def build_one(p: dict) -> tuple[int, str]:
    ds = os.path.join(FACES, p["key"] + "-ds")
    raw = os.path.join(FACES, p["key"], "curated")
    if not os.path.isdir(raw):
        raw = os.path.join(FACES, p["key"], "keep")
    if not os.path.isdir(raw):
        return 0, "no curated/keep dir"
    rc, out = run([PY, PREP, "build", raw, "--out", ds, "--trigger", "ohwx_woman"])
    m = re.search(r"生成 (\d+) 张", out)
    return (int(m.group(1)) if m else 0), out


def cmd_list(a) -> int:
    people = load_people()
    st = load_state()
    print(f"名单 {len(people)} 人（10 族 × 20）\n")
    by_fam: dict[str, list] = {}
    for p in people:
        by_fam.setdefault(f"{p['family']} {p['family_name']}", []).append(p)
    for fam, rows in by_fam.items():
        done = sum(1 for p in rows if st.get(p["key"], {}).get("built", 0) >= HARD_MIN)
        print(f"  {fam}: {done}/{len(rows)} 达标")
    got = sum(1 for p in people if st.get(p["key"], {}).get("built", 0) >= HARD_MIN)
    ideal = sum(1 for p in people if st.get(p["key"], {}).get("built", 0) >= IDEAL)
    print(f"\n合计：{got}/{len(people)} 过硬下限 · {ideal} 过目标线")
    return 0


def _holder_alive(holder: int) -> bool:
    """锁文件里记的是 pid。进程被强杀时析构不跑、锁留盘上，只靠超时会白等 90 分钟
    （2026-11-18 实锚：我用 taskkill 停了补采，随后两次启动全被自己的死锁挡住）。"""
    if not holder:
        return False
    try:
        if os.name == "nt":
            out = subprocess.run(["tasklist", "/FI", "PID eq %d" % holder],
                                 capture_output=True, text=True,
                                 creationflags=0x08000000).stdout
            return str(holder) in out
        os.kill(holder, 0)
        return True
    except Exception:
        return False


def acquire_lock() -> bool:
    """单写者：会话内连续跑与计划任务巡检可能同时起，撞车会重复下载并互相覆盖台账。"""
    try:
        os.makedirs(FACES, exist_ok=True)
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        holder = 0
        try:
            holder = int((open(LOCK).read() or "0").strip())
        except Exception:
            holder = 0
        # ①持有者进程已死 → 立刻接管，不等 90 分钟
        if holder and not _holder_alive(holder):
            try:
                os.remove(LOCK)
            except OSError:
                pass
            return acquire_lock()
        # ②进程查不到/锁内容坏了 → 退回超时判定
        try:
            if time.time() - os.path.getmtime(LOCK) > 5400:
                os.remove(LOCK)
                return acquire_lock()
        except OSError:
            pass
        return False


def release_lock() -> None:
    try:
        os.remove(LOCK)
    except OSError:
        pass


def cmd_run(a) -> int:
    if not acquire_lock():
        print("[skip] 另一路备料正在运行（_batch.lock），本路退出")
        return 0
    try:
        return _run_locked(a)
    finally:
        release_lock()


def _run_locked(a) -> int:
    people = load_people()
    st = load_state()
    todo = []
    for p in people:
        rec = st.get(p["key"], {})
        # 以「建成的训练图数」为准，不是过闸数——挑人会掉 15-25%，不能用过闸数冒充达标
        n = rec.get("built", 0)
        if a.family and p["family"] != a.family:
            continue
        if a.retry_low:
            if n < IDEAL:
                todo.append(p)
            continue
        if n >= IDEAL:
            continue
        # 够硬下限且已试过 MAX_TRIES 轮 → 收手，不无限追 40（老照片池子就这么大）
        if n >= HARD_MIN and rec.get("tries", 0) >= MAX_TRIES:
            continue
        todo.append(p)
    if a.limit:
        todo = todo[:a.limit]
    if not todo:
        print("[done] 没有待处理的人")
        return 0

    print(f"[{datetime.now():%H:%M:%S}] 本轮处理 {len(todo)} 人（network+CPU，不占 GPU）")
    for i, p in enumerate(todo, 1):
        t0 = time.time()
        rec = st.setdefault(p["key"], {})
        rec["name"] = p["name"]
        rec["family"] = p["family"]
        rec["tries"] = rec.get("tries", 0) + 1
        try:
            usable, out = collect_one(p, a.rounds)
            # 先挑人再建集：混进别人的脸会训出"多张脸的平均"，比素材少更糟
            curated, cout = curate_one(p) if usable > 0 else (0, "")
            built, bout = build_one(p) if curated >= 20 else (0, "")
        except subprocess.TimeoutExpired:
            usable, curated, built = 0, 0, 0
            out, cout, bout = "timeout", "", ""
        rec["usable"] = usable
        rec["curated"] = curated
        rec["built"] = built
        rec["status"] = ("ok" if built >= IDEAL
                         else "low" if built >= HARD_MIN
                         else "insufficient")
        rec["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_state(st)
        dt = time.time() - t0
        print(f"  [{i}/{len(todo)}] {p['key']} {p['name']}: 过闸 {usable} · 挑后 {curated} "
              f"· 建成 {built} · {rec['status']} · {dt:.0f}s")
        if rec["status"] == "insufficient":
            tail = [ln for ln in out.strip().splitlines() if ln.strip()][-2:]
            for ln in tail:
                print(f"      {ln.strip()[:110]}")
    save_state(st)
    cmd_list(a)
    return 0


def cmd_recurate(a) -> int:
    """只对已有 keep 目录的人重跑挑人+建集（不重新下载）。

    用途：挑选判据上线前已采集的那批，数据集里还混着别人的脸，需要就地重做。
    """
    if not acquire_lock():
        print("[skip] 另一路备料正在运行（_batch.lock），本路退出")
        return 0
    try:
        people = load_people()
        st = load_state()
        done = 0
        for p in people:
            rec = st.get(p["key"])
            if not rec:
                continue
            keep = os.path.join(FACES, p["key"], "keep")
            if not os.path.isdir(keep):
                continue
            cur, __ = curate_one(p)
            built, __ = build_one(p) if cur >= 5 else (0, "")
            rec["curated"] = cur
            rec["built"] = built
            rec["status"] = ("ok" if built >= IDEAL
                             else "low" if built >= HARD_MIN
                             else "insufficient")
            rec["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_state(st)
            done += 1
            print(f"  {p['key']} {p['name']}: 挑后 {cur} · 建成 {built} · {rec['status']}")
        print(f"[done] 重挑 {done} 人")
        return 0
    finally:
        release_lock()


def main(argv=None) -> int:
    # pythonw 承载时 sys.stdout 可能为 None，print 会抛 AttributeError 让任务静默死；
    # 控制台/管道为 GBK 时，含替换字符的日志又会抛 UnicodeEncodeError 中断整批。
    if sys.stdout is None or sys.stderr is None:
        try:
            os.makedirs(FACES, exist_ok=True)
            _f = open(os.path.join(FACES, "_batch-stdout.log"), "a", encoding="utf-8", buffering=1)
        except OSError:
            _f = None
        if _f is not None:
            if sys.stdout is None:
                sys.stdout = _f
            if sys.stderr is None:
                sys.stderr = _f
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    ap = argparse.ArgumentParser(description="200 人名单批量备料（不占 GPU）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    r = sub.add_parser("run")
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--family", default="")
    r.add_argument("--rounds", type=int, default=2, help="每人最多采几轮")
    r.add_argument("--retry-low", dest="retry_low", action="store_true",
                   help="只处理未达目标线(40)的人")
    sub.add_parser("recurate", help="对已有素材重跑挑人+建集（不重新下载）")
    a = ap.parse_args(argv)
    return {"list": cmd_list, "run": cmd_run, "recurate": cmd_recurate}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
