CompVista

Compensation Equity & Disparity Analysis Platform

CompVista is a compensation analysis platform that helps HR teams review employee pay across roles, levels, locations, currencies, and full-time-equivalent (FTE) arrangements. It provides compensation benchmarking, disparity indicators, data-quality visibility, adjustment proposals, and an approval workflow.



Data notice: CompVista uses synthetic employee and compensation data for demonstration. It is not intended to make employment decisions automatically. Analysis flags are indicators for human review, not proof of discrimination or a definitive finding of inequity.



Features



Compensation analysis





Employee, role, level, location, salary, and compensation-band data.



Effective-dated compensation bands.



Salary normalization using currency and FTE information.



Compa-ratio and band-position calculations.



Comparable employee group analysis.



Potential compensation disparity flags and HR-review indicators.



Data-quality reporting, including visibility into records excluded from analysis.



Proposal and approval workflow





Generate evidence-informed adjustment proposals for HR review.



Submit draft proposals for approval.



View proposal details and history.



Approve or reject submitted proposals with reviewer remarks.



Apply approved salary adjustments through the proposal workflow.



Track proposal lifecycle and audit/history information.



Frontend





Dashboard with compensation and alert summaries.



Compensation Analysis, Employees, Anomalies, and Data Quality views.



Reports & Exports with CSV downloads.



Proposals and Approvals workflow screens.



Settings for profile, organization display preferences, and notification preferences.

Settings persistence note: The current Settings page stores preferences in the browser's localStorage. These preferences are browser-local and are not synchronized to the backend or shared across devices.

Technology stack





Backend: Python, Flask, Flask-SQLAlchemy / SQLAlchemy, Flask-JWT-Extended



Database: SQLite



Data processing: Pandas, NumPy, Faker



Frontend: React, Vite, JavaScript



UI/icons: CSS and Lucide React icons



Repository layout

CompVista/
├── backend/
│   ├── app.py
│   ├── models/
│   ├── routes/
│   └── services/
├── data/
├── docs/
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── reports/
├── src/
│   ├── generate.py
│   ├── role_data.py
│   ├── band_data.py
│   └── verification and migration scripts
├── tests/
├── ER_Diagram.png
├── requirements.txt
├── .gitignore
└── README.md



Prerequisites





Python 3.10 or a compatible version supported by the dependencies.



Node.js and npm.



Git.



Setup

Run commands from the repository root unless a step says otherwise.

1. Clone the repository

git clone https://github.com/janu1996/CompVista.git
cd CompVista



2. Create and activate the Python environment

Windows PowerShell:

python -m venv venv
.\venv\Scripts\Activate.ps1

Install backend dependencies:

python -m pip install -r requirements.txt



3. Configure backend environment

Set a strong, private JWT secret for the current PowerShell session:

$env:JWT_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"

If you are using a prepared local database, set its path explicitly. Example only:

$env:COMPVISTA_DB_PATH = "backend/compvista_backup.db"

Use the database filename supplied with your own local setup. Do not commit database files, credentials, JWT secrets, or .env files to Git.

4. Start the backend

From the repository root:

python backend/app.py

The API is configured for local development at:

http://127.0.0.1:5000

Keep the backend terminal running.

5. Install and start the frontend

Open a second terminal:

cd frontend
npm install
npm run dev

Vite normally serves the frontend at:

http://localhost:5173

If the frontend uses a different backend URL, configure VITE_API_BASE_URL according to the frontend API client configuration. Do not place secrets in Vite environment variables.

Synthetic data and reproducibility

The synthetic data generation workflow uses the fixed seed:

20261022

The repository includes data-generation, compensation-band, validation, and migration scripts under src/. Review each script and its configured database target before running it.

Example commands:

python src/generate.py
python src/role_data.py
python src/band_data.py
python src/verify_bands.py
python src/verify_data.py

Important database safety: Some historical salary and employee-location migration scripts were developed and tested against isolated test databases. Do not run migration or reset scripts against a populated database unless you have identified the exact target, made a separate backup, and verified the migration plan. Never delete or overwrite an existing project database as a setup shortcut.

API and access

The backend exposes authentication, compensation analysis, and proposal-related routes. Protected endpoints require a valid JWT access token. The frontend API client is responsible for attaching the token to authenticated requests.

For the exact route list and request/response schemas, refer to the route modules under backend/routes/; this README intentionally avoids documenting unverified endpoint details.

Verification status

The following user-observed frontend workflows have been exercised during the current development session:





Settings preferences save in the browser and remain after a page refresh.



Reports & Exports CSV downloads.



Proposal submission and status updates.



Approvals page listing and proposal detail view.



Approve and reject actions with remarks.

These are manual workflow checks, not a claim that every acceptance criterion or every browser/API combination has passed. Backend regression tests and the challenge requirements must be checked separately before release.

Security and Git hygiene

Before committing or pushing:





Keep venv/, node_modules/, build output, .env files, secrets, logs, and local database files out of Git.



Check staged files with git status and git diff --cached --stat.



Inspect staged changes for credentials and local paths.



Do not stage every untracked diagnostic or one-off migration script without reviewing its purpose.



Never commit real employee data. This project is intended to use synthetic data.



Disclaimer

CompVista is a demonstration and decision-support project using synthetic data. Its outputs require qualified human review and should not be treated as legal, compliance, or employment decisions.