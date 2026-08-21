"""
Security and HIPAA/data privacy sanitization helpers.
"""

import re


def mask_phi(text: str) -> str:
    """
    Mask basic Protected Health Information (PHI) such as phone numbers, emails, and SSNs.
    """
    email_pattern = r"[\w\.-]+@[\w\.-]+"
    phone_pattern = r"\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b"
    ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"

    sanitized = re.sub(email_pattern, "[REDACTED EMAIL]", text)
    sanitized = re.sub(phone_pattern, "[REDACTED PHONE]", sanitized)
    sanitized = re.sub(ssn_pattern, "[REDACTED SSN]", sanitized)
    return sanitized
