import { createContext, useContext, useState, useEffect } from 'react'
import { login as apiLogin } from '../services/authService'

// Check if running in development mode
const DEV_MODE = import.meta.env.DEV_MODE === 'true'

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState('')
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Auto-login in development mode
  useEffect(() => {
    if (DEV_MODE && !token && !user) {
      console.log('[AuthContext] Development mode: Auto-logging in as admin')
      const mockUser = {
        id: 1,
        username: 'admin',
        email: 'admin@payroll.com',
        full_name: 'Development Admin',
        role: 'admin',
        divisions: ['PG1A', 'PG1B', 'PG2A', 'PG2B', 'DME', 'ARA', 'ARB1', 'ARB2', 'INFRA', 'AREC', 'IJL', 'STF-OFFICE', 'SECURITY']
      }
      setToken('dev-token')
      setUser(mockUser)
      console.log('[AuthContext] Development mode: Auto-login complete')
    }
  }, [])

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
