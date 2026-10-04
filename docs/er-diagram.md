# Entity-Relationship Diagram

This renders automatically when viewed on GitHub (GitHub supports Mermaid in Markdown). If viewing elsewhere, paste the code block into https://mermaid.live to render it.

```mermaid
erDiagram
    USERS ||--o{ ACCOUNTS : owns
    USERS ||--o{ BENEFICIARIES : saves
    USERS ||--o{ ACCOUNT_CLOSURE_REQUESTS : submits
    USERS ||--o{ AUDIT_LOGS : performs
    ACCOUNTS ||--o{ TRANSACTIONS : records
    ACCOUNTS ||--o{ ACCOUNT_CLOSURE_REQUESTS : targets

    USERS {
        bigint user_id PK
        varchar full_name
        varchar email UK
        varchar phone_number
        varchar password_hash
        varchar address
        varchar role
        varchar status
        datetime created_at
        datetime updated_at
    }

    ACCOUNTS {
        bigint account_id PK
        varchar account_number UK
        bigint user_id FK
        varchar account_type
        decimal balance
        varchar status
        bigint version
        datetime created_at
        datetime updated_at
    }

    TRANSACTIONS {
        bigint transaction_id PK
        varchar transaction_reference
        bigint account_id FK
        decimal amount
        varchar transaction_type
        decimal balance_before
        decimal balance_after
        varchar description
        varchar status
        bigint related_account_id FK
        datetime created_at
    }

    BENEFICIARIES {
        bigint beneficiary_id PK
        bigint user_id FK
        varchar name
        varchar account_number
        varchar bank_name
        varchar ifsc_code
        datetime created_at
    }

    ACCOUNT_CLOSURE_REQUESTS {
        bigint closure_request_id PK
        bigint user_id FK
        bigint account_id FK
        varchar reason
        text additional_notes
        varchar status
        varchar request_type
        text admin_notes
        bigint reviewed_by FK
        datetime requested_at
        datetime reviewed_at
    }

    AUDIT_LOGS {
        bigint audit_id PK
        bigint actor_user_id FK
        varchar action
        varchar entity_type
        varchar entity_id
        text description
        varchar ip_address
        datetime timestamp
    }

    EMAIL_LOGS {
        bigint email_log_id PK
        varchar recipient_email
        varchar subject
        text body
        varchar status
        text error_message
        datetime created_at
    }
```

## Design Notes

- **Authoritative Schema:** Managed via Alembic migrations (`backend/alembic/versions/`).
- **users -> accounts** is one-to-many: a customer can hold multiple accounts (e.g. `SAVINGS` and `CURRENT`), but each account belongs to exactly one customer.
- **accounts -> transactions** is one-to-many: every deposit, withdrawal, and leg of a transfer is recorded as a distinct row scoped to an account.
- **Fund Transfers:** A transfer produces two atomic `TRANSFER`-type transaction rows (debit `TRANSFER_OUT` + credit `TRANSFER_IN`) linked via a shared `transaction_reference`. Source and destination rows are acquired using ordered row locks to prevent deadlocks.
- **account_closure_requests:** Unifies account service requests (`CLOSURE` and `REOPEN`) with administrative review workflows.
- **audit_logs & email_logs:** System-wide traceability for administrative actions, compliance auditing, and email notification dispatch history.
