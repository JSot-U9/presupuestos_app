# -*- coding: utf-8 -*-
"""Importador de reportes presupuestales SIAF (formato con celdas
combinadas: PIA/PIM/Certificación/Compromiso/Devengado/Saldos/% Avance).

Esta clase es un refactor directo de la lógica validada en
`pruebas_presupuesto.py` (limpieza de columnas fantasma por celdas
combinadas, eliminación de cabeceras repetidas, y parseo jerárquico
Rubro -> Programa -> Meta -> Categoría -> Clasificador), reorganizada en
3 etapas reutilizables y con manejo de excepciones para uso en un
pipeline de escritorio con barra de progreso.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import pandas as pd
from sqlalchemy.orm import Session

from config import UMBRAL_MIN_FILAS, UMBRAL_PORCENTAJE
from models.presupuesto import Presupuesto
from models.proyecto import Proyecto
from utils.logger import get_logger

logger = get_logger(__name__)

# Palabras que identifican filas de encabezado repetidas dentro del reporte.
PATRONES_ENCABEZADO = [
    "RUBRO DE FINANCIAMIENTO",
    "SEC.FUNC",
    "CAT GTO",
    "(PIA)",
    "PIM",
    "CERTIFICACIÓN",
    "COMPROMISO",
    "DEVENGADO",
    "% AVANCE",
]

<<<<<<< Updated upstream
=======
# Detecta el proyecto/actividad de cada bloque del reporte, en los dos
# formatos de exportación SIAF observados. En ambos casos el identificador
# estable (comparable entre reportes) es el código de 7 dígitos de la
# actividad/proyecto específico (p.ej. "5000276"), no el "SEC.FUNC" (que es
# solo un número de secuencia interno del propio archivo).
#
# Formato "por Proyecto" (una sola línea combinada):
#   "0035  0066 3000001 5000276 GESTION DEL PROGRAMA 22 048 0109"
#    SEC.FUNC PROD/PRY ACT/AI/OBR  cod.actividad   descripción      FN DVF GRPF
PROYECTO_LINEA_COMBINADA_RE = re.compile(
    r"^\d{4}\s+\d{4}\s+\d+\s+(\d{5,7})\s+(.+?)\s+\d{1,3}\s+\d{1,3}\s+\d{1,4}$"
)

# Formato "por Programa" (código y descripción en líneas separadas):
#   "3000001 ACCIONES COMUNES"
#   "5000276  GESTION DEL PROGRAMA"
# Se usa el ÚLTIMO código de 7 dígitos visto antes de las filas de datos,
# que es siempre el más específico (la actividad, no el proyecto genérico).
PROYECTO_LINEA_SEPARADA_RE = re.compile(r"^(\d{5,7})\s+(.+)$")

# Detecta líneas de "Meta: <numero> - <codigo> <descripcion>"
META_LINE_RE = re.compile(r"^META[:\s]*([0-9]+)\s*-\s*(\d{5,7})\b\s*(.*)$", re.IGNORECASE)

>>>>>>> Stashed changes
ProgressCallback = Callable[[int, str], None]


class ExcelImportError(Exception):
    """Error controlado durante la importación (se muestra al usuario)."""


@dataclass
class ImportResult:
    filas_importadas: int = 0
    proyectos_detectados: int = 0
    columnas_fusionadas: list[str] = field(default_factory=list)
    filas_encabezado_eliminadas: int = 0
    advertencias: list[str] = field(default_factory=list)


class ExcelPresupuestoImporter:
    """Importa un reporte SIAF (.xls/.xlsx) a las tablas Proyecto/Presupuesto."""

    def __init__(self, anio: int, mes: Optional[int] = None):
        self.anio = anio
        self.mes = mes

    # ------------------------------------------------------------------
    # Etapa 1: limpieza estructural (columnas/filas fantasma)
    # ------------------------------------------------------------------
    def _limpiar_estructura(self, ruta: Path, resultado: ImportResult) -> pd.DataFrame:
        try:
            df = pd.read_excel(ruta, header=None)
        except Exception as exc:  # noqa: BLE001
            raise ExcelImportError(f"No se pudo leer el archivo: {exc}") from exc

        if df.empty:
            raise ExcelImportError("El archivo está vacío.")

        df = df.dropna(how="all")
        df = df.dropna(axis=1, how="all")
        df.reset_index(drop=True, inplace=True)
        # Se fuerza dtype=object en todo el DataFrame: las columnas fantasma
        # mezclan texto (cabeceras) y números, y pandas >= 2.x lanza
        # LossySetitemError si se intenta escribir texto en una columna
        # inferida como float64 durante la fusión de columnas.
        df = df.astype(object)

        umbral = max(UMBRAL_MIN_FILAS, int(len(df) * UMBRAL_PORCENTAJE))
        conteo = df.notna().sum()
        columnas = list(df.columns)

        for col in columnas:
            if conteo[col] > umbral:
                continue
            valores = df[col].dropna()
            if len(valores) == 0:
                continue

            pos = columnas.index(col)
            izquierda = next(
                (columnas[i] for i in range(pos - 1, -1, -1) if conteo[columnas[i]] > umbral),
                None,
            )
            derecha = next(
                (columnas[i] for i in range(pos + 1, len(columnas)) if conteo[columnas[i]] > umbral),
                None,
            )

            destino = None
            if izquierda is not None and derecha is not None:
                dist_izq = abs(pos - columnas.index(izquierda))
                dist_der = abs(columnas.index(derecha) - pos)
                destino = izquierda if dist_izq <= dist_der else derecha
            elif izquierda is not None:
                destino = izquierda
            elif derecha is not None:
                destino = derecha

            if destino is not None:
                resultado.columnas_fusionadas.append(f"{col} -> {destino}")
                for fila in valores.index:
                    if pd.isna(df.at[fila, destino]):
                        df.at[fila, destino] = df.at[fila, col]

        conteo = df.notna().sum()
        columnas_eliminar = conteo[conteo <= umbral].index.tolist()
        df = df.drop(columns=columnas_eliminar)
        df.reset_index(drop=True, inplace=True)

        # Eliminar cabeceras repetidas (se conserva solo el primer bloque)
        filas_encabezado = []
        for idx, fila in df.iterrows():
            texto = " ".join(str(x).upper() for x in fila if pd.notna(x))
            if any(p in texto for p in PATRONES_ENCABEZADO):
                filas_encabezado.append(idx)

        filas_eliminar: list[int] = []
        if filas_encabezado:
            split_point = -1
            for i in range(len(filas_encabezado) - 1):
                if filas_encabezado[i + 1] != filas_encabezado[i] + 1:
                    split_point = i
                    break
            if split_point != -1:
                filas_eliminar = filas_encabezado[split_point + 1:]

        resultado.filas_encabezado_eliminadas = len(filas_eliminar)
        df = df.drop(index=filas_eliminar).reset_index(drop=True)

        if df.shape[1] < 11:
            raise ExcelImportError(
                "La estructura del archivo no coincide con el formato SIAF esperado "
                f"(se detectaron {df.shape[1]} columnas útiles, se esperaban al menos 11)."
            )
        return df

    # ------------------------------------------------------------------
    # Etapa 2: parseo jerárquico Rubro/Programa/Meta/Categoría/Clasificador
    # ------------------------------------------------------------------
    def _parsear_jerarquia(self, df: pd.DataFrame) -> pd.DataFrame:
        # Reindexar columnas posicionalmente 0..10 tras la limpieza
        df = df.copy()
        df.columns = range(df.shape[1])

        rubro = programa = meta = categoria = None
<<<<<<< Updated upstream
=======
        meta_numero = meta_codigo = None
        proyecto_codigo = proyecto_nombre = None
>>>>>>> Stashed changes
        filas: list[dict] = []

        for _, fila in df.iterrows():
            c0 = "" if pd.isna(fila[0]) else str(fila[0]).strip()
            if c0 == "":
                continue

<<<<<<< Updated upstream
=======
            # --- Detección de proyecto/actividad (ambos formatos) ---
            m_combinado = PROYECTO_LINEA_COMBINADA_RE.match(c0)
            if m_combinado:
                proyecto_codigo, proyecto_nombre = m_combinado.group(1), m_combinado.group(2)
                meta = None  # nuevo proyecto: se espera una nueva línea "Meta: ..."
                meta_numero = meta_codigo = None
                continue

            m_separado = PROYECTO_LINEA_SEPARADA_RE.match(c0)
            if m_separado:
                # El último código de 7 dígitos visto antes de las filas de
                # datos es siempre el más específico (la actividad real).
                proyecto_codigo, proyecto_nombre = m_separado.group(1), m_separado.group(2)
                meta_numero = meta_codigo = None
                continue

>>>>>>> Stashed changes
            if c0.startswith("00 "):
                rubro = c0
                continue
            if re.match(r"^\d{4}\s", c0):
                programa = c0
                continue
            if c0.upper().startswith("META"):
                m_meta = META_LINE_RE.match(c0)
                if m_meta:
                    meta_numero, meta_codigo, meta_desc = m_meta.group(1), m_meta.group(2), m_meta.group(3)
                    # conservar también el texto completo original
                    meta = f"META: {meta_numero} - {meta_codigo} {meta_desc}".strip()
                else:
                    # fallback defensivo: guardar el texto tal cual
                    meta = c0
                    meta_numero = meta_codigo = None
                continue
            if c0 in ("5", "6"):
                categoria = fila[1]
                continue
            if c0.upper().startswith("TOTAL"):
                continue

            if c0.startswith("2."):
                filas.append(
                    {
                        "rubro": rubro,
                        "programa": programa,
                        "meta": meta,
                        "meta_numero": meta_numero,
                        "meta_codigo": meta_codigo,
                        "categoria": categoria,
                        "clasificador": c0,
                        "descripcion": fila[1],
                        "pia": fila[2],
                        "pim": fila[3],
                        "certificacion": fila[4],
                        "compromiso": fila[5],
                        "devengado": fila[6],
                        "saldo_certificacion": fila[7],
                        "saldo_compromiso": fila[8],
                        "saldo_devengado": fila[9],
                        "porcentaje_avance": fila[10],
                    }
                )

        return pd.DataFrame(filas)

    # ------------------------------------------------------------------
    # Etapa 3: persistencia en BD (asociada a un Proyecto)
    # ------------------------------------------------------------------
    def importar(
        self,
        ruta_archivo: str | Path,
        session: Session,
        proyecto_codigo: str,
        proyecto_nombre: Optional[str] = None,
        progress_cb: Optional[ProgressCallback] = None,
    ) -> ImportResult:
        """Importa el archivo completo y devuelve un resumen.

        Crea el Proyecto si no existe (por `proyecto_codigo`) y agrega
        las filas de presupuesto asociadas.
        """
        ruta = Path(ruta_archivo)
        if not ruta.exists():
            raise ExcelImportError(f"El archivo no existe: {ruta}")

        resultado = ImportResult()

        def _progreso(pct: int, msg: str) -> None:
            logger.info("[%s%%] %s", pct, msg)
            if progress_cb:
                progress_cb(pct, msg)

        _progreso(10, "Leyendo archivo y limpiando estructura...")
        df_limpio = self._limpiar_estructura(ruta, resultado)

        _progreso(50, "Parseando jerarquía presupuestal...")
        df_final = self._parsear_jerarquia(df_limpio)

        if df_final.empty:
            raise ExcelImportError(
                "No se encontraron filas de clasificador de gasto (patrón '2.xxx') "
                "en el archivo."
            )

        for col in (
            "pia", "pim", "certificacion", "compromiso", "devengado",
            "saldo_certificacion", "saldo_compromiso", "saldo_devengado",
            "porcentaje_avance",
        ):
            df_final[col] = pd.to_numeric(df_final[col], errors="coerce").fillna(0.0)

        _progreso(70, "Registrando proyecto...")
        proyecto = session.query(Proyecto).filter_by(codigo=proyecto_codigo).one_or_none()
        if proyecto is None:
            proyecto = Proyecto(
                codigo=proyecto_codigo,
                nombre=proyecto_nombre or proyecto_codigo,
                programa=str(df_final.iloc[0]["programa"]) if not df_final.empty else None,
                meta=str(df_final.iloc[0]["meta"]) if not df_final.empty else None,
            )
            session.add(proyecto)
            session.flush()  # obtiene proyecto.id sin cerrar la transacción
            resultado.proyectos_detectados += 1

        _progreso(85, "Insertando partidas presupuestales...")
        for _, fila in df_final.iterrows():
            registro = Presupuesto(
                proyecto_id=proyecto.id,
                anio=self.anio,
                mes=self.mes,
                rubro=fila["rubro"],
                programa=fila["programa"],
                meta=fila["meta"],
                meta_numero=str(fila["meta_numero"]) if fila.get("meta_numero") is not None else None,
                meta_codigo=str(fila["meta_codigo"]) if fila.get("meta_codigo") is not None else None,
                categoria=str(fila["categoria"]) if fila["categoria"] is not None else None,
                clasificador=fila["clasificador"],
                descripcion=fila["descripcion"],
                pia=float(fila["pia"]),
                pim=float(fila["pim"]),
                certificacion=float(fila["certificacion"]),
                compromiso=float(fila["compromiso"]),
                devengado=float(fila["devengado"]),
                saldo_certificacion=float(fila["saldo_certificacion"]),
                saldo_compromiso=float(fila["saldo_compromiso"]),
                saldo_devengado=float(fila["saldo_devengado"]),
                porcentaje_avance=float(fila["porcentaje_avance"]),
                archivo_origen=ruta.name,
            )
            session.add(registro)

        resultado.filas_importadas = len(df_final)
        _progreso(100, "Importación completada.")
        return resultado
