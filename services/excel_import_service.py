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
from models.clasificador import normalizar_codigo
from models.presupuesto import Presupuesto
from models.proyecto import Proyecto
from services.clasificador_service import ClasificadorService
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

# Detecta el proyecto/actividad de cada bloque del reporte, en los dos
# formatos de exportación SIAF observados. En ambos casos el identificador
# estable (comparable entre reportes) es el código de 7 dígitos de la
# actividad/proyecto específico (p.ej. "5000276"), no el "SEC.FUNC" (que es
# solo un número de secuencia interno del propio archivo).
#
# Formato "por Proyecto" (una sola línea combinada):
#   "0035  0066 3000001 5000276 GESTION DEL PROGRAMA 22 048 0109"
#    META PROG PROD  ACT_COD    ACT_DESC                  FN DVF GRPF
# Captura: (1=meta, 2=programa, 3=producto, 4=actividad_codigo, 5=actividad_descripcion,
#           6=funcion, 7=division_funcional, 8=grupo_funcional)
PROYECTO_LINEA_COMBINADA_RE = re.compile(
    r"^(\d{4})\s+(\d{4})\s+(\d+)\s+(\d{5,7})\s+(.+?)\s+(\d{1,3})\s+(\d{1,3})\s+(\d{1,4})$"
)

# Formato "por Programa" (código y descripción en líneas separadas):
#   "3000001 ACCIONES COMUNES"
#   "5000276  GESTION DEL PROGRAMA"
# Se usa el ÚLTIMO código de 7 dígitos visto antes de las filas de datos,
# que es siempre el más específico (la actividad, no el proyecto genérico).
PROYECTO_LINEA_SEPARADA_RE = re.compile(r"^(\d{5,7})\s+(.+)$")

ProgressCallback = Callable[[int, str], None]


class ExcelImportError(Exception):
    """Error controlado durante la importación (se muestra al usuario)."""


@dataclass
class ImportResult:
    filas_importadas: int = 0
    proyectos_creados: list[str] = field(default_factory=list)
    proyectos_existentes: list[str] = field(default_factory=list)
    columnas_fusionadas: list[str] = field(default_factory=list)
    filas_encabezado_eliminadas: int = 0
    clasificadores_no_encontrados: list[str] = field(default_factory=list)
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
    # Etapa 2: parseo jerárquico Proyecto/Rubro/Programa/Meta/Categoría/Clasificador
    # ------------------------------------------------------------------
    def _parsear_jerarquia(self, df: pd.DataFrame) -> pd.DataFrame:
        # Reindexar columnas posicionalmente 0..10 tras la limpieza
        df = df.copy()
        df.columns = range(df.shape[1])

        rubro = None
        meta = programa = producto = actividad_codigo = actividad_descripcion = None
        funcion = division_funcional = grupo_funcional = None
        clasi_presu = None
        proyecto_codigo = proyecto_nombre = None
        filas: list[dict] = []

        for _, fila in df.iterrows():
            c0 = "" if pd.isna(fila[0]) else str(fila[0]).strip()
            if c0 == "":
                continue

            # --- Detección de proyecto/actividad (ambos formatos) ---
            m_combinado = PROYECTO_LINEA_COMBINADA_RE.match(c0)
            if m_combinado:
                meta = m_combinado.group(1)
                programa = m_combinado.group(2)
                producto = m_combinado.group(3)
                actividad_codigo = m_combinado.group(4)
                actividad_descripcion = m_combinado.group(5)
                funcion = m_combinado.group(6)
                division_funcional = m_combinado.group(7)
                grupo_funcional = m_combinado.group(8)
                proyecto_codigo, proyecto_nombre = actividad_codigo, actividad_descripcion
                continue

            m_separado = PROYECTO_LINEA_SEPARADA_RE.match(c0)
            if m_separado:
                # En formato separado, se usa el ÚLTIMO código de 7 dígitos
                # visto antes de las filas de datos (la actividad más específica).
                actividad_codigo = m_separado.group(1)
                actividad_descripcion = m_separado.group(2)
                proyecto_codigo, proyecto_nombre = actividad_codigo, actividad_descripcion
                continue

            if c0.startswith("00 "):
                rubro = c0
                continue
            if re.match(r"^\d{4}\s", c0):
                programa = c0
                continue
            if c0.upper().startswith("META"):
                continue
            if c0 in ("5", "6"):
                clasi_presu = c0
                continue
            if c0.upper().startswith("TOTAL"):
                continue

            if c0.startswith("2."):
                filas.append(
                    {
                        "proyecto_codigo": proyecto_codigo,
                        "proyecto_nombre": proyecto_nombre,
                        "rubro": rubro,
                        "meta": meta,
                        "programa": programa,
                        "producto": producto,
                        "actividad_codigo": actividad_codigo,
                        "actividad_descripcion": actividad_descripcion,
                        "funcion": funcion,
                        "division_funcional": division_funcional,
                        "grupo_funcional": grupo_funcional,
                        "categoria": None,
                        "clasi_presu": clasi_presu,
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
    # Etapa 3: persistencia en BD (un Proyecto por cada actividad detectada)
    # ------------------------------------------------------------------
    def importar(
        self,
        ruta_archivo: str | Path,
        session: Session,
        proyecto_codigo: Optional[str] = None,
        proyecto_nombre: Optional[str] = None,
        progress_cb: Optional[ProgressCallback] = None,
    ) -> ImportResult:
        """Importa el archivo completo y devuelve un resumen.

        Los proyectos se detectan y crean AUTOMÁTICAMENTE a partir de las
        líneas de actividad/proyecto del propio reporte (no requiere que el
        usuario tipee un código). `proyecto_codigo`/`proyecto_nombre` solo
        se usan como respaldo para las filas de un reporte antiguo/atípico
        donde no se pudo detectar ningún proyecto.
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

        _progreso(40, "Detectando proyectos y parseando jerarquía presupuestal...")
        df_final = self._parsear_jerarquia(df_limpio)

        if df_final.empty:
            raise ExcelImportError(
                "No se encontraron filas de clasificador de gasto (patrón '2.xxx') "
                "en el archivo."
            )

        sin_proyecto = df_final["proyecto_codigo"].isna()
        if sin_proyecto.any():
            if not proyecto_codigo:
                raise ExcelImportError(
                    f"{int(sin_proyecto.sum())} fila(s) no pudieron asociarse a ningún "
                    "proyecto (no se reconoció el formato de línea de proyecto/actividad "
                    "del reporte). Indique un código de proyecto de respaldo para "
                    "continuar, o revise que el archivo sea un reporte SIAF válido."
                )
            df_final.loc[sin_proyecto, "proyecto_codigo"] = proyecto_codigo
            df_final.loc[sin_proyecto, "proyecto_nombre"] = proyecto_nombre or proyecto_codigo

        for col in (
            "pia", "pim", "certificacion", "compromiso", "devengado",
            "saldo_certificacion", "saldo_compromiso", "saldo_devengado",
            "porcentaje_avance",
        ):
            df_final[col] = pd.to_numeric(df_final[col], errors="coerce").fillna(0.0)

        _progreso(60, "Registrando proyectos detectados...")
        # get-or-create de cada proyecto único encontrado en el archivo.
        proyectos_cache: dict[str, Proyecto] = {}
        for codigo, nombre in (
            df_final[["proyecto_codigo", "proyecto_nombre"]]
            .drop_duplicates()
            .itertuples(index=False)
        ):
            proyecto = session.query(Proyecto).filter_by(codigo=codigo).one_or_none()
            if proyecto is None:
                proyecto = Proyecto(codigo=codigo, nombre=nombre or codigo)
                session.add(proyecto)
                session.flush()  # obtiene proyecto.id sin cerrar la transacción
                resultado.proyectos_creados.append(codigo)
            else:
                resultado.proyectos_existentes.append(codigo)
            proyectos_cache[codigo] = proyecto

        _progreso(85, "Insertando partidas presupuestales...")
        for _, fila in df_final.iterrows():
            codigo_original = str(fila["clasificador"]) if fila["clasificador"] is not None else None
            codigo_norm = normalizar_codigo(codigo_original) if codigo_original else None

            clasificador_catalogo = None
            descripcion_final = fila["descripcion"]
            if codigo_norm:
                clasificador_catalogo = ClasificadorService.buscar(session, self.anio, codigo_norm)
                if clasificador_catalogo is not None:
                    # El catálogo oficial es la fuente de verdad para la descripción.
                    descripcion_final = clasificador_catalogo.descripcion
                else:
                    resultado.clasificadores_no_encontrados.append(codigo_norm)

            proyecto = proyectos_cache[fila["proyecto_codigo"]]
            registro = Presupuesto(
                proyecto_id=proyecto.id,
                anio=self.anio,
                mes=self.mes,
                rubro=fila["rubro"],
                meta=fila["meta"],
                programa=fila["programa"],
                producto=fila["producto"],
                actividad_codigo=fila["actividad_codigo"],
                actividad_descripcion=fila["actividad_descripcion"],
                funcion=fila["funcion"],
                division_funcional=fila["division_funcional"],
                grupo_funcional=fila["grupo_funcional"],
                categoria=None,
                clasi_presu=fila["clasi_presu"],
                clasificador=codigo_norm,
                clasificador_original=codigo_original,
                clasificador_id=clasificador_catalogo.id if clasificador_catalogo else None,
                descripcion=descripcion_final,
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

        if resultado.clasificadores_no_encontrados:
            no_encontrados_unicos = sorted(set(resultado.clasificadores_no_encontrados))
            resultado.advertencias.append(
                f"{len(no_encontrados_unicos)} clasificador(es) no encontrados en el catálogo "
                f"para el año {self.anio} (se guardó la descripción tal cual venía en el reporte): "
                + ", ".join(no_encontrados_unicos[:10])
                + ("..." if len(no_encontrados_unicos) > 10 else "")
            )

        resultado.filas_importadas = len(df_final)
        _progreso(100, "Importación completada.")
        return resultado
