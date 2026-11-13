# Migration brief: monicaespinel.com from WordPress to Hugo on GitHub Pages

You are building and deploying a static version of monicaespinel.com, a blog and portfolio for Monica Espinel, a curator and writer. The current site runs on WordPress (with Jetpack and Google Site Kit). It is being replaced, and WordPress stays running until the cutover is verified.

## Fixed decisions

| Area | Value |
|---|---|
| Generator | Hugo extended, version **0.164.0** (pin it in the workflow) |
| Repository | `monica-espinel-site` (project repo, Pages from GitHub Actions) |
| Domain | `monicaespinel.com` (apex and `www`), `baseURL = "https://monicaespinel.com/"` |
| Contact form | Formspree. Endpoint: `https://formspree.io/f/xdegodvq` |
| Search | Pagefind, built after `hugo --minify`, output into `public/pagefind/` |
| Analytics | GA4, measurement ID `G-ZR270JS8ZG`, via Hugo's built-in Google Analytics partial |
| Hosting | GitHub Pages, deployed by `.github/workflows/pages.yml` |

## Goals

1. Every URL indexed on the current site resolves to the same page, or to a redirect page.
2. All post text, images, metadata, tags, categories, and the RSS feed are preserved.
3. No change to the domain, and no loss of search visibility.
4. WordPress is not touched. It remains the live source until the owner cancels it.

## Source material

- WordPress XML export (Tools → Export, all content): the current one is `source/monicaespinel.WordPress.2026-11-11.xml`. It is **gitignored and local only**, because it contains drafts, private pages, author emails and logins. Never commit it. Only the conversion scripts need it; the build uses the committed `content/`. A fresh clone won't have it: ask the owner for it before re-running `scripts/wp_*.py`.
- Uploads folder: `source/wp-content/uploads/`, committed (the build mounts it). These parts are gitignored and excluded from the mounts in `hugo.toml`: plugin data (`aioseo/`, `aioseo-logs/`, `wpforms/`) and `2026/01/image*`, the images of the unpublished draft "Homo Rodans". Keep any new private or draft-only file out the same way: add it to `.gitignore` and to the mount excludes.
- If either is missing, stop and ask. Do not guess content.
- See `README.md` for setup (Hugo 0.164.0 extended, Python packages, Node for Pagefind) and the full list of untracked files.

## Site structure to recreate

Top navigation, in this order:
- About → `/about/`
- Exhibitions → `/category/exhibitions/`
- Publications → `/category/publications/`
- Reviews → `/category/reviews/`
- Talks → `/category/talks/`
- Contact → `/contact/`

Each post keeps its WordPress slug as its URL. Example: `/beats-of-the-sacred-heart/`, `/juan-francisco-elso-por-america/`. Each post has: title, date, author, category, tags, and the body, which is mostly short notes with links to external publications, talks, and events.

Posts known from the homepage (confirm against the export): Beats of the Sacred Heart (2024-03-13), Embodying the Abject (2023-07-01), Xocomil, Vivian Suter's Salute to the Wind (2023-02-18), Juan Francisco Elso: Por América (2023-01-09), Burning with Desire (2022-10-27), Carmen Herrera memorial Whitney Museum (2022-09-28), Obra de la artista Carmen Herrera (2022-06-21), The Brooklyn Rail – 1970s: Carmen Herrera at Lisson (2022-06-07).

Author bylines: every post is bylined Monica Espinel. WordPress credits 5 posts to Simon Letort, and the owner decided on 2026-11-12 to change those to Monica Espinel. `scripts/wp_to_hugo.py` applies this through `BYLINE_OVERRIDES`. The old `/author/simon-letort/` archive still redirects to `/`.

The site's meta description: "Monica Espinel is a curator and writer specialized in Contemporary Art from Latin America. She is currently a Ph.D. candidate at The Graduate Center, City University of New York." Use it as the homepage description. Copy the description for each page from the WordPress export when it exists.

## Phase 1: Inventory

- Parse the WordPress XML. Produce `migration/url-inventory.csv` with columns: `old_url`, `type` (post, page, category, tag, author, pagination, feed), `title`, `description`, `date`.
- Include pagination (`/page/N/`), author archives, tag archives, and `/feed/`. Mark which ones will be kept and which will redirect.

**Done when:** the CSV exists and every URL from the export is listed.

## Phase 2: Content conversion

- Create one Markdown file per post and page in `content/`, with front matter: `title`, `date`, `slug`, `author`, `categories`, `tags`, `description`, `aliases`.
- File names match the WordPress slug. Output URLs match the old URLs exactly.
- Publish uploads at `/wp-content/uploads/` so existing image paths keep working. This is done with a Hugo mount of `source/wp-content/uploads/` in `hugo.toml` (plugin folders excluded), not a copy into `static/`, to avoid a second 177 MB copy in git. `source/wp-content/uploads/` must therefore stay in the repository: the build reads from it.
- Convert WordPress block markup to clean Markdown. Keep links, italics, and image captions.
- Categories use Hugo taxonomy pages at the same paths.

**Done when:** `hugo server` renders every post. A check script compares the rendered URL list to `url-inventory.csv` and prints any mismatch.

## Phase 3: Templates and SEO

- Base template `<head>` includes: `<title>`, meta description, canonical link, Open Graph and Twitter tags (`summary` card), `robots` meta, favicon, and the GA4 partial.
- In `hugo.toml`, set `googleAnalytics = "G-ZR270JS8ZG"` and include `{{ template "_internal/google_analytics.html" . }}` in the head.
- Generate `sitemap.xml` (Hugo default) and `robots.txt` that points to it.
- RSS at `/index.xml`. Add an alias so `/feed/` also works.
- Contact page (`/contact/`): form posts to `https://formspree.io/f/xdegodvq`, includes a honeypot field, and shows a success message. No `mailto:` link: the owner decided not to publish an email address on the site.
- Search page (`/search/`): loads Pagefind UI from `/pagefind/`.
- Add a Google Search Console verification record as a DNS TXT record. Do not use a meta tag.

**Done when:** Lighthouse SEO score is at least 95 on the homepage and one post. No broken internal links (check with a link checker).

## Phase 4: Redirects

GitHub Pages does not support server-side redirects, so use static redirect pages.

- Use Hugo `aliases:` front matter where an old URL maps to a new file.
- For old URLs with no matching file (WordPress pagination, author archives), generate redirect pages with a canonical link, a `meta refresh` tag, and a visible link. Use the nearest matching section.
- Decide the pagination handling from the Phase 1 CSV. Default: `/page/N/` redirects to `/`.

**Done when:** every URL in `url-inventory.csv` returns the page or a redirect page.

## Phase 5: Deployment

Create `.github/workflows/pages.yml` with three jobs in order: build with Hugo, build the Pagefind index, deploy with `actions/deploy-pages`.

- Trigger on push to `main`.
- Hugo version `0.164.0`, extended build.
- After `hugo --minify`, run `npx --yes pagefind@latest --site public`.
- Upload `public/` with `actions/upload-pages-artifact`.
- Add `static/CNAME` containing `monicaespinel.com`.
- Repository setting: Pages source is GitHub Actions.
- Done on 2026-11-11: the repo was made public, which lifted the Free-plan limits. The Pages source is GitHub Actions (default address `https://monica-espinel.github.io/monica-espinel-site/`). `main` is protected: a PR is required with 0 approvals, force pushes and deletion are blocked, and admins can bypass.

**Done when:** the Actions build passes, and the default `<username>.github.io/monica-espinel-site/` address serves the full site. (Note: because the custom domain is set at the root, check root-relative links work on the project URL. If they don't, the site can be checked on a local server instead.)

## Phase 6: DNS cutover (owner performs this step)

Do not change DNS yourself. Write the instructions for the owner:
1. Lower the TTL at the registrar to 300 seconds, at least 24 hours before cutover.
2. A records for the apex: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`.
3. CNAME for `www` to `<username>.github.io`.
4. Enter `monicaespinel.com` as the custom domain in Pages settings. Wait for the DNS check.
5. Enable Enforce HTTPS after the certificate is issued.
6. Confirm that MX records for the domain's email are not changed.

**Done when:** owner confirms both `https://monicaespinel.com` and `https://www.monicaespinel.com` load with a valid certificate.

## Phase 7: Post-launch verification

- Submit the new sitemap in Search Console.
- Use URL inspection on the homepage and three posts.
- Search the live site with Pagefind for a term from a known post.
- Confirm the GA4 Realtime report shows a pageview from the live domain.
- Send one test message through the contact form and confirm it reaches the owner's inbox.
- Check the Search Console coverage report weekly for four weeks.

## Rollback

If the new site has a serious problem, the owner points the A records back to the WordPress host. Keep WordPress running until the owner cancels it, at least 30 days after cutover.

## Out of scope

- Changing the domain or redesigning the layout.
- Migrating comments (check the export for any).
- Changing MX or email records.
- Canceling WordPress. The owner does this.

## Working rules

- Work on a branch and open a pull request for review. `main` is protected. Admins can technically push straight to it, but don't.
- After a PR is merged, clean up: switch to `main`, `git pull`, `git fetch --prune` (drops remote branches deleted on GitHub), then delete local branches whose work is merged. PRs are squash-merged, so `git branch --merged` misses them. Instead, delete a local branch only when `gh pr list --state all --head <branch>` shows a MERGED PR and the branch tip equals that PR's `headRefOid`. A branch with no merged PR, or with commits after the merge, may be unfinished work (possibly from another session): leave it and list it in the report.
- Commit in small steps, one per phase.
- Never commit secrets. The Formspree endpoint and GA4 ID are public and can be committed.
- Uploads: `source/wp-content/uploads/` is committed. If that folder is missing, stop and ask.
- The WordPress export is never committed (see Source material). Before committing, check that `git status` shows no `source/*.xml`.
- If something in the export is ambiguous, leave a `TODO:` comment in the file and list it in the final report. Don't invent content.
- Report at the end of each phase: what was done, what the acceptance check showed, and open questions.
