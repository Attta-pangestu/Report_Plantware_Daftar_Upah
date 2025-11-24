import { useEffect, useMemo, useRef, useState } from 'react'
import { AgGridReact } from 'ag-grid-react'
import HierHeaderGroup from '../components/common/HierHeaderGroup'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import '../styles/report.css'
import { fetchReportRows, fetchReportRowsBatched, fetchReportRowsSimple, fetchReportAggregate, fetchReportCount } from '../services/payrollService'
import { fetchDynamicHeaders, fetchColumnDefinitions, formatCurrency, formatNumber } from '../services/headerService'
import { login } from '../services/authService'
import { fetchReferenceHtml } from '../services/validationService'
import LoadingScreen from '../components/common/LoadingScreen'
import { fetchGangInfo } from '../services/gangService'
import { useAuth } from '../context/AuthContext'

// Check if running in development mode
const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true' || import.meta.env.DEV_MODE === 'true'

export default function Report({ token, user, month, year, gang_code, onLoad }) {
  // Authentication hook
  const { logout } = useAuth()

  // In development mode, use default values if props are not provided
  const devMonth = DEV_MODE ? (month || undefined) : month
  const devYear = DEV_MODE ? (year || undefined) : year
  const devGangCode = DEV_MODE ? (gang_code || undefined) : gang_code

  const [authToken, setAuthToken] = useState(token || null)
  const finalMonth = devMonth || month
  const finalYear = devYear || year
  const finalGangCode = devGangCode || gang_code
  const [rows, setRows] = useState([])
  const [pinnedBottom, setPinnedBottom] = useState([])
  const [columnDefs, setColumnDefs] = useState([])
  const computeRulesRef = useRef({})
  const [headers, setHeaders] = useState(null)
  const [hierarchyHeaders, setHierarchyHeaders] = useState(null)
  const [loading, setLoading] = useState(false)
  const [headerLoading, setHeaderLoading] = useState(false)
  const [loadingStatus, setLoadingStatus] = useState('Initializing...')
  const [currentEndpoint, setCurrentEndpoint] = useState('')
  const [error, setError] = useState('')
  const [showValidation, setShowValidation] = useState(false)
  const [referenceHtml, setReferenceHtml] = useState('')
  const [validationResult, setValidationResult] = useState(null)
  const gridRef = useRef(null)
  const aggCacheRef = useRef(new Map())
  const [overrideMonth, setOverrideMonth] = useState(null)
  const [overrideYear, setOverrideYear] = useState(null)
  const useInfinite = true
  const INFINITE_BATCH_SIZE = Number(import.meta.env.VITE_BATCH_SIZE || 200)
  const DISABLE_CACHE = (import.meta.env?.VITE_DISABLE_CACHE === 'true') || (import.meta.env?.VITE_DEV_MODE === 'true') || (import.meta.env?.DEV_MODE === 'true')
  const fpsRef = useRef({ last: performance.now(), frames: 0 })
  const aggregateInFlightRef = useRef(new Set())
  const dataInitRef = useRef(false)
  const autoHideMapRef = useRef({})
  const [firstBatchReady, setFirstBatchReady] = useState(false)
  const [initialRowsPreview, setInitialRowsPreview] = useState([])
  const [firstBatchAttempted, setFirstBatchAttempted] = useState(false)    
  const [gangInfo, setGangInfo] = useState(null)
  useEffect(() => {
    console.log('[Report] Column definitions useEffect triggered:', { authToken: !!authToken, finalMonth, finalYear, finalGangCode })
    async function loadColumnDefinitions() {
      setHeaderLoading(true)
      setLoadingStatus('Loading column definitions...')
      setCurrentEndpoint('/payroll/columns')
      setError('')
      try {
        // Parse month if it's a string in YYYY-MM format
        let monthValue = finalMonth
        let yearValue = finalYear

        if (typeof finalMonth === 'string' && finalMonth.includes('-')) {
          const [year, month] = finalMonth.split('-')
          monthValue = parseInt(month, 10)
          yearValue = parseInt(year, 10)
        }

        console.log('[Report] Loading headers for:', { monthValue, yearValue, finalGangCode })

        setLoadingStatus(`Fetching headers for Gang ${finalGangCode}...`)
        // Ensure auth token in dev mode
        let activeToken = authToken
        if (!activeToken && DEV_MODE) {
          try {
            const res = await login('admin', 'admin')
            setAuthToken(res.access_token)
            activeToken = res.access_token
          } catch (autoErr) {
            console.error('[Report] Auto-login failed:', autoErr)
          }
        }
        // Skip headers API - langsung ke column definitions
        setHeaders(null)
        setHierarchyHeaders({ level1: [], level2: [], level3: [] })

        setLoadingStatus(`Fetching column definitions for Gang ${finalGangCode}...`)
        try {
          const cols = await fetchColumnDefinitions(activeToken, monthValue, yearValue, finalGangCode)
          const normalized = Array.isArray(cols) ? cols : (Array.isArray(cols?.columns) ? cols.columns : [])
          // Gunakan headers dari backend langsung tanpa modification
          const transformed = removePlaceholderPotonganHeaders(relocateDynamicPotonganHeaders(normalized))
          ensureHierarchicalOrThrow(transformed)
          const enhanced = enhanceColumnsRecursive(transformed, 0)
          console.log('[Report] 📋 Column definitions diterima:', {
            total_columns: enhanced.length,
            sample_columns: enhanced.slice(0, 3).map(c => ({ field: c.field, header: c.headerName }))
          })

          const seqCol = {
            headerName: 'NO',
            width: 60,
            pinned: 'left',
            type: 'textColumn',
            valueGetter: params => {
              try {
                const idx = params.node.rowIndex
                return (typeof idx === 'number' ? idx + 1 : '')
              } catch (e) {
                return ''
              }
            }
          }
          setColumnDefs([seqCol, ...enhanced])
          computeRulesRef.current = createFallbackComputeRules()

          console.log('[Report] ✅ Column definitions siap, total:', enhanced.length, 'kolom')
          console.log('[Report] 🔄 Menunggu trigger data loading...')
        } catch (colErr) {
          console.error('[Report] Column definitions fetch failed:', colErr)
          computeRulesRef.current = createFallbackComputeRules()
          setError('Failed to load column definitions')
        }
      } catch (e) {
        console.error('Failed to initialize column definitions loading:', e)
      } finally {
        setHeaderLoading(false)
        setLoadingStatus('Column definitions loaded successfully')
        setCurrentEndpoint('')
      }
    }

    loadColumnDefinitions()
  }, [authToken, finalMonth, finalYear, finalGangCode, overrideMonth, overrideYear])

  useEffect(() => {
    console.log('[Report] Data loading useEffect triggered:', {
      columnDefsLength: columnDefs?.length || 0,
      columnDefs: columnDefs,
      authToken: !!authToken,
      finalMonth,
      finalYear,
      finalGangCode
    })

    async function run() {
      console.log('[Report] Starting data loading process...')
      setLoading(true);
      setLoadingStatus('Loading payroll data...')
      setCurrentEndpoint('/payroll/report')
      setError('')
      try {
        // Parse month if it's a string in YYYY-MM format
        let monthValue = finalMonth
        let yearValue = finalYear

        if (typeof finalMonth === 'string' && finalMonth.includes('-')) {
          const [year, month] = finalMonth.split('-')
          monthValue = parseInt(month, 10)
          yearValue = parseInt(year, 10)
        }

        console.log('[Report] 🚀 Starting data load for:', { month: monthValue, year: yearValue, gang: finalGangCode })

        setLoadingStatus(`📡 Mengambil data transaksi payroll untuk Gang ${finalGangCode}...`)

        // Ensure auth token is ready
        let activeToken = authToken
        if (!activeToken && DEV_MODE) {
          console.log('[Report] 🔐 Auto-login untuk mendapatkan token...')
          try {
            const res = await login('admin', 'admin')
            setAuthToken(res.access_token)
            activeToken = res.access_token
            console.log('[Report] ✅ Token berhasil didapatkan')
          } catch (autoErr) {
            console.error('[Report] ❌ Auto-login gagal:', autoErr)
          }
        }

        console.log('[Report] 📡 Mengirim request ke /payroll/report/real...')
        console.log('[Report] 📋 Parameter:', { month: monthValue, year: yearValue, gang_code: finalGangCode, skip: 0, limit: 200 })

        const startTime = Date.now()
        setLoadingStatus('⏳ Menunggu response data transaksi payroll...')

        const data = await fetchReportRowsSimple(activeToken, { month: (overrideMonth || monthValue), year: (overrideYear || yearValue), gang_code: finalGangCode, skip: 0, limit: INFINITE_BATCH_SIZE })

        const fetchTime = Date.now() - startTime
        console.log('[Report] ✅ Data transaksi diterima!')
        console.log('[Report] 📊 Jumlah record:', data.length, 'baris')
        console.log('[Report] ⏱️ Waktu response:', fetchTime, 'ms')

        console.log('[Report] 🔄 Memproses data transaksi dengan client-side compute...')
        const processingStart = Date.now()

        const computed = applyComputeToRows(data, computeRulesRef.current)
        const processingTime = Date.now() - processingStart

        setRows(computed)
        const safe = Array.isArray(computed) ? computed : []
        recomputeAutoHideMap(safe)
        setInitialRowsPreview(safe.slice(0, INFINITE_BATCH_SIZE))
        setFirstBatchAttempted(true)
        setFirstBatchReady(safe.length > 0)
        

        console.log('[Report] ✅ Data transaksi siap!')
        console.log('[Report] 📊 Total record diproses:', safe.length, 'baris')
        console.log('[Report] ⏱️ Waktu processing:', processingTime, 'ms')

        // Debug: Tampilkan sampel data
        if (safe.length > 0) {
          console.log('[Report] 🔍 Sample data baris pertama:')
          console.table(safe[0])
          console.log('[Report] 💰 Sample nilai upah_bersih:', safe.slice(0, 3).map(r => ({ nama: r.nama, upah_bersih: r.upah_bersih })))
        } else {
          console.warn('[Report] ⚠️ Tidak ada data transaksi yang ditemukan')
        }

        console.log('[Report] 🧮 Menghitung agregasi total...')
        setLoadingStatus('🧈 Menghitung total agregasi...')
        const agg = (field) => Math.round(safe.reduce((a, b) => a + Number(b[field] || 0), 0))
        if (safe.length > 0) {
          const grand = {
            no: '', jenis_kelamin: '', nik: '', nama: 'GRAND TOTAL',
            upah_dasar: '', hari_kerja: agg('hari_kerja'), upah_pokok: agg('upah_pokok'),
            cuti_tahunan_hari: agg('cuti_tahunan_hari'), cuti_sakit_haid_hari: agg('cuti_sakit_haid_hari'), cuti_minggu_hari: agg('cuti_minggu_hari'), cuti_nasional_hari: agg('cuti_nasional_hari'), jumlah_hk: agg('jumlah_hk'),
            gaji_pokok: agg('gaji_pokok'), beras_rate: '', beras_jumlah: agg('beras_jumlah'), jabatan_rate: '', jabatan_jumlah: agg('jabatan_jumlah'), masa_kerja_tahun: '', masa_kerja_jumlah: agg('masa_kerja_jumlah'), lembur_jam: '', lembur_jumlah: agg('lembur_jumlah'), total_tunjangan: agg('total_tunjangan'),
            premi_brondol: agg('premi_brondol'), premi_pruning: agg('premi_pruning'), premi_angkut_material: agg('premi_angkut_material'), premi_angkut_tbs: agg('premi_angkut_tbs'), premi_harvesting: agg('premi_harvesting'), premi_harvesting_incentive: agg('premi_harvesting_incentive'), premi_pupuk: agg('premi_pupuk'),
            pot_koreksi: agg('pot_koreksi'),
            total_premi: agg('total_premi'),
            jumlah_upah_kotor: agg('jumlah_upah_kotor'),
            pot_pph21: agg('pot_pph21'), pot_kontan: agg('pot_kontan'), pot_thr: agg('pot_thr'), pot_pinjam: agg('pot_pinjam'), pot_kl: agg('pot_kl'), pot_bpjs_kes: agg('pot_bpjs_kes'), pot_bpjs_pek: agg('pot_bpjs_pek'), pot_bpjs_maj: agg('pot_bpjs_maj'),
            pot_bpjs_kesehatan_pekerja: agg('pot_bpjs_kesehatan_pekerja'),
            pot_bpjs_kesehatan_majikan: agg('pot_bpjs_kesehatan_majikan'),
            pot_bpjs_pensiun_pekerja: agg('pot_bpjs_pensiun_pekerja'),
            pot_bpjs_pensiun_majikan: agg('pot_bpjs_pensiun_majikan'),
            pot_bpjs_jumlah: agg('pot_bpjs_jumlah'),
            pot_bpjs_pekerja_total: agg('pot_bpjs_pekerja_total'),
            pot_spsi: agg('pot_spsi'),
            total_potongan: agg('total_potongan'), upah_bersih: agg('upah_bersih')
          }
          for (let i = 1; i <= 7; i++) {
            const f = `premi_dynamic_${i}`
            const sum = agg(f)
            if (sum > 0) grand[f] = sum
          }
          setPinnedBottom([grand])
        } else {
          setPinnedBottom([])
        }

        console.log('[Report] ✅ Tabel payroll siap ditampilkan!')
        console.log('[Report] 📊 Summary:', {
          total_employees: safe.length,
          grand_total_upah_bersih: agg('upah_bersih'),
          grand_total_potongan: agg('total_potongan'),
          gang_code: finalGangCode,
          period: `${monthValue}/${yearValue}`
        })

        setLoadingStatus('✅ Tabel payroll siap!')
      } catch (e) {
        if (DEV_MODE && !authToken) {
          try {
            const res = await login('admin', 'admin')
            setAuthToken(res.access_token)
            const leafFields = []
            const walk = (c) => { if (c.children) c.children.forEach(walk); else if (c.field) leafFields.push(c.field) }
            columnDefs.forEach(walk)
            // Use simple endpoint in development mode for fallback
            let fallbackData
            if (DEV_MODE) {
              fallbackData = await fetchReportRowsSimple(res.access_token, { month: monthValue, year: yearValue, gang_code: finalGangCode, skip: 0, limit: 50 })
            } else {
              const leafFields = []
              const walk = (c) => { if (c.children) c.children.forEach(walk); else if (c.field) leafFields.push(c.field) }
              columnDefs.forEach(walk)
              fallbackData = await fetchReportRowsBatched(res.access_token, { month: monthValue, year: yearValue, gang_code: finalGangCode, fields: leafFields, benchmark: true, monitor: false })
            }
            const computed = applyComputeToRows(fallbackData, computeRulesRef.current)
            setRows(computed)
            const safe = Array.isArray(computed) ? computed : []
            recomputeAutoHideMap(safe)
            const agg = (field) => Math.round(safe.reduce((a, b) => a + Number(b[field] || 0), 0))
            if (safe.length > 0) {
              const grand = {
                no: '', jenis_kelamin: '', nik: '', nama: 'GRAND TOTAL',
                upah_dasar: '', hari_kerja: agg('hari_kerja'), upah_pokok: agg('upah_pokok'),
                cuti_tahunan_hari: agg('cuti_tahunan_hari'), cuti_sakit_haid_hari: agg('cuti_sakit_haid_hari'), cuti_minggu_hari: agg('cuti_minggu_hari'), cuti_nasional_hari: agg('cuti_nasional_hari'), jumlah_hk: agg('jumlah_hk'),
                gaji_pokok: agg('gaji_pokok'), beras_rate: '', beras_jumlah: agg('beras_jumlah'), jabatan_rate: '', jabatan_jumlah: agg('jabatan_jumlah'), masa_kerja_tahun: '', masa_kerja_jumlah: agg('masa_kerja_jumlah'), lembur_jam: '', lembur_jumlah: agg('lembur_jumlah'), total_tunjangan: agg('total_tunjangan'),
                premi_brondol: agg('premi_brondol'), premi_pruning: agg('premi_pruning'), premi_angkut_material: agg('premi_angkut_material'), premi_angkut_tbs: agg('premi_angkut_tbs'), premi_harvesting: agg('premi_harvesting'), premi_harvesting_incentive: agg('premi_harvesting_incentive'), premi_pupuk: agg('premi_pupuk'),
                pot_koreksi: agg('pot_koreksi'),
                total_premi: agg('total_premi'),
                jumlah_upah_kotor: agg('jumlah_upah_kotor'),
                pot_pph21: agg('pot_pph21'), pot_kontan: agg('pot_kontan'), pot_thr: agg('pot_thr'), pot_pinjam: agg('pot_pinjam'), pot_kl: agg('pot_kl'), pot_bpjs_kes: agg('pot_bpjs_kes'), pot_bpjs_pek: agg('pot_bpjs_pek'), pot_bpjs_maj: agg('pot_bpjs_maj'),
                pot_bpjs_kesehatan_pekerja: agg('pot_bpjs_kesehatan_pekerja'),
                pot_bpjs_kesehatan_majikan: agg('pot_bpjs_kesehatan_majikan'),
                pot_bpjs_pensiun_pekerja: agg('pot_bpjs_pensiun_pekerja'),
                pot_bpjs_pensiun_majikan: agg('pot_bpjs_pensiun_majikan'),
                pot_bpjs_jumlah: agg('pot_bpjs_jumlah'),
                pot_bpjs_pekerja_total: agg('pot_bpjs_pekerja_total'),
                pot_spsi: agg('pot_spsi'),
                total_potongan: agg('total_potongan'), upah_bersih: agg('upah_bersih')
              }
              for (let i = 1; i <= 7; i++) {
                const f = `premi_dynamic_${i}`
                const sum = agg(f)
                if (sum > 0) grand[f] = sum
              }
              setPinnedBottom([grand])
            } else {
              setPinnedBottom([])
            }

            
          } catch (e2) {
            setError('Failed to load report data')
            setRows([])
            setPinnedBottom([])
          }
        } else {
          setError('Failed to load report data')
          setRows([])
          setPinnedBottom([])
        }
      } finally {
        setLoading(false)
        setLoadingStatus('')
        setCurrentEndpoint('')
        if (typeof onLoad === 'function') onLoad()
      }
    }
    const shouldRun = !dataInitRef.current && !!finalMonth && !!finalYear && !!finalGangCode
    console.log('[Report] 🔍 Checking condition untuk data loading:', {
      columnDefsLength: columnDefs?.length || 0,
      authToken: !!authToken,
      finalMonth,
      finalYear,
      finalGangCode,
      dataInitRef: dataInitRef.current,
      shouldRun
    })
    if (shouldRun) {
      dataInitRef.current = true
      console.log('[Report] ✅ Kondisi terpenuhi - Memulai data loading untuk', finalGangCode, finalMonth, '/', finalYear)
      run()
    } else {
      console.log('[Report] ⏸️ Kondisi belum terpenuhi, menunggu:', {
        hasColumns: (columnDefs?.length || 0) > 0,
        hasToken: !!authToken,
        hasMonth: !!finalMonth,
        hasYear: !!finalYear,
        hasGang: !!finalGangCode,
        alreadyInitialized: dataInitRef.current
      })
    }
  }, [authToken, finalMonth, finalYear, finalGangCode, columnDefs, overrideMonth, overrideYear])

  useEffect(() => {
    let active = true
    ;(async () => {
      try {
        if (authToken && finalGangCode) {
          const info = await fetchGangInfo(authToken, finalGangCode)
          if (active) setGangInfo(info)
        }
      } catch (_) {}
    })()
    return () => { active = false }
  }, [authToken, finalGangCode])

  // Separate useEffect to monitor columnDefs changes
  useEffect(() => {
    console.log('[Report] ColumnDefs changed:', {
      length: columnDefs?.length || 0,
      authToken: !!authToken,
      finalMonth,
      finalYear,
      finalGangCode,
      dataInitRef: dataInitRef.current
    })
  }, [columnDefs, authToken, finalMonth, finalYear, finalGangCode])

  useEffect(() => {
    let rafId = 0
    const loop = (t) => {
      fpsRef.current.frames += 1
      const dt = t - fpsRef.current.last
      if (dt >= 1000) {
        const fps = Math.round((fpsRef.current.frames * 1000) / dt)
        console.log('[Perf] FPS:', fps)
        fpsRef.current.last = t
        fpsRef.current.frames = 0
      }
      rafId = requestAnimationFrame(loop)
    }
    rafId = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(rafId)
  }, [])

  const baseCol = {
    resizable: true,
    sortable: true,
    filter: true,
    floatingFilter: true,
    flex: 1,
    minWidth: 100
  }
  const collectLeafFieldsFromColumns = cols => {
    const out = new Set()
    const walk = c => {
      if (c && Array.isArray(c.children)) {
        c.children.forEach(walk)
      } else if (c && c.field) {
        out.add(String(c.field))
      }
    }
    ;(Array.isArray(cols) ? cols : []).forEach(walk)
    return out
  }
  const insertAttendanceGroupIfMissing = cols => {
    const existing = collectLeafFieldsFromColumns(cols)

    // Struktur ABSENSI yang baru sesuai permintaan user
    const kehadiran = { field: 'hari_kerja', headerName: 'KEHADIRAN' }

    const ketidakhadiran = { headerName: 'KETIDAKHADIRAN', children: [
      { field: 'cuti_tahunan_hari', headerName: 'TAHUNAN (Izin)' },
      { field: 'cuti_sakit_haid_hari', headerName: 'SAKIT + HAID' },
      { field: 'cuti_minggu_hari', headerName: 'MINGGU' },
      { field: 'cuti_nasional_hari', headerName: 'NASIONAL' },
      { field: 'cuti_izin_hari', headerName: 'IZIN' },
      { field: 'tidak_hadir_cth', headerName: 'CTH' },
      { field: 'tidak_hadir_alpa', headerName: 'ALPA' },
      { field: 'total_ketidakhadiran', headerName: 'TOTAL' }
    ]}

    const jumlahHK = { field: 'jumlah_hk', headerName: 'JUMLAH HK' }

    // Build children dengan hanya field yang belum ada
    const buildKids = items => {
      const kids = []
      const itemsArray = Array.isArray(items) ? items : [items]
      for (const k of itemsArray) {
        if (!existing.has(k.field)) kids.push(k)
      }
      return kids
    }

    const kehadiranKids = buildKids(kehadiran)
    const ketidakhadiranKids = buildKids(ketidakhadiran.children)
    const jumlahHKKids = buildKids(jumlahHK)

    // Build struktur ABSENSI
    const attendanceChildren = []

    // 1. Tambahkan KEHADIRAN (dari hari_kerja)
    if (kehadiranKids.length > 0) {
      attendanceChildren.push(kehadiranKids[0])
    }

    // 2. Tambahkan KETIDAKHADIRAN
    if (ketidakhadiranKids.length > 0) {
      attendanceChildren.push({ headerName: ketidakhadiran.headerName, children: ketidakhadiranKids })
    }

    // 3. Tambahkan JUMLAH HK
    if (jumlahHKKids.length > 0) {
      attendanceChildren.push({ headerName: 'TOTAL HK', children: jumlahHKKids })
    }

    if (attendanceChildren.length === 0) return cols

    const attendance = { headerName: 'ABSENSI', children: attendanceChildren }
    let out = Array.isArray(cols) ? cols.slice() : []

    // Cari dan hapus duplikasi ABSENSI
    const absensiIdxs = []
    for (let i = 0; i < out.length; i++) {
      const item = out[i]
      if (item && Array.isArray(item.children)) {
        const name = String(item.headerName || '').toUpperCase()
        if (name.includes('ABSENSI')) absensiIdxs.push(i)
      }
    }

    if (absensiIdxs.length > 0) {
      // Ganti ABSENSI pertama dengan struktur baru
      const gi = absensiIdxs[0]
      out[gi] = { headerName: 'ABSENSI', children: attendanceChildren }

      // Hapus ABSENSI lainnya (duplikasi)
      for (let k = absensiIdxs.length - 1; k >= 1; k--) out.splice(absensiIdxs[k], 1)

      // Hapus field lama (hari_kerja, jumlah_hk) dari tempat lain
      for (let i = 0; i < out.length; i++) {
        const item = out[i]
        if (!item) continue
        if (Array.isArray(item.children)) {
          const prune = (list) => {
            for (let j = list.length - 1; j >= 0; j--) {
              const n = list[j]
              if (n && Array.isArray(n.children)) prune(n.children)
              else if (n && (String(n.field || '') === 'hari_kerja' || String(n.field || '') === 'jumlah_hk')) {
                list.splice(j, 1)
              }
            }
          }
          prune(item.children)
          if (item.children.length === 0) out.splice(i, 1), i--
        } else if (String(item.field || '') === 'hari_kerja' || String(item.field || '') === 'jumlah_hk') {
          out.splice(i, 1)
          i--
        }
      }
    } else {
      // Jika belum ada ABSENSI, tambahkan baru setelah KARYAWAN
      const empSectionIdx = out.findIndex(item => item && String(item.headerName || '').toUpperCase().includes('KARYAWAN'))
      const insertIdx = empSectionIdx >= 0 ? empSectionIdx + 1 : 1
      out.splice(insertIdx, 0, attendance)
    }

    // Clean up field yang tidak diinginkan
    const rr = removeLeavesBy(out, leaf => {
      const f = String(leaf.field || '')
      return f === 'cuti_izin_hari' // Hanya cuti_izin_hari yang dihapus, CTH dan ALPA dipertahankan
    })

    return rr.top
  }
  const removeLeavesBy = (cols, pred) => {
    const removed = []
    const walk = list => {
      for (let i = list.length - 1; i >= 0; i--) {
        const c = list[i]
        if (c && Array.isArray(c.children)) {
          walk(c.children)
          if (c.children.length === 0) list.splice(i, 1)
        } else if (c && pred(c)) {
          removed.push(c)
          list.splice(i, 1)
        }
      }
    }
    const top = Array.isArray(cols) ? cols.slice() : []
    walk(top)
    return { top, removed }
  }
  const relocateDynamicPotonganHeaders = cols => {
    const pred = leaf => {
      const f = String(leaf.field || '')
      const h = String(leaf.headerName || '').toUpperCase().trim()
      if (!f.startsWith('premi_dynamic_')) return false
      if (h.startsWith('POT')) return true
      if (h.includes('POTONG')) return true
      return false
    }
    const r = removeLeavesBy(cols, pred)
    if (r.removed.length === 0) return r.top
    const potonganGroupName = 'POTONGAN LAINNYA'
    let attached = false
    for (const g of r.top) {
      if (g && Array.isArray(g.children)) {
        const name = String(g.headerName || '').toUpperCase()
        if (name.includes('POTONGAN')) {
          g.children.push({ headerName: potonganGroupName, children: r.removed })
          attached = true
          break
        }
      }
    }
    if (!attached) {
      r.top.push({ headerName: potonganGroupName, children: r.removed })
    }
    return r.top
  }
  const removePlaceholderPotonganHeaders = cols => {
    const pred = leaf => {
      const f = String(leaf.field || '')
      const h = String(leaf.headerName || '').toUpperCase()
      const isPotTotal = /^pot_total_\d+$/.test(f)
      const isPotonganFamily = h.includes('POTONGAN') || f.startsWith('pot_') || f.startsWith('pot_dynamic_')
      const hasTestWord = h.includes('TEST') || h.includes('CONTOH') || h.includes('SAMPLE')
      return isPotTotal || (isPotonganFamily && hasTestWord)
    }
    const r = removeLeavesBy(cols, pred)
    return r.top
  }

  // Enhanced column definitions with proper formatting
  const formatLeaf = (col) => {
    const cfg = { ...col, ...baseCol }
    const moneyFields = ['upah_dasar','upah_pokok','gaji_pokok','beras_jumlah','jabatan_jumlah','masa_kerja_jumlah','lembur_jumlah','total_tunjangan','premi_brondol','premi_pruning','premi_angkut_material','premi_angkut_tbs','premi_harvesting','premi_harvesting_incentive','premi_pupuk','total_premi','jumlah_upah_kotor','pot_pph21','pot_koreksi','total_potongan','upah_bersih','premi_dynamic_1','premi_dynamic_2','premi_dynamic_3','premi_dynamic_4','premi_dynamic_5','premi_dynamic_6','premi_dynamic_7','pot_dynamic_1','pot_dynamic_2','pot_dynamic_3','pot_dynamic_4','pot_dynamic_5','pot_dynamic_6','pot_dynamic_7','pot_bpjs_kesehatan_pekerja','pot_bpjs_kesehatan_majikan','pot_bpjs_pensiun_pekerja','pot_bpjs_pensiun_majikan','pot_bpjs_pekerja_total','pot_spsi']
    const intFields = ['no','hari_kerja','cuti_tahunan_hari','cuti_sakit_haid_hari','cuti_minggu_hari','cuti_nasional_hari','tidak_hadir_cth','tidak_hadir_alpa','jumlah_hk','masa_kerja_tahun','lembur_jam']

    // Helper function for integer formatting
    const formatInteger = (value) => {
      const v = value
      if (v === null || v === undefined) return ''
      const n = Number(v)
      const iv = isNaN(n) ? 0 : Math.round(n)
      return new Intl.NumberFormat('id-ID',{ minimumFractionDigits:0, maximumFractionDigits:0 }).format(iv)
    }

    if (cfg.field && moneyFields.includes(cfg.field)) {
      cfg.valueFormatter = p => formatInteger(p.value)
      cfg.type = 'rightAligned'; cfg.cellStyle = { textAlign: 'right' }
    } else if (cfg.field && intFields.includes(cfg.field)) {
      cfg.valueFormatter = p => formatInteger(p.value)
      cfg.type = 'rightAligned'; cfg.cellStyle = { textAlign: 'right' }
    } else if (cfg.field && ['nama'].includes(cfg.field)) {
      cfg.cellStyle = { textAlign: 'left', fontWeight: 'bold' }; cfg.type = 'leftAligned'; cfg.pinned = 'left'
    } else if (cfg.field && ['nik','jenis_kelamin'].includes(cfg.field)) {
      cfg.cellStyle = { textAlign: 'center' }; cfg.type = 'centerAligned'
    } else if (cfg.field === 'phone') {
      cfg.hide = true  // Hide phone column completely
    } else if (cfg.field) {
      // Default formatter for any numeric field not explicitly listed
      cfg.valueFormatter = p => {
        if (p.value === null || p.value === undefined) return ''
        if (typeof p.value === 'number') {
          return formatInteger(p.value)
        }
        return p.value
      }
    }
    const f = String(cfg.field || '')
    const hdr = String(cfg.headerName || '').toUpperCase()
    const isDeduction = hdr.includes('POTONGAN') || f.startsWith('pot_') || f.startsWith('pot_dynamic_')
    const isIncome = hdr.includes('PENDAPATAN') || hdr.includes('TUNJANGAN') || hdr.includes('PREMI') || f.startsWith('premi_') || f.startsWith('premi_dynamic_') || f === 'gaji_pokok' || f === 'total_tunjangan' || f === 'total_premi' || f === 'jumlah_upah_kotor'
    if (isDeduction) {
      cfg.headerClass = (cfg.headerClass ? cfg.headerClass + ' ' : '') + 'hdr-deduction'
      cfg.cellClass = (cfg.cellClass ? cfg.cellClass + ' ' : '') + 'cell-deduction'
    } else if (isIncome) {
      cfg.headerClass = (cfg.headerClass ? cfg.headerClass + ' ' : '') + 'hdr-income'
      cfg.cellClass = (cfg.cellClass ? cfg.cellClass + ' ' : '') + 'cell-income'
    }
    const classMap = {
      jumlah_upah_kotor: 'col-jumlah-kotor',
      total_potongan: 'col-total-potongan',
      upah_bersih: 'col-upah-bersih',
      cuti_tahunan_hari: 'cuti-col-odd',
      cuti_sakit_haid_hari: 'cuti-col-even',
      cuti_minggu_hari: 'cuti-col-odd',
      cuti_nasional_hari: 'cuti-col-even'
    }
    if (cfg.field && classMap[cfg.field]) {
      cfg.cellClass = classMap[cfg.field]
    }

    if (cfg.field) {
      const neverHide = new Set([
        'no','nik','nama','jenis_kelamin','upah_bersih','jumlah_upah_kotor','total_tunjangan','total_premi','gaji_pokok','upah_pokok','hari_kerja','jumlah_hk',
        'cuti_tahunan_hari','cuti_sakit_haid_hari','cuti_minggu_hari','cuti_nasional_hari',
        'premi_brondol','premi_pruning'
      ])
      if (!neverHide.has(cfg.field)) {
        const hide = !!autoHideMapRef.current[cfg.field]
        if (hide) cfg.hide = true
      }
    }

    // Soft color header/text styling per header text to differentiate columns
    const hdrText = String(cfg.headerName || '').toUpperCase()
    if (hdrText.includes('PREMI HARVESTING') && hdrText.includes('INCENTIVE')) {
      cfg.headerClass = 'hdr-premi-hi'
      cfg.cellClass = (cfg.cellClass ? cfg.cellClass + ' ' : '') + 'cell-premi-hi'
    } else if (hdrText.includes('PRUNING')) {
      cfg.headerClass = 'hdr-premi-pruning'
      cfg.cellClass = (cfg.cellClass ? cfg.cellClass + ' ' : '') + 'cell-premi-pruning'
    } else if (hdrText.includes('BRONDOL')) {
      cfg.headerClass = 'hdr-premi-brondol'
      cfg.cellClass = (cfg.cellClass ? cfg.cellClass + ' ' : '') + 'cell-premi-brondol'
    } else if (hdrText.includes('ANGKUT TBS')) {
      cfg.headerClass = 'hdr-premi-angkut-tbs'
      cfg.cellClass = (cfg.cellClass ? cfg.cellClass + ' ' : '') + 'cell-premi-angkut-tbs'
    } else if (hdrText.includes('ANGKUT MATERIAL')) {
      cfg.headerClass = 'hdr-premi-angkut-material'
      cfg.cellClass = (cfg.cellClass ? cfg.cellClass + ' ' : '') + 'cell-premi-angkut-material'
    } else if (hdrText.includes('PUPUK')) {
      cfg.headerClass = 'hdr-premi-pupuk'
      cfg.cellClass = (cfg.cellClass ? cfg.cellClass + ' ' : '') + 'cell-premi-pupuk'
    }
    return cfg
  }

  

  const enhanceColumnsRecursive = (cols, depth = 0) => {
    if (!Array.isArray(cols)) return []
    const out = []
    for (const c of cols) {
      if (c.children && Array.isArray(c.children)) {
        const kids = enhanceColumnsRecursive(c.children, depth + 1)
        const visibleKids = kids.filter(k => !k.hide)
        if (visibleKids.length > 0) {
          out.push({ ...c, children: visibleKids, headerGroupComponent: 'HierHeaderGroup', headerClass: `hdr-level-${depth + 1}`, marryChildren: true })
        }
      } else {
        const leaf = formatLeaf(c)
        leaf.headerClass = `hdr-level-${depth + 1}`
        if (!leaf.hide) out.push(leaf)
      }
    }
    return out
  }

  const ensureHierarchicalOrThrow = (cols) => {
    const arr = Array.isArray(cols) ? cols : []
    const hasGroup = arr.some(c => Array.isArray(c.children) && c.children.length > 0)
    const allLeaves = arr.every(c => !Array.isArray(c.children) || c.children.length === 0)
    if (!hasGroup || allLeaves) {
      throw new Error('Hierarchical headers required: detected flat columns')
    }
  }

  const recomputeAutoHideMap = (dataRows) => {
    try {
      const neverHide = new Set([
        'no','nik','nama','jenis_kelamin','upah_bersih','jumlah_upah_kotor','total_tunjangan','total_premi','gaji_pokok','upah_pokok','hari_kerja','jumlah_hk',
        'cuti_tahunan_hari','cuti_sakit_haid_hari','cuti_minggu_hari','cuti_nasional_hari'
      ])
      const fields = new Set()
      for (const r of dataRows || []) {
        Object.keys(r || {}).forEach(f => fields.add(f))
      }
      const m = {}
      for (const f of fields) {
        if (neverHide.has(f)) { m[f] = false; continue }
        let allEmpty = true
        for (const r of dataRows || []) {
          const v = r[f]
          if (v === null || v === undefined) continue
          if (typeof v === 'number') { if (v !== 0) { allEmpty = false; break } }
          else {
            const sv = String(v).trim()
            if (sv !== '' && sv !== '0' && sv !== '0.0') { allEmpty = false; break }
          }
        }
        m[f] = allEmpty
      }
      autoHideMapRef.current = m
    } catch {}
  }

  const runValidation = async () => {
    try {
      const refPath = 'D\\Gawean Rebinmas\\Monitoring Database\\Plantware_Auto_Report\\Daftar_Upah_Reporting\\Engine_HTML_Templating\\template_report\\ui\\output\\daftar_upah_gang_H1H_real_dynamic_2025-11-16_13-58-11.html'
      const html = await fetchReferenceHtml(refPath, finalToken)
      setReferenceHtml(html)
      const getLeafHeaders = (cols) => {
        const out = []
        const walk = (c) => {
          if (c.children && Array.isArray(c.children)) {
            c.children.forEach(walk)
          } else if (c.headerName) {
            out.push(String(c.headerName).trim())
          }
        }
        cols.forEach(walk)
        return out
      }
      const columnDefsToUse = enhanceColumnsRecursive(columnDefs)
      const gridHeaders = getLeafHeaders(columnDefsToUse)

      const theadMatch = html.match(/<thead[\s\S]*?<\/thead>/i)
      let refLeaf = []
      if (theadMatch) {
        const thead = theadMatch[0]
        const trs = [...thead.matchAll(/<tr[\s\S]*?<\/tr>/gi)].map(m => m[0])
        if (trs.length > 0) {
          const last = trs[trs.length - 1]
          refLeaf = [...last.matchAll(/<th[^>]*>([\s\S]*?)<\/th>/gi)].map(m => m[1].replace(/<[^>]*>/g,'').trim()).filter(x => x.length > 0)
        }
      }
      let valuesDiff = null
      try {
        const tbodyMatch = html.match(/<tbody[\s\S]*?<\/tbody>/i)
        if (tbodyMatch) {
          const tbody = tbodyMatch[0]
          const rowsHtml = [...tbody.matchAll(/<tr[\s\S]*?<\/tr>/gi)].map(m => m[0])
          const grandRowHtml = rowsHtml.reverse().find(r => /GRAND\s+TOTAL/i.test(r)) || rowsHtml[0]
          const cells = [...grandRowHtml.matchAll(/<t[dh][^>]*>([\s\S]*?)<\/t[dh]>/gi)].map(m => m[1].replace(/<[^>]*>/g,'').trim())
          const num = (s) => {
            const cleaned = (s || '').replace(/[^0-9.-]/g,'')
            if (cleaned === '') return null
            const n = Number(cleaned)
            return isNaN(n) ? null : n
          }
          const refNums = cells.map(num).filter(v => v !== null)
          const treeLeaves = []
          const collect = (c) => { if (c.children) c.children.forEach(collect); else treeLeaves.push(c) }
          const columnDefsToUse = enhanceColumnsRecursive(columnDefs)
          columnDefsToUse.forEach(collect)
          const gridFields = treeLeaves.map(l => l.field).filter(f => f && typeof pinnedBottom[0]?.[f] !== 'undefined')
          const gridNums = gridFields.map(f => Number(pinnedBottom[0][f] || 0))
          const sameLen = refNums.length === gridNums.length
          const equal = sameLen && gridNums.every((v, i) => v === refNums[i])
          valuesDiff = { valuesMatch: equal, gridValues: gridNums, referenceValues: refNums }
        }
      } catch {}
      const diffs = {
        headersMatch: gridHeaders.length === refLeaf.length && gridHeaders.every((h, i) => h === refLeaf[i]),
        gridHeaders,
        referenceHeaders: refLeaf,
        values: valuesDiff
      }
      setValidationResult(diffs)
      setShowValidation(true)
    } catch (e) {
      console.error('Validation load failed', e)
    }
  }

  const rowClassRules = {
    'row-odd': params => params.node.rowIndex % 2 === 0,
    'row-even': params => params.node.rowIndex % 2 === 1,
    'grand-total': params => params.node.footer
  }

  const exportCsv = () => {
    gridRef.current.api.exportDataAsCsv({ fileName: 'daftar_upah.csv' })
  }
  const autoSizeAll = () => {
    const allIds = []
    gridRef.current.columnApi.getColumns().forEach(c => allIds.push(c.getId()))
    gridRef.current.columnApi.autoSizeColumns(allIds)
  }
  const locCodesSummary = Array.from(new Set((rows || []).map(r => r?.loc_code).filter(Boolean))).join(', ')

  
  // Proceed even if headers are unavailable; rely on columnDefs from backend

  if (error) return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '50vh',
      flexDirection: 'column',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{
        color: '#d32f2f',
        fontSize: '18px',
        fontWeight: '500',
        marginBottom: '20px',
        textAlign: 'center'
      }}>
        ❌ {error}
      </div>
      <button
        onClick={() => window.location.reload()}
        style={{
          padding: '10px 20px',
          background: '#1976d2',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '14px'
        }}
      >
        Retry
      </button>
    </div>
  )

  

  // Keep loading until first batch of rows is ready in infinite mode
  if (useInfinite && !firstBatchReady && !firstBatchAttempted) return (
    <LoadingScreen
      isLoading={true}
      message={loadingStatus || 'Loading payroll data...'}
      gangCode={finalGangCode}
      month={finalMonth}
      year={finalYear}
      logoUrl={import.meta.env.VITE_COMPANY_LOGO_URL || '/rebinmas-logo.png'}
      steps={[
        { name: currentEndpoint ? `Requesting ${currentEndpoint}` : 'Connecting to payroll database', duration: 1600 },
        { name: loadingStatus || `Fetching rows for Gang ${finalGangCode}`, duration: 2200 },
        { name: `${typeof finalMonth==='string' ? finalMonth : finalMonth+'/'+finalYear}`, duration: 1500 }
      ]}
    />
  )

  if (!useInfinite && (!rows || rows.length === 0)) return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '50vh',
      flexDirection: 'column',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{
        color: '#666',
        fontSize: '18px',
        fontWeight: '500',
        textAlign: 'center',
        marginBottom: '10px'
      }}>
        📋 No Data Found
      </div>
      <div style={{
        color: '#999',
        fontSize: '14px',
        textAlign: 'center'
      }}>
        No payroll data available for the selected parameters
      </div>
      <div style={{
        color: '#666',
        fontSize: '12px',
        textAlign: 'center',
        marginTop: '20px'
      }}>
        Gang: {finalGangCode || '-'} | {(overrideMonth || finalMonth) ? new Date(2000, (overrideMonth || finalMonth) - 1).toLocaleString('default', { month: 'long' }) : '-'} {(overrideYear || finalYear) || '-'}
      </div>
    </div>
  )

  return (
    <div className="grid-wrapper">
      {/* Enhanced Report Header */}
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '12px',
        padding: '24px',
        marginBottom: '20px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
        color: 'white',
        fontFamily: 'Arial, sans-serif'
      }}>
        {/* Main Title */}
        <div style={{ textAlign: 'center', marginBottom: '16px' }}>
          <h1 style={{
            margin: 0,
            fontSize: '24px',
            fontWeight: 'bold',
            letterSpacing: '1px',
            textTransform: 'uppercase'
          }}>
            DAFTAR UPAH KARYAWAN
          </h1>
          <div style={{ fontSize: '18px', marginTop: '4px', opacity: 0.9 }}>
            Periode: {(overrideMonth || finalMonth) ? new Date(2000, (overrideMonth || finalMonth) - 1).toLocaleString('id-ID', { month: 'long' }) : '-'} {(overrideYear || finalYear) || '-'}
          </div>
        </div>

        {/* Gang Information */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '20px'
        }}>
          <div style={{ flex: 1, minWidth: '300px' }}>
            <div style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>
              🏭 GANG: {finalGangCode || '-'}
              {gangInfo?.loc_code && <span style={{ marginLeft: '8px', fontSize: '14px', opacity: 0.8 }}>(LOC: {gangInfo.loc_code})</span>}
            </div>
            <div style={{ fontSize: '14px', opacity: 0.9, lineHeight: 1.4 }}>
              {gangInfo?.description || '-'}
            </div>
            <div style={{ fontSize: '12px', opacity: 0.8, marginTop: '4px' }}>
              📍 Division: {gangInfo?.division || '-'}
            </div>
          </div>

          {/* User Information */}
          <div style={{ textAlign: 'right', minWidth: '250px' }}>
            <div style={{ fontSize: '14px', marginBottom: '4px' }}>
              👤 {user?.full_name || user?.username}
            </div>
            <div style={{ fontSize: '12px', opacity: 0.8 }}>
              🆔 {user?.username}
            </div>
            <div style={{ fontSize: '12px', opacity: 0.8 }}>
              🏢 Division: {Array.isArray(user?.divisions) ? user.divisions.slice(0, 3).join(', ') + (user.divisions.length > 3 ? '...' : '') : '-'}
            </div>
            <div style={{ fontSize: '11px', opacity: 0.7, marginTop: '4px' }}>
              📅 {new Date().toLocaleString('id-ID', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </div>
          </div>

          {/* User Avatar */}
          <div style={{ textAlign: 'center' }}>
            {user?.avatar_url ? (
              <img
                src={user.avatar_url}
                alt="profile"
                style={{
                  width: '60px',
                  height: '60px',
                  borderRadius: '50%',
                  border: '3px solid rgba(255,255,255,0.3)',
                  objectFit: 'cover'
                }}
                onError={(e) => {
                  e.currentTarget.style.display = 'none'
                }}
              />
            ) : (
              <div style={{
                width: '60px',
                height: '60px',
                borderRadius: '50%',
                background: 'rgba(255,255,255,0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: '600',
                fontSize: '20px',
                border: '3px solid rgba(255,255,255,0.3)'
              }}>
                {(user?.full_name || user?.username || 'U').slice(0,1).toUpperCase()}
              </div>
            )}
          </div>
        </div>

        {/* Status Badge */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          marginTop: '16px',
          gap: '12px'
        }}>
          <span style={{
            background: 'rgba(255,255,255,0.2)',
            padding: '4px 12px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: '500'
          }}>
            ✅ Data Real-time
          </span>
          <span style={{
            background: 'rgba(76, 175, 80, 0.3)',
            padding: '4px 12px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: '500'
          }}>
            📊 {rows.length} Records
          </span>
        </div>
      </div>

      {/* Enhanced Control Panel */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px',
        padding: '12px 16px',
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        {/* Left Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={autoSizeAll}
            style={{
              padding: '8px 16px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => e.target.style.backgroundColor = '#0056b3'}
            onMouseOut={(e) => e.target.style.backgroundColor = '#007bff'}
          >
            📐 Auto Size Columns
          </button>

          <button
            onClick={exportCsv}
            style={{
              padding: '8px 16px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => e.target.style.backgroundColor = '#1e7e34'}
            onMouseOut={(e) => e.target.style.backgroundColor = '#28a745'}
          >
            📥 Export CSV
          </button>

          {/* Month Picker */}
          <input
            type="month"
            value={((overrideMonth || finalMonth) && (overrideYear || finalYear)) ? `${String(overrideYear || finalYear).padStart(4,'0')}-${String(overrideMonth || finalMonth).padStart(2,'0')}` : ''}
            onChange={(e) => {
              try {
                const [yyyy, mm] = (e.target.value || '').split('-')
                const m = Number(mm); const y = Number(yyyy)
                if (!isNaN(m) && !isNaN(y) && m >= 1 && m <= 12) {
                  setRows([])
                  setPinnedBottom([])
                  setOverrideMonth(m)
                  setOverrideYear(y)
                  dataInitRef.current = false
                }
              } catch {}
            }}
            style={{
              padding: '8px 12px',
              border: '1px solid #ddd',
              borderRadius: '6px',
              fontSize: '14px',
              minWidth: '160px',
              cursor: 'pointer'
            }}
          />

          {/* Gang Selection Dropdown */}
          <select
            value={finalGangCode || ''}
            onChange={(e) => {
              const newGangCode = e.target.value
              if (newGangCode && newGangCode !== finalGangCode) {
                // Trigger reload dengan gang baru
                setRows([])
                setPinnedBottom([])
                dataInitRef.current = false
                window.location.reload()
              }
            }}
            style={{
              padding: '8px 12px',
              border: '1px solid #ddd',
              borderRadius: '6px',
              fontSize: '14px',
              minWidth: '120px',
              cursor: 'pointer'
            }}
          >
            <option value="">🔄 Pilih Gang</option>
            <option value="H1H">H1H</option>
            <option value="H1M">H1M</option>
            <option value="H1T">H1T</option>
            <option value="A1H">A1H</option>
            <option value="A1M">A1M</option>
            <option value="A1T">A1T</option>
            <option value="A2M">A2M</option>
            <option value="A2P">A2P</option>
            <option value="A2T">A2T</option>
            <option value="A3H">A3H</option>
            <option value="A3M">A3M</option>
            <option value="A3P">A3P</option>
            <option value="A3T">A3T</option>
            <option value="E1H">E1H</option>
            <option value="E1M">E1M</option>
            <option value="E1T">E1T</option>
            <option value="E2H">E2H</option>
            <option value="E2M">E2M</option>
            <option value="E2T">E2T</option>
            <option value="E3H">E3H</option>
            <option value="E3M">E3M</option>
            <option value="E3P">E3P</option>
            <option value="E3T">E3T</option>
          </select>
        </div>

        {/* Right Status & Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ fontSize: '12px', color: '#666' }}>
            <span style={{ marginRight: '16px' }}>
              📊 Total Records: <strong>{rows.length}</strong>
            </span>
            <span style={{ marginRight: '16px' }}>
              🏭 Gang: <strong>{finalGangCode || '-'}</strong>
            </span>
            <span>
              📅 Periode: <strong>
                {(overrideMonth || finalMonth) ? new Date(2000, (overrideMonth || finalMonth) - 1).toLocaleString('id-ID', { month: 'short' }) : '-'} {overrideYear || finalYear || '-'}
              </strong>
            </span>
          </div>

          {/* Logout Button */}
          <button
            onClick={() => {
              if (window.confirm('Apakah Anda yakin ingin keluar?')) {
                logout()
                window.location.reload() // Reload to trigger login redirect
              }
            }}
            style={{
              padding: '6px 12px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '12px',
              cursor: 'pointer',
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
            onMouseOver={(e) => e.target.style.backgroundColor = '#c82333'}
            onMouseOut={(e) => e.target.style.backgroundColor = '#dc3545'}
            title="Keluar dari sistem"
          >
            🚪 Keluar
          </button>
        </div>
      </div>

      <div className="ag-theme-alpine" style={{ height: 700, width: '100%' }}>
        <AgGridReact
          ref={gridRef}
          columnDefs={Array.isArray(columnDefs) ? columnDefs : []}
          rowData={rows}
          rowModelType={'infinite'}
          cacheBlockSize={INFINITE_BATCH_SIZE}
          maxBlocksInCache={5}
          getRowId={params => params.data?.nik || params.data?.NIK || params.data?.no}
          defaultColDef={baseCol}
          rowClassRules={rowClassRules}
          pinnedBottomRowData={pinnedBottom}
          rowSelection={'single'}
          pagination={false}
          rowBuffer={20}
          enableRangeSelection={true}
          suppressRowClickSelection={true}
          animateRows={true}
          domLayout='normal'
          sideBar={{ toolPanels: ['columns', 'filters'], defaultToolPanel: 'columns' }}
          getRowHeight={params => params.node.rowIndex === 0 ? 40 : 30}
          onFirstDataRendered={(params) => {
            try {
              const cols = params.columnApi.getAllDisplayedColumns()
              const ids = cols.map(c => c.getColId())
              if (ids.length > 0) {
                // Auto-size all columns to fit content
                params.columnApi.autoSizeColumns(ids)
                // Ensure minimum width for readability
                cols.forEach(col => {
                  const currentWidth = col.getActualWidth()
                  if (currentWidth < 80) {
                    params.columnApi.setColumnWidth(col.getColId(), 80)
                  }
                })
              }
            } catch (e) {
              console.error('Error auto-sizing columns:', e)
            }
          }}
          frameworkComponents={{ HierHeaderGroup }}
          onGridReady={params => {
            if (rows.length > 0) {
              params.api.ensureIndexVisible(0, 'top')
            }
            // Log grid ready state for debugging
            const activeColumnDefs = Array.isArray(columnDefs) ? columnDefs : []
            console.log('[AG Grid] Grid ready with columns:', activeColumnDefs.length)
            console.log('[AG Grid] Rows loaded:', rows.length)
            console.log('[AG Grid] Hierarchy headers:', hierarchyHeaders)
            const datasource = {
              getRows: async rq => {
                const start = rq.startRow
                const end = rq.endRow
                const monthValue = typeof finalMonth === 'string' && finalMonth.includes('-') ? parseInt(finalMonth.split('-')[1], 10) : finalMonth
                const yearValue = typeof finalMonth === 'string' && finalMonth.includes('-') ? parseInt(finalMonth.split('-')[0], 10) : finalYear
                let batch = null
                if (start === 0 && initialRowsPreview && initialRowsPreview.length > 0) {
                  batch = initialRowsPreview.slice(0, end - start)
                } else {
                  batch = await fetchReportRowsSimple(authToken, { month: (overrideMonth || monthValue), year: (overrideYear || yearValue), gang_code: finalGangCode, skip: start, limit: end - start })
                  batch = applyComputeToRows(batch, computeRulesRef.current)
                }
                let rowCount = undefined
                try {
                  const c = await fetchReportCount(authToken, { month: (overrideMonth || monthValue), year: (overrideYear || yearValue), gang_code: finalGangCode })
                  if (c && typeof c.count === 'number') {
                    rowCount = Number(c.count)
                  }
                } catch {}
                rq.successCallback(batch || [], rowCount)
              }
            }
            params.api.setDatasource(datasource)
          }}
        />
      </div>
      {showValidation && (
        <div className="validation-panel" style={{ marginTop: 16 }}>
          <h3>Reference Preview</h3>
          <iframe title="reference" style={{ width: '100%', height: '60vh', border: '1px solid #ccc' }} srcDoc={referenceHtml} />
          {validationResult && (
            <div style={{ marginTop: 8, fontSize: 14 }}>
              <div>Headers match: <strong>{validationResult.headersMatch ? 'Yes' : 'No'}</strong></div>
              {validationResult.values && (
                <div>Grand totals match: <strong>{validationResult.values.valuesMatch ? 'Yes' : 'No'}</strong></div>
              )}
              {!validationResult.headersMatch && (
                <div style={{ display:'flex', gap:16, marginTop:8 }}>
                  <div style={{ flex:1 }}>
                    <div style={{ fontWeight: 600 }}>Grid Headers</div>
                    <div>{validationResult.gridHeaders.join(' | ')}</div>
                  </div>
                  <div style={{ flex:1 }}>
                    <div style={{ fontWeight: 600 }}>Reference Headers</div>
                    <div>{validationResult.referenceHeaders.join(' | ')}</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
  const createFallbackComputeRules = () => {
    return {
      cuti_total: { type: 'sum', fields: ['cuti_tahunan_hari','cuti_sakit_haid_hari','cuti_minggu_hari','cuti_nasional_hari'] },
      total_ketidakhadiran: { type: 'sum', fields: ['cuti_tahunan_hari','cuti_sakit_haid_hari','cuti_minggu_hari','cuti_nasional_hari','tidak_hadir_cth','tidak_hadir_alpa'] },
      hari_kerja: { type: 'sub', a: 'jumlah_hk', b: 'cuti_total' },
      gaji_pokok: { type: 'mul', a: 'hari_kerja', b: 'upah_dasar' },
      upah_pokok: { type: 'mul', a: 'hari_kerja', b: 'upah_dasar' },
      total_tunjangan: { type: 'sum', fields: ['beras_jumlah','jabatan_jumlah','masa_kerja_jumlah','lembur_jumlah'] },
      total_premi: { type: 'sum', fields: ['premi_pruning','premi_brondol'], match_prefix: 'premi_dynamic_' },
      jumlah_upah_kotor: { type: 'sum', fields: ['gaji_pokok','total_tunjangan','total_premi'] },
      total_potongan: { type: 'sum', fields: ['pot_bpjs_pek','pot_bpjs_maj','pot_bpjs_jumlah','pot_bpjs_kesehatan_pekerja','pot_bpjs_kesehatan_majikan','pot_bpjs_pensiun_pekerja','pot_bpjs_pensiun_majikan','pot_bpjs_pekerja_total','pot_spsi','pot_pph21','pot_koreksi'], match_prefix: 'pot_dynamic_' },
      upah_bersih: { type: 'sub', a: 'jumlah_upah_kotor', b: 'total_potongan' }
    }
  }
  const collectComputeRules = (defs) => {
    const rules = {}
    const walk = (c) => {
      if (c.children && Array.isArray(c.children)) {
        c.children.forEach(walk)
      } else {
        const f = c.field
        const comp = c.compute
        if (f && comp) rules[f] = comp
      }
    }
    if (Array.isArray(defs)) defs.forEach(walk)
    return rules
  }

  const applyComputeToRows = (rows, rules) => {
    if (!rows || rows.length === 0 || !rules) return rows || []
    const safe = Array.isArray(rows) ? rows : []
    const out = safe.map((row) => {
      const r = { ...row }
      for (const [field, spec] of Object.entries(rules)) {
        let val = 0
        if (spec.type === 'sum') {
          const list = Array.isArray(spec.fields) ? spec.fields : []
          for (const k of list) {
            const v = Number(r[k] ?? 0)
            if (!isNaN(v)) val += v
          }
          const pfx = spec.match_prefix
          if (pfx) {
            for (const key of Object.keys(r)) {
              if (key.startsWith(pfx)) {
                const v = Number(r[key] ?? 0)
                if (!isNaN(v)) val += v
              }
            }
          }
        } else if (spec.type === 'sub') {
          const a = Number(r[spec.a] ?? 0)
          const b = Number(r[spec.b] ?? 0)
          val = (isNaN(a) ? 0 : a) - (isNaN(b) ? 0 : b)
        } else if (spec.type === 'mul') {
          const a = Number(r[spec.a] ?? 0)
          const b = Number(r[spec.b] ?? 0)
          val = (isNaN(a) ? 0 : a) * (isNaN(b) ? 0 : b)
        } else if (spec.type === 'div') {
          const a = Number(r[spec.a] ?? 0)
          const b = Number(r[spec.b] ?? 0)
          val = (isNaN(a) ? 0 : a) / ((isNaN(b) || b === 0) ? 1 : b)
        }
        r[field] = Math.round(val)
      }
      return r
    })
    return out
  }
