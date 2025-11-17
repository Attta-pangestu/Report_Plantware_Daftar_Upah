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
    timeout: 30000 // 30 second timeout
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

    // Return fallback structure
    const fallbackData = {
      report_info: {
        title: 'LAPORAN DAFTAR UPAH',
        generated_date: new Date().toISOString(),
        gang: gangCode || '-',
        database: 'Fallback',
        description: 'Fallback headers (API Error)',
        error: e.message
      },
      table_structure: {
        hierarchy: {
          level_1: { columns: [
            { id: 'no', text: 'NO', rowspan: 3, colspan: 1, children: [] },
            { id: 'nik', text: 'NIK', rowspan: 3, colspan: 1, children: [] },
            { id: 'name', text: 'NAMA', rowspan: 3, colspan: 1, children: [] },
            { id: 'upah_dasar', text: 'UPAH DASAR', rowspan: 3, colspan: 1, children: [] },
            { id: 'hari_kerja', text: 'HARI KERJA', rowspan: 3, colspan: 1, children: [] },
            { id: 'upah_pokok', text: 'UPAH POKOK', rowspan: 3, colspan: 1, children: [] },
            { id: 'upah_bersih', text: 'UPAH BERSIH', rowspan: 3, colspan: 1, children: [] }
          ] },
          level_2: { columns: [] },
          level_3: { columns: [] }
        },
        generated_headers: {
          level_1: { row: 1, columns: [
            { id: 'no', text: 'NO' },
            { id: 'nik', text: 'NIK' },
            { id: 'name', text: 'NAMA' },
            { id: 'upah_dasar', text: 'UPAH DASAR' },
            { id: 'hari_kerja', text: 'HARI KERJA' },
            { id: 'upah_pokok', text: 'UPAH POKOK' },
            { id: 'upah_bersih', text: 'UPAH BERSIH' }
          ] },
          level_2: { row: 2, columns: [] },
          level_3: { row: 3, columns: [] }
        }
      }
    }

    // Cache fallback for a shorter time (5 minutes)
    setCache(headerCache, `${cacheKey}_fallback`, fallbackData)

    return fallbackData
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
    timeout: 30000 // 30 second timeout
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

    // Return fallback column definitions
    const fallbackData = [
      { field: 'no', headerName: 'NO', width: 60, pinned: 'left' },
      { field: 'nik', headerName: 'NIK', width: 120, pinned: 'left' },
      { field: 'nama', headerName: 'NAMA', width: 200, pinned: 'left' },
      { field: 'upah_dasar', headerName: 'UPAH DASAR', width: 120, type: 'numericColumn' },
      { field: 'hari_kerja', headerName: 'HARI KERJA', width: 100, type: 'numericColumn' },
      { field: 'upah_pokok', headerName: 'UPAH POKOK', width: 120, type: 'numericColumn' },
      { field: 'upah_bersih', headerName: 'UPAH BERSIH', width: 120, type: 'numericColumn' }
    ]

    // Cache fallback for a shorter time
    setCache(columnCache, `${cacheKey}_fallback`, fallbackData)

    return fallbackData
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
