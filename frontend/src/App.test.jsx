import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'

vi.mock('./auth/useAuth', () => ({
  useAuth: () => ({
    user: null,
    loading: false,
    roles: [],
    permissions: [],
    hasPerm: () => false,
    login: vi.fn(),
    signup: vi.fn(),
    logout: vi.fn(),
  }),
}))

import App from './App.jsx'

describe('App routing', () => {
  it('shows the Login page for an unauthenticated visit to /login', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>
    )
    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('redirects an unauthenticated visit to a protected route back to /login', () => {
    render(
      <MemoryRouter initialEntries={['/users']}>
        <App />
      </MemoryRouter>
    )
    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
  })
})
