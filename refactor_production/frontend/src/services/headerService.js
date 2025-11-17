import axios from 'axios'

// Client-side cache for headers and columns
const headerCache = new Map()
const columnCache = new Map()
const CACHE_TTL = 15 * 60 * 1000 // 15 minutes in milliseconds

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
    timeout: 15000 // 15 second timeout untuk mencegah tunggu terlalu lama
  }
  if (token) config.headers = { Authorization: `Bearer ${token}` }

  try {
    console.log(`Fetching dynamic headers for: ${gangCode || 'all'} ${month}-${year}`)
    const startTime = Date.now()

    const response = await axios.get('/payroll/headers', config)
    const data = response.data

    const fetchTime = Date.now() - startTime
    console.log(`Dynamic headers fetched in ${fetchTime}ms`)

    // Cache the response
    setCache(headerCache, cacheKey, data)

    return data
  } catch (e) {
    console.error('Failed to fetch dynamic headers:', e)

    // No fallback - throw error immediately to prevent simple column display
    throw new Error(`Failed to load dynamic headers: ${e.message}. Backend API may be down or header structure file missing.`)
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
    timeout: 15000 // 15 second timeout untuk mencegah tunggu terlalu lama
  }
  if (token) config.headers = { Authorization: `Bearer ${token}` }

  try {
    console.log(`Fetching column definitions for: ${gangCode || 'all'} ${month}-${year}`)
    const startTime = Date.now()

    const response = await axios.get('/payroll/columns', config)
    const data = response.data

    const fetchTime = Date.now() - startTime
    console.log(`Column definitions fetched in ${fetchTime}ms`)

    // Cache the response
    setCache(columnCache, cacheKey, data)

    return data
  } catch (e) {
    console.error('Failed to fetch column definitions:', e)

    // No fallback - throw error to prevent simple column display
    throw new Error(`Failed to load column definitions: ${e.message}. Backend API may be down or header structure missing.`)
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
