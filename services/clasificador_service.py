# -*- coding: utf-8 -*-
"""Gestión del catálogo oficial de clasificadores de gasto (MEF).

Formato de entrada esperado (columnas exactas): ANIO, CLASIFICADOR,
DESCRIPCION, DESCRIPCION_DETALLADA. Es el archivo que el usuario indicó
como fuente de verdad para validar/enriquecer los clasificadores que trae
cada reporte SIAF importado.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from models.clasificador import Clasificador, normalizar_codigo
from utils.logger import get_logger

logger = get_logger(__name__)

COLUMNAS_REQUERIDAS = {"ANIO", "CLASIFICADOR", "DESCRIPCION"}


class CatalogoImportError(Exception):
    """Error controlado al importar el catálogo (se muestra al usuario)."""


class ClasificadorService:
    @staticmethod
    def importar_catalogo(ruta_archivo: str | Path, session: Session) -> int:
        """Carga (upsert) el catálogo de clasificadores. Devuelve la
        cantidad de registros insertados o actualizados."""
        ruta = Path(ruta_archivo)
        if not ruta.exists():
            raise CatalogoImportError(f"El archivo no existe: {ruta}")

        try:
            df = pd.read_excel(ruta)
        except Exception as exc:  # noqa: BLE001
            raise CatalogoImportError(f"No se pudo leer el archivo: {exc}") from exc

        columnas = {c.strip().upper() for c in df.columns}
        if not COLUMNAS_REQUERIDAS.issubset(columnas):
            faltantes = COLUMNAS_REQUERIDAS - columnas
            raise CatalogoImportError(
                f"El archivo no tiene el formato de catálogo esperado. "
                f"Faltan columnas: {', '.join(sorted(faltantes))}"
            )
        df.columns = [c.strip().upper() for c in df.columns]

        # Índice existente (anio, codigo_normalizado) -> objeto, para upsert en memoria.
        existentes = {
            (c.anio, c.codigo_normalizado): c for c in session.query(Clasificador).all()
        }

        contador = 0
        for _, fila in df.iterrows():
            if pd.isna(fila["ANIO"]) or pd.isna(fila["CLASIFICADOR"]):
                continue

            anio = int(fila["ANIO"])
            codigo_original = str(fila["CLASIFICADOR"]).strip()
            codigo_norm = normalizar_codigo(codigo_original)
            if not codigo_norm:
                continue

            descripcion = str(fila["DESCRIPCION"]).strip() if pd.notna(fila["DESCRIPCION"]) else ""
            detallada = (
                str(fila["DESCRIPCION_DETALLADA"]).strip()
                if "DESCRIPCION_DETALLADA" in df.columns and pd.notna(fila.get("DESCRIPCION_DETALLADA"))
                else None
            )

            clave = (anio, codigo_norm)
            registro = existentes.get(clave)
            if registro is None:
                registro = Clasificador(
                    anio=anio,
                    codigo=codigo_original,
                    codigo_normalizado=codigo_norm,
                    descripcion=descripcion,
                    descripcion_detallada=detallada,
                )
                session.add(registro)
                existentes[clave] = registro
            else:
                registro.codigo = codigo_original
                registro.descripcion = descripcion
                registro.descripcion_detallada = detallada
            contador += 1

        logger.info("Catálogo de clasificadores importado: %s registros (%s).", contador, ruta.name)
        return contador

    @staticmethod
    def buscar(session: Session, anio: int, codigo: str) -> Optional[Clasificador]:
        codigo_norm = normalizar_codigo(codigo)
        return (
            session.query(Clasificador)
            .filter_by(anio=anio, codigo_normalizado=codigo_norm)
            .one_or_none()
        )

    @staticmethod
    def contar(session: Session, anio: Optional[int] = None) -> int:
        query = session.query(Clasificador)
        if anio:
            query = query.filter_by(anio=anio)
        return query.count()
