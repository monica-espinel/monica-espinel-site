#!/usr/bin/env python3
"""Check every link in the built site (public/) for broken targets.

Usage: python3 -I scripts/check_links.py [--external [--wayback]] [public/]

Run it on a production build (hugo --minify --gc, then Pagefind), not on the output of
`hugo server`: that one has live-reload code and localhost addresses, so it is refused.

Internal (always): every href, src, srcset, form action and og:/twitter: image on every
  HTML page must point to a file in public/, and a #fragment must match an id on the
  target page. Links to monicaespinel.com (apex or www) count as internal.
External (--external, needs network): every other http(s) URL is fetched. It is reported
  as broken on an error or 4xx/5xx status, and as "moved" when it redirects to a different
  host or to a much shorter path (often a sign the page is gone and the site sends
  visitors to a generic page, as brooklynrail.org/media/files/... -> /contributors/ does).
  Redirects within the same site (a CDN subdomain, http -> https) are fine.
  "check" means the site refused the checker (401/403/429, dropped connection): many sites
  block scripts, so open those in a browser. "blocked" means the request never reached the
  site (network policy, DNS); check those from another machine. Requests send the site as
  Referer, so a Vimeo video that may only be embedded on monicaespinel.com is tested as there.
  --wayback looks up the latest Internet Archive copy of each broken or moved link, the
  usual replacement when the original page is gone.

Run after Pagefind (the search page loads /pagefind/ files). Exits 1 if any internal link
is broken, or, with --external, if any external link is broken or moved.
Unknown URLs on the live site get public/404.html, which links to home and search.
"""
import json
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlparse

SITE = "https://monicaespinel.com"
OWN_HOSTS = {"monicaespinel.com", "www.monicaespinel.com"}
SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:")
# Fetched at runtime with a page-specific query; not a link a visitor follows.
# The Formspree endpoint only accepts form posts, so a plain request gets 400 even when it works.
SKIP_EXTERNAL = ("https://www.googletagmanager.com/gtag/js", "https://formspree.io/")
UA = "Mozilla/5.0 (compatible; monicaespinel-link-check/1.0)"


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for k in ("id", "name"):
            if a.get(k) and (k == "id" or tag == "a"):
                self.ids.add(a[k])
        for k in ("href", "src", "action", "poster"):
            if a.get(k):
                self.links.append(a[k])
        if a.get("srcset"):
            self.links += [p.strip().split()[0] for p in a["srcset"].split(",") if p.strip()]
        prop = a.get("property") or a.get("name") or ""
        if tag == "meta" and prop in ("og:image", "og:image:url", "og:image:secure_url", "twitter:image") and a.get("content"):
            self.links.append(a["content"])


def parse(file):
    p = Page()
    p.feed(file.read_text(encoding="utf-8", errors="replace"))
    return p


def target_file(public, path):
    f = public / unquote(path).lstrip("/")
    return f / "index.html" if f.is_dir() else f


def fetch(url):
    """Return (status or None, final URL, error)."""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*", "Referer": SITE + "/"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.geturl(), None
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405, 501):
                continue  # some sites refuse HEAD; retry with GET
            return e.code, e.geturl() or url, None
        except Exception as e:  # noqa: BLE001 - report any network failure
            return None, url, str(getattr(e, "reason", e))
    return None, url, "no response"


def external_verdict(url, status, final, err):
    if status is None:
        blocked = any(s in err for s in ("Tunnel", "403", "Name or service", "ENOTFOUND", "nodename"))
        if blocked:
            return "blocked", err
        refused = any(s in err for s in ("closed connection", "reset", "timed out"))
        return ("check" if refused else "broken"), err
    if status in (401, 403, 429):
        return "check", f"HTTP {status} (refused the checker; open it in a browser)"
    if status >= 400:
        return "broken", f"HTTP {status}"
    a, b = urlparse(url), urlparse(final)
    site = lambda h: ".".join(h.lower().split(":")[0].split(".")[-2:])  # noqa: E731
    if site(a.netloc) != site(b.netloc):
        return "moved", f"-> {final}"
    if len(b.path.strip("/")) < len(a.path.strip("/")) / 2:
        return "moved", f"-> {final}"
    return "ok", "" if final == url else f"-> {final}"


def wayback(url):
    """Latest Internet Archive snapshot of url, or None."""
    api = "https://archive.org/wayback/available?url=" + quote(url, safe="")
    try:
        with urllib.request.urlopen(urllib.request.Request(api, headers={"User-Agent": UA}), timeout=30) as r:
            snap = json.load(r).get("archived_snapshots", {}).get("closest") or {}
        return snap.get("url") if snap.get("available") else None
    except Exception:  # noqa: BLE001
        return None


def main(argv):
    external = "--external" in argv
    use_wayback = "--wayback" in argv
    args = [a for a in argv if not a.startswith("--")]
    public = Path(args[0] if args else "public")
    if not (public / "index.html").exists():
        sys.exit(f"{public}/index.html not found: build the site first (hugo --minify --gc)")
    home = (public / "index.html").read_text(encoding="utf-8", errors="replace")
    if "livereload.js" in home or "localhost:1313" in home:
        sys.exit(f"{public}/ is a `hugo server` build (live reload, localhost links). Rebuild it with\n"
                 "  rm -rf public && hugo --minify --gc && npx --yes pagefind@latest --site public\n"
                 "and run this again.")

    pages = {f: parse(f) for f in public.rglob("*.html")}
    ids = {f: p.ids for f, p in pages.items()}
    broken, ext = [], {}
    for f, p in pages.items():
        here = "/" + f.relative_to(public).as_posix()
        for link in p.links:
            link = link.strip()
            if not link or link.startswith(SKIP_SCHEMES):
                continue
            u = urlparse(urljoin(SITE + here, link))
            if u.netloc not in OWN_HOSTS:
                if u.scheme in ("http", "https"):
                    ext.setdefault(u._replace(fragment="").geturl(), set()).add(here)
                continue
            t = target_file(public, u.path)
            if not t.exists():
                broken.append((here, link, "no such file"))
            elif u.fragment and t.suffix == ".html":
                if t not in ids:
                    ids[t] = parse(t).ids
                if unquote(u.fragment) not in ids[t]:
                    broken.append((here, link, f"no id '{u.fragment}' on {u.path}"))

    print(f"pages: {len(pages)}  internal broken: {len(broken)}  external URLs: {len(ext)}")
    for here, link, why in sorted(set(broken)):
        print(f"  BROKEN {link}  on {here}  ({why})")
    failed = bool(broken)

    if external:
        urls = sorted(u for u in ext if not u.startswith(SKIP_EXTERNAL))
        with ThreadPoolExecutor(8) as pool:
            results = list(pool.map(fetch, urls))
        counts = {}
        for url, (status, final, err) in zip(urls, results):
            verdict, note = external_verdict(url, status, final, err)
            counts[verdict] = counts.get(verdict, 0) + 1
            if verdict != "ok":
                print(f"  {verdict.upper():8} {url}  {note}  on {', '.join(sorted(ext[url]))}")
                if use_wayback and verdict in ("broken", "moved"):
                    print(f"           archive copy: {wayback(url) or 'none found'}")
            failed |= verdict in ("broken", "moved")
        print("external: " + "  ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
