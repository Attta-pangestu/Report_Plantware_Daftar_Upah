import { useEffect, useState } from 'react'
import Report from './pages/Report'
import LoginPage from './pages/LoginPage'
import { AuthProvider, useAuth } from './context/AuthContext'
import Modal from './components/common/Modal'
import LoadingScreen from './components/common/LoadingScreen'
import { fetchGangs } from './services/gangService'
import TestModePanel from './components/common/TestModePanel'

// Check if running in development mode
const DEV_MODE = import.meta.env.DEV || false
const TEST_MODE = DEV_MODE && import.meta.env.VITE_DEV_MODE === 'true'

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
      if (!isAuthenticated || !user) return

      setInitError('')
      try {
        console.log('[App] Starting authenticated bootstrap...')

        setFiltersOpen(true)

        // Load gangs from API based on user's accessible divisions
        if (user.divisions && user.divisions.length > 0) {
          console.log('[App] Loading gangs for user divisions:', user.divisions)
          try {
            // Load gangs for first accessible division
            const firstDivision = user.divisions[0]
            const gangsList = await fetchGangs(token, firstDivision, null, true)
            setGangs(gangsList)
            setDivision(firstDivision)
          } catch (gangError) {
            console.log('[App] Gang loading failed, using fallback for dev mode')
            const fallbackGangs = ['H1H', 'H001', 'H002', 'H003', 'A001', 'B001']
            setGangs(fallbackGangs)
            setDivision(user.divisions[0])
          }
        } else {
          console.log('[App] User has no division access')
          setGangError('No division access assigned')
        }
      } catch (error) {
        console.error('[App] Bootstrap error:', error)
        // For gangs loading error, provide fallback gangs
        if (error.message && error.message.includes('gangs')) {
          console.log('[App] Gangs loading failed, using fallback data')
          const fallbackGangs = ['H1H', 'H001', 'H002', 'H003']
          setGangs(fallbackGangs)
          setGang('H1H')
          setFiltersOpen(true)
          setReady(false)
          return
        }
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

  // Always show login page if not authenticated; keep it visible even while submitting
  if (!isAuthenticated) {
    return <LoginPage />
  }

  // Show loading screen only after authentication for background tasks
  if (loading) {
    return (
      <LoadingScreen
        isLoading={true}
        message="Initializing..."
        steps={[
          { name: 'Preparing report workspace', duration: 1000 },
          { name: 'Loading configuration', duration: 1000 }
        ]}
      />
    )
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
        <LoadingScreen
          isLoading={true}
          message="Generating payroll report..."
          gangCode={gang}
          month={month}
          year={year}
          steps={[
            { name: 'Connecting to database server', duration: 1000 },
            { name: 'Loading dynamic headers', duration: 2000 },
            { name: 'Fetching employee data from database', duration: 3000 },
            { name: 'Processing payroll calculations', duration: 2500 },
            { name: 'Auto-hiding empty columns', duration: 1000 },
            { name: 'Finalizing report layout', duration: 1500 }
          ]}
        />
      )}
      {ready ? <Report token={token} month={month} year={year} gang_code={gang_code} onLoad={() => setApplyLoading(false)} /> : null}
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  )
}
