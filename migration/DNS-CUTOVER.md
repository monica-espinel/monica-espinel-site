# DNS cutover: monicaespinel.com from WordPress to GitHub Pages

**Who does this:** the owner, at the domain's DNS provider (the registrar, or wherever the DNS records are managed) and in GitHub. Claude does not change DNS.

**What changes:** only the records that point the website to a server: the apex `A` / `AAAA` records and `www`. **Email (MX) and every other record stay as they are.**

**WordPress keeps running** at its host the whole time. Rolling back means putting the old records back (see the end of this guide).

**Good to know before you start:**

- **GitHub user/organization:** `monica-espinel`. Its Pages host is `monica-espinel.github.io`.
- **Repository:** `monica-espinel/monica-espinel-site`. The Pages source is already **GitHub Actions** (done in Phase 5).
- **Expected time:** about 15 minutes of work on the day, plus waiting for DNS (minutes to a few hours) and for the HTTPS certificate (usually under an hour, at most 24 hours). Until the certificate is issued, `https://` visitors see a certificate warning (see step 8), so pick a quiet time.

---

## Timeline at a glance

| When | Step |
|---|---|
| At least 24 hours before | 1. Write down the current records. 2. Lower the TTL to 300. 3. Verify the domain in GitHub. 4. Add the Search Console DNS record. |
| Cutover day, at a quiet time | 5. Set the custom domain in GitHub (before DNS). 6. Point the apex to GitHub. 7. Point `www` to GitHub. 8. Wait for the DNS check and certificate, turn on Enforce HTTPS. 9. Confirm email is untouched. 10. Check both addresses. |
| Afterwards | Raise the TTL again. Phase 7 checks (Search Console, GA4, contact form). |

---

## At least 24 hours before cutover

### 1. Write down the current records

At the DNS provider, take a screenshot or copy every record for `monicaespinel.com`. You need these values to roll back. In particular, note:

- [ ] `A` record(s) for the apex (`@` or `monicaespinel.com`): the WordPress host's IP address
- [ ] `AAAA` record(s) for the apex, if any
- [ ] **every** record named `www` (`CNAME`, `A`, `AAAA`, and anything else on `www`), with its value
- [ ] all `MX` records (email)
- [ ] all `TXT` records, especially `v=spf1 …` (email) and any `google-site-verification=…`
- [ ] any `CAA` records
- [ ] the current **TTL** of the apex and `www` records

**If the DNS is on Cloudflare** (orange cloud icons): set the apex and `www` records to **DNS only** (grey cloud) at cutover. GitHub needs to see its own IP addresses to issue the certificate.

### 2. Lower the TTL to 300 seconds

- [ ] Set the TTL of the apex `A` / `AAAA` records and the `www` record to **300** (5 minutes).
- [ ] Wait at least as long as the **old** TTL (often 1 to 24 hours) before the cutover. Until then, resolvers may still cache the old value for the old TTL.

This keeps the switch, and any rollback, to about 5 minutes.

### 3. Verify the domain in GitHub (prevents domain takeover)

Verifying the domain stops anyone else's GitHub Pages site from claiming `monicaespinel.com` while DNS points at GitHub.

- [ ] Go to GitHub → the **monica-espinel** organization → **Settings → Pages → Add a domain**, and enter `monicaespinel.com`. (For a personal account, it's **Settings → Pages** in your user settings.)
- [ ] GitHub shows a `TXT` record named like `_github-pages-challenge-monica-espinel.monicaespinel.com`, with a code value. Add exactly that `TXT` record at the DNS provider.
- [ ] Back in GitHub, click **Verify**. It can take a few minutes for the record to be visible.

This TXT record lives on its own `_github-pages-challenge-…` name, so it doesn't touch any existing record.

### 4. Search Console: verify by DNS (not the meta tag)

The WordPress site proves ownership to Google with a `google-site-verification` meta tag in its pages. The new site doesn't have that tag, as the brief decided. If you skip this step, Search Console loses verification at cutover.

- [ ] In Google Search Console, **add a Domain property** for `monicaespinel.com`, or for the existing property open **Settings → Ownership verification → add a method → Domain name provider**. Google shows a value like `google-site-verification=…`.
- [ ] At the DNS provider, **add** a `TXT` record on the apex (`@`) with that value.
  - **Add a new record, don't edit an existing one:** the apex may already have an SPF `TXT` record (`v=spf1 …`) for email, and it must stay.
- [ ] In Search Console, click **Verify**.

A Domain property covers `http`, `https`, `www` and the apex in one place.

---

## Cutover day

Check first that the latest deploy on GitHub passed: **Actions → Deploy site to GitHub Pages**, the newest run on `main` is green.

### 5. Set the custom domain in GitHub (before changing DNS)

Do this **first**, while DNS still points to WordPress. If you change DNS first, GitHub receives requests for monicaespinel.com before it knows the domain, and visitors get a GitHub "There isn't a GitHub Pages site here" error until this step is done. GitHub's own documentation recommends this order. The brief lists this step after the DNS records; doing it first changes nothing else. The domain verification in step 3 protects the domain in the meantime.

- [ ] In the repository: **Settings → Pages → Custom domain**, enter `monicaespinel.com` and click **Save**.
- [ ] GitHub now shows the DNS check as **failing**. That's expected until steps 6–7 are done. Visitors still see WordPress, because DNS hasn't changed.

From now on, the github.io project address redirects to `monicaespinel.com`, which is still WordPress until step 6.

`static/CNAME` in the repository already contains `monicaespinel.com`. With GitHub Actions deployments, this setting is what counts.

### 6. Point the apex to GitHub Pages

- [ ] **Delete** the apex `A` record(s) that point to the WordPress host.
- [ ] **Add four** `A` records for the apex (`@`), TTL 300:

| Type | Name | Value |
|---|---|---|
| A | @ | `185.199.108.153` |
| A | @ | `185.199.109.153` |
| A | @ | `185.199.110.153` |
| A | @ | `185.199.111.153` |

- [ ] **If the apex had `AAAA` records** pointing to the WordPress host, delete them. Then either leave IPv6 out, or (recommended by GitHub) add these four `AAAA` records:

| Type | Name | Value |
|---|---|---|
| AAAA | @ | `2606:50c0:8000::153` |
| AAAA | @ | `2606:50c0:8001::153` |
| AAAA | @ | `2606:50c0:8002::153` |
| AAAA | @ | `2606:50c0:8003::153` |

Never leave old `AAAA` records pointing to WordPress next to the new `A` records: IPv6 visitors would still reach WordPress.

### 7. Point `www` to GitHub Pages

A `CNAME` can't share its name with any other record, so clear `www` first.

- [ ] **Delete every existing record named `www`**: `A`, `AAAA`, `CNAME`, and anything else such as `TXT` or `MX` on `www`. They're all in your step 1 notes, for rollback.
- [ ] **Add** one `CNAME`, TTL 300:

| Type | Name | Value |
|---|---|---|
| CNAME | www | `monica-espinel.github.io` |

The value is the bare host name: no `https://`, and no `/monica-espinel-site`. Some providers want a trailing dot (`monica-espinel.github.io.`).

If the provider refuses the `CNAME` with an error like "conflicts with an existing record", a `www` record is still there: delete it and try again.

### 8. Wait for the DNS check and the certificate, then turn on HTTPS

- [ ] In **Settings → Pages**, click **Check again** until it shows **"DNS check successful"**. That takes minutes to a few hours after steps 6–7, depending on the old TTL.
- [ ] Wait until the Pages settings show the certificate as issued. Until then, the **Enforce HTTPS** box is greyed out with a message about the certificate.
- [ ] Tick **Enforce HTTPS**.

**Expect a short window of certificate warnings. This is normal: don't roll back because of it.** From the moment DNS points to GitHub until the certificate for monicaespinel.com is issued (usually under an hour, at most 24 hours), `https://monicaespinel.com` shows a "Your connection is not private" warning, because GitHub briefly serves its generic certificate. Plain `http://` works during that time.

- Do the cutover at a quiet time, for example in the evening, US Eastern time.
- Only roll back if the certificate still isn't issued after 24 hours, or if something else is wrong (wrong site, broken pages).

With the apex as the custom domain and `www` pointing to GitHub, GitHub redirects `www.monicaespinel.com` to `monicaespinel.com` automatically. That matches the WordPress site, whose canonical address is the apex.

**If the domain has `CAA` records** (step 1), one must allow `letsencrypt.org`, the certificate authority GitHub uses. Otherwise the certificate can't be issued.

### 9. Confirm email is untouched

- [ ] The `MX` records are exactly as written down in step 1.
- [ ] The SPF `TXT` record (`v=spf1 …`) and any DKIM records are still there.
- [ ] Send yourself an email at the domain's address and check it arrives.

### 10. Check that it works (Phase 6 is done when both load)

Use a private browser window, and phone data if possible, so no cached WordPress pages show.

- [ ] `https://monicaespinel.com` loads the new site with a valid padlock, without certificate warnings.
- [ ] `https://www.monicaespinel.com` loads with a valid padlock and ends up on `https://monicaespinel.com`.
- [ ] `http://monicaespinel.com` redirects to `https://`.
- [ ] Spot checks:
  - a post, for example `https://monicaespinel.com/beats-of-the-sacred-heart/`
  - an old URL, for example `https://monicaespinel.com/page/2/`, which should land on the homepage
  - `https://monicaespinel.com/feed/`, which should land on the RSS feed
  - the search page
- [ ] **Tell Claude** both addresses load with a valid certificate. That's the brief's acceptance check for this phase.

How do you tell the new site from WordPress? The new site's footer has "To the top ↑" but no "Powered by WordPress".

---

## After cutover

- [ ] Once everything has worked for a day or two, raise the TTL again (for example to 3600).
- [ ] Phase 7 checks: submit the sitemap, URL inspection, a search on the live site, GA4 Realtime, and a test contact message. Claude will list them.
- [ ] Keep WordPress running for **at least 30 days** after cutover (brief: Rollback).
  - Its admin is no longer reachable at `monicaespinel.com/wp-admin`, because that now goes to GitHub.
  - If you need it, use the host's own temporary address or control panel.
- [ ] **Formspree:** if reCAPTCHA is on in the form settings, turn it off to get the inline thank-you message. The honeypot covers spam. Messages arrive either way.

---

## Rollback (if something is seriously wrong)

1. At the DNS provider, delete the GitHub `A` (and `AAAA`) records and put back the WordPress apex `A` / `AAAA` records written down in step 1.
2. Delete the `www` `CNAME`, and put back every old `www` record from step 1.
3. With TTL 300, most visitors see WordPress again within minutes.
4. Leave the GitHub custom domain setting as it is, or remove it: either way WordPress serves the site once DNS points back.
5. Tell Claude what went wrong, so it can be fixed before the next attempt.

The Search Console DNS record and the GitHub domain-verification record can stay. They don't affect where the site is served from.
