
# CompVista - Data Dictionary

## 1. Purpose

This document describes the fields, data types, constraints, and validation rules used in the CompVista database.

## 2. Common Conventions

- Primary Key (PK): Uniquely identifies each record.
- Foreign Key (FK): References another table.
- NOT NULL: Field is mandatory.
- UNIQUE: Duplicate values are not allowed.
- OPTIONAL: Field can contain NULL.
- Monetary values: DECIMAL(15,2).
- Dates: YYYY-MM-DD.
- Timestamps: UTC datetime.

## 3. Employee

| Field | Type | Constraint | Description |
|---|---|---|---|
| employee_id | VARCHAR(20) | PK | Unique employee ID |
| first_name | VARCHAR(100) | Required | First name |
| last_name | VARCHAR(100) | Required | Last name |
| email | VARCHAR(150) | UNIQUE | Employee email |
| role_id | VARCHAR(20) | FK | Employee role |
| level_id | VARCHAR(20) | FK | Employee level |
| location_id | VARCHAR(20) | FK | Work location |
| hire_date | DATE | Required | Joining date |
| employment_status | VARCHAR(20) | Required | ACTIVE, INACTIVE, TERMINATED |
| created_at | DATETIME | Required | Creation timestamp |

## 4. Role

| Field | Type | Constraint | Description |
|---|---|---|---|
| role_id | VARCHAR(20) | PK | Unique role ID |
| role_name | VARCHAR(100) | UNIQUE | Job title |
| department | VARCHAR(100) | Required | Department |
| job_family | VARCHAR(100) | Required | Job category |
| description | TEXT | Optional | Role description |

## 5. Level

| Field | Type | Constraint | Description |
|---|---|---|---|
| level_id | VARCHAR(20) | PK | Unique level ID |
| level_name | VARCHAR(50) | UNIQUE | Level name |
| level_rank | INTEGER | UNIQUE | Seniority rank |
| description | TEXT | Optional | Level description |

## 6. Location

| Field | Type | Constraint | Description |
|---|---|---|---|
| location_id | VARCHAR(20) | PK | Unique location ID |
| location_name | VARCHAR(100) | Required | City or office |
| country | VARCHAR(100) | Required | Country |
| country_code | VARCHAR(5) | Required | Country code |
| currency_code | VARCHAR(3) | Required | Local currency |
| cost_of_living_index | FLOAT | Optional | Cost index |

## 7. CompensationBand

| Field | Type | Constraint | Description |
|---|---|---|---|
| band_id | VARCHAR(100) | PK | Unique band ID |
| role_id | VARCHAR(20) | FK | Associated role |
| level_id | VARCHAR(20) | FK | Associated level |
| location_id | VARCHAR(20) | FK | Associated location |
| min_salary | DECIMAL(15,2) | Required | Minimum salary |
| midpoint_salary | DECIMAL(15,2) | Required | Midpoint salary |
| max_salary | DECIMAL(15,2) | Required | Maximum salary |
| currency_code | VARCHAR(3) | Required | Band currency |
| effective_from | DATE | Required | Start date |
| effective_to | DATE | Optional | End date |

## 8. SalaryRecord

| Field | Type | Constraint | Description |
|---|---|---|---|
| salary_id | VARCHAR(50) | PK | Unique salary ID |
| employee_id | VARCHAR(20) | FK | Associated employee |
| band_id | VARCHAR(100) | FK | Applicable band |
| base_salary | DECIMAL(15,2) | Required | Actual salary |
| currency_code | VARCHAR(3) | Required | Original currency |
| fte | DECIMAL(4,2) | Required | Full-time equivalent |
| effective_from | DATE | Required | Salary start date |
| effective_to | DATE | Optional | Salary end date |
| change_reason | VARCHAR(100) | Required | Reason for salary change |
| created_at | DATETIME | Required | Creation timestamp |

## 9. PerformanceEvidence

| Field | Type | Constraint | Description |
|---|---|---|---|
| evidence_id | VARCHAR(50) | PK | Evidence ID |
| employee_id | VARCHAR(20) | FK | Employee reference |
| review_period | VARCHAR(20) | Required | Review period |
| performance_rating | DECIMAL(3,2) | Optional | Performance score |
| rating_scale | VARCHAR(20) | Optional | Rating scale |
| evidence_type | VARCHAR(50) | Required | Evidence category |
| description | TEXT | Required | Supporting details |
| recorded_by | VARCHAR(100) | Required | Reviewer |
| recorded_at | DATETIME | Required | Recording timestamp |

## 10. Tenure

| Field | Type | Constraint | Description |
|---|---|---|---|
| tenure_id | VARCHAR(50) | PK | Tenure ID |
| employee_id | VARCHAR(20) | FK | Employee reference |
| start_date | DATE | Required | Tenure start |
| end_date | DATE | Optional | Tenure end |
| tenure_type | VARCHAR(30) | Required | Employment type |
| fte | DECIMAL(4,2) | Required | Employment percentage |
| created_at | DATETIME | Required | Creation timestamp |

## 11. Promotion

| Field | Type | Constraint | Description |
|---|---|---|---|
| promotion_id | VARCHAR(50) | PK | Promotion ID |
| employee_id | VARCHAR(20) | FK | Employee reference |
| previous_role_id | VARCHAR(20) | FK | Previous role |
| new_role_id | VARCHAR(20) | FK | New role |
| previous_level_id | VARCHAR(20) | FK | Previous level |
| new_level_id | VARCHAR(20) | FK | New level |
| promotion_date | DATE | Required | Effective date |
| reason | TEXT | Required | Promotion reason |
| approved_by | VARCHAR(100) | Required | Approver |
| created_at | DATETIME | Required | Creation timestamp |

## 12. AdjustmentProposal

| Field | Type | Constraint | Description |
|---|---|---|---|
| proposal_id | VARCHAR(50) | PK | Proposal ID |
| employee_id | VARCHAR(20) | FK | Employee reference |
| current_salary_id | VARCHAR(50) | FK | Current salary record |
| proposed_salary | DECIMAL(15,2) | Required | Proposed salary |
| currency_code | VARCHAR(3) | Required | Proposal currency |
| reason | TEXT | Required | Adjustment reason |
| issue_type | VARCHAR(50) | Optional | Identified issue |
| status | VARCHAR(20) | Required | Proposal lifecycle status |
| proposed_by | VARCHAR(100) | Required | Proposal creator |
| approved_by | VARCHAR(100) | Optional | Approver |
| created_at | DATETIME | Required | Creation timestamp |
| approved_at | DATETIME | Optional | Approval timestamp |
| applied_at | DATETIME | Optional | Application timestamp |

## 13. AuditLog

| Field | Type | Constraint | Description |
|---|---|---|---|
| audit_id | VARCHAR(50) | PK | Audit ID |
| entity_type | VARCHAR(50) | Required | Changed entity |
| entity_id | VARCHAR(100) | Required | Changed record ID |
| action | VARCHAR(30) | Required | Action performed |
| old_value | TEXT | Optional | Previous value |
| new_value | TEXT | Optional | Updated value |
| performed_by | VARCHAR(100) | Required | User performing action |
| performed_at | DATETIME | Required | Action timestamp |
| remarks | TEXT | Optional | Additional details |

## 14. ProposalHistory

| Field | Type | Constraint | Description |
|---|---|---|---|
| history_id | VARCHAR(50) | PK | History ID |
| proposal_id | VARCHAR(50) | FK | Proposal reference |
| previous_status | VARCHAR(20) | Optional | Previous status |
| new_status | VARCHAR(20) | Required | Updated status |
| changed_by | VARCHAR(100) | Required | User performing action |
| remarks | TEXT | Optional | Change reason |
| changed_at | DATETIME | Required | Change timestamp |

## 15. General Validation Rules

- All primary keys must be unique.
- All foreign keys must reference existing records.
- Salary values must be greater than zero.
- FTE must be greater than 0 and at most 1.
- Minimum salary must be less than midpoint salary.
- Midpoint salary must be less than maximum salary.
- Effective end dates must be later than start dates.
- Historical records must be preserved.
- Proposal status transitions must follow valid lifecycle rules.

## 16. Documentation Status

Initial data dictionary completed. Field-level validation and implementation constraints will be verified during database development.
