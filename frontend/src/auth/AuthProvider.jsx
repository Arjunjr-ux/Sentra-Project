import { useCallback, useEffect, useMemo, useState } from 'react'
import * as authApi from '../api/auth'
import { registerAuthFailureHandler, setAccessToken } from '../api/client'
import { AuthContext } from './context'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const applySession = useCallback(async (accessToken) => {
    setAccessToken(accessToken)
    const me = await authApi.getMe()
    setUser(me)
    return me
  }, [])

  const clearSession = useCallback(() => {
    setAccessToken(null)
    setUser(null)
  }, [])

  // On load: trade the httpOnly refresh cookie for an access token, if present.
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const token = await authApi.refresh()
        if (!cancelled) await applySession(token)
      } catch {
        if (!cancelled) clearSession()
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [applySession, clearSession])

  // A refresh that fails mid-session (interceptor) drops us back to logged-out.
  useEffect(() => {
    registerAuthFailureHandler(() => clearSession())
    return () => registerAuthFailureHandler(null)
  }, [clearSession])

  const login = useCallback(
    async (email, password) => {
      const token = await authApi.login(email, password)
      return applySession(token)
    },
    [applySession]
  )

  const signup = useCallback(
    async (payload) => {
      const token = await authApi.register(payload)
      return applySession(token)
    },
    [applySession]
  )

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      clearSession()
    }
  }, [clearSession])

  const refetchMe = useCallback(async () => {
    const me = await authApi.getMe()
    setUser(me)
    return me
  }, [])

  const permissions = useMemo(() => user?.permissions ?? [], [user])
  const roles = useMemo(() => user?.roles ?? [], [user])

  const hasPerm = useCallback(
    (codename) => !!user && (user.is_superuser || permissions.includes(codename)),
    [user, permissions]
  )

  const value = useMemo(
    () => ({
      user,
      roles,
      permissions,
      loading,
      login,
      signup,
      logout,
      refetchMe,
      hasPerm,
    }),
    [user, roles, permissions, loading, login, signup, logout, refetchMe, hasPerm]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
