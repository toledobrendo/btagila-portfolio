# portfolio-frontend

Public portfolio site — Astro 7 with Tailwind CSS 4, built as **pure static output**
(no adapter, no runtime server).

Gallery content is fetched from the backend API **at build time**, so the built site is
just files. A published change therefore requires a rebuild (see `../ARCHITECTURE.md`
§1 and §7).

## Prerequisites

**Node ≥ 22.22.0** — Astro 7 requires it (`package.json` declares it under `engines`).

> ⚠️ **On this machine right now:** the system Node is **18.19.1**, which Astro 7 does
> not support. Either install Node 22+, or use the Docker commands below.

## Commands

With Node 22+:

```bash
npm install
npm run dev        # dev server on http://localhost:4321
npm run build      # static output → dist/
npm run preview    # serve the built output locally
npm run check      # astro check: type-checks .astro/.ts files
```

Without a local Node 22 (Docker):

```bash
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e npm_config_cache=/tmp/.npm \
  -v "$PWD":/app -v /tmp/opencode/npm-cache:/tmp/.npm -w /app node:22-alpine \
  sh -c "npm install && npm run build"
```

## Preview with local Docker

Every command below was run against this repository and returns **HTTP 200**. Use them
while there is no local Node 22, and as a rehearsal of the containerized flow CI will use.

**Dev server** — renders pages on demand, so gallery data is fetched when you load a page:

```bash
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e npm_config_cache=/tmp/.npm \
  -v "$PWD":/app -v /tmp/opencode/npm-cache:/tmp/.npm -w /app -p 4321:4321 node:22-alpine \
  sh -c "npm run dev -- --host 0.0.0.0 --port 4321"
```

→ <http://localhost:4321/>

**Production build** — build and serve `dist/` in one container:

```bash
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e npm_config_cache=/tmp/.npm \
  -v "$PWD":/app -v /tmp/opencode/npm-cache:/tmp/.npm -w /app -p 4321:4321 node:22-alpine \
  sh -c "npm run build && npm run preview -- --host 0.0.0.0 --port 4321"
```

**Static files, served the way Phase 8 will serve them** — plain nginx over `dist/`:

```bash
docker run --rm -p 8080:80 -v "$PWD/dist":/usr/share/nginx/html:ro nginx:alpine
```

→ <http://localhost:8080/>

### Gotchas

- **`--host 0.0.0.0` is mandatory.** Astro binds to `127.0.0.1` inside the container, so
  without it the published port never reaches the server. Host and container ports are
  kept identical (`4321:4321`) on purpose — that way the hot-reload WebSocket needs no
  `server.hmr` configuration.
- **`--user "$(id -u):$(id -g)"`** keeps files written into the mount owned by you rather
  than root; `HOME=/tmp` and `npm_config_cache` keep npm's cache inside the container
  instead of your home directory.
- **`node_modules/` is Alpine-built (musl).** The same `node:22-alpine` image runs it, so
  it matches — but if you later install Node on the host (glibc), delete `node_modules`
  and reinstall. Native binaries (`esbuild`, `rollup`) are platform-specific.
- **The built site is frozen at build time.** After a backend content change, re-run
  `npm run build` for it to appear in `dist/`. `.env` is read when the container starts,
  so restart it after changing configuration.

## Configuration

Copy `.env.example` to `.env`. Values are read at **build time**.

| Env var | Default | Purpose |
|---|---|---|
| `PUBLIC_API_BASE_URL` | `http://localhost:8080` | Backend API base URL. `PUBLIC_` because the contact form posts from the browser, so the value must be client-visible. Never put secrets here. |

## Images

Images are **not** optimised by Astro's build-time image pipeline. The backend's media
module (Phase 3) generates a fixed set of WebP renditions (640/1280/2048 px wide) at upload
time and serves them from its media volume, and the frontend emits `srcset`/`sizes` pointing
at those rendition URLs. Originals are assumed to be ≤ 2048 px on the longest side, so the
backend never resizes on demand and never upscales.

Keeping optimisation at upload time means the work happens once per photo instead of on
every build, and the static site needs no access to original files.

## Layout

```
src/
├── pages/          file-based routes (index.astro, gallery/, about, contact …)
├── styles/
│   └── global.css  Tailwind entry: @import "tailwindcss"
└── (layouts, components, lib → arrive with the design system in Phase 6)

public/             static assets served as-is (favicon, …)
astro.config.mjs    static output, Tailwind via the Vite plugin
tsconfig.json       extends astro/tsconfigs/strict
```

Design tokens and the real page set are Phase 6 of `../ROADMAP.md`. The OpenAPI contract
that this site fetches from is Phase 1.5.
