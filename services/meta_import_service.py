# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from models.meta_presupuesto import MetaPresupuesto
from utils.logger import get_logger

logger = get_logger(__name__)

COLUMNAS_REQUERIDAS = {"SEC_FUNC", "META", "FINALIDAD", "DESCRIPCION"}

# Patrón para limpiar la descripción: elimina el código de finalidad
# al inicio (ej. "0000464 CONSTRUCCION ..." -> "CONSTRUCCION ...")
_CODIGO_INICIAL_RE = re.compile(r"^\d{6,7}\s+")


class MetaImportError(Exception):
    """Error controlado durante la importación de metas."""


class MetaImportService:
    @staticmethod
    def importar(ruta_archivo: str | Path, session: Session) -> int:
        ruta = Path(ruta_archivo)
        if not ruta.exists():
            raise MetaImportError(f"El archivo no existe: {ruta}")

        try:
            df = pd.read_excel(ruta)
        except Exception as exc:
            raise MetaImportError(f"No se pudo leer el archivo: {exc}") from exc

        columnas = {c.strip().upper() for c in df.columns}
        if not COLUMNAS_REQUERIDAS.issubset(columnas):
            faltantes = COLUMNAS_REQUERIDAS - columnas
            raise MetaImportError(
                f"El archivo no tiene el formato esperado. "
                f"Faltan columnas: {', '.join(sorted(faltantes))}"
            )

        df.columns = [c.strip().upper() for c in df.columns]

        filas_validas = 0
        registros = []

        for _, fila in df.iterrows():
            sec_func = fila.get("SEC_FUNC")
            meta = fila.get("META")
            finalidad = fila.get("FINALIDAD")
            descripcion_raw = fila.get("DESCRIPCION")

            if pd.isna(sec_func) or pd.isna(meta):
                continue

            descripcion = str(descripcion_raw).strip() if pd.notna(descripcion_raw) else ""
            descripcion = _CODIGO_INICIAL_RE.sub("", descripcion).strip()

            registros.append(
                MetaPresupuesto(
                    nro_meta=str(int(sec_func)),
                    meta=str(int(meta)),
                    finalidad=str(int(finalidad)) if pd.notna(finalidad) else "",
                    descripcion=descripcion,
                )
            )
            filas_validas += 1

        if filas_validas == 0:
            raise MetaImportError("No se encontraron filas válidas en el archivo.")

        session.query(MetaPresupuesto).delete()
        session.flush()
        session.add_all(registros)

        logger.info("Metas importadas: %s registros (reemplazo completo).", filas_validas)
        return filas_validas
