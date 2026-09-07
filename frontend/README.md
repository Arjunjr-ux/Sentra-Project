# Sentra — frontend

Vite + React SPA for the Sentra access-management console. See the root
[`README.md`](../README.md) for setup and
[`SENTRA_BUILD_SPEC.md`](../SENTRA_BUILD_SPEC.md) §8–§9 for architecture and the
UI design system.

```bash
npm install
cp .env.example .env.local     # VITE_API_URL -> backend (defaults to http://localhost:8000/api/v1)
npm run dev                     # http://localhost:5173
```

The app needs the Phase 1/2 Django API running on `http://localhost:8000`. Seed
it (`python manage.py migrate && python manage.py seed_demo`) and sign in with a
demo account:

| Account              | Role    | Password          |
| -------------------- | ------- | ----------------- |
| `admin@sentra.dev`   | Admin   | `Sentra!Demo2026` |
| `manager@sentra.dev` | Manager | `Sentra!Demo2026` |
| `viewer@sentra.dev`  | Viewer  | `Sentra!Demo2026` |

| Script                            | Purpose                      |
| --------------------------------- | ---------------------------- |
| `npm run dev`                     | dev server                   |
| `npm run build`                   | production bundle -> `dist/` |
| `npm run preview`                 | serve the built bundle       |
| `npm run lint`                    | ESLint                       |
| `npm run format` / `format:check` | Prettier                     |
| `npm test`                        | Vitest (single run)          |

## Structure

```
src/
├─ api/         axios instance (in-memory token, 401-retry interceptor) + endpoint fns
├─ auth/        AuthProvider, useAuth, <Can>, <ProtectedRoute>, <RequirePerm>
├─ components/  AppShell, DataTable, Modal, ToastProvider, chips/pills/icons
├─ pages/       Login, Signup, Dashboard, Users, Roles, AuditLog
└─ lib/         error + formatting helpers
```
