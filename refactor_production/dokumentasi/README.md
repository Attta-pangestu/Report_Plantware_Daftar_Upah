# Dokumentasi Arsitektur Sistem Report Plantware Daftar Upah

## Gambaran Umum
Dokumentasi ini menjelaskan arsitektur sistem report daftar upah dari backend hingga rendering di AG Grid frontend.

## Struktur Proyek
```
refactor_production/
├── backend/
│   ├── app/
│   │   ├── api/           # Endpoint API
│   │   ├── core/          # Konfigurasi inti
│   │   ├── models/        # Model data
│   │   ├── repositories/  # Akses ke database
│   │   └── services/      # Business logic
│   └── main.py            # Aplikasi FastAPI utama
├── frontend/
│   ├── src/
│   │   ├── components/    # Komponen React
│   │   ├── pages/         # Halaman utama
│   │   └── services/      # Layanan API frontend
│   ├── package.json       # Dependensi frontend
│   └── vite.config.js     # Konfigurasi Vite
├── dokumentasi/          # Dokumentasi sistem (termasuk diagram)
└── Engine_HTML_Templating/ # Template HTML untuk laporan
```

## Alur Data
1. Frontend mengirim permintaan ke backend
2. Backend mengakses database melalui repositories
3. Services memproses data
4. Data dikembalikan ke frontend
5. AG Grid merender data dalam bentuk tabel interaktif