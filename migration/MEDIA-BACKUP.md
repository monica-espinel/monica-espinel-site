# Plan: back up linked media to GitHub, serve the copy if the original disappears

Status: step 1 done (2026-11-14): `data/media.json` and `scripts/check_media.py`. Steps 2–5 not started.

## What is already safe

- Everything under `/wp-content/uploads/` (PDFs, the 2021 mp4, images) is committed and served by Pages.
- Images that posts loaded from other sites are copied to `static/images/` (`scripts/fetch_external_images.py`,
  `migration/external-images.json`).

## What is still hosted elsewhere (`check_media.py check`, 2026-11-14)

`data/media.json` has 20 entries: 4 videos, 1 audio file, 1 PDF, 14 pages.

| Kind | Item | Post | 2026-11-14 |
|---|---|---|---|
| Video | Vimeo 761603460, Carmen Herrera Memorial (60 min) | remembering-carmen-herrera-whitney-museum | ok |
| Video | Vimeo 466668429 | ana-mercedes-hoyos | **unavailable**: the player says "This video isn't available. The owner has been notified." (also in a browser, also on the live WordPress page) |
| Video | YouTube wyCdwsBQdao, El Museo del Barrio | el-museo-del-barrio-celebrates-carmen-herrera-105-birthday | ok |
| Video | YouTube q4gg6U4ug6M, Brooklyn Rail NSE #576 | brooklyn-rail-carmen-herrera | ok |
| Audio | Podbean mp3, "Duet of Displacement" (53 MB) | parcharte | ok |
| PDF | CAA 111th conference programme | xocomil-vivian-suters-salute-to-the-wind | ok |
| Page | artpace.org/exhibitions/iair/iair_spring_2020 | artpace-international-artist-in-residence-program | **gone in practice**: refuses scripts; in a browser it redirects to Artpace's generic Exhibitions Archive |
| Page | 13 others (MoMA, Artforum, ISLAA, Brooklyn Rail ×2, UMD, El Museo, Artpace talk, Tatiana Arocha, Bread & Salt, Spotify, Apple, Amazon) | various | ok (MoMA, El Museo and the Artpace talk refuse scripts; checked in a browser) |

Vimeo 468397255 (spring-2020-international-artists-in-residence-talk) was deleted and is already removed from the post (#23).

The videos are the biggest risk and the biggest files (estimate 300 MB–1 GB each at 720p).

## Design

### 1. One manifest: `data/media.json`

One entry per external item, keyed by its original URL:

```json
"https://vimeo.com/761603460": {
  "kind": "video",
  "posts": ["remembering-carmen-herrera-whitney-museum"],
  "status": "live",
  "serve_copy": false,
  "copy": "https://github.com/monica-espinel/monica-espinel-media/releases/download/v1/vimeo-761603460.mp4",
  "sha256": "…",
  "archived": "2026-11-14",
  "wayback": "https://web.archive.org/web/2026…/https://vimeo.com/761603460"
}
```

- `kind`: video, audio, pdf or page. `status`: live or down (flipped by the watcher PR, below). `serve_copy`: the owner has permission to show the copy publicly.
- Step 1 writes the first four fields; step 3 adds `copy`, `sha256`, `archived`, `wayback`. A `rights` field (who owns each item) waits for the owner's decision below.
- It is keyed by the original URL (without `#fragment`), so templates can look an item up with `index site.Data.media $url`.
- JSON rather than YAML, so the scripts keep to the Python standard library, like the other checks.
- `check_media.py sync` builds and refreshes it from `content/`. It skips links in front matter and in `<!-- comments -->`.

### 2. Where the copies go on GitHub

GitHub limits decide this: git rejects files over 100 MB, and a Pages site should stay under 1 GB (it is ~180 MB now).

| Size | Storage | Served from |
|---|---|---|
| Small (page snapshots as PDF, small PDFs, up to ~20 MB) | this repo, `static/mirror/<host>/…` | the site itself, `/mirror/…` |
| Large (videos, the 53 MB mp3) | **Release assets** in a separate repo `monica-espinel-media` (2 GB per file, not in git history, not counted in the Pages size) | the release download URL |

Keeping large files out of this repo also keeps clones and Pages deploys fast.

**Spike first:** a release URL redirects to `objects.githubusercontent.com` with a download content type.
Most browsers still play it in `<video>`, but seeking needs range requests. One test video confirms this
before the rest are uploaded. If it fails, the fallback is to keep the archive on GitHub and serve the
public copy from the Internet Archive (archive.org streams video and is made for this).

### 3. Taking the copies (`scripts/backup_media.py`, run locally)

- Videos: `yt-dlp` at up to 720p mp4 (H.264/AAC, so `<video>` plays it everywhere), plus the poster image and the title.
  Run it on a laptop. YouTube often blocks downloads from GitHub's servers.
- Audio and files: plain download, keep the original bytes.
- External pages: a headless-Chrome print-to-PDF into `static/mirror/`, plus a Wayback Machine "Save Page Now" request,
  with the snapshot URL recorded. (The Artforum post already does this by hand: `Rosemberg-Sandoval-artforum.com-critics-picks.pdf`.)
- Uploads large files with `gh release upload`, writes the URL and sha256 into `data/media.json`. Re-running it skips what is already there.

### 4. Switching to the copy, with no content edits

The templates read `data/media.json`:

- `video-embed` shortcode: `status: live` gives the iframe, as now. `status: down` and `serve_copy: true`
  give a native `<video>` with the copy and the poster, plus a line "Original no longer online. Archived copy."
  If `serve_copy` is false, it shows the poster and a link to the Wayback snapshot.
- `podcast-episode` shortcode: same rule for `src`.
- New link render hook `layouts/_markup/render-link.html`: when a link's URL is in the manifest and is `down`,
  it points to the `/mirror/` PDF or the Wayback snapshot and adds "(archived copy)". Live links are unchanged.

The post Markdown never changes. Switching back is a one-line change of `status`.

### 5. Watching for disappearances (`.github/workflows/media-watch.yml`)

- Weekly cron plus manual runs. `scripts/check_media.py` checks each original: YouTube through oEmbed,
  Vimeo through the player page (oEmbed already 404s for two embed-restricted videos, so it can't be the signal),
  files with HEAD (status + content type), and pages with GET.
- After **two failed weeks in a row** (one failure can be a blip), it opens an issue and a PR setting `status: down`.
  A person merges it, as `main` requires. Nothing is auto-merged.
- Needs the repository setting "Allow GitHub Actions to create and approve pull requests". If you'd rather not
  enable it, the watcher only opens the issue.

### 6. Checks

- `scripts/check_media.py --verify`: every manifest entry has a copy, its sha256 matches, and each post's media appears in the manifest.
- A local build with one item forced to `down` shows the fallback player and the archived link.

## Decisions for the owner

1. **Rights.** The videos belong to the Whitney, the Brooklyn Rail, El Museo del Barrio, and Artpace; the episode to Parcharte.
   A private backup is low risk. Showing a copy publicly once the original is gone needs their permission.
   Proposal: the media repo is **private** (archive only) and `serve_copy` stays false until permission is given for an item.
   Note: a private repo's release files can't be played by visitors. Items cleared for public serving go into a second,
   public release, or to archive.org.
2. **Video quality:** 720p (proposed; about half the size of 1080p) or the best available.
3. **Should the watcher open PRs** (needs the Actions setting above) or only issues?

## Work order (one PR each)

1. ~~Manifest + `check_media.py` (inventory and live check only).~~ Done 2026-11-14.
2. Release-playback spike with one video.
3. `backup_media.py`, then take the copies (local run).
4. Shortcode fallbacks + link render hook.
5. `media-watch.yml`.
