# -*- coding: utf-8 -*-
"""Hashing de contraseñas con PBKDF2-HMAC-SHA256 (stdlib, sin dependencias
externas). Evita almacenar contraseñas en texto plano y evita requerir
bcrypt/argon2 como dependencia binaria adicional para la v1.
"""
from __future__ import annotations

import hashlib
import os

_ITERATIONS = 260_000
_ALGO = "sha256"


def hash_password(password: str) -> str:
    """Devuelve 'salt$hash' en hexadecimal."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(_ALGO, password.encode("utf-8"), salt, _ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac(_ALGO, password.encode("utf-8"), salt, _ITERATIONS)
    return digest.hex() == hash_hex
