# -*- coding: utf-8 -*-
"""Script de migración: agregar campo clasi_presu al modelo Presupuesto.

Este script agrega la columna clasi_presu (clasificación presupuestaria)
que almacena el valor de categoría del reporte SIAF (5, 6, etc.).

Uso:
    python migracion_clasi_presu.py
"""
from __future__ import annotations

from sqlalchemy import inspect, text

from database.connection import engine
from utils.logger import get_logger

logger = get_logger(__name__)


def migrar() -> None:
    """Ejecuta la migración de forma compatible con SQLite y PostgreSQL."""
    with engine.begin() as conn:
        inspector = inspect(engine)
        columnas_existentes = [col["name"] for col in inspector.get_columns("presupuestos")]

        if "clasi_presu" not in columnas_existentes:
            logger.info("Agregando columna: clasi_presu")
            sql = "ALTER TABLE presupuestos ADD COLUMN clasi_presu VARCHAR(10) NULL"
            try:
                conn.execute(text(sql))
                logger.info("✓ Columna clasi_presu agregada exitosamente")
            except Exception as exc:
                logger.error(f"✗ Error al agregar columna clasi_presu: {exc}")
        else:
            logger.info("Columna clasi_presu ya existe, omitiendo.")

        # Crear índice para mejorar búsquedas
        try:
            sql_idx = "CREATE INDEX IF NOT EXISTS idx_presupuesto_clasi_presu ON presupuestos(clasi_presu)"
            conn.execute(text(sql_idx))
            logger.info("✓ Índice idx_presupuesto_clasi_presu creado/verificado")
        except Exception as exc:
            logger.warning(f"Índice idx_presupuesto_clasi_presu posiblemente ya existe: {exc}")

        logger.info("\n✓ Migración completada exitosamente.")


if __name__ == "__main__":
    print("=" * 70)
    print("Migración: Agregar campo clasi_presu (clasificación presupuestaria)")
    print("=" * 70)
    print("\nIniciando migración...\n")
    migrar()
