# Migration plan: monicaespinel.com → Hugo on GitHub Pages

Plan derived from `CLAUDE.md` and a first read of the source material (2026-11-11).

## What the source material contains

| Item | Found |
|---|---|
| Export | `source/monicaespinel.WordPress.2026-11-11.xml` (WXR 1.2). Brief expects `source/wordpress-export.xml`; the scripts will take the path as an argument, no rename needed. |
| Uploads | `source/wp-content/uploads/`, 384 files, 177 MB, years 2009–2026, plus plugin folders `aioseo/`, `aioseo-logs/`, `wpforms/` |
| Published posts | 38 (2003-06-10 → 2024-03-13). All 8 homepage posts confirmed. |
| Published pages | 2: `about`, `contact`. Drafts/private (not migrated): `exhibitions`, `curriculum`, 2× `wpforms-preview`, 1 draft post "Homo Rodans". |
| Categories | exhibitions, publications, reviews, talks, uncategorized (unused) |
| Tags | 36 |
| Authors | `monica.espinel` (Monica Espinel), `simon.letort` (Simon Letort, 5 posts) |
| Comments | 0, so nothing to migrate |
| Attachments | 84 attachment pages (e.g. `/carmen-herrera/carmen-herrera-installation-shot-4/`) |
| Old slugs | 53 `_wp_old_slug` entries, which become `aliases` |
| Descriptions | `_aioseo_description` (48) and older `_aioseop_description` (29); AIOSEO OG title/description too |
| Body markup | Gutenberg blocks: paragraph, image, gallery, file (PDF), heading, embed (6), list, video, more, group, plus one each of shortcode (contact form), Jetpack podcast player, podcast-subscribe button |
| Nav menu | 24 items: 6 top items plus dropdowns listing posts under each category |

## Phase plan (one commit per phase, on branch `claude/peaceful-fermi-lv6a8k`)

### Phase 1: Inventory
- `scripts/wp_inventory.py` (stdlib only) parses the WXR and writes `migration/url-inventory.csv`:
  `old_url,type,title,description,date,action,target`.
- URL sources: published posts/pages, category + tag archives, author archives (`/author/<login>/`), pagination for home/category/tag/author (`/page/N/` from post counts, WP default 10 per page; confirm the setting), `/feed/` + per-category/tag feeds, `_wp_old_slug` URLs, attachment pages.
- `action` = `keep` | `alias` | `redirect`. Stated defaults: pagination → `/`, author → `/`, attachment → parent post, feeds → `/index.xml` or the taxonomy's `index.xml`.

### Phase 2: Content conversion
- `scripts/wp_to_hugo.py` writes `content/<slug>.md` for posts and `content/about.md`, `content/contact.md`.
- Front matter: `title, date, slug, author, categories, tags, description, aliases`. Description priority: `_aioseo_description` → `_aioseop_description` → none, otherwise left empty (14 posts and pages have none; **owner decision: leave empty**). Never generate one.
- Block → Markdown: paragraphs/headings/lists/links/italics to Markdown; `wp:image` with caption → `figure` shortcode; `wp:gallery` → a small `gallery` shortcode; `wp:file` → PDF link; `wp:embed` → YouTube/Vimeo shortcode or a plain link; podcast/Jetpack blocks → link to the source and a `TODO:` note.
- Permalinks: `[permalinks] posts = "/:slug/"`, categories `/category/:slug/`, tags `/tag/:slug/`.
- Uploads are published at `/wp-content/uploads/` through a Hugo **mount** of `source/wp-content/uploads`
  (in `hugo.toml`), not a copy into `static/`: same output paths, no second 177 MB copy in git. `aioseo*` and
  `wpforms/` are excluded. All WP size variants are kept because old HTML and external sites link to them.
- `scripts/check_urls.py` compares `hugo --renderToMemory`/`public/` against the CSV and prints mismatches.

### Phase 3: Templates and SEO
- Minimal custom theme in `layouts/` (no redesign; match the current simple blog layout).
- `<head>`: title, description, canonical, OG and Twitter `summary`, robots, favicon (from WP site icon in uploads), `_internal/google_analytics.html` with `googleAnalytics = "G-ZR270JS8ZG"` (Hugo 0.164 uses `[services.googleAnalytics] ID`, so set both forms or the one 0.164 reads).
- `robots.txt` (enableRobotsTXT + custom template pointing at `/sitemap.xml`), default sitemap, RSS `/index.xml` with `/feed/` alias.
- `/contact/`: Formspree form (`https://formspree.io/f/xdegodvq`), `_gotcha` honeypot, inline success message via JS
  (`Accept: application/json`); without JS the form still posts and Formspree shows its own thank-you page.
  **Owner decision: no `mailto:` link** (overrides the brief), so no email address is published on the site.
  The error message tells the visitor to try again later.
- `/search/`: Pagefind UI from `/pagefind/`, `data-pagefind-body` on article content.
- Search Console: owner adds the DNS TXT record (written into the Phase 6 instructions).
- Checks: Lighthouse (`npx lighthouse`, Chromium in container) on home + one post ≥ 95 SEO; `npx linkinator` or `lychee` against a local server.

### Phase 4: Redirects
- Aliases cover old slugs and `/feed/`.
- For the rest (pagination, author, attachment pages, feeds of taxonomies), a generated `content/_redirects/` set or a Hugo template that reads `data/redirects.csv` and emits HTML with canonical + `meta refresh` + visible link. Hugo's built-in alias template is overridden in `layouts/alias.html` so both paths produce identical redirect pages.
- Re-run `check_urls.py`: every CSV row must give 200 with content or a redirect page.

### Phase 5: Deployment
- `.github/workflows/pages.yml`: jobs `build` (Hugo extended 0.164.0, `hugo --minify`), `pagefind` (`npx --yes pagefind@latest --site public`, then `actions/upload-pages-artifact`), `deploy` (`actions/deploy-pages`). Trigger: push to `main` (+ `workflow_dispatch`).
- Pass `public/` between jobs via `actions/upload-artifact`.
- `static/CNAME` = `monicaespinel.com`.
- Owner sets Pages source = GitHub Actions. Before the custom domain is set, test on a local server, because root-relative URLs break under `/monica-espinel-site/`.

### Phase 6: DNS instructions
`migration/DNS-CUTOVER.md`: TTL 300 ≥24 h ahead, four A records, `www` CNAME, the Pages custom domain, Enforce HTTPS, Search Console TXT, leave MX alone, and rollback. I do not change DNS.

### Phase 7: Post-launch checklist
`migration/POST-LAUNCH.md` lists the brief's checks for the owner.

## Findings from the live author page (owner-supplied HTML, cached 2025-12-10)

- Author slug `/author/monica-espinel/` confirmed. Posts per page = 8 (`/page/5/` = 33 posts / 8).
- Theme is **Twenty Twenty**: accent `#cd2653`, text `#000`, secondary `#6d6d6d`, borders `#dcd7ca`, Inter font,
  centered entry headers, a featured image above each post, excerpts on archive pages. Phase 3 matches this look (no redesign).
- Site title `MONICA ESPINEL`, tagline `Curator & Writer`, footer `© <year> MONICA ESPINEL`.
- Favicon: `wp-content/uploads/2020/03/image.jpg` (served through Jetpack `i0.wp.com`).
- **Featured images** (`_thumbnail_id`) carry captions and are part of each post, so they go into front matter as `image`.
- **Bylines are hidden** on the live site by custom CSS (`.post-author { clip: … }`).
  **Decision (owner):** keep them hidden the same way. `author` stays in front matter and the byline is rendered
  in the HTML with a visually-hidden class (readable by screen readers and search engines, not shown on screen).
- Author archives are `noindex`, so redirecting them to `/` loses no search visibility.
- **Search Console is currently verified by a meta tag** (`google-site-verification`, probably via Site Kit).
  The brief wants DNS TXT instead. The owner must add the TXT record **before** cutover, or the property loses
  verification when the meta tag disappears. This goes into the Phase 6 instructions.
- The site also sends to an old Universal Analytics ID (`UA-10447421-6`). UA stopped processing data in 2024; only GA4 is kept.
- The live site refuses automated requests (403) even with network access allowed, so later live checks
  need the owner's browser or a bot-blocker exception.

## Findings from the live homepage (owner-supplied HTML, served 2026-10-22)

- 8 posts per page confirmed on the homepage too (`/page/5/` = 38 posts / 8). The 8 posts shown match the brief's list, in the same order.
- Homepage `<title>`: `Monica Espinel - Curator and Writer`. Meta description = the brief's text.
- Homepage `og:description` / `twitter:description` are out of date ("guest curator for Artpace in San Antonio").
  The new site uses the brief's description for all three.
- `og:image` / `twitter:image`: `/wp-content/uploads/2020/03/image.jpg`; `twitter:site` = `@monica_espinel`; `twitter:card` = `summary`.
- Homepage robots: `max-image-preview:large` (author archives: `noindex`). The new site keeps the same robots values.
- WordPress 7.1.3, AIOSEO 5.0.4, Site Kit still loading GA4 `G-ZR270JS8ZG` (plus the dead UA ID).

## Phase 3 results (templates and SEO)

- Look: Twenty Twenty recreated in `assets/css/main.css` (colours, Inter for headings/UI, serif body text,
  white header/footer bands, centred entry headers, "Category:" archive titles, post separators).
  Inter is self-hosted from `@fontsource-variable/inter` (OFL, `static/fonts/inter/`), as Twenty Twenty did.
  The mobile menu is a wrapped list instead of Twenty Twenty's slide-out modal.
- `<head>` (`layouts/_partials/seo.html`): title, description (left out when empty), canonical, robots
  (`max-image-preview:large`, `noindex` on search and redirect pages), Open Graph, Twitter `summary`,
  JSON-LD (WebSite, Person, BlogPosting), favicons generated from the WordPress site icon.
- GA4 exactly as the brief says: `googleAnalytics = "G-ZR270JS8ZG"` + `{{ template "_internal/google_analytics.html" . }}`.
  Hugo only outputs it in production builds, so `hugo server` previews send no pageviews.
- `robots.txt` points to `sitemap.xml` (79 URLs: every kept page, search excluded). RSS at `/index.xml`.
- Feeds: `/feed/` and the category/tag/author/per-post feed URLs are static redirect pages from
  `scripts/make_redirects.py` (run with `--types feed`). Hugo aliases can't point at `index.xml`.
  Note: feed readers usually don't follow HTML redirects, so old subscribers to `/feed/` need to re-subscribe
  to `/index.xml`. Pages and search engines are unaffected.
- Images: featured images, figures and galleries get WebP `srcset` sizes at build time (uploads mounted as
  assets); links and `og:image` keep pointing to the original files.
- Contact: Formspree form (honeypot `_gotcha`, inline success/error message, works without JavaScript).
- Search: `/search/` with Pagefind UI; only posts and pages are indexed (`data-pagefind-body`), without
  bylines, categories and tags.
- `404.html` (`noindex`, no canonical) and an alias template with canonical, meta refresh, visible link and
  `noindex`. `make_redirects.py` builds its pages from the same `layouts/alias.html`, and refuses any path
  Hugo renders itself.
- RSS (`layouts/rss.xml`): posts only, like the WordPress feed (no About, Contact or Search items).
- Share images (`og:image`, `twitter:image`): a JPEG copy at most 1200px wide, with width and height
  (originals go up to 7.5 MB; X/Twitter refuses images over 5 MB). Favicons are PNG.
- Contact form: if Formspree refuses the background (AJAX) request, for example because reCAPTCHA is on in
  the form settings, the form is sent the normal way, so messages still arrive. **Owner:** for the inline
  thank-you message, turn reCAPTCHA off in the Formspree form settings (the honeypot covers spam).
- Search Console verification: DNS TXT record, in the Phase 6 instructions (no meta tag on the new site).

Acceptance checks:
- Lighthouse SEO 100 on `/` and on `/parcharte/`. Posts without a description score 92 (owner decision).
  Performance 97–100, accessibility 100.
- linkinator: 270 internal links, 0 broken.
- `check_urls.py`: 170 URLs match, 0 mismatches, 235 pending Phase 4 (redirect pages).

## Phase 4 results (redirects)

- Hugo `aliases:` cover the 9 old post slugs (front matter, from `_wp_old_slug`).
- `scripts/make_redirects.py` (no `--types`: all rows) writes the other 317 redirect pages under `static/`,
  from `layouts/alias.html` (canonical, meta refresh, visible link, `noindex`):
  82 feeds (Phase 3), 126 attachment pages, 93 date archives, 11 pagination URLs, 2 author archives,
  3 empty category/tag pages.
- Targets, "nearest matching section": home pagination, author and date archives and empty terms → `/`;
  category pagination → the category; attachment pages → their post (or `/` when it has none).
- Not servable on GitHub Pages: `/?attachment_id=4491` (query string; the homepage is served instead).
  WordPress `?p=` shortlinks likewise show the homepage.
- Redirect pages are not in the sitemap or the search index.
- Every redirect page (Hugo aliases and generated pages, one template: `layouts/alias.html`) has an absolute
  canonical link but a **root-relative** meta refresh and visible link, so redirects stay on whatever host
  serves the site (previews, localhost) instead of jumping to the production domain (WordPress until cutover).
- `make_redirects.py` takes the site origin from `hugo.toml`, refuses any path Hugo renders (inventory pages
  *and* every page or alias in `content/`, so a new post can't be shadowed by an old attachment redirect),
  and has a `--check` mode that fails when the committed pages differ from the inventory.
- **Phase 5 workflow must run** `python3 -I scripts/make_redirects.py --check` and, after the build,
  `python3 -I scripts/check_urls.py --strict`, so a deploy fails on stale or missing redirects.

Acceptance checks:
- `check_urls.py --strict`: 405 of 406 inventory URLs return the page or a redirect page, 0 pending,
  0 mismatches (the 406th is the query-string URL above).
- In Chromium, sample redirects land on the right page: `/page/3/` → `/`, `/category/exhibitions/page/2/` →
  the category, `/author/monica-espinel/` and `/2024/03/13/` → `/`, `/black-milk/1-28/` → `/black-milk/`,
  `/crackerfarm0/` → `/crackerfarm/`, `/feed/` → `/index.xml`.

## Phase 5 (deployment)

- `.github/workflows/pages.yml`, three jobs in order:
  1. **build**: Hugo extended 0.164.0 from the official `.deb` (sha256 checked), `make_redirects.py --check`,
     `hugo --minify --gc` (production), `check_urls.py --strict`; processed images cached in `resources/_gen`.
  2. **pagefind**: `npx --yes pagefind@latest --site public`, then `actions/upload-pages-artifact`.
  3. **deploy**: `actions/deploy-pages`, on push to `main` (and manual runs) only.
  Pull requests run jobs 1–2 as a check, without deploying; a newer push cancels the older PR run.
- Actions are on their Node 24 majors (checkout v7, cache v6, upload-artifact v7, download-artifact v8,
  setup-node v7, configure-pages v6, upload-pages-artifact v5, deploy-pages v5), **pinned to full commit
  SHAs** with the version in a comment, like the checksum-verified Hugo download. Don't switch them back
  to tags: `.github/dependabot.yml` opens a monthly PR to update the pins.
- `actions/checkout` runs with `persist-credentials: false`: the job runs repository scripts and never
  needs the token afterwards (the repo is public, so fork PRs can run the build).
- On main, `actions/configure-pages` runs first and fails early if Pages isn't set to GitHub Actions.
- After Pagefind (`@latest`, unpinned as the brief asks), the job checks that `pagefind-ui.js`/`.css` exist
  (what `/search/` loads) and that it indexed exactly as many pages as the build marked for search
  (`data-pagefind-body`: posts and pages, 40 today). No fixed number, so removing a post doesn't break deploys.
- The image cache key covers layouts, config, content and uploads, so new posts save a fresh cache.
- GA4: `layouts/baseof.html` sets gtag's opt-out flag (`ga-disable-G-ZR270JS8ZG`) on any host other than
  the `baseURL` domain and its subdomains, before Hugo's built-in GA template. So the github.io project URL
  and local previews send no pageviews, and GA4 only shows traffic from monicaespinel.com. This is
  intentional: don't expect GA4 hits from the project URL during the Phase 5 check.
- `static/CNAME`: `monicaespinel.com`. (With Actions deployments GitHub uses the custom domain set in the
  Pages settings; the file documents it and is harmless.)
- Replayed in a fresh clone: build 12 s (183 images processed from scratch), 405/406 URLs, 40 pages indexed,
  `public/` 187 MB (Pages limit 1 GB).
- Pages source: **GitHub Actions**, set by the owner on 2026-11-11 when the repo was made public (#5, #6).
  `main` is protected (PR required). Don't enter the custom domain yet: that is Phase 6, after the DNS TTL is lowered.
- Merged with `main` after #5/#6: the build doesn't need the (now untracked) WordPress export, and the
  "Homo Rodans" draft images are no longer published. All checks still pass.
- Project URL: until the custom domain is set, the site is at `https://monica-espinel.github.io/monica-espinel-site/`.
  Root-relative links (`/about/`, CSS, images) point outside that folder there, so pages look unstyled and links
  break; the brief allows checking on a local server instead.

## Phase 5 result

- First deploy from `main` (#4 merged): workflow run #7 on 30b1bbf, **all jobs green including Deploy**
  (https://github.com/monica-espinel/monica-espinel-site/actions/runs/43142894674).
- The site is on `https://monica-espinel.github.io/monica-espinel-site/`. As expected, root-relative links
  point outside that folder there; the site was checked on a local server instead (brief note).

## Phase 6 (DNS cutover, owner)

- Instructions: `migration/DNS-CUTOVER.md`, a step-by-step checklist with tables of exact records.
  On top of the brief's six steps, it adds:
  - writing down every current record first (rollback values)
  - verifying the domain in the GitHub organization (protects against domain takeover)
  - the Search Console DNS TXT record before cutover (new site has no meta tag)
  - keeping the SPF `TXT` and other email records
  - removing old `AAAA` records, and GitHub's optional IPv6 `AAAA` records
  - Cloudflare "DNS only" and `CAA`/Let's Encrypt caveats
  - checks, and the rollback steps
  - **order:** the custom domain is saved in GitHub *before* the DNS change (GitHub's recommendation; the brief
    lists it after), so there's no window where GitHub serves "There isn't a GitHub Pages site here"
  - a warning to expect certificate errors on `https://` until the certificate is issued (pick a quiet time,
    don't roll back for that alone)
  - delete every `www` record before adding the `CNAME`, and any apex `ALIAS`/`ANAME` record
  - note where the nameservers and email are hosted: if at the WordPress host, move them **before** cancelling it
  - check for HSTS on the old site: returning visitors can't bypass the certificate warning during the window
  - troubleshooting for a slow certificate (leftover records, Cloudflare, `CAA`, re-saving the custom domain)
  - **GoDaddy** (registrar, per the owner): where the records and nameservers are, the TTL minimum if 300 isn't
    accepted, default records to leave, domain forwarding to switch off, and how names are written in its form
- Claude does not change DNS. **Done when** the owner confirms `https://monicaespinel.com` and
  `https://www.monicaespinel.com` load with a valid certificate.

## Open issues

- **5 Brooklyn Rail speaker photos missing** (post `/brooklyn-rail-carmen-herrera/`: Tony Bechara, Odili Donald Odita,
  Monica Espinel, Raphael Rubinstein, Tyhe Cooper). The post loads them from `brooklynrail.org/media/files/…`,
  which now redirects to the Brooklyn Rail Contributors page, so they are already broken on the live WordPress site.
  **Owner decision:** recover the Wayback Machine copies and store them in the repo.
  **Blocked:** `web.archive.org` is not allowed in this repository's cloud environment (the request to add it was
  rejected by the environments service). To finish: add `web.archive.org` under the environment's Network access,
  then run `python3 -I scripts/fetch_external_images.py source/monicaespinel.WordPress.2026-11-11.xml`
  and `python3 -I scripts/wp_to_hugo.py source/monicaespinel.WordPress.2026-11-11.xml content`, check the five
  portraits, and commit. Until then the post keeps the original (broken) image addresses.
- `brooklynrail.org` was allowed in the environment for this and is no longer needed; it can be removed.

## Open questions for the owner
1. ~~Contact `mailto:` address~~: resolved, no `mailto:` link; Formspree only (owner decision).
2. **Nav dropdowns**: the WP menu lists posts under each category. Keep only the six top items as the brief says, or recreate the dropdowns?
3. **Large uploads (177 MB, video/PDF in 2020–2023)**: fine for Pages (limit 1 GB), but should unused size variants be pruned? Default: keep everything referenced plus all variants.
4. **Attachment pages**: redirect to the parent post (my default) or to the file itself?
5. ~~Posts per page~~: resolved, 8 (confirmed on the live site).
6. **Merge strategy**: the brief says PR → `main`; I'll open the PR only when you ask.

## Tooling
- Hugo is not installed in the container. I'll download extended 0.164.0 from GitHub releases into `~/.local/bin` (not committed).
- Node 22 is available for Pagefind, Lighthouse and the link checker.
