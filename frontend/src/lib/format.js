export function formatTimestamp(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function roleLabel(roles) {
  if (!roles || roles.length === 0) return 'no role'
  return roles.map((r) => r.name).join(', ')
}

export function initials(nameOrEmail = '') {
  const source = (nameOrEmail || '').trim()
  if (!source) return '?'
  if (source.includes('@')) return source[0].toUpperCase()
  const parts = source.split(/\s+/).filter(Boolean)
  const chars = parts.length > 1 ? parts[0][0] + parts[parts.length - 1][0] : parts[0].slice(0, 2)
  return chars.toUpperCase()
}
