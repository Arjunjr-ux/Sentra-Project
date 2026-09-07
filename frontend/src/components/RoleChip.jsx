export function RoleChip({ name }) {
  return <span className="role-chip">{name}</span>
}

export function RoleChips({ roles }) {
  if (!roles || roles.length === 0) {
    return <span style={{ color: 'var(--text-muted)' }}>—</span>
  }
  return (
    <span className="chip-row">
      {roles.map((r) => (
        <RoleChip key={r.id ?? r.name} name={r.name} />
      ))}
    </span>
  )
}
