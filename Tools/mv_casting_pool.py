"""女主气质选角库（CASTING-POOL-v1）取用与合规机检。

名单=CEO 2026-11-12 亲授 200 人 ×10 风格分类。边界：只取气质、做原创脸——
真名仅内部美学索引，禁入提示词、禁复刻本人。

用法：
  python Tools/mv_casting_pool.py list
  python Tools/mv_casting_pool.py show ql
  python Tools/mv_casting_pool.py prompt ql [--era 2000tw]
  python Tools/mv_casting_pool.py assign 龙卷风
  python Tools/mv_casting_pool.py lint <file|dir> [...]      # 真名泄漏闸：命中即 rc=1
  python Tools/mv_casting_pool.py check                      # 库结构自检

判据来源=CASTING-LAW.md + research/SEAT-casting-20261020.md
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(ROOT, "cph4", "fleet", "mv-album-001-jay", "casting-pool-v1.json")

# 提示词里出现这些句式=拿真人当靶子，不论是否点到名都判负
RISKY_PHRASES = ["像哪个明星", "同款", "in the style of", "look like", "resembling", "celebrity lookalike"]


def load():
    with open(POOL, encoding="utf-8") as f:
        return json.load(f)


def find(data, key):
    k = (key or "").strip().lower()
    for fam in data["families"]:
        if fam["id"].lower() == k or fam["name"].lower() == k or k in [a.lower() for a in fam.get("aliases", [])]:
            return fam
    return None


def all_names(data):
    out = []
    for fam in data["families"]:
        for n in fam["internal_index_only"]:
            out.append((n, fam["id"]))
    return out


def cmd_list(data):
    print(f"{'id':<4} {'族名':<10} {'年代适配':<11} {'人数':<4} 适配曲")
    for fam in data["families"]:
        fit = fam["era_2000_tw"]["fit"]
        songs = "、".join(fam["music_fit"][:3]) or "—"
        print(f"{fam['id']:<4} {fam['name']:<10} {fit:<11} {len(fam['internal_index_only']):<4} {songs}")
    print(f"\n合计 {sum(len(f['internal_index_only']) for f in data['families'])} 人 / "
          f"{len(data['families'])} 族；无女主曲：{'、'.join(data['no_lead']['songs'])}")
    return 0


def cmd_show(data, key):
    fam = find(data, key)
    if not fam:
        print(f"未找到族：{key}", file=sys.stderr)
        return 2
    era = fam["era_2000_tw"]
    print(f"# {fam['name']}（{fam['id']}）")
    print(f"\n气质：{fam['gaze']}")
    print("\n四锚点：")
    for k, v in fam["structure"].items():
        print(f"  - {k}: {v}")
    print(f"\n年代适配 2000-2003 台湾：{era['fit']} — {era['note']}")
    print(f"\n适配曲：{'、'.join(fam['music_fit']) or '（无）'}")
    print(f"\n禁项：{'、'.join(fam['avoid'])}")
    print(f"\n内部索引（仅索引·禁入提示词）：{'、'.join(fam['internal_index_only'])}")
    return 0


def cmd_prompt(data, key, era_tag):
    fam = find(data, key)
    if not fam:
        print(f"未找到族：{key}", file=sys.stderr)
        return 2
    if fam["era_2000_tw"]["fit"] == "banned":
        print(f"[refuse] {fam['name']} = ANTI_K 禁项库，禁进入任何生成提示词", file=sys.stderr)
        return 1
    st = fam["structure"]
    print("# 主体（自包含·无真人名）")
    print(fam["prompt_block"])
    print("\n# 四锚点（与同曲族均值至少 2 项偏离 ≥8%）")
    print(f"brow: {st['brow']}; eye spacing: {st['eye']}; nose: {st['nose']}; lips: {st['lips']}")
    print("\n# 妆发与质感")
    print(f"skin: {st['skin']}; hair: {st['hair']}; jaw: {st['jaw']}")
    print(f"\n# 年代锚（{era_tag}）")
    print(f"{fam['era_2000_tw']['note']}")
    print("\n# 禁项（已用正向锚挤位，此处仅供 QC 复核，禁写入提示词）")
    print("、".join(fam["avoid"]))
    print("\n# 出片后硬闸")
    print("反向三问全 NOBODY（原文留档）；跨曲 cosine<0.4；同曲跨镜≥0.5；四锚点偏差≤5%")
    return 0


def cmd_assign(data, song):
    song = song.strip()
    if song in data["no_lead"]["songs"]:
        print(f"{song}：无女主位。{data['no_lead']['note']}")
        return 0
    hits = [(f["id"], f["name"], f["era_2000_tw"]["fit"]) for f in data["families"] if song in f["music_fit"]]
    if not hits:
        usable = [f["name"] for f in data["families"] if f["era_2000_tw"]["fit"] in ("high", "medium")]
        print(f"{song}：库内未登记适配族。按本曲情绪域在 {'、'.join(usable)} 中选，"
              f"开案后回填 casting-pool-v1.json 的 music_fit。")
        return 0
    print(f"{song} 候选族：")
    for fid, name, fit in hits:
        print(f"  - {fid} {name}（年代适配 {fit}）")
    print("\n禁跨曲复用：本曲定脸后 ID 块入该曲 canon，他曲不得抄（含种子）。")
    return 0


def _iter_files(targets):
    exts = {".md", ".txt", ".json", ".py", ".yaml", ".yml", ".jsonl", ".csv"}
    for t in targets:
        if os.path.isdir(t):
            for base, _, files in os.walk(t):
                for fn in files:
                    if os.path.splitext(fn)[1].lower() in exts:
                        yield os.path.join(base, fn)
        else:
            yield t


def cmd_lint(data, targets):
    names = all_names(data)
    bad = 0
    scanned = 0
    for path in _iter_files(targets):
        scanned += 1
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except OSError as e:
            print(f"[warn] 读不到 {path}: {e}", file=sys.stderr)
            continue
        # 名单本体文件豁免（本文件的 internal_index_only 是唯一合法落点）
        if os.path.basename(path) == os.path.basename(POOL):
            continue
        for i, line in enumerate(lines, 1):
            low = line.lower()
            for name, fid in names:
                if name in line:
                    print(f"{path}:{i}: [REAL-NAME] {name}（族 {fid}）")
                    bad += 1
            for ph in RISKY_PHRASES:
                if ph.lower() in low:
                    print(f"{path}:{i}: [TARGETING] {ph}")
                    bad += 1
    print(f"\n扫描 {scanned} 文件 · 命中 {bad} · 判 {'FAIL' if bad else 'PASS'}")
    return 1 if bad else 0


def cmd_check(data):
    errs = []
    fams = data["families"]
    ids = [f["id"] for f in fams]
    if len(fams) != 10:
        errs.append(f"族数={len(fams)}，应为 10")
    if len(set(ids)) != len(ids):
        errs.append("族 id 重复")
    seen = {}
    total = 0
    for f in fams:
        n = f["internal_index_only"]
        total += len(n)
        if len(n) != 20:
            errs.append(f"{f['id']} 人数={len(n)}，应为 20")
        for name in n:
            if name in seen:
                errs.append(f"名单重复：{name}（{seen[name]} 与 {f['id']}）")
            seen[name] = f["id"]
        if not f["prompt_block"].strip():
            errs.append(f"{f['id']} prompt_block 为空")
        for name in n:
            if name in f["prompt_block"]:
                errs.append(f"{f['id']} prompt_block 内含真名 {name}（泄漏）")
        if f["era_2000_tw"]["fit"] not in ("high", "medium", "restricted", "situational", "banned"):
            errs.append(f"{f['id']} era fit 值非法")
        if f["era_2000_tw"]["fit"] == "banned" and f["music_fit"]:
            errs.append(f"{f['id']} 标 banned 却挂了适配曲")
        for k in ("brow", "eye", "nose", "lips", "jaw", "skin", "hair"):
            if not f["structure"].get(k):
                errs.append(f"{f['id']} 缺锚点 {k}")
    if total != 200:
        errs.append(f"总人数={total}，应为 200")
    if errs:
        for e in errs:
            print(f"[FAIL] {e}")
        return 1
    print(f"[PASS] 10 族 / {total} 人 / 每族 20 / prompt_block 零真名泄漏 / 锚点齐")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="女主气质选角库取用与合规机检")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sp = sub.add_parser("show"); sp.add_argument("key")
    sp = sub.add_parser("prompt"); sp.add_argument("key"); sp.add_argument("--era", default="2000tw")
    sp = sub.add_parser("assign"); sp.add_argument("song")
    sp = sub.add_parser("lint"); sp.add_argument("targets", nargs="+")
    sub.add_parser("check")
    a = ap.parse_args(argv)

    data = load()
    if a.cmd == "list":
        return cmd_list(data)
    if a.cmd == "show":
        return cmd_show(data, a.key)
    if a.cmd == "prompt":
        return cmd_prompt(data, a.key, a.era)
    if a.cmd == "assign":
        return cmd_assign(data, a.song)
    if a.cmd == "lint":
        return cmd_lint(data, a.targets)
    return cmd_check(data)


if __name__ == "__main__":
    sys.exit(main())
