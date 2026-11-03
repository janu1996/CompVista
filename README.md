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
- Historical foreign exchange rate conversion to INR.
- Compa-ratio and within-band position calculations.
- Comparable employee group analysis.
- Compensation disparity detection.
- Below-band and peer-pay-gap detection.
- Data quality validation and reporting.
- Ground truth dataset for detector evaluation.

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

### Dataset and Reporting
- Synthetic dataset containing 5,000 employees.
- CSV and JSON dataset exports.
- SQL seed data export.
- SHA-256 checksum generation for export verification.
- Ground truth records in CSV and JSON formats.
- Database constraint validation.

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

**Backend Development – Core Compensation Analysis and Security Implemented**

Implemented components include:

- Core database design and SQLAlchemy models.
- Synthetic HR data generation.
- Compensation band master data.
- Compensation analysis services.
- Historical data validation.
- Historical FX conversion and INR normalization.
- JWT authentication and password hashing.
- Candidate, HR and Admin role-based authorization.
- Protected analysis APIs.
- Proposal lifecycle and approval workflow.
- Ground truth scenarios for missing salary, below-band and peer-pay-gap detection.
- CSV, JSON and SQL dataset exports.
- Database constraint validation.
- Repeat-export SHA-256 checksum verification.

The backend regression test suite can be executed using:

`python -m pytest tests -q`

The previously recorded regression result was 26 passing tests. Run the command above to verify the current codebase.

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

Configure the database path to the intended local database. For example:

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

The existing recorded test result is 26 passing tests.

Additional standalone validation scripts cover:

- Historical FX rate lookup and conversion.
- INR-normalized compensation analysis.
- Missing salary detection.
- Below-band detection.
- Peer-pay-gap detection.
- Negative salary database constraint.
- Invalid FTE database constraint.
- Invalid compensation band constraint.
- Ground truth CSV and JSON consistency.

The standalone workflow scripts under `src/` and `backend/` are separate from the pytest suite and require separate execution and review.

## Data Generation and Validation

Run the synthetic data generator:

```powershell
python src/generate.py
```

The generator uses a fixed random seed (`20261022`) and Faker seed for reproducible data generation.

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

### Dataset Export

Configure the database from which the dataset should be exported:

```powershell
$env:COMPVISTA_DB_PATH = "backend/compvista_backup.db"
```

Run the export script:

```powershell
Push-Location backend
python export_dataset.py
Pop-Location
```

The export script generates CSV and JSON files for the core dataset tables and a SQL INSERT data export.

Export locations:

- `data/csv/`
- `data/json/`
- `data/sql/compvista_seed.sql`
- `data/export_manifest.json`

The export manifest records table row counts, export file locations and a SHA-256 checksum.

Run the export script again against the same unchanged database to verify that the CSV and JSON export checksum remains identical.

This verifies repeat-export consistency for the same database. It does not, by itself, prove that two independent fresh database generation runs produce identical datasets.

### Ground Truth Dataset

Ground truth records are maintained separately in:

- `data/csv/ground_truth.csv`
- `data/json/ground_truth.json`

The current ground truth contains nine controlled scenarios:

- Seven missing-salary cases.
- One below-band scenario.
- One peer-pay-gap scenario.

These records describe expected detector outcomes and support evaluation of compensation analysis results.

### Currency Normalization

CompVista normalizes compensation values into INR for cross-currency analysis.

The synthetic FX dataset uses:

- INR to INR: 1.0
- GBP to INR: 110.0

The GBP rate is a fixed synthetic assumption for this demonstration dataset, not a live or historical market exchange rate.

FX conversions use effective-dated rates so that salary comparisons can use the applicable conversion rate for the analysis date.

**Database Safety:** Migration scripts may target isolated test databases. Do not run migration scripts or temporary test scripts against an existing populated database without a verified backup and explicit review.

## AI Usage and Validation

AI assistance was used during development to support implementation, debugging, documentation and test design.

AI-assisted code and suggestions were reviewed against the project requirements and validated through application-level checks, database constraints and detector scenario tests.

The project uses synthetic employee data. No real employee compensation information, production credentials or private HR records should be included in prompts or source control.

AI-generated suggestions are not treated as automatically correct; implementation decisions and validation results must be reviewed before use.

## Disclaimer

This project uses synthetic employee data for demonstration and analysis purposes. It does not contain real employee compensation information.

The synthetic exchange rates are demonstration assumptions and must not be treated as actual financial market rates.

Compensation disparity flags are indicators for HR review and do not independently establish discrimination or legal non-compliance.

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
│   ├── export_dataset.py
│   ├── models/
│   ├── routes/
│   └── services/
├── data/
│   ├── csv/
│   ├── json/
│   └── sql/
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

- `venv/` and `.venv/`, including nested virtual environments.
- `.env` and secret files.
- SQLite database files.
- Python cache files.
- `node_modules/` and build output.
- Local logs and temporary test artifacts.

Only source code, safe configuration examples, documentation, required dataset exports and required project assets should be committed.

Never upload virtual environments, database files, JWT tokens, staff credentials or private configuration to GitHub.
