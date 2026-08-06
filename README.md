# CollabDocs

CollabDocs is a Django-based collaboration platform skeleton for documents, workspaces, comments, tags, and audit logs.

## What is included

- Django 6.1 project with apps: `accounts`, `workspaces`, `documents`, `comments`, `tags`, `audit`
- PostgreSQL database configuration
- Initial model schema ready for migration
- REST framework dependency included for future API work

## Prerequisites

- Python 3.12
- PostgreSQL server
- `pip` package manager

## Setup

1. Clone the repository:

```bash
git clone <repo-url>
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

5. Create the PostgreSQL database and user if needed.

Example commands:

```bash
sudo -u postgres psql
CREATE DATABASE collabdocs;
CREATE USER collabdocs_admin WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE collabdocs TO collabdocs_admin;
\q
```

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

## Notes for collaborators

- Do not commit `.env`; it contains local credentials.
- The project settings file loads environment variables from `.env` using `python-dotenv`.
- Database configuration is in `config/settings.py`.
- The schema is defined within each app's `models.py`.

## Useful commands

```bash
python manage.py showmigrations
python manage.py sqlmigrate accounts 0001
python manage.py createsuperuser
```
