# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from database.connection import get_session
from reports.pdf_generator import generar_reporte_ejecucion
from services.dashboard_service import DashboardKPIs, DashboardService
from services.excel_export_service import exportar_proyectos_excel
from services.proyecto_service import ProyectoService


class DashboardController:
    @staticmethod
    def obtener_kpis() -> DashboardKPIs:
        with get_session() as session:
            return DashboardService.calcular_kpis(session)

    @staticmethod
    def ejecucion_por_proyecto(top_n: int = 10) -> list[tuple[str, float, float]]:
        with get_session() as session:
            return DashboardService.ejecucion_por_proyecto(session, top_n)

    @staticmethod
    def generar_pdf_ejecucion(destino: str) -> Path:
        with get_session() as session:
            kpis = DashboardService.calcular_kpis(session)
            detalle = DashboardService.ejecucion_por_proyecto(session)
        return generar_reporte_ejecucion(destino, kpis, detalle)

    @staticmethod
    def exportar_proyectos_excel(destino: str) -> Path:
        with get_session() as session:
            proyectos = ProyectoService.listar(session)
            return exportar_proyectos_excel(proyectos, destino)
