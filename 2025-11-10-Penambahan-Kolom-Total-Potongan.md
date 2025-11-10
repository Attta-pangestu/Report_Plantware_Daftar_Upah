--- 
date: 2025-11-10
tags: [AI-Context, Laporan-Upah, Total-Potongan, Perbaikan]
--- 

# Penambahan Kolom Total Potongan - Plantware Auto Report

## Ringkasan Perubahan

Menambahkan kolom baru "TOTAL POTONGAN" yang menjumlahkan:
- BPJS Kesehatan Pekerja
- BPJS Pensiun Pekerja  
- Iuran SPSI
- PPh21

Serta memodifikasi perhitungan Upah Bersih menjadi: **Upah Kotor - Total Potongan**

## Lokasi File yang Diubah

### 1. Template HTML
- **File**: Engine_HTML_Templating/template_report/ui/daftar_upah_template_final.html
- **Header**: Line 791, 835, 885 - Menambah kolom TOTAL POTONGAN
- **CSS**: Line 501-533 - Menambah styling untuk kolom Total Potongan
- **Grand Total**: Line 960 - Menampilkan grand total Total Potongan

### 2. Engine Database
- **File**: Engine_HTML_Templating/template_report/ui/daftar_upah_engine_real_database.py
- **Line 1244**: Menghitung Total Potongan per employee
- **Line 1248**: Menampilkan kolom Total Potongan di employee rows  
- **Line 1269**: Menghitung Upah Bersih = Jumlah Upah Kotor - Total Potongan
- **Line 1763**: Grand Total Total Potongan
- **Line 1782**: Menghitung ulang Grand Total Upah Bersih

## Detail Perubahan

### Template HTML (daftar_upah_template_final.html)

#### Header Modifications
```html
<!-- Main Header -->
<td rowspan="3" class="header-cell col-total-potongan main-header">TOTAL<br>POTONGAN</td>

<!-- Second Header -->
<td class="header-cell sub-header-total-potongan">JUMLAH<br>(Rp)</td>

<!-- Third Header -->
<td class="header-cell col-total-potongan">JUMLAH<br>(Rp)</td>

<!-- Grand Total -->
<td class="number-cell col-total-potongan" style="background-color: #e1f5fe; color: #0277bd;">{grand_total.total_potongan_total:,.0f}</td>
```

#### CSS Styling
```css
/* Total Potongan Column - Special styling */
.col-total-potongan {
    background: #e1f5fe !important;
    text-align: right !important;
    padding-right: 5px !important;
    font-weight: bold;
    font-size: 10pt;
    color: #0277bd !important;
    border: 1px solid #d0d0d0 !important;
}

/* Alternating row styles */
.employee-row:nth-child(odd) .col-total-potongan {
    background: #b3e5fc !important;
    color: #01579b !important;
}

.employee-row:nth-child(even) .col-total-potongan {
    background: #e1f5fe !important;
    color: #0277bd !important;
}
```

### Engine Database (daftar_upah_engine_real_database.py)

#### Per Employee Calculation (Line 1244)
```python
# Calculate Total Potongan = BPJS Kesehatan Pekerja + BPJS Pensiun Pekerja + Iuran SPSI + PPH21
total_potongan = bpjs_kesehatan_pekerja + bpjs_pensiun_pekerja + spsi_amount + pph21_amount
```

#### Upah Bersih Calculation (Line 1269)
```python
# Calculate Upah Bersih = Jumlah Upah Kotor - Total Potongan
upah_bersih = jumlah_upah_kotor - total_potongan
```

#### Grand Total Calculation (Line 1763 & 1782)
```python
# Total Potongan Grand Total
'total_potongan_total': bpjs_kesehatan_pekerja_total + bpjs_pensiun_pekerja_total + grand_total_spsi + grand_total_pph21,

# Recalculate Upah Bersih using new formula
'upah_bersih_total': grand_total_jumlah_upah_kotor - (bpjs_kesehatan_pekerja_total + bpjs_pensiun_pekerja_total + grand_total_spsi + grand_total_pph21),
```

## Dampak Perubahan

### Visual Layout
- **Posisi Kolom**: Total Potongan ditempatkan sebelum kolom Upah Bersih
- **Styling**: Warna biru muda (#e1f5fe) dengan teks biru tua (#0277bd)
- **Alignment**: Right-aligned untuk format currency

### Perhitungan
1. **Total Potongan** = BPJS Kesehatan Pekerja + BPJS Pensiun Pekerja + Iuran SPSI + PPh21
2. **Upah Bersih** = Jumlah Upah Kotor - Total Potongan
3. **Grand Total** mengikuti formula yang sama

## Komponen Potongan yang Termasuk

✅ **BPJS Kesehatan Pekerja** (1% dari base calculation)  
✅ **BPJS Pensiun Pekerja** (1% dari gaji_pokok_min)  
✅ **Iuran SPSI** (dari database query)  
✅ **PPh21** (dari database query)  

## Komponen Potongan yang TIDAK Termasuk

❌ BPJS Kesehatan Majikan (4% - ini adalah tanggungan perusahaan)  
❌ BPJS Pensiun Majikan (2% - ini adalah tanggungan perusahaan)  
❌ Caruman ASTEK (ini adalah dana pensiun, bukan potongan gaji)  

## Testing yang Diperlukan

1. Generate laporan dengan data karyawan aktif
2. Verifikasi kolom Total Potongan muncul dengan nilai yang benar
3. Verifikasi perhitungan Upah Bersih menggunakan formula baru
4. Verifikasi Grand Total Total Potongan dan Upah Bersih konsisten
5. Cek styling dan formatting currency

## Catatan Tambahan

- Perubahan bersifat backward compatible dengan struktur existing
- Formula perhitungan lebih transparan dan akurat  
- Memisahkan antara potongan karyawan (pekerja) dan tanggungan perusahaan (majikan)
- Konsisten dengan praktik payroll standard di Indonesia
