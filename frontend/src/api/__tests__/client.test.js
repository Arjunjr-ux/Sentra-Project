import axios from 'axios'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { client, registerAuthFailureHandler, setAccessToken } from '../client'

/* Drive the interceptor with a stub adapter shared by `client` and the bare
   axios call `rawRefresh` uses. */
let refreshCalls = 0
let refreshSucceeds = true

function reject(status, config) {
  const err = new Error(`HTTP ${status}`)
  err.config = config
  err.response = { status, data: {} }
  return Promise.reject(err)
}

function stubAdapter(config) {
  const url = config.url || ''
  if (url.includes('/auth/refresh/')) {
    refreshCalls += 1
    return refreshSucceeds
      ? Promise.resolve({ data: { access: 'newtok' }, status: 200, headers: {}, config })
      : reject(401, config)
  }
  if (config.headers?.Authorization === 'Bearer newtok') {
    return Promise.resolve({ data: { ok: true }, status: 200, headers: {}, config })
  }
  return reject(401, config)
}

const originalClientAdapter = client.defaults.adapter
const originalAxiosAdapter = axios.defaults.adapter

beforeEach(() => {
  refreshCalls = 0
  refreshSucceeds = true
  setAccessToken(null)
  registerAuthFailureHandler(null)
  client.defaults.adapter = stubAdapter
  axios.defaults.adapter = stubAdapter
})

afterEach(() => {
  client.defaults.adapter = originalClientAdapter
  axios.defaults.adapter = originalAxiosAdapter
})

describe('api client 401 handling', () => {
  it('refreshes once and replays the original request', async () => {
    const res = await client.get('/widgets/')
    expect(res.data).toEqual({ ok: true })
    expect(refreshCalls).toBe(1)
  })

  it('calls the auth-failure handler when the refresh also fails', async () => {
    refreshSucceeds = false
    const onFail = vi.fn()
    registerAuthFailureHandler(onFail)

    await expect(client.get('/widgets/')).rejects.toBeTruthy()
    expect(onFail).toHaveBeenCalledTimes(1)
  })

  it('dedupes concurrent 401s into a single refresh', async () => {
    const results = await Promise.all([client.get('/a/'), client.get('/b/'), client.get('/c/')])
    expect(results.every((r) => r.data.ok)).toBe(true)
    expect(refreshCalls).toBe(1)
  })

  it('does not retry a failed login', async () => {
    await expect(client.post('/auth/login/', {})).rejects.toBeTruthy()
    expect(refreshCalls).toBe(0)
  })
})
