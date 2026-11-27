"""公版音视频语料拉取器（有声书 / 老电影 / 动画）。

只拉公有领域与开放授权集合，落 media/asset/inbox/<source>/，并写 manifest + RIGHTS。
可用源（archive.org 集合）：
  librivox   -> collection:librivoxaudio     纯人声朗读，最干净，直接切片即可
  films      -> collection:feature_films     公有领域老电影，需抽音轨（含配乐）
  cartoons   -> collection:animationandcartoons  公版动画，需抽音轨

用法：
  python Tools/fleet/voice_fetch_pd.py --source librivox --items 1 --lang en
  python Tools/fleet/voice_fetch_pd.py --source films --items 3 --max-mb 800
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

ROOT = "media/asset/inbox"
API = "https://archive.org"
UA = {"User-Agent": "FluxGroup-research/1.0"}

COLLECTIONS = {
    "librivox": "collection:librivoxaudio",
    "films": "collection:feature_films",
    "cartoons": "collection:animationandcartoons",
}

AUDIO_EXT = (".mp3", ".ogg", ".flac", ".m4a", ".opus")
VIDEO_EXT = (".mp4", ".mkv", ".avi", ".webm", ".ogv", ".mpg", ".mpeg", ".m2ts", ".mov", ".mp2")


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def search(source, lang, rows, query_extra=""):
    q = COLLECTIONS[source]
    if lang:
        q += " AND language:(%s)" % lang
    if query_extra:
        q += " AND " + query_extra
    url = "%s/advancedsearch.php?q=%s&fl%%5B%%5D=identifier&fl%%5B%%5D=title&rows=%d&page=1&output=json" % (
        API, urllib.parse.quote(q), rows)
    j = json.loads(get(url).decode("utf-8", "replace"))
    return j.get("response", {}).get("docs", [])


def item_files(identifier):
    j = json.loads(get("%s/metadata/%s" % (API, identifier)).decode("utf-8", "replace"))
    out = []
    for f in j.get("files", []):
        name = f.get("name", "")
        ext = os.path.splitext(name)[1].lower()
        if ext not in AUDIO_EXT + VIDEO_EXT:
            continue
        # 优先 64kb 小文件，避免拉母带
        out.append({"name": name, "ext": ext,
                    "size": int(f.get("size", 0) or 0)})
    return j.get("metadata", {}), out


def download(url, dst, max_bytes=None):
    tmp = dst + ".part"
    have = os.path.getsize(tmp) if os.path.exists(tmp) else 0
    if max_bytes and have >= max_bytes:
        return have
    req = urllib.request.Request(url, headers=UA)
    if have:
        req.add_header("Range", "bytes=%d-" % have)
    try:
        with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "ab") as fh:
            while True:
                chunk = r.read(262144)
                if not chunk:
                    break
                fh.write(chunk)
                have += len(chunk)
                if max_bytes and have >= max_bytes:
                    break
    except Exception as e:
        print("  dl error:", e, file=sys.stderr)
    if os.path.exists(tmp):
        os.replace(tmp, dst)
    return os.path.getsize(dst) if os.path.exists(dst) else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, choices=list(COLLECTIONS))
    ap.add_argument("--items", type=int, default=1, help="拉几个条目")
    ap.add_argument("--per-item", type=int, default=0, help="每个条目最多拉几个文件（0=全）")
    ap.add_argument("--max-mb", type=int, default=400, help="本批总上限（MB）")
    ap.add_argument("--lang", default="", help="语言过滤，例如 en / zh")
    ap.add_argument("--query", default="", help="附加查询，例如 year:[1930 TO 1945]")
    a = ap.parse_args()

    out_dir = os.path.join(ROOT, a.source)
    os.makedirs(out_dir, exist_ok=True)
    docs = search(a.source, a.lang, max(a.items * 3, 3), a.query)
    if not docs:
        sys.exit("search returned 0 items")

    manifest, used, done = [], 0, 0
    for d in docs:
        if done >= a.items:
            break
        ident = d["identifier"]
        title = d.get("title", "")
        try:
            meta, files = item_files(ident)
        except Exception as e:
            print("skip", ident, e)
            continue
        # 64kb 优先，其次任意音频，最后视频
        files.sort(key=lambda f: (0 if "64kb" in f["name"] else 1 if f["ext"] in AUDIO_EXT else 2,
                                  f["size"]))
        picked = files[:a.per_item] if a.per_item else files
        got = 0
        for f in picked:
            if used + f["size"] / 1048576 > a.max_mb:
                break
            dst = os.path.join(out_dir, f["name"].replace("/", "_"))
            if os.path.exists(dst) and os.path.getsize(dst) == f["size"]:
                got += 1
                continue
            url = "%s/download/%s/%s" % (API, ident, urllib.parse.quote(f["name"]))
            n = download(url, dst)
            if n:
                used += n / 1048576
                got += 1
                print("  + %-48s %5.1fMB" % (f["name"][:48], n / 1048576))
        if got:
            done += 1
            manifest.append({"identifier": ident, "title": title, "files": got,
                             "license": "public-domain",
                             "collection": COLLECTIONS[a.source]})

    json.dump({"source": a.source, "fetched": manifest,
               "total_mb": round(used, 1), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")},
              open(os.path.join(out_dir, "_FETCH-MANIFEST.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    rp = os.path.join(os.path.dirname(out_dir), "RIGHTS-%s.json" % a.source)
    json.dump({"source": "archive.org / " + COLLECTIONS[a.source],
               "license": "public-domain",
               "real_person": "narration and film performers; public-domain collection",
               "consent": "public domain",
               "note": "公有领域集合，按 archive.org 条目 licenseurl 复核；本地研究用途"},
              open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("done: %d items, %.1f MB -> %s" % (done, used, out_dir))


if __name__ == "__main__":
    main()