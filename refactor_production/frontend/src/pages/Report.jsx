import { useEffect, useMemo, useRef, useState } from 'react'
import { AgGridReact } from 'ag-grid-react'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import '../styles/report.css'
import { fetchReportRows } from '../services/payrollService'

export default function Report({ token, month, year, gang_code }) {
  const [rows, setRows] = useState([])
  const [pinnedBottom, setPinnedBottom] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const gridRef = useRef(null)
  useEffect(() => {
    async function run() {
      setLoading(true); setError('')
      try {
        const data = await fetchReportRows(token, { month, year, gang_code })
        setRows(data)
        const safe = Array.isArray(data) ? data : []
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
      }
    }
    run()
  }, [token, month, year, gang_code])

  const currency = (v) => v === '' ? '' : (v ?? 0).toLocaleString('id-ID')
  const baseCol = { resizable: true, sortable: true }
  const colDefs = useMemo(() => ([
    { field: 'no', headerName: 'NO', width: 60, cellClass: 'cell-center' },
    { field: 'jenis_kelamin', headerName: 'L/P', width: 70, cellClass: 'cell-center', pinned: 'left' },
    { field: 'nik', headerName: 'NIK', width: 110, pinned: 'left' },
    { field: 'nama', headerName: 'NAMA', width: 180, pinned: 'left' },
    { field: 'upah_dasar', headerName: 'UPAH DASAR', width: 120, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
    { field: 'hari_kerja', headerName: 'HARI KERJA', width: 110, cellClass: 'cell-center' },
    { field: 'upah_pokok', headerName: 'UPAH POKOK', width: 120, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
    { headerName: 'CUTI/LIBUR', children: [
      { field: 'cuti_tahunan_hari', headerName: 'TAHUNAN (H)', width: 110, cellClass: 'cell-center cuti-col-odd' },
      { field: 'cuti_sakit_haid_hari', headerName: 'SAKIT+HAID (H)', width: 130, cellClass: 'cell-center cuti-col-even' },
      { field: 'cuti_minggu_hari', headerName: 'MINGGU (H)', width: 110, cellClass: 'cell-center cuti-col-odd' },
      { field: 'cuti_nasional_hari', headerName: 'NASIONAL (H)', width: 120, cellClass: 'cell-center cuti-col-even' },
      { field: 'cuti_izin_hari', headerName: 'IZIN (H)', width: 100, cellClass: 'cell-center cuti-col-odd' },
    ]},
    { field: 'jumlah_hk', headerName: 'HK', width: 80, cellClass: 'cell-center' },
    { field: 'gaji_pokok', headerName: 'GAJI POKOK', width: 120, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
    { headerName: 'TUNJANGAN', children: [
      { field: 'beras_rate', headerName: 'BERAS (RATE)', width: 120, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'beras_jumlah', headerName: 'BERAS (JUMLAH)', width: 130, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'jabatan_rate', headerName: 'JABATAN (RATE)', width: 130, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'jabatan_jumlah', headerName: 'JABATAN (JUMLAH)', width: 140, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'masa_kerja_tahun', headerName: 'MASA KERJA (LAMA)', width: 150, cellClass: 'cell-center' },
      { field: 'masa_kerja_jumlah', headerName: 'MASA KERJA (JUMLAH)', width: 160, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'lembur_jam', headerName: 'LEMBUR (JAM)', width: 120, cellClass: 'cell-center' },
      { field: 'lembur_jumlah', headerName: 'LEMBUR (JUMLAH)', width: 140, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
    ]},
    { field: 'total_tunjangan', headerName: 'TOTAL TUNJANGAN', width: 150, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
    { headerName: 'PREMI', children: [
      { field: 'premi_brondol', headerName: 'BRONDOL', width: 140, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'premi_pruning', headerName: 'PRUNING', width: 120, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'premi_angkut_material', headerName: 'PREMI ANGKUT MATERIAL', width: 180, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'premi_angkut_tbs', headerName: 'PREMI ANGKUT TBS', width: 160, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'premi_harvesting', headerName: 'PREMI HARVESTING', width: 160, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'premi_harvesting_incentive', headerName: 'PREMI HARVESTING +INCENTIVE PANEN', width: 240, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'premi_pupuk', headerName: 'PREMI PUPUK', width: 140, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
    ]},
    { field: 'total_premi', headerName: 'TOTAL PREMI', width: 130, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
    { field: 'jumlah_upah_kotor', headerName: 'JUMLAH UPAH KOTOR', width: 170, valueFormatter: p => currency(p.value), cellClass: 'cell-right col-jumlah-kotor' },
    { headerName: 'POTONGAN', children: [
      { field: 'pot_pph21', headerName: 'PPH21', width: 110, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'pot_kontan', headerName: 'Kontan', width: 110, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'pot_thr', headerName: 'THR', width: 110, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'pot_pinjam', headerName: 'Pinjam', width: 110, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'pot_kl', headerName: 'KL', width: 90, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'pot_bpjs_kes', headerName: 'BPJS Kes', width: 130, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'pot_bpjs_pek', headerName: 'BPJS Pek', width: 130, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'pot_bpjs_maj', headerName: 'BPJS Maj', width: 130, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'pot_total_1', headerName: 'Total', width: 110, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'pot_total_2', headerName: 'Total', width: 110, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'pot_total_3', headerName: 'Total', width: 110, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
      { field: 'pot_total_4', headerName: 'Total', width: 110, valueFormatter: p => currency(p.value), cellClass: 'cell-right' },
    ]},
    { field: 'total_potongan', headerName: 'TOTAL POTONGAN', width: 150, valueFormatter: p => currency(p.value), cellClass: 'cell-right col-total-potongan' },
    { field: 'upah_bersih', headerName: 'UPAH BERSIH', width: 140, valueFormatter: p => currency(p.value), cellClass: 'cell-right col-upah-bersih' },
    { headerName: 'TIDAK HADIR', children: [
      { field: 'tidak_hadir_cth', headerName: 'CTH', width: 80, cellClass: 'cell-center' },
      { field: 'tidak_hadir_alpa', headerName: 'ALPA', width: 80, cellClass: 'cell-center' },
    ]},
  ]), [])

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

  if (loading) return <div className="grid-wrapper">Loading report...</div>
  if (error) return <div className="grid-wrapper">{error}</div>
  if (!rows || rows.length === 0) return <div className="grid-wrapper">No data for selected parameters</div>
  return (
    <div className="grid-wrapper">
      <div style={{ marginBottom: 8 }}>
        <button onClick={exportCsv}>Export CSV</button>
        <button onClick={autoSizeAll} style={{ marginLeft: 8 }}>Auto-size Columns</button>
      </div>
      <div className="ag-theme-alpine" style={{ height: 600, width: '100%' }}>
        <AgGridReact ref={gridRef} columnDefs={colDefs} rowData={rows} defaultColDef={baseCol} rowClassRules={rowClassRules} pinnedBottomRowData={pinnedBottom} sideBar={{ toolPanels: ['columns','filters'], defaultToolPanel: 'columns' }} rowSelection={'single'} />
      </div>
    </div>
  )
}
