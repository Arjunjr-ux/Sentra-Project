/* Turn an axios error from the Sentra API into a human string. The backend
   guarantees a stable `detail` key (SENTRA_BUILD_SPEC.md §4). */
export function errorMessage(err, fallback = 'Something went wrong.') {
  const data = err?.response?.data
  if (!data) return err?.message || fallback
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  const firstField = Object.keys(data).find((k) => k !== 'errors')
  if (firstField) {
    const v = data[firstField]
    return Array.isArray(v) ? `${firstField}: ${v[0]}` : `${firstField}: ${v}`
  }
  return fallback
}

/* Per-field errors for inline form display: { email: "…", password: "…" }. */
export function fieldErrors(err) {
  const data = err?.response?.data
  if (!data || typeof data !== 'object') return {}
  const out = {}
  for (const [k, v] of Object.entries(data)) {
    if (k === 'detail' || k === 'errors') continue
    out[k] = Array.isArray(v) ? v[0] : String(v)
  }
  return out
}
