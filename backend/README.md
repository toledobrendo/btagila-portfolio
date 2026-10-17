# portfolio-backend

REST API for the portrait photographer portfolio — categories, albums and photos.

**Spring Boot 4.1.1 · Java 21 · Maven · PostgreSQL 18 · Flyway**

Public, read-only endpoints live under `/api/**`. Admin endpoints (JWT-protected) live
under `/admin/**` and are intended to be reachable only over a private tunnel
(see `../ARCHITECTURE.md` §6).

## Package layout

```
src/main/java/com/btagila/portfolio/
├── web/           REST controllers, request/response records, error handling
├── persistence/   JPA entities + Spring Data repositories (schema owned by Flyway)
├── security/      JWT issuing/validation, Spring Security config, admin user
├── media/         upload validation, rendition generation, storage
└── config/        @ConfigurationProperties + shared infrastructure beans

src/main/resources/
├── application.yml     12-factor config (every value overridable by env var)
└── db/migration/       Flyway migrations: V<n>__<description>.sql
```

## Prerequisites

- **A full JDK 21** (a JRE is not enough — Maven needs `javac`)
- **Docker** — for the local Postgres and for Testcontainers

> ⚠️ **On this machine right now:** `/usr/lib/jvm/java-21-openjdk-amd64` is JRE-only
> (no `javac`), and the `javac` on `PATH` is 1.7. Builds fail with
> `release version 21 not supported` until `JAVA_HOME` points at a real JDK 21 — or
> you use the Docker build below.

## Build

With a full JDK 21:

```bash
export JAVA_HOME=/path/to/jdk-21
./mvnw -DskipTests package
```

Without a JDK installed (Docker, Maven 3.10 + Temurin 21):

```bash
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e MAVEN_CONFIG=/tmp/.m2 \
  -v "$PWD":/app -v /tmp/opencode/m2:/tmp/.m2 -w /app \
  maven:3.10.0-eclipse-temurin-21-noble mvn -B -ntp -DskipTests package
```

## Run

`spring-boot-docker-compose` reads `compose.yaml`, starts Postgres automatically, and
wires the datasource:

```bash
export JAVA_HOME=/path/to/jdk-21
./mvnw spring-boot:run
```

Or start the database yourself and point the app at it:

```bash
docker compose up -d          # Postgres 18 on localhost:5432
./mvnw spring-boot:run
```

## Test

```bash
./mvnw test                   # Testcontainers starts PostgreSQL 18 (requires Docker)
```

## Configuration

Every value has a local default and an environment-variable override:

| Env var | Default | Purpose |
|---|---|---|
| `DB_URL` | `jdbc:postgresql://localhost:5432/portfolio` | JDBC URL |
| `DB_USERNAME` | `portfolio` | Database user |
| `DB_PASSWORD` | `portfolio` | Database password |
| `SERVER_PORT` | `8080` | HTTP port |
| `MEDIA_STORAGE_PATH` | `./data/media` | Where originals + renditions are stored |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:4321` | Origins allowed to call the admin API |

## What works today

| Endpoint | Status |
|---|---|
| `/actuator/health`, `/actuator/health/liveness`, `/actuator/health/readiness` | ✅ public (used by probes) |
| `/api/**`, `/admin/**` | not implemented yet (Phase 3–5 of `../ROADMAP.md`) |
| `/v3/api-docs`, `/swagger-ui/index.html` | 🔒 blocked by Spring Security's default chain until Phase 4 adds JWT |

`ddl-auto` is `validate` on purpose: **Flyway owns the schema**, Hibernate must never
create or alter tables.

## Spring Boot 4 naming notes

Boot 4 renamed several starters, which trips up older examples (and older AI-generated
code):

| Older name | Boot 4 name |
|---|---|
| `spring-boot-starter-web` | `spring-boot-starter-webmvc` |
| `spring-boot-starter-test` | per-starter `*-test` artifacts (e.g. `spring-boot-starter-webmvc-test`) |
| `org.testcontainers:postgresql` | `org.testcontainers:testcontainers-postgresql` |
| parent version `4.x.y.RELEASE` | `4.x.y` (no `.RELEASE` suffix) |

The last row is a real trap: Spring Initializr's metadata returns `4.1.1.RELEASE` as the
id, but Maven Central only has `4.1.1`.
