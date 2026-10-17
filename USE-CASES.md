# Use cases & acceptance criteria

**Status: draft for review.** This is the ROADMAP.md Phase 2 step 6 deliverable.

Actors, their scenarios, and a set of **testable outcomes** for each — written *before* the
code so the acceptance criteria can be handed to the test suites in Phases 4, 5, 8 and 9
unchanged. Each criterion has a stable id (`AC-ADM-05.2`) that test names and comments can
reference, which is what keeps the document and the tests from drifting apart.

Related: `ROADMAP.md` (sequencing) · `ARCHITECTURE.md` (design) · `openapi/openapi.yaml`
(the contract these criteria describe) · `CI-CD.md` (where they run).

---

## How to read this

- **UC** = use case. **AC** = acceptance criterion.
- Every AC is written as *observable* behaviour — a status code, a rendered element, a stored
  file. No "works correctly".
- Criteria are the **source**, tests are the derived artifact. A criterion with no test is a
  gap; a test with no criterion is untraceable. The matrix in §8 tracks the first direction.
- **Negative cases are first-class.** This app's security floor is a list of things that must
  *never* happen (§6).

### Test-level legend

| Tag | Level | Runs where |
|---|---|---|
| `B` | Build / CI | the Astro build, in CI |
| `U` | Unit | JUnit, no Spring context |
| `I` | Integration | Testcontainers + real PostgreSQL |
| `C` | Contract | generated from `openapi.yaml` (queries are non-critical; run manually in the first pass — see §8) |
| `E` | E2E | Playwright, admin or visitor |
| `A` | Accessibility | axe / Playwright |
| `P` | Performance | Lighthouse / budget assertions |
| `M` | Manual | eyeball pass, recorded in the review |

### One structural note that shapes half of these criteria

The public site is **static**. There is no API call at page-view time, so most "visitor"
criteria are really **build-time** criteria: they test whether the Astro build fetched and
rendered published content correctly. Only image loading, the lightbox and routing are
genuinely browser-runtime. Criterion tags reflect this — a lot of `B`, some `E`.

---

## 1. Actors

| Actor | Description | Surface |
|---|---|---|
| **Visitor** | anonymous, possibly on a phone, possibly with JS disabled | public static site + backend media URLs |
| **Photographer** | the single authenticated user; never publicly reachable | admin SPA, over a private tunnel |
| **Nightly cron** | safety-net rebuild (ARCHITECTURE.md §7) | CI |
| **CI** | builds, tests, evaluates these criteria | GitHub Actions |

---

## 2. Visitor use cases

### UC-VIS-01 — Browse the home page
**Actor** Visitor · **Trigger** `GET /` · **Levels** `B` `P`

- **AC-VIS-01.1** Given published albums exist, When the build runs, Then the home page
  renders at least one featured work with a caption/alt text.
- **AC-VIS-01.2** Given a visitor opens `/`, Then the page is served from static hosting with
  **no runtime call to `/api/**`**.
- **AC-VIS-01.3** Given JavaScript is disabled, Then text and images still render; only the
  lightbox degrades (to a link to the full image).

### UC-VIS-02 — Browse the gallery index
**Actor** Visitor · **Trigger** `GET /gallery` · **Levels** `B` `C`

- **AC-VIS-02.1** The gallery index lists exactly the published categories, in `sortOrder`
  (matches `listPublicCategories`).
- **AC-VIS-02.2** No draft category appears (§6, UC-SEC-01).
- **AC-VIS-02.3** Each category links to `/gallery/{slug}`.

### UC-VIS-03 — Browse albums in a category
**Actor** Visitor · **Trigger** `GET /gallery/{slug}` · **Levels** `B` `P`

- **AC-VIS-03.1** Only published albums of that category are listed, in `sortOrder`.
- **AC-VIS-03.2** Each album shows its cover photo — or, when no cover is picked, the first
  published photo.
- **AC-VIS-03.3** Given a category with no published albums, Then an empty state renders and
  the build does not fail.
- **AC-VIS-03.4** Given more albums than one page, Then `page`/`size` are honoured and
  `totalItems`/`totalPages` exclude drafts.

### UC-VIS-04 — Open an album
**Actor** Visitor · **Trigger** `GET /gallery/{category}/{album}` · **Levels** `B` `P`

- **AC-VIS-04.1** The grid shows only published photos, in display order.
- **AC-VIS-04.2** Every `<img>` declares `width`/`height` (no layout shift) and has a non-empty
  `alt` attribute.
- **AC-VIS-04.3** Given a draft album slug, Then the page is a 404 — indistinguishable from
  a slug that never existed.
- **AC-VIS-04.4** Given a draft photo in a published album, Then it does not appear.

### UC-VIS-05 — Use the lightbox
**Actor** Visitor · **Trigger** click a thumbnail · **Levels** `E` `A`

- **AC-VIS-05.1** Clicking a thumbnail opens the photo full-size, with next/previous.
- **AC-VIS-05.2** Arrow keys navigate, `Esc` closes.
- **AC-VIS-05.3** Focus is trapped inside the open lightbox and, on close, **returns to the
  thumbnail that opened it**.
- **AC-VIS-05.4** Given JS is disabled, Then the thumbnail is a plain link to the image.

### UC-VIS-06 — Read the About page
**Actor** Visitor · **Trigger** `GET /about` · **Levels** `B`

- **AC-VIS-06.1** The page renders static content with no runtime API call.
- **AC-VIS-06.2** Headings are semantic (`h1` per page) for screen readers and SEO.

### UC-VIS-07 — Reach the photographer
**Actor** Visitor · **Trigger** `GET /contact` · **Levels** `B` `E`

- **AC-VIS-07.1** The Contact page shows Facebook and Instagram links plus a `mailto:` address;
  each opens correctly.
- **AC-VIS-07.2** The page contains **no form** and the site issues no `POST` to any public
  endpoint (§6, UC-SEC-02).

### UC-VIS-08 — Unknown route
**Actor** Visitor · **Trigger** any unmatched path · **Levels** `E`

- **AC-VIS-08.1** An unmatched path renders a styled 404 with navigation links (not a stack
  trace, not a blank page).

### UC-VIS-09 — Load images efficiently
**Actor** Visitor · **Levels** `B` `P`

- **AC-VIS-09.1** Each `<img>` carries a `srcset` built from the photo's available renditions
  (640 / 1280 / 2048 px longest side) and a `sizes` attribute.
- **AC-VIS-09.2** Below-the-fold images `loading="lazy"`; the LCP/hero image is eager.
- **AC-VIS-09.3** Image URLs are the backend's `/media/{photoId}/{name}` absolute URLs.
- **AC-VIS-09.4** Original files are **never** served publicly — only renditions (§6,
  UC-SEC-06).

---

## 3. Admin use cases

### UC-ADM-01 — Log in
**Actor** Photographer · **Trigger** `POST /admin/auth/login` · **Levels** `I` `E`

- **AC-ADM-01.1** Valid credentials → `200` with `accessToken`, `refreshToken`, `tokenType:
  Bearer`, `expiresInSeconds`.
- **AC-ADM-01.2** Invalid credentials → `401` problem+json; **no** token issued.
- **AC-ADM-01.3** A request missing `email` or `password` → `400` with `errors[]` naming the
  field.
- **AC-ADM-01.4** Tokens are held **in memory only** — never `localStorage`/`sessionStorage`
  (XSS defence); a page reload requires logging in again.
- **AC-ADM-01.5** The password is stored bcrypt-hashed and never returned by any endpoint.

### UC-ADM-02 — Keep the session alive
**Actor** Photographer · **Trigger** `POST /admin/auth/refresh` · **Levels** `I` `E`

- **AC-ADM-02.1** The client refreshes **before** the access token expires, and in-flight
  admin actions continue without a re-login prompt.
- **AC-ADM-02.2** Refresh **rotates** the token: reusing a spent refresh token → `401`.
- **AC-ADM-02.3** Any admin call answered `401` sends the UI back to login rather than showing
  a raw error.
- **AC-ADM-02.4** Logout drops the tokens client-side; the next admin call → `401` (no
  server-side session to destroy).

### UC-ADM-03 — Manage categories
**Actor** Photographer · **Trigger** `/admin/categories*` · **Levels** `I` `E`

- **AC-ADM-03.1** Create → `201`; `slug` derived from `name` when omitted; starts **unpublished**
  unless `published: true` is sent.
- **AC-ADM-03.2** Creating a category whose slug already exists → `409`, nothing created.
- **AC-ADM-03.3** `PUT /admin/categories/order` with every category id → `204`, and
  `listAdminCategories` reflects the new order.
- **AC-ADM-03.4** A reorder body that omits an existing id → `400`.
- **AC-ADM-03.5** `PUT /admin/categories/{id}` replaces name/slug/order/published → `200`;
  toggling `published` works.
- **AC-ADM-03.6** Deleting an **empty** category → `204`.
- **AC-ADM-03.7** Deleting a category that **still contains albums** → `409`; nothing is
  deleted.
- **AC-ADM-03.8** A blank or over-long `name` → `400` with `errors[]`.
- **AC-ADM-03.9** Changing a `slug` — category or album — changes its public URL, and **no
  redirect** is served (accepted PoC limitation; see §7 #8).

### UC-ADM-04 — Manage albums
**Actor** Photographer · **Trigger** `/admin/albums*` · **Levels** `I` `E`

- **AC-ADM-04.1** Create requires `title` + `categoryId` → `201`; starts as a draft by default.
- **AC-ADM-04.2** `slug` is unique **within a category**; a collision → `409`.
- **AC-ADM-04.3** A missing `categoryId` → `400`.
- **AC-ADM-04.4** `PUT /admin/albums/{id}` updates title, description, category, order,
  published and `coverPhotoId`.
- **AC-ADM-04.5** `coverPhotoId` pointing at a photo **not** in the album → `400`; `null` clears
  the pick.
- **AC-ADM-04.6** `PATCH /admin/albums/{id}/publish` → `200`; after a rebuild the album appears
  in the public reads.
- **AC-ADM-04.7** Deleting an album that **still contains photos** → `409`.
- **AC-ADM-04.8** Deleting an empty album → `204`, and any cover reference is cleared.
- **AC-ADM-04.9** `GET /admin/albums/{id}/photos` lists **every** photo in the album, drafts
  included, in display order — the admin screen's photo list.

### UC-ADM-05 — Upload photos into an album
**Actor** Photographer · **Trigger** `POST /admin/albums/{id}/photos` · **Levels** `U` `I` `E`

*The core flow of the whole app. It gets the most criteria on purpose.*

- **AC-ADM-05.1** Given a logged-in photographer and an existing album, When they upload a batch
  of valid images, Then `201` returns a `PhotoBatch` — one `Photo` per file, **each a draft**,
  **each with at least one rendition**.
- **AC-ADM-05.2** Given a landscape `2048×1365` upload, Then the renditions are exactly
  `640×427`, `1280×853`, `2048×1365` — longest-side ladder, **never upscaled**.
- **AC-ADM-05.3** Given a portrait `1365×2048` upload, Then renditions are `427×640`, `853×1280`,
  `1365×2048`.
- **AC-ADM-05.4** Given a `900×600` upload, Then there are **2** renditions (`640×427` and
  `900×600`) — a target that collapses onto a smaller one is skipped. Every photo has **1–3**
  renditions.
- **AC-ADM-05.5** Renditions are generated **synchronously**: the `201` is not returned until
  every rendition exists on disk. No request ever triggers re-processing.
- **AC-ADM-05.6** Rendition files are named `{longestSide}-{contentHash}.{format}` under a
  per-photo directory; the original is retained server-side.
- **AC-ADM-05.7** Given a file whose bytes are not a supported image (e.g. an executable renamed
  `.jpg`), Then `400` problem+json with an `errors[]` entry naming the file, and **nothing is
  persisted**.
- **AC-ADM-05.8** Given a batch where **one** file is invalid, Then the whole request → `400`
  and **no** photo from the batch is created (atomic — all or nothing).
- **AC-ADM-05.9** Given a file over **25 MB** or a request over **100 MB**, Then `413`.
- **AC-ADM-05.10** Given an image whose decoded dimensions exceed the decompression-bomb guard,
  Then `400` — processing is refused before a full decode.
- **AC-ADM-05.11** Given a supported image with EXIF, Then renditions carry **no** EXIF/GPS/XMP
  (ICC profile may be kept).
- **AC-ADM-05.12** Uploading into an unknown album id → `404`; without a token → `401`.
- **AC-ADM-05.13** The uploaded photos appear in the album's admin view as drafts, and the
  request does not publish them.

### UC-ADM-06 — Edit a photo's details
**Actor** Photographer · **Trigger** `PATCH /admin/photos/{id}` · **Levels** `I` `E`

- **AC-ADM-06.1** A partial update of `title`/`altText`/`sortOrder`/`published` → `200` with the
  updated `Photo`; omitted fields are untouched.
- **AC-ADM-06.2** `altText` over 500 chars → `400` with `errors[]`.
- **AC-ADM-06.3** An unknown photo id → `404`.

### UC-ADM-07 — Reorder photos
**Actor** Photographer · **Trigger** `PUT /admin/albums/{id}/photos/order` · **Levels** `I` `E`

- **AC-ADM-07.1** A body carrying every photo id in final order → `204`; the public photo order
  matches after a rebuild.
- **AC-ADM-07.2** A body that omits a photo in the album, or includes a foreign id → `400`.

### UC-ADM-08 — Publish / unpublish a photo
**Actor** Photographer · **Trigger** `PATCH /admin/photos/{id}` · **Levels** `I` `E`

- **AC-ADM-08.1** `published: true` → after a rebuild the photo appears in the public album.
- **AC-ADM-08.2** `published: false` → it disappears from every public read.
- **AC-ADM-08.3** Publishing a photo never publishes its album or category (each level is
  independent).
- **AC-ADM-08.4** Setting `published: true` on a photo with an empty `altText` → `400`; the
  admin UI blocks it before the request is sent (same rule enforced on both layers).

### UC-ADM-09 — Delete a photo
**Actor** Photographer · **Trigger** `DELETE /admin/photos/{id}` · **Levels** `I` `E`

- **AC-ADM-09.1** → `204`; the row is gone **and** every rendition file is removed from disk.
- **AC-ADM-09.2** Its media URLs then return `404`; it is gone from public reads after a rebuild.
- **AC-ADM-09.3** Deleting the album's cover photo clears the cover reference — the album is
  kept, and its public cover falls back to the first published photo.
- **AC-ADM-09.4** Deleting the same photo again → `404`.

### UC-ADM-10 — Rebuild the public site
**Actor** Photographer · **Trigger** `POST /admin/rebuild` · **Levels** `I` `E`

- **AC-ADM-10.1** → `202` with `{status: accepted}` — asynchronous by design.
- **AC-ADM-10.2** Without a token → `401`.
- **AC-ADM-10.3** Publishing content does **not** trigger a rebuild by itself — only the button
  or the nightly cron does (option A). Repeated clicks while a build is running are harmless;
  they never corrupt content.
- **AC-ADM-10.4** A publish not followed by a rebuild stays invisible to visitors until the
  next rebuild — the accepted staleness of option A, bounded by the nightly cron.

### UC-ADM-11 — Confirm a change is live
**Actor** Photographer · **Levels** `E` `M`

- **AC-ADM-11.1** After a triggered rebuild completes, the published change is visible on the
  public site.
- **AC-ADM-11.2** The public footer displays the **build date**, injected at build time (never
  the visitor's clock), so a landed rebuild is visible at a glance.
- **AC-ADM-11.3** The footer date means "last built", not "last changed": a nightly rebuild
  advances it even when no content changed.

### UC-ADM-12 — Handle an unreachable backend
**Actor** Photographer · **Levels** `E`

- **AC-ADM-12.1** Given the private tunnel is down, Then the UI shows a clear, non-destructive
  error — it does not claim success.
- **AC-ADM-12.2** A failed upload leaves **no** half-imported album; retrying is safe.
- **AC-ADM-12.3** The UI distinguishes "not signed in" (`401`) from "backend unreachable"
  (network error).

### UC-ADM-13 — Work from empty states
**Actor** Photographer · **Levels** `E`

- **AC-ADM-13.1** With zero categories, zero albums or zero photos, each screen shows an
  actionable empty state and does not crash.

---

## 4. System & operations

### UC-SYS-01 — Nightly rebuild
**Actor** Nightly cron · **Levels** `M`

- **AC-SYS-01.1** A scheduled build runs once a night, independent of the manual button.
- **AC-SYS-01.2** A failed scheduled build is visible (notification), not silent.

### UC-SYS-02 — Serve media immutably
**Actor** Visitor · **Trigger** `GET /media/{photoId}/{name}` · **Levels** `I` `C`

- **AC-SYS-02.1** → `200` with `Cache-Control: immutable` and a long max-age, plus an `ETag`.
- **AC-SYS-02.2** A conditional request with a matching `If-None-Match` → `304`.
- **AC-SYS-02.3** An unknown photo/name → `404`.

### UC-SYS-03 — Report health
**Actor** Compose / k8s · **Trigger** `GET /actuator/health` · **Levels** `I`

- **AC-SYS-03.1** → `200` with `{status: UP}` when the DB is reachable; used by the Compose
  healthcheck and, later, k8s probes.

---

## 5. Negative & security use cases

### UC-SEC-01 — Unpublished content never leaks
**Levels** `I` `C` `E`

- **AC-SEC-01.1** A draft category/album/photo is absent from **every** public response —
  including pagination `totalItems`/`totalPages`.
- **AC-SEC-01.2** A draft slug → `404`, never `200` and never `403` (no existence oracle).
- **AC-SEC-01.3** Album objects embedded in public responses carry only published data; a
  draft photo is never exposed as a public cover — the cover falls back to the first
  **published** photo.

### UC-SEC-02 — The public API has no write endpoints
**Levels** `I` `C`

- **AC-SEC-02.1** Any `POST`/`PUT`/`PATCH`/`DELETE` under `/api/**` → `405` (or `404`), never
  `200`.
- **AC-SEC-02.2** No contact/message endpoint exists; no public path accepts user input.
- **AC-SEC-02.3** The public site sends no credentials and stores no visitor data.

### UC-SEC-03 — Admin endpoints require a valid token
**Levels** `I` `C`

- **AC-SEC-03.1** `/admin/**` without an `Authorization` header → `401`.
- **AC-SEC-03.2** With an expired, malformed, or wrong-signature token → `401`.
- **AC-SEC-03.3** A **refresh** token presented as a bearer access token → `401`.
- **AC-SEC-03.4** `/admin/**` is not reachable from the public internet (deployment property —
  private tunnel; asserted in the Phase 10 runbook, not by a unit test).

### UC-SEC-04 — CORS admits only the admin origin
**Levels** `I`

- **AC-SEC-04.1** A preflight from the configured admin origin (`http://localhost:5173`) is
  allowed.
- **AC-SEC-04.2** A request from any other origin gets **no** `Access-Control-Allow-Origin`.
- **AC-SEC-04.3** No wildcard origin is ever emitted when credentials are in play.

### UC-SEC-05 — Uploads reject hostile input
**Levels** `U` `I`

- **AC-SEC-05.1** The file type is decided by **magic bytes**, not the extension or the
  `Content-Type` header.
- **AC-SEC-05.2** Zero-byte, truncated and malformed images → `400`.
- **AC-SEC-05.3** A decompression bomb (huge declared dimensions) → `400` before a full decode.
- **AC-SEC-05.4** Stored filenames are server-generated (content-hash based), so a hostile
  original filename cannot traverse paths.
- **AC-SEC-05.5** Over-limit uploads → `413` (mirrors AC-ADM-05.9).

### UC-SEC-06 — Rendition URLs are immutable
**Levels** `I` `C`

- **AC-SEC-06.1** The name embeds a content hash: identical content → identical name; different
  content → different name.
- **AC-SEC-06.2** Because the name is content-addressed, browsers/CDN may cache it forever
  (`immutable`) with no invalidation story needed.
- **AC-SEC-06.3** Originals are **never** publicly addressable.

---

## 6. Non-functional use cases

### UC-NFR-01 — Accessibility
**Levels** `A`

- **AC-NFR-01.1** Every interactive element is keyboard-reachable with a visible focus ring.
- **AC-NFR-01.2** The lightbox traps focus while open and restores it on close (UC-VIS-05.3).
- **AC-NFR-01.3** Published photos require non-empty alt text.
- **AC-NFR-01.4** An automated axe scan reports **zero critical** issues on the key pages.

### UC-NFR-02 — Performance
**Levels** `P`

- **AC-NFR-02.1** Images declare dimensions and are served as WebP renditions sized to the
  viewport via `srcset`.
- **AC-NFR-02.2** Below-the-fold images lazy-load; the LCP image does not.
- **AC-NFR-02.3** An album page meets the agreed LCP/CLS budget (numbers fixed in Phase 2
  step 8).

### UC-NFR-03 — SEO
**Levels** `B`

- **AC-NFR-03.1** Every page has a unique `<title>`, meta description and OG tags.
- **AC-NFR-03.2** A sitemap and `robots.txt` are generated; canonical URLs are absolute.
- **AC-NFR-03.3** Headings are hierarchical and semantic.

---

## 7. Gaps & open questions (found while writing this)

These are the payoff of writing the catalog before the code — each is a decision or a missing
piece, not a typo.

**Status:** every item is resolved in review (answers inline). Resolved items are reflected in
the contract (`openapi/openapi.yaml`), in the criteria above, and in `ROADMAP.md` where they
affect sequencing.

1. **`GET /admin/albums/{id}/photos` is missing from the contract.** `getAdminAlbum` says
   "photos are fetched separately", but no such operation exists — so the admin UI cannot list
   an album's photos **including drafts**. Add it (paginated, `PageOfPhoto`). *Blocks
   UC-ADM-05/07/08/09.*
**Answer: Add this on the contract**

2. **Deleting a photo that is an album cover.** `deleteAlbum` says the cover reference is
   cleared, but `deletePhoto` says nothing. Decide: clear the album's `coverPhotoId` on photo
   delete (recommended), or refuse. Affects AC-ADM-09.3.
**Answer: Clear the album's cover photo**

3. **Cover fallback when the cover photo is unpublished/deleted.** Public cover should fall
   back to the first **published** photo; needs to be stated in the contract. Affects
   AC-SEC-01.3.
**Answer: Agree**

4. **Batch-upload atomicity.** The `400` response implies all-or-nothing, but nothing states it.
   Confirm, then make AC-ADM-05.8 normative.
**Answer: Yes, all or nothing**

5. **Debounce on rebuild** is "deferred" in the roadmap — but AC-ADM-10.3 needs a definite
   answer before Phase 8 ships the trigger.
**Answer: Option A — manual "Rebuild site" button + nightly cron; no automatic trigger, no
debounce.** Rationale and the debounce alternative are in `ARCHITECTURE.md` §7.

6. **How does the photographer know a rebuild finished?** `202` is fire-and-forget today. Decide
   between a CI status link and a polled status endpoint.
**Answer: Include the build/deploy date on the frontend/ footer**

7. **Category publish has no dedicated endpoint** (unlike albums' `/publish`). Toggling
   `published` requires a full `PUT`. Either accept it or add
   `PATCH /admin/categories/{id}/publish` for symmetry.
**Answer: Add the PATCH on the contract**

8. **Slug changes break live URLs.** Renaming an album/category changes its public path. For the
   PoC: accept it (documented), or add redirects. Affects AC-ADM-03.5/04.4.
**Answer: Accept**

9. **Alt text and publishing.** Should a photo be **unpublishable** while `altText` is empty
   (AC-NFR-01.3 implies visibility)? Decide whether the backend enforces it or only the UI does.
**Answer: Enforce on both frontend and backend**

10. **Contract tests (`C`)** are non-critical and deferred to a manual first pass — flagged here
    so the §8 tags aren't mistaken for CI gates on day one.
**Answer: Acknowledged — deferred, not a CI gate on day one.**

---

## 8. Traceability matrix

Every use case → the contract operation(s) it exercises → primary test level → the phase that
owns the test.

| Use case | OpenAPI operation(s) | Level | Phase |
|---|---|---|---|
| UC-VIS-01 Home | `listPublicAlbums` | B | 8 |
| UC-VIS-02 Gallery index | `listPublicCategories` | B/C | 8 |
| UC-VIS-03 Category page | `listPublicAlbums` (`category`) | B | 8 |
| UC-VIS-04 Album page | `getPublicAlbum`, `listPublicAlbumPhotos` | B/P | 8 |
| UC-VIS-05 Lightbox | — (client only) | E/A | 8, 9 |
| UC-VIS-06 About | — (static) | B | 8 |
| UC-VIS-07 Contact | — (static) | B/E | 8 |
| UC-VIS-08 404 | — (routing) | E | 8 |
| UC-VIS-09 Image loading | `/media/{photoId}/{name}` | B/P | 8, 9 |
| UC-ADM-01 Login | `login` | I/E | 4, 5 |
| UC-ADM-02 Session | `refreshToken` | I/E | 4, 5 |
| UC-ADM-03 Categories | `createCategory`, `reorderCategories`, `updateCategory`, `setCategoryPublished`, `deleteCategory`, `listAdminCategories` | I/E | 4, 5 |
| UC-ADM-04 Albums | `createAlbum`, `listAdminAlbums`, `getAdminAlbum`, `updateAlbum`, `deleteAlbum`, `setAlbumPublished`, `listAdminAlbumPhotos` | I/E | 4, 5 |
| UC-ADM-05 Upload | `uploadPhotos` + media pipeline | U/I/E | 3, 4, 5 |
| UC-ADM-06 Photo edit | `updatePhoto` | I/E | 4, 5 |
| UC-ADM-07 Reorder photos | `reorderPhotos` | I/E | 4, 5 |
| UC-ADM-08 Publish photo | `updatePhoto` | I/E | 4, 5 |
| UC-ADM-09 Delete photo | `deletePhoto` | I/E | 4, 5 |
| UC-ADM-10 Rebuild | `triggerRebuild` | I/E | 4, 5 |
| UC-ADM-11 Live confirm | `triggerRebuild` + public reads | E/M | 8, 9 |
| UC-ADM-12 Offline | — (client error handling) | E | 5 |
| UC-ADM-13 Empty states | admin reads | E | 5 |
| UC-SYS-01 Nightly rebuild | — (CI scheduled build) | M | 8 |
| UC-SYS-02 Immutable media | `/media/{photoId}/{name}` | I/C | 4 |
| UC-SYS-03 Health | `/actuator/health` | I | 4 |
| UC-SEC-01 No draft leaks | all `public` operations | I/C/E | 4, 9 |
| UC-SEC-02 No public writes | all `/api/**` | I/C | 4 |
| UC-SEC-03 Admin auth | all `/admin/**` | I/C | 4 |
| UC-SEC-04 CORS | preflight | I | 4 |
| UC-SEC-05 Hostile uploads | `uploadPhotos` | U/I | 3, 4 |
| UC-SEC-06 Immutable URLs | media pipeline | I/C | 3, 4 |
| UC-NFR-01 Accessibility | public + admin UI | A | 9 |
| UC-NFR-02 Performance | public UI | P | 9 |
| UC-NFR-03 SEO | build output | B | 9 |

**Coverage gaps to close:** the criteria marked `C` are deferred (§7 #10); UC-VIS-05/08 and
UC-ADM-12/13 have no contract operation by design and are UI-only. `AC-ADM-11.2` (footer build
date) is a Phase 8 build-output concern.
