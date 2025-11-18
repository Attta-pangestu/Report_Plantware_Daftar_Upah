import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'
import { login as apiLogin } from '../services/authService'

// TESTING ONLY
const TEST_MODE = (import.meta.env.VITE_DEV_MODE === 'true') || (import.meta.env.DEV_MODE === 'true')

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const initialTestingToken = (TEST_MODE && typeof localStorage !== 'undefined') ? (localStorage.getItem('testing_token') || 'permanent-testing-token-2025-rebinmas-daftar-upah') : ''
  const [token, setToken] = useState(initialTestingToken)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(TEST_MODE) // Loading true in test mode initially
  const [error, setError] = useState('')

  // TESTING ONLY: Auto-login in testing mode
  useEffect(() => {
    if (TEST_MODE && !user) {
      (async () => {
        try {
          let t = initialTestingToken
          if (!t) {
            const r = await axios.get('/auth/test-token')
            t = r?.data?.access_token || 'permanent-testing-token'
            localStorage.setItem('testing_token', t)
          }
          const mockUser = {
            id: 1,
            username: 'admin',
            email: 'admin@payroll.com',
            full_name: 'Development Admin',
            role: 'admin',
            divisions: ['PG1A', 'PG1B', 'PG2A', 'PG2B', 'DME', 'ARA', 'ARB1', 'ARB2', 'INFRA', 'AREC', 'IJL', 'STF-OFFICE', 'SECURITY']
          }
          setToken(t)
          setUser(mockUser)
          setLoading(false)
          console.warn('[AuthContext] TESTING ONLY: Token injected and auto-login complete', { token: t, user: mockUser.username })
        } catch (e) {
          console.warn('[AuthContext] TESTING ONLY: Failed to pre-inject token, using fallback', e)
          // Fallback: set minimal token and user
          const fallbackToken = 'permanent-testing-token-2025-rebinmas-daftar-upah'
          const fallbackUser = {
            id: 1,
            username: 'admin',
            email: 'admin@payroll.com',
            full_name: 'Development Admin',
            role: 'admin',
            divisions: ['PG1A', 'PG1B', 'PG2A', 'PG2B', 'DME', 'ARA', 'ARB1', 'ARB2', 'INFRA', 'AREC', 'IJL', 'STF-OFFICE', 'SECURITY']
          }
          localStorage.setItem('testing_token', fallbackToken)
          setToken(fallbackToken)
          setUser(fallbackUser)
          setLoading(false)
        }
      })()
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

  // In test mode, consider authenticated if user is set (even without valid token)
  const isAuthenticated = TEST_MODE ? !!user : !!token
  return <AuthCtx.Provider value={{ token, isAuthenticated, user, login, loading, error }}>{children}</AuthCtx.Provider>
}

export function useAuth() {
  return useContext(AuthCtx)
}
