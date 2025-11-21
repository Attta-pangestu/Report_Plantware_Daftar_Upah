# Daftar Upah Reporting System - Production Ready

Aplikasi payroll reporting modern dengan FastAPI backend dan React frontend untuk PT Rebinmas.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │  SQL Server DB  │
│  (React/Vite)   │◄──►│   (FastAPI)      │◄──►│  (db_ptrj)      │
│  Port: 5175     │    │  Port: 8002      │    │ Port: 1433      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

### System Requirements
- **OS**: Windows 10/11
- **Python**: 3.8+
- **Node.js**: 16+
- **Database**: Microsoft SQL Server
- **Memory**: Minimum 4GB RAM
- **Storage**: Minimum 2GB free space

### Required Software
1. **Python 3.8+**
   ```bash
   python --version  # Check version
   ```

2. **Node.js 16+**
   ```bash
   node --version    # Check version
   npm --version     # Check version
   ```

3. **Microsoft SQL Server**
   - SQL Server 2019+ (Local or Remote)
   - ODBC Driver 17 for SQL Server

4. **Git** (for version control)

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/Attta-pangestu/Report_Plantware_Daftar_Upah.git
cd Daftar_Upah_Reporting/refactor_production
```

### 2. Setup Database Configuration
Edit `backend/config.json`:

```json
{
  "database": {
    "driver": "ODBC Driver 17 for SQL Server",
    "server": "localhost",
    "port": 1433,
    "username": "sa",
    "password": "your_password",
    "database_name": "db_ptrj",
    "trusted_connection": false,
    "encrypt": false
  },
  "database_profiles": {
    "local": {
      "driver": "ODBC Driver 17 for SQL Server",
      "server": "localhost",
      "port": 1433,
      "username": "sa",
      "password": "your_password",
      "database_name": "db_ptrj",
      "trusted_connection": false,
      "encrypt": false
    },
    "remote": {
      "driver": "ODBC Driver 17 for SQL Server",
      "server": "10.0.0.110",
      "port": 1433,
      "username": "sa",
      "password": "ptrj@123",
      "database_name": "db_ptrj",
      "trusted_connection": false,
      "encrypt": false
    }
  }
}
```

### 3. Start Backend Server

#### Option A: Local Database
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start backend with local database
python main.py
```

#### Option B: Remote Database
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start backend with remote database
set DB_PROFILE=remote
python main.py
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
```

### 4. Start Frontend Development Server

#### Option A: Default Configuration
```bash
# Navigate to frontend directory (new terminal)
cd frontend

# Install Node.js dependencies
npm install

# Start development server
npx cross-env VITE_BACKEND_URL=http://localhost:8002 npm run dev:test
```

#### Option B: Using Package.json Script
```bash
cd frontend
npm run dev:test
```

**Expected Output:**
```
VITE v5.4.21 ready in 13052 ms

➜  Local:   http://localhost:5175/
➜  Network: http://192.168.137.1:5175/
➜  Network: http://10.0.0.128:5175/
```

### 5. Access Application

1. **Open Browser**: `http://localhost:5175`
2. **Login Credentials**:
   - Username: `admin`
   - Password: `admin`

## 📁 Project Structure

```
refactor_production/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/               # API Endpoints
│   │   ├── models/            # Pydantic Models
│   │   ├── repositories/      # Data Access Layer
│   │   ├── services/          # Business Logic
│   │   └── core/              # Configuration
│   ├── database/              # Database Module
│   │   ├── config/            # DB Configuration
│   │   ├── models/            # DB Models
│   │   ├── queries/           # SQL Queries
│   │   └── services/          # DB Services
│   ├── config.json            # Database Configuration
│   ├── main.py                # Application Entry Point
│   └── requirements.txt       # Python Dependencies
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── pages/             # Main Pages
│   │   ├── components/        # Reusable Components
│   │   ├── services/          # API Services
│   │   ├── context/           # React Context
│   │   └── styles/            # CSS Styles
│   ├── public/                # Static Assets
│   ├── vite.config.test.js    # Vite Configuration
│   └── package.json           # Node.js Dependencies
└── README.md                  # This File
```

## ⚙️ Configuration

### Backend Configuration

#### Database Profiles
The application supports multiple database profiles configured in `config.json`:

- **`local`**: Local SQL Server instance
- **`remote`**: Remote SQL Server (10.0.0.110)
- **Custom profiles**: Add new profiles as needed

#### Environment Variables
```bash
# Database Profile Selection
DB_PROFILE=local        # Default: remote
DB_PROFILE=remote

# Override Database Settings
DB_SERVER=localhost
DB_PORT=1433
DB_NAME=db_ptrj
DB_USER=sa
DB_PASS=password
```

#### Server Configuration
```python
# main.py configuration
HOST="0.0.0.0"          # Server host
PORT=8002               # Server port
DEBUG=False             # Production mode
WORKERS=1               # Number of workers
```

### Frontend Configuration

#### Vite Configuration (`vite.config.test.js`)
```javascript
const isDev = process.env.VITE_DEV_MODE === 'true'
const backendUrl = process.env.VITE_BACKEND_URL || 'http://localhost:8002'

export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 5175,
    proxy: isDev ? {
      '/auth': { target: backendUrl, changeOrigin: true },
      '/employees': { target: backendUrl, changeOrigin: true },
      '/payroll': { target: backendUrl, changeOrigin: true }
    } : { /* production proxy */ }
  }
})
```

#### Environment Variables
```bash
# Development Mode
VITE_DEV_MODE=true
VITE_BACKEND_URL=http://localhost:8002

# Batch Size Configuration
VITE_BATCH_SIZE=200

# Cache Settings
VITE_DISABLE_CACHE=true
VITE_DEV_MODE=true
```

## 🔄 Development Workflow

### Starting Development Environment

1. **Terminal 1 - Backend**:
   ```bash
   cd backend
   python main.py
   ```

2. **Terminal 2 - Frontend**:
   ```bash
   cd frontend
   npx cross-env VITE_BACKEND_URL=http://localhost:8002 npm run dev:test
   ```

3. **Browser**: Access `http://localhost:5175`

### Development Features

#### Backend Development
- **Auto-reload**: Server restarts on code changes
- **Database Connection Pooling**: 20 concurrent connections
- **API Documentation**: `http://localhost:8002/docs`
- **Health Check**: `http://localhost:8002/payroll/health`

#### Frontend Development
- **Hot Module Replacement**: Instant browser updates
- **Development Mode**: Auto-login with admin/admin
- **Proxy Configuration**: Automatic API proxy to backend
- **AG Grid Optimizations**: Enhanced data grid features

## 🛠️ API Endpoints

### Authentication
- `POST /auth/login` - User login
- `GET /auth/test-token` - Development token (dev mode only)

### Payroll Management
- `GET /payroll/report` - Generate payroll report
- `GET /payroll/headers` - Get dynamic headers
- `GET /payroll/columns` - Get column definitions
- `GET /payroll/gangs` - List available gangs
- `GET /payroll/health` - System health check

### Employees
- `GET /employees/list` - List employees
- `GET /employees/search` - Search employees

## 🎯 Application Features

### AG Grid Optimizations
- ✅ **Auto-size columns** on initial render
- ✅ **Integer formatting** (no decimals)
- ✅ **Pinned columns** (No & Name)
- ✅ **Month picker** for period selection
- ✅ **Hide phone column**
- ✅ **Export CSV** functionality
- ✅ **Infinite scrolling** for large datasets

### Frontend Features
- 🎨 **Modern UI** with responsive design
- 🔐 **JWT Authentication** with role-based access
- 📊 **Real-time data** loading with progress indicators
- 🔄 **Dynamic column** generation from database
- 📱 **Mobile-responsive** design
- 🎯 **Auto-hide empty columns**

### Backend Features
- ⚡ **High-performance** data processing
- 🧵 **Multi-threaded** operations
- 🔗 **Connection pooling** (20 connections)
- 🛡️ **Input validation** with Pydantic models
- 📈 **Performance monitoring** and logging

## 🔧 Troubleshooting

### Common Issues

#### 1. Backend Connection Failed
**Problem**: `Login failed for user 'sa' (18456)`

**Solutions**:
```bash
# Check SQL Server service
netstat -an | findstr :1433

# Test connection with different profile
set DB_PROFILE=local
python main.py

# Verify SQL Server Authentication Mode
# - Enable "SQL Server and Windows Authentication mode"
# - Ensure 'sa' account is enabled
```

#### 2. Frontend Proxy Error
**Problem**: `ECONNREFUSED` when connecting to backend

**Solutions**:
```bash
# Ensure backend is running
curl http://localhost:8002/payroll/health

# Check frontend proxy configuration
npx cross-env VITE_BACKEND_URL=http://localhost:8002 npm run dev:test

# Restart frontend
npm run dev:test
```

#### 3. Cross-env Not Found
**Problem**: `cross-env: command not found`

**Solutions**:
```bash
# Install cross-env
npm install --save-dev cross-env

# Or use npx
npx cross-env VITE_BACKEND_URL=http://localhost:8002 npm run dev:test
```

#### 4. Port Already in Use
**Problem**: Port 8002 or 5175 already occupied

**Solutions**:
```bash
# Find process using port
netstat -ano | findstr :8002

# Kill process
taskkill /PID <process_id> /F

# Or use different port
# Backend: Edit main.py
# Frontend: port automatically assigned
```

#### 5. Database Connection Issues
**Problem**: Cannot connect to SQL Server

**Solutions**:
```bash
# Test database connection
python -c "
import pyodbc
conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=db_ptrj;UID=sa;PWD=password;'
try:
    conn = pyodbc.connect(conn_str)
    print('Connected successfully!')
except Exception as e:
    print(f'Connection failed: {e}')
"

# Check ODBC Driver
odbcinst -j
```

### Debug Mode

#### Enable Debug Logging
```bash
# Backend debug mode
export DEBUG=true
python main.py

# Frontend debug mode
npx cross-env VITE_DEV_MODE=true VITE_BACKEND_URL=http://localhost:8002 npm run dev:test
```

#### Monitor Performance
```bash
# Backend performance endpoints
curl http://localhost:8002/payroll/performance/compare

# Frontend browser console
# Open Developer Tools → Console tab
```

## 📚 Development Commands

### Backend Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run with specific database profile
set DB_PROFILE=remote && python main.py

# Run tests
pytest

# Check database connection
python -c "from database.config.settings import connection_string; print(connection_string())"
```

### Frontend Commands
```bash
# Install dependencies
npm install

# Development server
npm run dev:test

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# Install missing package
npm install cross-env --save-dev
```

### Database Operations
```bash
# Test connection to remote server
python test_remote_connection.py

# Test multiple credentials
python test_multiple_users.py

# Run with environment variables
set DB_PROFILE=remote && set DB_PASS=ptrj@123 && python main.py
```

## 🚀 Production Deployment

### Backend Production
```bash
# Install production dependencies
pip install -r requirements.txt

# Set production variables
export DEBUG=false
export WORKERS=4

# Run with Gunicorn (recommended)
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8002

# Or run with Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8002 --workers 4
```

### Frontend Production
```bash
# Build production bundle
npm run build

# Preview production build
npm run preview

# Serve with nginx or apache
# Copy dist/ folder to web server
```

## 📞 Support

For issues and support:
1. Check this documentation first
2. Review error logs in terminal
3. Test database connection with provided scripts
4. Check API documentation: `http://localhost:8002/docs`

---

**Version**: 1.0.0
**Last Updated**: November 2025
**Framework**: FastAPI + React + AG Grid
**Database**: Microsoft SQL Server