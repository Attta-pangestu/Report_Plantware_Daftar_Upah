import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'
import { login as apiLogin } from '../services/authService'

const TEST_MODE = (import.meta.env?.VITE_DEV_MODE === 'true') || (import.meta.env?.DEV_MODE === 'true')

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState('')
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(false) // Start with false, let auto-login handle loading state
  const [error, setError] = useState('')

  // Auto-login moved to LoginPage in test mode to show the login UI while submitting automatically

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

  const isAuthenticated = !!token
  return <AuthCtx.Provider value={{ token, isAuthenticated, user, login, loading, error }}>{children}</AuthCtx.Provider>
}

export function useAuth() {
  return useContext(AuthCtx)
}
