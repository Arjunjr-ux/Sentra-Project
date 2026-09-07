import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Modal } from '../../components/Modal'
import { FormField } from '../../components/FormField'
import { usersApi } from '../../api/resources'
import { errorMessage, fieldErrors } from '../../lib/apiError'
import { useToast } from '../../components/useToast'

/* Create or edit a user. Roles are picked as toggleable pills and saved via the
   dedicated PUT /users/{id}/roles/ endpoint (SENTRA_BUILD_SPEC.md §4/§9). */
export function UserFormModal({ mode, user, allRoles, onClose }) {
  const editing = mode === 'edit'
  const toast = useToast()
  const queryClient = useQueryClient()

  const [fullName, setFullName] = useState(user?.full_name || '')
  const [email, setEmail] = useState(user?.email || '')
  const [password, setPassword] = useState('')
  const [roleIds, setRoleIds] = useState(new Set((user?.roles || []).map((r) => r.id)))
  const [banner, setBanner] = useState('')
  const [fields, setFields] = useState({})

  const toggleRole = (id) => {
    setRoleIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const mutation = useMutation({
    mutationFn: async () => {
      const ids = [...roleIds]
      if (editing) {
        await usersApi.update(user.id, { full_name: fullName, email })
        await usersApi.replaceRoles(user.id, ids)
      } else {
        const created = await usersApi.create({ full_name: fullName, email, password })
        if (ids.length) await usersApi.replaceRoles(created.id, ids)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      toast.success(editing ? 'User updated' : 'User created')
      onClose()
    },
    onError: (err) => {
      setFields(fieldErrors(err))
      setBanner(errorMessage(err, 'Could not save the user.'))
    },
  })

  return (
    <Modal
      title={editing ? 'Edit user' : 'Add user'}
      onClose={onClose}
      footer={
        <>
          <button className="btn btn-secondary" onClick={onClose} disabled={mutation.isPending}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
          >
            {mutation.isPending ? 'Saving…' : editing ? 'Save' : 'Create'}
          </button>
        </>
      }
    >
      {banner && <div className="error-banner">{banner}</div>}

      <FormField
        id="uf-name"
        label="Full name"
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
        error={fields.full_name}
      />
      <FormField
        id="uf-email"
        label="Email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={fields.email}
      />
      {!editing && (
        <FormField
          id="uf-password"
          label="Temporary password"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={fields.password}
        />
      )}

      <div className="field">
        <span className="field-label">Roles</span>
        <div className="pill-select">
          {allRoles.map((role) => (
            <button
              type="button"
              key={role.id}
              className={roleIds.has(role.id) ? 'pill on' : 'pill'}
              onClick={() => toggleRole(role.id)}
            >
              {role.name}
            </button>
          ))}
        </div>
      </div>
    </Modal>
  )
}
