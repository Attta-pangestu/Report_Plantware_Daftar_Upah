import { useEffect, useMemo, useRef, useState } from 'react'
import { AgGridReact } from 'ag-grid-react'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import '../styles/report.css'
import { fetchReportRows } from '../services/payrollService'
import { fetchColumnDefinitions, fetchDynamicHeaders, formatCurrency, formatNumber } from '../services/headerService'

// Check if running in development mode
const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true' || import.meta.env.DEV_MODE === 'true'

export default function Report({ token, month, year, gang_code, onLoad }) {
  // In development mode, use default values if props are not provided
  const devToken = DEV_MODE ? 'dev-token' : token
  const devMonth = DEV_MODE ? '2025-05' : month
  const devYear = DEV_MODE ? 2025 : year
  const devGangCode = DEV_MODE ? 'H1H' : gang_code

  const finalToken = devToken || token
  const finalMonth = devMonth || month
  const finalYear = devYear || year
  const finalGangCode = devGangCode || gang_code
  const [rows, setRows] = useState([])
  const [pinnedBottom, setPinnedBottom] = useState([])
  const [columnDefs, setColumnDefs] = useState([])
  const [headers, setHeaders] = useState(null)
  const [hierarchyHeaders, setHierarchyHeaders] = useState(null)
  const [loading, setLoading] = useState(false)
  const [headerLoading, setHeaderLoading] = useState(false)
  const [error, setError] = useState('')
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
          fetchColumnDefinitions(finalToken)
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

        setColumnDefs(columnDefsData)
      } catch (e) {
        console.error('Failed to load headers:', e)
        setError('Failed to load dynamic headers')
      } finally {
        setHeaderLoading(false)
      }
    }

    if (finalToken) {
      loadHeaders()
    }
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
        const data = await fetchReportRows(finalToken, { month: monthValue, year: yearValue, gang_code: finalGangCode })
        setRows(data)
        const safe = Array.isArray(data) ? data : []

        // Debug: Tampilkan data baris pertama di console
        if (safe.length > 0) {
          console.log('🔍 Data Baris Pertama (JSON):')
          console.log(JSON.stringify(safe[0], null, 2))
          console.log('📊 Data Baris Pertama (Object):')
          console.table(safe[0])
        } else {
          console.warn('⚠️ Tidak ada data yang ditemukan')
        }
        const agg = (field) => safe.reduce((a, b) => a + Number(b[field] || 0), 0)
        setPinnedBottom(safe.length > 0 ? [{
          no: '', jenis_kelamin: '', nik: '', nama: 'GRAND TOTAL',
          upah_dasar: '', hari_kerja: '', upah_pokok: agg('upah_pokok'),
          cuti_tahunan_hari: agg('cuti_tahunan_hari'), cuti_sakit_haid_hari: agg('cuti_sakit_haid_hari'), cuti_minggu_hari: agg('cuti_minggu_hari'), cuti_nasional_hari: agg('cuti_nasional_hari'), cuti_izin_hari: agg('cuti_izin_hari'), jumlah_hk: agg('jumlah_hk'),
          gaji_pokok: agg('gaji_pokok'), beras_rate: '', beras_jumlah: agg('beras_jumlah'), jabatan_rate: '', jabatan_jumlah: agg('jabatan_jumlah'), masa_kerja_tahun: '', masa_kerja_jumlah: agg('masa_kerja_jumlah'), lembur_jam: '', lembur_jumlah: agg('lembur_jumlah'), total_tunjangan: agg('total_tunjangan'),
          premi_brondol: agg('premi_brondol'), premi_pruning: agg('premi_pruning'), premi_angkut_material: agg('premi_angkut_material'), premi_angkut_tbs: agg('premi_angkut_tbs'), premi_harvesting: agg('premi_harvesting'), premi_harvesting_incentive: agg('premi_harvesting_incentive'), premi_pupuk: agg('premi_pupuk'), total_premi: agg('total_premi'),
          jumlah_upah_kotor: agg('jumlah_upah_kotor'), pot_pph21: agg('pot_pph21'), pot_kontan: agg('pot_kontan'), pot_thr: agg('pot_thr'), pot_pinjam: agg('pot_pinjam'), pot_kl: agg('pot_kl'), pot_bpjs_kes: agg('pot_bpjs_kes'), pot_bpjs_pek: agg('pot_bpjs_pek'), pot_bpjs_maj: agg('pot_bpjs_maj'), pot_total_1: agg('pot_total_1'), pot_total_2: agg('pot_total_2'), pot_total_3: agg('pot_total_3'), pot_total_4: agg('pot_total_4'), total_potongan: agg('total_potongan'), upah_bersih: agg('upah_bersih'), tidak_hadir_cth: agg('tidak_hadir_cth'), tidak_hadir_alpa: agg('tidak_hadir_alpa')
        }] : [])
      } catch (e) {
        setError('Failed to load report data')
        setRows([])
        setPinnedBottom([])
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
  const enhancedColumnDefs = useMemo(() => {
    return columnDefs.map(col => {
      // Column specific configurations
      const colConfig = {
        ...col,
        ...baseCol,
        valueFormatter: undefined,
        type: undefined,
        cellStyle: undefined
      }

      // Numeric columns with currency formatting
      if (col.field && ['upah_dasar', 'upah_pokok', 'gaji_pokok', 'beras_jumlah', 'jabatan_jumlah',
          'masa_kerja_jumlah', 'lembur_jumlah', 'total_tunjangan', 'premi_brondol', 'premi_pruning',
          'premi_angkut_material', 'premi_angkut_tbs', 'premi_harvesting', 'premi_harvesting_incentive',
          'premi_pupuk', 'total_premi', 'jumlah_upah_kotor', 'pot_pph21', 'pot_kontan', 'pot_thr',
          'pot_pinjam', 'pot_kl', 'pot_bpjs_kes', 'pot_bpjs_pek', 'pot_bpjs_maj', 'pot_total_1',
          'pot_total_2', 'pot_total_3', 'pot_total_4', 'total_potongan', 'upah_bersih'].includes(col.field)) {
        colConfig.valueFormatter = (params) => {
          const val = params.value
          if (val === null || val === undefined || val === 0) return '-'
          return new Intl.NumberFormat('id-ID', {
            style: 'currency',
            currency: 'IDR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
          }).format(val)
        }
        colConfig.type = 'rightAligned'
        colConfig.cellStyle = { textAlign: 'right' }
      }
      // Integer columns
      else if (col.field && ['no', 'hari_kerja', 'cuti_tahunan_hari', 'cuti_sakit_haid_hari', 'cuti_minggu_hari',
          'cuti_nasional_hari', 'cuti_izin_hari', 'jumlah_hk', 'masa_kerja_tahun', 'lembur_jam',
          'tidak_hadir_cth', 'tidak_hadir_alpa'].includes(col.field)) {
        colConfig.valueFormatter = (params) => {
          const val = params.value
          if (val === null || val === undefined || val === 0) return '-'
          return new Intl.NumberFormat('id-ID').format(val)
        }
        colConfig.type = 'rightAligned'
        colConfig.cellStyle = { textAlign: 'right' }
      }
      // Text columns with left alignment for names
      else if (col.field && ['nama'].includes(col.field)) {
        colConfig.cellStyle = { textAlign: 'left' }
        colConfig.type = 'leftAligned'
      }
      // Center aligned columns
      else if (col.field && ['nik', 'jenis_kelamin'].includes(col.field)) {
        colConfig.cellStyle = { textAlign: 'center' }
        colConfig.type = 'centerAligned'
      }

      return colConfig
    })
  }, [columnDefs])

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
    <div className="grid-wrapper">
      <div className="loading-overlay">
        <div className="spinner" />
        <div className="loading-text">
          {headerLoading ? 'Loading dynamic headers...' : `Analyzing ${gang_code || '-'} for ${month || '-'}-${year || '-'}`}
        </div>
      </div>
    </div>
  )
  if (error) return <div className="grid-wrapper error-text">{error}</div>
  if (!rows || rows.length === 0) return <div className="grid-wrapper info-text">No data for selected parameters</div>

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
      </div>

      <div className="ag-theme-alpine" style={{ height: 700, width: '100%' }}>
        <AgGridReact
          ref={gridRef}
          columnDefs={enhancedColumnDefs}
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
          getRowHeight={params => params.node.rowIndex === 0 ? 40 : 30}
          onGridReady={params => {
            if (rows.length > 0) {
              params.api.ensureIndexVisible(0, 'top')
            }
            // Log grid ready state for debugging
            console.log('[AG Grid] Grid ready with columns:', enhancedColumnDefs.length)
            console.log('[AG Grid] Rows loaded:', rows.length)
            console.log('[AG Grid] Hierarchy headers:', hierarchyHeaders)
          }}
        />
      </div>
    </div>
  )
}
