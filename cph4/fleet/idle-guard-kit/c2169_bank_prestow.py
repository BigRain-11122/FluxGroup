# c2169_bank_prestow.py - pre-stow the KN A-pack 768P successors (batch C2169).
# Producer law: the bank must never be empty at closeout. The running 768P wave
# is job 65, so two successors are stowed now: the zero-GPU harvest gate and the
# station-4 conform authoring job.
import json

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"

JOBS = [
    {
        "id": "kn-pa768-harvest-c2169",
        "status": "pending",
        "priority": 66,
        "auth": "station-3 gate for the KN A pack: the 30-unit 768P wave is burning (job 65), and its output is unread until every clip is probed, duplicate-run checked and sampled.",
        "require": {"files_at_least": [["media/mv-album-001-jay/clips-local-768", "KN_A-KN30.mp4", 1]]},
        "cmd": ["D:\\ComfyUI\\python_embeded\\python.exe",
                "K:\\Fluxgroup\\FluxGroup\\cph4\\fleet\\mv-album-001-jay\\kn_pa768_harvest_c2169.py"],
        "log_out": "media/mv-album-001-jay/logs/kn_pa768_harvest.out.log",
        "log_err": "media/mv-album-001-jay/logs/kn_pa768_harvest.err.log",
        "note": "Zero GPU. Waits for ALBUM LANE DONE (or 30 stable clips), then per unit: ffprobe, framemd5 duplicate run, three native frames, two 5-column boards, verdict JSON KN-PA768-HARVEST-c2169.json. PASS gate = HARVEST-END ok=30 check=0.",
        "created_ts": "2026-10-24 06:1x",
    },
    {
        "id": "kn-pa-station4-conform-author-c2169",
        "status": "pending",
        "priority": 67,
        "auth": "O-20261023-2325 station 4 follows the 768P pass: the KN A pack needs a conform (windows from the pack manifest) before the director can read motion across cuts.",
        "require": {"files_at_least": [["cph4/fleet/mv-album-001-jay", "KN-PA768-HARVEST-c2169.json", 1]]},
        "cmd": [],
        "log_out": "media/mv-album-001-jay/logs/kn_pa_conform.out.log",
        "log_err": "media/mv-album-001-jay/logs/kn_pa_conform.err.log",
        "note": "Authoring job (no GPU): build the KN A conform from the verified pack manifest windows onto clips-local-768, 960px review proxy plus a cut strip board. Only start when the harvest verdict is PASS; the window table must be re-derived from the pack, not hand typed.",
        "created_ts": "2026-10-24 06:1x",
    },
]


def main():
    raw = open(BANK, "rb").read()
    assert b"\r\n" in raw
    data = json.loads(raw.decode("utf-8-sig"))
    ids = {j["id"] for j in data["jobs"]}
    added = []
    for job in JOBS:
        if job["id"] in ids:
            print("SKIP exists %s" % job["id"])
            continue
        data["jobs"].append(job)
        added.append(job["id"])
    if not added:
        print("BANK_NO_CHANGE")
        return 0
    text = json.dumps(data, ensure_ascii=False, indent=1).replace("\n", "\r\n")
    open(BANK, "w", encoding="utf-8", newline="").write(text)
    check = json.loads(open(BANK, "rb").read().decode("utf-8-sig"))
    pending = [j["id"] for j in check["jobs"] if j.get("status") == "pending"]
    print("BANK_ADDED %s" % ",".join(added))
    print("BANK_PENDING %d %s" % (len(pending), ",".join(pending)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())