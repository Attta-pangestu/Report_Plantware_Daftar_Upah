# 🔧 Backend Mode CLI Configuration

## 📖 Overview

Backend sekarang mendukung **Command Line Interface (CLI)** untuk mode deployment dengan konfigurasi IP yang berbeda. Ini memudahkan setup untuk development dan production environment.

## 🚀 Quick Start

### Development Mode (Dual IP)
```bash
# Development mode - supports localhost + 10.0.0.128
python main.py --mode dev

# Development mode dengan custom port
python main.py --mode dev --port 8003

# Development mode dengan custom IP
python main.py --mode dev --custom-ip 192.168.1.100
```

### Production Mode (Single IP)
```bash
# Production mode - menggunakan 10.0.0.110
python main.py --mode prod

# Production mode dengan custom port
python main.py --mode prod --port 8080

# Production mode dengan custom IP
python main.py --mode prod --custom-ip 203.0.113.200
```

### Custom IP Only
```bash
# Custom IP tanpa mode
python main.py --custom-ip 192.168.1.50
```

## 📋 Mode Configuration

### **Development Mode (`--mode dev`)**
- **IP Addresses**: `localhost` + `10.0.0.128`
- **CORS**: Allow all origins (`["*"]`)
- **Use Case**: Development dengan akses dari 2 lokasi
- **Default Port**: 8002

### **Production Mode (`--mode prod`)**
- **IP Address**: `10.0.0.110`
- **CORS**: Allow all origins (`["*"]`)
- **Use Case**: Production server fixed IP
- **Default Port**: 8002

### **Custom IP (`--custom-ip`)**
- **IP Address**: Sesuai yang ditentukan
- **CORS**: Allow all origins
- **Use Case**: Fleksible untuk berbagai environment

## 🔧 Command Line Arguments

### **Required Arguments**
```bash
python main.py
```

### **Optional Arguments**

| Argument | Type | Description | Example |
|----------|------|-------------|---------|
| `--mode` | choice | Run mode (dev/prod) | `--mode dev` |
| `--custom-ip` | string | Custom IP address | `--custom-ip 192.168.1.100` |
| `--port` | int | HTTP port | `--port 8080` |
| `--uvicorn-workers` | int | Number of workers | `--uvicorn-workers 4` |
| `--db-driver` | string | Database driver | `--db-driver mssql` |
| `--db-server` | string | Database server | `--db-server localhost` |
| `--db-port` | int | Database port | `--db-port 1433` |
| `--db-name` | string | Database name | `--db-name mydb` |
| `--db-user` | string | Database user | `--db-user sa` |
| `--db-pass` | string | Database password | `--db-pass password` |
| `--db-profile` | string | Database profile | `--db-profile production` |

## 🖥️ Help Command

```bash
python main.py --help
```

Output:
```
usage: main.py [-h] [--mode {dev,prod}] [--custom-ip CUSTOM_IP]
               [--db-driver DB_DRIVER] [--db-server DB_SERVER]
               [--db-port DB_PORT] [--db-name DB_NAME] [--db-user DB_USER]
               [--db-pass DB_PASS] [--db-profile DB_PROFILE]
               [--uvicorn-workers UVICORN_WORKERS] [--port PORT]

Payroll Backend Server

options:
  -h, --help            show this help message and exit
  --mode {dev,prod}     Run mode: dev=localhost+10.0.0.128, prod=10.0.0.110
  --custom-ip CUSTOM_IP
                        Custom IP address to override mode-based IP
  --port PORT           Backend HTTP port

Mode Examples:
  python main.py --mode dev     # Development mode (localhost + 10.0.0.128)
  python main.py --mode prod    # Production mode (10.0.0.110)
  python main.py --mode dev --custom-ip 192.168.1.100  # Custom IP for dev mode
```

## 📊 Server Information Display

Saat server dimulai, akan menampilkan konfigurasi lengkap:

```
============================================================
PAYROLL BACKEND SERVER CONFIGURATION
============================================================
🚀 Run Mode: dev
🌐 Mode IP: ['localhost', '10.0.0.128']
🔗 Host: 0.0.0.0
📡 Port: 8002
⚙️  Workers: 1
🔧 Dev Mode: False
📋 Access URLs:
   • http://localhost:8002
   • http://10.0.0.128:8002
============================================================
```

## 🔌 API Endpoint Information

### **Dev Mode Endpoint**
```bash
GET /dev-mode
```

Response:
```json
{
  "dev_mode": false,
  "run_mode": "dev",
  "mode_ip": ["localhost", "10.0.0.128"],
  "test_mode": false,
  "test_mode_hardcoded": false,
  "default_gang": "H1H",
  "default_month": 5,
  "default_year": 2025,
  "has_testing_token": true,
  "environment_vars": {
    "TEST_MODE": null,
    "DEV_MODE": null,
    "VITE_DEV_MODE": null
  }
}
```

## 🎯 Use Cases

### **1. Local Development**
```bash
# Single machine development
python main.py
# or
python main.py --mode dev
```

### **2. Multi-Computer Development**
```bash
# Server komputer utama (localhost + 10.0.0.128)
python main.py --mode dev

# Client komputer lain akses via:
# http://10.0.0.128:8002
```

### **3. Production Server**
```bash
# Fixed IP production server
python main.py --mode prod

# Production dengan custom database
python main.py --mode prod --db-server prod-sql --db-name prod_db
```

### **4. Staging Environment**
```bash
# Staging dengan custom IP
python main.py --custom-ip 192.168.1.50 --port 8080
```

### **5. Testing & Debugging**
```bash
# Different port for testing
python main.py --mode dev --port 8003

# Multiple workers for load testing
python main.py --mode prod --uvicorn-workers 4
```

## 🔄 NPM Scripts Integration

### **Root Level Scripts** (`package.json`)
```json
{
  "scripts": {
    "backend:dev": "cd backend && python main.py --mode dev",
    "backend:prod": "cd backend && python main.py --mode prod",
    "backend:custom": "cd backend && python main.py --mode dev --custom-ip 192.168.1.100",
    "dev": "concurrently \"npm run backend:dev\" \"npm run frontend:lan\"",
    "prod": "concurrently \"npm run backend:prod\" \"npm run frontend:lan\"",
    "custom": "concurrently \"npm run backend:custom\" \"npm run frontend:lan\""
  }
}
```

### **Usage**
```bash
# Start development server
npm run dev

# Start production server
npm run prod

# Custom IP setup
npm run custom
```

## 🔍 Troubleshooting

### **Issue: Port already in use**
```bash
# Use different port
python main.py --mode dev --port 8003
```

### **Issue: Can't access from other computers**
1. Check firewall settings
2. Verify IP configuration
3. Test with `curl` from client machine:
```bash
curl http://SERVER_IP:8002/health
```

### **Issue: Database connection error**
```bash
# Override database settings
python main.py --mode dev --db-server 192.168.1.100 --db-name payroll_db
```

### **Issue: Mode IP not showing correctly**
1. Check if arguments are passed correctly
2. Verify server startup logs
3. Test `/dev-mode` endpoint

## 🚀 Best Practices

### **Development**
```bash
# Standard development setup
python main.py --mode dev --port 8002

# With database override for testing
python main.py --mode dev --db-name payroll_test
```

### **Production**
```bash
# Production with multiple workers
python main.py --mode prod --uvicorn-workers 4 --port 80

# Production with custom database
python main.py --mode prod --db-server prod-sql --db-name prod_payroll --db-user prod_user --db-pass secure_pass
```

### **Security**
```bash
# Production with custom IP for security
python main.py --mode prod --custom-ip 10.0.1.100 --port 443
```

## 📋 Configuration Summary

| Mode | IP Addresses | CORS | Use Case |
|------|-------------|------|---------|
| `--mode dev` | `localhost`, `10.0.0.128` | `["*"]` | Multi-location development |
| `--mode prod` | `10.0.0.110` | `["*"]` | Fixed production server |
| `--custom-ip IP` | Custom IP | `["*"]` | Flexible deployment |
| Default | `localhost` | Limited | Single machine only |

---

**🔧 CLI mode provides flexible deployment options for different environments!**