import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import api, { setAccessToken } from '../services/api'

const AuthContext = createContext(null)

export const homeFor = (user) => (user?.role === 'customer' ? '/portal' : '/app')

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .post('/auth/refresh/')
      .then(({ data }) => {
        setAccessToken(data.access)
        return api.get('/auth/me/')
      })
      .then(({ data }) => setUser(data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email, password) => {
    const { data } = await api.post('/auth/login/', { email, password })
    setAccessToken(data.access)
    setUser(data.user)
    return data.user
  }, [])

  const logout = useCallback(async () => {
    await api.post('/auth/logout/').catch(() => {})
    setAccessToken(null)
    setUser(null)
  }, [])

  const value = useMemo(() => ({ user, loading, login, logout }), [user, loading, login, logout])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
