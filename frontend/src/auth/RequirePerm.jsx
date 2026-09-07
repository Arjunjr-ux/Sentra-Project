import { useAuth } from './useAuth'

/* Route-level permission gate — a 403 state, not just a hidden nav item
   (SENTRA_BUILD_SPEC.md §8). */
export function RequirePerm({ perm, children }) {
  const { hasPerm } = useAuth()

  if (!hasPerm(perm)) {
    return (
      <div className="full-center">
        <div className="card state-card">
          <h2>Access denied</h2>
          <p>
            You don&rsquo;t have permission to view this page. It requires{' '}
            <span className="mono">{perm}</span>.
          </p>
        </div>
      </div>
    )
  }

  return children
}
