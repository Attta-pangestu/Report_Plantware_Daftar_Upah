import axios from 'axios'

const TEST_MODE = (import.meta.env?.VITE_DEV_MODE === 'true') || (import.meta.env?.DEV_MODE === 'true')

// TESTING ONLY
let testingToken = null

// TESTING ONLY
async function ensureTestingToken() {
  if (testingToken) return testingToken
  try {
    const r = await axios.get('/auth/test-token')
    testingToken = r?.data?.access_token || 'permanent-testing-token'
    localStorage.setItem('testing_token', testingToken)
  } catch (_) {
    testingToken = localStorage.getItem('testing_token') || 'permanent-testing-token'
  }
  return testingToken
}

if (TEST_MODE) {
  console.warn('TESTING ONLY: Test mode enabled — auto-injecting permanent test token for all requests')
  // TESTING ONLY: Prefetch token at startup
  ensureTestingToken()

  axios.interceptors.request.use(async (config) => {
    try {
      const token = localStorage.getItem('testing_token') || await ensureTestingToken()
      config.headers = config.headers || {}
      const hasAuth = typeof config.headers.Authorization === 'string' && config.headers.Authorization.trim().length > 'Bearer'.length
      if (!hasAuth) {
        // For test mode, only add Authorization header if token doesn't look like a test token
        if (!token || !token.includes('testing-token')) {
          config.headers.Authorization = `Bearer ${token}`
        } else {
          console.warn('TESTING ONLY: Skipping Authorization header for test token')
        }
      }
    } catch (e) {
      console.warn('TESTING ONLY: Failed to resolve testing token, proceeding without header')
    }
    try {
      const start = Date.now()
      config.meta = Object.assign({}, config.meta, { start })
      const u = (config.baseURL || '') + (config.url || '')
      const m = (config.method || 'get').toUpperCase()
      const p = config.params || {}
      console.log(`[HTTP] -> ${m} ${u}`, { params: p, headers: Object.keys(config.headers || {}) })
    } catch (_) {}
    return config
  })

  axios.interceptors.response.use(
    (res) => {
      try {
        const start = res.config?.meta?.start || Date.now()
        const dur = Date.now() - start
        const u = (res.config?.baseURL || '') + (res.config?.url || '')
        const m = (res.config?.method || 'get').toUpperCase()
        console.log(`[HTTP] <- ${m} ${u} ${res.status} ${dur}ms`, { length: Array.isArray(res.data) ? res.data.length : undefined })
      } catch (_) {}
      return res
    },
    async (error) => {
      const status = error?.response?.status
      if (TEST_MODE && status === 401) {
        console.warn('TESTING ONLY: Received 401 — injecting testing token and retrying once')
        try {
          const token = await ensureTestingToken()
          const cfg = error.config
          cfg.headers = cfg.headers || {}
          cfg.headers.Authorization = `Bearer ${token}`
          return axios(cfg)
        } catch (e) {
          console.warn('TESTING ONLY: Retry after token inject failed')
        }
      }
      try {
        const cfg = error.config || {}
        const u = (cfg.baseURL || '') + (cfg.url || '')
        const m = (cfg.method || 'get').toUpperCase()
        const start = cfg.meta?.start || Date.now()
        const dur = Date.now() - start
        console.error(`[HTTP] !! ${m} ${u} ${status || 'ERR'} ${dur}ms`, { message: error.message })
      } catch (_) {}
      return Promise.reject(error)
    }
  )
}
