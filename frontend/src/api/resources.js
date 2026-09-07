import { client } from './client'

/* ---- list + export helpers ---------------------------------------------- */

function stripPaging(params = {}) {
  const out = {}
  for (const [k, v] of Object.entries(params)) {
    if (k === 'page' || k === 'page_size') continue
    if (v !== '' && v != null) out[k] = v
  }
  return out
}

function filenameFromDisposition(header, fallback) {
  const match = /filename="?([^";]+)"?/.exec(header || '')
  return match ? match[1] : fallback
}

export async function downloadExport(path, params, fallbackName) {
  const res = await client.get(path, {
    params: stripPaging(params),
    responseType: 'blob',
  })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = filenameFromDisposition(res.headers['content-disposition'], fallbackName)
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

/* ---- users ------------------------------------------------------------- */

export const usersApi = {
  list: (params) => client.get('/users/', { params }).then((r) => r.data),
  create: (body) => client.post('/users/', body).then((r) => r.data),
  update: (id, body) => client.patch(`/users/${id}/`, body).then((r) => r.data),
  deactivate: (id) => client.delete(`/users/${id}/`),
  replaceRoles: (id, roleIds) =>
    client.put(`/users/${id}/roles/`, { role_ids: roleIds }).then((r) => r.data),
  export: (params) => downloadExport('/users/export/', params, 'users.xlsx'),
}

/* ---- roles ----------------------------------------------------------- */

export const rolesApi = {
  list: (params) =>
    client.get('/roles/', { params: { page_size: 100, ...params } }).then((r) => r.data),
  create: (body) => client.post('/roles/', body).then((r) => r.data),
  update: (id, body) => client.patch(`/roles/${id}/`, body).then((r) => r.data),
  remove: (id) => client.delete(`/roles/${id}/`),
  replacePermissions: (id, permissionIds) =>
    client.put(`/roles/${id}/permissions/`, { permission_ids: permissionIds }).then((r) => r.data),
  export: (params) => downloadExport('/roles/export/', params, 'roles.xlsx'),
}

/* ---- permissions (catalogue, unpaginated) -------------------------- */

export const permissionsApi = {
  list: () => client.get('/permissions/').then((r) => r.data),
}

/* ---- audit logs --------------------------------------------------- */

export const auditApi = {
  list: (params) => client.get('/audit-logs/', { params }).then((r) => r.data),
  export: (params) => downloadExport('/audit-logs/export/', params, 'audit-logs.xlsx'),
}
