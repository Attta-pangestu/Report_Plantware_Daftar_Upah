# Multi-Computer Access Setup

This document explains how to configure the payroll system for multi-computer access, allowing users to access the application from different computers on the network.

## Configuration Changes Made

### 1. Backend Requirements
Updated `backend/requirements.txt` with new dependencies:
- `passlib[bcrypt]==1.7.4` (exact version)
- `bcrypt==4.0.1` (exact version)
- Other dependencies remain the same

### 2. CORS Configuration
Updated `backend/main.py` to allow cross-origin requests:
- In development mode (`DEV_MODE=true`), allows all origins (`*`)
- In production mode, restricts to specific origins
- Supports environment variable `CORS_ALLOW_ORIGINS` for custom origins

### 3. Frontend Proxy Configuration
Updated `frontend/vite.config.js` with dynamic backend routing:
- Supports environment variables for backend host and port
- Added proxy error logging for debugging
- Defaults to `localhost:8004` but can be customized

## Usage Instructions

### For Local Development (Same Computer)
1. Start backend:
   ```bash
   cd backend
   DEV_MODE=true python -m uvicorn main:app --host 0.0.0.0 --port 8004 --reload
   ```

2. Start frontend:
   ```bash
   cd frontend
   npm run dev:test
   ```

3. Access at: `http://localhost:5175`

### For Multi-Computer Access

#### Option 1: Using Default Network Setup
1. **Backend Server** (on main computer):
   ```bash
   cd backend
   DEV_MODE=true python -m uvicorn main:app --host 0.0.0.0 --port 8004 --reload
   ```

2. **Frontend Server** (on main computer):
   ```bash
   cd frontend
   npm run dev:network
   ```

3. **Client Access** (from other computers):
   - Find the IP address of the main computer (e.g., `192.168.1.100`)
   - Access at: `http://192.168.1.100:5175`

#### Option 2: Using Custom Backend Host
If the backend is running on a different computer:

1. **Backend Server** (on server computer):
   ```bash
   cd backend
   DEV_MODE=true python -m uvicorn main:app --host 0.0.0.0 --port 8004 --reload
   ```

2. **Frontend Server** (on client computer):
   ```bash
   cd frontend
   VITE_BACKEND_HOST=192.168.1.100 VITE_BACKEND_PORT=8004 npm run dev:custom-backend
   ```

Replace `192.168.1.100` with the actual IP address of the backend server.

#### Option 3: Using Environment Variables
Create a `.env` file in the frontend directory:
```env
VITE_BACKEND_HOST=192.168.1.100
VITE_BACKEND_PORT=8004
```

Then run:
```bash
cd frontend
npm run dev:custom-backend
```

## Environment Variables

### Backend
- `DEV_MODE=true` - Enables development mode and permissive CORS
- `CORS_ALLOW_ORIGINS` - Comma-separated list of allowed origins

### Frontend
- `VITE_BACKEND_HOST` - Backend server IP address or hostname
- `VITE_BACKEND_PORT` - Backend server port (default: 8004)
- `BACKEND_HOST` - Alternative backend host variable
- `BACKEND_PORT` - Alternative backend port variable

## Network Configuration Tips

### Finding Your IP Address
- **Windows**: `ipconfig` (look for "IPv4 Address")
- **Mac/Linux**: `ifconfig` or `ip addr` (look for "inet" address)

### Firewall Settings
Make sure the following ports are open on the backend server:
- Port `8004` for backend API
- Port `5175` for frontend (if running frontend on same server)

### Testing Connectivity
1. **Test backend access**: `http://[IP]:8004/docs` (should show FastAPI docs)
2. **Test frontend access**: `http://[IP]:5175` (should show the application)

## Available NPM Scripts

```bash
# Development
npm run dev                    # Standard development
npm run dev:test              # Development with test mode (port 5175)
npm run dev:5175              # Development on port 5175
npm run dev:network           # Network access with default backend
npm run dev:custom-backend    # Custom backend configuration

# Production
npm run build                 # Build for production
npm run preview              # Preview production build
npm run test                 # Run tests
```

## Troubleshooting

### CORS Issues
- Ensure `DEV_MODE=true` on the backend for permissive CORS
- Check browser console for CORS errors
- Verify firewall settings

### Proxy Issues
- Check the terminal output for proxy configuration logs
- Verify backend server is running and accessible
- Check network connectivity between computers

### Connection Refused
- Verify both computers are on the same network
- Check IP addresses and ports
- Ensure firewall allows the connections
- Verify backend and frontend are running with correct host settings

## Security Notes

- Development mode allows all origins (`*`) - suitable for development only
- For production, configure specific allowed origins via `CORS_ALLOW_ORIGINS`
- Consider using HTTPS for production deployments
- Keep backend dependencies updated for security patches