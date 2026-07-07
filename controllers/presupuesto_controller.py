# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from database.connection import get_session
from models.presupuesto import Presupuesto
from services.excel_export_service import exportar_presupuesto_excel
from services.excel_import_service import ExcelImportError, ExcelPresupuestoImporter, ImportResult
from services.presupuesto_service import PresupuestoService

__all__ = ["PresupuestoController", "ExcelImportError", "ImportResult"]


class PresupuestoController:
    @staticmethod
    def listar(proyecto_id: Optional[int] = None, anio: Optional[int] = None,
               texto_busqueda: str = "") -> list[Presupuesto]:
        with get_session() as session:
            registros = PresupuestoService.listar(session, proyecto_id, anio, texto_busqueda)
            for r in registros:
                _ = r.proyecto.codigo if r.proyecto else None  # fuerza carga antes de expunge
                session.expunge(r)
            return registros

    @staticmethod
    def eliminar(presupuesto_id: int) -> None:
        with get_session() as session:
            PresupuestoService.eliminar(session, presupuesto_id)

    @staticmethod
    def importar_excel(
        ruta_archivo: str,
        anio: int,
        proyecto_codigo: str,
        proyecto_nombre: str = "",
        mes: Optional[int] = None,
        progress_cb: Optional[Callable[[int, str], None]] = None,
    ) -> ImportResult:
        importador = ExcelPresupuestoImporter(anio=anio, mes=mes)
        with get_session() as session:
            return importador.importar(
                ruta_archivo, session, proyecto_codigo, proyecto_nombre, progress_cb
            )

    @staticmethod
    def exportar_excel(destino: str, proyecto_id: Optional[int] = None) -> Path:
        with get_session() as session:
            registros = PresupuestoService.listar(session, proyecto_id=proyecto_id)
            for r in registros:
                _ = r.proyecto.codigo if r.proyecto else None
            return exportar_presupuesto_excel(registros, destino)
