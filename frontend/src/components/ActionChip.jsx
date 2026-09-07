function category(action = '') {
  if (action.startsWith('auth.')) return 'auth'
  if (action.includes('export')) return 'export'
  if (action.startsWith('user.')) return 'user'
  if (action.startsWith('role.')) return 'role'
  return 'other'
}

export function ActionChip({ action }) {
  return <span className={`action-chip ${category(action)}`}>{action}</span>
}
