import axios from 'axios'

export const fetchDynamicHeaders = async (token, month = null, year = null, gangCode = null) => {
  const params = {}
  if (month) params.month = month
  if (year) params.year = year
  if (gangCode) params.gang_code = gangCode

  const config = { params }
  if (token) config.headers = { Authorization: `Bearer ${token}` }
  try {
    const response = await axios.get('/payroll/headers', config)
    return response.data
  } catch (e) {
    return {
      report_info: {
        title: 'LAPORAN DAFTAR UPAH',
        generated_date: '',
        gang: gangCode || '-',
        database: '-',
        description: 'Fallback headers'
      },
      table_structure: {
        hierarchy: {
          level_1: { columns: [
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
  }
}

export const fetchColumnDefinitions = async (token, month = null, year = null, gangCode = null) => {
  const params = {}
  if (month) params.month = month
  if (year) params.year = year
  if (gangCode) params.gang_code = gangCode
  const config = { params }
  if (token) config.headers = { Authorization: `Bearer ${token}` }
  try {
    const response = await axios.get('/payroll/columns', config)
    return response.data
  } catch (e) {
    return [
      { field: 'nik', headerName: 'NIK' },
      { field: 'nama', headerName: 'NAMA' },
      { field: 'upah_dasar', headerName: 'UPAH DASAR' },
      { field: 'hari_kerja', headerName: 'HARI KERJA' },
      { field: 'upah_pokok', headerName: 'UPAH POKOK' },
      { field: 'upah_bersih', headerName: 'UPAH BERSIH' }
    ]
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
