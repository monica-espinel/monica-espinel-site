# DNS cutover: monicaespinel.com from WordPress to GitHub Pages

**Who does this:** the owner, at the domain's DNS provider (the registrar, or wherever the DNS records are managed) and in GitHub. Claude does not change DNS.

**What changes:**
- **Step 0:** the DNS moves from Bluehost to GoDaddy, with every record copied unchanged.
- **The cutover:** only the records that point the website to a server change, the apex `A` / `AAAA` records and `www`.

**Email (MX) and every other record stay as they are.**

**WordPress keeps running** at its host the whole time. Rolling back means putting the old records back (see the end of this guide).

**Good to know before you start:**

- **GitHub user/organization:** `monica-espinel`. Its Pages host is `monica-espinel.github.io`.
- **Repository:** `monica-espinel/monica-espinel-site`. The Pages source is already **GitHub Actions** (done in Phase 5).
- **Expected time:** about 15 minutes of work on the day, plus waiting for DNS (minutes to a few hours) and for the HTTPS certificate (usually under an hour, at most 24 hours). Until the certificate is issued, `https://` visitors see a certificate warning (see step 8), so pick a quiet time.

---

## Where the DNS is: moving from Bluehost to GoDaddy

The domain is **registered at GoDaddy**, and its DNS is hosted by **Bluehost** today (nameservers `ns1.bluehost.com` and `ns2.bluehost.com`).

**Decision (owner, 2026-11-12): stop using Bluehost's DNS.** Move it to **GoDaddy**, the registrar, as **step 0**, before the website cutover:
- Step 0 copies every record across unchanged, so the site stays on WordPress and email keeps flowing.
- After a wait of 48 hours, check that nothing changed.
- Steps 1–10 (the cutover) then happen in **GoDaddy's DNS editor**.

Doing one change at a time means any problem has only one possible cause. Once DNS is off Bluehost, cancelling Bluehost later can't take the domain down.

**In GoDaddy** (screens change from time to time, so look for these names if a label differs):
- **The domain:** sign in → **My Products** → monicaespinel.com → **DNS**.
- **The DNS Records tab** lists the records. The **Nameservers** tab sets who hosts the DNS.
- **Names in GoDaddy's form:**
  - `@` means the apex, `monicaespinel.com`;
  - write `www`, not `www.monicaespinel.com`;
  - for other names, write only the part before `.monicaespinel.com`, for example `google._domainkey`;
  - `TXT` values go in without quotes.
- **TTL:** for `@` and `www`, use GoDaddy's lowest option (often 600 seconds, or "custom" with the minimum it allows). For everything else, 1 hour is fine.
- **Forwarding:** on the domain's page, the **Forwarding** section must be off. It would override the `A` records.

---

## Step 0: Move the DNS from Bluehost to GoDaddy (at least 48 hours before the cutover)

Nothing visible changes in this step. The records are copied with the **same values**, so the site stays on WordPress and email stays on Google Workspace.

### 0a. Before switching: check DNSSEC, and have the records ready

- [x] **Check DNSSEC first.** Done 2026-11-12: a DS lookup on `https://dns.google/query?name=monicaespinel.com&rr_type=DS` returned no Answer; the `.com` registry (`192.12.94.30`) has no DS record, so **DNSSEC is off** and switching is safe. To check another time: GoDaddy → monicaespinel.com → **DNS → DNSSEC** (sometimes under the domain's settings), or the same `dns.google` lookup.
  - **No DS records listed** (DNSSEC off, the usual case with Bluehost): continue.
  - **DS records listed:** don't switch yet. They belong to Bluehost's DNS signing keys, and pointing the domain at GoDaddy with them still in place makes it unreachable for most internet users, website and email alike.
    1. **Remove the DS records** at GoDaddy.
    2. **Wait 2 days** for the change to spread.
    3. **Then do the switch.**
    4. **Optionally, turn DNSSEC on again** at GoDaddy afterwards.
- [x] **Have the step 0c table open** before switching, so the records go in within minutes.
- [x] **Pick a quiet time**, for example in the evening or at a weekend. For a few minutes after the switch, GoDaddy's starting zone has no `MX` records (see below).

### 0b. Switch the nameservers to GoDaddy's

- [x] GoDaddy → monicaespinel.com → **DNS → Nameservers → Change nameservers** → choose **GoDaddy's default nameservers** (`ns##.domaincontrol.com`; GoDaddy fills them in). Save.
- [x] Go straight on to step 0c. GoDaddy usually only lets you edit the records once its own nameservers are selected, and it starts with a few default records (for example a "Parked" `@` record).

Nameserver changes spread slowly, over up to 24–48 hours. During that time some visitors still get answers from Bluehost's DNS, and some from GoDaddy's. That's fine as long as both have the same records, so **don't delete anything at Bluehost**. The one exception is cutting over before step 0d is done: then make the same changes in both zones (see "Cutting over before step 0d" under Cutover day).

**Enter the five `MX` records first** in step 0c, straight after switching. Until they exist at GoDaddy, a sender whose DNS lookup reaches GoDaddy's starting zone finds no `MX` record. It then tries the domain's own address, GoDaddy's parking server, which can reject the message, so it may **bounce** instead of being retried. The risk is small, because few lookups reach GoDaddy in the first minutes, but entering `MX` first keeps it to a few minutes.

### 0c. Enter the records at GoDaddy

In **DNS Records**, make the zone match this list exactly. **Start with the five `MX` rows**, then the rest. Edit GoDaddy's default records where they exist: for example, change the "Parked" `@` `A` record to the WordPress IP, and keep `www` → `@`.

| Type | Name | Value | Notes |
|---|---|---|---|
| A | `@` | `162.241.252.140` | WordPress at Bluehost, **until the cutover** (step 6). TTL: lowest option |
| CNAME | `www` | `@` (i.e. `monicaespinel.com`) | changed to GitHub at the cutover (step 7). TTL: lowest option |
| MX | `@` | `aspmx.l.google.com`, priority **1** | Google Workspace email |
| MX | `@` | `alt1.aspmx.l.google.com`, priority **5** | |
| MX | `@` | `alt2.aspmx.l.google.com`, priority **5** | |
| MX | `@` | `alt3.aspmx.l.google.com`, priority **10** | |
| MX | `@` | `alt4.aspmx.l.google.com`, priority **10** | |
| TXT | `@` | `v=spf1 +a +mx +ip4:162.241.252.140 +include:websitewelcome.com ~all` | SPF, unchanged for now (see the SPF note below) |
| TXT | `@` | `google-site-verification=AMn5oaCp-54x9IBt6hZju8cJ7LCJqOBsnQ6gNpy2Fk0` | Search Console |
| TXT | `@` | `google-site-verification=wHV2CvCki23M20q4s7tT_QoJS1UpK66yUkJKxjk4ymI` | Search Console |
| TXT | `google._domainkey` | the Google DKIM key, below | Google Workspace DKIM |
| TXT | `default._domainkey` | the Bluehost DKIM key, below | mail sent by WordPress at Bluehost; remove when Bluehost is cancelled |
| TXT | `_github-challenge-monica-espinel-org` | `de2ec6c8aa` | GitHub organization domain verification |
| CNAME | `calendar` | `ghs.googlehosted.com` | Google Workspace |
| CNAME | `drive` | `ghs.googlehosted.com` | Google Workspace |
| CNAME | `zqlnqvtpi7av` | `gv-ujqze7omrgeoxy.dv.googlehosted.com` | Google verification |

Copy the two DKIM values exactly, as one line each:

`google._domainkey`:

```
v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAk5kTuAHVp81lVTszqUeGM8qztGHXuAELCYseNevgr6C4e3ufMTIf8xURxOGeCMxKvtSPef1GreqW2ANDIy/oODXA9rzP7Vjvl+Rxn9kWlEl4I3mxW5tSX8BZwiY+IfJlN9GHnVj3pUJk0vjrb5Bh322tDsvtyJGl3CqyFzmtIe/cD3cnQXW3bh5SeqvZ9N2C2eyP8gpJwsGLFBqPnXYZ6dBH28fvHHyNzDq/2jZXi6FGRQ89iFgOqqH7k/X+mo1pnudPZYP5BW7bWljfIDYCMrztHUkUfD/pordHxYX+mfFrskN9ghDUQIZMfQYwM3LH8R4Nrjtr46pvMVnyyP1EpQIDAQAB
```

`default._domainkey`:

```
v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyKM7FcQibzJC2gl0g3NKGrayKF7hfESh4aSAZ19znnt/nUMRdBR7zC1MfHQmq87Vvd/fB/SPZCMT4G4JuPLjb2uTTIb13gJyk+lF+L6hJTz+Qeln2d5uOwUaBQDpxvpfHcrOp6GBfzzBYphu0YTBPzbQed5qEKMToVfU5CKTjtNI9WHO5K7kdfeBm9OxP0vBu68Ft+PjdyqCYrONs6GSqKTu1W8fFHtAlVGwdiPXBeTx2XNPp6BhgHOsduNPAhNW3+d3IFwjbGwJk6ef4C6yc9Z8RchWkzVK5IY6HHt72xcjmeVCUrbqmBMa4qwgqnw6d34fxdQyyj/WxR5JYK6ITwIDAQAB;
```

**Don't copy these Bluehost/cPanel records.** They only serve Bluehost's control panel, its own mail tools, and its certificates:
- `autoconfig`, `autodiscover`, `cpanel`, `ftp`, `webdisk`, `webmail`, `whm`, `localhost`
- `_acme-challenge`, `_acme-challenge.autodiscover`, `_acme-challenge.mail`
- both `_cpanel-dcv-test-record` `TXT` records
- the `_autodiscover._tcp` `SRV` record

The WordPress site keeps working without them. Its own certificate renews over HTTP while the `@` record points to Bluehost.

- [x] Done 2026-11-12: GoDaddy's export matched the table 16/16, with `_dmarc` and `_domainconnect` removed. A spot-check by Claude at `ns11.domaincontrol.com` found no `_domainconnect`, `_dmarc`, `ftp`, `pay`, `shop`, `email`, `mail` or cPanel names, no `AAAA` and no wildcard. Delete any other default record GoDaddy added that isn't in the table. **Keep `_domainconnect` if GoDaddy created it**: it's harmless.

### 0d. Check, at least 48 hours later

Wait **a full 48 hours** after the switch in 0b. The `.com` registry's pointer to a domain's nameservers is cached for up to 2 days, so until then some visitors' DNS still asks Bluehost. GoDaddy showing the nameservers as "active" only means the registrar has the change, not that everyone uses it.

- [ ] At least 48 hours have passed since 0b.
- [ ] Public DNS uses GoDaddy: on `https://dns.google`, look up `monicaespinel.com` with type **NS**. The answer must list `ns##.domaincontrol.com`, not `ns1/ns2.bluehost.com`.
- [ ] `https://monicaespinel.com` still shows the WordPress site, with a valid padlock.
- [ ] Email to and from the domain works: send one each way.
- [ ] In Google Workspace admin (Apps → Gmail → Authenticate email), DKIM still shows as authenticating, if you use it.
- [ ] Optional: an online "DNS lookup" tool (for example Google's `dns.google`) returns the values above for `monicaespinel.com` (`A`, `MX`, `TXT`) and `www` (`CNAME`).

Then continue with steps 1–4 and the cutover, all at **GoDaddy**.

To cut over before these 48 hours are up, see "Cutting over before step 0d" under Cutover day.

**If something goes wrong in step 0:** put the nameservers back to `ns1.bluehost.com` and `ns2.bluehost.com` at GoDaddy. Bluehost's zone is still there untouched.

---

### The current records (Bluehost zone export, 2026-11-12, after Cloudflare was turned off)

These are the values to restore if you roll back:

| Record | Value | At cutover |
|---|---|---|
| `@` `A` | **`162.241.252.140`** (WordPress at Bluehost). It was `66.235.200.147` while Bluehost's Cloudflare integration was on. | **Replace** with GitHub's four `A` records (step 6) |
| `www` `CNAME` | `monicaespinel.com` | **Replace** with `monica-espinel.github.io` (step 7) |
| `@` `AAAA`, `CAA`, `ALIAS`/`ANAME` | none | nothing to delete. Adding GitHub's `AAAA` records is optional. |
| everything else in the step 0c table | as listed | **keep** |

**Email is Google Workspace**, not Bluehost, so the mailboxes never depended on the Bluehost plan.

**Note on SPF (an email record, outside this migration's scope):**
- The SPF record authorizes `+a`, the apex's `A` record IPs. After cutover, those are GitHub's IPs, so `+a` would authorize GitHub's Pages servers to send mail as monicaespinel.com. They don't send mail, so the risk is low but untidy.
- The record also doesn't include Google (`include:_spf.google.com`), so mail sent from Google Workspace relies on DKIM to pass checks.
- When Bluehost is cancelled and nothing sends mail from it any more, have whoever manages the email set SPF to `v=spf1 include:_spf.google.com ~all`, and remove `default._domainkey`.
- This guide doesn't change either.

---

## Timeline at a glance

| When | Step |
|---|---|
| At least 48 hours before | 0. Check DNSSEC, move the DNS from Bluehost to GoDaddy with all records unchanged, wait 48 hours, then check site and email. |
| At least 24 hours before | 1. Write down the current records. 2. Lower the TTL to 300. 3. Verify the domain in GitHub. 4. Add the Search Console DNS record. |
| Cutover day, at a quiet time (before 0d is done: in both zones, see below) | 5. Set the custom domain in GitHub (before DNS). 6. Point the apex to GitHub. 7. Point `www` to GitHub. 8. Wait for the DNS check and certificate, turn on Enforce HTTPS. 9. Confirm email is untouched. 10. Check both addresses. |
| Afterwards | Raise the TTL again. Phase 7 checks (Search Console, GA4, contact form). |

**Progress (2026-11-12):**
- **Step 1 is done:** the records are written down (new Bluehost export after turning off Cloudflare: apex `A` `162.241.252.140`). HSTS checked by Claude, 2026-11-12 at 22:00: none (see step 1).
- **Bluehost's Cloudflare integration is off**, confirmed by Claude, 2026-11-12 at 22:00: the homepage answers with `Server: Apache`, without `cf-ray`, and has no `/cdn-cgi/challenge-platform/` script.
- **Step 0a: DNSSEC is off** (no DS record at the `.com` registry).
- **Step 0b done** (2026-11-12, about 11:55 US Eastern): the nameservers were switched to GoDaddy's, `ns11.domaincontrol.com` and `ns12.domaincontrol.com`.
- **Step 0c done** (12:00):
  - The records were imported from a zone file built from the Bluehost export.
  - GoDaddy's export matches it **16/16 records**, with values and TTLs identical.
  - **Correction (Claude, 2026-11-12 at 22:00): the two DKIM keys are not equal. Fix them before the cutover; see "Fix the two DKIM records" below.** The other records match.
  - GoDaddy's default `_dmarc` record was removed (not in the Bluehost zone), and so was `_domainconnect`.
- **Early email test (2026-11-12, after 0c):** a message to the domain was received, and the reply went out. Both directions work.
- **Step 5 done early (2026-11-12):** the custom domain is saved in GitHub. Its DNS check fails until steps 6–7 (`NotServedByPagesError`), as expected.
- **Step 4 done:** Search Console is verified through DNS ("Domain name provider"), so nothing needed adding.
- **Step 3 done:** monicaespinel.com is a verified domain for GitHub Pages in the monica-espinel organization (2026-11-12).
- **Early NS check (2026-11-12):** `dns.google` already returns `ns11/ns12.domaincontrol.com`, answered by GoDaddy's nameservers. This is Google's resolver only; others can cache Bluehost's nameservers until the 48 hours are up.
- **Checks by Claude (2026-11-12 at 22:00 US Eastern), read-only, nothing changed:**
  - **The `.com` registry** returns `ns11/ns12.domaincontrol.com`, with a 172800 s (48 h) TTL.
  - **NS lookups:** Google (`8.8.8.8`), Cloudflare (`1.1.1.1`), Quad9 (`9.9.9.9`) and OpenDNS all return GoDaddy's nameservers. Other resolvers can still cache Bluehost's until about 2026-11-14 at 12:00.
  - **The GoDaddy zone, queried at `ns11.domaincontrol.com`, matches the step 0c table** for:
    - `A`: `162.241.252.140`
    - the 5 `MX`
    - SPF and both `google-site-verification` records
    - `www`, `calendar`, `drive` and `zqlnqvtpi7av`
    - both `_github-…` `TXT` records
    - no `AAAA`, `CAA` or `_dmarc` record
    - **Except the two DKIM keys**, see below.
  - **Step 2 is in place:** `@` `A` and `www` `CNAME` have a **600 s** TTL at GoDaddy. Nothing needs changing.
  - **The latest deploy on `main` is green** (Deploy site to GitHub Pages, Phase 5 merge).
  - **GitHub Pages:** custom domain `monicaespinel.com`, build type GitHub Actions, no certificate yet, Enforce HTTPS off. Expected before steps 6–7.
- **DKIM fixed (owner, 2026-11-12), re-checked by Claude:**
  - Both `google._domainkey` and `default._domainkey` now match the step 0c values character for character, as one record each.
  - Checked at `ns11` and `ns12.domaincontrol.com`, at Bluehost, and through `8.8.8.8` and `1.1.1.1`.
  - The `A`, `MX`, SPF/verification `TXT` and `www` records are unchanged.
  - **Google Workspace admin confirms it (owner's screenshot, 2026-11-12):** Apps → Gmail → Authenticate email shows "Status: Authenticating email with DKIM" for monicaespinel.com, and the key it shows matches the published `google._domainkey`. Don't click "Generate new record" or "Stop authentication". The "You must update the DNS records" text on that page is Google's standing setup note.
- **Fix the two DKIM records at GoDaddy (owner, before the cutover), done, kept for reference:**
  - **The problem:** in GoDaddy's zone, both keys have the three characters `" "` (quote, space, quote) inside them:
    - `google._domainkey`: between `…N2C2` and `eyP8g…`
    - `default._domainkey`: between `…P0vBu` and `68Ft+…`

    That is where the zone file split each long value into two strings, and the import kept the quotes as text. Bluehost's copies are correct.
  - **Why it matters:** with the key as it is now, Gmail's DKIM signature on Workspace mail fails for anyone whose DNS asks GoDaddy. The SPF record doesn't include Google, so such mail passes neither check, and it's more likely to land in spam. The early email test still worked because delivery doesn't require DKIM.
  - **To fix:**
    1. GoDaddy → DNS Records → edit the `TXT` record `google._domainkey`.
    2. Replace its whole value with the one-line value under step 0c, pasted as is, without quotes. GoDaddy splits long values itself.
    3. Save. Do the same for `default._domainkey`.
    4. Tell Claude, who will re-check both keys against Bluehost's.
    5. Then, in Google Workspace admin (Apps → Gmail → Authenticate email), check that DKIM shows as authenticating.
  - This only corrects the copy from step 0. It doesn't change the email setup.
- **Cutover started (2026-11-12, late evening): GoDaddy done, checked by Claude.**
  - The owner imported [`godaddy-cutover.txt`](godaddy-cutover.txt) after deleting the old `@` `A` and `www` `CNAME`.
  - `ns11` and `ns12.domaincontrol.com` serve:
    - GitHub's four `A` and four `AAAA` records;
    - `www` `CNAME` `monica-espinel.github.io`;
    - all at 600 s.
  - `MX`, SPF, both verification `TXT` records, both DKIM keys and both `_github-…` records are unchanged.
  - Google, Cloudflare and Quad9 already return GitHub's IPs, and GitHub serves the new site for `monicaespinel.com` over `http://`.
  - **Step 8, checked by Claude:**
    - GitHub shows "DNS check successful".
    - The Let's Encrypt certificate for `monicaespinel.com` and `www.monicaespinel.com` is issued and served. It expires 2027-02-11 and renews automatically.
    - `https://monicaespinel.com/` returns 200 from GitHub, and `https://www.monicaespinel.com/` returns a 301 to the apex.
    - Bluehost's old records didn't block the certificate.
  - **Bluehost done (owner), checked by Claude:** `ns1.bluehost.com` serves GitHub's four `A` records and `www` → `monica-espinel.github.io`. Its `MX` records are unchanged. Both zones now agree. Bluehost has no `AAAA` records, which is fine.
  - **Step 9, checked by Claude:** `MX`, SPF, DKIM and the verification records are unchanged in both zones.
  - **Step 10, checked by Claude (2026-11-12):**
    - `https://monicaespinel.com/` loads the new site with a valid certificate.
    - `https://www.monicaespinel.com/` redirects to the apex.
    - A post, `/beats-of-the-sacred-heart/`, loads.
    - `/page/2/` redirects to `/` with a meta refresh, and `/feed/` to `/index.xml`.
    - `/search/` and `/pagefind/pagefind.js` load, as do `/contact/`, `/category/exhibitions/`, `/index.xml`, `/sitemap.xml` and `/robots.txt`. All return 200.
  - **Still open:** **Enforce HTTPS is not on.** The Pages API reports `https_enforced: false`, and `http://monicaespinel.com/` returns 200 instead of redirecting to `https://`. Tick the box again in Settings → Pages, and check that it stays ticked after a reload.
- **Next, either:**
  - **Wait:** step 0d on or after 2026-11-14 at 12:00 (the NS check on `dns.google`, the site still on WordPress, email in both directions), then step 2 and steps 6–10 at GoDaddy only. Until then, don't change anything at Bluehost.
  - **Or cut over now (owner's choice, 2026-11-12):** steps 2 and 6–10 in **both** zones, GoDaddy's and Bluehost's. See "Cutting over before step 0d" under Cutover day.

---

## At least 24 hours before cutover

### 1. Write down the current records

Done: the owner exported the Bluehost zone twice on 2026-11-12, the second time after turning off Cloudflare. The values are in the step 0c table and in *The current records* above. These are the rollback values.

- [x] `A` record for the apex: **`162.241.252.140`** (one record; WordPress at Bluehost). It was `66.235.200.147` while Bluehost's Cloudflare integration was on.
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

- [x] **The nameservers:** `ns1.bluehost.com` and `ns2.bluehost.com`, so Bluehost hosts the DNS today. Step 0 moves them to GoDaddy.
- [x] **Who provides email:** **Google Workspace** (`MX` → Google), so the mailboxes don't depend on Bluehost.
- [x] **Checked by Claude, 2026-11-12: no HSTS.** The responses for `https://monicaespinel.com/` and `https://www.monicaespinel.com/` have no `Strict-Transport-Security` header. Returning visitors can still click through the short certificate warning in step 8. How to check this another way: **Whether the WordPress site forces HTTPS in browsers (HSTS).** In a browser, open `https://monicaespinel.com`, then open Developer tools → Network, reload, click the first request, and look under *Response headers* for `Strict-Transport-Security`. Note whether it's there. Step 8 explains why it matters.

**Cloudflare:** Bluehost's Cloudflare integration was on, and the owner turned it off (2026-11-12).
- [x] **Apex `A` record after turning Cloudflare off:** `162.241.252.140`, from the second zone export. Bluehost replaced the proxy address with the server's own.
- [x] **Confirmed by Claude, 2026-11-12 at 22:00: Cloudflare is off.** The site answers with `Server: Apache`, without `cf-ray`, and the page has no challenge script. Earlier note, kept for reference: **Confirm Cloudflare is really off.** A copy of the homepage the owner loaded after turning it off still contained Cloudflare's challenge script (`/cdn-cgi/challenge-platform/…`). The change may take up to an hour to apply, or the browser may have shown a cached page. To check:
  1. Open `https://monicaespinel.com` in a private window, open Developer tools → Network, and reload.
  2. Click the first request, and look under *Response headers*.
  3. `server: cloudflare` or a `cf-ray` header means Cloudflare is still active. Wait, then check Bluehost's settings again. Neither header means it's off.
  4. In the same place, note whether `strict-transport-security` is there (the HSTS item above).

### 2. Lower the TTL to 300 seconds

After step 0, the TTL is set **at GoDaddy**. Bluehost's TTL no longer matters once the nameservers point to GoDaddy.
- [x] Checked by Claude, 2026-11-12: both are at **600 s** at GoDaddy. At GoDaddy, check that the `@` `A` record and the `www` `CNAME` have the **lowest TTL** GoDaddy offers. Step 0c already sets this. Use 300 seconds (the brief's value) if offered, otherwise GoDaddy's minimum (often 600 seconds).
- [x] *(Not needed: the TTL was set in 0c.)* **Only if you changed a TTL just now** (rather than in 0c): wait at least as long as the previous TTL before the cutover, so resolvers drop the old value. The 48-hour wait in step 0 covers anything set in 0c.

The cutover, and any rollback, then takes effect within about that TTL: 5 minutes at 300 seconds, 10 minutes at 600.

### 3. Verify the domain in GitHub (prevents domain takeover)

Verifying the domain stops anyone else's GitHub Pages site from claiming `monicaespinel.com` while DNS points at GitHub.

- [x] Go to GitHub → the **monica-espinel** organization → **Settings → Pages → Add a domain**, and enter `monicaespinel.com`. (For a personal account, it's **Settings → Pages** in your user settings.)
- [x] GitHub shows a `TXT` record named like `_github-pages-challenge-monica-espinel.monicaespinel.com`, with a code value. Add exactly that `TXT` record at the DNS provider.
  - Done 2026-11-12 at GoDaddy: `_github-pages-challenge-monica-espinel` `TXT` `142a1fc26294c117b9db2502c7f20c`.
  - `dns.google` already returns it, answered by GoDaddy's nameserver `173.201.73.6`.
- [x] Back in GitHub, click **Verify**. Done 2026-11-12: "Successfully verified monicaespinel.com". The first try had failed while GitHub's lookup was still cached; a later retry worked. **Keep this `TXT` record permanently**: GitHub re-checks it.

This TXT record lives on its own `_github-pages-challenge-…` name, so it doesn't touch any existing record. The zone already has `_github-challenge-monica-espinel-org`: that's the *organization's* verified-domain record. Keep it, but it isn't the Pages one, so this step is still needed.

### 4. Search Console: verify by DNS (not the meta tag)

The WordPress site proves ownership to Google with a `google-site-verification` meta tag in its pages. The new site doesn't have that tag, as the brief decided. If you skip this step, Search Console loses verification at cutover.

- [x] **Done, nothing to add (owner, 2026-11-12):** the Search Console property `https://monicaespinel.com/` shows **"You are a verified owner"**. The verification method used is **Domain name provider: Successfully verified**, through the existing DNS `TXT` record, now at GoDaddy. The HTML meta tag isn't a method in use, so removing it at cutover changes nothing. Keep both `google-site-verification` records.

**This may already be done:** the zone already has two `google-site-verification` `TXT` records, `AMn5o…` and `wHV2C…`, the second being the same token as the old site's meta tag. In Search Console, open **Settings → Ownership verification** for the monicaespinel.com property(ies). If **Domain name provider** is listed as a verified method, skip to step 5. Either way, never delete those two records.

- [ ] *(Not needed: already verified.)* Otherwise: in Google Search Console, **add a Domain property** for `monicaespinel.com`, or for the existing property open **Settings → Ownership verification → add a method → Domain name provider**. Google shows a value like `google-site-verification=…`.
- [ ] At the DNS provider, **add** a `TXT` record on the apex (`@`) with that value.
  - **Add a new record, don't edit an existing one:** the apex may already have an SPF `TXT` record (`v=spf1 …`) for email, and it must stay.
- [ ] In Search Console, click **Verify**.

A Domain property covers `http`, `https`, `www` and the apex in one place.

---

## Cutover day

Check first that the latest deploy on GitHub passed: **Actions → Deploy site to GitHub Pages**, the newest run on `main` is green.

### Cutting over before step 0d: make each change in both zones

Until 48 hours after step 0b (2026-11-14, about 12:00 US Eastern), some DNS servers still ask **Bluehost's** nameservers, whose zone points to WordPress. If only GoDaddy's zone changes:
- **The certificate can be held up.** Let's Encrypt checks the domain from several of its own servers before GitHub gets the certificate. If one of those checks reaches Bluehost's zone, it finds WordPress and issuance fails. GitHub retries, but visitors on `https://` could see "connection not private" for many hours instead of about one.
- **Some visitors keep seeing WordPress** until their DNS forgets Bluehost. That's only a delay, not an error.

To cut over earlier anyway, make **steps 2, 6 and 7 identically in both zones**, so every DNS server gives the same answer:

| Where | Record | Change |
|---|---|---|
| GoDaddy **and** Bluehost | `@` `A` `162.241.252.140` | Delete, and add GitHub's four `A` records (step 6) |
| GoDaddy **and** Bluehost | `www` `CNAME` `monicaespinel.com` | Change to `monica-espinel.github.io` (step 7) |
| GoDaddy **and** Bluehost | TTL of `@` and `www` | The lowest each allows (step 2) |

- [ ] **GoDaddy:** steps 2, 6 and 7.
- [ ] **Bluehost:** Domains → monicaespinel.com → **DNS** (Zone Editor), the same three changes. Change nothing else there: `MX`, `TXT`, DKIM and the other `A` records (`cpanel`, `webmail` and so on) stay as they are.
- [ ] Then steps 8–10 as usual.

**Rollback also needs both zones** until 2026-11-14: put back `@` `A` `162.241.252.140` and `www` `CNAME` `monicaespinel.com` in each. After that date, Bluehost's zone no longer matters.

### 5. Set the custom domain in GitHub (before changing DNS)

Do this **first**, while DNS still points to WordPress. If you change DNS first, GitHub receives requests for monicaespinel.com before it knows the domain, and visitors get a GitHub "There isn't a GitHub Pages site here" error until this step is done. GitHub's own documentation recommends this order. The brief lists this step after the DNS records; doing it first changes nothing else. The domain verification in step 3 protects the domain in the meantime.

- [x] In the repository: **Settings → Pages → Custom domain**, enter `monicaespinel.com` and click **Save**. Done 2026-11-12, ahead of cutover day: it's harmless while DNS points to WordPress.
- [x] GitHub now shows the DNS check as **failing**. Seen 2026-11-12: "Both monicaespinel.com and its alternate name are improperly configured … (NotServedByPagesError)". Expected until steps 6–7. That's expected until steps 6–7 are done. Visitors still see WordPress, because DNS hasn't changed.

From now on, the github.io project address redirects to `monicaespinel.com`, which is still WordPress until step 6.

`static/CNAME` in the repository already contains `monicaespinel.com`. With GitHub Actions deployments, this setting is what counts.

**Optional preview on your computer only, once this step is done.** You can see the real new site at `monicaespinel.com` before anyone else does:
1. Add `185.199.108.153 monicaespinel.com www.monicaespinel.com` to `/etc/hosts` (on a Mac: `sudo nano /etc/hosts`).
2. Clear the DNS cache with `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder`.
3. In a private window, open **`http://monicaespinel.com`**. `https://` shows a certificate warning until the real cutover.
4. **Remove the line afterwards** and clear the cache again.

### 6. Point the apex to GitHub Pages

- [ ] **Delete** the apex `A` record(s) that point to the WordPress host.
- [ ] **Delete** any `ALIAS`, `ANAME` or `CNAME` record on the apex (step 1). It conflicts with the new `A` records: the provider either refuses them, or keeps sending some visitors to WordPress.
- [ ] **Add four** `A` records for the apex (`@`), with the same low TTL as step 2:

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
- [ ] **Add** one `CNAME`, with the same low TTL as step 2:

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
- [ ] **Before cancelling WordPress (Bluehost):** the DNS already moved to GoDaddy in step 0, so cancelling Bluehost can't take the domain down, and email is Google Workspace. Before cancelling:
  1. Check that GoDaddy's nameservers are active and the zone matches step 0c, now with GitHub's `A` and `www` records.
  2. Ideally, have whoever manages the email update SPF to `v=spf1 include:_spf.google.com ~all` and remove `default._domainkey` at GoDaddy (see the SPF note).
  3. Then cancel the Bluehost plan.
- [ ] **Formspree:** if reCAPTCHA is on in the form settings, turn it off to get the inline thank-you message. The honeypot covers spam. Messages arrive either way.

---

## Rollback (if something is seriously wrong)

Before 2026-11-14 at about 12:00 (48 hours after step 0b), do steps 1–2 **at Bluehost too**, if the cutover changed both zones.

1. At GoDaddy, delete the GitHub `A` records (and `AAAA` records, if added), and put back **`@` `A` `162.241.252.140`**.
2. Change the `www` `CNAME` back to **`@`** (`monicaespinel.com`).
3. With the lowered TTL (5 or 10 minutes at GoDaddy), most visitors see WordPress again within about that time.
4. Leave the GitHub custom domain setting as it is, or remove it: either way WordPress serves the site once DNS points back.
5. Tell Claude what went wrong, so it can be fixed before the next attempt.

The Search Console DNS record and the GitHub domain-verification record can stay. They don't affect where the site is served from.
