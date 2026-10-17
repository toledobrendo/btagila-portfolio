# portfolio-admin

Admin app for the portfolio — **React 19 + Vite 8 + Tailwind CSS 4**, styled with plain
Tailwind (no component library).

It runs on the **photographer's local machine**, not on the public server, and reaches the
backend over a private tunnel. Admin endpoints (`/admin/**`) are never exposed to the
internet (see `../ARCHITECTURE.md` §6).

## Prerequisites

**Node `^20.19.0 || >=22.12.0`** (required by Vite 8; declared in `package.json`).

> ⚠️ **On this machine right now:** the system Node is **18.19.1**, which Vite 8 does not
> support. Either install Node 22+, or use the Docker commands below.

## Commands

With Node 22+:

```bash
npm install
npm run dev        # dev server on http://localhost:5173
npm run build      # tsc -b && vite build → dist/
npm run preview    # serve the built output
npm run lint       # oxlint
```

Without a local Node 22 (Docker):

```bash
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e npm_config_cache=/tmp/.npm \
  -v "$PWD":/app -v /tmp/opencode/npm-cache:/tmp/.npm -w /app node:22-alpine \
  sh -c "npm install && npm run build"
```

## Preview with local Docker

Every command below was run against this repository and returns **HTTP 200**. Use them
while there is no local Node 22.

**Dev server** — live reload:

```bash
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e npm_config_cache=/tmp/.npm \
  -v "$PWD":/app -v /tmp/opencode/npm-cache:/tmp/.npm -w /app -p 5173:5173 node:22-alpine \
  sh -c "npm run dev -- --host 0.0.0.0 --port 5173"
```

→ <http://localhost:5173/> — that port is already in the backend's `CORS_ALLOWED_ORIGINS`
default, so browser calls to the API are allowed without touching configuration.

**Production build** — build, then serve `dist/` in one container:

```bash
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e npm_config_cache=/tmp/.npm \
  -v "$PWD":/app -v /tmp/opencode/npm-cache:/tmp/.npm -w /app -p 5173:5173 node:22-alpine \
  sh -c "npm run build && npm run preview -- --host 0.0.0.0 --port 5173"
```

`vite preview` defaults to port **4173**, which is *not* in the backend's allowed CORS
origins. It is pinned to 5173 above so the origin matches; if you use 4173 instead, add it
to `CORS_ALLOWED_ORIGINS` once the API calls land in Phase 5.

> The backend must be running (`./mvnw spring-boot:run` in `../backend`) for real data.
> The admin screens that call it arrive in Phase 5.

### Gotchas

- **`--host 0.0.0.0` is mandatory.** Vite binds to `127.0.0.1` inside the container, so
  without it the published port never reaches the server. Host and container ports are
  kept identical (`5173:5173`) on purpose — that way the hot-reload WebSocket needs no
  `server.hmr` configuration.
- **`--user "$(id -u):$(id -g)"`** keeps files written into the mount owned by you rather
  than root; `HOME=/tmp` and `npm_config_cache` keep npm's cache inside the container
  instead of your home directory.
- **`node_modules/` is Alpine-built (musl).** The same `node:22-alpine` image runs it, so
  it matches — but if you later install Node on the host (glibc), delete `node_modules`
  and reinstall. Native binaries (`esbuild`, `rollup`) are platform-specific.

## Configuration

Copy `.env.example` to `.env.local` or `.env`. Only `VITE_`-prefixed variables reach the
app, and they are embedded in the client bundle — **no secrets**.

| Env var | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8080` | Backend API base URL (`/admin/**` endpoints) |

The dev server's default port (5173) is already in the backend's `CORS_ALLOWED_ORIGINS`
default, so local development works without extra configuration.

## Structure

```
src/
├── main.tsx        entry point
├── App.tsx         placeholder shell
└── index.css       Tailwind entry: @import "tailwindcss"

index.html          Vite HTML entry
vite.config.ts      React + Tailwind plugins
.oxlintrc.json      linting (oxlint — the create-vite default; ESLint not installed)
```

## Notes

- **Linting is oxlint**, not ESLint — that is what create-vite 9 generates for React
  templates. If the CI conventions in Phase 9 need ESLint specifically, this is the file
  to revisit.
- **Auth token handling** follows `../ARCHITECTURE.md` §6: JWT in the `Authorization`
  header, held in memory with a short expiry rather than `localStorage`.
- **Routing** (login → dashboard → upload → albums) is deliberately not
  installed yet; it arrives with the screens in Phase 5.
