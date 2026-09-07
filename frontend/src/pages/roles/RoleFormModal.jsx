import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Modal } from '../../components/Modal'
import { FormField } from '../../components/FormField'
import { rolesApi } from '../../api/resources'
import { errorMessage, fieldErrors } from '../../lib/apiError'
import { useToast } from '../../components/useToast'

export function RoleFormModal({ mode, role, onClose, onCreated }) {
  const editing = mode === 'edit'
  const toast = useToast()
  const queryClient = useQueryClient()

  const [name, setName] = useState(role?.name || '')
  const [description, setDescription] = useState(role?.description || '')
  const [banner, setBanner] = useState('')
  const [fields, setFields] = useState({})

  const mutation = useMutation({
    mutationFn: () =>
      editing
        ? rolesApi.update(role.id, { name, description })
        : rolesApi.create({ name, description }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['roles'] })
      toast.success(editing ? 'Role updated' : 'Role created')
      if (!editing && onCreated) onCreated(data)
      onClose()
    },
    onError: (err) => {
      setFields(fieldErrors(err))
      setBanner(errorMessage(err, 'Could not save the role.'))
    },
  })

  return (
    <Modal
      title={editing ? 'Rename role' : 'New role'}
      onClose={onClose}
      footer={
        <>
          <button className="btn btn-secondary" onClick={onClose} disabled={mutation.isPending}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !name.trim()}
          >
            {mutation.isPending ? 'Saving…' : editing ? 'Save' : 'Create'}
          </button>
        </>
      }
    >
      {banner && <div className="error-banner">{banner}</div>}
      <FormField
        id="rf-name"
        label="Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        error={fields.name}
      />
      <FormField
        id="rf-desc"
        label="Description"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        error={fields.description}
      />
    </Modal>
  )
}
