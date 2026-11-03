# CompVista
### Compensation Equity & Disparity Analysis Platform

CompVista is a data-driven platform designed to analyze employee compensation, compare salaries across roles, levels, and locations, and identify potential unexplained pay disparities.

The platform helps HR teams understand compensation fairness through salary benchmarking, effective-dated compensation bands, explainable analysis, evidence-based adjustment proposals, and approval tracking.

## Key Features

### Compensation Analysis
- Synthetic HR compensation data generation.
- Employee, Role, Level, Location and CompensationBand master data.
- Effective-dated compensation bands.
- Salary history management.
- Salary normalization based on currency and FTE.
- Compa-ratio and within-band position calculations.
- Comparable employee group analysis.
- Compensation disparity detection.
- Data quality validation and reporting.

### Proposal Management
- Evidence-based adjustment proposals.
- Proposal submission, approval and rejection workflow.
- Salary adjustment application.
- Duplicate adjustment prevention.
- Audit trail and approval history tracking.
- Employee location history tracking.

### Authentication and Authorization
- Candidate registration and login.
- JWT-based authentication.
- Secure password hashing.
- Role-based access control (RBAC).
- Three user roles: Candidate, HR and Admin.
- Protected compensation analysis APIs.
- Candidate access restricted to their linked employee record.
- HR and Admin access to organization-level analysis.
- Staff account provisioning through a local administrative script.

## Technology Stack

- Python
- Flask
- Flask-SQLAlchemy
- SQLAlchemy
- SQLite
- Flask-JWT-Extended
- Werkzeug password hashing
- Pandas
- NumPy
- Faker
- React.js (frontend development)
- Git and GitHub

## User Roles

| Role | Permissions |
|---|---|
| Candidate | Access own linked compensation information and proposals |
| HR | Organization-level compensation analysis and proposal management |
| Admin | Administrative access to protected analysis and proposal APIs |

Public registration creates Candidate accounts only. HR and Admin accounts are provisioned through a local staff account creation script.

## Authentication API

Base URL: `http://127.0.0.1:5000`

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Register a Candidate |
| POST | `/api/auth/login` | Authenticate and receive JWT |
| GET | `/api/auth/me` | Retrieve authenticated user profile |

## Compensation Analysis API

| Method | Endpoint | Access |
|---|---|---|
| GET | `/api/analysis/summary` | HR, Admin |
| GET | `/api/analysis/results` | HR, Admin |
| GET | `/api/analysis/me` | Linked Candidate |

Protected endpoints require a JWT access token in the Authorization header.

## Project Status

**Backend Development – Authentication and Authorization Implemented**

Implemented components include:
- Core database design and SQLAlchemy models.
- Synthetic HR data generation.
- Compensation band master data.
- Compensation analysis services.
- Proposal lifecycle and approval workflow.
- Historical data validation.
- JWT authentication and password hashing.
- Candidate, HR and Admin role-based authorization.
- Protected analysis and proposal APIs.

The existing backend regression test suite completed with **26 passing tests** using:

`python -m pytest tests -q`

Frontend development, complete frontend-backend integration, and remaining end-to-end testing are pending.

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/janu1996/CompVista.git
cd CompVista
```

### 2. Create Virtual Environment

```powershell
python -m venv venv
```

### 3. Activate Virtual Environment

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Configure Environment Variables

Set a secure JWT secret in PowerShell:

```powershell
$env:JWT_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
```

For the existing populated local database:

```powershell
$env:COMPVISTA_DB_PATH = "backend/compvista_backup.db"
```

Keep secret values in environment variables or a local `.env` file. Never commit secrets or database files.

### 6. Run Flask Backend

```powershell
python backend/app.py
```

Backend URL:

`http://127.0.0.1:5000`

Health check:

`http://127.0.0.1:5000/health`

## Staff Account Provisioning

HR and Admin accounts are created using the local staff provisioning script.

```powershell
python backend/create_staff_user.py
```

The script supports HR and ADMIN roles and requests passwords securely through the terminal.

Do not expose staff credentials or JWT tokens in source code or GitHub.

## Testing

Run the backend regression tests:

```powershell
python -m pytest tests -q
```

Latest recorded result:

- 26 tests passed.
- No failures in the `tests/` suite.

The standalone workflow scripts under `src/` are separate from the pytest suite and require separate execution and review.

## Data Generation and Validation

Run the synthetic data generator:

```powershell
python src/generate.py
```

Run compensation band generation:

```powershell
python src/role_data.py
python src/band_data.py
```

Run band validation:

```powershell
python src/verify_bands.py
```

Run general dataset validation:

```powershell
python src/verify_data.py
```

**Database Safety:** Migration scripts may target isolated test databases. Do not run migration scripts against an existing populated database without a verified backup and explicit review.

## Disclaimer

This project uses synthetic employee data for demonstration and analysis purposes. It does not contain real employee compensation information.

## Future Enhancements

- Complete React frontend dashboard.
- Candidate, HR and Admin role-based user interfaces.
- Frontend-backend API integration.
- Secure candidate-to-employee account linking.
- Comprehensive end-to-end testing.
- Advanced compensation benchmarking reports.
- Additional explainable disparity detection.
- Final deployment and documentation.

## Entity Relationship Diagram

![CompVista ER Diagram](ER_Diagram.png)

## Project Structure

```text
CompVista/
├── backend/
│   ├── app.py
│   ├── extensions.py
│   ├── create_staff_user.py
│   ├── create_users_table.py
│   ├── models/
│   ├── routes/
│   └── services/
├── data/
├── docs/
├── frontend/
├── reports/
├── src/
├── tests/
├── ER_Diagram.png
├── requirements.txt
├── README.md
└── .gitignore
```

## Git and Security

The following files and directories must remain excluded from Git:

- `venv/` and `.venv/`
- `.env` and secret files
- SQLite database files
- Python cache files
- `node_modules/` and build output

Only source code, safe configuration examples, documentation and required project assets should be committed.
