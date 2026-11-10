# Test strategy

**Status: draft for review.** This is the `ROADMAP.md` Phase 2 step 8 deliverable: what gets
tested at each level, with which tool, where it runs, and which check is allowed to block a
merge.

The **acceptance criteria are the source; tests are the derived artifact.** Every test name
carries the AC id it proves (`AC-ADM-05.8_atomic_batch...`), so a criterion with no test — or a
test with no criterion — is visible in a grep. `USE-CASES.md` §8 is the traceability matrix this
document operationalises.

Related: `USE-CASES.md` (what must be true) · `openapi/openapi.yaml` (the normative contract) ·
`ARCHITECTURE.md` (why the site is static) · `CI-CD.md` (pipeline mechanics) · `ROADMAP.md`
(which phase owns each suite).

---

## 0. Taxonomy is tags (settled)

The catalogue and the contract use **tags**: albums are M:N with tags, an album must have ≥ 1
tag, multiple `?tag=` values use **AND** semantics, and unpublished tags are hidden from public
lists/pickers but do not hide albums. There is **no separate tag page and no separate
tag-management use case**: the gallery is one flat list with a tag filter, and tags are created
inline from the album form. `AC-VIS-03.3` and `UC-ADM-03` are retired; their ids are not reused.

---

## 1. Principles

1. **Risk-first, not coverage-first.** No coverage-percentage target. The gates are the
   criteria that protect data and security: draft leakage, admin auth, upload atomicity,
   media deletion. A pretty page is caught by a human; a leaked draft is caught here.
2. **Test at the lowest level that can prove the criterion.** Rendition math is a unit test;
   "draft absent from pagination totals" is an integration test; "focus returns to the
   thumbnail" is E2E. Do not re-prove backend rules through the browser.
3. **The public site is static, so most visitor criteria are build-time tests.** There is no
   page-view API call. `B` tests assert the produced HTML; only lightbox, routing and image
   loading need a real browser (`E`/`P`).
4. **The contract is normative.** Integration tests validate against `openapi.yaml`; consumer
   builds (frontend, admin) compile against a generated client. Drift fails loudly.
5. **Focused E2E.** Per `ROADMAP.md` risk notes, E2E covers the critical journeys, not every
   permutation. Backend integration carries the breadth.
6. **A flaky test is a bug.** One retry is allowed on CI with a retained trace; a test that
   passes on retry is quarantined with an issue, not silently tolerated.

---

## 2. Levels at a glance

| Tag | Level | Tool | Owns | First runs |
|---|---|---|---|---|
| `B` | Build output | Astro build + Node assertions | Static rendering, SEO, image markup, draft exclusion | Phase 8 |
| `U` | Unit | JUnit 5, no Spring context | Media/rendition math, validation, slug rules | Phase 3 |
| `I` | Integration | Testcontainers PostgreSQL + MockMvc/WebTestClient | API + DB + media filesystem, auth, security, atomicity | Phase 4 |
| `C` | Contract | Spectral + in-process spec validation | Wire shape vs `openapi.yaml` | Phase 4 (lint always; validation manual first pass) |
| `E` | E2E | Playwright (Chromium) | Critical admin and visitor journeys | Phase 5 / 8 |
| `A` | Accessibility | axe-core via Playwright + keyboard assertions | Keyboard, focus, contrast, reduced motion | Phase 9 |
| `P` | Performance | Lighthouse CI (production build) | LCP/CLS/TBT budgets | Phase 9 |
| `M` | Manual | checklist in the PR/release | Visual pass vs Figma, nightly rebuild, offline tunnel | Phase 8 |

`C` is **not a merge gate on day one** — `USE-CASES.md` §7 #10 accepts a manual first pass.
Spectral lint *is* cheap and always on.

---

## 3. What each level covers

### 3.1 Unit (backend) — `U`

Pure logic, no database, no HTTP, target **< 30 s** for the whole suite.

- Rendition ladder: longest-side 640/1280/2048, **never upscale**, collapsing targets skipped
  (`AC-ADM-05.2/3/4`), 1–3 renditions per photo, portrait and landscape.
- Deterministic names: `{longestSide}-{contentHash}.{format}` (`AC-ADM-05.6`,
  `AC-SEC-05.4`, `AC-SEC-06.1`).
- Format detection by **magic bytes**, not extension/`Content-Type` (`AC-SEC-05.1`);
  zero-byte/truncated/malformed rejection (`AC-SEC-05.2`); decompression-bomb guard before a
  full decode (`AC-ADM-05.10`, `AC-SEC-05.3`).
- EXIF/GPS/XMP stripped from renditions, ICC allowed (`AC-ADM-05.11`).
- Slug derivation rules (uniqueness needs the DB — that is `I`) and blank/over-long field
  validation (`AC-ADM-04.3`, `AC-ADM-06.2`).
- Cover-fallback selection rule (unit over the service's pure resolver), alt-text publish rule
  (`AC-ADM-08.4`).

Some of these are also asserted end-to-end in `I` (e.g. one real upload); `U` owns the
combinatorics so `I` stays fast.

**Not unit-tested:** controllers, repositories, security filters — they need the context and
belong to `I`.

### 3.2 Integration (backend) — `I`

Real PostgreSQL in **Testcontainers**, real Spring context, media written to a per-test
`@TempDir`; no mocked repositories. Target **< 5 min**.

- Every CRUD operation listed in `USE-CASES.md` §8 and every status code named in §2–6:
  `201/200/204`, `400` with `errors[]`, `401`, `404`, `409` (delete-with-children, slug
  collision), `413`.
- **Atomic batch upload** (`AC-ADM-05.7/8`): a valid+invalid batch leaves **zero** photo rows
  and **zero** files; retry succeeds.
- **Draft leakage** (`UC-SEC-01`): every public operation, including pagination totals;
  draft slug → `404` not `403`; public cover never a draft.
- **Auth** (`UC-SEC-03`): missing/expired/malformed/wrong-signature token; refresh token
  presented as access token; refresh rotation and reuse → `401` (`AC-ADM-02.2`).
- **CORS** (`UC-SEC-04`): allowed local origin vs a foreign origin; no wildcard with
  credentials.
- **Media** (`UC-SYS-02`, `UC-SEC-06`): files exist on disk after upload, `immutable` +
  `ETag`, `304` on match, originals not addressable, files removed on photo delete
  (`AC-ADM-09.1`).
- **Public write refusal** (`UC-SEC-02`): all `/api/**` mutations → `405`/`404`, never `200`.
- Persistence invariants: order updates, cover clearing on photo delete, independent
  publish flags, `GET /admin/albums/{id}/photos` includes drafts.
- Health (`UC-SYS-03`) and graceful behavior on an unreachable DB (startup probe/readiness).

Layout: `backend/src/test/java/.../integration/*IT.java`, run by Maven Failsafe in `verify`;
unit `*Test.java` runs in `test` with Surefire. Reuse one PostgreSQL container per JVM
(singleton pattern) and reset only the tables each test needs.

### 3.3 Contract — `C`

- **Always:** Spectral lint of `openapi.yaml` (`openapi/.spectral.yaml`) + a test that the
  spec parses, operation ids are unique, and every operation in `USE-CASES.md` §8 exists.
- **Phase 4 non-gate:** validate real requests/responses in-process against the spec
  (`swagger-request-validator` or equivalent) inside `I` tests. This catches "we shipped a
  field the contract doesn't declare" without a second running service.
- **Deferred:** generated property/fuzz tests (e.g. Schemathesis) against a live stack — a
  manual first pass until Phase 9, per `USE-CASES.md` §7 #10.
- **Consumer compile:** generation of the TypeScript client for frontend/admin must succeed
  from the committed spec (Phase 5/8). A type that no longer exists fails the consumer build.

The spec is never generated *from* the code for test purposes; `springdoc`'s `/v3/api-docs` is
informational only (`openapi/README.md`).

### 3.4 Build output (public frontend) — `B`

The Astro build is pointed at a **fixture API** (`test-fixtures/api`, contract-shaped JSON) so
CI needs no database and results are deterministic. The fixture dataset deliberately contains
published + draft tags/albums/photos, set and unset covers, and a tag with no albums.

Assertions over `dist/*.html` (Node + a DOM parser), one test per criterion:

- Gallery lists exactly the published albums in `sortOrder`; the tag filter lists only
  published tags (`AC-VIS-02.1/2`, `AC-VIS-03.1`, `AC-SEC-01.1`).
- Cover present, or fallback to first **published** photo; no draft cover (`AC-VIS-03.2`,
  `AC-SEC-01.3`).
- Album tag chips omit unpublished tags (`AC-SEC-01.1`).
- Album grid: published photos only, display order, every `<img>` has `width`/`height` and
  non-empty `alt` (`AC-VIS-04.1/2/4`).
- Draft album slug produces the 404 page (`AC-VIS-04.3`).
- `srcset`/`sizes` from available renditions, media URLs absolute, lazy vs eager rules
  (`AC-VIS-09.1/2/3`, `AC-NFR-02.1/2`).
- Home/About/Contact emit no client-side fetch to `/api/**` and no form (`AC-VIS-01.2`,
  `AC-VIS-06.1`, `AC-VIS-07.2`, `AC-SEC-02.3`).
- One `h1` per page, unique `<title>`/meta/OG, sitemap + `robots.txt` (`AC-VIS-06.2`,
  `AC-NFR-03`).
- Footer build date is the injected `BUILD_TIMESTAMP` with a fixed clock (`AC-ADM-11.2/3`).

Today the frontend still reads `frontend/src/data/albums.ts`; this harness lands with Phase 8
step 29 (build-time fetching). One **nightly** job rebuilds against the real seeded backend to
catch consumer/contract drift the fixture cannot see.

### 3.5 End-to-end (Playwright) — `E`

One root `e2e/` workspace with two projects (`visitor`, `admin`), Chromium only (mobile + desktop
viewports for the visitor; desktop-only admin). Runs against the **real** Compose stack
(PostgreSQL + backend + frontend + admin) from a clean volume.

**Admin — serial, one journey chained where it is cheaper:**

1. Login → create album → create a published tag inline → upload 2 valid photos → edit alt
   text → reorder → pick cover → publish photo + album → trigger rebuild (`AC-ADM-01`,
   `04–10`).
2. Upload a batch containing one invalid file → clear error, album unchanged, retry safe
   (`AC-ADM-05.8`, `AC-ADM-12.2`).
3. Publish a photo with empty alt text → UI blocks before the request (`AC-ADM-08.4`).
4. Expired/invalid session → back to login, no raw error (`AC-ADM-02.3`).
5. Private tunnel down → distinct "unreachable" message, never a false success
   (`AC-ADM-12.1/3`).
6. Zero tags/albums/photos → actionable empty states, no crash (`UC-ADM-13`).

**Visitor:**

1. Home → gallery → filter by tag → album → lightbox; arrows, `Esc`, focus trap, focus returns
   to the opener (`AC-VIS-01–05`, `AC-NFR-01.2`).
2. Unknown route shows the styled 404 with navigation (`AC-VIS-08.1`).
3. Contact links have correct `href`s and no form (`AC-VIS-07.1/2`).
4. `javaScriptEnabled: false` context: home and album still render; thumbnail is a plain link
   (`AC-VIS-01.3`, `AC-VIS-05.4`).
5. Mobile viewport smoke for the public header/menu.

**Rebuild is stubbed, not run.** E2E points the backend's CI trigger at a local webhook and
asserts the `202` + outgoing payload; "content becomes visible after a rebuild" is proven by the
`B` suite building from the post-rebuild fixture. This keeps E2E under 10 minutes.

**Isolation:** mutations run serially with a fresh compose project per run; visitor tests may
run in parallel (read-only). Seed through the **API**, not SQL, so E2E exercises the same paths
a photographer does. A UI login per test (tokens are in-memory by design) is the cost of
`AC-ADM-01.4`; use a helper, not `localStorage`.

### 3.6 Accessibility — `A`

- axe-core scan on 9 key screens (home, gallery, album, about, contact, 404, admin login,
  admin album detail, lightbox open), at mobile and desktop widths.
- **Gate: zero critical *and* zero serious issues.** WCAG AA contrast (4.5:1 body, 3:1 large/UI),
  semantic headings, labelled controls. Moderate/minor are reported, tracked, not gating.
- Keyboard assertions in Playwright: every interactive element reachable with a visible focus
  ring (`AC-NFR-01.1`); lightbox focus trap + restore (`AC-NFR-01.2`).
- `prefers-reduced-motion` context: lightbox/transition animation is suppressed (DESIGN.md §5,
  `global.css` rule).
- Alt text is a data rule, not an axe heuristic: enforced at publish (`AC-NFR-01.3`,
  `AC-ADM-08.4`).
- Exemptions are allowlisted by rule + selector with a comment and an owner — never a blanket
  disable.

### 3.7 Performance — `P`

Lighthouse CI against the **production build**, mobile emulation (Slow 4G, 4× CPU), cold cache,
median of 3 runs, on Home and the 12-photo Album page (the image-heavy one). Budgets are fixed
here, per `AC-NFR-02.3`:

| Metric | Budget | Note |
|---|---|---|
| LCP | **≤ 2.5 s** | p75-equivalent, mobile |
| CLS | **≤ 0.1** | images must declare dimensions |
| TBT (INP proxy) | **≤ 200 ms** | lightbox JS must stay small |
| Lighthouse perf score | ≥ 90 | advisory, not a hard gate |

Desktop is checked at 1440 px against the same CLS budget (LCP advisory). `P` is a Phase 9
gate; before that it runs nightly/advisory so tuning does not block feature merges.

### 3.8 Manual — `M`

- Visual pass against `layout/*.png` at 390 / 768 / 1440 (the gutter work lives here too).
- Nightly cron build actually runs and notifies on failure (`AC-SYS-01`).
- Footer date advances on a no-op rebuild (`AC-ADM-11.3`).
- Tunnel/`ssh -L` path, CORS origin, and `/admin/**` not publicly reachable (`AC-SEC-03.4`).
- Content review: alt text quality, titles, cover choice.

---

## 4. Test data & fixtures

One **seed dataset** serves `I`, `E` and the fixture API. It is small but adversarial:

| Fixture | Proves |
|---|---|
| 1 admin user (bcrypt) | login, hashing, no password in responses |
| 3 tags: heavy/light weight, one unpublished | ordering, hidden picks, tag filter AND semantics |
| 4 albums: published, draft, no-cover, empty | listing, 404, cover fallback, empty state |
| 8 photos: portrait, landscape, 900×600, draft, empty alt, long title, deleted-cover fallback | rendition ladder, draft exclusion, publish block, truncation |
| EXIF-tagged JPEG, corrupt `.jpg`, 25 MB+ file, bomb header | metadata stripping, magic bytes, `413`, decode guard |

- **Files:** a handful of real KB-sized images under `backend/src/test/resources/fixtures/`;
  over-limit and bomb files are generated on the fly (never committed).
- **The fixture API** (`test-fixtures/api`) serves the same seed as contract-shaped JSON for
  `B` tests — one dataset, three consumers.
- **Isolation:** integration tests own a temp media dir and reset touched tables; E2E wipes
  volumes at start; no test ever points at real content or a deployed environment.
- **Determinism:** fixed clock for build timestamps, fixed UUIDs in fixtures, sorted queries
  (an unordered `List` assertion is a flake waiting to happen).

---

## 5. Local commands & environments

| Suite | Command | Needs |
|---|---|---|
| Backend unit | `cd backend && ./mvnw test` | JDK only |
| Backend integration | `cd backend && ./mvnw verify` | Docker (Testcontainers) |
| Contract lint | the pinned `spectral` Docker command in `openapi/README.md` | Docker |
| Frontend build tests | `cd frontend && npm run test:build` | Node 22, fixture API |
| E2E (all) | `docker compose up -d --wait && npm run e2e` (root `e2e/`) | Docker, Node 22 |
| A11y / perf | `npm run e2e -- --project=a11y` / `npm run perf` | Docker / Chrome |

`test:build`, `perf` and the root `e2e/` workspace are the planned interfaces; they land with
their phases (5/8/9). CI mirrors these commands exactly; nothing is CI-only. Node is pinned to
22 (the host default is older — see `CI-CD.md` §9).

---

## 6. CI pipeline plan

Admin gets the first pipeline (`ROADMAP.md` Phase 6, `CI-CD.md`), but **full-stack E2E cannot
live there** — Phase 6 has no backend stack. The plan:

| Phase | Workflow / job | Trigger (paths) | Runs | Gate |
|---|---|---|---|---|
| 4 | `backend-ci` | `backend/**`, `openapi/**` | `./mvnw -B verify` (U+I), Spectral lint, upload reports | yes |
| 5/6 | `admin-ci` (planned, Phase 6) | `admin/**` | `npm ci`, lint, `tsc -b && vite build`, `docker build`, `npm test` when present | yes |
| 8 | `frontend-ci` | `frontend/**` | `npm ci`, `npm run build`, build-output tests (`B`) | yes |
| 9 | `e2e` (reusable) | PRs touching `**` | Compose up, seed, Playwright visitor+admin, axe, Lighthouse | yes if < 10 min and stable |
| 9 | `nightly` | cron + `workflow_dispatch` | Full suite, real-API frontend build, a11y/perf, scheduled rebuild (`AC-SYS-01`) | notify only |

Sketch of the first one (shape reused for frontend in Phase 9):

```yaml
name: backend CI
on:
  push: { branches: [main], paths: ['backend/**', 'openapi/**', '.github/workflows/backend-ci.yml'] }
  pull_request: { paths: ['backend/**', 'openapi/**', '.github/workflows/backend-ci.yml'] }
permissions: { contents: read }
jobs:
  test:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: backend } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: '21', cache: maven }
      - run: ./mvnw -B verify          # Surefire (U) + Failsafe (I, Testcontainers)
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: backend-reports, path: 'backend/target/*-reports' }
      - run: |
          docker run --rm -v "$PWD/..":/work -w /work \
            node:22-alpine sh -c "npx --yes @stoplight/spectral-cli lint openapi/openapi.yaml --ruleset openapi/.spectral.yaml"
```

Operational rules:

- **Path filters** everywhere (as the admin pipeline in `CI-CD.md` does); a docs-only commit runs
  nothing.
- **Caches:** npm (`setup-node cache: npm`), Maven (`setup-java cache: maven`), Docker layers
  (`type=gha`).
- **Artifacts on failure:** Surefire/Failsafe XML, Playwright traces/videos, Lighthouse JSON,
  axe results. Never debug a red CI by rerunning blind.
- **Branch protection:** required checks = `backend-ci`, `admin-ci`, `frontend-ci`; add `e2e`
  once its runtime and flake rate are proven (Phase 9). A required check that people learn to
  ignore is worse than none (`ROADMAP.md` step 21).
- **Secrets:** none for tests. No registry, no tunnel, no production credentials — the suite
  must run on a fork PR.

**Time budgets:** backend U < 30 s, I < 5 min, B < 2 min, E2E critical < 10 min, nightly full
< 25 min.

---

## 7. Gates & definition of done

Criteria are prioritised so a PoC can sequence the work honestly:

| Priority | Criteria | Becomes a gate |
|---|---|---|
| **P0** | Draft leakage, admin auth/CORS, atomic upload, media deletion/integrity, public write refusal (`UC-SEC-*`, `AC-ADM-05.7/8/9`, `AC-ADM-09.1`) | Phase 4 |
| **P1** | Core admin CRUD + visitor browse/lightbox, rebuild visibility, accessibility critical/serious | Phase 9 |
| **P2** | Performance budgets, SEO/OG/sitemap, empty-state polish | Phase 9, advisory until tuned |

Definition of done for a feature: its ACs are exercised at the level(s) in `USE-CASES.md` §8,
the test name contains the AC id, and the suite is green locally with the same command CI uses.

**Traceability check (Phase 9):** a small script greps the test trees for `AC-<AREA>-<n>.<m>` and
diffs the set against `USE-CASES.md` §8. A P0/P1 criterion with no test fails the job; an
orphaned AC id in a test warns. This is what keeps the catalogue from drifting into fiction.

---

## 8. Deliberately out of scope

- Cross-browser matrix (Firefox/WebKit) — Chromium only for the PoC.
- Visual-regression snapshots — the Figma pass is manual (`M`), pixels are cheaper to review
  than to maintain.
- Load/soak testing and CDN tuning — portfolio scale, one host (`ARCHITECTURE.md`).
- k3s, SBOM/provenance, image signing — later concerns (`CI-CD.md` §11).
- Admin mobile layouts — admin is desktop-only by design.
- Redirects on slug rename — accepted PoC limitation (`USE-CASES.md` §7 #8).
- Exhaustive JS-disabled permutations — the two critical pages only.

---

## 9. Risks & watch items

| Risk | Mitigation |
|---|---|
| Fixture API drifts from the real API → `B` tests pass, site breaks | Nightly build against the seeded real backend; contract lint in the same CI. |
| E2E rebuild test is slow/flaky | Stub the CI trigger; assert payload + `202`; prove visibility in `B`. |
| Testcontainers unavailable on a runner | GitHub `ubuntu-latest` has Docker; fail fast with a clear message rather than skipping. |
| Media tests leave files behind / collide | Temp media dir per test; content-hash names make cross-test collisions impossible. |
| Decompression-bomb fixture hurts the runner | Generate the header only; assert refusal before decode. |
| Lighthouse variance causes red builds | Median of 3, fixed emulation, metrics gate (score advisory). |
| In-memory admin tokens make E2E slow | One login helper per worker; still assert the reload-logs-out rule once. |
| Tag lifecycle endpoints have no dedicated UI scenario | `createTag` is covered inline; the rest have no UI scenario until a tag screen exists. |

---

## 10. Decisions needed (review)

1. **Contract validation approach** — Spectral + in-process request/response validation now;
   generated fuzz tests deferred (§3.3). Accept? Accept
2. **Perf budgets** — LCP ≤ 2.5 s, CLS ≤ 0.1, TBT ≤ 200 ms, score ≥ 90 advisory (§3.7).
   Accept or tighten? Accept
3. **One root `e2e/` workspace** + `test-fixtures/api` shared by `B` and `E` (§3.4/3.5). Accept
4. **Full-stack E2E starts in Phase 9**, not Phase 6 — admin CI in Phase 6 stays
   lint/build/docker. Accept? Accept
