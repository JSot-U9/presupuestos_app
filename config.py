# -*- coding: utf-8 -*-
"""Configuración central del Sistema de Gestión de Ejecución Presupuestal.

Todas las rutas y parámetros sensibles se leen de variables de entorno,
con valores por defecto pensados para que la app funcione "out of the box"
en modo SQLite, y se reconfigure a PostgreSQL en producción sin tocar código.
"""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------
# Producción esperada: postgresql+psycopg2://usuario:password@host:5432/presupuesto_db
# Por defecto (v1 / demo / desarrollo sin servidor Postgres): SQLite local.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{(DATA_DIR / 'presupuesto.db').as_posix()}",
)

SQL_ECHO = os.getenv("SQL_ECHO", "0") == "1"

# ---------------------------------------------------------------------------
# Aplicación
# ---------------------------------------------------------------------------
APP_NAME = "Sistema de Gestión de Ejecución Presupuestal"
APP_VERSION = "1.0.0"
ORGANIZATION = os.getenv("ORG_NAME", "UNSAAC")

# Umbral usado por el importador SIAF para detectar columnas "fantasma"
# generadas por celdas combinadas (idéntico criterio al script original).
UMBRAL_MIN_FILAS = 5
UMBRAL_PORCENTAJE = 0.02

# Roles soportados en v1 (permisos granulares quedan para v2)
ROLES = ("ADMIN", "EDITOR", "VISUALIZADOR")

LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"
