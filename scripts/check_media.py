#!/usr/bin/env python3
"""Keep the list of media and pages that posts link to on other sites, and check they still exist.

Usage:
  python3 -I scripts/check_media.py sync [--prune]   update data/media.json from content/
  python3 -I scripts/check_media.py check [--kind video|audio|pdf|page]

Plan: migration/MEDIA-BACKUP.md (step 1 of 5). Uses only the standard library.

data/media.json maps each original URL (without #fragment) to an entry:
  kind        video | audio | pdf | page
  posts       slugs of the pages that link to it
  status      live | down. Set by hand (later by the watcher PR), never by `check`.
              Templates will show the backup copy when it is "down" (step 4).
  serve_copy  true only once the owner has permission to show a copy publicly
Later steps add: copy, sha256, archived, wayback.

sync   scans content/ for video embeds, podcast players and links to other sites. New URLs
       are added (status live, serve_copy false); existing entries keep their fields and get
       their `posts` refreshed. URLs no posts use any more are listed, and removed with
       --prune (never when the entry already has a backup copy). Links in front matter and in
       <!-- comments --> are skipped: visitors don't see them.
check  checks every original (network needed) and prints one line per item:
         ok           it exists
         check        the site refused the checker or the answer is unclear; open it in a browser
         unavailable  it exists but can't be played (Vimeo: "This video isn't available")
         gone         deleted (404 from YouTube/Vimeo, or an error/redirect for files and pages)
       Videos: YouTube and Vimeo oEmbed, then the Vimeo player when oEmbed has no answer.
       Audio and PDF: a one-byte GET, which must return the expected content type.
       Pages: the same rules as scripts/check_links.py --external.
       Exits 1 if any item is unavailable or gone.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I leaves the script dir off sys.path
from check_links import SITE, UA, external_verdict, fetch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "media.json"
CONTENT = ROOT / "content"
OWN_HOSTS = {"monicaespinel.com", "www.monicaespinel.com"}

FRONT_MATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.S)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
SLUG_RE = re.compile(r"^slug:\s*['\"]?([^'\"\n]+)", re.M)
SHORTCODE_RE = re.compile(r"\{\{<\s*([\w-]+)(.*?)>\}\}", re.S)
PARAM_RE = re.compile(r'(\w+)="([^"]*)"')
LINK_RES = [
    re.compile(r"\]\((https?://[^\s)]+)"),        # [text](url "title")
    re.compile(r"<(https?://[^>\s]+)>"),          # <url>
    re.compile(r'(?:href|src)="(https?://[^"]+)"'),  # raw HTML
]
VIDEO_URL = {"vimeo": "https://vimeo.com/{}", "youtube": "https://www.youtube.com/watch?v={}"}
FILE_TYPES = {"audio": ("audio/",), "pdf": ("application/pdf",), "video": ("video/",)}


def kind_of(url):
    u = urlparse(url)
    host, path = u.netloc.lower(), u.path.lower()
    if host.endswith(("youtube.com", "youtu.be", "vimeo.com")):
        return "video"
    if path.endswith(".pdf"):
        return "pdf"
    if path.endswith((".mp3", ".m4a", ".ogg", ".wav")):
        return "audio"
    if path.endswith((".mp4", ".mov", ".webm")):
        return "video"
    return "page"


def scan(content=CONTENT):
    """{url: set of slugs} for every external media item or link in content/."""
    found = {}
    for f in sorted(content.rglob("*.md")):
        text = f.read_text(encoding="utf-8")
        m = SLUG_RE.search(FRONT_MATTER_RE.match(text).group(0)) if FRONT_MATTER_RE.match(text) else None
        slug = m.group(1).strip() if m else f.stem
        body = COMMENT_RE.sub("", FRONT_MATTER_RE.sub("", text, count=1))
        urls = []
        for name, args in SHORTCODE_RE.findall(body):
            p = dict(PARAM_RE.findall(args))
            if name == "video-embed" and p.get("provider") in VIDEO_URL:
                urls.append(VIDEO_URL[p["provider"]].format(p["id"]))
            elif p.get("src", "").startswith("http"):
                urls.append(p["src"])
        for rx in LINK_RES:
            urls += rx.findall(body)
        for url in urls:
            u = urlparse(url)
            if u.netloc.lower() in OWN_HOSTS:
                continue
            found.setdefault(u._replace(fragment="").geturl(), set()).add(slug)
    return found


def load():
    return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}


def save(manifest):
    MANIFEST.parent.mkdir(exist_ok=True)
    MANIFEST.write_text(json.dumps(dict(sorted(manifest.items())), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sync(prune):
    found, manifest = scan(), load()
    added = [u for u in found if u not in manifest]
    for url, slugs in found.items():
        entry = manifest.setdefault(url, {"kind": kind_of(url), "posts": [], "status": "live", "serve_copy": False})
        entry["posts"] = sorted(slugs)
    unused = [u for u in manifest if u not in found]
    for url in unused:
        keep = "copy" in manifest[url]
        print(f"unused{' (has a copy, kept)' if keep else ''}: {url}")
        if prune and not keep:
            del manifest[url]
    save(manifest)
    for url in added:
        print(f"added: {url}")
    kinds = {}
    for e in manifest.values():
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    print(f"{len(manifest)} entries in {MANIFEST.relative_to(ROOT)} (" + ", ".join(f"{k}: {v}" for k, v in sorted(kinds.items())) + ")")


def get(url, extra=None):
    """(status or None, headers or {}, first bytes of the body, error)."""
    headers = {"User-Agent": UA, "Referer": SITE + "/", **(extra or {})}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
            return r.status, r.headers, r.read(4096), None
    except urllib.error.HTTPError as e:
        return e.code, e.headers or {}, e.read(4096) if e.fp else b"", None
    except Exception as e:  # noqa: BLE001 - report any network failure
        return None, {}, b"", str(getattr(e, "reason", e))


def check_video(url):
    host = urlparse(url).netloc
    if "youtube" in host or "youtu.be" in host:
        status, _, _, err = get("https://www.youtube.com/oembed?format=json&url=" + quote(url, safe=""))
        if status == 200:
            return "ok", "YouTube oEmbed 200"
        if status in (400, 404):
            return "gone", f"YouTube oEmbed {status}"
        if status in (401, 403):
            return "check", f"YouTube oEmbed {status} (private, or embedding turned off)"
        return "check", err or f"YouTube oEmbed {status}"
    if "vimeo" in host:
        vid = urlparse(url).path.strip("/").split("/")[-1]
        status, _, _, err = get("https://vimeo.com/api/oembed.json?url=" + quote(f"https://vimeo.com/{vid}", safe=""))
        if status == 200:
            return "ok", "Vimeo oEmbed 200"
        # oEmbed 404 is also what private or domain-restricted videos get; the player tells them apart.
        pstatus, _, body, perr = get(f"https://player.vimeo.com/video/{vid}")
        if pstatus == 404:
            return "gone", "Vimeo player 404"
        if pstatus == 403 and b"isn't available" in body:
            return "unavailable", "Vimeo player: \"This video isn't available\""
        if pstatus == 200:
            return "ok", "Vimeo player 200"
        return "check", perr or f"Vimeo oEmbed {status}, player {pstatus}"
    return check_file(url, "video")


def check_file(url, kind):
    status, headers, _, err = get(url, {"Range": "bytes=0-0"})
    if status in (200, 206):
        ctype = headers.get("Content-Type", "").split(";")[0].strip().lower()
        if ctype.startswith(FILE_TYPES[kind]):
            return "ok", f"HTTP {status} {ctype}"
        return "gone", f"HTTP {status} but {ctype or 'no content type'} (expected {kind})"
    verdict, note = external_verdict(url, status, url, err or "")
    return ("gone" if verdict in ("broken", "moved") else verdict), note


def check_page(url):
    verdict, note = external_verdict(url, *fetch(url))
    return ("gone" if verdict in ("broken", "moved") else "check" if verdict == "blocked" else verdict), note


def check_one(item):
    url, entry = item
    kind = entry["kind"]
    if kind == "video":
        return check_video(url)
    if kind in FILE_TYPES:
        return check_file(url, kind)
    return check_page(url)


def check(only):
    manifest = load()
    if not manifest:
        sys.exit(f"{MANIFEST.relative_to(ROOT)} is empty or missing: run `check_media.py sync` first")
    items = [(u, e) for u, e in manifest.items() if not only or e["kind"] == only]
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(check_one, items))
    counts, failed = {}, False
    for (url, entry), (verdict, note) in sorted(zip(items, results), key=lambda r: (r[0][1]["kind"], r[0][0])):
        counts[verdict] = counts.get(verdict, 0) + 1
        bad = verdict in ("unavailable", "gone")
        failed |= bad
        flag = "  (manifest says live)" if bad and entry["status"] == "live" else ""
        print(f"{verdict:11} {entry['kind']:5} {url}  {note}{flag}  on {', '.join(entry['posts'])}")
    print("  ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    return 1 if failed else 0


def main(argv):
    cmd = argv[0] if argv else ""
    if cmd == "sync":
        sync("--prune" in argv)
        return 0
    if cmd == "check":
        only = argv[argv.index("--kind") + 1] if "--kind" in argv else None
        return check(only)
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
