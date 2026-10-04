import sys
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.user import User
from app.models.audit_log import AuditLog


def reactivate_admin(email: str = None, db=None) -> bool:
    if not email:
        if len(sys.argv) > 1:
            email = sys.argv[1].strip()
        else:
            try:
                email = input("Enter administrator email to reactivate: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled.")
                return False

    if not email:
        print("Error: Administrator email cannot be empty.")
        return False

    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user:
            print(f"Error: User with email '{email}' was not found.")
            return False

        if user.role != "ADMIN":
            print(f"Error: User '{email}' does not have the ADMIN role (current role: {user.role}).")
            return False

        if user.status == "ACTIVE":
            print(f"Notice: Administrator '{email}' is already active.")
            return True

        old_status = user.status
        user.status = "ACTIVE"

        # Record recovery audit log
        audit = AuditLog(
            actor_user_id=user.id,
            action="ADMIN_ACTIVATED",
            entity_type="USER",
            entity_id=str(user.id),
            description=f"Administrator {user.email} status recovered from {old_status} to ACTIVE via CLI recovery script",
            ip_address="127.0.0.1",
            timestamp=datetime.now(timezone.utc),
        )
        db.add(audit)
        db.commit()
        db.refresh(user)

        print(f"Success: Administrator '{user.email}' (ID: {user.id}) successfully reactivated.")
        print(f"Status changed from {old_status} -> ACTIVE.")
        return True
    except Exception as e:
        db.rollback()
        print(f"Error during reactivation: {e}")
        return False
    finally:
        if owns_session:
            db.close()


if __name__ == "__main__":
    success = reactivate_admin()
    sys.exit(0 if success else 1)
