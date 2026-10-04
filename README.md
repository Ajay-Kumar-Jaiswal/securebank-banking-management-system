# SecureBank — Banking Management System

A full-stack banking management system built with **FastAPI, React, and MySQL**, featuring secure authentication, account management, financial transactions, admin controls, audit logging, and account closure/reopen workflows.

## Tech Stack

**Backend:** Python 3.12+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, MySQL 8, JWT, Bcrypt, Pytest

**Frontend:** React 18, Vite, React Router, Axios

## Features

### Customer
- Secure registration and JWT authentication
- Savings and current accounts
- Deposit and withdrawal
- Account-to-account transfers
- Beneficiary management
- Transaction history and filtering
- Profile and password management
- Account closure and reopen requests
- Email notifications

### Admin
- Role-based access control
- Customer and account management
- Transaction monitoring
- Account closure/reopen approvals
- Audit log viewer
- Dashboard statistics

## Architecture

```text
React + Vite
      ↓
FastAPI REST API
      ↓
Service Layer
      ↓
Repository Layer
      ↓
SQLAlchemy
      ↓
MySQL
```
```
securebank/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── scripts/
│   │   └── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env.example
├── docs/
├── postman/
└── README.md
```
---
## Setup

### Backend

```bash
cd backend
python -m venv .venv
```

**Windows:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example` and configure your MySQL credentials.

**Run migrations:**
```bash
alembic upgrade head
```

**Create an admin account:**
```bash
python -m app.scripts.create_admin
```

**Start the backend:**
```bash
uvicorn app.main:app --reload --port 8000
```

API: http://localhost:8000  
Swagger: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Testing

**Run backend tests:**
```bash
cd backend
python -m pytest -v
```

**106 tests passing.**

**Build the frontend:**
```bash
cd frontend
npm run build
```

## Security

- JWT-based authentication
- Bcrypt password hashing
- Role-based access control
- Input validation
- Decimal-based monetary calculations
- Database transactions and row-level locking
- Audit logging
- Email logging
- No default admin credentials
- Secrets stored in environment variables

## API Testing

Postman collection:

`postman/Banking-Management-System.postman_collection.json`

## License

This project is for educational and portfolio purposes.
