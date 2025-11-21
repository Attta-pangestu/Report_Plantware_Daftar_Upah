// Cookie Service untuk menyimpan informasi login dan session
import Cookies from 'js-cookie'

const TOKEN_KEY = 'payroll_auth_token'
const USER_KEY = 'payroll_user_info'
const REMEMBER_KEY = 'payroll_remember_me'

// Cookie options
const COOKIE_OPTIONS = {
  expires: 7, // 7 hari
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'strict',
  path: '/'
}

export const cookieService = {
  // Save authentication token
  saveToken: (token, rememberMe = false) => {
    try {
      const options = { ...COOKIE_OPTIONS }
      if (rememberMe) {
        options.expires = 30 // 30 hari jika remember me
      } else {
        options.expires = 1 // 1 hari default
      }
      Cookies.set(TOKEN_KEY, token, options)
      localStorage.setItem(REMEMBER_KEY, rememberMe)
      console.log('[CookieService] Token saved successfully')
    } catch (error) {
      console.error('[CookieService] Failed to save token:', error)
    }
  },

  // Get authentication token
  getToken: () => {
    try {
      return Cookies.get(TOKEN_KEY)
    } catch (error) {
      console.error('[CookieService] Failed to get token:', error)
      return null
    }
  },

  // Save user information
  saveUser: (user) => {
    try {
      const userJson = JSON.stringify(user)
      Cookies.set(USER_KEY, userJson, COOKIE_OPTIONS)
      console.log('[CookieService] User info saved successfully:', { username: user.username, divisions: user.divisions?.length })
    } catch (error) {
      console.error('[CookieService] Failed to save user:', error)
    }
  },

  // Get user information
  getUser: () => {
    try {
      const userJson = Cookies.get(USER_KEY)
      return userJson ? JSON.parse(userJson) : null
    } catch (error) {
      console.error('[CookieService] Failed to get user:', error)
      return null
    }
  },

  // Save remember me preference
  saveRememberMe: (rememberMe) => {
    try {
      localStorage.setItem(REMEMBER_KEY, rememberMe)
      if (!rememberMe) {
        // Jika tidak remember me, hapus token yang ada
        cookieService.clearToken()
        cookieService.clearUser()
      }
    } catch (error) {
      console.error('[CookieService] Failed to save remember me:', error)
    }
  },

  // Get remember me preference
  getRememberMe: () => {
    try {
      return localStorage.getItem(REMEMBER_KEY) === 'true'
    } catch (error) {
      console.error('[CookieService] Failed to get remember me:', error)
      return false
    }
  },

  // Clear all authentication data
  clearAuth: () => {
    try {
      Cookies.remove(TOKEN_KEY, { path: '/' })
      Cookies.remove(USER_KEY, { path: '/' })
      localStorage.removeItem(REMEMBER_KEY)
      console.log('[CookieService] Authentication data cleared')
    } catch (error) {
      console.error('[CookieService] Failed to clear auth data:', error)
    }
  },

  // Clear token only
  clearToken: () => {
    try {
      Cookies.remove(TOKEN_KEY, { path: '/' })
    } catch (error) {
      console.error('[CookieService] Failed to clear token:', error)
    }
  },

  // Clear user info only
  clearUser: () => {
    try {
      Cookies.remove(USER_KEY, { path: '/' })
    } catch (error) {
      console.error('[CookieService] Failed to clear user:', error)
    }
  },

  // Check if user is logged in
  isLoggedIn: () => {
    const token = cookieService.getToken()
    const user = cookieService.getUser()
    return !!(token && user)
  },

  // Get authentication header
  getAuthHeader: () => {
    const token = cookieService.getToken()
    return token ? { Authorization: `Bearer ${token}` } : {}
  }
}

export default cookieService