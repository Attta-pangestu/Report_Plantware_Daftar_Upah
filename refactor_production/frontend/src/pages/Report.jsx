import { useEffect, useMemo, useRef, useState } from 'react'
import { AgGridReact } from 'ag-grid-react'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import '../styles/report.css'
import { fetchReportRows } from '../services/payrollService'
import { fetchColumnDefinitions, fetchDynamicHeaders, formatCurrency, formatNumber } from '../services/headerService'
import { login } from '../services/authService'
import { fetchReferenceHtml } from '../services/validationService'
import LoadingScreen from '../components/common/LoadingScreen'

// Check if running in development mode
const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true' || import.meta.env.DEV_MODE === 'true'

export default function Report({ token, month, year, gang_code, onLoad }) {
  // In development mode, use default values if props are not provided
  const [authToken, setAuthToken] = useState(token || null)
  const devToken = DEV_MODE ? (authToken || token) : token
  const devMonth = DEV_MODE ? (month || '2025-05') : month
  const devYear = DEV_MODE ? (year || 2025) : year
  const devGangCode = DEV_MODE ? (gang_code || 'H1H') : gang_code
  
  const finalToken = devToken || token
  const finalMonth = devMonth || month
  const finalYear = devYear || year
  const finalGangCode = devGangCode || gang_code
  const [rows, setRows] = useState([])
  const [pinnedBottom, setPinnedBottom] = useState([])
  const [columnDefs, setColumnDefs] = useState([])
  const [headers, setHeaders] = useState(null)
  const [hierarchyHeaders, setHierarchyHeaders] = useState(null)
  const [enhancedColumnDefs, setEnhancedColumnDefs] = useState([]) // Cache hasil enhancement
  const [autohideProcessed, setAutohideProcessed] = useState(false) // Flag untuk mencegah proses ulang
  const [loading, setLoading] = useState(false)
  const [headerLoading, setHeaderLoading] = useState(false)
  const [error, setError] = useState('')
  const [showValidation, setShowValidation] = useState(false)
  const [referenceHtml, setReferenceHtml] = useState('')
  const [validationResult, setValidationResult] = useState(null)
  const gridRef = useRef(null)
  useEffect(() => {
    async function loadHeaders() {
      setHeaderLoading(true)
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
        const [headersData, columnDefsData] = await Promise.all([
          fetchDynamicHeaders(finalToken, monthValue, yearValue, finalGangCode),
          fetchColumnDefinitions(finalToken, monthValue, yearValue, finalGangCode)
        ])
        setHeaders(headersData)

        // Extract hierarchy headers for 3-level header structure
        const tableStructure = headersData.table_structure || {}
        const generatedHeaders = tableStructure.generated_headers || {}

        setHierarchyHeaders({
          level1: generatedHeaders.level_1?.columns || [],
          level2: generatedHeaders.level_2?.columns || [],
          level3: generatedHeaders.level_3?.columns || []
        })

        const gen = headersData?.table_structure?.generated_headers || {}
        const l1 = gen?.level_1?.columns || []
        const l2 = gen?.level_2?.columns || []
        const l3 = gen?.level_3?.columns || []
        const l2ByParent = {}
        l2.forEach(c => { const p = c.parent; if (!l2ByParent[p]) l2ByParent[p] = []; l2ByParent[p].push(c) })
        const l3ByParent = {}
        l3.forEach(c => { const p = c.parent; if (!l3ByParent[p]) l3ByParent[p] = []; l3ByParent[p].push(c) })
        const mapField = (id) => {
          const m = {
            no:'no', gender:'jenis_kelamin', nik:'nik', name:'nama', upah_dasar:'upah_dasar', hari_kerja:'hari_kerja', upah_pokok:'upah_pokok', jml_hk:'jumlah_hk', gaji_pokok:'gaji_pokok', total_tunjangan:'total_tunjangan', upah_bersih:'upah_bersih',
            cuti_tahunan_unit:'cuti_tahunan_hari', cuti_sakit_haid_unit:'cuti_sakit_haid_hari', cuti_minggu_unit:'cuti_minggu_hari', cuti_nasional_unit:'cuti_nasional_hari', cuti_izin_unit:'cuti_izin_hari',
            beras_rate:'beras_rate', beras_jumlah:'beras_jumlah', jabatan_rate:'jabatan_rate', jabatan_jumlah:'jabatan_jumlah', masa_kerja_lama:'masa_kerja_tahun', masa_kerja_jumlah:'masa_kerja_jumlah', lembur_jam:'lembur_jam', lembur_jumlah:'lembur_jumlah',
            brondol_jumlah:'premi_brondol', pruning_jumlah:'premi_pruning', premi_angkut_material_jumlah:'premi_angkut_material', premi_angkut_tbs_jumlah:'premi_angkut_tbs', premi_harvesting_jumlah:'premi_harvesting', premi_harvesting_incentive_jumlah:'premi_harvesting_incentive', premi_pupuk_jumlah:'premi_pupuk',
            premi_koreksi_jumlah:'premi_koreksi', bpjs_pensiun_pekerja:'pot_bpjs_pensiun_pekerja', bpjs_pensiun_majikan:'pot_bpjs_pensiun_majikan',
            pph21:'pot_pph21', potongan_kontan:'pot_kontan', thr:'pot_thr', pinjam:'pot_pinjam', kl:'pot_kl', bpjs_kes:'pot_bpjs_kes', bpjs_pek:'pot_bpjs_pek', bpjs_maj:'pot_bpjs_maj', total1:'pot_total_1', total2:'pot_total_2', total3:'pot_total_3', total4:'pot_total_4', cth:'tidak_hadir_cth', alpa:'tidak_hadir_alpa'
          }
          return m[id] || id
        }
        const built = []
        const leftColumns = []
        const otherColumns = []

        l1.forEach(c1 => {
          const childrenIds = c1.children || []
          if (!childrenIds || childrenIds.length === 0) {
            const field = mapField(c1.id)
            if (field) {
              const colDef = { field, headerName: c1.text, pinned: ['no','nama'].includes(field) ? 'left' : undefined }
              if (['no','nama'].includes(field)) {
                leftColumns.push(colDef)
              } else {
                otherColumns.push(colDef)
              }
            }
            return
          }
          const group2 = (l2ByParent[c1.id] || []).map(c2 => {
            const isPremiHI = String(c2.text || '').toUpperCase().includes('PREMI HARVESTING') && String(c2.text || '').toUpperCase().includes('INCENTIVE')
            let leaves = (l3ByParent[c2.id] || []).map(c3 => ({ field: mapField(c3.id), headerName: c3.text }))
            if (isPremiHI) {
              leaves = leaves.map(leaf => ({ ...leaf, field: 'premi_harvesting_incentive' }))
            }
            return { headerName: c2.text, children: leaves }
          })
          otherColumns.push({ headerName: c1.text, children: group2 })
        })

        // Pastikan kolom utama (no, gender, nik, name) berada di paling kiri dan selalu tampil
        const essentialColumns = []
        const remainingLeftColumns = []

        leftColumns.forEach(col => {
          if (['no', 'jenis_kelamin', 'nik', 'nama'].includes(col.field)) {
            essentialColumns.push(col)
          } else {
            remainingLeftColumns.push(col)
          }
        })

        // Urutkan essential columns: no, gender, nik, nama
        const orderedEssential = []
        if (essentialColumns.some(c => c.field === 'no')) {
          orderedEssential.push(essentialColumns.find(c => c.field === 'no'))
        }
        if (essentialColumns.some(c => c.field === 'jenis_kelamin')) {
          orderedEssential.push(essentialColumns.find(c => c.field === 'jenis_kelamin'))
        }
        if (essentialColumns.some(c => c.field === 'nik')) {
          orderedEssential.push(essentialColumns.find(c => c.field === 'nik'))
        }
        if (essentialColumns.some(c => c.field === 'nama')) {
          orderedEssential.push(essentialColumns.find(c => c.field === 'nama'))
        }

        built.push(...orderedEssential, ...remainingLeftColumns, ...otherColumns)
        const hasChildren = Array.isArray(columnDefsData) && columnDefsData.some(c => c.children)
        const chosen = hasChildren ? columnDefsData : built
        const leafFields = []
        const walk = (c) => { if (c.children) c.children.forEach(walk); else if (c.field) leafFields.push(c.field) }
        chosen.forEach(walk)
        const dupFields = leafFields.filter((f, i, a) => a.indexOf(f) !== i)
        console.log('[Columns] Leaf fields count:', leafFields.length)
        if (dupFields.length > 0) {
          console.warn('[Columns] Duplicate fields detected:', dupFields)
        }
        setColumnDefs(chosen)
        try {
          await fetchReportRows(finalToken, { month: monthValue, year: yearValue, gang_code: finalGangCode, fields: ['nik'], limit: 1, benchmark: false, monitor: false })
        } catch (prefetchErr) {}
      } catch (e) {
        console.error('Failed to load headers:', e)
        if (DEV_MODE && !finalToken) {
          try {
            const res = await login('admin', 'admin')
            setAuthToken(res.access_token)
            const [headersData, columnDefsData] = await Promise.all([
              fetchDynamicHeaders(res.access_token, monthValue, yearValue, finalGangCode),
              fetchColumnDefinitions(res.access_token, monthValue, yearValue, finalGangCode)
            ])
            setHeaders(headersData)
            const gen = headersData?.table_structure?.generated_headers || {}
            const l1 = gen?.level_1?.columns || []
            const l2 = gen?.level_2?.columns || []
            const l3 = gen?.level_3?.columns || []
            const l2ByParent = {}
            l2.forEach(c => { const p = c.parent; if (!l2ByParent[p]) l2ByParent[p] = []; l2ByParent[p].push(c) })
            const l3ByParent = {}
            l3.forEach(c => { const p = c.parent; if (!l3ByParent[p]) l3ByParent[p] = []; l3ByParent[p].push(c) })
            const mapField = (id) => {
              const m = {
                no:'no', gender:'jenis_kelamin', nik:'nik', name:'nama', upah_dasar:'upah_dasar', hari_kerja:'hari_kerja', upah_pokok:'upah_pokok', jml_hk:'jumlah_hk', gaji_pokok:'gaji_pokok', total_tunjangan:'total_tunjangan', upah_bersih:'upah_bersih',
                cuti_tahunan_unit:'cuti_tahunan_hari', cuti_sakit_haid_unit:'cuti_sakit_haid_hari', cuti_minggu_unit:'cuti_minggu_hari', cuti_nasional_unit:'cuti_nasional_hari', cuti_izin_unit:'cuti_izin_hari',
                beras_rate:'beras_rate', beras_jumlah:'beras_jumlah', jabatan_rate:'jabatan_rate', jabatan_jumlah:'jabatan_jumlah', masa_kerja_lama:'masa_kerja_tahun', masa_kerja_jumlah:'masa_kerja_jumlah', lembur_jam:'lembur_jam', lembur_jumlah:'lembur_jumlah',
                brondol_jumlah:'premi_brondol', pruning_jumlah:'premi_pruning', premi_angkut_material_jumlah:'premi_angkut_material', premi_angkut_tbs_jumlah:'premi_angkut_tbs', premi_harvesting_jumlah:'premi_harvesting', premi_harvesting_incentive_jumlah:'premi_harvesting_incentive', premi_pupuk_jumlah:'premi_pupuk',
                premi_koreksi_jumlah:'premi_koreksi', bpjs_pensiun_pekerja:'pot_bpjs_pensiun_pekerja', bpjs_pensiun_majikan:'pot_bpjs_pensiun_majikan',
                pph21:'pot_pph21', potongan_kontan:'pot_kontan', thr:'pot_thr', pinjam:'pot_pinjam', kl:'pot_kl', bpjs_kes:'pot_bpjs_kes', bpjs_pek:'pot_bpjs_pek', bpjs_maj:'pot_bpjs_maj', total1:'pot_total_1', total2:'pot_total_2', total3:'pot_total_3', total4:'pot_total_4', cth:'tidak_hadir_cth', alpa:'tidak_hadir_alpa'
              }
              return m[id] || id
            }
            const built = []
            const leftColumns = []
            const otherColumns = []

            l1.forEach(c1 => {
              const childrenIds = c1.children || []
              if (!childrenIds || childrenIds.length === 0) {
                const field = mapField(c1.id)
                if (field) {
                  const colDef = { field, headerName: c1.text, pinned: ['no','nama'].includes(field) ? 'left' : undefined }
                  if (['no','nama'].includes(field)) {
                    leftColumns.push(colDef)
                  } else {
                    otherColumns.push(colDef)
                  }
                }
                return
              }
              const group2 = (l2ByParent[c1.id] || []).map(c2 => {
                const leaves = (l3ByParent[c2.id] || []).map(c3 => ({ field: mapField(c3.id), headerName: c3.text }))
                return { headerName: c2.text, children: leaves }
              })
              otherColumns.push({ headerName: c1.text, children: group2 })
            })

            // Pastikan kolom utama (no, gender, nik, name) berada di paling kiri dan selalu tampil
            const essentialColumns = []
            const remainingLeftColumns = []

            leftColumns.forEach(col => {
              if (['no', 'jenis_kelamin', 'nik', 'nama'].includes(col.field)) {
                essentialColumns.push(col)
              } else {
                remainingLeftColumns.push(col)
              }
            })

            // Urutkan essential columns: no, gender, nik, nama
            const orderedEssential = []
            if (essentialColumns.some(c => c.field === 'no')) {
              orderedEssential.push(essentialColumns.find(c => c.field === 'no'))
            }
            if (essentialColumns.some(c => c.field === 'jenis_kelamin')) {
              orderedEssential.push(essentialColumns.find(c => c.field === 'jenis_kelamin'))
            }
            if (essentialColumns.some(c => c.field === 'nik')) {
              orderedEssential.push(essentialColumns.find(c => c.field === 'nik'))
            }
            if (essentialColumns.some(c => c.field === 'nama')) {
              orderedEssential.push(essentialColumns.find(c => c.field === 'nama'))
            }

            // Pastikan kolom 'no' dan 'nama' berada di paling kiri
            built.push(...orderedEssential, ...remainingLeftColumns, ...otherColumns)
            const hasChildren = Array.isArray(columnDefsData) && columnDefsData.some(c => c.children)
            const chosen = hasChildren ? columnDefsData : built
            const leafFields = []
            const walk = (c) => { if (c.children) c.children.forEach(walk); else if (c.field) leafFields.push(c.field) }
            chosen.forEach(walk)
            const dupFields = leafFields.filter((f, i, a) => a.indexOf(f) !== i)
            console.log('[Columns] Leaf fields count:', leafFields.length)
            if (dupFields.length > 0) {
              console.warn('[Columns] Duplicate fields detected:', dupFields)
            }
            setColumnDefs(chosen)
          } catch (e2) {
            setError('Failed to load dynamic headers')
          }
        } else {
          setError('Failed to load dynamic headers')
        }
      } finally {
        setHeaderLoading(false)
      }
    }

    loadHeaders()
  }, [finalToken, finalMonth, finalYear, finalGangCode])

  useEffect(() => {
    async function run() {
      setLoading(true); setError('')
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
        const leafFields = []
        const walk = (c) => { if (c.children) c.children.forEach(walk); else if (c.field) leafFields.push(c.field) }
        columnDefs.forEach(walk)
        const data = await fetchReportRows(finalToken, { month: monthValue, year: yearValue, gang_code: finalGangCode, fields: leafFields, benchmark: true, monitor: false })
        setRows(data)
        const safe = Array.isArray(data) ? data : []
        
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
          // Koreksi column
          premi_koreksi: agg('premi_koreksi'),
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

        // Proses autohide hanya sekali saat data pertama kali dimuat
        if (!autohideProcessed && safe.length > 0) {
          console.log('[AutoHide] Processing column auto-hide for', safe.length, 'rows')
          const enhanced = enhanceColumnsRecursive(columnDefs)
          const hiddenColumns = hideEmptyPremiColumns(enhanced, safe)
          setEnhancedColumnDefs(hiddenColumns)
          setAutohideProcessed(true)
          console.log('[AutoHide] Column auto-hide completed. Columns before:', enhanced.length, 'after:', hiddenColumns.length)
        } else if (autohideProcessed) {
          console.log('[AutoHide] Skipping auto-hide - already processed')
        }

        // Frontend no longer auto-hides columns; backend filters dynamic headers
      } catch (e) {
        if (DEV_MODE && !finalToken) {
          try {
            const res = await login('admin', 'admin')
            setAuthToken(res.access_token)
            const leafFields = []
            const walk = (c) => { if (c.children) c.children.forEach(walk); else if (c.field) leafFields.push(c.field) }
            columnDefs.forEach(walk)
            const data = await fetchReportRows(res.access_token, { month: monthValue, year: yearValue, gang_code: finalGangCode, fields: leafFields, benchmark: true, monitor: false })
            setRows(data)
            const safe = Array.isArray(data) ? data : []
            const agg = (field) => Math.round(safe.reduce((a, b) => a + Number(b[field] || 0), 0))
            setPinnedBottom(safe.length > 0 ? [{
              no: '', jenis_kelamin: '', nik: '', nama: 'GRAND TOTAL',
              upah_dasar: '', hari_kerja: '', upah_pokok: agg('upah_pokok'),
              cuti_tahunan_hari: agg('cuti_tahunan_hari'), cuti_sakit_haid_hari: agg('cuti_sakit_haid_hari'), cuti_minggu_hari: agg('cuti_minggu_hari'), cuti_nasional_hari: agg('cuti_nasional_hari'), cuti_izin_hari: agg('cuti_izin_hari'), jumlah_hk: agg('jumlah_hk'),
              gaji_pokok: agg('gaji_pokok'), beras_rate: '', beras_jumlah: agg('beras_jumlah'), jabatan_rate: '', jabatan_jumlah: agg('jabatan_jumlah'), masa_kerja_tahun: '', masa_kerja_jumlah: agg('masa_kerja_jumlah'), lembur_jam: '', lembur_jumlah: agg('lembur_jumlah'), total_tunjangan: agg('total_tunjangan'),
              premi_brondol: agg('premi_brondol'), premi_pruning: agg('premi_pruning'), premi_angkut_material: agg('premi_angkut_material'), premi_angkut_tbs: agg('premi_angkut_tbs'), premi_harvesting: agg('premi_harvesting'), premi_harvesting_incentive: agg('premi_harvesting_incentive'), premi_pupuk: agg('premi_pupuk'),
              // Koreksi column
              premi_koreksi: agg('premi_koreksi'),
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

            // Proses autohide hanya sekali saat data pertama kali dimuat (dev mode)
            if (!autohideProcessed && safe.length > 0) {
              console.log('[AutoHide] Processing column auto-hide for', safe.length, 'rows (dev mode)')
              const enhanced = enhanceColumnsRecursive(columnDefs)
              const hiddenColumns = hideEmptyPremiColumns(enhanced, safe)
              setEnhancedColumnDefs(hiddenColumns)
              setAutohideProcessed(true)
              console.log('[AutoHide] Column auto-hide completed. Columns before:', enhanced.length, 'after:', hiddenColumns.length)
            } else if (autohideProcessed) {
              console.log('[AutoHide] Skipping auto-hide - already processed (dev mode)')
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
        if (typeof onLoad === 'function') onLoad()
      }
    }
    if (columnDefs.length > 0) {
      run()
    }
  }, [finalToken, finalMonth, finalYear, finalGangCode, columnDefs])

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
    const moneyFields = ['upah_dasar','upah_pokok','gaji_pokok','beras_jumlah','jabatan_jumlah','masa_kerja_jumlah','lembur_jumlah','total_tunjangan','premi_brondol','premi_pruning','premi_angkut_material','premi_angkut_tbs','premi_harvesting','premi_harvesting_incentive','premi_pupuk','total_premi','jumlah_upah_kotor','pot_pph21','pot_kontan','pot_thr','pot_pinjam','pot_kl','pot_bpjs_kes','pot_bpjs_pek','pot_bpjs_maj','pot_total_1','pot_total_2','pot_total_3','pot_total_4','total_potongan','upah_bersih']
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

  // Auto-hide kolom premi yang tidak ada data sama sekali
  const hideEmptyPremiColumns = (cols, data) => {
    if (!Array.isArray(cols) || !Array.isArray(data)) return cols

    const checkColumnHasData = (field) => {
      // Jangan sembunyikan kolom esensial dan kolom-kolom potongan/premi penting
      const essentialColumns = [
        // Basic essential columns
        'no', 'jenis_kelamin', 'nik', 'nama',
        // Payroll summary columns
        'upah_pokok', 'total_tunjangan', 'upah_bersih',
        // Koreksi column (treated as premi but actually deduction)
        'premi_koreksi', 'koreksi',
        // BPJS columns (should always be visible even if 0)
        'pot_bpjs_kesehatan_pekerja', 'pot_bpjs_kesehatan_majikan',
        'pot_bpjs_pensiun_pekerja', 'pot_bpjs_pensiun_majikan',
        'pot_bpjs_kes', 'pot_bpjs_pek', 'pot_bpjs_maj',
        'pot_bpjs_jumlah', 'pot_bpjs_pekerja_total',
        // Other important deductions
        'pot_spsi', 'spsi', 'pot_pph21', 'pph21',
        // Important totals
        'total_premi', 'total_potongan', 'jumlah_upah_kotor'
      ]

      if (essentialColumns.includes(field)) {
        return true
      }

      // Untuk kolom premi lainnya, sembunyikan jika tidak ada data > 0
      const premiColumns = [
        'premi_brondol', 'premi_pruning', 'premi_angkut_material',
        'premi_angkut_tbs', 'premi_harvesting', 'premi_harvesting_incentive', 'premi_pupuk'
      ]

      if (premiColumns.includes(field)) {
        return data.some(row => row[field] != null && row[field] !== '' && Number(row[field]) > 0)
      }

      // Untuk kolom lain, sembunyikan jika tidak ada data
      return data.some(row => row[field] != null && row[field] !== '' && Number(row[field]) !== 0)
    }

    const checkGroupHasData = (group) => {
      // For grouped columns, check if any leaf column has data
      if (group.children && Array.isArray(group.children)) {
        return group.children.some(child => {
          if (child.children) {
            return checkGroupHasData(child)
          } else if (child.field) {
            return checkColumnHasData(child.field)
          }
          return false
        })
      } else if (group.field) {
        return checkColumnHasData(group.field)
      }
      return true // Always show headers without fields
    }

    const processColumn = (col) => {
      if (col.children && Array.isArray(col.children)) {
        // Process level 2 header dengan children level 3
        const processedChildren = col.children.map(child => {
          if (child.children && Array.isArray(child.children)) {
            // Level 3 children - periksa apakah ada data
            const visibleChildren = child.children.filter(leaf => {
              if (!leaf.field) return true
              return checkColumnHasData(leaf.field)
            })
            return {
              ...child,
              children: visibleChildren,
              hide: visibleChildren.length === 0
            }
          }
          return child
        }).filter(child => !child.hide)

        return {
          ...col,
          children: processedChildren,
          hide: !checkGroupHasData(col) // Use group data check instead of children length
        }
      } else if (col.field) {
        // Leaf column - periksa apakah ada data
        return {
          ...col,
          hide: !checkColumnHasData(col.field)
        }
      }
      return col
    }

    return cols.map(processColumn).filter(col => !col.hide)
  }

  const enhanceColumnsRecursive = (cols) => cols.map(c => {
    if (c.children && Array.isArray(c.children)) {
      return { ...c, children: enhanceColumnsRecursive(c.children) }
    }
    return formatLeaf(c)
  })

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
      const columnDefsToUse = enhancedColumnDefs.length > 0 ? enhancedColumnDefs : enhanceColumnsRecursive(columnDefs)
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
          const columnDefsToUse = enhancedColumnDefs.length > 0 ? enhancedColumnDefs : enhanceColumnsRecursive(columnDefs)
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

  if (headerLoading || loading) return (
    <LoadingScreen
      isLoading={true}
      message={headerLoading ? 'Loading report configuration...' : 'Analyzing payroll data...'}
      gangCode={finalGangCode}
      month={finalMonth}
      year={finalYear}
      logoUrl={import.meta.env.VITE_COMPANY_LOGO_URL || '/rebinmas-logo.png'}
      steps={headerLoading ? [
        { name: `Loading headers for Gang ${finalGangCode}`, duration: 1800 },
        { name: `Fetching dynamic columns for ${finalGangCode}`, duration: 2200 },
        { name: 'Building column hierarchy', duration: 1500 }
      ] : [
        { name: 'Connecting to payroll database', duration: 1500 },
        { name: `Loading rows for Gang ${finalGangCode}`, duration: 2800 },
        { name: `Aggregating ${typeof finalMonth==='string' ? finalMonth : finalMonth+'/'+finalYear}`, duration: 2500 }
      ]}
    />
  )
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

  if (!rows || rows.length === 0) return (
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
          columnDefs={enhancedColumnDefs.length > 0 ? enhancedColumnDefs : enhanceColumnsRecursive(columnDefs)}
          rowData={rows}
          defaultColDef={baseCol}
          rowClassRules={rowClassRules}
          pinnedBottomRowData={pinnedBottom}
          rowSelection={'single'}
          pagination={true}
          paginationPageSize={20}
          paginationPageSizeSelector={[10, 20, 50, 100]}
          rowBuffer={20}
          enableRangeSelection={true}
          suppressRowClickSelection={true}
          animateRows={true}
          domLayout='autoHeight'
          sideBar={{ toolPanels: ['columns', 'filters'], defaultToolPanel: 'columns' }}
          getRowHeight={params => params.node.rowIndex === 0 ? 40 : 30}
          onGridReady={params => {
            if (rows.length > 0) {
              params.api.ensureIndexVisible(0, 'top')
            }
            // Log grid ready state for debugging
            const activeColumnDefs = enhancedColumnDefs.length > 0 ? enhancedColumnDefs : enhanceColumnsRecursive(columnDefs)
            console.log('[AG Grid] Grid ready with columns:', activeColumnDefs.length)
            console.log('[AG Grid] Rows loaded:', rows.length)
            console.log('[AG Grid] Hierarchy headers:', hierarchyHeaders)
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
