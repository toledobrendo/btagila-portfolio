# Roadmap: Portrait Photographer Portfolio

A portrait photographer portfolio website, also serving as a proof of concept for AI-assisted development.

**Stack decisions:**
- **Backend:** Spring Boot + PostgreSQL (REST API, media storage, auth)
- **Public frontend:** Astro (static output, fetches gallery data from the API)
- **Admin UI:** Separate module/app, runs on the photographer's **local machine** (never publicly exposed)
- **Pages:** Home + Gallery + About + Contact, galleries by category
- **Deployment:** Each module is its own Docker image. **Docker Compose on a single small VPS first, k3s later** (same images); every module also deployable locally.
- **CI/CD:** GitHub Actions + GHCR (GitHub Container Registry). The **admin** module gets the first pipeline as a deliberate learning exercise — Phase 6 is continuous **delivery** (tag → image in GHCR → explicit pull), Phase 7 is continuous **deployment** (a self-hosted runner on the local machine). Backend and frontend reuse the same shape later. Design in `CI-CD.md`.

**Monorepo layout:**

```
portfolio/
├── .github/workflows/   # CI/CD pipelines (admin first — Phase 6)
├── docker-compose.yml   # full local stack: postgres + backend + frontend + admin
├── backend/    # Spring Boot (REST API + media handling) + Dockerfile
├── frontend/   # Astro public site + Dockerfile
├── admin/      # Admin UI + Dockerfile
└── deploy/     # compose (VPS) + Kubernetes manifests / Helm chart (later)
```

Each module builds to an **independent Docker image**, versioned and deployable on its own — locally, on the VPS, or on k3s.

---

## Phase 1 — Foundation

1. **Scaffold the backend**: Spring Boot (Java 21+, Maven/Gradle), with modules for web (REST), persistence (JPA), security, and media.
2. **Scaffold the public frontend**: `npm create astro` with TypeScript, Tailwind CSS — pure static build (no Node adapter needed anymore).
3. **Scaffold the admin app** (separate frontend, e.g. Astro or React + Vite + Tailwind) — designed to run **locally** on the photographer's machine.
4. **Init git** with a sensible `.gitignore` (exclude `data/`, build outputs, `.env`).
5. **Define the API contract first** (OpenAPI spec): endpoints for categories, albums, photos and admin operations — including the **JWT bearer security scheme** and the CORS-allowed origins. This is the contract all three modules are built against.

## Phase 2 — Use cases, UI design & test strategy

6. **Use case catalog**: actors (visitor, photographer/admin) and their scenarios — visitor: browse galleries by category, view album with lightbox, read about, reach the photographer via Facebook/Instagram; admin: log in, batch-upload photos, organize into albums/categories, reorder, publish/draft, pick cover. Write each scenario as **Given/When/Then acceptance criteria — these double directly as test cases** in the phases that follow. Deliverable: `USE-CASES.md` (draft for review).
7. **UI design**: wireframes/mockups for the key screens (public: home, gallery index, category, album + lightbox, about, contact; admin: login, dashboard, upload, album management). Define **design tokens** up front (typography, palette, spacing). Iterate with the photographer on the mockups *before* any UI is built — taste is the product.
8. **Test strategy**: decide per level what gets tested — unit + integration (Testcontainers with PostgreSQL) for the backend, contract tests generated from the OpenAPI spec, E2E (Playwright) for the critical admin and visitor flows, plus a11y/performance checks. Plan the CI pipeline that will run it all (admin first — Phase 6).

## Phase 3 — Data & media layer

9. **PostgreSQL schema** (via Flyway migrations): `categories`, `albums`, `photos` (title, ordering, published flag, cover), `app_user`.
10. **Image pipeline** with `imgscalr` or TwelveMonkeys/ImageIO (or shell out to `sharp` via a small Node tool): on upload, generate a small **fixed** set of WebP renditions (640/1280/2048 px **longest side**, so portrait and landscape get the same steps), store originals on disk, record metadata in PostgreSQL. Originals are assumed to be ≤ 2048 px on the longest side, so there is no on-demand resizing and no upscaling — adding a size later is a config change, not a new code path.
11. **Local deployment of the whole stack**: a root `docker-compose.yml` brings up PostgreSQL + backend + frontend + admin, and each module also runs standalone from its own Dockerfile (so any single one can be deployed/run on the local machine). Keep config 12-factor style (env vars) from day one so the same images run locally, on the VPS, and on k3s unchanged.

## Phase 4 — API & security

12. **Auth (JWT)**: admin login endpoint (bcrypt-hashed password), role claim, Spring Security stateless JWT validation on `/admin/**`; CORS restricted to the admin's local origin(s). Access token + short expiry, in-memory on the admin side. **Split the API**: `/api/**` public (read-only), `/admin/**` reachable only over a private tunnel.
13. **CRUD endpoints**: categories, albums, photos (multipart upload, reorder, publish/draft, cover selection). Batch uploads are **atomic** (one bad file → nothing persisted); publishing a photo requires non-empty `altText`; the admin photo list includes drafts (`GET /admin/albums/{id}/photos`).
14. **Public read endpoints + media**: published galleries/photos only; media files served by the backend with `ETag` and `Cache-Control: immutable` on content-hashed renditions.
15. **Probe-ready backend behavior**: Spring Boot Actuator health/readiness endpoints, graceful shutdown, all config via env vars — no hardcoded paths, media directory configurable via volume mount (works for Compose now, k8s probes later).
16. **Tests alongside**: unit + integration tests with Testcontainers (real PostgreSQL), security tests, and contract tests against the OpenAPI spec — driven by the Phase 2 acceptance criteria.

## Phase 5 — Admin UI (separate module)

17. **Login screen** + token/session storage.
18. **Screens**: dashboard, drag-and-drop upload, category & album management, photo reorder, publish/draft toggle, cover picker.
19. **Playwright tests** for the critical admin flows: login, upload, organize, publish.

## Phase 6 — CI & continuous delivery for admin (practice)

The goal of this phase is to learn the pipeline *mechanics* (triggers, caching, artifacts, permissions, logs) on the simplest module, and to separate **delivery** from **deployment** — this phase never touches a running service.

20. **Admin image + CI workflow** — give the module something to deliver *and* a way to check it. First `admin/Dockerfile` (multi-stage: Node 22 build → **unprivileged nginx**) plus `admin/.dockerignore`, so the module is a real artifact (`docker build -t admin admin/`); Phase 3 step 11 may have added a minimal one for local runs — this is where it becomes registry-ready. Then `.github/workflows/admin-ci.yml`, triggered by pull requests and pushes that touch `admin/**` (path filters, so unrelated commits don't burn minutes). Steps: `npm ci` with the npm cache, `npm run lint` (oxlint), `npm run build` (type-checks via `tsc -b`, then `vite build`), and a `docker build` to prove the Dockerfile. Upload `dist/` as a build artifact; add a `npm test` step once Phase 5 introduces tests.
21. **Make the checks blocking** — branch protection on `main` requiring the admin CI checks, plus a documented local equivalent (the same commands, runnable before pushing). CI only has value if a failing check actually prevents the merge.
22. **Continuous delivery: tag → image in GHCR** — on a version tag (`admin-v*`), build and push a versioned image to `ghcr.io/toledobrendo/btagila-portfolio/admin` (tagged `vX.Y.Z`, `sha-<short>` and `latest`) and cut a GitHub Release describing the change. Deploying stays a deliberate, documented command on the local machine: `docker compose pull admin && docker compose up -d admin`. That is the whole "tag → artifact → consume" loop — what most people mean by CD.

## Phase 7 — Continuous deployment for admin (local, practice)

Delivery (Phase 6) ends with a published artifact. This phase removes the human from the last step — on a machine that is *not* a server.

23. **Self-hosted runner on the local machine** — register a GitHub Actions self-hosted runner, scoped to a runner group, so workflows can run on the machine that actually serves the admin app. Document install, update and removal. Security rule: **private repo only, and fork PRs must never be able to trigger it** — a workflow on a self-hosted runner executes with your filesystem, Docker socket and SSH keys in reach. See `CI-CD.md`.
24. **Auto-deploy on release** — `.github/workflows/admin-deploy.yml`, triggered when a release is published: pull the new image, `docker compose up -d admin`, wait for a health check, and automatically roll back to the previous tag if it fails. Target configuration and secrets live on the runner, never in the repository.
25. **Deploy visibility & rollback** — a `deploy` GitHub Environment recording what shipped and when, success/failure notification, and a documented manual rollback (re-run compose with the previous image tag). A deployment you can't reverse isn't a deployment.

## Phase 8 — Public site

26. **Apply the design system** from Phase 2 (tokens → Tailwind config, layout, typography).
27. **Pages**: Home (hero + featured work), Gallery index → Category → Album with lightbox, About, Contact.
28. **Contact page**: static Astro linking Facebook/Instagram (plus a `mailto:` email) — no form and no backend write, so the public API stays read-only.
29. **Data fetching + rebuild trigger**: build-time fetching from the API. The trigger is a manual **"Rebuild site" button** in admin, with a nightly cron as the backstop (`ARCHITECTURE.md` §7, decision A) — publishing does **not** auto-trigger a rebuild, and automatic triggering + debounce is a documented growth path, not PoC scope. The footer shows the **build date**, baked in at build time, so a landed rebuild is visible at a glance. Deploy = new frontend image tag → rolling update.
30. **Playwright tests** for visitor flows: browse by category, open album/lightbox.

## Phase 9 — Testing & quality assurance

31. **Full E2E suite**: every Phase 2 use case covered, runnable against the docker-compose stack locally and in CI.
32. **Performance**: responsive `srcset`, lazy loading, optimized WebP output, Astro image tooling for local assets.
33. **SEO/a11y**: meta + OG tags, sitemap, alt text discipline, keyboard-navigable lightbox, mobile responsiveness, automated a11y checks (axe) in CI.
34. **Backend hardening**: input validation, upload limits/type checks, filename sanitization.
35. **CI for all modules**: promote the Phase 6 admin workflow into a reusable workflow and apply it to the backend and frontend — lint + build, unit/integration/E2E tests, and Docker image builds on every push.

## Phase 10 — Deployment

36. **Docker images** — one per module, each independently buildable, runnable locally, and versioned (git tag → image tag):
    - `backend`: multi-stage build (JDK build → slim JRE/distroless runtime), non-root user, media dir as configurable mount point.
    - `frontend` / `admin`: Node build stage → **unprivileged nginx** (or Caddy) serving static files — the admin image is already registry-ready from Phase 6; Phase 10 makes versioning and publishing uniform across modules.
37. **Local stack**: root `docker-compose.yml` (PostgreSQL + backend + frontend + admin). This is the dev environment, the demo environment, and the way any one module is run on the local machine.
38. **Budget production path (Compose on one small VPS)** ≈ €6–9/month:
    - VPS: Hetzner CX33 (4 vCPU / 8 GB) — ~€9/mo incl. IPv4; CX23 (2 vCPU / 4 GB, ~€6/mo) is the floor.
    - Reverse proxy (Caddy/Traefik) + free Let's Encrypt TLS for `portfolio.<domain>` and `api.<domain>`; or a Cloudflare Tunnel to open no ports.
    - PostgreSQL container + volume on the same box; media on local disk served by the backend (single host ⇒ RWO is a non-issue).
    - Frontend build runs in **CI**, not on the VPS — the box only serves.
    - Backups: `restic`/`rclone` of the Postgres dump + media to Cloudflare R2 / Backblaze B2 (R2: 10 GB free, zero egress).
39. **Admin on the local machine**: admin SPA runs on the photographer's machine and reaches the backend over a **private tunnel (Tailscale/WireGuard)** — `/admin/**` never exposed publicly. Fallback: `ssh -L` port-forward. Public traffic only ever touches `/api/**` (read-only) and image URLs.
40. **Growth path — k3s**: when needed, run the same images on single-node k3s (certified Kubernetes), keeping the manifests in `deploy/`. Only multi-node adoption forces media onto object storage to lift the single-attach constraint.
41. **Ops**: env-var config, restart policies (Compose) / probes and graceful shutdown (k3s), log rotation, and a documented restore procedure for Postgres + media.

## Phase 11 — The PoC write-up

42. **README/docs** capturing the AI-assisted process: prompts, iteration notes, what worked vs. what needed manual fixes — the actual proof-of-concept deliverable.

---

## Risk notes

- **Three deployables** (backend, frontend, admin) is more moving parts than a single app — the API contract (OpenAPI) is what keeps them in sync, so define it early.
- **Image processing in the JVM** is workable (imgscalr, TwelveMonkeys) but less polished than `sharp`; consider a tiny Node-based preprocessing step if quality/performance falls short.
- **Build-time fetching** means the public site refreshes only on a rebuild, and the rebuild is **manual** — the admin "Rebuild site" button, with a nightly cron as the backstop (`ARCHITECTURE.md` §7, decision A). Automating the trigger (with a debounce) is a documented growth path.
- **Image uploads** need care: file type validation, size limits, and filename sanitization.
- **RWO media volume is a non-issue on one host** — with a single VPS (or single-node k3s) there's only one node to attach it to. It only constrains you if the app spreads to multiple nodes; then move media to object storage (R2/S3) to make the backend stateless.
- **Images served by the backend** means photo bandwidth flows through the backend process — cache hard (immutable, content-hashed renditions) and size the box with that in mind. Hetzner's 20 TB included egress is plenty.
- **Admin on a local machine** means the admin must reach the API over a private tunnel (Tailscale/WireGuard) — don't be tempted to expose `/admin/**` publicly. Allowlist exact CORS origins (no wildcards), keep the JWT in memory, and note batch uploads travel over home upload bandwidth.
- **Self-hosted runner = arbitrary code on your machine** — the Phase 7 runner must only ever be attached to a private repo, and fork PRs must not be able to trigger workflows on it. A workflow running there has your filesystem, Docker socket and SSH keys in reach.
- **Single VPS = single point of failure** — acceptable for a hobbyist portfolio, but keep the Postgres + media backups tested and offline (R2/B2), not on the same box.
- **Rebuild storms**: only a concern if publishing is later automated. With the manual button (decision A) there is none — a debounce is required *before* adding auto-triggering, not now (see `ARCHITECTURE.md` §7).
- **Renaming breaks public URLs**: changing a category/album `slug` changes its path, and no redirect is served. Accepted for the PoC (no existing traffic to preserve); a real site would need a slug-history table.
- **UI design is where AI-generated output is most visible** — budget real iteration time with the photographer in Phase 2; a generic-looking portfolio undermines the PoC.
- **Test scope for a PoC**: keep the E2E suite focused on critical flows (upload → publish → browse); exhaustive UI testing isn't worth the cost here.
- **K8s specifics**: keep the manifests portable so the Compose → k3s move is a redeploy, not a rewrite; each image must be pushed to a registry the target can pull from.
