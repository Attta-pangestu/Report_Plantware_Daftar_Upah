import axios from 'axios'

export const fetchDynamicHeaders = async (token, month = null, year = null, gangCode = null) => {
  const params = {}
  if (month) params.month = month
  if (year) params.year = year
  if (gangCode) params.gang_code = gangCode

  const response = await axios.get('/payroll/headers', {
    params,
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
  return response.data
}

export const fetchColumnDefinitions = async (token) => {
  const response = await axios.get('/payroll/columns', {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
  return response.data
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