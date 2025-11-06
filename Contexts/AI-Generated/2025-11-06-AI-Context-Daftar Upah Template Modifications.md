# 2025-11-06-AI-Context-Daftar Upah Template Modifications

## Project Overview
Saya telah melakukan modifikasi pada template HTML daftar upah untuk PT Rebinmas dengan perubahan-perubahan berikut:

## Files Modified
1. **daftar_upah_template_final.html** - Template HTML utama
2. **daftar_upah_engine_real_database.py** - Engine untuk generate report dari database

## Changes Made

### 1. Column Width Improvements
- Menambahkan `max-width` pada semua kolom untuk memastikan content tidak terlalu lebar
- Mengatur `min-width` untuk mempertahankan ukuran minimum yang readable
- Example: `.col-no { width: 30px; max-width: 40px; min-width: 30px; }`

### 2. Alternating Row Colors for Cuti/Libur Columns
- Menambahkan CSS classes:
  - `.cuti-col-odd { background-color: #f5f5f5; }`
  - `.cuti-col-even { background-color: #ffffff; }`
- Implementasi di engine untuk memberikan warna selang-seling pada kolom cuti/libur

### 3. Content Centering
- Menambahkan `.center-cell` class untuk centering horizontal dan vertical
- Diterapkan pada semua kolom data di engine

### 4. Zero Value Replacement
- Method `clean_zero_value()` untuk mengganti 0 dengan string kosong
- Diterapkan pada semua numeric values agar 0 ditampilkan sebagai kosong

### 5. Red Text for Cuti/Libur Values
- CSS: `.cuti-libur-text { color: #dc3545; font-weight: bold; }`
- Diterapkan pada semua nilai cuti/libur (baik hari maupun jumlah)

### 6. Real HK Count Integration
- Method `get_employee_hk_count()` untuk query jumlah HK dari database
- Menggunakan query yang ada di file `get_total_HK_each_Emp.sql`
- Query ke tabel `PR_EMP_ATTN` dengan filter `IsPresent = 'true'`

## Database Query Used
```sql
SELECT COUNT(*) as hk_count
FROM "PR_EMP_ATTN"
WHERE EmpCode = ?
  AND AttnDate >= ?
  AND AttnDate < DATEADD(month, 1, ?)
  AND IsPresent = 'true'
```

## Implementation Details

### Template Modifications
```css
/* Alternating row colors for cuti/libur columns */
.cuti-col-odd { background-color: #f5f5f5; }
.cuti-col-even { background-color: #ffffff; }

/* Red text for cuti/libur values */
.cuti-libur-text { color: #dc3545; font-weight: bold; }

/* Better centering */
.center-cell {
    text-align: center !important;
    vertical-align: middle !important;
    justify-content: center;
    align-items: center;
}
```

### Engine Modifications
1. **get_employee_hk_count()** - Method untuk query HK dari database
2. **clean_zero_value()** - Method untuk mengganti 0 dengan kosong
3. **generate_final_employee_rows()** - Update untuk:
   - Apply alternating colors pada kolom cuti
   - Apply red text untuk nilai cuti/libur
   - Apply center-cell class untuk semua kolom
   - Clean zero values
   - Get real HK count dari database

## Files Location
- Template: `Engine_HTML_Templating/template_report/ui/daftar_upah_template_final.html`
- Engine: `Engine_HTML_Templating/template_report/ui/daftar_upah_engine_real_database.py`
- HK Query: `Engine_HTML_Templating/template_report/query/get_total_HK_each_Emp.sql`
- Cuti Manager: `Engine_HTML_Templating/template_report/ui/cuti_data_manager.py`

## Implementation Status ✅ COMPLETED

### Testing Results
- ✅ Report berhasil digenerate dengan data real (33 employees dari gang H1M)
- ✅ Warna selang-seling kolom cuti/libur berfungsi (cuti-col-odd & cuti-col-even)
- ✅ Text merah untuk nilai cuti/libur berfungsi (cuti-libur-text)
- ✅ Centering horizontal dan vertical berfungsi (center-cell)
- ✅ 0 values berhasil diganti dengan kosong
- ✅ HK count terambil dari database (contoh: 31 hari, 5 hari)
- ✅ Syntax error berhasil diperbaiki
- ✅ Database connection issue berhasil diperbaiki

### Output File
- Generated: `daftar_upah_gang_H1M_real_2025-11-06_11-58-30.html`
- Size: 41,560 bytes (5 employees)
- Full version: 175,911 bytes (33 employees)

### Final Implementation Notes
- Database config menggunakan nested structure: `config['database']['driver']`
- HK count query berhasil menggunakan parameterized query
- Cuti data berhasil terintegrasi dari database
- Template styling berfungsi dengan baik

## Template Structure Update - November 2025

### Changes Made:
1. **Header Updates**:
   - "TAHUN" → "TAHUNAN (Izin)" untuk Personal Annual Leave
   - Sakit dan Haid tetap terpisah (sesuai permintaan)
   - Menghapus kolom "Total Cuti/Libur (Rp)" sama sekali

2. **Column Structure**:
   - Cuti/Libur: TAHUNAN (Izin) | SAKIT | HAID | MINGGU | NASIONAL | MELAHIRKAN | IZIN
   - JML HK: Data real dari database
   - **Removed**: Total Cuti/Libur (Rp) columns (7 kolom dihapus)
   - Tunjangan/Premi: 18 kolom (tetap)
   - Potongan: 13 kolom (tetap)

3. **Engine Updates**:
   - Remove Total Cuti/Libur (Rp) generation
   - Remove cuti_jumlah calculations
   - Maintain all styling (alternating colors, red text, centering)

4. **Testing Results (Updated)**:
   - ✅ Report berhasil digenerate dengan struktur baru
   - ✅ File size lebih kecil: 28,297 bytes (vs 41,560 bytes sebelumnya)
   - ✅ Tidak ada lagi kolom Total Cuti/Libur (Rp)
   - ✅ Header "TAHUNAN (Izin)" berhasil ditampilkan
   - ✅ Sakit dan Haid tetap terpisah

### Updated Output File
- Latest: `daftar_upah_gang_H1M_real_2025-11-06_14-45-01.html`
- Size: 27,410 bytes (3 employees, dengan 5 kolom cuti dan query sakit+haid)

## Final Structure Update - 5 Kolom Cuti/Libur

### Struktur Header Terbaru:
1. **TAHUNAN (Izin)** - Personal Annual Leave
2. **SAKIT + HAID** - Personal Sick Leave (gabungan dari query)
3. **MINGGU** - Hari Minggu
4. **NASIONAL** - Hari Libur Nasional
5. **IZIN** - Izin biasa

### Changes Made:
1. **Kolom Dihapus**:
   - MELAHIRKAN (tidak lagi dipakai)
   - HAID terpisah (digabung ke SAKIT + HAID)
   - Total dari 7 kolom menjadi 5 kolom

2. **Query Integration**:
   - Tetap menggunakan `get_cuti_sakit.sql` dengan TaskCode 'GA9126AB2'
   - Data gabungan sakit + haid langsung ke kolom "SAKIT + HAID"
   - `cuti_sakit_hari` = total query result
   - `cuti_haid_hari` = 0 (karena sudah digabung)

3. **Template Optimization**:
   - File size berkurang: 27,410 bytes (lebih kecil 887 bytes)
   - Header lebih compact dan jelas
   - Tetap maintain styling (alternating colors, red text)

### Testing Results:
- ✅ **H0019**: Tahunan=2, Sakit+haid=1, Minggu=4, Nasional=3, Izin=0
- ✅ **H0130**: Tahunan=0, Sakit+haid=0, Minggu=4, Nasional=3, Izin=0
- ✅ **H0459**: Tahunan=0, Sakit+haid=0, Minggu=1, Nasional=1, Izin=0

## Kolom Upah Dasar & Hari Kerja - November 2025

### Changes Made:
1. **Kolom Baru**:
   - **Upah Dasar**: Diambil dari `HR_PAYROLL.PayRate` menggunakan `get_payrate_emp_code.sql`
   - **Hari Kerja**: Dihasilkan dari formula `JML HK - (Tahunan + Sakit + Minggu + Nasional)`

2. **Template Structure Baru**:
   ```
   NO | L/P | NIK | NAMA | UPAH DASAR | HARI KERJA | TAHUNAN (Izin) | SAKIT + HAID | MINGGU | NASIONAL | IZIN | JML HK | ...
   ```

3. **Engine Updates**:
   - `get_employee_payrate()`: Query PayRate dari database
   - `calculate_hari_kerja()`: Hitung hari kerja actual
   - CSS styling untuk kolom baru (Upah Dasar: right-align, bold; Hari Kerja: background biru)

4. **Testing Results (Updated)**:
   - **H0130**: Upah Dasar=129,220, Hari Kerja=24, HK=31, Cuti=7 (0+0+4+3)
   - **H0019**: Upah Dasar=129,220, Hari Kerja=21, HK=31, Cuti=10 (2+1+4+3)
   - **H0459**: Upah Dasar=129,220, Hari Kerja=3, HK=5, Cuti=2 (0+0+1+1)

5. **File Size**: 28,685 bytes (bertambah 1,275 bytes untuk 2 kolom baru)

### Latest Output:
- File: `daftar_upah_gang_H1M_real_2025-11-06_15-14-14.html`
- Status: ✅ All features working correctly

## Kolom Gaji Pokok (Rp) - November 2025

### Changes Made:
1. **Kolom Baru**:
   - **Gaji Pokok (Rp)**: Formula **JML HK × Payrate (Rp)**
   - Positioned di samping kanan JML HK

2. **Template Structure Terbaru**:
   ```
   NO | L/P | NIK | NAMA | UPAH DASAR | HARI KERJA | TAHUNAN (Izin) | SAKIT + HAID | MINGGU | NASIONAL | IZIN | JML HK | GAJI POKOK (Rp) | ...
   ```

3. **Styling**:
   - Background color: **#b4e06e** (hijau)
   - Text alignment: Right
   - Font weight: **bold**
   - Padding right: 5px

4. **Formula Implementation**:
   - `calculate_gaji_pokok(hk_count, payrate)`: JML HK × Payrate
   - Payrate diambil dari `HR_PAYROLL.PayRate` (129,220)
   - JML HK dari query `PR_EMP_ATTN`

5. **Testing Results (Updated)**:
   - **H0130**: HK=31 × Payrate=129,220 = **4,005,820**
   - **H0019**: HK=31 × Payrate=129,220 = **4,005,820**
   - **H0459**: HK=5 × Payrate=129,220 = **646,100**

6. **File Size**: 29,548 bytes (bertambah 863 bytes untuk kolom baru)

### Verification:
- ✅ **Background Color**: #b4e06e (hijau)
- ✅ **Bold Text**: font-weight: bold
- ✅ **Right Alignment**: text-align: right
- ✅ **Formula**: HK × Payrate = Gaji Pokok
- ✅ **Payrate**: 129,220 (dari database)
- ✅ **Format**: Currency (Rp) with comma separator

## Perhitungan Cuti Sakit + Haid - Update Terbaru

### Changes Made:
1. **Query Integration**:
   - Menggunakan `get_cuti_sakit.sql` dengan TaskCode 'GA9126AB2'
   - Query ini sudah menghasilkan data gabungan sakit + haid
   - Tidak perlu split logic lagi (70% sakit, 30% haid)

2. **Logic Update di cuti_data_manager**:
   - `cuti_sakit_hari` = total hari dari query (sakit + haid gabungan)
   - `cuti_haid_hari` = 0 (karena sudah digabung ke sakit)
   - `cuti_sakit_jumlah` = cuti_sakit_hari * 75000
   - `cuti_haid_jumlah` = 0

3. **Testing Results**:
   - **H0019**: Sakit+haid=1 (dari query), Haid=0
   - **H0130**: Sakit+haid=0, Haid=0
   - **H0459**: Sakit+haid=0, Haid=0

### Key Improvements:
- ✅ Data real dari query untuk setiap employee
- ✅ Tidak ada lagi assumption/default untuk haid perempuan
- ✅ Perhitungan berdasarkan data aktual dari TaskCode 'GA9126AB2'
- ✅ Debug messages lebih jelas menunjukkan "Sakit+haid" records

## Tags
#AI-Context #DaftarUpah #TemplateModification #HTML #CSS #Python #Database #Payroll