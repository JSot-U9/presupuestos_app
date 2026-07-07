# -*- coding: utf-8 -*-
"""Validaciones de formularios usadas por controllers/services."""
from __future__ import annotations

import re

CODIGO_PROYECTO_RE = re.compile(r"^[A-Za-z0-9\-_.]{2,40}$")


class ValidationError(Exception):
    """Error de validación de formulario, mostrado directamente al usuario."""


def require_not_empty(value: str, field_name: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValidationError(f"El campo '{field_name}' es obligatorio.")
    return value


def validar_codigo_proyecto(codigo: str) -> str:
    codigo = require_not_empty(codigo, "Código")
    if not CODIGO_PROYECTO_RE.match(codigo):
        raise ValidationError(
            "El código de proyecto solo admite letras, números, guiones y puntos."
        )
    return codigo


def validar_username(username: str) -> str:
    username = require_not_empty(username, "Usuario")
    if len(username) < 3:
        raise ValidationError("El usuario debe tener al menos 3 caracteres.")
    return username


def validar_password(password: str) -> str:
    if not password or len(password) < 6:
        raise ValidationError("La contraseña debe tener al menos 6 caracteres.")
    return password


def validar_numero(value, field_name: str, permitir_negativo: bool = False) -> float:
    try:
        numero = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"'{field_name}' debe ser un número válido.")
    if not permitir_negativo and numero < 0:
        raise ValidationError(f"'{field_name}' no puede ser negativo.")
    return numero
