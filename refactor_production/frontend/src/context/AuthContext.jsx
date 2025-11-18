import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'
import { login as apiLogin } from '../services/authService'

// TESTING ONLY - Force development mode for testing
const TEST_MODE = true

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const initialTestingToken = (TEST_MODE && typeof localStorage !== 'undefined') ? (localStorage.getItem('testing_token') || 'permanent-testing-token-2025-rebinmas-daftar-upah') : ''
  const [token, setToken] = useState(initialTestingToken)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(false) // Start with false, let auto-login handle loading state
  const [error, setError] = useState('')

  // TESTING ONLY: Auto-login in testing mode using actual login request
  useEffect(() => {
    if (TEST_MODE && !user && !loading) {
      (async () => {
        try {
          console.warn('[AuthContext] TESTING ONLY: Attempting auto-login with credentials')
          // Use actual login API with hardcoded credentials
          const success = await login('admin', 'admin')
          if (success) {
            console.warn('[AuthContext] TESTING ONLY: Auto-login successful')
          } else {
            console.warn('[AuthContext] TESTING ONLY: Auto-login failed, using fallback user')
            // Fallback: set mock user directly if login fails
            const fallbackUser = {
              id: 1,
              username: 'admin',
              email: 'admin@payroll.com',
              full_name: 'Development Admin',
              role: 'admin',
              divisions: ['PG1A', 'PG1B', 'PG2A', 'PG2B', 'DME', 'ARA', 'ARB1', 'ARB2', 'INFRA', 'AREC', 'IJL', 'STF-OFFICE', 'SECURITY']
            }
            setUser(fallbackUser)
            setToken('dev-mode-token')
            setLoading(false)
          }
        } catch (e) {
          console.warn('[AuthContext] TESTING ONLY: Auto-login error, using fallback', e)
          // Fallback: set mock user directly on error
          const fallbackUser = {
            id: 1,
            username: 'admin',
            email: 'admin@payroll.com',
            full_name: 'Development Admin',
            role: 'admin',
            divisions: ['PG1A', 'PG1B', 'PG2A', 'PG2B', 'DME', 'ARA', 'ARB1', 'ARB2', 'INFRA', 'AREC', 'IJL', 'STF-OFFICE', 'SECURITY']
          }
          setUser(fallbackUser)
          setToken('dev-mode-token')
          setLoading(false)
        }
      })()
    }
  }, [user, loading])

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
