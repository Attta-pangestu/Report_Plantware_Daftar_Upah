import { useEffect, useMemo, useRef, useState } from 'react'
import { AgGridReact } from 'ag-grid-react'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import '../styles/report.css'
import { fetchReportRows, fetchReportRowsBatched, fetchReportRowsSimple, fetchReportAggregate, fetchReportCount } from '../services/payrollService'
import { fetchDynamicHeaders, fetchColumnDefinitions, formatCurrency, formatNumber } from '../services/headerService'
import { login } from '../services/authService'
import { fetchReferenceHtml } from '../services/validationService'
import LoadingScreen from '../components/common/LoadingScreen'

// Check if running in development mode
const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true' || import.meta.env.DEV_MODE === 'true'

export default function Report({ token, month, year, gang_code, onLoad }) {
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
  const useInfinite = true
  const INFINITE_BATCH_SIZE = Number(import.meta.env.VITE_BATCH_SIZE || 50)
  const fpsRef = useRef({ last: performance.now(), frames: 0 })
  const aggregateInFlightRef = useRef(new Set())
  const dataInitRef = useRef(false)
  const [firstBatchReady, setFirstBatchReady] = useState(false)
  const [initialRowsPreview, setInitialRowsPreview] = useState([])
  const [firstBatchAttempted, setFirstBatchAttempted] = useState(false)
  useEffect(() => {
    async function loadHeaders() {
      setHeaderLoading(true)
      setLoadingStatus('Loading report headers...')
      setCurrentEndpoint('/payroll/headers')
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
        try {
          const headersData = await fetchDynamicHeaders(activeToken, monthValue, yearValue, finalGangCode)
          setLoadingStatus('Processing header structure...')
          setHeaders(headersData)

          // Extract hierarchy headers for 3-level header structure
          setLoadingStatus('Building 3-level header hierarchy...')
          if (headersData) {
            const tableStructure = headersData.table_structure || {}
            const generatedHeaders = tableStructure.generated_headers || {}
            setHierarchyHeaders({
              level1: generatedHeaders.level_1?.columns || [],
              level2: generatedHeaders.level_2?.columns || [],
              level3: generatedHeaders.level_3?.columns || []
            })
          } else {
            setHierarchyHeaders({ level1: [], level2: [], level3: [] })
          }
        } catch (hdrErr) {
          console.warn('[Report] Headers fetch failed; proceeding with columns only:', hdrErr?.message || hdrErr)
          setHeaders(null)
          setHierarchyHeaders({ level1: [], level2: [], level3: [] })
        }

        setLoadingStatus('Finalizing column definitions...')
        try {
          const cols = await fetchColumnDefinitions(activeToken, monthValue, yearValue, finalGangCode)
          const normalized = Array.isArray(cols) ? cols : (Array.isArray(cols?.columns) ? cols.columns : [])
          setColumnDefs(normalized)
          computeRulesRef.current = collectComputeRules(normalized)
          if (!Array.isArray(normalized) || normalized.length === 0) {
            computeRulesRef.current = createFallbackComputeRules()
          }
        } catch (colErr) {
          console.error('[Report] Column definitions fetch failed:', colErr)
          // Use fallback compute rules so rows can still be computed client-side
          computeRulesRef.current = createFallbackComputeRules()
          setError('Failed to load column definitions')
        }
      } catch (e) {
        console.error('Failed to initialize header loading:', e)
      } finally {
        setHeaderLoading(false)
        setLoadingStatus('Headers loaded successfully')
        setCurrentEndpoint('')
      }
    }

    loadHeaders()
  }, [authToken, finalMonth, finalYear, finalGangCode])

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

        console.log('[Report] Loading data rows for:', { monthValue, yearValue, finalGangCode })

        setLoadingStatus(`Fetching payroll data for Gang ${finalGangCode}...`)

        // Proceed to fetch data even if columnDefs are not yet ready; grid uses infinite model
        const leafFields = []
        const walk = (c) => { if (c.children) c.children.forEach(walk); else if (c.field) leafFields.push(c.field) }
        if (Array.isArray(columnDefs)) columnDefs.forEach(walk)

        console.log('[Report] Fetching data with fields:', leafFields.length, 'fields')

        let safe = []
        if (useInfinite) {
          const key = `${finalGangCode}:${yearValue}:${monthValue}`
          const existing = aggCacheRef.current.get(key)
          if (existing) {
            const pinned0 = { no: '', jenis_kelamin: '', nik: '', nama: 'GRAND TOTAL' }
            const assign0 = (k) => { pinned0[k] = Math.round(Number(existing[k] || 0)) }
            assign0('upah_pokok'); assign0('beras_jumlah'); assign0('jabatan_jumlah'); assign0('masa_kerja_jumlah'); assign0('lembur_jumlah'); assign0('total_tunjangan'); assign0('total_premi'); assign0('jumlah_upah_kotor'); assign0('pot_bpjs_jumlah'); assign0('total_potongan'); assign0('upah_bersih')
            setPinnedBottom([pinned0])
          }
          
          // Ensure auth token in dev mode for data fetch as well
          let activeToken = authToken
          if (!activeToken && DEV_MODE) {
            try {
              const res = await login('admin', 'admin')
              setAuthToken(res.access_token)
              activeToken = res.access_token
            } catch (autoErr) {
              console.error('[Report] Auto-login (data) failed:', autoErr)
            }
          }
          setFirstBatchAttempted(true)
          const preview = await fetchReportRowsSimple(activeToken, { month: monthValue, year: yearValue, gang_code: finalGangCode, skip: 0, limit: INFINITE_BATCH_SIZE })
          const computedPreview = applyComputeToRows(preview, computeRulesRef.current)
          setInitialRowsPreview(Array.isArray(computedPreview) ? computedPreview : [])
          setFirstBatchReady((Array.isArray(preview) ? preview.length : 0) > 0)
          safe = Array.isArray(computedPreview) ? computedPreview : []
        } else {
          const data = await fetchReportRowsSimple(authToken, { month: monthValue, year: yearValue, gang_code: finalGangCode, skip: 0, limit: INFINITE_BATCH_SIZE })
          const computed = applyComputeToRows(data, computeRulesRef.current)
          setRows(Array.isArray(computed) ? computed : [])
          safe = Array.isArray(computed) ? computed : []
        }
        
        // Debug: Tampilkan data baris pertama di console
        if (safe.length > 0) {
          console.log('🔍 Data Baris Pertama (JSON):')
          console.log(JSON.stringify(safe[0], null, 2))
          console.log('📊 Data Baris Pertama (Object):')
          console.table(safe[0])
          const keys = Object.keys(safe[0] || {})
          const sampleDistinct = {}
          keys.forEach(k => { sampleDistinct[k] = new Set(safe.slice(0, Math.min(10, safe.length)).map(r => r[k])).size })
          console.log('[Rows] Distinct counts across first 10 rows:', sampleDistinct)
        } else {
          console.warn('⚠️ Tidak ada data yang ditemukan')
        }
        const agg = (field) => Math.round(safe.reduce((a, b) => a + Number(b[field] || 0), 0))
        setPinnedBottom(safe.length > 0 ? [{
          no: '', jenis_kelamin: '', nik: '', nama: 'GRAND TOTAL',
          upah_dasar: '', hari_kerja: '', upah_pokok: agg('upah_pokok'),
          cuti_tahunan_hari: agg('cuti_tahunan_hari'), cuti_sakit_haid_hari: agg('cuti_sakit_haid_hari'), cuti_minggu_hari: agg('cuti_minggu_hari'), cuti_nasional_hari: agg('cuti_nasional_hari'), cuti_izin_hari: agg('cuti_izin_hari'), jumlah_hk: agg('jumlah_hk'),
          gaji_pokok: agg('gaji_pokok'), beras_rate: '', beras_jumlah: agg('beras_jumlah'), jabatan_rate: '', jabatan_jumlah: agg('jabatan_jumlah'), masa_kerja_tahun: '', masa_kerja_jumlah: agg('masa_kerja_jumlah'), lembur_jam: '', lembur_jumlah: agg('lembur_jumlah'), total_tunjangan: agg('total_tunjangan'),
          premi_brondol: agg('premi_brondol'), premi_pruning: agg('premi_pruning'), premi_angkut_material: agg('premi_angkut_material'), premi_angkut_tbs: agg('premi_angkut_tbs'), premi_harvesting: agg('premi_harvesting'), premi_harvesting_incentive: agg('premi_harvesting_incentive'), premi_pupuk: agg('premi_pupuk'),
          pot_koreksi: agg('pot_koreksi'),
          total_premi: agg('total_premi'),
          jumlah_upah_kotor: agg('jumlah_upah_kotor'),
          pot_pph21: agg('pot_pph21'), pot_kontan: agg('pot_kontan'), pot_thr: agg('pot_thr'), pot_pinjam: agg('pot_pinjam'), pot_kl: agg('pot_kl'), pot_bpjs_kes: agg('pot_bpjs_kes'), pot_bpjs_pek: agg('pot_bpjs_pek'), pot_bpjs_maj: agg('pot_bpjs_maj'),
          // BPJS detailed columns
          pot_bpjs_kesehatan_pekerja: agg('pot_bpjs_kesehatan_pekerja'),
          pot_bpjs_kesehatan_majikan: agg('pot_bpjs_kesehatan_majikan'),
          pot_bpjs_pensiun_pekerja: agg('pot_bpjs_pensiun_pekerja'),
          pot_bpjs_pensiun_majikan: agg('pot_bpjs_pensiun_majikan'),
          pot_bpjs_jumlah: agg('pot_bpjs_jumlah'),
          pot_bpjs_pekerja_total: agg('pot_bpjs_pekerja_total'),
          // SPSI column
          pot_spsi: agg('pot_spsi'),
          pot_total_1: agg('pot_total_1'), pot_total_2: agg('pot_total_2'), pot_total_3: agg('pot_total_3'), pot_total_4: agg('pot_total_4'), total_potongan: agg('total_potongan'), upah_bersih: agg('upah_bersih'), tidak_hadir_cth: agg('tidak_hadir_cth'), tidak_hadir_alpa: agg('tidak_hadir_alpa')
        }] : [])

        setLoadingStatus('Table ready')
      } catch (e) {
        if (DEV_MODE && !authToken) {
          try {
            const res = await login('admin', 'admin')
            setAuthToken(res.access_token)
            const leafFields = []
            const walk = (c) => { if (c.children) c.children.forEach(walk); else if (c.field) leafFields.push(c.field) }
            columnDefs.forEach(walk)
            // Use simple endpoint in development mode for fallback
            let data
            if (DEV_MODE) {
              data = await fetchReportRowsSimple(res.access_token, { month: monthValue, year: yearValue, gang_code: finalGangCode, skip: 0, limit: 50 })
            } else {
              const leafFields = []
              const walk = (c) => { if (c.children) c.children.forEach(walk); else if (c.field) leafFields.push(c.field) }
              columnDefs.forEach(walk)
              data = await fetchReportRowsBatched(res.access_token, { month: monthValue, year: yearValue, gang_code: finalGangCode, fields: leafFields, benchmark: true, monitor: false })
            }
            const computed = applyComputeToRows(data, computeRulesRef.current)
            setRows(computed)
            const safe = Array.isArray(computed) ? computed : []
            const agg = (field) => Math.round(safe.reduce((a, b) => a + Number(b[field] || 0), 0))
            setPinnedBottom(safe.length > 0 ? [{
              no: '', jenis_kelamin: '', nik: '', nama: 'GRAND TOTAL',
              upah_dasar: '', hari_kerja: '', upah_pokok: agg('upah_pokok'),
              cuti_tahunan_hari: agg('cuti_tahunan_hari'), cuti_sakit_haid_hari: agg('cuti_sakit_haid_hari'), cuti_minggu_hari: agg('cuti_minggu_hari'), cuti_nasional_hari: agg('cuti_nasional_hari'), cuti_izin_hari: agg('cuti_izin_hari'), jumlah_hk: agg('jumlah_hk'),
              gaji_pokok: agg('gaji_pokok'), beras_rate: '', beras_jumlah: agg('beras_jumlah'), jabatan_rate: '', jabatan_jumlah: agg('jabatan_jumlah'), masa_kerja_tahun: '', masa_kerja_jumlah: agg('masa_kerja_jumlah'), lembur_jam: '', lembur_jumlah: agg('lembur_jumlah'), total_tunjangan: agg('total_tunjangan'),
              premi_brondol: agg('premi_brondol'), premi_pruning: agg('premi_pruning'), premi_angkut_material: agg('premi_angkut_material'), premi_angkut_tbs: agg('premi_angkut_tbs'), premi_harvesting: agg('premi_harvesting'), premi_harvesting_incentive: agg('premi_harvesting_incentive'), premi_pupuk: agg('premi_pupuk'),
              pot_koreksi: agg('pot_koreksi'),
              total_premi: agg('total_premi'),
              jumlah_upah_kotor: agg('jumlah_upah_kotor'),
              pot_pph21: agg('pot_pph21'), pot_kontan: agg('pot_kontan'), pot_thr: agg('pot_thr'), pot_pinjam: agg('pot_pinjam'), pot_kl: agg('pot_kl'), pot_bpjs_kes: agg('pot_bpjs_kes'), pot_bpjs_pek: agg('pot_bpjs_pek'), pot_bpjs_maj: agg('pot_bpjs_maj'),
              // BPJS detailed columns
              pot_bpjs_kesehatan_pekerja: agg('pot_bpjs_kesehatan_pekerja'),
              pot_bpjs_kesehatan_majikan: agg('pot_bpjs_kesehatan_majikan'),
              pot_bpjs_pensiun_pekerja: agg('pot_bpjs_pensiun_pekerja'),
              pot_bpjs_pensiun_majikan: agg('pot_bpjs_pensiun_majikan'),
              pot_bpjs_jumlah: agg('pot_bpjs_jumlah'),
              pot_bpjs_pekerja_total: agg('pot_bpjs_pekerja_total'),
              // SPSI column
              pot_spsi: agg('pot_spsi'),
              pot_total_1: agg('pot_total_1'), pot_total_2: agg('pot_total_2'), pot_total_3: agg('pot_total_3'), pot_total_4: agg('pot_total_4'), total_potongan: agg('total_potongan'), upah_bersih: agg('upah_bersih'), tidak_hadir_cth: agg('tidak_hadir_cth'), tidak_hadir_alpa: agg('tidak_hadir_alpa')
            }] : [])

            
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
    console.log('[Report] Checking condition for data loading:', {
      columnDefsLength: columnDefs?.length || 0,
      shouldRun: !dataInitRef.current && !!authToken && !!finalMonth && !!finalYear && !!finalGangCode
    })
    if (!dataInitRef.current && !!authToken && !!finalMonth && !!finalYear && !!finalGangCode) {
      dataInitRef.current = true
      console.log('[Report] Condition met, executing data loading...')
      run()
    } else {
      console.log('[Report] Condition NOT met, skipping data loading')
    }
  }, [authToken, finalMonth, finalYear, finalGangCode, columnDefs])

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

  // Enhanced column definitions with proper formatting
  const formatLeaf = (col) => {
    const cfg = { ...col, ...baseCol }
    const moneyFields = ['upah_dasar','upah_pokok','gaji_pokok','beras_jumlah','jabatan_jumlah','masa_kerja_jumlah','lembur_jumlah','total_tunjangan','premi_brondol','premi_pruning','premi_angkut_material','premi_angkut_tbs','premi_harvesting','premi_harvesting_incentive','premi_pupuk','total_premi','jumlah_upah_kotor','pot_pph21','pot_kontan','pot_thr','pot_pinjam','pot_kl','pot_bpjs_kes','pot_bpjs_pek','pot_bpjs_maj','pot_total_1','pot_total_2','pot_total_3','pot_total_4','pot_koreksi','total_potongan','upah_bersih']
    const intFields = ['no','hari_kerja','cuti_tahunan_hari','cuti_sakit_haid_hari','cuti_minggu_hari','cuti_nasional_hari','cuti_izin_hari','jumlah_hk','masa_kerja_tahun','lembur_jam','tidak_hadir_cth','tidak_hadir_alpa']
    if (cfg.field && moneyFields.includes(cfg.field)) {
      cfg.valueFormatter = p => {
        const v = p.value
        if (v === null || v === undefined || v === 0) return '-'
        // Pastikan nilai bulat tanpa desimal
        const roundedValue = Math.round(Number(v))
        return new Intl.NumberFormat('id-ID',{style:'currency',currency:'IDR',minimumFractionDigits:0,maximumFractionDigits:0}).format(roundedValue)
      }
      cfg.type = 'rightAligned'; cfg.cellStyle = { textAlign: 'right' }
    } else if (cfg.field && intFields.includes(cfg.field)) {
      cfg.valueFormatter = p => { const v = p.value; if (v === null || v === undefined || v === 0) return '-'; return new Intl.NumberFormat('id-ID').format(v) }
      cfg.type = 'rightAligned'; cfg.cellStyle = { textAlign: 'right' }
    } else if (cfg.field && ['nama'].includes(cfg.field)) {
      cfg.cellStyle = { textAlign: 'left' }; cfg.type = 'leftAligned'
    } else if (cfg.field && ['nik','jenis_kelamin'].includes(cfg.field)) {
      cfg.cellStyle = { textAlign: 'center' }; cfg.type = 'centerAligned'
    }
    const classMap = {
      jumlah_upah_kotor: 'col-jumlah-kotor',
      total_potongan: 'col-total-potongan',
      upah_bersih: 'col-upah-bersih',
      cuti_tahunan_hari: 'cuti-col-odd',
      cuti_sakit_haid_hari: 'cuti-col-even',
      cuti_minggu_hari: 'cuti-col-odd',
      cuti_nasional_hari: 'cuti-col-even',
      cuti_izin_hari: 'cuti-col-odd'
    }
    if (cfg.field && classMap[cfg.field]) {
      cfg.cellClass = classMap[cfg.field]
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

  

  const enhanceColumnsRecursive = (cols) => {
    if (!Array.isArray(cols)) return []
    return cols.map(c => {
      if (c.children && Array.isArray(c.children)) {
        return { ...c, children: enhanceColumnsRecursive(c.children) }
      }
      return formatLeaf(c)
    })
  }

  // Enhanced column defs hanya di-update sekali saat autohide diproses
  // Tidak menggunakan useMemo untuk mencegah re-komputasi berulang

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
    'grand-total': params => params.node.footer,
    'first-row': params => params.node.rowIndex === 0
  }

  const exportCsv = () => {
    gridRef.current.api.exportDataAsCsv({ fileName: 'daftar_upah.csv' })
  }
  const autoSizeAll = () => {
    const allIds = []
    gridRef.current.columnApi.getColumns().forEach(c => allIds.push(c.getId()))
    gridRef.current.columnApi.autoSizeColumns(allIds)
  }
  const scrollToFirstRow = () => {
    if (gridRef.current && rows.length > 0) {
      gridRef.current.api.ensureIndexVisible(0, 'top')
      gridRef.current.api.clearFocusedCell()
      gridRef.current.api.setFocusedCell(0, 'no')

      // Debug: Tampilkan data baris pertama di console saat tombol diklik
      console.log('🔍 DEBUG - Data Baris Pertama (JSON):')
      console.log(JSON.stringify(rows[0], null, 2))
      console.log('📊 DEBUG - Data Baris Pertama (Object):')
      console.table(rows[0])
      console.log('📈 Total baris data:', rows.length)
    } else {
      console.warn('⚠️ Tidak ada data untuk di-debug')
    }
  }

  // Only show loading when headers are actively being loaded
  if (headerLoading) return (
    <LoadingScreen
      isLoading={true}
      message={loadingStatus || (headerLoading ? 'Loading report configuration...' : 'Analyzing payroll data...')}
      gangCode={finalGangCode}
      month={finalMonth}
      year={finalYear}
      logoUrl={import.meta.env.VITE_COMPANY_LOGO_URL || '/rebinmas-logo.png'}
      steps={headerLoading ? [
        { name: currentEndpoint ? `Requesting ${currentEndpoint}` : `Loading headers for Gang ${finalGangCode}`, duration: 1800 },
        { name: `Fetching dynamic columns for ${finalGangCode}`, duration: 2200 },
        { name: loadingStatus || 'Building column hierarchy', duration: 1500 }
      ] : [
        { name: currentEndpoint ? `Requesting ${currentEndpoint}` : 'Connecting to payroll database', duration: 1500 },
        { name: loadingStatus || `Loading rows for Gang ${finalGangCode}`, duration: 2800 },
        { name: `Aggregating ${typeof finalMonth==='string' ? finalMonth : finalMonth+'/'+finalYear}`, duration: 2500 }
      ]}
    />
  )
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

  // Render loading screen until column definitions are ready
  if (headerLoading || !Array.isArray(columnDefs) || columnDefs.length === 0) return (
    <LoadingScreen
      month={finalMonth}
      year={finalYear}
      logoUrl={import.meta.env.VITE_COMPANY_LOGO_URL || '/rebinmas-logo.png'}
      steps={[
        { name: currentEndpoint ? `Requesting ${currentEndpoint}` : 'Waiting for header API response', duration: 1600 },
        { name: loadingStatus || 'Processing header structure...', duration: 2000 },
        { name: 'Building table columns', duration: 1400 }
      ]}
    />
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
        Gang: {finalGangCode || '-'} | {finalMonth ? new Date(2000, finalMonth - 1).toLocaleString('default', { month: 'long' }) : '-'} {finalYear || '-'}
      </div>
    </div>
  )

  return (
    <div className="grid-wrapper">
      {headers && (
        <div className="report-header" style={{
          padding: '16px',
          backgroundColor: '#f5f5f5',
          marginBottom: '16px',
          borderRadius: '4px',
          border: '1px solid #ddd'
        }}>
          <h2 style={{ margin: '0 0 8px 0', fontSize: '18px', fontWeight: 'bold' }}>
            {headers.report_info?.title || 'LAPORAN DAFTAR UPAH'}
          </h2>
          <div style={{ fontSize: '14px', color: '#666' }}>
            <div>Gang: <strong>{headers.report_info?.gang || gang_code || '-'}</strong></div>
            <div>Generated: <strong>{headers.report_info?.generated_date || '-'}</strong></div>
            <div>Database: <strong>{headers.report_info?.database || '-'}</strong></div>
          </div>
        </div>
      )}

      <div style={{ marginBottom: 8 }}>
        <button onClick={scrollToFirstRow} style={{ backgroundColor: '#4caf50', color: 'white', border: 'none', padding: '4px 8px', marginRight: 8 }}>
          Debug First Row
        </button>
        <button onClick={exportCsv}>Export CSV</button>
        <button onClick={autoSizeAll} style={{ marginLeft: 8 }}>Auto-size Columns</button>
        <button onClick={runValidation} style={{ marginLeft: 8, backgroundColor: '#2196f3', color: 'white', border: 'none', padding: '4px 8px' }}>Validate vs Reference</button>
      </div>

      <div className="ag-theme-alpine" style={{ height: 700, width: '100%' }}>
        <AgGridReact
          ref={gridRef}
          // Always use enhanced column definitions with auto-hide logic applied
          columnDefs={enhanceColumnsRecursive(Array.isArray(columnDefs) ? columnDefs : [])}
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
          onFirstDataRendered={() => {}}
          onGridReady={params => {
            if (rows.length > 0) {
              params.api.ensureIndexVisible(0, 'top')
            }
            // Log grid ready state for debugging
            const activeColumnDefs = enhanceColumnsRecursive(columnDefs)
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
                  batch = await fetchReportRowsSimple(authToken, { month: monthValue, year: yearValue, gang_code: finalGangCode, skip: start, limit: end - start })
                  batch = applyComputeToRows(batch, computeRulesRef.current)
                }
                let rowCount = undefined
                try {
                  const key = `${finalGangCode}:${yearValue}:${monthValue}`
                  const cached = aggCacheRef.current.get(key)
                  if (cached && typeof cached.count === 'number') {
                    rowCount = Number(cached.count)
                  } else {
                    const c = await fetchReportCount(authToken, { month: monthValue, year: yearValue, gang_code: finalGangCode })
                    if (c && typeof c.count === 'number') {
                      rowCount = Number(c.count)
                      const existing = aggCacheRef.current.get(key) || {}
                      aggCacheRef.current.set(key, { ...existing, count: rowCount })
                    }
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
      total_tunjangan: { type: 'sum', fields: ['beras_jumlah','jabatan_jumlah','masa_kerja_jumlah','lembur_jumlah'] },
      total_premi: { type: 'sum', fields: ['premi_pruning','premi_brondol','premi_angkut_material','premi_angkut_tbs','premi_harvesting','premi_harvesting_incentive','premi_pupuk'], match_prefix: 'premi_dynamic_' },
      jumlah_upah_kotor: { type: 'sum', fields: ['gaji_pokok','total_tunjangan','total_premi'] },
      total_potongan: { type: 'sum', fields: ['pot_bpjs_pek','pot_bpjs_maj','pot_bpjs_jumlah','pot_bpjs_kesehatan_pekerja','pot_bpjs_kesehatan_majikan','pot_bpjs_pensiun_pekerja','pot_bpjs_pensiun_majikan','pot_bpjs_pekerja_total','pot_spsi','pot_pph21','pot_koreksi'] },
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
        r[field] = val
      }
      return r
    })
    return out
  }
