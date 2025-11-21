import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'
import { login as apiLogin, getMe, getTestToken } from '../services/authService'
import cookieService from '../services/cookieService'

const TEST_MODE = (import.meta.env?.VITE_DEV_MODE === 'true') || (import.meta.env?.DEV_MODE === 'true')

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState('')
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(false) // Start with false, let auto-login handle loading state
  const [error, setError] = useState('')
  const [loginInProgress, setLoginInProgress] = useState(false) // Prevent multiple login attempts

  useEffect(() => {
    // Restore authentication from cookies on app load
    try {
      console.log('[AuthContext] Checking for saved authentication in cookies')
      const savedToken = cookieService.getToken()
      const savedUser = cookieService.getUser()

      if (savedToken && savedUser) {
        console.log('[AuthContext] Restoring authentication from cookies')
        setToken(savedToken)
        setUser(savedUser)
        axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`
      } else {
        console.log('[AuthContext] No saved authentication found')
        // Clear any inconsistent auth data
        cookieService.clearAuth()
      }
    } catch (error) {
      console.error('[AuthContext] Error restoring authentication:', error)
      cookieService.clearAuth()
    }
  }, [])

  // Auto-login moved to LoginPage in test mode to show the login UI while submitting automatically

  async function login(username, password, rememberMe = true) {
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
          // Save token and user info using cookieService
          cookieService.saveToken(tok, rememberMe)
          cookieService.saveUser(usr)
          cookieService.saveRememberMe(rememberMe)
          axios.defaults.headers.common['Authorization'] = `Bearer ${tok}`
          console.log('[Auth] Authentication saved to cookies successfully (rememberMe:', rememberMe, ')')
        } catch (error) {
          console.error('[Auth] Failed to save authentication to cookies:', error)
        }
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
            try {
              // Save test token and user info using cookieService
              cookieService.saveToken(tok, true) // Remember me for test mode
              cookieService.saveUser(usr)
              axios.defaults.headers.common['Authorization'] = `Bearer ${tok}`
              console.log('[Auth] Test token authentication saved to cookies')
            } catch (error) {
              console.error('[Auth] Failed to save test authentication to cookies:', error)
            }
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
      // Clear all authentication data using cookieService
      cookieService.clearAuth()
      delete axios.defaults.headers.common['Authorization']
      console.log('[Auth] Logged out successfully, authentication data cleared')
    } catch (error) {
      console.error('[Auth] Error during logout:', error)
      // Fallback manual cleanup
      try {
        document.cookie = 'auth_token=; Max-Age=0; path=/'
        document.cookie = 'payroll_user_info=; Max-Age=0; path=/'
        localStorage.removeItem('payroll_remember_me')
      } catch (_) {}
    }
    setToken('')
    setUser(null)
  }

  const isAuthenticated = !!token
  return <AuthCtx.Provider value={{ token, isAuthenticated, user, login, logout, loading, error }}>{children}</AuthCtx.Provider>
}

export function useAuth() {
  return useContext(AuthCtx)
}
