import axios from 'axios'

export async function fetchGangs(token, division = null, search = null, force = false) {
  const params = {}
  if (division) params.division = division
  if (search) params.search = search
  if (force) params.force = force
  const r = await axios.get('/payroll/gangs', {
    headers: { Authorization: `Bearer ${token}` },
    params
  })
  return r.data
}

export async function fetchDivisions(token) {
  const r = await axios.get('/payroll/divisions', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return r.data
}

export async function fetchGangInfo(token, gangCode) {
  const r = await axios.get(`/payroll/gang/${gangCode}/info`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return r.data
}
