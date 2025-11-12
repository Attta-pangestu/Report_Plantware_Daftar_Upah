--- 
date: 2025-11-10
tags: [AI-Context, Ikhtisar, Upah-Bersih, Formula-Payroll]
---

# Ikhtisar Kalkulasi Upah Bersih - Plantware Auto Report

## 📌 Formula Utama

### **Upah Bersih = Upah Kotor - Total Potongan**

## 🔍 Komponen Kalkulasi

### 1. **Upah Kotor (Gross Salary)**
Upah Kotor adalah total pendapatan karyawan sebelum dipotong, terdiri dari:
- **Gaji Pokok** (Jumlah HK × Upah Dasar)
- **Total Tunjangan** (Beras, Jabatan, Masa Kerja, Lembur, dll)
- **Total Premi** (Brondol, Pruning, Panen, + Koreksi sebagai nilai negatif)

\
### 2. **Total Potongan (Total Deductions)**
Total Potongan adalah jumlah semua potongan yang menjadi tanggungan karyawan:
- **BPJS Kesehatan Pekerja** (1% dari base calculation)
- **BPJS Pensiun Pekerja** (1% dari gaji pokok minimum)
- **Iuran SPSI** (Sesuai query database)
- **PPh21** (Pajak Penghasilan Pasal 21)

\
### 3. **Upah Bersih (Net Salary)**
Upah Bersih adalah take-home pay yang diterima karyawan:

\
## 💡 Contoh Perhitungan

### Tabel Perhitungan Per Employee

| Komponen | Jumlah (Rp) | Keterangan |
|----------|-------------|------------|
| **PENDAPATAN** | | |
| Gaji Pokok | 5.000.000 | 25 HK × Rp200.000 |
| Total Tunjangan | 2.000.000 | Beras + Jabatan + Masa Kerja + Lembur |
| Total Premi | 1.500.000 | Brondol + Pruning + Panen (-Koreksi) |
| **Upah Kotor** | **8.500.000** | **Total PENDAPATAN** |
| | | |
| **POTONGAN** | | |
| BPJS Kesehatan Pekerja | 85.000 | 1% dari base calculation |
| BPJS Pensiun Pekerja | 38.766 | 1% dari gaji pokok minimum |
| Iuran SPSI | 50.000 | Sesuai database |
| PPh21 | 300.000 | Sesuai database |
| **Total Potongan** | **473.766** | **Total POTONGAN** |
| | | |
| **UPAH BERSIH** | **8.026.234** | **8.500.000 - 473.766** |

## 📊 Visualisasi Flow

\
## ⚙️ Implementasi dalam Kode

### Level Employee (Line 1244-1269)
\
### Level Grand Total (Line 1763, 1782)
\
## 🎯 Keuntungan Formula Ini

### 1. **Transparansi**
- Karyawan dapat melihat dengan jelas komponen pendapatan
- Potongan yang dikenakan terlihat rinci
- Perhitungan bersih dapat dipahami dengan mudah

### 2. **Akurasi**
- Upah bersih mencerminkan take-home pay yang sebenarnya
- Tidak ada hidden deductions
- Sesuai dengan praktik payroll standard

### 3. **Kepatuhan**
- Memisahkan tanggungan karyawan vs perusahaan
- BPJS Majikan tidak termasuk dalam potongan karyawan
- Sesuai dengan regulasi perpajakan Indonesia

### 4. **Audit Trail**
- Setiap komponen terdokumentasi dengan jelas
- Mudah untuk audit internal maupun eksternal
- Konsisten dari level employee hingga grand total

## 🔍 Validasi Hasil

### Checklist Validasi:
- [ ] Total Potongan = Jumlah 4 komponen potongan
- [ ] Upah Bersih = Upah Kotor - Total Potongan  
- [ ] Grand Total Upah Bersih = Σ(Upah Bersih per employee)
- [ ] Format currency sesuai (comma separator, 0 decimal)
- [ ] Tidak ada nilai negatif (kecuali koreksi)

### Contoh Validasi:
\
## 📝 Catatan Penting

1. **Koreksi Selalu Negatif**: Koreksi diperlakukan sebagai nilai negatif dalam Total Premi
2. **BPJS Majikan Bukan Potongan**: BPJS Kesehatan Majikan (4%) dan Pensiun Majikan (2%) adalah tanggungan perusahaan
3. **Komponen Tetap**: Formula ini konsisten untuk semua level karyawan
4. **Scalability**: Berlaku untuk jumlah employee berapa pun

---
*Update: 2025-11-10 - Implementasi kolom Total Potongan dan formula Upah Bersih yang baru*
