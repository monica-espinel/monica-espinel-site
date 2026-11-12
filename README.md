# monicaespinel.com

A static rebuild of [monicaespinel.com](https://monicaespinel.com), Monica Espinel's blog and portfolio. It replaces the old WordPress site. The site is built with Hugo and will be hosted on GitHub Pages. The migration plan and its phases are in [CLAUDE.md](CLAUDE.md), and progress notes are in [migration/PLAN.md](migration/PLAN.md).

WordPress stays live until the cutover is verified. Nothing in this repo changes it.

## What you need

| Tool | Version | Used for |
|---|---|---|
| Hugo **extended** | **0.164.0** exactly (the same version as CI) | Building the site |
| Python 3 | Developed with 3.13 | Migration scripts in `scripts/` |
| Python packages | `beautifulsoup4`, `markdownify`, `PyYAML` | Only `wp_to_hugo.py` needs these |
| Node.js | Any current LTS | The Pagefind search index (`npx pagefind`) |

### Installing Hugo 0.164.0 on macOS

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

Then do one of these:

- Install it system-wide by double-clicking the `.pkg`.
- Unpack it without installing:

```bash
pkgutil --expand-full hugo_extended_0.164.0_darwin-universal.pkg hugo-pkg && ./hugo-pkg/Payload/hugo version
```

The version output must end in `+extended`.

## Files that are not in git

Some source files are deliberately kept out of the repository (see [.gitignore](.gitignore)). Get them before you run the migration scripts.

| Path | What it is | Why it's not committed | How to get it |
|---|---|---|---|
| `source/*.xml` | WordPress export (WXR) | Contains 3 unpublished drafts, 2 private pages, author emails and WordPress logins | WordPress admin → Tools → Export → All content. Save it in `source/`; any file name works. |
| `source/wp-content/uploads/aioseo/`, `aioseo-logs/` | SEO plugin dictionaries and bot-blocker logs | The logs contain visitor IP addresses, and none of it is site content | Not needed |
| `source/wp-content/uploads/wpforms/` | Forms plugin cache | Plugin data, not site content | Not needed |
| `source/wp-content/uploads/2026/01/image*` | Images used only by the unpublished draft "Homo Rodans" | Unpublished work | Not needed. If the post is ever published, remove the ignore rule and the exclude in `hugo.toml`. |

You only need the export to **re-run the conversion**. A normal site build doesn't need it, because the converted `content/` is committed.

Everything else in `source/wp-content/uploads/` **is** committed. `hugo.toml` mounts that folder at `/wp-content/uploads/` so old image links keep working. Don't move it into `static/`.

## Everyday work

Run these from the repository root.

Preview locally at http://localhost:1313:

```bash
hugo server
```

Production build plus search index (this matches what CI will run):

```bash
hugo --minify && npx --yes pagefind@latest --site public
```

Check that every old WordPress URL resolves to a page or a redirect page:

```bash
python3 -I scripts/check_urls.py --strict public/ migration/url-inventory.csv
```

The search page (`/search/`) only works after Pagefind has run. `hugo server` doesn't build the search index.

## Re-running the migration

This is only needed if the WordPress content changes before cutover. Export again into `source/`, then:

```bash
python3 -m pip install beautifulsoup4 markdownify PyYAML
```

```bash
python3 -I scripts/wp_inventory.py source/monicaespinel.WordPress.2026-11-11.xml migration/url-inventory.csv
```

```bash
python3 -I scripts/check_inventory.py source/monicaespinel.WordPress.2026-11-11.xml migration/url-inventory.csv
```

```bash
python3 -I scripts/wp_to_hugo.py source/monicaespinel.WordPress.2026-11-11.xml content/
```

```bash
python3 -I scripts/fetch_external_images.py source/monicaespinel.WordPress.2026-11-11.xml
```

```bash
python3 -I scripts/make_redirects.py
```

Replace the file name with the name of your new export. Commit the regenerated `content/`, `migration/` and `static/` output; never commit the export.

## Repository settings

The repo is **private**, and the `monica-espinel` organization is on GitHub's **Free** plan. On that plan, a private repo can't use:

- **GitHub Pages**: Settings → Pages → Source: GitHub Actions returns "Your current plan does not support GitHub Pages for this repository".
- **Branch protection and rulesets**: these return "Upgrade to GitHub Pro or make this repository public".

Before Phase 5 (deployment), one of these has to change:

1. **Make the repo public.** This is free and matches the plan in CLAUDE.md. The private files above are already untracked. Earlier commits (`e9d72af`, `59dbe88`) still contain them, which was judged acceptable.
2. **Upgrade the organization** to a paid plan and keep the repo private.

Once either is done:

- Set Settings → Pages → Build and deployment → Source to **GitHub Actions**.
- Protect `main`: require a pull request, with 0 approvals so a single maintainer can merge, and block force pushes and deletion.

## Working rules

- Work on a branch and open a pull request; don't push straight to `main`.
- Commit in small steps.
- Never commit secrets. The Formspree endpoint and the GA4 measurement ID are public and fine to commit.
