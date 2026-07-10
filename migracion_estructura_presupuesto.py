# -*- coding: utf-8 -*-
"""Script de migración: agregar campos de estructura presupuestal.

Este script agrega los nuevos campos al modelo Presupuesto:
- producto (código 3000001)
- actividad_codigo (código 5000276)
- actividad_descripcion (GESTION DEL PROGRAMA)
- funcion (código 22)
- division_funcional (código 048)
- grupo_funcional (código 0109)

Uso:
    python migracion_estructura_presupuesto.py
"""
from __future__ import annotations

from sqlalchemy import text

from database.connection import engine
from utils.logger import get_logger

logger = get_logger(__name__)


def migrar() -> None:
    """Ejecuta la migración de forma compatible con SQLite y PostgreSQL."""
    with engine.begin() as conn:
        inspector = engine.inspect(engine)
        columnas_existentes = [col["name"] for col in inspector.get_columns("presupuestos")]

        campos_nuevos = [
            ("producto", "VARCHAR(20)"),
            ("actividad_codigo", "VARCHAR(20)"),
            ("actividad_descripcion", "VARCHAR(300)"),
            ("funcion", "VARCHAR(10)"),
            ("division_funcional", "VARCHAR(10)"),
            ("grupo_funcional", "VARCHAR(10)"),
        ]

        for nombre_campo, tipo_sql in campos_nuevos:
            if nombre_campo not in columnas_existentes:
                logger.info(f"Agregando columna: {nombre_campo}")
                # SQLite usa ALTER TABLE ... ADD COLUMN
                # PostgreSQL también (sin DEFAULT ni NOT NULL por defecto)
                sql = f"ALTER TABLE presupuestos ADD COLUMN {nombre_campo} {tipo_sql} NULL"
                try:
                    conn.execute(text(sql))
                    logger.info(f"✓ Columna {nombre_campo} agregada exitosamente")
                except Exception as exc:
                    logger.error(f"✗ Error al agregar columna {nombre_campo}: {exc}")
            else:
                logger.info(f"Columna {nombre_campo} ya existe, omitiendo.")

        # Crear índices en los campos nuevos para mejorar búsquedas
        indices = [
            ("idx_presupuesto_meta", "presupuestos", "meta"),
            ("idx_presupuesto_programa", "presupuestos", "programa"),
            ("idx_presupuesto_producto", "presupuestos", "producto"),
            ("idx_presupuesto_actividad_codigo", "presupuestos", "actividad_codigo"),
            ("idx_presupuesto_funcion", "presupuestos", "funcion"),
            ("idx_presupuesto_division_funcional", "presupuestos", "division_funcional"),
            ("idx_presupuesto_grupo_funcional", "presupuestos", "grupo_funcional"),
        ]

        for idx_name, tabla, columna in indices:
            try:
                # Intentar crear el índice
                sql_idx = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {tabla}({columna})"
                conn.execute(text(sql_idx))
                logger.info(f"✓ Índice {idx_name} creado/verificado")
            except Exception as exc:
                logger.warning(f"Índice {idx_name} posiblemente ya existe: {exc}")

        logger.info("\n✓ Migración completada exitosamente.")


def recrear_bd() -> None:
    """Opción alternativa: eliminar y recrear la BD desde cero.
    
    ADVERTENCIA: Esto borra todos los datos. Solo usar en desarrollo.
    """
    from pathlib import Path
    from config import DATABASE_URL

    if "sqlite:///" in DATABASE_URL:
        db_path = DATABASE_URL.replace("sqlite:///", "")
        db_file = Path(db_path)
        if db_file.exists():
            logger.warning(f"Eliminando BD SQLite: {db_file}")
            db_file.unlink()

    from database.connection import init_db
    init_db()
    logger.info("✓ Base de datos recreada desde cero.")


if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("Migración: Agregar estructura presupuestal jerárquica")
    print("=" * 70)

    if len(sys.argv) > 1 and sys.argv[1] == "--recrear":
        print("\n⚠️  OPCIÓN DESTRUCTIVA: Eliminará todos los datos.\n")
        confirmacion = input("¿Continuar? (escriba 'sí' para confirmar): ").strip().lower()
        if confirmacion == "sí":
            recrear_bd()
        else:
            print("Operación cancelada.")
    else:
        print("\nOpción 1: Migración segura (ADD COLUMN)")
        print("  → Preserva datos existentes")
        print("  → Agrega nuevos campos como NULL")
        print("\nOpción 2: Recrear BD desde cero")
        print("  → Ejecutar con: python migracion_estructura_presupuesto.py --recrear")
        print("  → ⚠️  Borra TODOS los datos (solo desarrollo)")
        print("\nIniciando Opción 1...\n")
        migrar()
