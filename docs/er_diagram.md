
# CompVista - Entity Relationship Diagram

This diagram represents the database entities and their relationships.

```mermaid
erDiagram
    ROLE ||--o{ EMPLOYEE : has
    LEVEL ||--o{ EMPLOYEE : assigned_to
    LOCATION ||--o{ EMPLOYEE : works_at

    ROLE ||--o{ COMPENSATION_BAND : defines
    LEVEL ||--o{ COMPENSATION_BAND : defines
    LOCATION ||--o{ COMPENSATION_BAND : defines

    EMPLOYEE ||--o{ SALARY_RECORD : has
    COMPENSATION_BAND ||--o{ SALARY_RECORD : references

    EMPLOYEE ||--o{ PERFORMANCE_EVIDENCE : has
    EMPLOYEE ||--o{ TENURE : has
    EMPLOYEE ||--o{ PROMOTION : receives
    ROLE ||--o{ PROMOTION : previous_or_new_role
    LEVEL ||--o{ PROMOTION : previous_or_new_level

    EMPLOYEE ||--o{ ADJUSTMENT_PROPOSAL : receives
    SALARY_RECORD ||--o{ ADJUSTMENT_PROPOSAL : references

    ADJUSTMENT_PROPOSAL ||--o{ PROPOSAL_HISTORY : tracks

    EMPLOYEE {
        string employee_id PK
        string first_name
        string last_name
        string email
        string role_id FK
        string level_id FK
        string location_id FK
        date hire_date
        string employment_status
    }

    ROLE {
        string role_id PK
        string role_name
        string department
        string job_family
    }

    LEVEL {
        string level_id PK
        string level_name
        int level_rank
    }

    LOCATION {
        string location_id PK
        string location_name
        string country
        string currency_code
    }

    COMPENSATION_BAND {
        string band_id PK
        string role_id FK
        string level_id FK
        string location_id FK
        decimal min_salary
        decimal midpoint_salary
        decimal max_salary
        date effective_from
        date effective_to
    }

    SALARY_RECORD {
        string salary_id PK
        string employee_id FK
        string band_id FK
        decimal base_salary
        string currency_code
        decimal fte
        date effective_from
        date effective_to
    }

    PERFORMANCE_EVIDENCE {
        string evidence_id PK
        string employee_id FK
        decimal performance_rating
        string evidence_type
        date recorded_at
    }

    TENURE {
        string tenure_id PK
        string employee_id FK
        date start_date
        date end_date
        decimal fte
    }

    PROMOTION {
        string promotion_id PK
        string employee_id FK
        string previous_role_id FK
        string new_role_id FK
        string previous_level_id FK
        string new_level_id FK
        date promotion_date
    }

    ADJUSTMENT_PROPOSAL {
        string proposal_id PK
        string employee_id FK
        string current_salary_id FK
        decimal proposed_salary
        string status
    }

    PROPOSAL_HISTORY {
        string history_id PK
        string proposal_id FK
        string previous_status
        string new_status
        datetime changed_at
    }
```

## Additional Entity

AUDIT_LOG stores system-wide changes. It uses entity_type and entity_id to identify the affected record, so it is not represented as a conventional foreign-key relationship in this diagram.
