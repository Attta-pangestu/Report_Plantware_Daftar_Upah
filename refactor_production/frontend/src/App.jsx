import { useEffect, useState } from 'react'
import Report from './pages/Report'
import LoginPage from './pages/LoginPage'
import { AuthProvider, useAuth } from './context/AuthContext'
import Modal from './components/common/Modal'
import { fetchGangs } from './services/gangService'

// Check if running in development mode
const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true' || import.meta.env.DEV_MODE === 'true'

function AppInner() {
  const { token, isAuthenticated, user, loading, error } = useAuth()
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [monthInput, setMonthInput] = useState('')
  const [gangs, setGangs] = useState([])
  const [gang, setGang] = useState('')
  const [division, setDivision] = useState('')
  const [ready, setReady] = useState(false)
  const [applyLoading, setApplyLoading] = useState(false)
  const [gangLoading, setGangLoading] = useState(false)
  const [gangError, setGangError] = useState('')
  const [initError, setInitError] = useState('')
  const [gangSearch, setGangSearch] = useState('')  // State untuk search gang

  useEffect(() => {
    async function bootstrap() {
      // In dev mode, auto-login with admin credentials
      if (DEV_MODE && !isAuthenticated) {
        console.log('[App] Development mode: Auto-login with admin credentials')
        // Simulate successful login
        const mockUser = {
          id: 1,
          username: 'admin',
          email: 'admin@payroll.com',
          full_name: 'Development Admin',
          role: 'admin',
          divisions: ['PG1A', 'PG1B', 'PG2A', 'PG2B', 'DME', 'ARA', 'ARB1', 'ARB2', 'INFRA', 'AREC', 'IJL', 'STF-OFFICE', 'SECURITY']
        }
        // Auto-login
        // You might need to update your AuthContext to handle this
        // For now, let's continue with the regular flow
      }

      if (!isAuthenticated || !user) return

      setInitError('')
      try {
        console.log('[App] Starting authenticated bootstrap...')

        // Show filters modal for authenticated users
        setFiltersOpen(true)

        // In dev mode, set default values
        if (DEV_MODE) {
          console.log('[App] Development mode: Setting default values')
          setMonthInput('2025-05') // May 2025
          setDivision('ARB2')      // ARB2 division

          // Load gangs for ARB2 division
          const gangsList = await fetchGangs(token || 'dev-token', 'ARB2', null, true)
          setGangs(gangsList)

          // Look for H1H gang
          const h1hGang = gangsList.find(g => g.toUpperCase() === 'H1H')
          if (h1hGang) {
            setGang(h1hGang)
            console.log('[App] Development mode: Found H1H gang, auto-submitting filters')
            // Auto-submit filters in dev mode
            setTimeout(() => {
              setFiltersOpen(false)
              setReady(true)
            }, 1000)
          } else {
            console.log('[App] Development mode: H1H gang not found, showing filters')
          }
          return
        }

        // Load gangs from API based on user's accessible divisions
        if (user.divisions && user.divisions.length > 0) {
          console.log('[App] Loading gangs for user divisions:', user.divisions)
          // Load gangs for first accessible division
          const firstDivision = user.divisions[0]
          const gangsList = await fetchGangs(token, firstDivision, null, true)
          setGangs(gangsList)
          setDivision(firstDivision)
        } else {
          console.log('[App] User has no division access')
          setGangError('No division access assigned')
        }
      } catch (error) {
        console.error('[App] Bootstrap error:', error)
        setInitError('Failed to load application data: ' + error.message)
      }
    }

    bootstrap()
  }, [isAuthenticated, user, token])

  useEffect(() => {
    async function loadGangs() {
      if (!division) { setGangs([]); setGang(''); return }
      setGangLoading(true); setGangError('')
      try {
        // Include search term in API call
        const searchTerm = gangSearch.trim() || null
        const list = await fetchGangs(token || '', division, searchTerm, true)
        setGangs(list)
        if (!list || list.length === 0) {
          if (searchTerm) {
            setGangError(`No gangs found for division "${division}" matching "${searchTerm}"`)
          } else {
            setGangError(`No gangs found for division "${division}"`)
          }
        } else {
          setGangError('')
        }
        // Clear selected gang if it's not in the filtered results
        if (gang && !list.includes(gang)) {
          setGang('')
        }
      } catch (e) {
        setGangError('Failed to load gangs')
      } finally {
        setGangLoading(false)
      }
    }
    loadGangs()
  }, [division, gangSearch, token])

  const submitFilters = () => {
    if (!monthInput || !division || !gang) return alert('Please select month, division and gang')
    console.log('[App] Submitting filters for:', { monthInput, division, gang })
    setFiltersOpen(false)
    setApplyLoading(true)
    setReady(true)
  }

  // Show loading screen during authentication
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div>Loading Payroll System...</div>
        <div style={{ marginTop: 10, fontSize: 12, color: '#666' }}>Authenticating...</div>
      </div>
    )
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage />
  }

  // Show error screen if initialization failed
  if (initError) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{ color: 'red', marginBottom: 20 }}>Error: {initError}</div>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    )
  }

  const [yyyy, mm] = monthInput ? monthInput.split('-') : ['', '']
  const month = mm ? Number(mm) : undefined
  const year = yyyy ? Number(yyyy) : undefined
  const gang_code = gang || undefined

  return (
    <>
      <Modal open={filtersOpen} title="Select Month & Gang" onClose={() => setFiltersOpen(false)}>
        <div style={{ display:'grid', gap:12, minWidth: 400 }}>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 'bold' }}>
              Month:
            </label>
            <input
              type="month"
              value={monthInput}
              onChange={e => setMonthInput(e.target.value)}
              style={{ width: '100%', padding: 4 }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 'bold' }}>
              Division:
            </label>
            <select
              value={division}
              onChange={e => setDivision(e.target.value)}
              style={{ width: '100%', padding: 4 }}
            >
              <option value="">-- Select Division --</option>
              {user.divisions.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
            {user.divisions.length === 0 && (
              <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                No divisions assigned to your account
              </div>
            )}
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 'bold' }}>
              Search Gang (Optional):
            </label>
            <input
              type="text"
              value={gangSearch}
              onChange={e => setGangSearch(e.target.value)}
              placeholder="Search gang codes..."
              disabled={!division}
              style={{
                width: '100%',
                padding: 4,
                marginBottom: 4
              }}
            />
            {gangSearch && (
              <div style={{ fontSize: 12, color: '#666', marginTop: 2 }}>
                Searching for: "{gangSearch}" in division "{division}"
              </div>
            )}
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 'bold' }}>
              Gang:
              {gangLoading && <span style={{ marginLeft: 10, fontSize: 12, color: '#666' }}>Loading...</span>}
              {gangSearch && <span style={{ marginLeft: 10, fontSize: 12, color: '#0066cc' }}>Filtered</span>}
            </label>
        <select
          value={gang}
          onChange={e => setGang((e.target.value || '').trim())}
          disabled={!division || gangLoading}
          style={{ width: '100%', padding: 4 }}
        >
          <option value="">-- Select Gang --</option>
          {gangs.map(g => (
            <option key={g} value={(g || '').trim()}>{(g || '').trim()}</option>
          ))}
        </select>
            {gangError && (
              <div style={{ fontSize: 12, color: 'red', marginTop: 4 }}>
                {gangError}
              </div>
            )}
          </div>

          <div style={{ textAlign:'right', paddingTop: 8 }}>
            <button
              onClick={submitFilters}
              disabled={!monthInput || !division || !gang || gangLoading}
              style={{
                padding: '6px 16px',
                cursor: (!monthInput || !division || !gang || gangLoading) ? 'not-allowed' : 'pointer',
                opacity: (!monthInput || !division || !gang || gangLoading) ? 0.6 : 1
              }}
            >
              {gangLoading ? 'Loading...' : 'Apply'}
            </button>
          </div>

          <div style={{
            marginTop: '12px',
            paddingTop: '8px',
            borderTop: '1px solid #eee',
            fontSize: '12px',
            color: '#666'
          }}>
            Logged in as: <strong>{user.full_name}</strong> ({user.username})<br/>
            Role: <strong>{user.role}</strong> | Access to {user.divisions.length} divisions
          </div>
        </div>
      </Modal>
      {applyLoading && (
        <div style={{ position:'fixed', top:0, left:0, right:0, bottom:0, background:'rgba(255,255,255,0.8)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:9999 }}>
          <div style={{ textAlign:'center' }}>
            <div style={{ width:48, height:48, border:'4px solid #ccc', borderTopColor:'#1976d2', borderRadius:'50%', animation:'spin 1s linear infinite', margin:'0 auto' }} />
            <div style={{ marginTop:10, color:'#333' }}>Loading report data...</div>
            <div style={{ marginTop:5, fontSize:12, color:'#666' }}>Headers are being preloaded for faster display</div>
          </div>
        </div>
      )}
      {ready ? <Report token={token} month={month} year={year} gang_code={gang_code} onLoad={() => setApplyLoading(false)} /> : null}
    </>
  )
}

export default function App() {
  // In development mode, bypass auth and go directly to report
  if (DEV_MODE) {
    console.log('[App] Development mode: Bypassing auth, showing Report directly')
    return <Report />
  }

  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  )
}
