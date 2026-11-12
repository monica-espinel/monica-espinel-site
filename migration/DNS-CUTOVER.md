# DNS cutover: monicaespinel.com from WordPress to GitHub Pages

**Who does this:** the owner, at the domain's DNS provider (the registrar, or wherever the DNS records are managed) and in GitHub. Claude does not change DNS.

**What changes:** only the records that point the website to a server: the apex `A` / `AAAA` records and `www`. **Email (MX) and every other record stay as they are.**

**WordPress keeps running** at its host the whole time. Rolling back means putting the old records back (see the end of this guide).

**Good to know before you start:**

- **GitHub user/organization:** `monica-espinel`. Its Pages host is `monica-espinel.github.io`.
- **Repository:** `monica-espinel/monica-espinel-site`. The Pages source is already **GitHub Actions** (done in Phase 5).
- **Expected time:** about 15 minutes of work on the day, plus waiting for DNS (minutes to a few hours) and for the HTTPS certificate (usually under an hour, at most 24 hours). Until the certificate is issued, `https://` visitors see a certificate warning (see step 8), so pick a quiet time.

---

## Where the DNS is: Bluehost (domain registered at GoDaddy)

The domain is **registered at GoDaddy**, but its **nameservers point to Bluehost**: `ns1.bluehost.com` and `ns2.bluehost.com` (owner, 2026-11-12). So **Bluehost hosts the DNS**: every record change in this guide happens in **Bluehost's DNS editor**. Changes in GoDaddy's DNS Records tab have no effect while the nameservers point to Bluehost.

Bluehost's screens change from time to time, so look for these names if a label differs.

- **Where the records are:** Bluehost account → **Domains** → monicaespinel.com → **DNS** (in older accounts, **cPanel → Zone Editor**).
- **TTL:** if Bluehost doesn't accept **300**, choose its lowest option. Rollback then takes as long as that TTL instead of 5 minutes.
- **Records you'll see:**
  - The apex `A` (`@`) and usually `www` point to Bluehost's server. You change these.
  - Bluehost also creates host records such as `mail`, `ftp`, `cpanel`, `webmail`, `autodiscover`, and `_domainconnect`. Leave them as they are: they don't affect the website.
- **Email:** look at the `MX` records.
  - Pointing to Bluehost (for example `mail.monicaespinel.com` or a Bluehost host name): the mailboxes are at Bluehost.
  - Pointing to Google or Microsoft: email is elsewhere.
  - Either way, the cutover doesn't touch them (step 9).
- [x] **Bluehost's CDN / Cloudflare integration: turned off** by the owner (2026-11-12). GitHub must see its own IP addresses to issue the certificate, so leave it off.
- **Names in the form:**
  - `@` means the apex, `monicaespinel.com`;
  - write `www`, not `www.monicaespinel.com`;
  - for the GitHub verification record, write only the part before `.monicaespinel.com`, for example `_github-pages-challenge-monica-espinel`;
  - `TXT` values go in without quotes.
- **GoDaddy, the registrar:** nothing changes there for the cutover. Do check the domain's **Forwarding** setting at GoDaddy is off.

### The current records (from the owner's Bluehost zone export, 2026-11-12)

These are the values to restore if you roll back. DNS records are public, but the export file itself isn't committed.

| Record | Current value | At cutover |
|---|---|---|
| `@` `A` | `66.235.200.147` (the WordPress site). TTL now **15 minutes** (owner, 2026-11-12; the zone export showed 3600) | **Replace** with GitHub's four `A` records (step 6) |
| `www` `CNAME` | `monicaespinel.com` | **Replace** with `monica-espinel.github.io` (step 7) |
| `@` `AAAA`, `CAA`, `ALIAS`/`ANAME` | none | nothing to delete. Adding GitHub's `AAAA` records is optional. |
| `@` `MX` (5 records) | Google Workspace: `aspmx.l.google.com` (1), `alt1`/`alt2.aspmx.l.google.com` (5), `alt3`/`alt4.aspmx.l.google.com` (10) | **keep** |
| `google._domainkey` `TXT` | Google Workspace DKIM key | **keep** |
| `@` `TXT` `google-site-verification=…` (2 records: `AMn5o…` and `wHV2C…`) | Search Console verification | **keep** (step 4) |
| `@` `TXT` `v=spf1 +a +mx +ip4:162.241.252.140 +include:websitewelcome.com ~all` | SPF (email) | **keep for now** (see the note below) |
| `_github-challenge-monica-espinel-org` `TXT` | GitHub *organization* domain verification | **keep** (not the same as the Pages record in step 3) |
| `calendar`, `drive` `CNAME` → `ghs.googlehosted.com`; `zqlnqvtpi7av` `CNAME` → `…dv.googlehosted.com` | Google Workspace | **keep** |
| `autoconfig`, `autodiscover`, `cpanel`, `ftp`, `webdisk`, `webmail`, `whm` `A` → `162.241.252.140`; `localhost`; `default._domainkey`; `_cpanel-dcv-test-record`; `_acme-challenge*`; `_autodiscover._tcp` `SRV` | Bluehost/cPanel services | **keep** until Bluehost is cancelled; they don't affect the website |

**Email is Google Workspace**, not Bluehost: the mailboxes don't depend on the Bluehost plan. Only the DNS zone does.

**Note on SPF (an email record, outside this migration's scope):**

- The SPF record authorizes `+a`, the apex's `A` record IPs. After cutover, those are GitHub's IPs, so `+a` would authorize GitHub's Pages servers to send mail as monicaespinel.com. They don't send mail, so the risk is low but untidy.
- The record also doesn't include Google (`include:_spf.google.com`), so mail sent from Google Workspace relies on DKIM to pass checks.
- When the DNS moves off Bluehost (see *After cutover*), it's a good moment to have whoever manages the email set SPF to `v=spf1 include:_spf.google.com ~all`. That's the Google-only form, once nothing sends mail from Bluehost any more.
- This guide doesn't change it.

**Important for later:** because Bluehost hosts the DNS, and maybe the email too, **cancelling the Bluehost plan would take monicaespinel.com offline**, the new site included. See "Before cancelling WordPress (Bluehost)" under *After cutover*: move the DNS, and email if it's at Bluehost, first.

---

## Timeline at a glance

| When | Step |
|---|---|
| At least 24 hours before | 1. Write down the current records. 2. Lower the TTL to 300. 3. Verify the domain in GitHub. 4. Add the Search Console DNS record. |
| Cutover day, at a quiet time | 5. Set the custom domain in GitHub (before DNS). 6. Point the apex to GitHub. 7. Point `www` to GitHub. 8. Wait for the DNS check and certificate, turn on Enforce HTTPS. 9. Confirm email is untouched. 10. Check both addresses. |
| Afterwards | Raise the TTL again. Phase 7 checks (Search Console, GA4, contact form). |

**Progress (2026-11-12):**
- **Step 1 is done:** the records are written down, except the HSTS check.
- **Step 2 is partly done:** the apex TTL is 15 minutes; the `www` TTL and the 1-hour wait remain.
- **Bluehost's Cloudflare integration is off.** Re-check the apex `A` value afterwards (step 1).
- **Steps 3 and 4** are next.

---

## At least 24 hours before cutover

### 1. Write down the current records

Done: the owner exported the Bluehost zone on 2026-11-12. The values are in the table under *Where the DNS is* above, and these are the rollback values.

- [x] `A` record for the apex: **`66.235.200.147`** (one record; the WordPress site)
- [x] `AAAA` records for the apex: **none**
- [x] `ALIAS`, `ANAME` or `CNAME` on the apex: **none**
- [x] Every record named `www`: **one `CNAME` to `monicaespinel.com`**, nothing else
- [x] `MX` records: **Google Workspace**, five records (`aspmx.l.google.com` priority 1, `alt1`/`alt2` priority 5, `alt3`/`alt4` priority 10)
- [x] `TXT` records:
  - SPF `v=spf1 +a +mx +ip4:162.241.252.140 +include:websitewelcome.com ~all`
  - two `google-site-verification` records (`AMn5o…`, `wHV2C…`)
  - `_github-challenge-monica-espinel-org`
  - DKIM `google._domainkey` and `default._domainkey`
  - cPanel/ACME records
- [x] `CAA` records: **none**, so certificate issuance isn't restricted
- [x] TTL: **3600** in the export; the apex `A` is now **15 minutes** (step 2)

Where things are hosted (needed to cancel WordPress safely later):

- [x] **The nameservers:** `ns1.bluehost.com` and `ns2.bluehost.com`, so Bluehost hosts the DNS. Leave them as they are for the cutover.
- [x] **Who provides email:** **Google Workspace** (`MX` → Google), so the mailboxes don't depend on Bluehost.
- [ ] **Whether the WordPress site forces HTTPS in browsers (HSTS).** In a browser, open `https://monicaespinel.com`, then open Developer tools → Network, reload, click the first request, and look under *Response headers* for `Strict-Transport-Security`. Note whether it's there. Step 8 explains why it matters.

**Cloudflare:** Bluehost's Cloudflare integration was on, and the owner turned it off (2026-11-12).
- [ ] **Re-check the apex `A` record** in Bluehost's DNS editor now. Turning Cloudflare off can change it: with the integration on, the apex may have pointed at the proxy rather than the WordPress server.
  - If it's no longer `66.235.200.147`, write down the new value. That is the rollback value.
  - Also check the site still loads on WordPress, which it should.
- [ ] **Confirm Cloudflare is really off.** A copy of the homepage the owner loaded after turning it off still contained Cloudflare's challenge script (`/cdn-cgi/challenge-platform/…`). The change may take up to an hour to apply, or the browser may have shown a cached page. To check:
  1. Open `https://monicaespinel.com` in a private window, open Developer tools → Network, and reload.
  2. Click the first request, and look under *Response headers*.
  3. `server: cloudflare` or a `cf-ray` header means Cloudflare is still active. Wait, then check Bluehost's settings again. Neither header means it's off.
  4. In the same place, note whether `strict-transport-security` is there (the HSTS item above).

### 2. Lower the TTL to 300 seconds

- [x] Apex `A` record: TTL is **15 minutes** in Bluehost's editor (owner, 2026-11-12).
  - If Bluehost offers 5 minutes (300 s, the brief's value), use it.
  - If 15 minutes is the lowest option, keep it. The only difference is that a rollback takes about 15 minutes instead of 5.
- [ ] Set the **`www` `CNAME`** to the same TTL.
- [ ] Wait at least as long as the **old** TTL before starting the cutover. The old TTL was 3600 (1 hour, from the zone export), so wait at least an hour after the last TTL change; doing it the day before covers that. Until then, resolvers may still cache the old value.

This keeps the switch, and any rollback, to about 5 minutes.

### 3. Verify the domain in GitHub (prevents domain takeover)

Verifying the domain stops anyone else's GitHub Pages site from claiming `monicaespinel.com` while DNS points at GitHub.

- [ ] Go to GitHub → the **monica-espinel** organization → **Settings → Pages → Add a domain**, and enter `monicaespinel.com`. (For a personal account, it's **Settings → Pages** in your user settings.)
- [ ] GitHub shows a `TXT` record named like `_github-pages-challenge-monica-espinel.monicaespinel.com`, with a code value. Add exactly that `TXT` record at the DNS provider.
- [ ] Back in GitHub, click **Verify**. It can take a few minutes for the record to be visible.

This TXT record lives on its own `_github-pages-challenge-…` name, so it doesn't touch any existing record. The zone already has `_github-challenge-monica-espinel-org`: that's the *organization's* verified-domain record. Keep it, but it isn't the Pages one, so this step is still needed.

### 4. Search Console: verify by DNS (not the meta tag)

The WordPress site proves ownership to Google with a `google-site-verification` meta tag in its pages. The new site doesn't have that tag, as the brief decided. If you skip this step, Search Console loses verification at cutover.

**This may already be done:** the zone already has two `google-site-verification` `TXT` records, `AMn5o…` and `wHV2C…`, the second being the same token as the old site's meta tag. In Search Console, open **Settings → Ownership verification** for the monicaespinel.com property(ies). If **Domain name provider** is listed as a verified method, skip to step 5. Either way, never delete those two records.

- [ ] Otherwise: in Google Search Console, **add a Domain property** for `monicaespinel.com`, or for the existing property open **Settings → Ownership verification → add a method → Domain name provider**. Google shows a value like `google-site-verification=…`.
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
- [ ] **Delete** any `ALIAS`, `ANAME` or `CNAME` record on the apex (step 1). It conflicts with the new `A` records: the provider either refuses them, or keeps sending some visitors to WordPress.
- [ ] **Add four** `A` records for the apex (`@`), TTL 5 minutes, or Bluehost's lowest (15 minutes):

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

Today `www` is a `CNAME` to `monicaespinel.com`, and nothing else is on `www`.

- [ ] **Delete every existing record named `www`**: `A`, `AAAA`, `CNAME`, and anything else such as `TXT` or `MX` on `www`. They're all in your step 1 notes, for rollback.
- [ ] **Add** one `CNAME`, TTL 5 minutes, or Bluehost's lowest (15 minutes):

| Type | Name | Value |
|---|---|---|
| CNAME | www | `monica-espinel.github.io` |

The value is the bare host name: no `https://`, and no `/monica-espinel-site`. Some providers want a trailing dot (`monica-espinel.github.io.`).

If the provider refuses the `CNAME` with an error like "conflicts with an existing record", a `www` record is still there: delete it and try again.

### 8. Wait for the DNS check and the certificate, then turn on HTTPS

- [ ] In **Settings → Pages**, click **Check again** until it shows **"DNS check successful"**. That takes minutes to a few hours after steps 6–7, depending on the old TTL.
- [ ] Wait until the Pages settings show the certificate as issued. Until then, the **Enforce HTTPS** box is greyed out with a message about the certificate.
- [ ] Tick **Enforce HTTPS**.

**Expect a short window of certificate warnings. This is normal: don't roll back because of it.** From the moment DNS points to GitHub until the certificate for monicaespinel.com is issued (usually under an hour, at most 24 hours), `https://monicaespinel.com` shows a "Your connection is not private" warning, because GitHub briefly serves its generic certificate. Plain `http://` works during that time for most visitors.

There's one exception. If step 1 found `Strict-Transport-Security` (HSTS) on the WordPress site, browsers that visited it before always use `https://`, and they show the certificate error **without a way to continue** until the certificate is issued. That's expected too, and it ends once the certificate is issued. It's one more reason to pick a quiet time.

- Do the cutover at a quiet time, for example in the evening, US Eastern time.
- Only roll back if the certificate still isn't issued after 24 hours, or if something else is wrong (wrong site, broken pages).

With the apex as the custom domain and `www` pointing to GitHub, GitHub redirects `www.monicaespinel.com` to `monicaespinel.com` automatically. That matches the WordPress site, whose canonical address is the apex.

**If the domain has `CAA` records** (step 1), one must allow `letsencrypt.org`, the certificate authority GitHub uses. Otherwise the certificate can't be issued.

#### If the certificate isn't issued within an hour or two

Don't just wait the full 24 hours. Go through the usual causes:

1. **Settings → Pages** says what's wrong: read the message next to the custom domain or the HTTPS box.
2. **The DNS check isn't passing.** An old record is still there. Check that:
   - the apex has only GitHub's four `A` records (and its `AAAA` records, if you added them);
   - no WordPress `A`, `AAAA`, `ALIAS` or `ANAME` record is left on the apex;
   - `www` has only the `CNAME`.
3. **Cloudflare** is still proxying (orange cloud). Set the apex and `www` records to "DNS only".
4. **A `CAA` record** doesn't allow `letsencrypt.org`. Add `0 issue "letsencrypt.org"`.
5. **After fixing DNS**, re-trigger the certificate, as GitHub's documentation describes:
   - in **Settings → Pages**, remove the custom domain and **Save**;
   - enter `monicaespinel.com` again and **Save**.

   Issuance usually follows within minutes.

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
- [ ] **Before cancelling WordPress (Bluehost)**, move what Bluehost still provides. **This applies here**, because Bluehost hosts the DNS. Do it as its own step, at least a few days after the cutover has proved stable, not on cutover day.
  1. **Copy every DNS record** from Bluehost's DNS editor to GoDaddy: GoDaddy → My Products → monicaespinel.com → DNS → DNS Records. GoDaddy can host the DNS for free, since it's the registrar. That includes:
     - GitHub's four apex `A` records (and `AAAA`, if added), and the `www` `CNAME`;
     - the `MX` records, and the SPF and DKIM `TXT` records;
     - the Search Console `google-site-verification` `TXT` record;
     - the `_github-pages-challenge-monica-espinel` `TXT` record.
  2. **Email** is Google Workspace (the `MX` records point to Google), so the mailboxes stay. Copy the Google records in step 1:
     - the five `MX` records;
     - `google._domainkey`;
     - the `calendar`, `drive` and `zqlnqvtpi7av` `CNAME`s;
     - both `google-site-verification` `TXT` records;
     - the SPF record, ideally updated as in the SPF note above.

     Leave out the Bluehost/cPanel-only records:
     - `autoconfig`, `autodiscover`, `cpanel`, `ftp`, `webdisk`, `webmail`, `whm` and `localhost`;
     - `default._domainkey`, `_cpanel-dcv-test-record` and `_acme-challenge*`;
     - the `_autodiscover._tcp` `SRV` record.
  3. **Switch the nameservers** at GoDaddy, under the **Nameservers** tab, from `ns1.bluehost.com` / `ns2.bluehost.com` back to **GoDaddy's default nameservers** (`ns##.domaincontrol.com`; GoDaddy fills them in).
  4. **Wait at least a day**, then check that the site, `www`, HTTPS and email all still work.
  5. **Only then** cancel the Bluehost plan.

  Skipping steps 1–3 means monicaespinel.com stops resolving, and the new site with it, as soon as Bluehost deletes the account.
- [ ] **Formspree:** if reCAPTCHA is on in the form settings, turn it off to get the inline thank-you message. The honeypot covers spam. Messages arrive either way.

---

## Rollback (if something is seriously wrong)

1. At the DNS provider, delete the GitHub `A` (and `AAAA`) records and put back the WordPress apex `A` / `AAAA` records written down in step 1.
2. Delete the `www` `CNAME`, and put back every old `www` record from step 1.
3. With the lowered TTL (15 minutes, or 5 if Bluehost allows it), most visitors see WordPress again within about 15 minutes.
4. Leave the GitHub custom domain setting as it is, or remove it: either way WordPress serves the site once DNS points back.
5. Tell Claude what went wrong, so it can be fixed before the next attempt.

The Search Console DNS record and the GitHub domain-verification record can stay. They don't affect where the site is served from.
