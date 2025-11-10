--- 
date: 2025-11-10
tags: [AI-Context, Laporan-Upah, Koreksi, Perbaikan]
--- 

# Modifikasi Koreksi Laporan Upah - Plantware Auto Report

## Ringkasan Perubahan

Melakukan perbaikan pada perhitungan koreksi di laporan daftar upah agar ditampilkan sebagai nilai negatif sesuai permintaan user.

## Lokasi File yang Diubah

### 1. Engine Database
- **File**: Engine_HTML_Templating/template_report/ui/daftar_upah_engine_real_database.py
- **Fungsi**: get_employee_koreksi_amount() (line 856)
- **Perubahan**: Menambahkan -abs() pada return value untuk memastikan koreksi selalu negatif

### 2. Template HTML
- **File**: Engine_HTML_Templating/template_report/ui/daftar_upah_template_final.html
- **Header**: Line 795 - Menambahkan '(Minus)' pada label KOREKSI
- **CSS**: Line 393-413 - Menambahkan styling khusus untuk kolom koreksi

## Detail Perubahan

### Engine Database (daftar_upah_engine_real_database.py)

```python
# Sebelum
return total_amount

# Sesudah
# Koreksi harus ditampilkan sebagai nilai negatif (pengurangan)
return -abs(total_amount)
```

### Template HTML (daftar_upah_template_final.html)

#### Header Modification
```html
<!-- Sebelum -->
<td class="header-cell sub-header-premi">KOREKSI</td>

<!-- Sesudah -->
<td class="header-cell sub-header-premi">KOREKSI<br>(Minus)</td>
```

#### CSS Styling
```css
/* Koreksi Column - Special styling for negative values */
.col-koreksi {
    background: #ffebee !important;
    color: #c62828 !important;
    text-align: right !important;
    padding-right: 5px !important;
    font-weight: bold !important;
    font-size: 9pt !important;
    border: 1px solid #d0d0d0 !important;
}

/* Koreksi column in alternating rows */
.employee-row:nth-child(odd) .col-koreksi {
    background: #ffcdd2 !important;
    color: #b71c1c !important;
}

.employee-row:nth-child(even) .col-koreksi {
    background: #ffebee !important;
    color: #c62828 !important;
}
```

## Dampak Perubahan

1. **Jumlah Total Premi**: Akan berkurang karena koreksi sekarang bernilai negatif
2. **Jumlah Upah Kotor**: Akan berkurang karena Total Premi yang termasuk koreksi negatif
3. **Visual Indikator**: Kolom koreksi sekarang memiliki:
   - Warna merah background (#ffebee/#ffcdd2)
   - Text merah tua (#c62828/#b71c1c)
   - Label '(Minus)' di header
   - Alignment right untuk nilai negatif

## Alur Perhitungan

```
Koreksi (dari database) → -abs(nilai) → Total Premi ↓ → Jumlah Upah Kotor ↓
```

## Testing yang Diperlukan

1. Generate laporan dengan data koreksi positif di database
2. Verifikasi nilai koreksi muncul sebagai negatif di laporan
3. Verifikasi Total Premi dan Upah Kotor terhitung dengan benar
4. Verifikasi styling koreksi berwarna merah sesuai CSS

## Catatan Tambahan

- Perubahan bersifat backward compatible
- Tidak mempengaruhi perhitungan lain diluar koreksi
- Koreksi tetap diambil dari query yang sama, hanya nilai return yang diubah
