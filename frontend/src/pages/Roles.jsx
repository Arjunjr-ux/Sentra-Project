import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../auth/useAuth'
import { Can } from '../auth/Can'
import { Skeleton } from '../components/Skeleton'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { IconCheck, IconPlus } from '../components/icons'
import { useToast } from '../components/useToast'
import { permissionsApi, rolesApi } from '../api/resources'
import { errorMessage } from '../lib/apiError'
import { RoleFormModal } from './roles/RoleFormModal'

const GROUP_ORDER = ['users', 'roles', 'permissions', 'audit']

function groupPermissions(catalogue) {
  const groups = {}
  for (const p of catalogue) {
    const prefix = p.codename.split('.')[0]
    ;(groups[prefix] ||= []).push(p)
  }
  const keys = [
    ...GROUP_ORDER.filter((k) => groups[k]),
    ...Object.keys(groups).filter((k) => !GROUP_ORDER.includes(k)),
  ]
  return keys.map((k) => ({
    key: k,
    items: groups[k].sort((a, b) => a.codename.localeCompare(b.codename)),
  }))
}

export function Roles() {
  const { hasPerm } = useAuth()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()

  const [modal, setModal] = useState(null) // {mode:'create'} | {mode:'edit', role}
  const [confirmDelete, setConfirmDelete] = useState(null)

  const rolesQuery = useQuery({ queryKey: ['roles', 'list'], queryFn: () => rolesApi.list() })
  const permsQuery = useQuery({ queryKey: ['permissions'], queryFn: () => permissionsApi.list() })

  const roles = rolesQuery.data?.results ?? []
  const catalogue = useMemo(() => permsQuery.data ?? [], [permsQuery.data])
  const groups = useMemo(() => groupPermissions(catalogue), [catalogue])
  const codeToId = useMemo(
    () => Object.fromEntries(catalogue.map((p) => [p.codename, p.id])),
    [catalogue]
  )

  const selectedId = searchParams.get('role')
  const selected = roles.find((r) => String(r.id) === selectedId) || roles[0] || null

  const selectRole = (id) => {
    const next = new URLSearchParams(searchParams)
    next.set('role', String(id))
    setSearchParams(next, { replace: true })
  }

  const canManage = hasPerm('roles.manage')
  const chipsEditable = canManage && selected && !selected.is_system

  const replacePerms = useMutation({
    mutationFn: ({ roleId, codenames }) =>
      rolesApi.replacePermissions(roleId, codenames.map((c) => codeToId[c]).filter(Boolean)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] })
      toast.success('Permissions updated')
    },
    onError: (err) => toast.error(errorMessage(err, 'Could not update permissions.')),
  })

  const removeRole = useMutation({
    mutationFn: (id) => rolesApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] })
      toast.success('Role deleted')
      setConfirmDelete(null)
      const next = new URLSearchParams(searchParams)
      next.delete('role')
      setSearchParams(next, { replace: true })
    },
    onError: (err) => {
      toast.error(errorMessage(err, 'Could not delete the role.'))
      setConfirmDelete(null)
    },
  })

  const togglePermission = (codename) => {
    if (!chipsEditable) return
    const current = new Set(selected.permissions)
    if (current.has(codename)) current.delete(codename)
    else current.add(codename)
    replacePerms.mutate({ roleId: selected.id, codenames: [...current] })
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Roles &amp; Permissions</h1>
          <p className="page-subtitle">
            Changes apply immediately and are written to the audit log
          </p>
        </div>
        <Can perm="roles.manage">
          <button className="btn btn-primary" onClick={() => setModal({ mode: 'create' })}>
            <IconPlus />
            New role
          </button>
        </Can>
      </div>

      <div className="roles-layout">
        <div className="card role-list">
          {rolesQuery.isLoading && (
            <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} height={44} />
              ))}
            </div>
          )}
          {roles.map((role) => (
            <div
              key={role.id}
              className={
                selected && role.id === selected.id ? 'role-list-item selected' : 'role-list-item'
              }
              onClick={() => selectRole(role.id)}
            >
              <div className="row">
                <span className="rl-name">{role.name}</span>
                <span className="rl-count">{role.permission_count} perms</span>
              </div>
              {role.description && <div className="rl-desc">{role.description}</div>}
            </div>
          ))}
        </div>

        <div className="card role-detail">
          {!selected && !rolesQuery.isLoading && <p>Select a role to view its permissions.</p>}

          {selected && (
            <>
              <div className="role-detail-head">
                <h2>{selected.name}</h2>
                {selected.is_system && <span className="locked-badge">System role — locked</span>}
                <span style={{ flex: 1 }} />
                {canManage && !selected.is_system && (
                  <>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => setModal({ mode: 'edit', role: selected })}
                    >
                      Rename
                    </button>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => setConfirmDelete(selected)}
                    >
                      Delete
                    </button>
                  </>
                )}
              </div>

              {selected.description && <p className="rd-desc">{selected.description}</p>}

              {permsQuery.isLoading && <Skeleton height={120} />}

              {groups.map((group) => (
                <div className="perm-group" key={group.key}>
                  <h3>{group.key}</h3>
                  <div className="perm-grid">
                    {group.items.map((perm) => {
                      const on = selected.permissions.includes(perm.codename)
                      const cls = ['perm-chip']
                      if (on) cls.push('on')
                      if (chipsEditable) cls.push('clickable')
                      else cls.push('readonly')
                      return (
                        <div
                          key={perm.codename}
                          className={cls.join(' ')}
                          onClick={() => togglePermission(perm.codename)}
                        >
                          <span className="perm-check">
                            {on && <IconCheck width={12} height={12} />}
                          </span>
                          <span>
                            <span className="code">{perm.codename}</span>
                            <span className="desc">{perm.description}</span>
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>

      {modal && (
        <RoleFormModal
          mode={modal.mode}
          role={modal.role}
          onClose={() => setModal(null)}
          onCreated={(role) => selectRole(role.id)}
        />
      )}

      {confirmDelete && (
        <ConfirmDialog
          title="Delete role"
          message={`Delete the "${confirmDelete.name}" role? Users assigned to it will lose its permissions.`}
          confirmLabel="Delete"
          danger
          onCancel={() => setConfirmDelete(null)}
          onConfirm={() => removeRole.mutateAsync(confirmDelete.id)}
        />
      )}
    </div>
  )
}
