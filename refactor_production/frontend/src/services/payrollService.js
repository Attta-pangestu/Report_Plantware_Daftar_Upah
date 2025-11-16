import axios from 'axios'

export async function fetchReportRows(token, { month, year, gang_code }) {
  const params = {}
  if (month) params.month = month
  if (year) params.year = year
  if (gang_code) params.gang_code = gang_code
  const r = await axios.get('/payroll/report', { headers: { Authorization: `Bearer ${token}` }, params })
  return r.data
}
