# db

## Purpose

This folder contains database-related assets for the Graduate Applicant System.

Its role is to support local development and backend persistence by defining:
- database initialization
- schema creation
- seed or bootstrap data
- future migrations or database setup helpers

The `db/` folder exists to support the application's persistence layer. It should not contain application business logic or MCP tool logic.

---

## What belongs here

Examples of things that belong in this folder:

- SQL files for initializing the database
- schema creation scripts
- seed data scripts or seed SQL
- migration files
- local development database setup assets
- reference database diagrams or notes tied directly to schema setup

Example future structure:

```text
db/
├─ init/
│  └─ 001_schema.sql
├─ seed/
│  └─ 001_seed_dev.sql
└─ migrations/