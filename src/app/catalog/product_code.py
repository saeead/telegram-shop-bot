"""Product code generation."""

from __future__ import annotations

import secrets
import string

_ALPHABET = string.ascii_uppercase + string.digits


def generate_product_code(prefix: str = "P") -> str:
    """Generate a compact human-readable code.

    Uniqueness is ultimately enforced by the database unique constraint; the random
    suffix makes collisions practically negligible and keeps codes easy to dictate.
    """

    normalized = prefix.strip().upper()
    if not normalized or not normalized.isalnum():
        raise ValueError("product code prefix must be alphanumeric")
    suffix = "".join(secrets.choice(_ALPHABET) for _ in range(8))
    return f"{normalized}-{suffix}"
