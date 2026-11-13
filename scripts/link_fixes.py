#!/usr/bin/env python3
"""Replace or remove links to pages that no longer exist on other sites.

Usage: python3 -I scripts/link_fixes.py [content/]

scripts/wp_to_hugo.py applies FIXES to every page it writes, so a re-run of the conversion
keeps them. Running this file applies them to the committed content/ directly.
Found with scripts/check_links.py --external --wayback (2026-11-13). Each replacement was
checked to load, and to be the same page or file, before it was added here.
Default for a dead link: the page's new address on the same site, else the Internet
Archive copy, else the link is removed and the text kept.
"""
import sys
from pathlib import Path

WAYBACK = "https://web.archive.org/web/{}im_/https://brooklynrail.org/media/files/{}"

# (old text, new text). Exact text as wp_to_hugo.py writes it; "" removes it.
FIXES = [
    # ISLAA moved its bookshop pages under /publications/ (same publication, Vistas 8).
    ("https://islaa.org/bookshop/vistas-8", "https://islaa.org/publications/vistas-8/"),
    # The Podbean episode page redirects to Podbean's "/freeze" page (account frozen); the
    # audio file still works. Apple Podcasts has the same episode, "Duet of Displacement".
    ('link="https://parcharte.podbean.com/e/duet_of_displacement/"',
     'link="https://podcasts.apple.com/us/podcast/parcharte/id1602470370?i=1000546394552"'),
    # Deutsche Bank removed the exhibition page (404, no archive copy). The catalogue PDF
    # on the next line of the post covers the same exhibition.
    ('More information: [https://www.db.com/us/content/en/1108.html]'
     '(https://www.db.com/us/content/en/1108.html "https://www.db.com/us/content/en/1108.html")\n\n', ""),
    # The Vimeo video was deleted (player and oEmbed both 404, no archive copy).
    ('{{< video-embed provider="vimeo" id="468397255" >}}', ""),
    # Brooklyn Rail speaker photos: the files now redirect to /contributors/. Use the
    # Internet Archive copies (snapshot status 200) until local copies are stored
    # (scripts/fetch_external_images.py, which wins: the old URL is then gone from the text).
    ("https://brooklynrail.org/media/files/ala_8023_headshot-1-.jpg?nf_resize=fit&w=250",
     WAYBACK.format("20230301221224", "ala_8023_headshot-1-.jpg?nf_resize=fit&w=250")),
    ("https://brooklynrail.org/media/files/monicaespinel.jpeg?nf_resize=fit&w=250",
     WAYBACK.format("20230212125247", "monicaespinel.jpeg?nf_resize=fit&w=250")),
    ("https://brooklynrail.org/media/files/portrait-raphael.jpg?nf_resize=fit&w=250",
     WAYBACK.format("20211102015301", "portrait-raphael.jpg?nf_resize=fit&w=250")),
    ("https://brooklynrail.org/media/files/tyhe-cooper.jpeg?nf_resize=smartcrop&w=130&h=130",
     WAYBACK.format("20220302205400", "tyhe-cooper.jpeg?nf_resize=smartcrop&w=130&h=130")),
    # No archive copy of Tony Bechara's photo: drop the image, keep the bio.
    ('{{< figure src="https://brooklynrail.org/media/files/tonybechara.jpeg?nf_resize=fit&w=250"'
     ' alt="A photograph of Tony Bechara" >}}\n\n', ""),
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
