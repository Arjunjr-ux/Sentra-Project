import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

vi.mock('../useAuth', () => ({ useAuth: vi.fn() }))

import { useAuth } from '../useAuth'
import { Can } from '../Can'

function mockPerms(list, { superuser = false } = {}) {
  useAuth.mockReturnValue({
    hasPerm: (c) => superuser || list.includes(c),
  })
}

describe('<Can>', () => {
  it('renders children when the permission is held', () => {
    mockPerms(['users.edit'])
    render(
      <Can perm="users.edit">
        <button>Edit</button>
      </Can>
    )
    expect(screen.getByRole('button', { name: 'Edit' })).toBeInTheDocument()
  })

  it('renders nothing when the permission is missing', () => {
    mockPerms(['users.view'])
    render(
      <Can perm="users.edit">
        <button>Edit</button>
      </Can>
    )
    expect(screen.queryByRole('button', { name: 'Edit' })).not.toBeInTheDocument()
  })

  it('renders the fallback when provided and permission is missing', () => {
    mockPerms([])
    render(
      <Can perm="roles.manage" fallback={<span>locked</span>}>
        <button>New role</button>
      </Can>
    )
    expect(screen.getByText('locked')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'New role' })).not.toBeInTheDocument()
  })

  it('always renders children for a superuser', () => {
    mockPerms([], { superuser: true })
    render(
      <Can perm="audit.view">
        <span>secret</span>
      </Can>
    )
    expect(screen.getByText('secret')).toBeInTheDocument()
  })
})
