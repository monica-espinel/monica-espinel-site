#!/usr/bin/env python3
"""Compare the built site (public/) with migration/url-inventory.csv.

Usage: python3 -I scripts/check_urls.py [--strict] [public/] [migration/url-inventory.csv]

For each inventory row:
  keep      the URL must be a real page (not a redirect page)
  alias     the URL must be a redirect page, and its target must exist
  redirect  the URL must be a redirect page to the row's target (Phase 4)
Rows still waiting for a later phase (feeds: Phase 3, redirect pages: Phase 4) are
reported as pending. With --strict, pending rows count as mismatches.
Exits 1 if there is any mismatch.
"""
import csv
import re
import sys
from pathlib import Path
from urllib.parse import unquote

REFRESH_RE = re.compile(r'<meta[^>]+http-equiv=["\']?refresh["\']?[^>]+url=([^"\'>]+)', re.I)


def url_to_file(public, url):
    path = unquote(url.split("?")[0].split("#")[0]).lstrip("/")
    p = public / path
    if url.endswith("/") or not Path(path).suffix:
        p = p / "index.html"
    return p


def redirect_target(file):
    try:
        text = file.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return None
    m = REFRESH_RE.search(text)
    if not m:
        return None
    return re.sub(r"^https?://[^/]+", "", m.group(1).strip())


def main(argv):
    strict = "--strict" in argv
    args = [a for a in argv if not a.startswith("--")]
    public = Path(args[0] if args else "public")
    inv = Path(args[1] if len(args) > 1 else "migration/url-inventory.csv")
    rows = list(csv.DictReader(inv.open(encoding="utf-8")))

    mismatches, pending, ok = [], [], 0
    for r in rows:
        url, action, target, typ = r["old_url"], r["action"], r["target"], r["type"]
        if action == "unsupported":
            continue
        f = url_to_file(public, url)
        exists = f.exists()
        dest = redirect_target(f) if exists and f.suffix == ".html" else None

        if action == "keep":
            if not exists:
                mismatches.append((url, "missing page"))
            elif dest:
                mismatches.append((url, f"expected a page, found a redirect to {dest}"))
            else:
                ok += 1
            continue

        later = "Phase 3 (feeds)" if typ == "feed" else "Phase 4 (redirect pages)"
        if not exists:
            (mismatches if strict else pending).append((url, f"no file yet, {later}"))
        elif not dest:
            mismatches.append((url, "expected a redirect page, found a normal page"))
        elif dest.rstrip("/") != target.rstrip("/"):
            if typ == "feed" and not strict and action == "alias":
                pending.append((url, f"redirects to {dest}, should be {target}: {later}"))
            else:
                mismatches.append((url, f"redirects to {dest}, expected {target}"))
        elif not url_to_file(public, target).exists():
            mismatches.append((url, f"redirect target {target} does not exist"))
        else:
            ok += 1

    listed = {r["old_url"] for r in rows}
    extra = sorted(
        "/" + str(p.parent.relative_to(public)).replace(".", "").strip("/") + ("/" if p.parent != public else "")
        for p in public.rglob("index.html")
        if "/" + str(p.parent.relative_to(public)).replace(".", "").strip("/") + "/" not in listed
        and p.parent != public and not redirect_target(p)
    )

    print(f"inventory rows: {len(rows)}  ok: {ok}  pending: {len(pending)}  mismatches: {len(mismatches)}")
    by_reason = {}
    for url, why in pending:
        by_reason.setdefault(why.split(": ")[-1] if ":" in why else why, []).append(url)
    for why, urls in by_reason.items():
        print(f"  pending, {why}: {len(urls)}")
    if extra:
        print(f"new pages not in the inventory (fine if intended): {', '.join(extra)}")
    for url, why in mismatches:
        print(f"MISMATCH {url}: {why}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
