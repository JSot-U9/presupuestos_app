# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from sqlalchemy import Integer

from database.connection import get_session
from models.meta_presupuesto import MetaPresupuesto
from models.presupuesto import Presupuesto
from services.excel_export_service import exportar_presupuesto_excel
from services.excel_import_service import ExcelImportError, ExcelPresupuestoImporter, ImportResult
from services.presupuesto_service import PresupuestoService

__all__ = ["PresupuestoController", "ExcelImportError", "ImportResult"]


class PresupuestoController:
    @staticmethod
    def listar(proyecto_id: Optional[int] = None, anio: Optional[int] = None,
               texto_busqueda: str = "", meta: Optional[str] = None,
               rubro: Optional[str] = None, categoria: Optional[str] = None) -> list[Presupuesto]:
        with get_session() as session:
            registros = PresupuestoService.listar(session, proyecto_id, anio, texto_busqueda, meta, rubro, categoria)
            for r in registros:
                _ = r.proyecto.codigo if r.proyecto else None  # fuerza carga antes de expunge
                session.expunge(r)
            return registros

    @staticmethod
    def listar_metas() -> list[str]:
        with get_session() as session:
            metas = session.query(MetaPresupuesto.nro_meta).order_by(
                MetaPresupuesto.nro_meta.cast(Integer)
            ).distinct().all()
            return [str(m[0]).zfill(4) for m in metas]

    @staticmethod
    def listar_rubros(proyecto_id: Optional[int] = None) -> list[str]:
        with get_session() as session:
            query = session.query(Presupuesto.rubro).distinct().order_by(Presupuesto.rubro)
            if proyecto_id:
                query = query.filter(Presupuesto.proyecto_id == proyecto_id)
            return [str(r[0]) for r in query.all() if r[0] is not None]

    @staticmethod
    def listar_categorias(proyecto_id: Optional[int] = None) -> list[str]:
        with get_session() as session:
            query = session.query(Presupuesto.categoria).distinct().order_by(Presupuesto.categoria)
            if proyecto_id:
                query = query.filter(Presupuesto.proyecto_id == proyecto_id)
            return [str(c[0]) for c in query.all() if c[0] is not None]

    @staticmethod
    def listar_programas(proyecto_id: Optional[int] = None) -> list[str]:
        """Retorna lista de códigos de programa únicos."""
        with get_session() as session:
            query = session.query(Presupuesto.programa).distinct().order_by(Presupuesto.programa)
            if proyecto_id:
                query = query.filter(Presupuesto.proyecto_id == proyecto_id)
            return [str(p[0]) for p in query.all() if p[0] is not None]

    @staticmethod
    def listar_funciones(proyecto_id: Optional[int] = None) -> list[str]:
        """Retorna lista de códigos de función únicos."""
        with get_session() as session:
            query = session.query(Presupuesto.funcion).distinct().order_by(Presupuesto.funcion)
            if proyecto_id:
                query = query.filter(Presupuesto.proyecto_id == proyecto_id)
            return [str(f[0]) for f in query.all() if f[0] is not None]

    @staticmethod
    def listar_productos(proyecto_id: Optional[int] = None) -> list[str]:
        """Retorna lista de códigos de producto únicos."""
        with get_session() as session:
            query = session.query(Presupuesto.producto).distinct().order_by(Presupuesto.producto)
            if proyecto_id:
                query = query.filter(Presupuesto.proyecto_id == proyecto_id)
            return [str(p[0]) for p in query.all() if p[0] is not None]

    @staticmethod
    def listar_actividades(proyecto_id: Optional[int] = None) -> list[str]:
        """Retorna lista de códigos de actividad únicos."""
        with get_session() as session:
            query = session.query(Presupuesto.actividad_codigo).distinct().order_by(Presupuesto.actividad_codigo)
            if proyecto_id:
                query = query.filter(Presupuesto.proyecto_id == proyecto_id)
            return [str(a[0]) for a in query.all() if a[0] is not None]

    @staticmethod
    def eliminar(presupuesto_id: int) -> None:
        with get_session() as session:
            PresupuestoService.eliminar(session, presupuesto_id)

    @staticmethod
    def importar_excel(
        ruta_archivo: str,
        anio: int,
        proyecto_codigo: Optional[str] = None,
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
