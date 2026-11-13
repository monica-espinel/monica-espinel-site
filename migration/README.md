# Migration from WordPress (archive)

monicaespinel.com moved from WordPress to this Hugo site on **2026-11-12**. The migration is finished. This folder keeps the record of how it was done, and the few follow-up items that are still open. Day-to-day work on the site is described in the main [README](../README.md).

The original brief, with its seven phases, is [CLAUDE.md](../CLAUDE.md) at the repository root.

## What's in this folder

| File | What it is |
|---|---|
| [PLAN.md](PLAN.md) | The migration plan, what the WordPress export contained, decisions made with the owner, and the results of each phase |
| [DNS-CUTOVER.md](DNS-CUTOVER.md) | The DNS cutover checklist (Phase 6): moving DNS from Bluehost to GoDaddy, pointing the domain to GitHub Pages, rollback values |
| [godaddy-cutover.txt](godaddy-cutover.txt) | The DNS records entered at GoDaddy |
| [POST-LAUNCH.md](POST-LAUNCH.md) | The post-launch checks (Phase 7) and their results |
| [url-inventory.csv](url-inventory.csv) | Every URL of the old WordPress site, and what it maps to now. **CI reads this file**: don't move or rename it. |
| [generated-content.txt](generated-content.txt) | The list of files in `content/` that `scripts/wp_to_hugo.py` generated. The script uses it to delete pages that are no longer in the export. |
| [external-images.json](external-images.json) | Images that posts loaded from other sites, mapped to the local copies in `static/images/` (for example the Brooklyn Rail speaker photos, restored from the Wayback Machine) |
| [screenshots/](screenshots/) | Screenshots taken during Phases 2 and 3 |

## Status

All seven phases are done. On 2026-11-13, `scripts/check_live.py` checked all 405 old WordPress URLs on the live domain, and every one returned its page or a redirect page.

Still open:

- [ ] **Search Console coverage**, once a week until 2026-12-10. The table is in [POST-LAUNCH.md](POST-LAUNCH.md#7-search-console-coverage-weekly-for-four-weeks-owner).
- [ ] **Raise the DNS TTL** of `@` (`A` and `AAAA`) and `www` at GoDaddy from 600 to 3600. They were still at 600 on 2026-11-13.
- [ ] **Keep WordPress (Bluehost) running until at least 2026-12-12.** Before cancelling it, read "Before cancelling WordPress" in [DNS-CUTOVER.md](DNS-CUTOVER.md).
- [ ] **Three questions defaults were applied for, but never confirmed** (see "Open questions for the owner" in [PLAN.md](PLAN.md)): the nav dropdowns, pruning unused image sizes, and where attachment pages redirect.

## Files that are not in git

Some source files are deliberately kept out of the repository (see [.gitignore](../.gitignore) and the mount excludes in [hugo.toml](../hugo.toml)).

| Path | What it is | Why it's not committed | How to get it |
|---|---|---|---|
| `source/*.xml` | WordPress export (WXR) | Contains 3 unpublished drafts, 2 private pages, author emails and WordPress logins | WordPress admin → Tools → Export → All content. Save it in `source/`; any file name works. |
| `source/wp-content/uploads/aioseo/`, `aioseo-logs/` | SEO plugin dictionaries and bot-blocker logs | The logs contain visitor IP addresses, and none of it is site content | Not needed |
| `source/wp-content/uploads/wpforms/` | Forms plugin cache | Plugin data, not site content | Not needed |
| `source/wp-content/uploads/2026/01/image*` | Images used only by the unpublished draft "Homo Rodans" | Unpublished work | Not needed. If the post is ever published, remove the ignore rule and the exclude in `hugo.toml`. |

The export is only needed to re-run the conversion. A normal build doesn't need it, because the converted `content/` is committed. **Never commit the export**: before committing, check that `git status` shows no `source/*.xml`.

## Re-running the conversion

You shouldn't need to. Since the cutover, posts are edited directly in `content/`. Re-running `scripts/wp_to_hugo.py` regenerates every migrated post from the export and **overwrites any edits made since**. New posts are safe, because they aren't in `generated-content.txt`.

If it's ever needed (for example to recover a page from WordPress), the Python packages and the commands are:

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

Replace the file name with the name of your export. Review the diff of `content/` carefully, then commit the regenerated `content/`, `migration/` and `static/` output.

### The scripts

| Script | What it does |
|---|---|
| `scripts/wxr.py` | Shared code for reading the WordPress export |
| `scripts/wp_inventory.py` | Writes `url-inventory.csv` from the export |
| `scripts/check_inventory.py` | Checks the inventory lists every URL in the export |
| `scripts/wp_to_hugo.py` | Converts posts, pages, categories and tags into `content/` |
| `scripts/fetch_external_images.py` | Downloads images that posts loaded from other sites |
| `scripts/make_redirects.py` | Writes the redirect pages under `static/` for old URLs with no matching page. Run with `--check` in CI. |
| `scripts/check_urls.py` | Checks that a build (`public/`) has a page or redirect for every inventory URL. Run in CI. |
| `scripts/check_live.py` | The same check against the live site, over the network |

## Repository history

The repo was private at first. On the organization's Free plan a private repo can't use GitHub Pages or branch protection, so it was made **public** on 2026-11-11. The private source files listed above were untracked before the switch (`15c72d9`). The two earliest commits (`e9d72af`, `59dbe88`) still contain them; that was judged acceptable.

### After pulling a merge that untracks files

When a merge stops tracking a file (as `15c72d9` did for the export and plugin folders), `git pull` deletes that file from your disk. Restore it from the commit before the merge; it stays ignored:

```bash
git show 179095d:source/monicaespinel.WordPress.2026-11-11.xml > source/monicaespinel.WordPress.2026-11-11.xml
```
