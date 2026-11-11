#!/usr/bin/env python3
"""Download images that published posts load from other sites, so the site keeps a copy.

Usage: python3 -I scripts/fetch_external_images.py source/<export>.xml

Saves each image to static/images/external/<host>/<file> (the exact size the post used)
and writes migration/external-images.json mapping the original URL to the local path.
If the original is gone, it tries the Internet Archive's copy (web.archive.org, 2022 snapshot).
scripts/wp_to_hugo.py uses a local copy wherever the mapped file exists.
Owner decision (Phase 2): store copies, recovering from the Wayback Machine where needed.
"""
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

NS = {"wp": "http://wordpress.org/export/1.2/", "content": "http://purl.org/rss/1.0/modules/content/"}
OWN = re.compile(r"^https?://(www\.)?monicaespinel\.com/")
EXT = {"image/jpeg": ".jpeg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}
MAP = Path("migration/external-images.json")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "monicaespinel.com site migration"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(), r.headers.get_content_type()


def main(src):
    ch = ET.parse(src).getroot().find("channel")
    urls = []
    for i in ch.findall("item"):
        if i.findtext("wp:status", namespaces=NS) != "publish" or \
                i.findtext("wp:post_type", namespaces=NS) not in ("post", "page"):
            continue
        body = i.findtext("content:encoded", namespaces=NS) or ""
        for u in re.findall(r'<img [^>]*src="([^"]+)"', body):
            u = html.unescape(u)
            if u.startswith("http") and not OWN.match(u) and u not in urls:
                urls.append(u)

    mapping = json.loads(MAP.read_text()) if MAP.exists() else {}
    missing = []
    for u in urls:
        if u in mapping and Path("static" + mapping[u]).exists():
            print(f"have  {mapping[u]}")
            continue
        data = ctype = None
        for candidate in (u, f"https://web.archive.org/web/2022id_/{u}"):
            try:
                data, ctype = fetch(candidate)
            except OSError as e:
                print(f"  failed {candidate}: {e}")
                continue
            if ctype in EXT:
                print(f"  from {candidate}")
                break
            print(f"  not an image ({ctype}): {candidate}")
            data = None
        if data is None:
            missing.append(u)
            continue
        p = urlparse(u)
        stem = Path(p.path).stem
        local = f"/images/external/{p.netloc}/{stem}{EXT[ctype]}"
        dest = Path("static" + local)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        mapping[u] = local
        print(f"saved {local} ({len(data)} bytes, {ctype})")

    MAP.write_text(json.dumps(mapping, indent=2) + "\n")
    print(f"{len(mapping)} external images mapped in {MAP}")
    if missing:
        print(f"{len(missing)} could not be downloaded:")
        for u in missing:
            print(f"  {u}")
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1])
