import sys
import getpass
import re
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService


def prompt_admin_creation(db=None) -> bool:
    owns_session = False
    if db is None:
        try:
            db = SessionLocal()
            owns_session = True
        except Exception as e:
            print(f"\n[ERROR] Database connection failed: {e}")
            print("Please ensure your MySQL server is running and DATABASE_URL in backend/.env is correct.\n")
            return False

    try:
        print("\n" + "=" * 50)
        print("    SecureBank Administrator Creation Tool")
        print("=" * 50 + "\n")

        # 1. Prompt for Admin username
        username = input("Admin username: ").strip()
        if not username:
            print("[ERROR] Username cannot be empty.")
            return False
        if len(username) < 2:
            print("[ERROR] Username must be at least 2 characters long.")
            return False

        # 2. Prompt for Admin email
        email = input("Admin email: ").strip().lower()
        if not email:
            print("[ERROR] Email cannot be empty.")
            return False
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(email_regex, email):
            print("[ERROR] Invalid email address format.")
            return False

        # 3. Check if email already exists
        user_repo = UserRepository(db)
        existing = user_repo.get_by_email(email)
        if existing:
            if existing.role == "ADMIN":
                print(f"\n[NOTICE] An administrator with email '{email}' already exists.")
                return False
            else:
                print(f"\n[NOTICE] User '{email}' exists with role '{existing.role}'.")
                choice = input("Do you wish to promote this user to ADMIN with a new password? (y/N): ").strip().lower()
                if choice != "y":
                    print("Operation cancelled.")
                    return False

        # 4. Prompt for Password securely (masked)
        password = getpass.getpass("Admin password: ").strip()
        if not password:
            print("[ERROR] Password cannot be empty.")
            return False
        if len(password) < 8:
            print("[ERROR] Password must be at least 8 characters long for security.")
            return False

        confirm_password = getpass.getpass("Confirm admin password: ").strip()
        if password != confirm_password:
            print("[ERROR] Passwords do not match.")
            return False

        # 5. Hash password and save
        hashed_pw = hash_password(password)
        audit_service = AuditService(db)

        if existing:
            existing.full_name = username
            existing.password_hash = hashed_pw
            existing.role = "ADMIN"
            existing.status = "ACTIVE"
            user_repo.update(existing)
            db.commit()
            db.refresh(existing)
            user_id = existing.id
            audit_action = "ADMIN_PROMOTED"
            description = f"User {email} promoted to ADMIN via backend CLI bootstrap tool"
        else:
            admin_user = User(
                full_name=username,
                email=email,
                phone_number="",
                password_hash=hashed_pw,
                address="",
                role="ADMIN",
                status="ACTIVE",
            )
            created = user_repo.create(admin_user)
            db.commit()
            db.refresh(created)
            user_id = created.id
            audit_action = "ADMIN_BOOTSTRAP_CREATED"
            description = f"Administrator account created for {email} via backend CLI bootstrap tool"

        # 6. Audit Logging
        audit_service.log(
            action=audit_action,
            entity_type="USER",
            entity_id=str(user_id),
            description=description,
            actor_user_id=user_id,
            ip_address="127.0.0.1",
        )
        db.commit()

        print("\n" + "-" * 50)
        print("[SUCCESS] Administrator account successfully created!")
        print(f"  Username: {username}")
        print(f"  Email:    {email}")
        print("  Role:     ADMIN")
        print("  Status:   ACTIVE")
        print("-" * 50)
        print("\nYou can now log in at the login page using your email and password.")
        print("After logging in, you will be automatically directed to the Admin Portal.\n")
        return True

    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled by user.")
        return False
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        return False
    finally:
        if owns_session:
            db.close()


def main():
    success = prompt_admin_creation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
