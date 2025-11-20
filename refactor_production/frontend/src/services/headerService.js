import axios from 'axios'

// Client-side cache for headers and columns
const headerCache = new Map()
const columnCache = new Map()
const CACHE_TTL = 15 * 60 * 1000 // 15 minutes in milliseconds
// In-flight request registries to prevent duplicate axios calls
const inFlightHeaders = new Map()
const inFlightColumns = new Map()

const getCacheKey = (token, month, year, gangCode) => {
  return `${token || 'guest'}_${gangCode || 'all'}_${year || 'current'}_${month || 'current'}`
}

const getFromCache = (cache, key) => {
  const cached = cache.get(key)
  if (cached && (Date.now() - cached.timestamp) < CACHE_TTL) {
    console.log(`Cache hit for ${cache === headerCache ? 'headers' : 'columns'}: ${key}`)
    return cached.data
  }
  if (cached) {
    cache.delete(key) // Remove expired cache
  }
  return null
}

const setCache = (cache, key, data) => {
  cache.set(key, { data, timestamp: Date.now() })
  console.log(`Cached ${cache === headerCache ? 'headers' : 'columns'} for key: ${key}`)
}

export const fetchDynamicHeaders = async (token, month = null, year = null, gangCode = null) => {
  const cacheKey = getCacheKey(token, month, year, gangCode)

  // Try to get from cache first
  const cachedHeaders = getFromCache(headerCache, cacheKey)
  if (cachedHeaders) {
    return cachedHeaders
  }

  const params = {}
  if (month) params.month = month
  if (year) params.year = year
  if (gangCode) params.gang_code = gangCode

  const config = {
    params,
    timeout: 45000 // Increased timeout to 45 seconds for database queries
  }
  if (token) config.headers = { Authorization: `Bearer ${token}` }

  // Return existing in-flight promise if present
  if (inFlightHeaders.has(cacheKey)) {
    return await inFlightHeaders.get(cacheKey)
  }

  try {
    console.log(`[Headers API] Fetching dynamic headers for: ${gangCode || 'all'} ${month}-${year}`)
    console.log(`[Headers API] Request: GET /payroll/headers with params:`, JSON.stringify(params, null, 2))
    const startTime = Date.now()

    const promise = axios.get('/payroll/headers', config)
    inFlightHeaders.set(cacheKey, promise)
    const response = await promise
    const data = response.data

    const fetchTime = Date.now() - startTime
    console.log(`[Headers API] Response received in ${fetchTime}ms`)
    console.log(`[Headers API] Header structure:`, data ? '✅ Valid' : '❌ Empty')

    // Cache the response
    setCache(headerCache, cacheKey, data)
    inFlightHeaders.delete(cacheKey)

    return data
  } catch (e) {
    console.error('[Headers API] Failed to fetch dynamic headers:', e)
    inFlightHeaders.delete(cacheKey)

    // Enhanced error logging
    const errorDetails = {
      message: e.message,
      code: e.code,
      response: e.response?.status,
      responseText: e.response?.data?.detail || e.response?.data,
      url: '/payroll/headers',
      params: params,
      timestamp: new Date().toISOString()
    }
    console.error('[Headers API] Error details:', JSON.stringify(errorDetails, null, 2))

    // Direct error - no static fallback, always require database connection
    throw new Error(`Database connection failed for headers: ${e.message}. Status: ${e.response?.status || 'Network Error'}. Please check database connectivity and try again.`)
  }
}

export const fetchColumnDefinitions = async (token, month = null, year = null, gangCode = null) => {
  const cacheKey = getCacheKey(token, month, year, gangCode)

  // Try to get from cache first
  const cachedColumns = getFromCache(columnCache, cacheKey)
  if (cachedColumns) {
    return cachedColumns
  }

  const params = {}
  if (month) params.month = month
  if (year) params.year = year
  if (gangCode) params.gang_code = gangCode

  const config = {
    params,
    timeout: 45000 // Increased timeout to 45 seconds for database queries
  }
  if (token) config.headers = { Authorization: `Bearer ${token}` }

  if (inFlightColumns.has(cacheKey)) {
    return await inFlightColumns.get(cacheKey)
  }

  try {
    console.log(`Fetching column definitions for: ${gangCode || 'all'} ${month}-${year}`)
    const startTime = Date.now()

    const promise = axios.get('/payroll/columns', config)
    inFlightColumns.set(cacheKey, promise)
    const response = await promise
    const data = response.data

    const fetchTime = Date.now() - startTime
    console.log(`Column definitions fetched in ${fetchTime}ms`)
    console.log('[Columns API] Raw response data:', data)
    console.log('[Columns API] Data type:', typeof data)
    console.log('[Columns API] Is array?:', Array.isArray(data))
    console.log('[Columns API] Data length:', data?.length)

    // Cache the response
    setCache(columnCache, cacheKey, data)
    inFlightColumns.delete(cacheKey)

    return data
  } catch (e) {
    console.error('Failed to fetch column definitions:', e)
    inFlightColumns.delete(cacheKey)

    // Enhanced error logging
    const errorDetails = {
      message: e.message,
      code: e.code,
      response: e.response?.status,
      url: '/payroll/columns',
      params: params,
      timestamp: new Date().toISOString()
    }
    console.error('Column fetch error details:', errorDetails)

    // Direct error - no static fallback, always require database connection
    throw new Error(`Database connection failed for column definitions: ${e.message}. Status: ${e.response?.status || 'Network Error'}. Please check database connectivity and try again.`)
  }
}

// Clear cache utility function
export const clearCache = () => {
  headerCache.clear()
  columnCache.clear()
  console.log('Header and column caches cleared')
}

// Cache status utility function
export const getCacheStatus = () => {
  return {
    headersCache: {
      size: headerCache.size,
      keys: Array.from(headerCache.keys())
    },
    columnsCache: {
      size: columnCache.size,
      keys: Array.from(columnCache.keys())
    }
  }
}

export const formatCurrency = (value) => {
  if (value === null || value === undefined || value === 0) return '-'
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}

export const formatNumber = (value) => {
  if (value === null || value === undefined || value === 0) return '-'
  return new Intl.NumberFormat('id-ID').format(value)
}

export const getMonthName = (monthNumber) => {
  const months = [
    '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
  ]
  return months[monthNumber] || ''
}


// Auto-hide by zero totals has been removed; backend now filters dynamic headers
