-- ============================================================
-- SecureBank Banking Management System — Reference MySQL Schema
-- ============================================================
-- NOTE: Alembic migrations located in 'backend/alembic/versions/'
-- are the SINGLE SOURCE OF TRUTH for database schema and evolutions.
--
-- This file serves as an explicit, architectural reference schema
-- illustrating table definitions, foreign keys, constraints, and indexes
-- for MySQL 8.x (InnoDB).
--
-- DO NOT seed default admin credentials or plaintext passwords here.
-- To create an Administrator account, run the interactive CLI tool:
--     python -m app.scripts.create_admin
-- ============================================================

CREATE DATABASE IF NOT EXISTS banking_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE banking_db;

-- ------------------------------------------------------------
-- 1. users
-- Application users (CUSTOMER or ADMIN roles)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id        BIGINT AUTO_INCREMENT PRIMARY KEY,
    full_name      VARCHAR(150) NOT NULL,
    email          VARCHAR(150) NOT NULL,
    phone_number   VARCHAR(20)  NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    address        VARCHAR(255) NULL,
    role           VARCHAR(20)  NOT NULL DEFAULT 'CUSTOMER',
    status         VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE',
    created_at     DATETIME     NOT NULL,
    updated_at     DATETIME     NULL,
    CONSTRAINT uk_users_email UNIQUE (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE UNIQUE INDEX idx_users_email ON users(email);

-- ------------------------------------------------------------
-- 2. accounts
-- Customer bank accounts (SAVINGS / CURRENT)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS accounts (
    account_id      BIGINT AUTO_INCREMENT PRIMARY KEY,
    account_number  VARCHAR(20)   NOT NULL,
    user_id         BIGINT        NOT NULL,
    account_type    VARCHAR(20)   NOT NULL,
    balance         DECIMAL(19,2) NOT NULL DEFAULT 0.00,
    status          VARCHAR(20)   NOT NULL DEFAULT 'ACTIVE',
    version         BIGINT        DEFAULT 0,
    created_at      DATETIME      NOT NULL,
    updated_at      DATETIME      NULL,
    CONSTRAINT uk_accounts_account_number UNIQUE (account_number),
    CONSTRAINT fk_accounts_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_accounts_user_id ON accounts(user_id);
CREATE UNIQUE INDEX idx_accounts_account_number ON accounts(account_number);

-- ------------------------------------------------------------
-- 3. transactions
-- Financial audit ledger (DEPOSIT, WITHDRAWAL, TRANSFER_IN, TRANSFER_OUT)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id        BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_reference VARCHAR(40)   NOT NULL,
    account_id            BIGINT        NOT NULL,
    amount                DECIMAL(19,2) NOT NULL,
    transaction_type      VARCHAR(20)   NOT NULL,
    balance_before        DECIMAL(19,2) NULL,
    balance_after         DECIMAL(19,2) NULL,
    description           VARCHAR(255)  NULL,
    status                VARCHAR(20)   NOT NULL DEFAULT 'SUCCESS',
    related_account_id    BIGINT        NULL,
    created_at            DATETIME      NOT NULL,
    CONSTRAINT fk_transactions_account FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE RESTRICT,
    CONSTRAINT fk_transactions_related_account FOREIGN KEY (related_account_id) REFERENCES accounts(account_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_reference ON transactions(transaction_reference);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);

-- ------------------------------------------------------------
-- 4. beneficiaries
-- Saved payees for intra-bank transfers
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS beneficiaries (
    beneficiary_id  BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT       NOT NULL,
    name            VARCHAR(150) NOT NULL,
    account_number  VARCHAR(20)  NOT NULL,
    bank_name       VARCHAR(150) NOT NULL,
    ifsc_code       VARCHAR(20)  NOT NULL,
    created_at      DATETIME     NOT NULL,
    CONSTRAINT fk_beneficiaries_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_beneficiaries_user_id ON beneficiaries(user_id);

-- ------------------------------------------------------------
-- 5. account_closure_requests
-- Formal account service requests (CLOSURE, REOPEN)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS account_closure_requests (
    closure_request_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id            BIGINT        NOT NULL,
    account_id         BIGINT        NOT NULL,
    reason             VARCHAR(255)  NOT NULL,
    additional_notes   TEXT          NULL,
    status             VARCHAR(20)   NOT NULL DEFAULT 'PENDING',
    request_type       VARCHAR(20)   NOT NULL DEFAULT 'CLOSURE',
    admin_notes        TEXT          NULL,
    reviewed_by        BIGINT        NULL,
    requested_at       DATETIME      NOT NULL,
    reviewed_at        DATETIME      NULL,
    CONSTRAINT fk_closure_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT,
    CONSTRAINT fk_closure_account FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE RESTRICT,
    CONSTRAINT fk_closure_reviewer FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_closure_user_id ON account_closure_requests(user_id);
CREATE INDEX idx_closure_account_id ON account_closure_requests(account_id);
CREATE INDEX idx_closure_status ON account_closure_requests(status);
CREATE INDEX idx_closure_request_type ON account_closure_requests(request_type);

-- ------------------------------------------------------------
-- 6. audit_logs
-- Immutable security & operational audit trail
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id       BIGINT AUTO_INCREMENT PRIMARY KEY,
    actor_user_id  BIGINT       NULL,
    action         VARCHAR(100) NOT NULL,
    entity_type    VARCHAR(100) NOT NULL,
    entity_id      VARCHAR(100) NULL,
    description    TEXT         NOT NULL,
    ip_address     VARCHAR(50)  NULL,
    timestamp      DATETIME     NOT NULL,
    CONSTRAINT fk_audit_actor FOREIGN KEY (actor_user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_audit_actor_id ON audit_logs(actor_user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);

-- ------------------------------------------------------------
-- 7. email_logs
-- Outgoing notification dispatch records
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS email_logs (
    email_log_id    BIGINT AUTO_INCREMENT PRIMARY KEY,
    recipient_email VARCHAR(150) NOT NULL,
    subject         VARCHAR(255) NOT NULL,
    body            TEXT         NOT NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'SENT',
    error_message   TEXT         NULL,
    created_at      DATETIME     NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_email_recipient ON email_logs(recipient_email);
CREATE INDEX idx_email_created_at ON email_logs(created_at);
