import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'
import { login as apiLogin, getMe, getTestToken } from '../services/authService'

const TEST_MODE = (import.meta.env?.VITE_DEV_MODE === 'true') || (import.meta.env?.DEV_MODE === 'true')

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState('')
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(false) // Start with false, let auto-login handle loading state
  const [error, setError] = useState('')
  const [loginInProgress, setLoginInProgress] = useState(false) // Prevent multiple login attempts

  useEffect(() => {
    try {
      const t = document.cookie.split('; ').find(x => x.startsWith('auth_token='))
      const tok = t ? decodeURIComponent(t.split('=')[1]) : ''
      if (tok) {
        setToken(tok)
        axios.defaults.headers.common['Authorization'] = `Bearer ${tok}`
        ;(async () => {
          try {
            const u = await getMe(tok)
            setUser(u)
          } catch (e) {
            setError('Failed to restore session')
          }
        })()
      }
    } catch (_) {}
  }, [])

  // Auto-login moved to LoginPage in test mode to show the login UI while submitting automatically

  async function login(username, password) {
    // Prevent multiple simultaneous login attempts
    if (loginInProgress) {
      console.log('[Auth] Login already in progress, skipping duplicate request')
      return false
    }

    setLoading(true)
    setLoginInProgress(true)
    setError('')
    console.log('[Auth] Starting login process for username:', username)

    try {
      const res = await apiLogin(username, password)
      const tok = res?.access_token
      let usr = res?.user

      console.log('[Auth] Login API response received')

      if (!usr && tok) {
        try {
          console.log('[Auth] Fetching user details with token')
          usr = await getMe(tok)
        } catch (error) {
          console.error('[Auth] Failed to fetch user details:', error)
        }
      }

      if (tok && usr) {
        console.log('[Auth] Login successful, setting authentication state')
        setToken(tok)
        setUser(usr)
        try {
          const secure = typeof window !== 'undefined' && window.location && window.location.protocol === 'https:'
          const flags = `path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax` + (secure ? '; Secure' : '')
          document.cookie = `auth_token=${encodeURIComponent(tok)}; ${flags}`
          axios.defaults.headers.common['Authorization'] = `Bearer ${tok}`
        } catch (_) {}
        return true
      }
      throw new Error('Missing token or user')
    } catch (e) {
      console.error('[Auth] Primary login failed:', e.message)

      // Only try test token as fallback in test mode
      if (TEST_MODE) {
        try {
          console.log('[Auth] Attempting test token fallback')
          const t = await getTestToken()
          const tok = t?.access_token
          if (tok) {
            console.log('[Auth] Test token received, fetching user details')
            const usr = await getMe(tok)
            setToken(tok)
            setUser(usr)
            console.log('[Auth] Test token login successful')
            return true
          }
        } catch (fallbackError) {
          console.error('[Auth] Test token fallback failed:', fallbackError.message)
        }
      }

      setError('Login failed')
      return false
    } finally {
      setLoading(false)
      setLoginInProgress(false)
    }
  }

  const logout = () => {
    try {
      document.cookie = 'auth_token=; Max-Age=0; path=/'
      delete axios.defaults.headers.common['Authorization']
    } catch (_) {}
    setToken('')
    setUser(null)
  }

  const isAuthenticated = !!token
  return <AuthCtx.Provider value={{ token, isAuthenticated, user, login, logout, loading, error }}>{children}</AuthCtx.Provider>
}

export function useAuth() {
  return useContext(AuthCtx)
}
