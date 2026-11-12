#!/usr/bin/env python3
"""Phase 1 acceptance check: every URL in the export is in url-inventory.csv,
or is excluded for a stated reason. Exits 1 on any unexplained URL.

Usage: python3 -I scripts/check_inventory.py source/<export>.xml migration/url-inventory.csv
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I leaves the script dir off sys.path
from wxr import channel, path_of, t  # noqa: E402

# Item types whose <link> is not a public page on the WordPress site.
NOT_PUBLIC_TYPES = {
    "nav_menu_item": "menu entry, not a public page",
    "custom_css": "theme CSS object",
    "wp_global_styles": "theme styles object",
}


def main(src, inv):
    listed = {r["old_url"] for r in csv.DictReader(open(inv, encoding="utf-8"))}
    ch = channel(src)
    excluded, missing = defaultdict(list), []
    for i in ch.findall("item"):
        link = t(i, "link")
        if not link.startswith("https://monicaespinel.com"):
            continue
        url = path_of(link)
        if url in listed:
            continue
        typ, status = t(i, "wp:post_type"), t(i, "wp:status")
        if typ in NOT_PUBLIC_TYPES:
            excluded[NOT_PUBLIC_TYPES[typ]].append(url)
        elif status in ("draft", "private", "pending", "future", "trash"):
            excluded[f"{typ} with status {status}, never public"].append(url)
        else:
            missing.append((url, typ, status))

    for reason, urls in excluded.items():
        print(f"excluded ({reason}): {len(urls)}")
    if missing:
        print("MISSING from inventory:")
        for m in missing:
            print("  ", *m)
        sys.exit(1)
    print(f"OK: every public URL in the export is in {inv} ({len(listed)} rows)")


if __name__ == "__main__":
    main(*sys.argv[1:3])
