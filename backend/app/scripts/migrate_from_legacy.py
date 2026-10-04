import os
import sys
from decimal import Decimal
from datetime import datetime
from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.beneficiary import Beneficiary
from app.models.audit_log import AuditLog


def run_migration(
    mysql_host=None,
    mysql_user=None,
    mysql_password=None,
    mysql_db=None,
):
    mysql_host = mysql_host or os.getenv("LEGACY_MYSQL_HOST", "localhost")
    mysql_user = mysql_user or os.getenv("LEGACY_MYSQL_USER", "")
    mysql_password = mysql_password or os.getenv("LEGACY_MYSQL_PASSWORD", "")
    mysql_db = mysql_db or os.getenv("LEGACY_MYSQL_DATABASE", "banking_db")

    if not mysql_user or not mysql_password:
        print("Error: LEGACY_MYSQL_USER and LEGACY_MYSQL_PASSWORD must be set in environment.")
        return

    try:
        import pymysql
    except ImportError:
        print("pymysql not installed. Cannot run legacy migration.")
        return

    print("Connecting to legacy MySQL database...")
    try:
        conn = pymysql.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_db,
            cursorclass=pymysql.cursors.DictCursor,
        )
    except Exception as e:
        print(f"Could not connect to MySQL: {e}")
        return

    # Ensure tables exist in target DB
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        cursor = conn.cursor()

        # 1. Migrate Users
        cursor.execute("SELECT * FROM users")
        legacy_users = cursor.fetchall()
        user_id_map = {}
        print(f"Found {len(legacy_users)} users in MySQL.")
        for u in legacy_users:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if existing:
                print(f"User {u['email']} already exists in target DB. Mapping ID.")
                user_id_map[u["user_id"]] = existing.id
            else:
                new_user = User(
                    full_name=u["full_name"],
                    email=u["email"],
                    phone_number=u["phone_number"],
                    password_hash=u["password_hash"],
                    address=u.get("address") or "",
                    role=u.get("role") or "CUSTOMER",
                    status="ACTIVE",
                    created_at=u.get("created_at") or datetime.utcnow(),
                )
                db.add(new_user)
                db.flush()
                user_id_map[u["user_id"]] = new_user.id
                print(f"Migrated user {new_user.email} -> ID {new_user.id}")

        # 2. Migrate Accounts
        cursor.execute("SELECT * FROM accounts")
        legacy_accounts = cursor.fetchall()
        account_id_map = {}
        print(f"Found {len(legacy_accounts)} accounts in MySQL.")
        for a in legacy_accounts:
            existing = db.query(Account).filter(Account.account_number == a["account_number"]).first()
            if existing:
                print(f"Account {a['account_number']} already exists. Mapping ID.")
                account_id_map[a["account_id"]] = existing.id
            else:
                target_user_id = user_id_map.get(a["user_id"])
                if not target_user_id:
                    print(f"Warning: User ID {a['user_id']} not found for account {a['account_number']}. Skipping.")
                    continue
                new_account = Account(
                    account_number=a["account_number"],
                    user_id=target_user_id,
                    account_type=a["account_type"],
                    balance=Decimal(str(a["balance"])),
                    status=a.get("status") or "ACTIVE",
                    version=a.get("version") or 0,
                    created_at=a.get("created_at") or datetime.utcnow(),
                )
                db.add(new_account)
                db.flush()
                account_id_map[a["account_id"]] = new_account.id
                print(f"Migrated account {new_account.account_number} -> ID {new_account.id}")

        # 3. Migrate Transactions
        cursor.execute("SELECT * FROM transactions")
        legacy_txs = cursor.fetchall()
        print(f"Found {len(legacy_txs)} transactions in MySQL.")
        for t in legacy_txs:
            existing = db.query(Transaction).filter(
                Transaction.transaction_reference == t["transaction_reference"],
                Transaction.account_id == account_id_map.get(t["account_id"]),
            ).first()
            if existing:
                continue
            target_acc_id = account_id_map.get(t["account_id"])
            if not target_acc_id:
                continue

            raw_type = t.get("transaction_type") or "DEPOSIT"
            new_tx = Transaction(
                transaction_reference=t["transaction_reference"],
                account_id=target_acc_id,
                transaction_type=raw_type,
                amount=Decimal(str(t["amount"])),
                balance_before=Decimal(str(t["balance_after"] - t["amount"])) if t.get("balance_after") else None,
                balance_after=Decimal(str(t["balance_after"])) if t.get("balance_after") else Decimal("0.00"),
                description=t.get("description") or "",
                status=t.get("status") or "SUCCESS",
                created_at=t.get("created_at") or datetime.utcnow(),
            )
            db.add(new_tx)

        db.commit()
        print("Data migration completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
    finally:
        db.close()
        conn.close()


if __name__ == "__main__":
    run_migration()
