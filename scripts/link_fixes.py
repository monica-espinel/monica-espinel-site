#!/usr/bin/env python3
"""Replace or remove links to pages that no longer exist on other sites.

Usage: python3 -I scripts/link_fixes.py [content/]

scripts/wp_to_hugo.py applies FIXES to every page it writes, so a re-run of the conversion
keeps them. Running this file applies them to the committed content/ directly.
Found with scripts/check_links.py --external --wayback (2026-11-13). Each replacement was
checked to load, and to be the same page or file, before it was added here.
Default for a dead link: the page's new address on the same site, else the Internet
Archive copy, else the link is removed and the text kept.
Images other sites removed are stored instead: migration/external-images.json maps them to
local copies (the Brooklyn Rail speaker photos). The Parcharte episode-page link is dropped
by wp_to_hugo.py itself (owner decision, 2026-11-13).
"""
import sys
from pathlib import Path

# (old text, new text). Exact text as wp_to_hugo.py writes it; "" removes it.
FIXES = [
    # ISLAA moved its bookshop pages under /publications/ (same publication, Vistas 8).
    ("https://islaa.org/bookshop/vistas-8", "https://islaa.org/publications/vistas-8/"),
    # Deutsche Bank removed the exhibition page (404, no archive copy). The catalogue PDF
    # on the next line of the post covers the same exhibition.
    ('More information: [https://www.db.com/us/content/en/1108.html]'
     '(https://www.db.com/us/content/en/1108.html "https://www.db.com/us/content/en/1108.html")\n\n', ""),
]


def apply(text):
    """Return text with every fix applied, and the list of fixes that matched."""
    used = []
    for old, new in FIXES:
        if old in text:
            text = text.replace(old, new)
            used.append(old)
    return text, used


def main(argv):
    root = Path(argv[0] if argv else "content")
    used = set()
    for f in sorted(root.rglob("*.md")):
        text = f.read_text(encoding="utf-8")
        new, hits = apply(text)
        used.update(hits)
        if new != text:
            f.write_text(new, encoding="utf-8")
            print(f"fixed {f} ({len(hits)})")
    for old, _ in FIXES:
        if old not in used:
            print(f"not found (already fixed?): {old[:90]}")


if __name__ == "__main__":
    main(sys.argv[1:])
