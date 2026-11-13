# monicaespinel.com

The website of Monica Espinel, curator and writer: [monicaespinel.com](https://monicaespinel.com).

The site is built with [Hugo](https://gohugo.io) from the text files in this repository and hosted on GitHub Pages. Every change merged into `main` is published automatically, usually within about 2 minutes. There is no server or database to look after.

It has been live since 2026-11-12, when it replaced the old WordPress site. The migration is finished. Its history and remaining follow-up items are in [migration/](migration/README.md).

## Where things are

| Path | What's there |
|---|---|
| `content/posts/` | One Markdown file per post. The file name is the post's address: `beats-of-the-sacred-heart.md` → `monicaespinel.com/beats-of-the-sacred-heart/` |
| `content/about.md`, `content/contact.md` | The About and Contact pages |
| `content/categories/`, `content/tags/` | The display names of categories and tags |
| `source/wp-content/uploads/` | Images and files, published at `/wp-content/uploads/` (the same addresses as on WordPress) |
| `hugo.toml` | Site settings: title, description, menu, analytics, contact form |
| `layouts/`, `assets/` | Templates and styles |
| `.github/workflows/pages.yml` | The build and deploy workflow |
| `migration/`, `scripts/` | The WordPress migration (archive) and the URL checks CI still runs |

## Adding a post

Each post is a single text file in `content/posts/`. You can create it on the GitHub website, without installing anything.

1. Open [`content/posts/`](https://github.com/monica-espinel/monica-espinel-site/tree/main/content/posts) on GitHub, then **Add file → Create new file**.
2. Name the file after the post's address, in lowercase with hyphens, ending in `.md`. Example: `ceremonies-of-summer.md`.
3. Paste the template below and fill it in. Write the text of the post under the second `---` line.
4. Click **Commit changes…**, choose **Create a new branch for this commit and start a pull request**, then **Propose changes** and **Create pull request**.
5. Wait for the checks on the pull request to turn green (about 2 minutes). They build the whole site, so a mistake in the file shows up here instead of on the live site.
6. Click **Merge pull request**. The post is live about 2 minutes later.

### Template

```yaml
---
title: "Title of the post"
date: 2026-11-13T10:00:00
slug: title-of-the-post
author: Monica Espinel
categories:
- publications
tags:
- carmen-herrera
- whitney-museum
description: "One or two sentences for search engines and link previews."
image: /wp-content/uploads/2026/11/photo.jpg
image_alt: "What the image shows"
image_caption: "Artist, Title, year. Courtesy …"
---

The text of the post. A [link to the article](https://example.com) and *italics* work like this.
```

### The fields

| Field | Required | Notes |
|---|---|---|
| `title` | Yes | Keep the quotes if the title contains a colon. |
| `date` | Yes | New York time. A date in the future keeps the post hidden until a build runs after that date (any later merge). |
| `slug` | Yes | The address, the same as the file name without `.md`. Never change it after publishing: links to the old address would break. |
| `author` | Yes | `Monica Espinel` |
| `categories` | Yes | One of `exhibitions`, `publications`, `reviews`, `talks`. These are the menu sections. |
| `tags` | No | Lowercase, with hyphens. See [Categories and tags](#categories-and-tags). |
| `description` | Recommended | Shown in Google results and link previews. Without it, the page's search score drops a little. |
| `image` | No | The featured image, shown on the homepage and in link previews. Without it, previews use the site's default image. |
| `image_alt`, `image_caption` | With `image` | `image_alt` describes the image for people who can't see it. `image_caption` is shown under it. |
| `draft: true` | No | Add this line to keep a post off the site. Remove it to publish. |

The homepage shows the first words of each post as a preview. To choose where the preview ends, put `<!--more-->` on its own line in the text.

### Images

Images live in `source/wp-content/uploads/`, in a folder per year and month, as on WordPress: for example `source/wp-content/uploads/2026/11/photo.jpg`, used as `/wp-content/uploads/2026/11/photo.jpg`. The build makes smaller copies for phones and for link previews, so upload the full-size JPEG or PNG. Use lowercase file names without spaces.

On GitHub, open the year folder, then **Add file → Upload files**. To start a new month (or year), drag a *folder* with that name, containing the images, onto the upload page: GitHub creates the folder. Upload the images in the same pull request as the post, or merge them first.

An image inside the text of a post, with an optional caption:

```
{{< figure src="/wp-content/uploads/2026/11/photo.jpg" alt="What the image shows" caption="Artist, Title, year" >}}
```

Several images side by side, as a gallery:

```
{{< gallery >}}
{{< figure src="/wp-content/uploads/2026/11/one.jpg" alt="…" >}}
{{< figure src="/wp-content/uploads/2026/11/two.jpg" alt="…" >}}
{{< /gallery >}}
```

A YouTube or Vimeo video: `{{< video-embed provider="youtube" id="VIDEO_ID" >}}` (the `id` is the part after `v=` in a YouTube address).

### Categories and tags

- **Categories** are fixed: the four menu sections. Adding a new one means changing the menu in `hugo.toml` too.
- **Tags** can be added freely. Each tag gets a page at `/tag/<tag>/`. Reuse an existing tag where one fits: the list is in [`content/tags/`](content/tags/).
- A new tag is displayed from its slug. To give it a proper name, with capitals or accents, add `content/tags/<tag>/_index.md` containing:

```yaml
---
title: An-My Lê
slug: an-my-le
---
```

## Changing or removing a post

- **Fix or update a post:** open its file in `content/posts/` on GitHub, click the pencil icon, edit, and propose the change as above.
- **Hide a post:** add `draft: true` to its fields. The file stays, and you can publish it again later.
- **Delete a post:** delete its file. Its address then shows the "page not found" page. If other sites link to it, prefer hiding it, or ask for a redirect to another page.
- **The About page** is `content/about.md`. The contact form is in `content/contact.md`; its messages go through Formspree to Monica's inbox.

Posts converted from WordPress are edited the same way, directly in their files. Don't re-run the WordPress conversion scripts: they would overwrite these edits (see [migration/](migration/README.md)).

## Working on the site locally

For template or style changes, or to preview posts before proposing them.

### What you need

| Tool | Version | Used for |
|---|---|---|
| Hugo **extended** | **0.164.0** exactly (the same version as CI) | Building the site |
| Python 3 | 3.11 or later | The URL checks in `scripts/` (standard library only) |
| Node.js | Any current LTS | The Pagefind search index (`npx pagefind`) |

#### Installing Hugo 0.164.0 on macOS

For this version, GitHub only publishes a `.pkg` installer for macOS, with no `.tar.gz` download. `brew install hugo` installs the latest version, which may not match CI. To get exactly 0.164.0:

```bash
curl -fLO https://github.com/gohugoio/hugo/releases/download/v0.164.0/hugo_extended_0.164.0_darwin-universal.pkg
```

```bash
curl -fLO https://github.com/gohugoio/hugo/releases/download/v0.164.0/hugo_0.164.0_checksums.txt
```

```bash
grep " hugo_extended_0.164.0_darwin-universal.pkg$" hugo_0.164.0_checksums.txt | shasum -a 256 -c
```

Then either install it system-wide by double-clicking the `.pkg`, or unpack it without installing:

```bash
pkgutil --expand-full hugo_extended_0.164.0_darwin-universal.pkg hugo-pkg && ./hugo-pkg/Payload/hugo version
```

The version output must end in `+extended`.

### Preview

From the repository root, including drafts, at http://localhost:1313:

```bash
hugo server -D
```

The search page (`/search/`) only works after Pagefind has run (see below). `hugo server` doesn't build the search index.

### Checks before pushing

CI ([`.github/workflows/pages.yml`](.github/workflows/pages.yml)) runs these on every pull request, in this order, and fails if any of them fails.

1. The redirect pages for old WordPress addresses are up to date:

```bash
python3 -I scripts/make_redirects.py --check
```

2. Production build:

```bash
hugo --minify --gc
```

3. Every old WordPress address still resolves to a page or a redirect page. New posts are listed as "new pages not in the inventory", which is expected:

```bash
python3 -I scripts/check_urls.py --strict public/ migration/url-inventory.csv
```

4. The search index:

```bash
npx --yes pagefind@latest --site public
```

CI also checks that Pagefind wrote `pagefind-ui.js` and `pagefind-ui.css`, and that it indexed every page the build marked for search (posts and pages, which carry `data-pagefind-body`).

5. No broken links: every internal link, image and `#anchor` on every page. Run it after Pagefind, because the search page loads its files:

```bash
python3 -I scripts/check_links.py public
```

Add `--external` to also fetch every link to other sites. CI doesn't do this, because other sites go down without warning. Run it now and then from a normal internet connection. It lists each external link as broken (an error, or a 4xx/5xx status), moved (it redirects to another site or to a much shorter address, which usually means the page is gone), check (the site refused the script, so open it in a browser), or blocked (it never reached the site). Add `--wayback` to also look up an Internet Archive copy of each broken or moved link. Run it on a production build, not on the output of `hugo server`; the script refuses that one.

Unknown addresses on the live site show `404.html`, which links to the home page and to search.

To run the same address check against the live site, over the network:

```bash
python3 -I scripts/check_live.py
```

## Deployment and settings

- **Deploys:** every push to `main` builds the site, indexes it with Pagefind and deploys it to GitHub Pages. Pull requests run the same build and checks without deploying. If a build fails, nothing is deployed and the live site stays as it was.
- **Domain:** `monicaespinel.com`, with `www` redirecting to it. The custom domain is set in Settings → Pages and in `static/CNAME`. DNS is at GoDaddy. Records are documented in [migration/DNS-CUTOVER.md](migration/DNS-CUTOVER.md).
- **Branch protection on `main`:** changes need a pull request (0 approvals, so a maintainer can merge their own). Force pushes and branch deletion are blocked. Admins can bypass the rules in an emergency.
- **Analytics:** GA4 (`G-ZR270JS8ZG`), counted only on `monicaespinel.com` and its subdomains. On any other host, such as a local preview, the page sets Google's opt-out flag. Don't point a subdomain at a test build: its visits would be counted.
- **Search Console:** verified through a DNS `TXT` record. Keep the `google-site-verification` and `_github-pages-challenge-monica-espinel` `TXT` records.
- **Contact form:** Formspree, endpoint `https://formspree.io/f/xdegodvq`. No email address is published on the site.
- **Dependencies:** the workflow's actions are pinned to commit SHAs. Dependabot (`.github/dependabot.yml`) opens a monthly PR when they need updating.

## Working rules

- Work on a branch and open a pull request; don't push straight to `main`.
- Never commit secrets. The Formspree endpoint and the GA4 measurement ID are public and fine to commit.
- Never commit the WordPress export (`source/*.xml`) or other private files. Some files are deliberately kept out of git; the list is in [migration/](migration/README.md#files-that-are-not-in-git).
