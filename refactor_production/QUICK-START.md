# 🚀 Quick Start Guide - Network Access

## ⚡ Super Quick Start (Windows)

1. **Double-click file ini**: `start-network.bat`
2. **Pilih opsi 3** (Start Both Services)
3. **Buka browser**: `http://IP_KOMPUTER:5175`

## 🌐 Cara Akses dari Komputer Lain

### Langkah 1: Jalankan Server

**Opsi A: Script Otomatis (Recommended)**
```bash
# Windows
start-network.bat

# Node.js
node network-setup.js --backend --frontend
```

**Opsi B: Manual**
```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev:lan
```

### Langkah 2: Cari IP Address Komputer Server

**Windows:**
```cmd
ipconfig
# Cari "IPv4 Address" (contoh: 192.168.1.100)
```

**Linux/Mac:**
```bash
ifconfig
# atau
ip addr show
```

### Langkah 3: Akses dari Client

Buka browser di komputer client dan akses:
```
http://IP_KOMPUTER_SERVER:5175
```

Contoh:
```
http://192.168.1.100:5175
```

## 🔧 Konfigurasi Firewall (Wajib)

### Windows Otomatis
```cmd
# Jalankan sebagai Administrator
netsh advfirewall firewall add rule name="Payroll Backend" dir=in action=allow protocol=TCP localport=8002
netsh advfirewall firewall add rule name="Payroll Frontend" dir=in action=allow protocol=TCP localport=5175
```

### Windows Manual
1. Buka **Windows Firewall Advanced Settings**
2. **Inbound Rules → New Rule...**
3. **Port → TCP → Specific ports**: `8002,5175`
4. **Allow the connection**
5. **Name**: `Payroll System`

## 📱 Testing Koneksi

### Test dari Server
```bash
# Test backend
curl http://localhost:8002/health

# Test frontend
curl http://localhost:5175
```

### Test dari Client
```bash
# Test koneksi server
ping IP_SERVER

# Test backend
curl http://IP_SERVER:8002/health

# Test frontend
curl http://IP_SERVER:5175
```

## 🆘 Troubleshooting

### ❌ "Cannot connect to backend"
**Solusi:**
1. Pastikan backend berjalan: `python main.py`
2. Cek IP: `ipconfig`
3. Test: `curl http://IP_SERVER:8002/health`
4. Coba restart frontend

### ❌ "Connection refused"
**Solusi:**
1. Cek firewall Windows
2. Pastikan port tidak diblokir
3. Restart service

### ❌ "CORS error"
**Solusi:**
1. Backend harus berjalan di `0.0.0.0:8002`
2. Frontend harus menggunakan IP backend yang benar

## 📋 Port Information

| Service | Port | Access URL |
|---------|------|------------|
| Backend | 8002 | `http://IP:8002` |
| Frontend | 5175 | `http://IP:5175` |
| API Docs | 8002 | `http://IP:8002/docs` |

## 🎯 Default Login

```
Username: admin
Password: admin
```

## 📞 Help

Jika masih ada masalah:
1. Cek file `NETWORK-SETUP.md` untuk detail lengkap
2. Pastikan semua services berjalan
3. Test dengan `curl` untuk debugging
4. Cek Windows Firewall settings

---

**📝 Catatan:**
- Server dan client harus dalam jaringan yang sama
- Pastikan tidak ada antivirus yang memblokir port
- Gunakan kabel network untuk koneksi yang lebih stabil