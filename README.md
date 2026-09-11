# Sentra

Access-management console. Administrators manage users, define roles, attach granular
permissions to roles, and assign roles to users. Every API endpoint enforces role-based
access control; every sensitive action is written to an append-only audit log.

- **Backend** — Django + DRF + SimpleJWT: custom user model, first-class Role / Permission /
  AuditLog tables, JWT auth (access token in memory, refresh token in an httpOnly cookie),
  filter / sort / server-side pagination and streamed `.xlsx` export on every list.
- **Frontend** — React + Vite SPA: protected routing, a `<Can>` permission gate, one shared
  data table for Users and Audit Log with all state in the URL, create/edit modals, toasts.

The [`docs/`](docs/) directory holds the original design document, brief deck, and
interactive prototype the build was based on.

## Live deployment

| | URL |
|---|---|
| Frontend | `https://<sentra-web>.onrender.com` |
| API | `https://<sentra-api>.onrender.com/api/v1` |
| Swagger UI | `https://<sentra-api>.onrender.com/api/v1/schema/swagger-ui/` |

> Replace the placeholders with the real service URLs after connecting the repo to Render.

**Render free-tier caveats:** the API web service sleeps after ~15 minutes idle, so the
first request after a cold start takes ~30 seconds to wake it up. Free PostgreSQL instances
also expire after a set period (~30 days) — if the API returns database errors long after
deploy, the database needs recreating.

## Architecture (§2)

```
┌─────────────────────┐   HTTPS/JSON    ┌──────────────────────────┐
│  React SPA (Vite)    │ ──────────────▶ │   Django + DRF           │
│  Render Static Site  │   Bearer JWT    │   Render Web Service     │
│  axios + interceptors│ ◀────────────── │   gunicorn + whitenoise  │
└─────────────────────┘                  └───────────┬──────────────┘
  access token in memory                              │ psycopg
  refresh token: httpOnly cookie              ┌────────▼──────────────┐
                                               │  PostgreSQL (Render)  │
                                               └────────────────────────┘
```

| Layer | Choice |
|---|---|
| Backend | Django 5.2 LTS + DRF 3.18 + SimpleJWT · Python 3.12 |
| Database | SQLite locally · PostgreSQL in deploy (via `DATABASE_URL`) |
| Frontend | React 19 + Vite 8 + React Router 7 + TanStack Query 5 + axios |
| Deploy | Render (web service + static site + Postgres) via [`render.yaml`](render.yaml) |

**Version note:** `SENTRA_BUILD_SPEC.md` §2 targets "Django 6.0 / Python 3.14", which did not
exist when the spec was written. Django 6.x now exists but is **not** an LTS, so this build
stays on the **Django 5.2 LTS** line. DRF 3.18 is the current stable release (the spec
mentions 3.16). Exact versions are pinned in
[`backend/requirements.txt`](backend/requirements.txt) /
[`backend/requirements-dev.txt`](backend/requirements-dev.txt) and
[`frontend/package.json`](frontend/package.json) + `package-lock.json`.

## Local setup

### Backend → http://localhost:8000

```bash
cd backend && python -m venv .venv && .venv/Scripts/activate   # source .venv/bin/activate on macOS/Linux
pip install -r requirements-dev.txt
cp .env.example .env
python manage.py migrate && python manage.py seed_demo
python manage.py runserver
```

### Frontend → http://localhost:5173

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Demo credentials

The `seed_demo` command creates a populated database — a demo admin, manager, and viewer
(plus sample users and audit entries). All demo accounts share one password.

| Account | Role | Password |
|---|---|---|
| `admin@sentra.dev` | Admin | `Sentra!Demo2026` |
| `manager@sentra.dev` | Manager | `Sentra!Demo2026` |
| `viewer@sentra.dev` | Viewer | `Sentra!Demo2026` |

`seed_demo` is idempotent and runs on every Render deploy, so the live app is always
populated.

## Repository layout

```
.
├─ backend/    Django project (config/) — apps: accounts, rbac, audit, common
├─ frontend/   Vite + React app
├─ docs/       Design_Doc.pdf, Team_Brief_Deck.pdf, Sentra_Prototype_standalone.html
├─ render.yaml Render blueprint (web service + static site + Postgres)
└─ .github/workflows/ci.yml
```

## Tooling

| | Backend | Frontend |
|---|---|---|
| Lint | `ruff check .` | `npm run lint` (ESLint) |
| Format | `black .` | `npm run format` (Prettier) |
| Test | `pytest` | `npm test` (Vitest) |
| Audit | `pip-audit` | `npm audit` |

CI (`.github/workflows/ci.yml`) runs lint + format check + tests on every push and pull
request, with an 80% coverage gate on the backend auth/RBAC code paths. Dependency audits
run non-fatally.

> **Windows note:** this machine's Application Control policy blocks the freshly installed
> console-script `.exe` shims in `backend/.venv/Scripts/` (e.g. `pytest.exe`, `black.exe`).
> Invoke them as modules instead — `python -m pytest`, `python -m black .`. `ruff` has no
> module entry point; it runs in CI (Linux).
