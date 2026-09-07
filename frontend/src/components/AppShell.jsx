import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { Avatar } from './Avatar'
import { roleLabel } from '../lib/format'
import { IconClipboard, IconDashboard, IconLogout, IconShield, IconUsers } from './icons'

function NavItem({ to, icon, label, end }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
    >
      {icon}
      {label}
    </NavLink>
  )
}

export function AppShell() {
  const { user, roles, logout, hasPerm } = useAuth()
  const navigate = useNavigate()

  const canSeeRoles = hasPerm('roles.view') || hasPerm('roles.manage')

  const onSignOut = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-mark">S</span>
          <span className="auth-wordmark">Sentra</span>
        </div>

        <nav>
          <NavItem to="/" end icon={<IconDashboard />} label="Dashboard" />
          <NavItem to="/users" icon={<IconUsers />} label="Users" />
          {canSeeRoles && <NavItem to="/roles" icon={<IconShield />} label="Roles & Permissions" />}
          {hasPerm('audit.view') && (
            <NavItem to="/audit" icon={<IconClipboard />} label="Audit Log" />
          )}
        </nav>

        <div className="sidebar-spacer" />

        <div className="user-card">
          <Avatar name={user?.full_name} email={user?.email} small />
          <div className="meta">
            <div className="name">{user?.full_name || user?.email}</div>
            <div className="role">{roleLabel(roles)}</div>
          </div>
          <button className="icon-btn" onClick={onSignOut} aria-label="Sign out" title="Sign out">
            <IconLogout />
          </button>
        </div>
      </aside>

      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
