# CompVista
### Compensation Equity & Disparity Analysis Platform

CompVista is a data-driven platform designed to analyze employee compensation, compare salaries across roles, levels, and locations, and identify potential unexplained pay disparities.

The platform helps HR teams understand compensation fairness through salary benchmarking, effective-dated compensation bands, explainable analysis, evidence-based adjustment proposals, and approval tracking.

## Key Features

- Synthetic HR compensation data generation
- Employee, Role, Level, Location and CompensationBand master data
- Effective-dated compensation bands
- Salary history management
- Salary normalization based on currency and FTE
- Compa-ratio and within-band position calculations
- Comparable employee group analysis
- Compensation disparity detection
- Evidence-based adjustment proposals
- Proposal approval and rejection workflow
- Salary adjustment application
- Audit trail and approval history tracking
- Data validation and reporting

## Technology Stack

- Python
- Flask
- SQLAlchemy
- SQLite
- Pandas
- NumPy
- Faker
- React.js
- Git and GitHub

## Project Status

🚧 Under Development

Core database design, synthetic data generation, compensation band master data, analysis services, and proposal workflow implementation are in progress.

## Disclaimer

This project uses synthetic employee data for demonstration and analysis purposes. It does not contain real employee compensation information.

---

## Development Progress

### Day 1 – November 1, 2026

**Project Setup**
- Created CompVista GitHub repository.
- Connected local project with GitHub.
- Created initial project folder structure.
- Added requirements.txt and .gitignore.
- Created initial README.md.

**Database Design**
- Designed core database entities.
- Defined primary keys and foreign keys.
- Documented entity relationships.
- Designed AuditLog and ProposalHistory.
- Created ER diagram.
- Created initial data dictionary.

**Status:** Project setup and initial database documentation completed.

### Day 2 – November 2, 2026

**Database Implementation**
- Implemented SQLAlchemy database models.
- Configured Flask application with SQLite.
- Implemented Employee, Role, Level and Location models.
- Implemented CompensationBand and SalaryRecord models.
- Implemented PerformanceEvidence, Tenure and Promotion models.
- Implemented AdjustmentProposal, AuditLog and ProposalHistory models.

**Synthetic Data Generation**
- Implemented synthetic HR data generation.
- Generated 5,000 employee records.
- Created role, level and location master data.
- Generated salary history and related HR records.
- Used a fixed random seed for reproducibility.

**Compensation Band Master Data**
- Expanded role master data to 40 roles.
- Configured 5 levels and 8 locations.
- Generated 1,600 effective-dated compensation bands.
- Migrated 16,598 salary references to the new band IDs.
- Preserved all 16,598 salary records during migration.
- Removed 800 obsolete band records from the separate upgrade test database.

**Band Validation**
- Verified 1,600 expected role-level-location combinations.
- Checked duplicate combinations.
- Checked missing and unexpected combinations.
- Validated minimum, midpoint and maximum salary ranges.
- Validated effective dates.

**Validation Results**
- Expected combinations: 1,600
- Actual unique combinations: 1,600
- Duplicate combinations: 0
- Missing combinations: 0
- Unexpected combinations: 0
- Invalid salary ranges: 0
- Invalid effective dates: 0

**Status:** Compensation band master data migration and validation completed successfully in the upgrade test database.

**Next Steps**
- Complete synthetic dataset validation.
- Strengthen compensation analysis and currency/FTE normalization.
- Complete comparable group and disparity analysis.
- Expand proposal evidence and approval workflow.
- Implement remaining validation, exception and reporting requirements.
- Develop frontend dashboard and user workflows.
- Prepare test evidence and project documentation.

---

## Entity Relationship Diagram

![CompVista ER Diagram](ER_Diagram.png)

## Project Structure

```text
CompVista/
│
├── backend/
│   ├── app.py
│   ├── extensions.py
│   ├── models/
│   ├── routes/
│   └── services/
│
├── data/
├── docs/
├── frontend/
├── reports/
│
├── src/
│   ├── generate.py
│   ├── role_data.py
│   ├── band_data.py
│   ├── migrate_bands.py
│   ├── verify_bands.py
│   ├── verify_data.py
│   ├── test_analysis.py
│   ├── test_proposals.py
│   ├── test_approval.py
│   └── test_apply.py
│
├── tests/
├── ER_Diagram.png
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/janu1996/CompVista.git
cd CompVista
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run Flask Backend

```bash
python backend/app.py
```

The backend runs locally using Flask and SQLite.

## Data Generation and Validation

Run the synthetic data generator:

```bash
python src/generate.py
```

Run compensation band master data generation:

```bash
python src/role_data.py
python src/band_data.py
```

Run band validation:

```bash
python src/verify_bands.py
```

Run general dataset validation:

```bash
python src/verify_data.py
```

**Note:** The band migration and validation scripts currently target the separate upgrade test database. Do not run migration against the original database without creating and verifying a backup first.

## Reproducibility

- Synthetic data generation uses a fixed seed: `20261022`.
- A consistent seed supports repeatable data generation.
- Data validation scripts check important master data and compensation band constraints.

## Future Enhancements

- Interactive React dashboard.
- Advanced compensation benchmarking reports.
- Additional explainable disparity detection.
- Evidence-linked proposal reviews.
- Role-based access control for HR, managers and administrators.
- Comprehensive test coverage and exception reporting.
- CSV, JSON and SQL export support.