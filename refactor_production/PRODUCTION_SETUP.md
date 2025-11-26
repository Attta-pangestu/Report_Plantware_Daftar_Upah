# Production Setup Guide

## Overview

This guide explains how to run the Payroll Reporting System in production mode using IP address **10.0.0.110** for both frontend and backend servers.

## Configuration Details

### Backend Configuration
- **IP Address**: 10.0.0.110
- **Port**: 8002
- **Mode**: Production (`--mode prod`)
- **Access URL**: `http://10.0.0.110:8002`

### Frontend Configuration
- **IP Address**: 10.0.0.110
- **Port**: 5176
- **Config File**: `vite.config.prod.js`
- **Access URL**: `http://10.0.0.110:5176`

## Quick Start

### Method 1: Using Startup Script (Recommended)
```bash
# Navigate to project root
cd D:\Gawean Rebinmas\Monitoring Database\Plantware_Auto_Report\Daftar_Upah_Reporting\refactor_production

# Run production startup script
start-production.bat
```

### Method 2: Manual Startup

#### Start Backend
```bash
cd backend
python main.py --mode prod --port 8002
```

#### Start Frontend (in separate terminal)
```bash
cd frontend
npm run prod:frontend
```

## Available Scripts

### Frontend Package.json Scripts
```bash
# Development mode (localhost + 10.0.0.128)
npm run dev

# Production mode (10.0.0.110)
npm run prod
npm run prod:frontend    # Start with host 0.0.0.0

# Build for production
npm run build:prod

# Preview production build
npm run preview:prod
```

### Backend Command Line Options
```bash
# Production mode with 10.0.0.110
python main.py --mode prod

# Production mode with custom port
python main.py --mode prod --port 8003

# Custom IP override
python main.py --mode prod --custom-ip 192.168.1.100
```

## Configuration Files

### Backend: `main.py`
- **Production Mode**: `--mode prod` automatically sets IP to 10.0.0.110
- **CORS Origins**: Includes all 10.0.0.110 ports (5173-5184)
- **Host**: Binds to 0.0.0.0 for network access

### Frontend: `vite.config.prod.js`
- **Backend Target**: `http://10.0.0.110:8002`
- **Frontend Port**: 5176
- **Host**: 0.0.0.0 for network access
- **Proxy**: All API routes proxied to backend

## Testing Configuration

### Automated Testing
```bash
# Run configuration test
test-production-config.bat
```

### Manual Testing
```bash
# Test backend health
curl http://10.0.0.110:8002/payroll/health

# Test backend mode info
curl http://10.0.0.110:8002/dev-mode

# Test frontend access
curl -I http://10.0.0.110:5176
```

## Access URLs

Once servers are running:

- **Backend API**: `http://10.0.0.110:8002`
- **Frontend Application**: `http://10.0.0.110:5176`
- **API Documentation**: `http://10.0.0.110:8002/docs`

## Production vs Development Mode

| Feature | Development Mode | Production Mode |
|---------|------------------|-----------------|
| IP Address | localhost + 10.0.0.128 | 10.0.0.110 |
| Backend Port | 8002 | 8002 |
| Frontend Port | 5175 | 5176 |
| Auto-login | Enabled | Disabled |
| Test Data | Default H1H/May 2025 | Real data |
| Debug Logging | Verbose | Minimal |

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   netstat -ano | findstr :8002
   netstat -ano | findstr :5176

   # Kill the process
   taskkill /PID <PID> /F
   ```

2. **CORS Errors**
   - Ensure backend is running with `--mode prod`
   - Check that 10.0.0.110 is in CORS origins list

3. **Connection Refused**
   - Verify both servers are running
   - Check firewall settings for ports 8002 and 5176
   - Ensure IP 10.0.0.110 is accessible on network

4. **Database Connection Issues**
   - Verify database configuration in `Explore_database/config.json`
   - Check database server connectivity from 10.0.0.110

### Logs and Debugging

#### Backend Logs
- Console output shows mode, IP, and port information
- Request logging enabled for all API calls
- Error logs for database and proxy issues

#### Frontend Logs
- Browser console shows proxy configuration
- Network tab in DevTools for API requests
- Build logs for production compilation

## Security Considerations

1. **Network Access**: Servers bind to 0.0.0.0, accessible from any network interface
2. **CORS**: Configured for specific IP ranges only
3. **Authentication**: JWT-based auth (no auto-login in production)
4. **Database**: Use production database credentials

## Performance Optimization

1. **Frontend Build**: Production build includes code splitting and minification
2. **Backend**: Multi-worker support available with `--uvicorn-workers`
3. **Database**: Connection pooling enabled by default
4. **Caching**: Frontend build optimized for caching

## Maintenance

### Regular Tasks
- Monitor server logs for errors
- Check database connection health
- Update CORS origins if IP ranges change
- Backup configuration files

### Updates
- Test changes in development first
- Update configuration files if needed
- Restart servers after configuration changes
- Verify all endpoints after updates