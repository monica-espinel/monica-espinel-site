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
- [ ] Search Console → property **monicaespinel.com** → **Sitemaps** → enter `sitemap.xml` → **Submit**. The status should become "Success" within a day.
- [ ] In the same list, **remove any old WordPress sitemaps**, for example `wp-sitemap.xml`, `sitemap_index.xml` or `post-sitemap.xml`. They now return 404. If `sitemap.xml` was already listed (All in One SEO used that path), just resubmit it.

## 3. URL inspection: homepage and three posts (*Owner*)

In Search Console, paste each URL into the search bar at the top, then click **Test live URL**:

- [ ] `https://monicaespinel.com/`
- [ ] `https://monicaespinel.com/beats-of-the-sacred-heart/`
- [ ] `https://monicaespinel.com/juan-francisco-elso-por-america/`
- [ ] `https://monicaespinel.com/xocomil-vivian-suters-salute-to-the-wind/`

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
- [ ] GA4 → **Reports → Realtime**: open any page of the site in another tab, and check a view appears within a minute. If nothing appears, test from a browser without Do Not Track and without an ad blocker.

## 6. Test message through the contact form (*Owner*)

**Checked by Claude:**
- The form on `/contact/` posts to `https://formspree.io/f/xdegodvq`.
- It has the `_gotcha` honeypot and the subject "Message from monicaespinel.com".
- It shows "Thank you. Your message has been sent." inline.
- There's no `mailto:` link anywhere on the page.

**To do:**
- [ ] Send one message from `https://monicaespinel.com/contact/`, with a name, your email and a short text.
- [ ] Check that the page shows the thank-you message, and the message reaches the inbox set up in Formspree. Look in spam too the first time.
- [ ] If Formspree shows a reCAPTCHA page instead of the inline message, turn reCAPTCHA off in the form's settings: the honeypot covers spam.

## 7. Search Console coverage, weekly for four weeks (*Owner*)

Check **Indexing → Pages** once a week. Expect old WordPress URLs to move to "Page with redirect" or "Alternate page with proper canonical tag". Look for a rise in **"Not found (404)"** or **"Server error"**.

| Week of | Indexed | Not indexed | New 404s? | Notes |
|---|---|---|---|---|
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

**Passed by Claude:** checks 1 and 4, and the technical part of 2, 3, 5 and 6.

**Open, for the owner:**
- sitemap submission;
- URL inspection;
- GA4 Realtime;
- the test message;
- four weekly coverage checks.
