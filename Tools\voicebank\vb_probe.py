# -*- coding: utf-8 -*-
"""vb_probe.py - inspect a Bilibili video's audio ceiling + find a named 有声书 host."""
import json
import sys
import urllib.request

from bilibili_api import search, video, sync

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def video_audio(bvid):
    v = video.Video(bvid=bvid)
    info = sync(v.get_info())
    data = sync(v.get_download_url(0))
    dash = (data or {}).get("dash") or {}
    audios = []
    for a in dash.get("audio") or []:
        audios.append({"id": a.get("id"), "bandwidth": a.get("bandwidth"),
                       "mime": a.get("mimeType"), "codecs": a.get("codecs")})
    flac = dash.get("flac") or {}
    return {
        "bvid": bvid,
        "title": info.get("title"),
        "owner": (info.get("owner") or {}).get("name"),
        "mid": (info.get("owner") or {}).get("mid"),
        "duration": info.get("duration"),
        "pages": len(info.get("pages") or []),
        "audios": audios,
        "flac": {"present": bool(flac), "bandwidth": (flac.get("audio") or {}).get("bandwidth")},
    }


def find_host(kw):
    out = []
    for page in (1, 2):
        try:
            r = sync(search.search_by_type(kw, search_type=search.SearchObjectType.VIDEO, page=page))
        except Exception as e:
            out.append({"error": repr(e)[:120]})
            break
        for v in (r or {}).get("result") or []:
            out.append({"bvid": v.get("bvid"), "title": v.get("title"),
                        "author": v.get("author"), "mid": v.get("mid"),
                        "dur": v.get("duration"), "play": v.get("play")})
    return out


res = {"target": video_audio("BV1sa756bEVy"),
       "host_search": find_host("侯卫东官场笔记")[:20]}
print(json.dumps(res, ensure_ascii=False, indent=1))