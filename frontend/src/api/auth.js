import { client, rawRefresh } from './client'

export async function login(email, password) {
  const { data } = await client.post('/auth/login/', { email, password })
  return data.access
}

export async function register({ email, full_name, password }) {
  const { data } = await client.post('/auth/register/', { email, full_name, password })
  return data.access
}

export async function logout() {
  await client.post('/auth/logout/', {})
}

export async function getMe() {
  const { data } = await client.get('/auth/me/')
  return data
}

/* Used once on app load to trade the httpOnly refresh cookie for an access
   token, so a page reload keeps the session. */
export async function refresh() {
  return rawRefresh()
}
