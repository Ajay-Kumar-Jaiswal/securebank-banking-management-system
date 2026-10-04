import re
from typing import Optional

PHONE_NUMBER_PATTERN = r"^[6-9][0-9]{9}$"
PHONE_REGEX = re.compile(PHONE_NUMBER_PATTERN)
PHONE_VALIDATION_ERROR_MSG = (
    "Phone number must be exactly 10 digits and start with 6, 7, 8, or 9."
)


def validate_phone_number(v: Optional[str], required: bool = True) -> Optional[str]:
    """
    Reusable phone number validator adhering to:
    - Exactly 10 digits
    - Digits only
    - First digit must be 6, 7, 8, or 9
    - No spaces, letters, symbols, or prefixes
    - Returns normalized 10-digit string
    - Raises ValueError with clear message if invalid
    """
    if v is None:
        if required:
            raise ValueError(PHONE_VALIDATION_ERROR_MSG)
        return None

    if not isinstance(v, str):
        raise ValueError(PHONE_VALIDATION_ERROR_MSG)

    cleaned = v.strip()
    if not cleaned or not PHONE_REGEX.match(cleaned):
        raise ValueError(PHONE_VALIDATION_ERROR_MSG)

    return cleaned
