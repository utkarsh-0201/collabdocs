# CollabDocs

CollabDocs is a Django-based collaboration platform for documents, workspaces, comments, tags, and audit logs.

## Project Overview

CollabDocs is the backend API for a platform where users can create workspaces, invite collaborators, write and version documents, leave comments, and control access with role-based permissions. Think of it as a simplified Notion or Google Docs — API-only.

**Core capabilities (planned/in progress):**
- **Workspaces** — team spaces that group related documents and members
- **Role-based access** — workspace members are assigned `admin`, `editor`, or `viewer` roles that govern what they can do
- **Documents** — created within a workspace, with draft/published/archived status
- **Versioning** — every document save is snapshotted, so history can be reviewed or restored
- **Comments** — threaded discussion on documents, including nested replies
- **Tags** — many-to-many labeling for organizing and filtering documents
- **Audit logging** — automatic tracking of who did what, and when, across the platform

## What is included

- Django 6.1 project with apps: `accounts`, `workspaces`, `documents`, `comments`, `tags`, `audit`
- PostgreSQL database configuration
- Initial model schema ready for migration
- REST framework dependency included for future API work

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | Django 6.1 |
| API | Django REST Framework |
| Database | PostgreSQL 16 (Dockerized) |
| Config | `python-dotenv` / `.env`-based settings |

## App Structure

| App | Owns | Depends on |
|---|---|---|
| `accounts` | `User` | — |
| `workspaces` | `Workspace`, `WorkspaceMember` | `accounts` |
| `documents` | `Document`, `DocumentVersion` | `accounts`, `workspaces` |
| `comments` | `Comment` | `accounts`, `documents` |
| `tags` | `Tag` | `documents` |
| `audit` | `AuditLog` | `accounts` |

Each app is scoped to one collaborator or sub-team to minimize merge conflicts. See [Notes for collaborators](#notes-for-collaborators) below for the recommended workflow.

## Prerequisites

- Python 3.12
- PostgreSQL server (or Docker, see below)
- `pip` package manager
- Docker (optional, for running PostgreSQL in a container)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/utkarsh-0201/collabdocs
cd collabdocs
```

2. Create and activate a virtual environment:
```bash
python3 -m venv collab_docs_env
source collab_docs_env/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the example environment file and update values:
```bash
cp .env.example .env
```

Then edit `.env` and provide your local PostgreSQL credentials:
- `POSTGRES_DB` or `DB_NAME`
- `POSTGRES_USER` or `DB_USER`
- `POSTGRES_PASSWORD` or `DB_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

The settings file supports both `POSTGRES_*` and `DB_*` environment variables for compatibility.

> ⚠️ Never commit your `.env` file — it contains real local credentials. Only `.env.example` (with placeholder values) should be tracked in git.

## Running migrations

Generate and apply migrations to build the schema:
```bash
python manage.py makemigrations
python manage.py migrate
```

If you are starting from a fresh clone and the app models have not yet been migrated, the above commands will create the initial migration files and apply them.

## Running the development server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

## PostgreSQL Docker setup

Build the PostgreSQL image and run the database container:
```bash
docker build -t collabdocs-postgres .
docker run -d \
  --name collabdocs_postgres \
  --env-file .env \
  -p 5432:5432 \
  -v collabdocs_pgdata:/var/lib/postgresql/data \
  collabdocs-postgres
```

Verify the container is running and connect via `psql`:
```bash
docker ps
docker exec -it collabdocs_postgres psql -U <your_db_user> -d <your_db_name>
```

Stop or reset the database:
```bash
docker stop collabdocs_postgres          # stop container, keep data
docker rm -f collabdocs_postgres         # remove container, keep volume
docker volume rm collabdocs_pgdata       # wipe all data (fresh start)
```

## Notes for collaborators

- Do not commit `.env`; it contains local credentials.
- The project settings file loads environment variables from `.env` using `python-dotenv`.
- Database configuration is in `config/settings.py`.
- The schema is defined within each app's `models.py`.
- **Own your app.** Each collaborator should primarily work within their assigned app (see [App Structure](#app-structure)) to reduce merge conflicts.
- **Branching.** Create a feature branch per change, e.g. `feature/<app-name>-<short-description>`, and open a PR into `main` rather than committing directly.
- **Migrations.** Run `makemigrations <app_name>` scoped to your own app. If you hit a migration numbering conflict after pulling `main`, delete your unmerged migration and regenerate it — never hand-edit migration numbers.
- **Commit migration files.** Migrations are part of the source code and must be committed, not gitignored.

## API overview

The project exposes REST endpoints under the `/api/` prefix.

### Workspaces
- `GET /api/workspaces/` — list workspaces
- `POST /api/workspaces/` — create a workspace
- `GET /api/workspaces/<id>/` — workspace detail
- `GET /api/workspaces/<id>/members/` — list workspace members
- `POST /api/workspaces/<id>/members/` — add a member
- `GET /api/workspaces/<id>/summary/` — workspace summary counts

### Documents
- `GET /api/documents/` — list/filter documents
- `POST /api/documents/` — create a document with initial version
- `GET /api/documents/<id>/` — document detail
- `PUT /api/documents/<id>/` — update document and append a new version
- `GET /api/documents/<id>/versions/` — list document versions
- `GET /api/documents/<id>/stats/` — version/comment/contributor statistics
- `POST /api/documents/<id>/tags/` — attach tags to a document

### Comments
- `GET /api/comments/` — list threaded comments for a document
- `POST /api/comments/` — create a top-level comment or reply

### Tags
- `POST /api/tags/` — create a tag

### Audit logs
- `GET /api/audit-logs/` — list audit entries with actor/date filtering

### Request logging middleware
The project includes a custom request logger in `config/middleware.py`, registered in `config/settings.py`.
It prints one line per request with:
- HTTP method
- request path
- response status code
- elapsed time in milliseconds

Example:

```text
METHOD: GET | PATH: /api/workspaces/ | STATUS: 200 | TIME: 12.34 ms
```

## Useful commands

```bash
python manage.py showmigrations
python manage.py sqlmigrate accounts 0001
python manage.py createsuperuser
```

## Roadmap

- [ ] DRF serializers and viewsets for all models
- [ ] Role-based permission classes (admin / editor / viewer)
- [ ] Document versioning logic (atomic save + version snapshot)
- [ ] Threaded comment API
- [ ] Tag filtering endpoints
- [ ] Automatic audit logging via signals
- [ ] Authentication (token/session)
- [ ] API documentation (e.g. drf-spectacular / Swagger)
