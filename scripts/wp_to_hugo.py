#!/usr/bin/env python3
"""Phase 2: convert a WordPress WXR export to Hugo content.

Usage: python3 -I scripts/wp_to_hugo.py source/<export>.xml content/

Writes:
  content/posts/<slug>.md          one file per published post
  content/<slug>.md                one file per published page
  content/categories/<slug>/_index.md, content/tags/<slug>/_index.md
                                   term pages, so URLs keep the WordPress slugs
Needs: beautifulsoup4, markdownify, PyYAML (run once locally; output is committed).
"""
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import yaml
from bs4 import BeautifulSoup
from markdownify import markdownify

NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "dc": "http://purl.org/dc/elements/1.1/",
}
SITE_RE = re.compile(r"https?://(?:www\.)?monicaespinel\.com(?=/)")
BLOCK_RE = re.compile(r"<!--\s+(/)?wp:([a-z0-9/-]+)(?:\s+(\{.*?\}))?\s*(/)?-->", re.S)
# Podcast platforms that no longer exist; links removed (owner decision, Phase 2).
DROP_PLATFORMS = {"Google-Podcasts"}  # shut down in 2024
TODOS = []  # (file, message) for the final report


def t(el, path):
    return (el.findtext(path, namespaces=NS) or "").strip()


def meta(item):
    out = defaultdict(list)
    for m in item.findall("wp:postmeta", NS):
        out[t(m, "wp:meta_key")].append(t(m, "wp:meta_value"))
    return out


def rel(url):
    """Make links to the site root-relative so they work on any host."""
    return SITE_RE.sub("", url or "")


# ---------------------------------------------------------------- blocks ---

def parse_blocks(src):
    """Return a list of nodes: ('html', text) or ('block', name, attrs, inner_nodes, inner_html)."""
    nodes, stack, pos = [], [], 0
    root = nodes
    for m in BLOCK_RE.finditer(src):
        closing, name, attrs, selfclose = m.group(1), m.group(2), m.group(3), m.group(4)
        target = stack[-1]["children"] if stack else root
        if m.start() > pos:
            target.append(("html", src[pos:m.start()]))
        pos = m.end()
        if closing:
            if not stack or stack[-1]["name"] != name:
                raise ValueError(f"unbalanced block wp:{name}")
            b = stack.pop()
            parent = stack[-1]["children"] if stack else root
            parent.append(("block", b["name"], b["attrs"], b["children"], src[b["start"]:m.start()]))
        else:
            a = json.loads(attrs) if attrs else {}
            if selfclose:
                target.append(("block", name, a, [], ""))
            else:
                stack.append({"name": name, "attrs": a, "children": [], "start": m.end()})
    if stack:
        raise ValueError(f"unclosed block wp:{stack[-1]['name']}")
    tail = src[pos:]
    if tail.strip():
        root.append(("html", tail))
    return nodes


def md(fragment):
    if not fragment or not fragment.strip():
        return ""
    fragment = rel(fragment).replace(" ", " ").replace("&nbsp;", " ")
    out = markdownify(fragment, heading_style="ATX", bullets="-", strip=["span", "div"],
                      escape_underscores=False, escape_misc=False)
    out = re.sub(r"[ \t]+\n", "\n", out)
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def inline_md(fragment):
    """Markdown for captions: one line, no paragraph breaks."""
    return re.sub(r"\s*\n\s*", " ", md(fragment)).strip()


def sc_attr(v):
    """Quote a shortcode parameter value."""
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


# Local copies of images that posts loaded from other sites (scripts/fetch_external_images.py).
EXTERNAL = json.loads(Path("migration/external-images.json").read_text()) \
    if Path("migration/external-images.json").exists() else {}


def local_copy(src):
    local = EXTERNAL.get(html.unescape(src))
    if local and Path("static" + local).exists():
        return local
    if src.startswith("http") and not SITE_RE.match(src):
        TODOS.append(("(external image)", f"no local copy yet: {src}"))
    return src


def figure_sc(img_src, alt="", link="", caption=""):
    parts = [f"src={sc_attr(rel(local_copy(img_src)))}"]
    if alt:
        parts.append(f"alt={sc_attr(alt)}")
    if link:
        parts.append(f"link={sc_attr(rel(link))}")
    if caption:
        parts.append(f"caption={sc_attr(caption)}")
    return "{{< figure " + " ".join(parts) + " >}}"


def figure_from_html(fig_html):
    soup = BeautifulSoup(fig_html, "html.parser")
    img = soup.find("img")
    if not img:
        return ""
    a = img.find_parent("a")
    cap = soup.find("figcaption")
    return figure_sc(img.get("src", ""), img.get("alt", ""), a.get("href", "") if a else "",
                     inline_md(cap.decode_contents()) if cap else "")


def video_id(url):
    m = re.search(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/))([\w-]{11})", url)
    if m:
        start = re.search(r"[?&#]t=(\d+)", url)
        return "youtube", m.group(1), start.group(1) if start else ""
    m = re.search(r"vimeo\.com/(\d+)", url)
    if m:
        start = re.search(r"#t=([\dhms]+)", url)
        return "vimeo", m.group(1), start.group(1) if start else ""
    return None, None, None


def render(nodes, ctx):
    out = []
    for n in nodes:
        if n[0] == "html":
            text = md(n[1])
            if text:
                out.append(text)
            continue
        _, name, attrs, children, inner = n
        out.append(render_block(name, attrs, children, inner, ctx))
    return "\n\n".join(p for p in out if p)


def render_block(name, attrs, children, inner, ctx):
    if name in ("paragraph", "heading", "list", "list-item", "quote", "html", "freeform", "preformatted", "table"):
        if name == "html":
            ctx.todo(f"raw HTML block converted to Markdown, check rendering: {inner.strip()[:80]!r}")
        return md(inner)
    if name == "image":
        return figure_from_html(inner)
    if name == "gallery":
        soup = BeautifulSoup(inner, "html.parser")
        blocks = [c for c in children if c[0] == "block"]
        if blocks:  # WordPress 5.9+ gallery: nested image blocks
            figs = [render_block(c[1], c[2], c[3], c[4], ctx) for c in blocks]
        else:       # older gallery: <ul><li><figure>…
            figs = [figure_from_html(str(f)) for f in soup.select("li figure")]
        cap = soup.find("figcaption", class_="blocks-gallery-caption")
        head = "{{< gallery" + (f" caption={sc_attr(inline_md(cap.decode_contents()))}" if cap else "") + " >}}"
        return "\n".join([head, *[f for f in figs if f], "{{< /gallery >}}"])
    if name == "file":
        a = BeautifulSoup(inner, "html.parser").find("a")
        href = rel(attrs.get("href") or (a.get("href") if a else ""))
        label = a.get_text(" ", strip=True) if a else href.rsplit("/", 1)[-1]
        return f"[{label}]({href})"
    if name == "embed":
        url = attrs.get("url", "")
        provider, vid, start = video_id(url)
        if provider:
            p = f"provider={sc_attr(provider)} id={sc_attr(vid)}"
            if start:
                p += f" start={sc_attr(start)}"
            return "{{< video-embed " + p + " >}}"
        cap = BeautifulSoup(inner, "html.parser").find("figcaption")
        label = inline_md(cap.decode_contents()) if cap else url
        return f"[{label}]({rel(url)})"
    if name == "video":
        v = BeautifulSoup(inner, "html.parser").find("video")
        return "{{< video src=" + sc_attr(rel(v.get("src", ""))) + " >}}" if v else ""
    if name == "jetpack/podcast-player":
        feed = attrs.get("url", "")
        guids = ", ".join(e.get("guid", "") for e in attrs.get("selectedEpisodes", []))
        ctx.todo(f"Jetpack podcast player (feed {feed}, episode {guids}) replaced by a link to the feed")
        return ("{{/* TODO: the WordPress page embedded a Jetpack podcast player for episode "
                f"{guids}. Replace with the episode's own player embed if wanted. */}}}}\n\n"
                f"[Podcast feed]({feed})").replace("}}}}", "}}")
    if name == "secondline-themes/podcast-subscribe-button":
        links = []
        for b in attrs.get("secondline_psb_repeat_subscribe", []):
            platform = b.get("secondline_psb_subscribe_platform", "")
            if platform in DROP_PLATFORMS:
                continue
            # The plugin only shows the custom label for its "Custom" platform; otherwise it is a placeholder.
            label = (b.get("secondline_psb_custom_link_label") if platform.lower() == "custom" else "") \
                or platform.replace("-", " ")
            if b.get("secondline_psb_subscribe_url"):
                links.append(f"[{label}]({b['secondline_psb_subscribe_url']})")
        return "Listen on: " + " · ".join(links) if links else ""
    if name == "shortcode":
        code = inner.strip()
        if code.startswith("[wpforms"):
            return "{{< contact-form >}}"
        ctx.todo(f"unknown shortcode dropped: {code[:80]}")
        return "{{/* TODO: WordPress shortcode not converted: " + code.replace("*/", "") + " */}}"
    if name == "more":
        return "<!--more-->"
    if name in ("group", "columns", "column", "cover"):
        return render(children, ctx) if children else md(inner)
    if name == "separator":
        return "---"
    if name == "spacer":
        return ""
    ctx.todo(f"unhandled block wp:{name}, converted as plain HTML")
    return md(inner)


# --------------------------------------------------------------- content ---

class Ctx:
    def __init__(self, path):
        self.path = path

    def todo(self, msg):
        TODOS.append((self.path, msg))


def description(m):
    for key in ("_aioseo_description", "_aioseop_description"):
        for v in m.get(key, []):
            if v and not v.startswith("#"):
                return re.sub(r"\s+", " ", html.unescape(v)).strip()
    return ""


def dump(front, body):
    fm = yaml.safe_dump(front, allow_unicode=True, sort_keys=False, width=1000).strip()
    return f"---\n{fm}\n---\n\n{body.strip()}\n"


def main(src, out_dir):
    out = Path(out_dir)
    ch = ET.parse(src).getroot().find("channel")
    items = ch.findall("item")
    by_id = {t(i, "wp:post_id"): i for i in items}
    authors = {t(a, "wp:author_login"): t(a, "wp:author_display_name") for a in ch.findall("wp:author", NS)}
    used = {"category": set(), "post_tag": set()}
    written = []

    for i in items:
        typ, status = t(i, "wp:post_type"), t(i, "wp:status")
        if typ not in ("post", "page") or status != "publish":
            continue
        m = meta(i)
        slug = t(i, "wp:post_name")
        path = out / ("posts" if typ == "post" else "") / f"{slug}.md"
        ctx = Ctx(str(path))
        front = {
            "title": html.unescape(t(i, "title")),
            "date": t(i, "wp:post_date").replace(" ", "T"),
            "lastmod": t(i, "wp:post_modified").replace(" ", "T"),
            "slug": slug,
            "author": authors.get(t(i, "dc:creator"), t(i, "dc:creator")),
        }
        if typ == "post":
            cats = [c.get("nicename") for c in i.findall("category") if c.get("domain") == "category"]
            tags = [c.get("nicename") for c in i.findall("category") if c.get("domain") == "post_tag"]
            used["category"].update(cats)
            used["post_tag"].update(tags)
            front["categories"] = cats
            if tags:
                front["tags"] = tags
        desc = description(m)
        if desc:
            front["description"] = desc
        aliases = sorted({f"/{o}/" for o in m.get("_wp_old_slug", []) if o and o != slug})
        if aliases:
            front["aliases"] = aliases
        thumb = by_id.get((m.get("_thumbnail_id") or [""])[0])
        if thumb is not None:
            tm = meta(thumb)
            front["image"] = "/wp-content/uploads/" + tm["_wp_attached_file"][0]
            alt = (tm.get("_wp_attachment_image_alt") or [""])[0]
            cap = inline_md(t(thumb, "excerpt:encoded"))
            if alt:
                front["image_alt"] = alt
            if cap:
                front["image_caption"] = cap
        excerpt = t(i, "excerpt:encoded")
        if excerpt:
            front["summary"] = inline_md(excerpt)
        front["wordpress_id"] = int(t(i, "wp:post_id"))

        body = render(parse_blocks(i.findtext("content:encoded", namespaces=NS) or ""), ctx)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dump(front, body), encoding="utf-8")
        written.append(path)

    # Term pages: keep WordPress slugs as URL keys, names as titles.
    terms = [("category", "categories", "wp:category", "wp:category_nicename", "wp:cat_name", "wp:category_description"),
             ("post_tag", "tags", "wp:tag", "wp:tag_slug", "wp:tag_name", "wp:tag_description")]
    for domain, section, tag, slug_el, name_el, desc_el in terms:
        for el in ch.findall(tag, NS):
            slug = t(el, slug_el)
            if slug not in used[domain]:
                continue  # empty terms redirect (Phase 4)
            front = {"title": html.unescape(t(el, name_el)), "slug": slug}
            if t(el, desc_el):
                front["description"] = html.unescape(t(el, desc_el))
            p = out / section / slug / "_index.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(dump(front, ""), encoding="utf-8")
            written.append(p)

    print(f"{len(written)} files written under {out}/")
    for f, msg in TODOS:
        print(f"TODO {f}: {msg}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
