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
        config.headers.Authorization = `Bearer ${token}`
      }
    } catch (e) {
      console.warn('TESTING ONLY: Failed to resolve testing token, proceeding without header')
    }
    return config
  })

  axios.interceptors.response.use(
    (res) => res,
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
      return Promise.reject(error)
    }
  )
}
