# utils/phone.py

import re


def normalize_phone(phone: str | None) -> str | None:
    """
    Basic phone normalization.

    For MVP:
    - Keeps leading +
    - Removes spaces, brackets, hyphens, dots
    - Returns None if empty

    Later, we can replace this with python-phonenumbers for stricter E.164 validation.
    """

    if not phone:
        return None

    phone = phone.strip()

    if not phone:
        return None

    if phone.startswith("+"):
        return "+" + re.sub(r"\D", "", phone[1:])

    return re.sub(r"\D", "", phone)


def phone_search_pattern(phone: str | None) -> str | None:
    """
    Creates a loose phone search value.
    Useful because DB may contain +1xxx, xxx-xxx, or formatted phone values.
    """

    normalized = normalize_phone(phone)

    if not normalized:
        return None

    # Remove + for loose matching
    return normalized.replace("+", "")