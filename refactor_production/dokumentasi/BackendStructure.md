backend/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── employees.py       # Employee endpoints
│   │   ├── payroll.py         # Payroll endpoints
│   │   ├── reports.py         # Report endpoints
│   │   └── config.py          # Configuration endpoints
│   ├── core/                  # Core functionality
│   │   ├── config.py          # Application config
│   │   ├── security.py       # Security utilities
│   │   └── exceptions.py     # Custom exceptions
│   ├── models/                # Data models (Pydantic)
│   │   ├── employee.py       # Employee models
│   │   ├── payroll.py         # Payroll models
│   │   └── config.py          # Configuration models
│   ├── repositories/          # Data access layer
│   │   ├── employee_repository.py
│   │   ├── payroll_repository.py
│   │   └── config_repository.py
│   ├── services/              # Business logic
│   │   ├── employee_service.py
│   │   ├── payroll_service.py
│   │   ├── report_service.py
│   │   └── config_service.py
│   └── utils/                 # Utility functions
│       ├── database.py        # Database connection
│       └── helpers.py         # Helper functions
├── migrations/                # Database migrations
├── tests/                     # Test files
├── requirements.txt           # Python dependencies
└── main.py                   # Application entry point

Report API
- Endpoint: `GET /payroll/report` returns list of payroll rows for grid rendering.
- Model: `app/models/payroll.py::PayrollRow` includes fields aligned with Daftar Upah columns.
- Service: `app/services/payroll_service.py::generate_rows` composes demo rows from `EmployeeRepository`.
- Auth: Requires `Authorization: Bearer <token>` from `/auth/login`.
