# 🌐 Payroll System Network Setup

Panduan lengkap untuk mengkonfigurasi payroll system agar dapat diakses dari komputer lain dalam jaringan LAN.

## 🚀 Quick Start

### Metode 1: Menggunakan Script Otomatis

```bash
# Jalankan setup otomatis (deteksi IP otomatis)
node network-setup.js

# Setup + start backend
node network-setup.js --backend

# Setup + start frontend
node network-setup.js --frontend

# Setup + start keduanya
node network-setup.js --backend --frontend
```

### Metode 2: Manual Setup

#### 1. Backend Setup
```bash
cd backend
python main.py
# Backend akan berjalan di http://0.0.0.0:8002
```

#### 2. Frontend Setup (dengan custom backend)
```bash
cd frontend

# Ganti 192.168.1.100 dengan IP komputer server
VITE_BACKEND_HOST=192.168.1.100 npm run dev:custom-backend

# Atau gunakan script yang sudah disediakan
npm run dev:lan  # Untuk akses LAN
```

## 📋 Konfigurasi Detail

### Backend Configuration

Backend sudah dikonfigurasi untuk menerima request dari jaringan eksternal:

- **Host**: `0.0.0.0` (menerima request dari mana saja)
- **Port**: `8002`
- **CORS**: Enabled untuk semua origins

### Frontend Configuration

Frontend memiliki beberapa opsi konfigurasi:

#### Opsi 1: Development Mode (Local)
```bash
npm run dev
# http://localhost:5174 -> http://localhost:8002
```

#### Opsi 2: LAN Access
```bash
npm run dev:lan
# http://IP_KOMPUTER:5175 -> http://localhost:8002
```

#### Opsi 3: Custom Backend Host
```bash
VITE_BACKEND_HOST=192.168.1.100 npm run dev:custom-backend
# http://IP_KOMPUTER:5175 -> http://192.168.1.100:8002
```

#### Opsi 4: External Backend (contoh)
```bash
VITE_BACKEND_HOST=192.168.1.100 npm run dev:external
# Menggunakan IP yang sudah diset di package.json
```

## 🔧 Environment Variables

### Backend Variables
```bash
DB_HOST=localhost
DB_PORT=1433
DB_NAME=db_ptrj
```

### Frontend Variables
```bash
VITE_BACKEND_HOST=192.168.1.100  # IP server backend
VITE_BACKEND_PORT=8002           # Port backend
VITE_DEV_MODE=true               # Enable development mode
```

## 🌐 Port Configuration

| Service | Default Port | Network Access |
|---------|-------------|----------------|
| Backend | 8002 | `0.0.0.0:8002` (External) |
| Frontend | 5174 | `localhost:5174` (Local) |
| Frontend LAN | 5175 | `0.0.0.0:5175` (External) |

## 🔥 Firewall Configuration

### Windows Firewall

Untuk mengizinkan akses dari komputer lain:

1. **Buka Windows Firewall Advanced Settings**
2. **Inbound Rules -> New Rule...**
3. **Port Rule -> TCP**
4. **Specific ports**: `8002,5175`
5. **Allow the connection**
6. **Select all profiles (Domain, Private, Public)**
7. **Name**: `Payroll System`

### Atau melalui command line:
```cmd
# Allow backend port
netsh advfirewall firewall add rule name="Payroll Backend" dir=in action=allow protocol=TCP localport=8002

# Allow frontend port
netsh advfirewall firewall add rule name="Payroll Frontend" dir=in action=allow protocol=TCP localport=5175
```

## 📱 Akses dari Client

Dari komputer lain di jaringan yang sama, akses menggunakan:

```
Frontend: http://IP_SERVER:5175
Backend API: http://IP_SERVER:8002
API Documentation: http://IP_SERVER:8002/docs
```

Contoh:
```
Frontend: http://192.168.1.100:5175
Backend API: http://192.168.1.100:8002
```

## 🛠️ Troubleshooting

### Issue: Tidak bisa akses dari komputer lain

#### 1. Cek IP Address
```bash
# Windows
ipconfig
# Cari IPv4 Address (biasanya 192.168.x.x)

# Linux/Mac
ifconfig
# atau
ip addr show
```

#### 2. Cek apakah server berjalan di correct interface
```bash
# Cek apakah backend berjalan di 0.0.0.0
netstat -an | findstr :8002
# Harus menunjukkan: 0.0.0.0:8002

# Cek apakah frontend berjalan di 0.0.0.0
netstat -an | findstr :5175
# Harus menunjukkan: 0.0.0.0:5175
```

#### 3. Test koneksi lokal
```bash
# Test backend
curl http://localhost:8002/health

# Test frontend
curl http://localhost:5175
```

#### 4. Test koneksi dari client
```bash
# Test koneksi ke backend
curl http://IP_SERVER:8002/health

# Test ping
ping IP_SERVER
```

#### 5. Cek Windows Firewall
```cmd
# Cek apakah rule sudah ada
netsh advfirewall firewall show rule name="Payroll Backend"
netsh advfirewall firewall show rule name="Payroll Frontend"
```

### Issue: CORS Error

Backend sudah dikonfigurasi dengan CORS enabled. Jika masih ada error:

1. Pastikan backend berjalan di `0.0.0.0:8002`
2. Cek frontend configuration untuk memastikan menggunakan backend URL yang benar

### Issue: Proxy Error di Frontend

Jika frontend tidak bisa konek ke backend:

1. Pastikan backend sudah berjalan
2. Cek environment variable `VITE_BACKEND_HOST`
3. Restart frontend service setelah mengubah konfigurasi

## 🎯 Best Practices

### Untuk Development
- Gunakan `npm run dev:test` untuk development dengan data dummy
- Gunakan `npm run dev:lan` untuk testing di jaringan lokal
- Pastikan database bisa diakses dari network

### Untuk Production
- Gunakan environment file `.env.production`
- Setup reverse proxy (nginx/Apache) untuk production
- Enable HTTPS dengan SSL certificate
- Setup proper firewall rules

### Security Considerations
- **Development**: CORS enabled untuk semua origins
- **Production**: Batasi CORS hanya untuk domain yang dibutuhkan
- Gunakan authentication dan authorization
- Enable HTTPS di production
- Regular security updates

## 📋 Command Reference

### Backend Commands
```bash
cd backend

# Start server (network ready)
python main.py

# Start dengan port tertentu
uvicorn main:app --host 0.0.0.0 --port 8002

# Development mode dengan auto-reload
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

### Frontend Commands
```bash
cd frontend

# Development (local only)
npm run dev

# LAN Access (proxy ke localhost:8002)
npm run dev:lan

# Custom backend host
VITE_BACKEND_HOST=192.168.1.100 npm run dev:custom-backend

# External backend (predefined IP)
npm run dev:external

# Test mode dengan data dummy
npm run dev:test
```

### Network Commands
```bash
# Get IP address
ipconfig

# Test connection
ping 192.168.1.100

# Test port connection
telnet 192.168.1.100 8002

# Cek active ports
netstat -an | findstr LISTEN
```

## 🆘 Support

Jika mengalami masalah:

1. Cek log file di backend dan frontend
2. Pastikan semua requirements terinstall
3. Verify database connection
4. Test dengan curl untuk debugging
5. Check Windows Firewall settings

Untuk bantuan lebih lanjut, hubungi team development atau lihat error logs di console.