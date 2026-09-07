export function StatusPill({ active }) {
  return (
    <span className={active ? 'status active' : 'status inactive'}>
      <span className="dot" />
      {active ? 'Active' : 'Inactive'}
    </span>
  )
}
