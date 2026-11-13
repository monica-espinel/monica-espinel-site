# Phase 7: post-launch verification

The cutover was on **2026-11-12**, late evening US Eastern. GoDaddy and Bluehost both point to GitHub Pages, the certificate is issued, and Enforce HTTPS is on (see `DNS-CUTOVER.md`).

**Who does what:**
- **Claude** ran the checks that need no account (marked *Claude*), on 2026-11-12.
- **The owner** does the ones that need a Google account or the inbox (marked *Owner*).

---

## 1. Every old URL resolves (*Claude*: passed)

`scripts/check_live.py` requests every row of `migration/url-inventory.csv` from `https://monicaespinel.com`:

```bash
python3 -I scripts/check_live.py
```

Result on 2026-11-12:

```
Checked 405 inventory URLs on https://monicaespinel.com alias: 48, keep: 79, redirect: 278, plus http/www redirects
OK: every URL resolves
```

**What it checks:**
- `keep` rows are real pages that return 200.
- `alias` and `redirect` rows are redirect pages to the expected target, and the target returns 200.
- `http://`, `http://www.` and `https://www.` all end on `https://monicaespinel.com/`.

Run it again any time, for example after a content change.

## 2. Submit the sitemap in Search Console (*Owner*)

**Checked by Claude:**
- `https://monicaespinel.com/sitemap.xml` lists **79 URLs**, the 79 `keep` pages, all on `https://monicaespinel.com/`.
- `robots.txt` points to it and blocks nothing.

**To do:**
- [x] Search Console → property **monicaespinel.com** → **Sitemaps** → enter `sitemap.xml` → **Submit**. The status should become "Success" within a day.
  - Done by Claude, 2026-11-12: resubmitted `https://monicaespinel.com/sitemap.xml`, where All in One SEO's index had been listed.
  - Google read it straight away: type "Sitemap", **79 discovered pages**, status **Success**.
- [x] In the same list, **remove any old WordPress sitemaps**, for example `wp-sitemap.xml`, `sitemap_index.xml` or `post-sitemap.xml`. They now return 404. If `sitemap.xml` was already listed (All in One SEO used that path), just resubmit it.
  - Done by Claude, 2026-11-12. Removed:
    - `https://monicaespinel.com/sitemap.rss` (now 404);
    - `http://monicaespinel.com/sitemap.xml` and `https://www.monicaespinel.com/sitemap.xml`, both from 2020, which now redirect to the same file.
  - Only the new sitemap is listed now.

## 3. URL inspection: homepage and three posts (*Owner*)

In Search Console, paste each URL into the search bar at the top, then click **Test live URL**:

- [x] `https://monicaespinel.com/`
- [x] `https://monicaespinel.com/beats-of-the-sacred-heart/`
- [x] `https://monicaespinel.com/juan-francisco-elso-por-america/`
- [x] `https://monicaespinel.com/xocomil-vivian-suters-salute-to-the-wind/`

**Done by Claude, 2026-11-12, about 22:47–22:51 US Eastern:**
- All four live tests say **"URL is available to Google / Page can be indexed"**.
- **Request indexing** was clicked for each. All four are now in Google's priority crawl queue.

What Google's index showed before the live test:

| URL | Google index (old crawl) |
|---|---|
| `/` | On Google |
| `/juan-francisco-elso-por-america/` | On Google |
| `/beats-of-the-sacred-heart/` | **Not on Google:** "Blocked due to access forbidden (403)", last crawled 2026-07-17 |
| `/xocomil-vivian-suters-salute-to-the-wind/` | **Not on Google:** same 403, last crawled 2026-07-18 |

**Two findings:**
- **The old WordPress host was refusing Googlebot (HTTP 403) by July 2026.** This probably explains why only 24 pages were indexed. The new site serves Googlebot normally, so the count should rise over the next weeks.
- **Breadcrumbs rich results are gone.** The old pages had Breadcrumbs structured data from All in One SEO ("1 valid item detected", 14 valid in the property). The new pages' live tests show "URL has no enhancements". This doesn't affect indexing, only the breadcrumb trail Google can show under a result.
  - Fixed in pull request #9, which adds `BreadcrumbList` JSON-LD with the same trails as the old site.

**What to expect:**
- "URL is available to Google".
- The canonical chosen by the page is the same URL.
- Optional: click **Request indexing** for each.

**Checked by Claude on the post:** the canonical is `https://monicaespinel.com/beats-of-the-sacred-heart/`. The robots meta is `max-image-preview:large`, with no `noindex`. The meta description is set.

## 4. Search the live site with Pagefind (*Claude*: passed)

- On `https://monicaespinel.com/search/`, the term **"Carmen Herrera"** returns **8 results**, including "Carmen Herrera memorial Whitney Museum", "Obra de la artista Carmen Herrera" and "The Brooklyn Rail - 1970s: Carmen Herrera at Lisson".
- `pagefind-ui.js`, `pagefind.js` and the worker load with HTTP 200.
- No console errors.

## 5. GA4 Realtime shows a pageview (*Claude*: hit sent; *Owner*: confirm in GA4)

**Checked by Claude:** loading `https://monicaespinel.com/beats-of-the-sacred-heart/` sends a `page_view` to `google-analytics.com/g/collect` with:
- `tid=G-ZR270JS8ZG`
- `dl=https://monicaespinel.com/beats-of-the-sacred-heart/`

The tag only runs on `monicaespinel.com`, so local previews don't count. It also skips visitors who have Do Not Track turned on.

**To do:**
- [x] GA4 → **Reports → Realtime**: open any page of the site in another tab, and check a view appears within a minute. If nothing appears, test from a browser without Do Not Track and without an ad blocker.
  - **Checked by Claude, 2026-11-12, about 22:55.** The right property is **"monicaespinel.com"** (property ID `320308156`).
  - Realtime showed 4 active users and 21 views in 30 minutes, with page paths `/`, `/about/`, `/beats-of-the-sacred-heart/`, `/category/exhibitions/`, `/category/talks/`, `/contact/`, `/search/`, and others.
  - It also showed 4 views of "404 Page not found". **All were `/wp-admin/…`**: someone opening the old WordPress admin, which no longer exists on the domain. That's expected, and no real page is missing.
  - **Note:** a second GA4 property named after the site, "monicaespinel.com/ GA4 - MonsterInsights" (`363685349`, `G-2SYEGT8QLB`), receives no data. Use property `320308156`.

## 6. Test message through the contact form (*Owner*)

**Checked by Claude:**
- The form on `/contact/` posts to `https://formspree.io/f/xdegodvq`.
- It has the `_gotcha` honeypot and the subject "Message from monicaespinel.com".
- It shows "Thank you. Your message has been sent." inline.
- There's no `mailto:` link anywhere on the page.

**To do:**
- [x] Send one message from `https://monicaespinel.com/contact/`, with a name, your email and a short text.
  - Done by Claude on 2026-11-12, from the live site.
  - Name "Site migration test", email `test@example.com`.
  - The message text starts "Test message from the new monicaespinel.com (GitHub Pages)…".
- [x] Check that the page shows the thank-you message, and the message reaches the inbox set up in Formspree. Look in spam too the first time.
  - **The page part passed:** Formspree accepted the message, and the page showed "Thank you. Your message has been sent." inline, with no reCAPTCHA.
  - **Owner checked Formspree (2026-11-12):** the submission arrived in the "Contact me" form, with all fields intact (subject, name, email and message). **But Formspree filed it under Spam**, so it wasn't emailed. The likely cause is the placeholder address `test@example.com`.
  - [x] **A real message reaches the inbox.** Confirmed by the owner on 2026-11-12 at 22:59: a message sent from `/contact/` with a real address landed in Formspree's **Inbox** tab, with status **delivered** to the owner's mailbox. The contact form works end to end.
  - [ ] Optional: in Formspree → Submissions → Spam, select the test and mark it as not spam. Then delete it.
  - If a later message goes to Spam: check Formspree → Settings for spam filtering, and keep the honeypot. Messages flagged as spam can always be read in that tab.
- [x] *(Not needed: no reCAPTCHA page appeared.)* If Formspree shows a reCAPTCHA page instead of the inline message, turn reCAPTCHA off in the form's settings: the honeypot covers spam.

## 7. Search Console coverage, weekly for four weeks (*Owner*)

Check **Indexing → Pages** once a week. Expect old WordPress URLs to move to "Page with redirect" or "Alternate page with proper canonical tag". Look for a rise in **"Not found (404)"** or **"Server error"**.

| Week of | Indexed | Not indexed | New 404s? | Notes |
|---|---|---|---|---|
| 2026-11-12 (baseline) | 24 | 53 | n/a | Search Console overview at cutover, still reflecting WordPress, including the 403s to Googlebot |
| 2026-11-19 | | | | |
| 2026-11-26 | | | | |
| 2026-12-03 | | | | |
| 2026-12-10 | | | | |

**If a 404 shows up for a URL that matters:** send Claude the URL. It can be added as an alias in the matching page's front matter, or as a redirect page, in a small pull request.

---

## Also after cutover (from `DNS-CUTOVER.md`)

- [ ] **Around 2026-11-14:** raise the TTL of `@` and `www` back to 3600 at GoDaddy, once everything has worked for a day or two.
- [ ] **Keep WordPress (Bluehost) running until at least 2026-12-12**, 30 days after cutover. Before cancelling it, see "Before cancelling WordPress" in `DNS-CUTOVER.md` (SPF and `default._domainkey`).
- [ ] **Optional:** the Bluehost zone no longer matters after 2026-11-14. Leave it as it is until the plan is cancelled.

## Phase 7 status

**Done (2026-11-12):**
- 1 (all URLs);
- 2 (sitemap submitted, old ones removed);
- 3 (URL inspection and indexing requests);
- 4 (Pagefind);
- 5 (GA4 Realtime);
- 6 (the contact form works end to end: a real message was delivered to the owner's mailbox; the earlier placeholder test was filed as spam).

**Open, for the owner:**
- the four weekly coverage checks, starting 2026-11-19.

**Breadcrumbs:** decided 2026-11-12, added in pull request #9 (`BreadcrumbList` JSON-LD). Run Google's Rich Results Test on a post once it's deployed.
