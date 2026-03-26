from __future__ import annotations


def validate_password_policy(*, username: str, password: str) -> bool:
    if len(password) < 8 or len(password) > 64:
        return False
    if password == username:
        return False
    if password == "admin":
        return False
    has_letter = any(ch.isalpha() for ch in password)
    has_number = any(ch.isdigit() for ch in password)
    return has_letter and has_number

