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
| **frontend** | A TypeScript client is generated from it (Phase 6) so build-time fetching is type-checked. |
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
directory, not the spec file. Phase 7 wires this into CI.

To read the API as documentation rather than YAML, run the backend and open
<http://localhost:8080/swagger-ui.html> — or drop `openapi.yaml` into any OpenAPI viewer.

## Decisions this contract fixes

These are the choices a consumer would otherwise have to guess at. Changing any of them
is a contract change, not an implementation detail.

- **`album` is the entity** (not "gallery"): a category contains albums, an album contains
  photos. "Gallery" is the public *index page* that lists categories. Matches the domain
  model in `../ARCHITECTURE.md` §4.
- **Split API**: `/api/**` public (read-only plus the contact form); `/admin/**` requires a
  JWT bearer token and is reachable only over a private tunnel.
- **Pagination**: zero-based `page` + `size`, page envelope `{items, page, size,
  totalItems, totalPages}`. Offsets are fine at portfolio scale.
- **Errors**: `application/problem+json` (RFC 9457) — Spring Boot's default — with an
  `errors[]` array for bean-validation failures.
- **Media**: variants are content-hashed (`480-a3f19c2b.webp`), so their URLs are
  immutable and cacheable for a year. The URL embeds the hash, so re-encoding identical
  bytes keeps the URL stable and changed bytes get a new one.
- **CORS**: documented under `x-cors-allowed-origins` (defaults `localhost:5173` and
  `:4321`, matching `backend/src/main/resources/application.yml`). The OpenAPI spec has no
  standard field for it.
- **Uploads** are multipart batches attached to an album, 25 MB per file / 100 MB per
  request, and create **drafts** — publishing is a separate, explicit step.
- **Tokens**: short-lived access token plus a rotating refresh token; the admin holds both
  in memory (never `localStorage`).

## Deliberately not in the contract (yet)

- About-page content — it is static Astro content, not an API resource (Phase 6).
- Admin user management — one photographer, one account. The `app_user` table exists; no
  CRUD endpoints.
- Refresh-token revocation/denylist — rotation covers the hobbyist threat model.
