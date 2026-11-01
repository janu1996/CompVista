
# CompVista - Database Schema

## 1. Overview

CompVista uses a relational database to manage employee compensation information, salary history, performance evidence, promotions, and compensation adjustment proposals.

## 2. Database

- Database: SQLite
- ORM: SQLAlchemy
- Primary Key: Unique identifier for each record.
- Foreign Key: Connects related tables.

## 3. Core Entities

The database contains the following 10 core entities:

1. Employee
2. Role
3. Level
4. Location
5. CompensationBand
6. SalaryRecord
7. PerformanceEvidence
8. Tenure
9. Promotion
10. AdjustmentProposal

## 4. Design Principles

- Maintain unique primary keys.
- Enforce foreign key relationships.
- Preserve salary and promotion history.
- Use effective dates for compensation bands.
- Track proposal approval and application states.
- Maintain an audit trail for compensation changes.

## 5. Status

Database schema design is in progress.


## 6. Employee Entity

Stores basic employee information.

| Field | Data Type | Constraint | Description |
|---|---|---|---|
| employee_id | VARCHAR(20) | Primary Key | Unique employee ID |
| first_name | VARCHAR(100) | NOT NULL | Employee first name |
| last_name | VARCHAR(100) | NOT NULL | Employee last name |
| email | VARCHAR(150) | UNIQUE, NOT NULL | Employee email |
| role_id | VARCHAR(20) | Foreign Key | References Role |
| level_id | VARCHAR(20) | Foreign Key | References Level |
| location_id | VARCHAR(20) | Foreign Key | References Location |
| hire_date | DATE | NOT NULL | Date of joining |
| employment_status | VARCHAR(20) | NOT NULL | ACTIVE, INACTIVE, TERMINATED |
| created_at | DATETIME | NOT NULL | Record creation timestamp |

### Employee ID Format

EMP-000001

### Relationships

- One Role can have many Employees.
- One Level can have many Employees.
- One Location can have many Employees.
- One Employee can have multiple SalaryRecords.
- One Employee can have multiple Promotions.
- One Employee can have multiple AdjustmentProposals.


## 7. Role Entity

Stores job role information.

| Field | Data Type | Constraint | Description |
|---|---|---|---|
| role_id | VARCHAR(20) | Primary Key | Unique role ID |
| role_name | VARCHAR(100) | UNIQUE, NOT NULL | Job title |
| department | VARCHAR(100) | NOT NULL | Department |
| job_family | VARCHAR(100) | NOT NULL | Job category |
| description | TEXT | OPTIONAL | Role description |

Example ID: ROLE-0001

## 8. Level Entity

Stores employee seniority and career levels.

| Field | Data Type | Constraint | Description |
|---|---|---|---|
| level_id | VARCHAR(20) | Primary Key | Unique level ID |
| level_name | VARCHAR(50) | UNIQUE, NOT NULL | Level name |
| level_rank | INTEGER | UNIQUE, NOT NULL | Numeric hierarchy |
| description | TEXT | OPTIONAL | Level description |

Example ID: LEVEL-01

## 9. Location Entity

Stores employee work locations.

| Field | Data Type | Constraint | Description |
|---|---|---|---|
| location_id | VARCHAR(20) | Primary Key | Unique location ID |
| location_name | VARCHAR(100) | NOT NULL | City or office name |
| country | VARCHAR(100) | NOT NULL | Country |
| country_code | VARCHAR(5) | NOT NULL | Country code |
| currency_code | VARCHAR(3) | NOT NULL | Local currency |
| cost_of_living_index | FLOAT | OPTIONAL | Location cost index |

Example ID: LOC-0001


## 10. CompensationBand Entity

Stores salary ranges for a specific role, level, and location during a defined period.

| Field | Data Type | Constraint | Description |
|---|---|---|---|
| band_id | VARCHAR(100) | Primary Key | Unique band ID |
| role_id | VARCHAR(20) | Foreign Key, NOT NULL | References Role |
| level_id | VARCHAR(20) | Foreign Key, NOT NULL | References Level |
| location_id | VARCHAR(20) | Foreign Key, NOT NULL | References Location |
| min_salary | DECIMAL(15,2) | NOT NULL | Minimum salary |
| midpoint_salary | DECIMAL(15,2) | NOT NULL | Midpoint salary |
| max_salary | DECIMAL(15,2) | NOT NULL | Maximum salary |
| currency_code | VARCHAR(3) | NOT NULL | Salary currency |
| effective_from | DATE | NOT NULL | Band start date |
| effective_to | DATE | OPTIONAL | Band end date |
| created_at | DATETIME | NOT NULL | Record creation timestamp |

### Band ID Format

BAND-ROLE-LEVEL-LOCATION-2026

### Validation Rules

- Minimum salary must be less than midpoint salary.
- Midpoint salary must be less than maximum salary.
- Effective end date must be later than effective start date.
- Role, Level, and Location must reference valid records.
- Historical bands must be retained.
- Overlapping effective periods for the same role, level, and location must be prevented unless explicitly justified.


## 11. SalaryRecord Entity

Stores employee salary history. Every salary change creates a new record instead of overwriting the previous salary.

| Field | Data Type | Constraint | Description |
|---|---|---|---|
| salary_id | VARCHAR(50) | Primary Key | Unique salary record ID |
| employee_id | VARCHAR(20) | Foreign Key, NOT NULL | References Employee |
| band_id | VARCHAR(100) | Foreign Key, NOT NULL | References CompensationBand |
| base_salary | DECIMAL(15,2) | NOT NULL | Actual base salary |
| currency_code | VARCHAR(3) | NOT NULL | Original salary currency |
| fte | DECIMAL(4,2) | NOT NULL | Full-time equivalent |
| effective_from | DATE | NOT NULL | Salary start date |
| effective_to | DATE | OPTIONAL | Salary end date |
| change_reason | VARCHAR(100) | NOT NULL | HIRE, PROMOTION, ADJUSTMENT, ANNUAL_REVIEW |
| created_at | DATETIME | NOT NULL | Record creation timestamp |

### Salary ID Format

SAL-EMP-000001-2026-01

### Validation Rules

- Employee ID must reference a valid employee.
- Band ID must reference a valid compensation band.
- Base salary must be greater than zero.
- FTE must be greater than 0 and less than or equal to 1.
- Effective end date must be later than effective start date.
- Previous salary records must be preserved.
- Salary records must not have overlapping effective periods for the same employee.

### Derived Calculations

1. FTE-normalized salary = Base salary / FTE
2. Currency-normalized salary = Base salary × applicable FX rate
3. Compa-ratio = Normalized salary / Compensation band midpoint


## 12. PerformanceEvidence Entity

Stores documented employee performance information used as supporting evidence during compensation reviews.

| Field | Data Type | Constraint | Description |
|---|---|---|---|
| evidence_id | VARCHAR(50) | Primary Key | Unique evidence ID |
| employee_id | VARCHAR(20) | Foreign Key, NOT NULL | References Employee |
| review_period | VARCHAR(20) | NOT NULL | Performance review period |
| performance_rating | DECIMAL(3,2) | OPTIONAL | Performance score |
| rating_scale | VARCHAR(20) | OPTIONAL | Rating scale |
| evidence_type | VARCHAR(50) | NOT NULL | PERFORMANCE_REVIEW, ACHIEVEMENT, SKILL |
| description | TEXT | NOT NULL | Supporting evidence description |
| recorded_by | VARCHAR(100) | NOT NULL | Reviewer or manager |
| recorded_at | DATETIME | NOT NULL | Evidence recording date |

### Evidence ID Format

PERF-EMP-000001-2026

### Validation Rules

- Employee ID must reference a valid employee.
- Evidence description cannot be empty.
- Performance rating must follow the documented rating scale.
- Review period must be valid.
- Historical evidence must be preserved.


## 13. Tenure Entity

Stores employee service duration and employment history.

| Field | Data Type | Constraint | Description |
|---|---|---|---|
| tenure_id | VARCHAR(50) | Primary Key | Unique tenure ID |
| employee_id | VARCHAR(20) | Foreign Key, NOT NULL | References Employee |
| start_date | DATE | NOT NULL | Employment start date |
| end_date | DATE | OPTIONAL | Employment end date |
| tenure_type | VARCHAR(30) | NOT NULL | FULL_TIME, PART_TIME, CONTRACT |
| fte | DECIMAL(4,2) | NOT NULL | Employment percentage |
| created_at | DATETIME | NOT NULL | Record creation timestamp |

### Tenure ID Format

TEN-EMP-000001-2026

### Validation Rules

- Employee ID must reference a valid employee.
- Start date must be valid.
- End date must be later than start date.
- FTE must be greater than 0 and less than or equal to 1.
- Previous tenure records must be preserved.


## 14. Promotion Entity

Stores employee promotion history, including previous and new roles and levels.

| Field | Data Type | Constraint | Description |
|---|---|---|---|
| promotion_id | VARCHAR(50) | Primary Key | Unique promotion ID |
| employee_id | VARCHAR(20) | Foreign Key, NOT NULL | References Employee |
| previous_role_id | VARCHAR(20) | Foreign Key, NOT NULL | Previous role |
| new_role_id | VARCHAR(20) | Foreign Key, NOT NULL | New role |
| previous_level_id | VARCHAR(20) | Foreign Key, NOT NULL | Previous level |
| new_level_id | VARCHAR(20) | Foreign Key, NOT NULL | New level |
| promotion_date | DATE | NOT NULL | Promotion effective date |
| reason | TEXT | NOT NULL | Promotion justification |
| approved_by | VARCHAR(100) | NOT NULL | Approving manager |
| created_at | DATETIME | NOT NULL | Record creation timestamp |

### Promotion ID Format

PROM-EMP-000001-2026

### Validation Rules

- Employee ID must reference a valid employee.
- Previous and new roles must reference valid Role records.
- Previous and new levels must reference valid Level records.
- Promotion date must be valid.
- Previous role and new role should not be identical when recording a role change.
- Promotion history must never be overwritten.


## 15. AdjustmentProposal Entity

Stores proposed employee compensation changes with supporting evidence and approval history.

| Field | Data Type | Constraint | Description |
|---|---|---|---|
| proposal_id | VARCHAR(50) | Primary Key | Unique proposal ID |
| employee_id | VARCHAR(20) | Foreign Key, NOT NULL | References Employee |
| current_salary_id | VARCHAR(50) | Foreign Key, NOT NULL | References SalaryRecord |
| proposed_salary | DECIMAL(15,2) | NOT NULL | Proposed salary |
| currency_code | VARCHAR(3) | NOT NULL | Proposal currency |
| reason | TEXT | NOT NULL | Adjustment justification |
| issue_type | VARCHAR(50) | OPTIONAL | Identified compensation issue |
| status | VARCHAR(20) | NOT NULL | DRAFT, SUBMITTED, APPROVED, REJECTED, APPLIED |
| proposed_by | VARCHAR(100) | NOT NULL | Proposal creator |
| approved_by | VARCHAR(100) | OPTIONAL | Approving authority |
| created_at | DATETIME | NOT NULL | Proposal creation date |
| approved_at | DATETIME | OPTIONAL | Approval date |
| applied_at | DATETIME | OPTIONAL | Application date |

### Proposal ID Format

ADJ-2026-000001

### Validation Rules

- Employee ID must reference a valid employee.
- Current salary ID must reference a valid SalaryRecord.
- Proposed salary must be greater than zero.
- Only approved proposals can be applied.
- Rejected proposals cannot be applied.
- Every status change must be preserved in an audit history.
- Proposal evidence must be documented.


## 16. Entity Relationships

### One-to-Many Relationships

1. Role → Employee
   - One role can have multiple employees.

2. Level → Employee
   - One level can have multiple employees.

3. Location → Employee
   - One location can have multiple employees.

4. Employee → SalaryRecord
   - One employee can have multiple salary records.

5. Employee → PerformanceEvidence
   - One employee can have multiple performance records.

6. Employee → Tenure
   - One employee can have multiple tenure records over time.

7. Employee → Promotion
   - One employee can have multiple promotions.

8. Employee → AdjustmentProposal
   - One employee can have multiple adjustment proposals.

9. CompensationBand → SalaryRecord
   - One compensation band can be referenced by multiple salary records.

10. Role + Level + Location → CompensationBand
    - Each compensation band belongs to one role, one level, and one location.

### Relationship Rules

- All foreign keys must reference existing records.
- Parent records must be created before dependent records.
- Historical records must be preserved.
- Deleting a parent record must not silently delete its history.
- Effective dates must be validated.


## 17. AuditLog Entity

Stores a permanent history of important changes made in the system.

| Field | Data Type | Constraint | Description |
|---|---|---|---|
| audit_id | VARCHAR(50) | Primary Key | Unique audit ID |
| entity_type | VARCHAR(50) | NOT NULL | Changed entity name |
| entity_id | VARCHAR(100) | NOT NULL | ID of the changed record |
| action | VARCHAR(30) | NOT NULL | CREATE, UPDATE, APPROVE, REJECT, APPLY |
| old_value | TEXT | OPTIONAL | Previous value |
| new_value | TEXT | OPTIONAL | Updated value |
| performed_by | VARCHAR(100) | NOT NULL | User performing the action |
| performed_at | DATETIME | NOT NULL | Action timestamp |
| remarks | TEXT | OPTIONAL | Reason for change |

### Audit ID Format

AUD-2026-000001

### Validation Rules

- Every important state change must create an audit record.
- Previous and new values must be preserved where applicable.
- Audit records must never be overwritten or silently deleted.
- Approval and application actions must record who performed them and when.


## 18. ProposalHistory Entity

Stores every status transition and approval action performed on an AdjustmentProposal.

| Field | Data Type | Constraint | Description |
|---|---|---|---|
| history_id | VARCHAR(50) | Primary Key | Unique history ID |
| proposal_id | VARCHAR(50) | Foreign Key, NOT NULL | References AdjustmentProposal |
| previous_status | VARCHAR(20) | OPTIONAL | Previous proposal status |
| new_status | VARCHAR(20) | NOT NULL | Updated proposal status |
| changed_by | VARCHAR(100) | NOT NULL | Person performing the action |
| remarks | TEXT | OPTIONAL | Reason for status change |
| changed_at | DATETIME | NOT NULL | Status change timestamp |

### History ID Format

HIST-2026-000001

### Valid Status Transitions

DRAFT → SUBMITTED → APPROVED → APPLIED

DRAFT → REJECTED

SUBMITTED → REJECTED

### Validation Rules

- Proposal ID must reference a valid AdjustmentProposal.
- Every status transition must create a new history record.
- Previous and new statuses must be recorded.
- Only APPROVED proposals can move to APPLIED.
- History records must never be overwritten or deleted.

