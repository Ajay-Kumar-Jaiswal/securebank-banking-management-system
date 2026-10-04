# SecureBank — Enterprise Banking Management System

An enterprise-grade, production-architected full-stack Banking Management System designed with clean layered architecture, robust relational data integrity, strict financial transaction atomicity, and role-based access control.

The system is built on a high-performance **Python 3.12+ / FastAPI** backend utilizing **SQLAlchemy 2.0**, **Pydantic v2**, and **Alembic**, backed by **MySQL 8.x**, and paired with a responsive, modern **React 18 (Vite)** single-page application.

---

## Architecture & Technology Stack

### Backend
- **Framework:** Python 3.12+ / [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous, Type-Safe REST API)
- **Database:** MySQL 8.x via PyMySQL connector
- **ORM & Data Layer:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) with Repository and Service patterns
- **Validation & Serialization:** [Pydantic v2](https://docs.pydantic.dev/latest/) with strict camelCase / snake_case aliasing
- **Schema Migrations:** [Alembic](https://alembic.sqlalchemy.org/) (Single source of truth for database schema)
- **Security & Authentication:** PyJWT (Bearer Tokens), Direct Bcrypt password hashing
- **Monetary Precision:** Python `Decimal` / Database `Numeric(19, 2)` throughout (floating-point money calculations strictly prohibited)
- **Concurrency & Deadlock Prevention:** Pessimistic ordered row-level locking (`SELECT ... FOR UPDATE`) on transfer operations
- **Resilient Email Dispatch:** Non-blocking transactional notification pipeline with persistent database audit in `EmailLog`
- **Testing:** [pytest](https://docs.pytest.org/) with in-memory SQLite isolation and 100% test pass rate

### Frontend
- **Framework:** React 18, React Router v6, Axios
- **Tooling:** Vite, PostCSS
- **Design System:** Custom responsive ledger-inspired UI theme with accessible modal confirmation dialogs, mobile navigation drawer, and badge indicators

---

## System Architecture

```
React (Vite Single Page Application)
   │
   │  HTTPS + JSON, Bearer JWT
   ▼
FastAPI API Routers (app/api/)
   │
   ├── Auth, Users, Accounts, Transactions, Beneficiaries, Account Requests, Admin
   │
Service Layer (app/services/)
   │
   ├── AuthService, AccountService, TransactionService, BeneficiaryService,
   │   AccountRequestService, AdminService, AuditService, EmailService
   │
Repository Layer (app/repositories/)
   │
   ├── UserRepository, AccountRepository, TransactionRepository,
   │   BeneficiaryRepository, AccountRequestRepository, AuditLogRepository, EmailLogRepository
   │
SQLAlchemy 2.x ORM Models (app/models/)
   │
   ▼
MySQL Database (Alembic Migrations)
```

---

## Key Features

### 1. Customer Banking Portal
- **Authentication & Security:** Registration with 10-digit phone number validation, JWT login, profile management, and password change.
- **Account Management:** Open multiple `SAVINGS` or `CURRENT` accounts with unique account number generation.
- **Financial Transactions:**
  - **Deposit:** Real-time atomic deposit with pre-submission confirmation modals.
  - **Withdrawal:** Atomic deduction with insufficient-funds rejection and confirmation modals.
  - **Fund Transfer:** Intra-bank transfer with destination validation, deadlock-safe ordered row locking, and simultaneous dual transaction ledger entries (`TRANSFER_OUT` and `TRANSFER_IN`).
- **Beneficiaries:** Add, view, and safely remove payees with destination account verification.
- **Transaction History:** Filter by account, transaction type (`DEPOSIT`, `WITHDRAWAL`, `TRANSFER_IN`, `TRANSFER_OUT`), and date range.
- **Account Requests Workflow:**
  - Submit formal service requests:
    - **Closure Request:** Allowed on active accounts when balance is zero.
    - **Reopen Request:** Allowed on closed accounts.
  - Real-time status tracking (`PENDING`, `APPROVED`, `REJECTED`) with administrative decision notes.

### 2. Executive Admin Portal
- **Role-Based Access Control:** Strict role-based isolation (Customer and Admin roles).
- **Dashboard Metrics:** Real-time bank telemetry including customer counts, account statuses, pending requests, total custodial deposits, and transaction volume aggregates.
- **Customer Management:** Comprehensive search and status filters; inspect complete customer details including linked accounts, balances, and ledger history.
- **Account Governance:** Activate, suspend, or close customer accounts with balance checks and administrative audit logging.
- **Account Requests Hub:** Unified management of customer closure and reopening requests with approval/rejection modals and note tracking.
- **System Audit Log Viewer:** Searchable audit trail capturing actor, action, entity type, entity ID, client IP address, and timestamp.

---

## Directory Structure

```
banking-management-system/
├── backend/
│   ├── alembic/                 # Alembic migration scripts
│   │   ├── versions/            # Versioned migration revisions
│   │   └── env.py
│   ├── app/
│   │   ├── api/                 # REST Routers & dependencies
│   │   ├── core/                # Config, DB engine, security, exceptions, logging
│   │   ├── models/              # SQLAlchemy database models
│   │   ├── repositories/        # Database access layer
│   │   ├── schemas/             # Pydantic v2 validation schemas
│   │   ├── services/            # Business logic layer
│   │   ├── scripts/             # Admin creation & maintenance CLI tools
│   │   ├── tests/               # Automated pytest suite
│   │   └── main.py              # Application entrypoint
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/                 # Axios clients for all endpoints
│   │   ├── components/          # Navbar, Modals, Badges, Protected Routes
│   │   ├── context/             # AuthContext (JWT & state management)
│   │   ├── pages/               # Customer & Admin views
│   │   │   ├── admin/           # Admin portal pages
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Accounts.jsx
│   │   │   ├── Transfer.jsx
│   │   │   └── ...
│   │   ├── utils/               # Formatters & error parsing
│   │   ├── App.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
├── docs/                        # Architecture diagrams & reference schema
│   ├── schema.sql
│   └── er-diagram.md
├── postman/                     # Postman API test collection
└── README.md
```

---

## Quickstart Guide

### Prerequisites
- Python 3.12 or newer
- Node.js 18 or newer
- MySQL Server 8.x
- Git

---

### Step 1: Set Up Backend

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `backend/.env` with your MySQL database credentials and settings:
   ```ini
   DATABASE_URL=mysql+pymysql://<user>:<password>@localhost:3306/banking_db
   JWT_SECRET_KEY=your-secure-random-secret-key
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
   ```

5. Run database migrations to apply the schema:
   ```bash
   alembic upgrade head
   ```

6. Create your first Administrator account:
   ```bash
   python -m app.scripts.create_admin
   ```
   > **Note:** The application does **NOT** ship with any default administrator accounts or preset credentials. This interactive CLI tool will securely prompt you for:
   > - Admin username
   > - Admin email
   > - Admin password (masked input)
   >
   > The password is validated, salted, and hashed using Bcrypt before being stored in MySQL.

7. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   - API Server: `http://localhost:8000`
   - Interactive Swagger API Documentation: `http://localhost:8000/docs`
   - ReDoc Documentation: `http://localhost:8000/redoc`

---

### Step 2: Set Up Frontend

1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Ensure `VITE_API_BASE_URL` is set:
   ```ini
   VITE_API_BASE_URL=http://localhost:8000/api
   ```

4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   - Open your browser at `http://localhost:5173`

5. Build for production:
   ```bash
   npm run build
   ```

---

## Running the Automated Test Suite

The backend includes a comprehensive pytest suite covering all business logic, phone validation rules, access control boundaries, deadlock protection, edge cases, and email logging:

```bash
cd backend
python -m pytest -v
```

All test modules execute against an isolated in-memory test database with 100% pass rate.

---

## Environment Variables Reference

### Backend (`backend/.env`)

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | SQLAlchemy MySQL connection string | `mysql+pymysql://<user>:<password>@localhost:3306/banking_db` |
| `JWT_SECRET_KEY` | Secret key used for signing JWT tokens | `your-secure-random-secret-key` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Expiration time for access tokens | `60` |
| `SMTP_HOST` | Hostname for outgoing SMTP mail server | `smtp.gmail.com` |
| `SMTP_PORT` | Port for outgoing SMTP server | `587` |
| `SMTP_USERNAME` | SMTP username / sender account | `your-email@example.com` |
| `SMTP_PASSWORD` | SMTP password or App Password | `your-smtp-password` |
| `SMTP_FROM_EMAIL` | Sender address for outgoing emails | `your-email@example.com` |
| `SMTP_FROM_NAME` | Sender display name | `SecureBank Management System` |
| `FRONTEND_URL` | Allowed origin for frontend client | `http://localhost:5173` |
| `ENVIRONMENT` | Environment mode (`development` / `production`) | `development` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Frontend (`frontend/.env`)

| Variable | Description | Default |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000/api` |

---

## Security & Reliability Design Patterns

1. **Strict Relational Precision:** Balances and transaction amounts use fixed-point `Decimal` / `Numeric(19, 2)` arithmetic to eliminate floating-point drift.
2. **Deadlock-Free Fund Transfers:** Source and destination account records are acquired with ordered row-level locks (`SELECT ... FOR UPDATE` ordered by account ID ascending) to enforce lock hierarchy consistency.
3. **Resilient Notifications:** Transaction execution is isolated from external mail server downtime; unsent messages are safely audited in `email_logs`.
4. **Immutable Audit Trails:** Administrative status changes, transaction settlements, user profile edits, and closure requests write audit records to `audit_logs` containing the actor ID, action type, target entity ID, timestamp, and client IP.
5. **No Preset Admin Credentials:** The system strictly enforces interactive admin bootstrapping via CLI, eliminating default-credential vulnerabilities.
