import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../auth/useAuth'
import { Can } from '../auth/Can'
import { DataTable } from '../components/DataTable'
import { Avatar } from '../components/Avatar'
import { RoleChips } from '../components/RoleChip'
import { StatusPill } from '../components/StatusPill'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { IconPlus } from '../components/icons'
import { useToast } from '../components/useToast'
import { usersApi, rolesApi } from '../api/resources'
import { errorMessage } from '../lib/apiError'
import { formatTimestamp } from '../lib/format'
import { UserFormModal } from './users/UserFormModal'

export function Users() {
  const { hasPerm } = useAuth()
  const toast = useToast()
  const queryClient = useQueryClient()

  const [modal, setModal] = useState(null) // {mode:'create'} | {mode:'edit', user}
  const [confirmUser, setConfirmUser] = useState(null)

  const rolesQuery = useQuery({ queryKey: ['roles', 'all'], queryFn: () => rolesApi.list() })
  const allRoles = rolesQuery.data?.results ?? []

  const countQuery = useQuery({
    queryKey: ['users', 'count'],
    queryFn: () => usersApi.list({ page_size: 1 }),
  })

  const setActive = useMutation({
    mutationFn: ({ id, active }) =>
      active ? usersApi.update(id, { is_active: true }) : usersApi.deactivate(id),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      toast.success(vars.active ? 'User activated' : 'User deactivated')
      setConfirmUser(null)
    },
    onError: (err) => {
      toast.error(errorMessage(err, 'Could not update the user.'))
      setConfirmUser(null)
    },
  })

  const columns = [
    {
      key: 'user',
      header: 'User',
      sortKey: 'full_name',
      render: (u) => (
        <div className="cell-user">
          <Avatar name={u.full_name} email={u.email} />
          <div>
            <div className="name">{u.full_name || '—'}</div>
            <div className="email">{u.email}</div>
          </div>
        </div>
      ),
    },
    { key: 'roles', header: 'Roles', render: (u) => <RoleChips roles={u.roles} /> },
    { key: 'status', header: 'Status', render: (u) => <StatusPill active={u.is_active} /> },
    {
      key: 'last_login',
      header: 'Last login',
      sortKey: 'last_login',
      cellClass: 'mono',
      render: (u) => formatTimestamp(u.last_login),
    },
  ]

  const filters = [
    {
      key: 'role',
      label: 'Role',
      options: [
        { value: '', label: 'All roles' },
        ...allRoles.map((r) => ({ value: String(r.id), label: r.name })),
      ],
    },
    {
      key: 'is_active',
      label: 'Status',
      options: [
        { value: '', label: 'All statuses' },
        { value: 'true', label: 'Active' },
        { value: 'false', label: 'Inactive' },
      ],
    },
  ]

  const rowActions = (u) => (
    <>
      <Can perm="users.edit">
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => setModal({ mode: 'edit', user: u })}
        >
          Edit
        </button>
      </Can>
      <Can perm="users.delete">
        {u.is_active ? (
          <button className="btn btn-secondary btn-sm" onClick={() => setConfirmUser(u)}>
            Deactivate
          </button>
        ) : (
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setActive.mutate({ id: u.id, active: true })}
          >
            Activate
          </button>
        )}
      </Can>
    </>
  )

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Users</h1>
          <p className="page-subtitle">{countQuery.data?.count ?? 0} users</p>
        </div>
        <Can perm="users.create">
          <button className="btn btn-primary" onClick={() => setModal({ mode: 'create' })}>
            <IconPlus />
            Add user
          </button>
        </Can>
      </div>

      <DataTable
        queryKey={['users']}
        fetcher={(params) => usersApi.list(params)}
        columns={columns}
        filters={filters}
        searchable
        searchPlaceholder="Search by name or email…"
        exportFn={(params) => usersApi.export(params)}
        rowActions={hasPerm('users.edit') || hasPerm('users.delete') ? rowActions : undefined}
        emptyTitle="No users match your filters"
        emptyAction={
          <Can perm="users.create">
            <button
              className="btn btn-primary btn-sm"
              onClick={() => setModal({ mode: 'create' })}
              style={{ marginTop: 12 }}
            >
              Add the first user
            </button>
          </Can>
        }
      />

      {modal && (
        <UserFormModal
          mode={modal.mode}
          user={modal.user}
          allRoles={allRoles}
          onClose={() => setModal(null)}
        />
      )}

      {confirmUser && (
        <ConfirmDialog
          title="Deactivate user"
          message={`Deactivate ${confirmUser.full_name || confirmUser.email}? They will lose access until reactivated.`}
          confirmLabel="Deactivate"
          danger
          onCancel={() => setConfirmUser(null)}
          onConfirm={() => setActive.mutateAsync({ id: confirmUser.id, active: false })}
        />
      )}
    </div>
  )
}
