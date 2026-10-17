# API contract

`openapi.yaml` is the **normative** contract for the whole project — hand-written before
the code, and the thing that keeps three independently built (and AI-generated) modules
from drifting apart (`../ARCHITECTURE.md` §5).

OpenAPI **3.1.0**, matching what `springdoc-openapi` 3.1 generates from the backend.

| File | Purpose |
|---|---|
| `openapi.yaml` | The contract. Single source of truth. |
| `.spectral.yaml` | Linter config — the official OpenAPI ruleset (`spectral:oas`). |

## How each module uses it

| Module | Use |
|---|---|
| **backend** | Implements it. Contract tests (Phase 4) assert the running API matches this file. `/v3/api-docs` is springdoc's *generated* view — informational only, never authoritative. |
| **frontend** | A TypeScript client is generated from it (Phase 8) so build-time fetching is type-checked. |
| **admin** | Same generated client (Phase 5), including the auth types. |

Because the contract is hand-written, a spec change is a normal code change: update this
file in the same commit as the behaviour it describes. Contract tests are what catch
drift.

## Validating

No local Node required — the image is pinned:

```bash
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e npm_config_cache=/tmp/.npm \
  -v "$PWD":/work -v /tmp/opencode/npm-cache:/tmp/.npm -w /work node:22-alpine \
  sh -c "npx --yes @stoplight/spectral-cli lint openapi/openapi.yaml --ruleset openapi/.spectral.yaml"
```

`--ruleset` is explicit because Spectral resolves its config relative to the working
directory, not the spec file. Phase 9 wires this into CI.

To read the API as documentation rather than YAML, drop `openapi.yaml` into any OpenAPI
viewer. The backend's own Swagger UI (`/swagger-ui.html`, `/v3/api-docs`) is already wired
up but sits behind Spring Security's default chain until Phase 4, so it returns `401`
today — it becomes usable once the security configuration lands.

## Decisions this contract fixes

These are the choices a consumer would otherwise have to guess at. Changing any of them
is a contract change, not an implementation detail.

- **`album` is the entity** (not "gallery"): a category contains albums, an album contains
  photos. "Gallery" is the public *index page* that lists categories. Matches the domain
  model in `../ARCHITECTURE.md` §4.
- **Split API**: `/api/**` public and read-only (no public write endpoints); `/admin/**` requires a
  JWT bearer token and is reachable only over a private tunnel.
- **Pagination**: zero-based `page` + `size`, page envelope `{items, page, size,
  totalItems, totalPages}`. Offsets are fine at portfolio scale.
- **Errors**: `application/problem+json` (RFC 9457) — Spring Boot's default — with an
  `errors[]` array for bean-validation failures.
- **Media**: renditions are content-hashed (`1280-a3f19c2b.webp`), so their URLs are
  immutable and cacheable for a year. The URL embeds the hash, so re-encoding identical
  bytes keeps the URL stable and changed bytes get a new one.
- **CORS**: documented under `x-cors-allowed-origins` (defaults `localhost:5173` and
  `:4321`, matching `backend/src/main/resources/application.yml`). The OpenAPI spec has no
  standard field for it.
- **Uploads** are multipart batches attached to an album, 25 MB per file / 100 MB per
  request, and create **drafts** — publishing is a separate, explicit step.
- **Uploads are atomic**: a batch containing any invalid file creates nothing — the whole
  request is rejected (`400`/`413`), so an album is never half-imported.
- **Accessibility gates publishing**: a photo with an empty `altText` cannot be published
  (`400`), enforced by both the backend and the admin UI. Uploads therefore start
  unpublished until alt text is written.
- **Cover photos**: the pick must belong to the album; when absent (or deleted) the cover
  falls back to the first photo — for public reads, the first **published** photo, so a
  draft is never exposed as a cover. Deleting the cover photo clears the reference rather
  than failing.
- **Publishing is per level**: a photo, its album and its category each have their own
  `published` flag; publishing one never publishes its parent.
- **Rebuild trigger is manual** (decision A): `POST /admin/rebuild` is the "Rebuild site" button,
  with a nightly cron as the backstop. **Publishing never auto-triggers a rebuild**, and the
  response is asynchronous (`202`) — the footer's build date confirms completion. Auto-triggering
  with a debounce is a documented growth path, not PoC scope (`../ARCHITECTURE.md` §7).
- **Tokens**: short-lived access token plus a rotating refresh token; the admin holds both
  in memory (never `localStorage`).

## Deliberately not in the contract (yet)

- About-page content — it is static Astro content, not an API resource (Phase 8).
- Contact form / messages — the Contact page is static Astro linking Facebook and
  Instagram (plus a `mailto:` email). There is no public write endpoint and no admin inbox
  (a deliberate simplification: zero public write surface, nothing to rate-limit or spam-filter).
- Admin user management — one photographer, one account. The `app_user` table exists; no
  CRUD endpoints.
- Refresh-token revocation/denylist — rotation covers the hobbyist threat model.
- URL redirects on rename — changing a category/album `slug` breaks its previous public
  URL. Accepted for the PoC: a rename is a deliberate act, and there is no traffic to
  preserve yet. Redirects would need a slug-history table.
