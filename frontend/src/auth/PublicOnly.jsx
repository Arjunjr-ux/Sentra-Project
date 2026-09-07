import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from './useAuth'

/* /login and /signup: bounce to the dashboard if already signed in. */
export function PublicOnly() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="full-center">
        <div className="spinner" role="status" aria-label="Loading" />
      </div>
    )
  }

  return user ? <Navigate to="/" replace /> : <Outlet />
}
