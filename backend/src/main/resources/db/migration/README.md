# Flyway migrations

Migrations live here as `V<n>__<description>.sql` and are the single source of truth
for the database schema (Hibernate runs with `ddl-auto=validate`).

Naming: `V1__baseline.sql`, `V2__add_album_cover.sql`, …

The first migration is written in Phase 3 of ROADMAP.md.
