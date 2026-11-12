"""Shared helpers for reading the WordPress WXR export.

Used by wp_inventory.py, wp_to_hugo.py, check_inventory.py and fetch_external_images.py.
Scripts run with `python3 -I` (no script directory on sys.path), so each one adds this
directory to sys.path before importing.
"""
import html
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

# Repository root, so paths don't depend on the current directory.
ROOT = Path(__file__).resolve().parent.parent

NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "dc": "http://purl.org/dc/elements/1.1/",
}
SITE_URL_RE = re.compile(r"^https?://(?:www\.)?monicaespinel\.com(?=/)")


def channel(path):
    return ET.parse(path).getroot().find("channel")


def t(el, path):
    """Text of a child element, stripped and HTML-unescaped."""
    return html.unescape((el.findtext(path, namespaces=NS) or "").strip())


def raw(el, path):
    """Text of a child element that holds HTML, stripped but not unescaped."""
    return (el.findtext(path, namespaces=NS) or "").strip()


def meta(item):
    """postmeta as {key: [values]}."""
    out = defaultdict(list)
    for m in item.findall("wp:postmeta", NS):
        out[t(m, "wp:meta_key")].append(t(m, "wp:meta_value"))
    return out


def is_published(item, types=("post", "page")):
    return t(item, "wp:post_type") in types and t(item, "wp:status") == "publish"


def description(m):
    """SEO description from All in One SEO (new key first, then the legacy one).
    Values that are only an AIOSEO smart tag (e.g. "#post_excerpt") are not real text."""
    for key in ("_aioseo_description", "_aioseop_description"):
        for v in m.get(key, []):
            if v and not v.startswith("#"):
                return re.sub(r"\s+", " ", v).strip()
    return ""


def path_of(url):
    """Site-relative path of a URL, keeping any query string."""
    p = urlparse(url)
    return (p.path or "/") + (f"?{p.query}" if p.query else "")
