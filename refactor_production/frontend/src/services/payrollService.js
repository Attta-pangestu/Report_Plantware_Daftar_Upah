import axios from 'axios'

export async function fetchReportRows(token, { month, year, gang_code, fields, skip, limit, benchmark = false, monitor = false }) {
  const params = {}
  if (month) params.month = month
  if (year) params.year = year
  if (gang_code) params.gang_code = gang_code
  if (Array.isArray(fields) && fields.length > 0) params.fields = fields.join(',')
  if (typeof skip === 'number') params.skip = skip
  if (typeof limit === 'number') params.limit = limit
  if (benchmark) params.benchmark = true
  if (monitor) params.monitor = true
  const config = { params }
  if (token) config.headers = { Authorization: `Bearer ${token}` }
  const r = await axios.get('/payroll/report', config)
  return r.data
}
