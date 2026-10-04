import random
import secrets
from datetime import datetime, timezone


def generate_account_number() -> str:
    """Generate a 12-character account number: 'AC' prefix followed by 10 digits."""
    digits = "".join([str(random.randint(0, 9)) for _ in range(10)])
    return f"AC{digits}"


def generate_transaction_reference() -> str:
    """Generate a transaction reference: 'TXN-YYYYMMDD-' followed by 8 hex chars."""
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    hex_part = secrets.token_hex(4).upper()
    return f"TXN-{date_part}-{hex_part}"
