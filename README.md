# Sentra

Access-management console — administrators manage users, define roles, attach granular
permissions to roles, and assign roles to users. Every API endpoint enforces role-based
access control; every sensitive action is written to an audit log.

> **Status:** Phase 0 — monorepo scaffold and tooling only. No application logic yet.
> See [`SENTRA_BUILD_SPEC.md`](SENTRA_BUILD_SPEC.md) for the full spec and
> [`CLAUDE_CODE_PROMPTS.md`](CLAUDE_CODE_PROMPTS.md) for the build phases.

## Stack

| Layer    | Choice |
|----------|--------|
| Backend  | Django 5.2 LTS + DRF 3.18 + SimpleJWT · Python 3.14 |
| Database | SQLite locally · PostgreSQL in deploy (via `DATABASE_URL`) |
| Frontend | React 19 + Vite 8 + React Router 7 + TanStack Query 5 + axios |
| Deploy   | Render (web service + static site + Postgres) — added in Phase 4 |

**Version note:** `SENTRA_BUILD_SPEC.md` §2 targets "Django 6.0 / Python 3.14", which did
not exist when the spec was written. Django 6.x now exists but is **not** an LTS, so this
build stays on the **Django 5.2 LTS** line per the Phase 0 prompt. DRF 3.18 is the current
stable release (the spec mentions 3.16). Exact versions are pinned in
[`backend/requirements.txt`](backend/requirements.txt) /
[`backend/requirements-dev.txt`](backend/requirements-dev.txt) and
[`frontend/package.json`](frontend/package.json) + `package-lock.json`.

## Repository layout

```
.
├─ backend/    Django project (config/) + virtualenv (.venv/, gitignored)
├─ frontend/   Vite + React app
├─ docs/       Design_Doc.pdf, Team_Brief_Deck.pdf, Sentra_Prototype_standalone.html
├─ .github/workflows/ci.yml   CI placeholder (filled in Phase 4)
├─ SENTRA_BUILD_SPEC.md
└─ CLAUDE_CODE_PROMPTS.md
```

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate            # Windows  •  source .venv/bin/activate on macOS/Linux
pip install -r requirements-dev.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver        # http://localhost:8000
```

- OpenAPI schema: `http://localhost:8000/api/v1/schema/`
- Swagger UI: `http://localhost:8000/api/v1/schema/swagger-ui/`

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev                       # http://localhost:5173
```

## Tooling

| | Backend | Frontend |
|---|---|---|
| Lint | `ruff check .` | `npm run lint` (ESLint) |
| Format | `black .` | `npm run format` (Prettier) |
| Test | `pytest` | `npm test` (Vitest) |
| Audit | `pip-audit` | `npm audit` |

> **Windows note:** this machine's Application Control policy blocks running the freshly
> installed console-script `.exe` shims in `backend/.venv/Scripts/` (e.g. `ruff.exe`,
> `pytest.exe`). Invoke the pure-Python tools as modules instead —
> `python -m pytest`, `python -m black .`, `python -m pip_audit`. `ruff` has no module
> entry point and only runs in CI (Linux) locally-blocked here; CI is unaffected.

## Demo credentials

Added in Phase 1 (seed command). The deployed URLs and Swagger link are added in Phase 4.
