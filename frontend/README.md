# Sentra — frontend

Vite + React SPA for the Sentra access-management console. See the root
[`README.md`](../README.md) for setup and the [`SENTRA_BUILD_SPEC.md`](../SENTRA_BUILD_SPEC.md)
§8–§9 for architecture and the UI design system.

```bash
npm install
cp .env.example .env.local     # VITE_API_URL -> backend
npm run dev                     # http://localhost:5173
```

| Script | Purpose |
|---|---|
| `npm run dev` | dev server |
| `npm run build` | production bundle -> `dist/` |
| `npm run preview` | serve the built bundle |
| `npm run lint` | ESLint |
| `npm run format` / `format:check` | Prettier |
| `npm test` | Vitest (single run) |
