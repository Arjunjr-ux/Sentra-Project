import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { PublicOnly } from './auth/PublicOnly'
import { RequirePerm } from './auth/RequirePerm'
import { AppShell } from './components/AppShell'
import { Login } from './pages/Login'
import { Signup } from './pages/Signup'
import { Dashboard } from './pages/Dashboard'
import { Users } from './pages/Users'
import { Roles } from './pages/Roles'
import { AuditLog } from './pages/AuditLog'

export default function App() {
  return (
    <Routes>
      <Route element={<PublicOnly />}>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/users" element={<Users />} />
          <Route
            path="/roles"
            element={
              <RequirePerm perm="roles.view">
                <Roles />
              </RequirePerm>
            }
          />
          <Route
            path="/audit"
            element={
              <RequirePerm perm="audit.view">
                <AuditLog />
              </RequirePerm>
            }
          />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
