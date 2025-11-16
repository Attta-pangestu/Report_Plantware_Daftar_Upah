import axios from 'axios'

export async function login(username, password) {
  const r = await axios.post('/auth/login', { username, password })
  return r.data
}

export async function getMe(token) {
  const r = await axios.get('/auth/me', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return r.data
}

export async function getAccessibleDivisions(token) {
  const r = await axios.get('/auth/accessible-divisions', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return r.data
}
