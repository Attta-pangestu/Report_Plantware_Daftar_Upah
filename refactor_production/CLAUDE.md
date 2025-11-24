# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a refactored production-ready payroll reporting system ("Daftar Upah Reporting") for PT Rebinmas that generates employee payroll data with a modern frontend-backend architecture. The system features dynamic header generation, threaded data processing, and real-time reporting capabilities.

## Architecture

The project uses a modern full-stack architecture with clear separation of concerns:

### Backend (FastAPI)
- **Framework**: FastAPI with uvicorn server
- **Database**: Microsoft SQL Server with connection pooling
- **Authentication**: JWT-based authentication with role-based access control
- **Architecture Pattern**: Layered architecture with services, repositories, and API layers

### Frontend (React + Vite)
- **Framework**: React 18 with Vite build tool
- **UI Grid**: AG-Grid for data display and manipulation
- **Styling**: CSS with modular report styles
- **State Management**: React Context for authentication and data

### Key Components

#### Backend Structure
- `backend/app/api/` - REST API endpoints (auth, payroll, employees, reports)
- `backend/app/services/` - Business logic layer (payroll, header generation, threading)
- `backend/app/repositories/` - Data access layer with database queries
- `backend/app/models/` - Pydantic models for data validation
- `backend/app/core/` - Configuration, security, and core utilities
- `backend/database/` - Database connection pooling and query management

#### Frontend Structure
- `frontend/src/pages/` - Main application pages (Report, Login, Employees)
- `frontend/src/components/` - Reusable UI components (Modal, LoadingScreen, AgGridWrapper)
- `frontend/src/context/` - React Context providers (Auth, Headers)
- `frontend/src/services/` - API service layer for backend communication

## Common Development Commands

### Backend Development
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run backend tests
pytest

# Run specific test file
pytest tests/test_specific_file.py

# Run tests with coverage
pytest --cov=app tests/

# Run development server (default port 8002)
python main.py
# OR
uvicorn main:app --host 0.0.0.0 --port 8002 --reload

# Run with environment variables
DEV_MODE=true VITE_DEV_MODE=true python main.py

# Run with specific port
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Development
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server (default port 5173)
npm run dev

# Run with development mode enabled (port 5175)
npm run dev:test

# Run on alternative port 5175
npm run dev:5175

# Build for production
npm run build

# Preview production build
npm run preview

# Run frontend tests
npm run test

# Run tests in watch mode
npm run test -- --watch

# Run tests with coverage
npm run test -- --coverage
```

### Database Operations
```bash
# Test database connection
cd backend
python -c "from database.services.database import Database; print('Connection healthy' if Database.instance().test_connection() else 'Connection failed')"

# Initialize database with connection pooling
cd backend
python -c "from database.services.database import Database; db = Database.instance(pool_size=5); print('Database initialized')"

# Run database queries
cd backend
python -c "from database.services.database import Database; db = Database.instance(); results = db.query_all('SELECT * FROM employees', []); print(results)"
```

## Configuration

### Environment Variables
- `DEV_MODE` - Enable development mode (auto-login, default values)
- `VITE_DEV_MODE` - Frontend development mode flag
- `TEST_MODE` - Enable test mode with hardcoded defaults
- `DEFAULT_GANG` - Default gang code for testing (H1H)
- `DEFAULT_MONTH` - Default month for testing (5)
- `DEFAULT_YEAR` - Default year for testing (2025)

### Database Configuration
Database configuration is loaded from `../Explore_database/config.json` with fallback to environment variables:
- `DB_DRIVER` - Database driver (mssql)
- `DB_SERVER` - Database server address
- `DB_PORT` - Database port (1433)
- `DB_NAME` - Database name (db_ptrj)
- `DB_USER` - Database username
- `DB_PASS` - Database password

## Key Features

### Dynamic Header Generation
- Automatic column detection based on data
- Hierarchical header structure (up to 3 levels)
- Threaded processing for performance optimization
- Auto-hide empty columns functionality

### Payroll Processing
- Multi-threaded data extraction for large datasets
- Real-time payroll calculations
- Support for various allowances and deductions
- Performance benchmarking and monitoring

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (admin/user)
- Division-based data access restrictions
- Development mode with auto-login

## API Endpoints

### Payroll Management
- `GET /payroll/report` - Generate payroll report with pagination
- `GET /payroll/headers` - Get dynamic column headers
- `GET /payroll/columns` - Get column definitions
- `GET /payroll/gangs` - List available gang codes
- `GET /payroll/divisions` - List available divisions

### Performance & Debugging
- `GET /payroll/health` - System health check
- `GET /payroll/performance/compare` - Compare sequential vs threaded performance
- `GET /payroll/debug/employee_query` - Debug employee queries
- `GET /payroll/debug/employees` - Debug employee data

### Exports & Validation
- `GET /payroll/export_html` - Export HTML report
- `GET /payroll/validate_html` - Validate against reference HTML
- `GET /payroll/reference_html` - Load reference HTML file

## Key Architecture Patterns

### API Endpoints: Headers vs Columns
The system has two distinct but related endpoints:

- **`/payroll/headers`**: Generates dynamic header structures from database queries, returns metadata and hierarchy
- **`/payroll/columns`**: Converts headers into AG-Grid column definitions with client-side formatting
- Headers endpoint provides raw data structure with performance metrics
- Columns endpoint provides grid-ready configuration with field mapping and styling

### Dynamic Header Structure Configuration
The system uses JSON-based header configuration stored in `backend/struktur/struktur_header_report.json`:

- **Three-level hierarchy**: Level 1 (main categories), Level 2 (sub-categories), Level 3 (unit columns)
- **Dynamic column generation**: Based on database queries and business rules
- **Field mapping**: Converts JSON structure IDs to database field names via `_map_to_data_field()`
- **Data path extraction**: Critical to use `hierarchy` path, not `generated_headers` path in `get_column_definitions()`

### Attendance/Absensi Group Structure
The ABSENSI group follows this hierarchy:
```
Level 1: ABSENSI (colspan: 3)
  └── Level 2: KEHADIRAN → hari_kerja
  └── Level 2: KETIDAKHADIRAN (colspan: 7)
      ├── cuti_tahunan → cuti_tahunan_hari
      ├── cuti_sakit_haid → cuti_sakit_haid_hari
      ├── cuti_minggu → cuti_minggu_hari
      ├── cuti_nasional → cuti_nasional_hari
      ├── cth → tidak_hadir_cth
      ├── alpa → tidak_hadir_alpa
      └── total_ketidakhadiran → total_ketidakhadiran
  └── Level 2: TOTAL HK → jumlah_hk
```

### Authentication Flow
- JWT-based authentication with role-based access control (ADMIN, USER, MANAGER)
- Token management via `js-cookie` in frontend with React Context state
- Development mode provides auto-login (admin/admin credentials)
- Division-based data access restrictions enforced at service layer

### Database Layer Architecture
- Singleton pattern for connection pooling with configurable pool sizes
- JSON-based query organization using parameterized statements (`?` placeholders)
- Transaction support with context managers for atomic operations
- Separate configuration for development vs production environments

### Frontend State Management
- React Context for authentication state and headers data
- AG-Grid with infinite scrolling for large datasets (200-row blocks)
- Dynamic column definitions derived from backend header generation
- Performance optimizations including caching and batch loading

## Development Workflow

### Running the Full Application
1. Start the backend server: `cd backend && python main.py`
2. Start the frontend development server: `cd frontend && npm run dev:test`
3. Access the application at `http://localhost:5175`
4. Backend API available at `http://localhost:8002`

### Testing Performance
- Use `/payroll/performance/compare` endpoint to benchmark threaded vs sequential processing
- Monitor memory usage with `monitor=true` parameter in report endpoints
- Enable threading with `use_threading=true` for large datasets

### Debugging
- Check system health: `GET /payroll/health`
- Debug database queries: `GET /payroll/debug/employee_query`
- Validate data consistency: `GET /payroll/validate_html`

## Threaded Processing

The system implements multi-threaded data processing for performance optimization:
- `ThreadedHeaderService` - Parallel header generation
- `ThreadedDataExtractor` - Parallel payroll data extraction
- Connection pooling for concurrent database access
- Configurable thread pool sizes

## Frontend Grid Configuration

AG-Grid is configured with:
- Dynamic column definitions from backend
- Pinned bottom rows for summaries
- Auto-sizing based on content
- Export capabilities
- Performance optimizations for large datasets

## Testing Notes

- Development mode auto-configures with test data (H1H gang, May 2025)
- Use `TEST_MODE=true` for consistent testing environment
- Frontend supports mock authentication in development mode
- Database connection pooling handles concurrent requests efficiently

## Common Issues & Solutions

### Authentication Issues (401 Unauthorized)
- **Problem**: Getting 401 errors even when logged in
- **Solution**: Check JWT token expiration and refresh mechanism
- **Debug**: Check browser's Application tab for cookie `access_token`
- **Development**: In dev mode, auto-login should prevent this, but token may still expire

### Cookie Management
- The system uses `js-cookie` for token management
- Cookies are configured in `frontend/src/services/cookieService.js`
- Authentication state is managed through React Context in `frontend/src/context/AuthContext.jsx`
- Ensure CORS settings allow credentials: `credentials: 'include'` in axios requests

### Common Debugging Commands
```bash
# Check backend health
curl http://localhost:8002/payroll/health

# Test authentication token
curl -H "Authorization: Bearer <token>" http://localhost:8002/payroll/gangs

# Monitor database connections
python -c "from database.services.database import Database; print(Database.instance().pool_status())"
```

### Header Generation Debugging
When modifying attendance/absensi fields:
1. **Update JSON structure**: Modify `backend/struktur/struktur_header_report.json`
2. **Add field mappings**: Update `_map_to_data_field()` in `backend/app/services/header_service.py`
3. **Test headers API**: `GET /payroll/headers` returns hierarchical structure
4. **Test columns API**: `GET /payroll/columns` returns flat AG-Grid definitions
5. **Data path critical**: Ensure `get_column_definitions()` uses `hierarchy` not `generated_headers`

## Database Module

The database module provides centralized database access with connection pooling and error handling:

### Structure
- `backend/database/config/` - Database configuration settings
- `backend/database/models/` - Database model definitions
- `backend/database/queries/` - SQL query definitions (JSON format, group-based)
- `backend/database/services/` - Core database services (pooling, transactions, logging)

### Features
- Connection pooling with configurable pool sizes
- Automatic error handling and logging
- Transaction support with context managers
- Query organization using JSON files with `?` placeholders
- Support for multiple database environments

### Usage Patterns
```python
# Initialize database connection pool
db = Database.instance(pool_size=5)

# Execute queries
results = db.query_all(sql, params)

# Use transactions
with db.transaction() as cur:
    cur.execute("INSERT INTO table VALUES (?, ?)", [value1, value2])
```

## Performance Considerations

- Threaded processing can improve performance by 2-3x for large datasets
- Memory monitoring available for data extraction operations
- Pagination recommended for reports with >1000 rows
- Connection pooling prevents database connection exhaustion
- Database queries use parameterized statements with `?` placeholders for security