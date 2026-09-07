import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../../api/auth', () => ({
  refresh: vi.fn(),
  getMe: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
}))

import * as authApi from '../../api/auth'
import { AuthProvider } from '../AuthProvider'
import { useAuth } from '../useAuth'

const VIEWER = {
  id: 'u1',
  email: 'viewer@sentra.dev',
  full_name: 'Vera Viewer',
  is_superuser: false,
  roles: [{ id: 3, name: 'Viewer' }],
  permissions: ['permissions.view', 'roles.view', 'users.view'],
}

function Probe() {
  const { user, loading, permissions, roles, hasPerm, login, logout } = useAuth()
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="email">{user?.email ?? 'anon'}</span>
      <span data-testid="perms">{permissions.join(',')}</span>
      <span data-testid="roles">{roles.map((r) => r.name).join(',')}</span>
      <span data-testid="usersView">{String(hasPerm('users.view'))}</span>
      <span data-testid="auditView">{String(hasPerm('audit.view'))}</span>
      <button onClick={() => login('viewer@sentra.dev', 'pw')}>login</button>
      <button onClick={() => logout()}>logout</button>
    </div>
  )
}

const renderProbe = () =>
  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>
  )

beforeEach(() => {
  vi.clearAllMocks()
})
afterEach(() => {
  vi.resetAllMocks()
})

describe('useAuth', () => {
  it('bootstraps from the refresh cookie and exposes user, roles, permissions', async () => {
    authApi.refresh.mockResolvedValue('access-token')
    authApi.getMe.mockResolvedValue(VIEWER)

    renderProbe()

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'))
    expect(screen.getByTestId('email')).toHaveTextContent('viewer@sentra.dev')
    expect(screen.getByTestId('roles')).toHaveTextContent('Viewer')
    expect(screen.getByTestId('perms')).toHaveTextContent('permissions.view,roles.view,users.view')
    expect(screen.getByTestId('usersView')).toHaveTextContent('true')
    expect(screen.getByTestId('auditView')).toHaveTextContent('false')
  })

  it('ends logged-out when there is no valid refresh cookie', async () => {
    authApi.refresh.mockRejectedValue(new Error('401'))

    renderProbe()

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'))
    expect(screen.getByTestId('email')).toHaveTextContent('anon')
    expect(authApi.getMe).not.toHaveBeenCalled()
  })

  it('login() populates the session', async () => {
    authApi.refresh.mockRejectedValue(new Error('401'))
    authApi.login.mockResolvedValue('fresh-token')
    authApi.getMe.mockResolvedValue(VIEWER)

    renderProbe()
    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'))

    await userEvent.click(screen.getByText('login'))

    await waitFor(() => expect(screen.getByTestId('email')).toHaveTextContent('viewer@sentra.dev'))
    expect(authApi.login).toHaveBeenCalledWith('viewer@sentra.dev', 'pw')
  })

  it('logout() clears the session', async () => {
    authApi.refresh.mockResolvedValue('access-token')
    authApi.getMe.mockResolvedValue(VIEWER)
    authApi.logout.mockResolvedValue(undefined)

    renderProbe()
    await waitFor(() => expect(screen.getByTestId('email')).toHaveTextContent('viewer@sentra.dev'))

    await userEvent.click(screen.getByText('logout'))

    await waitFor(() => expect(screen.getByTestId('email')).toHaveTextContent('anon'))
    expect(authApi.logout).toHaveBeenCalled()
  })

  it('hasPerm() is always true for a superuser', async () => {
    authApi.refresh.mockResolvedValue('access-token')
    authApi.getMe.mockResolvedValue({ ...VIEWER, is_superuser: true, permissions: [] })

    renderProbe()

    await waitFor(() => expect(screen.getByTestId('auditView')).toHaveTextContent('true'))
  })
})
