import { createContext, useContext, useState } from 'react'
import { login as apiLogin } from '../services/authService'

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState('')
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function login(username, password) {
    setLoading(true); setError('')
    try {
      const res = await apiLogin(username, password)
      setToken(res.access_token)
      setUser(res.user)
      return true
    } catch (e) {
      setError('Login failed')
      return false
    } finally {
      setLoading(false)
    }
  }

  return <AuthCtx.Provider value={{ token, isAuthenticated: !!token, user, login, loading, error }}>{children}</AuthCtx.Provider>
}

export function useAuth() {
  return useContext(AuthCtx)
}
