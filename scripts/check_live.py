#!/usr/bin/env python3
"""Phase 7: check every URL in migration/url-inventory.csv against the live site.

Usage: python3 -I scripts/check_live.py [https://monicaespinel.com] [migration/url-inventory.csv]

For each inventory row (rows marked "unsupported" are skipped):
  keep            the URL returns 200 and is a real page (no meta refresh)
  alias/redirect  the URL returns 200 with a meta refresh to the row's target,
                  and that target itself returns 200
Also checks that http:// redirects to https:// and www to the apex.
Exits 1 on any failure. Uses only the standard library.
"""
import csv
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, urljoin

REFRESH_RE = re.compile(r'<meta[^>]+http-equiv=["\']?refresh["\']?[^>]+url=([^"\'>]+)', re.I)
UA = "monicaespinel-site-check/1.0"


def fetch(url):
    """Return (status, final_url, first 8 KB of body) following redirects."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status, r.geturl(), r.read(8192).decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, url, ""
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == 2:
                return None, url, str(e)
            time.sleep(2)


def refresh_target(body):
    m = REFRESH_RE.search(body)
    if not m:
        return None
    return re.sub(r"^https?://[^/]+", "", m.group(1).strip())


def norm(path):
    return path.rstrip("/") or "/"


def check_row(base, r):
    url, action, target = r["old_url"], r["action"], r["target"]
    full = base + quote(url, safe="/%:?=&#+")
    status, final, body = fetch(full)
    if status != 200:
        return url, f"HTTP {status}" + (f" ({body})" if status is None else "")
    dest = refresh_target(body)
    if action == "keep":
        return (url, f"expected a page, found a redirect to {dest}") if dest else (url, None)
    if not dest:
        return url, "expected a redirect page, found a normal page"
    if norm(dest) != norm(target):
        return url, f"redirects to {dest}, expected {target}"
    t_status, _, t_body = fetch(urljoin(full, quote(dest, safe="/%:?=&#+")))
    if t_status != 200:
        return url, f"target {dest} returns HTTP {t_status}"
    if refresh_target(t_body):
        return url, f"target {dest} is itself a redirect page"
    return url, None


def check_hosts(base):
    host = base.split("://", 1)[1]
    fails = []
    for start in (f"http://{host}/", f"http://www.{host}/", f"https://www.{host}/"):
        status, final, _ = fetch(start)
        if status != 200 or final.rstrip("/") != base.rstrip("/"):
            fails.append((start, f"ends at {final} (HTTP {status}), expected {base}/"))
    return fails


def main(argv):
    base = (argv[0] if argv else "https://monicaespinel.com").rstrip("/")
    inv = argv[1] if len(argv) > 1 else "migration/url-inventory.csv"
    rows = [r for r in csv.DictReader(open(inv, encoding="utf-8")) if r["action"] != "unsupported"]

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda r: check_row(base, r), rows))
    fails = [(u, msg) for u, msg in results if msg] + check_hosts(base)

    counts = {}
    for r in rows:
        counts[r["action"]] = counts.get(r["action"], 0) + 1
    print(f"Checked {len(rows)} inventory URLs on {base} " +
          ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) + ", plus http/www redirects")
    for u, msg in fails:
        print(f"FAIL {u}: {msg}")
    print("OK: every URL resolves" if not fails else f"{len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
