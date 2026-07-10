# -*- coding: utf-8 -*-
"""Script de prueba: migración e importación con el nuevo formato.

Uso:
    python prueba_importacion.py <ruta_archivo.xls>
"""
from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import inspect, text

from config import UMBRAL_MIN_FILAS, UMBRAL_PORCENTAJE
from database.connection import engine, get_session, init_db
from models.clasificador import normalizar_codigo
from services.excel_import_service import ExcelPresupuestoImporter
from utils.logger import get_logger

logger = get_logger(__name__)


def aplicar_migracion() -> None:
    """Agrega los nuevos campos a la BD."""
    logger.info("\n" + "=" * 70)
    logger.info("PASO 1: Aplicando migración de estructura presupuestal")
    logger.info("=" * 70)

    with engine.begin() as conn:
        inspector = inspect(engine)
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
                logger.info(f"  → Agregando columna: {nombre_campo}")
                sql = f"ALTER TABLE presupuestos ADD COLUMN {nombre_campo} {tipo_sql} NULL"
                try:
                    conn.execute(text(sql))
                    logger.info(f"    ✓ {nombre_campo} agregado")
                except Exception as exc:
                    logger.warning(f"    (Posiblemente ya existe): {exc}")
            else:
                logger.info(f"  → {nombre_campo} ya existe")

    logger.info("✓ Migración completada\n")


def probar_importacion(ruta_archivo: str) -> None:
    """Importa el archivo con el nuevo formato."""
    logger.info("=" * 70)
    logger.info("PASO 2: Importando archivo presupuestal")
    logger.info("=" * 70)

    ruta = Path(ruta_archivo)
    if not ruta.exists():
        logger.error(f"✗ Archivo no encontrado: {ruta}")
        return

    logger.info(f"Archivo: {ruta.name} ({ruta.stat().st_size:,} bytes)")

    importador = ExcelPresupuestoImporter(anio=2026, mes=None)

    def progreso_cb(pct: int, msg: str) -> None:
        logger.info(f"  [{pct:3d}%] {msg}")

    try:
        with get_session() as session:
            resultado = importador.importar(
                ruta_archivo=ruta,
                session=session,
                progress_cb=progreso_cb,
            )

        logger.info("\n✓ Importación exitosa\n")
        logger.info("Resumen:")
        logger.info(f"  Filas importadas: {resultado.filas_importadas}")
        logger.info(f"  Proyectos creados: {resultado.proyectos_creados}")
        logger.info(f"  Proyectos existentes: {resultado.proyectos_existentes}")
        logger.info(f"  Columnas fusionadas: {len(resultado.columnas_fusionadas)}")
        logger.info(f"  Filas encabezado eliminadas: {resultado.filas_encabezado_eliminadas}")
        if resultado.clasificadores_no_encontrados:
            logger.info(f"  ⚠️  Clasificadores no encontrados: {len(resultado.clasificadores_no_encontrados)}")

        if resultado.advertencias:
            logger.info("\nAdvertencias:")
            for adv in resultado.advertencias:
                logger.warning(f"  ⚠️  {adv}")

    except Exception as exc:
        logger.error(f"\n✗ Error durante importación: {exc}", exc_info=True)
        return

    # Mostrar muestra de datos importados
    logger.info("\n" + "=" * 70)
    logger.info("PASO 3: Validando datos importados")
    logger.info("=" * 70)

    with get_session() as session:
        from models.presupuesto import Presupuesto

        # Consultar los últimos 5 registros importados
        registros = (
            session.query(Presupuesto)
            .order_by(Presupuesto.id.desc())
            .limit(5)
            .all()
        )

        if registros:
            logger.info("\nÚltimos 5 registros importados:")
            for i, reg in enumerate(reversed(registros), 1):
                logger.info(f"\n  [{i}] Presupuesto ID {reg.id}")
                logger.info(f"      Año: {reg.anio}")
                logger.info(f"      Rubro: {reg.rubro}")
                logger.info(f"      Meta: {reg.meta}")
                logger.info(f"      Programa: {reg.programa}")
                logger.info(f"      Producto: {reg.producto}")
                logger.info(f"      Actividad Código: {reg.actividad_codigo}")
                logger.info(f"      Actividad Descripción: {reg.actividad_descripcion}")
                logger.info(f"      Función: {reg.funcion}")
                logger.info(f"      División Funcional: {reg.division_funcional}")
                logger.info(f"      Grupo Funcional: {reg.grupo_funcional}")
                logger.info(f"      Clasificador: {reg.clasificador}")
                logger.info(f"      Descripción: {reg.descripcion}")
                logger.info(f"      PIM: {reg.pim:,.2f}")

            # Estadísticas agregadas
            total_registros = session.query(Presupuesto).count()
            logger.info(f"\n  Total de registros en BD: {total_registros}")

            # Campos únicos
            metas_unicas = session.query(Presupuesto.meta).distinct().count()
            programas_unicos = session.query(Presupuesto.programa).distinct().count()
            productos_unicos = session.query(Presupuesto.producto).distinct().count()
            actividades_unicas = session.query(Presupuesto.actividad_codigo).distinct().count()

            logger.info(f"\n  Valores únicos capturados:")
            logger.info(f"    Metas: {metas_unicas}")
            logger.info(f"    Programas: {programas_unicos}")
            logger.info(f"    Productos: {productos_unicos}")
            logger.info(f"    Actividades: {actividades_unicas}")

        logger.info("\n✓ Validación completada")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python prueba_importacion.py <ruta_archivo.xls>")
        print("Ejemplo: python prueba_importacion.py data/reporte.xls")
        sys.exit(1)

    archivo = sys.argv[1]

    # Inicializar BD si no existe
    init_db()

    # Ejecutar pasos
    aplicar_migracion()
    probar_importacion(archivo)

    logger.info("\n" + "=" * 70)
    logger.info("✓ Prueba completada")
    logger.info("=" * 70)
