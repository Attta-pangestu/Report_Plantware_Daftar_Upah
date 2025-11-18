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

# Run development server
python main.py
# OR
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run with environment variables
DEV_MODE=true VITE_DEV_MODE=true python main.py
```

### Frontend Development
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run with development mode enabled
npm run dev:test

# Build for production
npm run build

# Preview production build
npm run preview
```

### Database Operations
```bash
# Test database connection
cd backend
python -c "from database.services.database import Database; print('Connection healthy' if Database.instance().test_connection() else 'Connection failed')"
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

## Development Workflow

### Running the Full Application
1. Start the backend server: `cd backend && python main.py`
2. Start the frontend development server: `cd frontend && npm run dev:test`
3. Access the application at `http://localhost:5174`
4. Backend API available at `http://localhost:8000`

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

## Performance Considerations

- Threaded processing can improve performance by 2-3x for large datasets
- Memory monitoring available for data extraction operations
- Pagination recommended for reports with >1000 rows
- Connection pooling prevents database connection exhaustion