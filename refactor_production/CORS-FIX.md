# 🔧 CORS Fix - Frontend Backend Connection

## ❌ Masalah yang Diperbaiki

Frontend mencoba mengakses `http://localhost:8002` dari origin `http://10.0.0.110:5175` menyebabkan CORS error:

```
Access to XMLHttpRequest at 'http://localhost:8002/dev-mode' from origin 'http://10.0.0.110:5175'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## ✅ Solusi yang Diimplementasikan

### 1. **Auto IP Detection di Vite Config**
File: `frontend/vite.config.js`

```javascript
// Auto-detect local IP address for network access
const getLocalIP = () => {
  try {
    const { networkInterfaces } = require('os')
    const nets = networkInterfaces()

    for (const name of Object.keys(nets)) {
      for (const net of nets[name]) {
        // Skip internal and non-IPv4 addresses
        if (net.family === 'IPv4' && !net.internal) {
          return net.address
        }
      }
    }
    return 'localhost'
  } catch (e) {
    return 'localhost'
  }
}

// Network mode detection
const isNetworkMode = process.env.npm_config_host === '0.0.0.0' ||
                      process.env.HOST === '0.0.0.0' ||
                      process.argv.includes('--host') ||
                      process.env.NODE_ENV === 'network'

if (isNetworkMode) {
  const localIP = getLocalIP()
  console.log(`🌐 Network mode detected, using IP: ${localIP}`)
  return `http://${localIP}:${customPort}`
}
```

### 2. **Dynamic Backend URL Detection**
File: `frontend/src/utils/httpSetup.js`

```javascript
const getBackendURL = () => {
  const _port = (import.meta.env?.VITE_BACKEND_PORT || import.meta.env?.BACKEND_PORT || '8002')
  let _host = (import.meta.env?.VITE_BACKEND_HOST || import.meta.env?.BACKEND_HOST)

  // If no custom host is specified, detect if we should use the current host IP
  if (!_host || _host === 'localhost') {
    // Check if we're accessing from an IP address (not localhost)
    const currentHost = window.location.hostname
    if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
      _host = currentHost
      console.log(`🌐 Detected network access, using backend: ${_host}`)
    } else {
      _host = 'localhost'
    }
  }

  return `http://${_host}:${_port}`
}

const _url = getBackendURL()
axios.defaults.baseURL = _url
```

### 3. **Network Mode di NPM Scripts**
File: `frontend/package.json`

```json
{
  "scripts": {
    "dev:network": "cross-env VITE_DEV_MODE=true NODE_ENV=network vite --host 0.0.0.0 --port 5175",
    "dev:custom-backend": "cross-env VITE_DEV_MODE=true NODE_ENV=network vite --host 0.0.0.0",
    "dev:lan": "cross-env VITE_DEV_MODE=true NODE_ENV=network vite --host 0.0.0.0 --port 5175"
  }
}
```

### 4. **CORS Configuration di Backend**
File: `backend/main.py`

```python
def _allowed_origins():
    # For multi-computer access, allow all origins in development mode
    if DEV_MODE:
        return ["*"]  # Allow all origins in development mode

    return [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ]
```

## 🚀 Cara Penggunaan yang Benar

### **Metode 1: Auto-Detection (Recommended)**
```bash
# Backend
cd backend
python main.py

# Frontend - akan auto-detect IP
cd frontend
npm run dev:lan
```

### **Metode 2: Custom Backend Host**
```bash
# Backend
cd backend
python main.py

# Frontend dengan IP custom
cd frontend
VITE_BACKEND_HOST=10.0.0.110 npm run dev:custom-backend
```

### **Metode 3: Script Otomatis**
```bash
# Auto-start kedua services dengan IP detection
node network-setup.js --backend --frontend
```

## 📋 Alur Kerja Auto-Detection

1. **Frontend Start** → Detect `--host 0.0.0.0` atau `NODE_ENV=network`
2. **IP Detection** → Get local IP (ex: `10.0.0.110`)
3. **Vite Proxy** → Route requests ke `http://10.0.0.110:8002`
4. **HTTP Setup** → Auto-detect current hostname sebagai backend URL
5. **Backend CORS** → Allow semua origins di DEV_MODE

## 🔍 Debug Console Logs

### **Vite Config Logs:**
```
Proxy configuration: {
  isDev: true,
  backendTarget: 'http://10.0.0.110:8002',
  envVars: { NODE_ENV: 'network', VITE_DEV_MODE: 'true' }
}
🌐 Network mode detected, using IP: 10.0.0.110
```

### **HTTP Setup Logs:**
```
🔗 HTTP Setup - Backend URL: http://10.0.0.110:8002
🌐 Current Frontend Host: 10.0.0.110
🌐 Detected network access, using backend: 10.0.0.110
```

## 🧪 Testing

### **Test Backend Connection:**
```bash
# Dari komputer server
curl http://10.0.0.110:8002/health

# Dari komputer client
curl http://10.0.0.110:8002/health
```

### **Test Frontend Access:**
```bash
# Buka browser di client
http://10.0.0.110:5175
```

### **Check Console Logs:**
- Buka browser developer tools
- Cek console untuk logs:
  - `🔗 HTTP Setup - Backend URL: http://10.0.0.110:8002`
  - `🌐 Detected network access, using backend: 10.0.0.110`

## ⚠️ Common Issues & Solutions

### **Issue: Masih localhost:8002 di console**
**Solution**: Pastikan frontend dijalankan dengan `npm run dev:lan` atau set `NODE_ENV=network`

### **Issue: CORS masih error**
**Solution**:
1. Pastikan backend berjalan dengan `DEV_MODE=true`
2. Restart frontend setelah mengubah config
3. Cek backend logs untuk CORS configuration

### **Issue: Tidak bisa auto-detect IP**
**Solution**:
1. Pastikan komputer terhubung ke network
2. Cek dengan `ipconfig` (Windows) atau `ifconfig` (Linux/Mac)
3. Gunakan manual mode: `VITE_BACKEND_HOST=IP_ADDRESS npm run dev:custom-backend`

## 🎯 Best Practices

1. **Gunakan `npm run dev:lan`** untuk jaringan lokal
2. **Pastikan DEV_MODE=true** di backend untuk CORS
3. **Check console logs** untuk debugging
4. **Restart services** setelah mengubah konfigurasi
5. **Use script otomatis** untuk kemudahan

---

**🔧 Fix ini memastikan frontend dan frontend dapat berkomunikasi dengan benar dalam jaringan LAN!**