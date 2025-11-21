# 🚀 Quick Start Guide

## 1️⃣ Start Backend Server

```bash
# Navigate to backend
cd backend

# Install dependencies (first time only)
pip install -r requirements.txt

# Start backend
python main.py
```

**Expected Output:**
```
INFO: Uvicorn running on http://0.0.0.0:8002
```

## 2️⃣ Start Frontend Server

```bash
# Navigate to frontend (new terminal)
cd frontend

# Install dependencies (first time only)
npm install

# Start frontend
npx cross-env VITE_BACKEND_URL=http://localhost:8002 npm run dev:test
```

**Expected Output:**
```
➜  Local:   http://localhost:5175/
```

## 3️⃣ Access Application

🌐 **URL**: `http://localhost:5175`
👤 **Username**: `admin`
🔑 **Password**: `admin`

## 🔧 Database Configuration

Edit `backend/config.json`:

```json
{
  "database_profiles": {
    "local": {
      "server": "localhost",
      "username": "sa",
      "password": "your_password"
    },
    "remote": {
      "server": "10.0.0.110",
      "username": "sa",
      "password": "ptrj@123"
    }
  }
}
```

## ⚡ Remote Database

```bash
# Start with remote database
cd backend
set DB_PROFILE=remote
python main.py
```

## 🛠️ Common Commands

### Backend
```bash
# Test database connection
python test_remote_connection.py

# Run with different profile
set DB_PROFILE=local && python main.py
```

### Frontend
```bash
# Install missing package
npm install cross-env --save-dev

# Alternative start method
npm run dev:test

# Build for production
npm run build
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `cross-env not found` | `npm install cross-env --save-dev` |
| Backend connection failed | Check `config.json` database settings |
| Port already in use | `netstat -ano | findstr :8002` then `taskkill /PID <id> /F` |
| Login failed | Verify SQL Server authentication mode |

## 📞 Application Features

✅ **AG Grid Optimizations**
- Auto-size columns
- Integer formatting (no decimals)
- Pinned columns (No & Name)
- Month picker
- Export CSV

✅ **Backend Features**
- Multi-threaded processing
- Connection pooling (20 connections)
- JWT authentication

✅ **Frontend Features**
- Real-time data loading
- Dynamic column generation
- Mobile-responsive design

---

**Need Help?** Check `README.md` for detailed documentation.